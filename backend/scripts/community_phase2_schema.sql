-- =============================================================================
-- Community Feature Phase 2 Database Schema for Supabase
-- Additional tables for follows, bookmarks, reports, and enhanced features
-- =============================================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- USER_FOLLOWS TABLE
-- Tracks which users follow which other users
-- =============================================================================

CREATE TABLE IF NOT EXISTS user_follows (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    follower_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    following_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(follower_id, following_id),
    CHECK (follower_id != following_id)  -- Prevent self-follows
);

-- Indexes for user_follows
CREATE INDEX IF NOT EXISTS idx_user_follows_follower ON user_follows(follower_id);
CREATE INDEX IF NOT EXISTS idx_user_follows_following ON user_follows(following_id);

-- =============================================================================
-- BOOKMARKS TABLE
-- Tracks which posts users have bookmarked
-- =============================================================================

CREATE TABLE IF NOT EXISTS bookmarks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    post_id UUID NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, post_id)
);

-- Indexes for bookmarks
CREATE INDEX IF NOT EXISTS idx_bookmarks_user_id ON bookmarks(user_id);
CREATE INDEX IF NOT EXISTS idx_bookmarks_post_id ON bookmarks(post_id);
CREATE INDEX IF NOT EXISTS idx_bookmarks_created_at ON bookmarks(created_at DESC);

-- =============================================================================
-- REPORTS TABLE
-- For reporting inappropriate content
-- =============================================================================

CREATE TABLE IF NOT EXISTS reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    reporter_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    reported_user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    post_id UUID REFERENCES posts(id) ON DELETE CASCADE,
    comment_id UUID REFERENCES post_comments(id) ON DELETE CASCADE,
    reason VARCHAR(100) NOT NULL,  -- 'spam', 'harassment', 'inappropriate', 'other'
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'reviewed', 'resolved', 'dismissed'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    reviewed_by UUID REFERENCES users(id) ON DELETE SET NULL
);

-- Indexes for reports
CREATE INDEX IF NOT EXISTS idx_reports_reporter ON reports(reporter_id);
CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status);
CREATE INDEX IF NOT EXISTS idx_reports_created_at ON reports(created_at DESC);

-- =============================================================================
-- USER_BLOCKS TABLE
-- For blocking other users
-- =============================================================================

CREATE TABLE IF NOT EXISTS user_blocks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    blocker_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    blocked_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(blocker_id, blocked_id),
    CHECK (blocker_id != blocked_id)  -- Prevent self-blocks
);

-- Indexes for user_blocks
CREATE INDEX IF NOT EXISTS idx_user_blocks_blocker ON user_blocks(blocker_id);
CREATE INDEX IF NOT EXISTS idx_user_blocks_blocked ON user_blocks(blocked_id);

-- =============================================================================
-- ADD COLUMNS TO EXISTING TABLES
-- =============================================================================

-- Add parent_id to post_comments for nested replies
ALTER TABLE post_comments ADD COLUMN IF NOT EXISTS parent_id UUID REFERENCES post_comments(id) ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS idx_post_comments_parent_id ON post_comments(parent_id);

-- Add image_url to posts for image uploads
ALTER TABLE posts ADD COLUMN IF NOT EXISTS image_url TEXT;

-- Add bio and followers/following counts to users (if not exists)
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'users' AND column_name = 'bio') THEN
        ALTER TABLE users ADD COLUMN bio TEXT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'users' AND column_name = 'followers_count') THEN
        ALTER TABLE users ADD COLUMN followers_count INTEGER DEFAULT 0;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'users' AND column_name = 'following_count') THEN
        ALTER TABLE users ADD COLUMN following_count INTEGER DEFAULT 0;
    END IF;
END $$;

-- =============================================================================
-- HELPER FUNCTIONS FOR FOLLOW COUNTERS
-- =============================================================================

-- Increment followers count for a user
CREATE OR REPLACE FUNCTION increment_followers_count(p_user_id UUID)
RETURNS VOID AS $$
BEGIN
    UPDATE users SET followers_count = COALESCE(followers_count, 0) + 1 WHERE id = p_user_id;
END;
$$ LANGUAGE plpgsql;

-- Decrement followers count for a user
CREATE OR REPLACE FUNCTION decrement_followers_count(p_user_id UUID)
RETURNS VOID AS $$
BEGIN
    UPDATE users SET followers_count = GREATEST(0, COALESCE(followers_count, 0) - 1) WHERE id = p_user_id;
END;
$$ LANGUAGE plpgsql;

-- Increment following count for a user
CREATE OR REPLACE FUNCTION increment_following_count(p_user_id UUID)
RETURNS VOID AS $$
BEGIN
    UPDATE users SET following_count = COALESCE(following_count, 0) + 1 WHERE id = p_user_id;
END;
$$ LANGUAGE plpgsql;

-- Decrement following count for a user
CREATE OR REPLACE FUNCTION decrement_following_count(p_user_id UUID)
RETURNS VOID AS $$
BEGIN
    UPDATE users SET following_count = GREATEST(0, COALESCE(following_count, 0) - 1) WHERE id = p_user_id;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- FUNCTION TO GET TRENDING POSTS
-- Based on likes + comments in last 24-48 hours with decay
-- =============================================================================

