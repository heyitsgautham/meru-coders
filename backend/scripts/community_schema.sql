-- =============================================================================
-- Community Feature Database Schema for Supabase
-- Twitter-like social platform for Sanskrit Community
-- =============================================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- POSTS TABLE
-- Main table for user posts with optional Sanskrit text and meter analysis
-- =============================================================================

CREATE TABLE IF NOT EXISTS posts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    sanskrit_text TEXT,
    meter_analysis JSONB,
    likes_count INTEGER DEFAULT 0,
    comments_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for posts
CREATE INDEX IF NOT EXISTS idx_posts_user_id ON posts(user_id);
CREATE INDEX IF NOT EXISTS idx_posts_created_at ON posts(created_at DESC);

-- =============================================================================
-- POST_LIKES TABLE
-- Tracks which users have liked which posts
-- =============================================================================

CREATE TABLE IF NOT EXISTS post_likes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    post_id UUID NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(post_id, user_id)
);

-- Indexes for post_likes
CREATE INDEX IF NOT EXISTS idx_post_likes_post_id ON post_likes(post_id);
CREATE INDEX IF NOT EXISTS idx_post_likes_user_id ON post_likes(user_id);

-- =============================================================================
-- POST_COMMENTS TABLE
-- Stores comments on posts
-- =============================================================================

CREATE TABLE IF NOT EXISTS post_comments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    post_id UUID NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for post_comments
CREATE INDEX IF NOT EXISTS idx_post_comments_post_id ON post_comments(post_id);
CREATE INDEX IF NOT EXISTS idx_post_comments_user_id ON post_comments(user_id);
CREATE INDEX IF NOT EXISTS idx_post_comments_created_at ON post_comments(created_at);

-- =============================================================================
-- NOTIFICATIONS TABLE (For Phase 2 - Deferred)
-- Prepared table structure for future notification feature
-- =============================================================================

CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL, -- 'like', 'comment', 'follow', 'mention'
    actor_id UUID REFERENCES users(id) ON DELETE SET NULL,
    post_id UUID REFERENCES posts(id) ON DELETE CASCADE,
    comment_id UUID REFERENCES post_comments(id) ON DELETE CASCADE,
    content TEXT,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for notifications
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(user_id, is_read);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at DESC);

-- =============================================================================
-- HELPER FUNCTIONS FOR COUNTERS
-- These RPC functions are called from the backend to update counts atomically
-- =============================================================================

-- Increment likes count
CREATE OR REPLACE FUNCTION increment_likes_count(p_post_id UUID)
RETURNS VOID AS $$
BEGIN
    UPDATE posts SET likes_count = likes_count + 1 WHERE id = p_post_id;
END;
$$ LANGUAGE plpgsql;

-- Decrement likes count
CREATE OR REPLACE FUNCTION decrement_likes_count(p_post_id UUID)
RETURNS VOID AS $$
BEGIN
    UPDATE posts SET likes_count = GREATEST(0, likes_count - 1) WHERE id = p_post_id;
END;
$$ LANGUAGE plpgsql;

-- Increment comments count
CREATE OR REPLACE FUNCTION increment_comments_count(p_post_id UUID)
RETURNS VOID AS $$
BEGIN
    UPDATE posts SET comments_count = comments_count + 1 WHERE id = p_post_id;
END;
$$ LANGUAGE plpgsql;

-- Decrement comments count
CREATE OR REPLACE FUNCTION decrement_comments_count(p_post_id UUID)
RETURNS VOID AS $$
BEGIN
    UPDATE posts SET comments_count = GREATEST(0, comments_count - 1) WHERE id = p_post_id;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- Ensure users can only modify their own content
-- =============================================================================

-- Enable RLS on all tables
ALTER TABLE posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE post_likes ENABLE ROW LEVEL SECURITY;
ALTER TABLE post_comments ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;

-- Posts policies
CREATE POLICY "Anyone can view posts" ON posts FOR SELECT USING (true);
CREATE POLICY "Users can insert their own posts" ON posts FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update their own posts" ON posts FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete their own posts" ON posts FOR DELETE USING (auth.uid() = user_id);

-- Post likes policies
CREATE POLICY "Anyone can view likes" ON post_likes FOR SELECT USING (true);
CREATE POLICY "Users can insert their own likes" ON post_likes FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can delete their own likes" ON post_likes FOR DELETE USING (auth.uid() = user_id);

-- Post comments policies
CREATE POLICY "Anyone can view comments" ON post_comments FOR SELECT USING (true);
CREATE POLICY "Users can insert their own comments" ON post_comments FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update their own comments" ON post_comments FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete their own comments" ON post_comments FOR DELETE USING (auth.uid() = user_id);

-- Notifications policies
CREATE POLICY "Users can view their own notifications" ON notifications FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "System can insert notifications" ON notifications FOR INSERT WITH CHECK (true);
CREATE POLICY "Users can update their own notifications" ON notifications FOR UPDATE USING (auth.uid() = user_id);

-- =============================================================================
-- Add avatar_url column to users table if it doesn't exist
-- =============================================================================

DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'users' AND column_name = 'avatar_url') THEN
        ALTER TABLE users ADD COLUMN avatar_url TEXT;
    END IF;
END $$;

-- =============================================================================
-- COMMENTS
-- =============================================================================
-- 
-- To run this script:
-- 1. Go to your Supabase dashboard
-- 2. Navigate to SQL Editor
-- 3. Create a new query and paste this script
-- 4. Run the script
--
-- The tables will be created with proper indexes, RLS policies, and helper functions.
-- The backend uses the service key, so RLS policies won't block backend operations.
--
-- =============================================================================