CREATE OR REPLACE FUNCTION get_trending_posts(p_limit INTEGER DEFAULT 20, p_offset INTEGER DEFAULT 0)
RETURNS TABLE (
    id UUID,
    user_id UUID,
    content TEXT,
    sanskrit_text TEXT,
    meter_analysis JSONB,
    image_url TEXT,
    likes_count INTEGER,
    comments_count INTEGER,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    trending_score FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id,
        p.user_id,
        p.content,
        p.sanskrit_text,
        p.meter_analysis,
        p.image_url,
        p.likes_count,
        p.comments_count,
        p.created_at,
        p.updated_at,
        -- Trending score: engagement weighted by recency
        -- Higher weight for recent posts, decays over time
        (
            (COALESCE(p.likes_count, 0) * 2 + COALESCE(p.comments_count, 0) * 3)::FLOAT
            / POWER(EXTRACT(EPOCH FROM (NOW() - p.created_at)) / 3600 + 2, 1.5)
        ) AS trending_score
    FROM posts p
    WHERE p.created_at > NOW() - INTERVAL '7 days'  -- Only consider posts from last 7 days
    ORDER BY trending_score DESC
    LIMIT p_limit
    OFFSET p_offset;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- FULL TEXT SEARCH INDEX FOR POSTS
-- =============================================================================

-- Add a search vector column if it doesn't exist
ALTER TABLE posts ADD COLUMN IF NOT EXISTS search_vector tsvector;

-- Create a function to update search vector
CREATE OR REPLACE FUNCTION posts_search_vector_update() RETURNS trigger AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('simple', COALESCE(NEW.content, '')), 'A') ||
        setweight(to_tsvector('simple', COALESCE(NEW.sanskrit_text, '')), 'B');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for automatic search vector update
DROP TRIGGER IF EXISTS posts_search_vector_trigger ON posts;
CREATE TRIGGER posts_search_vector_trigger
    BEFORE INSERT OR UPDATE ON posts
    FOR EACH ROW
    EXECUTE FUNCTION posts_search_vector_update();

-- Create GIN index for fast text search
CREATE INDEX IF NOT EXISTS idx_posts_search_vector ON posts USING gin(search_vector);

-- Update existing posts with search vectors
UPDATE posts SET search_vector = 
    setweight(to_tsvector('simple', COALESCE(content, '')), 'A') ||
    setweight(to_tsvector('simple', COALESCE(sanskrit_text, '')), 'B')
WHERE search_vector IS NULL;

-- =============================================================================
-- ROW LEVEL SECURITY POLICIES FOR NEW TABLES
-- =============================================================================

-- Enable RLS on new tables
ALTER TABLE user_follows ENABLE ROW LEVEL SECURITY;
ALTER TABLE bookmarks ENABLE ROW LEVEL SECURITY;
ALTER TABLE reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_blocks ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist (for idempotent migrations)
DROP POLICY IF EXISTS "Anyone can view follows" ON user_follows;
DROP POLICY IF EXISTS "Users can insert their own follows" ON user_follows;
DROP POLICY IF EXISTS "Users can delete their own follows" ON user_follows;

DROP POLICY IF EXISTS "Users can view their own bookmarks" ON bookmarks;
DROP POLICY IF EXISTS "Users can insert their own bookmarks" ON bookmarks;
DROP POLICY IF EXISTS "Users can delete their own bookmarks" ON bookmarks;

DROP POLICY IF EXISTS "Users can view their own reports" ON reports;
DROP POLICY IF EXISTS "Users can insert reports" ON reports;

DROP POLICY IF EXISTS "Users can view their own blocks" ON user_blocks;
DROP POLICY IF EXISTS "Users can insert their own blocks" ON user_blocks;
DROP POLICY IF EXISTS "Users can delete their own blocks" ON user_blocks;

-- User follows policies
CREATE POLICY "Anyone can view follows" ON user_follows FOR SELECT USING (true);
CREATE POLICY "Users can insert their own follows" ON user_follows FOR INSERT WITH CHECK (auth.uid() = follower_id);
CREATE POLICY "Users can delete their own follows" ON user_follows FOR DELETE USING (auth.uid() = follower_id);

-- Bookmarks policies
CREATE POLICY "Users can view their own bookmarks" ON bookmarks FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert their own bookmarks" ON bookmarks FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can delete their own bookmarks" ON bookmarks FOR DELETE USING (auth.uid() = user_id);

-- Reports policies
CREATE POLICY "Users can view their own reports" ON reports FOR SELECT USING (auth.uid() = reporter_id);
CREATE POLICY "Users can insert reports" ON reports FOR INSERT WITH CHECK (auth.uid() = reporter_id);
-- Admins can view all reports (handled in backend with service key)

-- User blocks policies
CREATE POLICY "Users can view their own blocks" ON user_blocks FOR SELECT USING (auth.uid() = blocker_id);
CREATE POLICY "Users can insert their own blocks" ON user_blocks FOR INSERT WITH CHECK (auth.uid() = blocker_id);
CREATE POLICY "Users can delete their own blocks" ON user_blocks FOR DELETE USING (auth.uid() = blocker_id);

-- =============================================================================
-- COMMENTS
-- =============================================================================
-- 
-- Phase 2 Schema adds:
-- 1. user_follows - For following system
-- 2. bookmarks - For saving posts
-- 3. reports - For reporting content
-- 4. user_blocks - For blocking users
-- 5. parent_id in comments - For nested replies
-- 6. image_url in posts - For image uploads
-- 7. bio, followers_count, following_count in users
-- 8. Trending posts function
-- 9. Full text search on posts
--
-- To run this script:
-- 1. Go to your Supabase dashboard
-- 2. Navigate to SQL Editor
-- 3. Create a new query and paste this script
-- 4. Run the script
--
-- =============================================================================
