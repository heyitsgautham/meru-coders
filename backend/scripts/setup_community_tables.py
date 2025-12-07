#!/usr/bin/env python3
"""
Script to create community tables in Supabase using the REST API.
Run this once to set up the database schema.
"""

import sys
sys.path.insert(0, '/home/harevasu/Projects/meru-coders')

from supabase import create_client

# Supabase credentials
SUPABASE_URL = 'https://qogojsxaoevcalqvdpof.supabase.co'
SUPABASE_SERVICE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFvZ29qc3hhb2V2Y2FscXZkcG9mIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NDk2MTcxMSwiZXhwIjoyMDgwNTM3NzExfQ.76h1iXzABb0wvcW49D_mAYYMRWvmm6FYvwR8jiOYniQ'

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def test_connection():
    """Test the Supabase connection"""
    try:
        result = supabase.table('users').select('id').limit(1).execute()
        print("✅ Connected to Supabase successfully!")
        print(f"   Users found: {len(result.data) if result.data else 0}")
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


def main():
    print("=" * 60)
    print("Community Tables Setup Script")
    print("=" * 60)
    print()
    
    # Test connection
    if not test_connection():
        print("\nPlease check your Supabase credentials and try again.")
        return
    
    print()
    print("=" * 60)
    print("IMPORTANT: Run the following SQL in Supabase SQL Editor")
    print("=" * 60)
    print()
    print("1. Go to: https://supabase.com/dashboard/project/qogojsxaoevcalqvdpof/sql")
    print("2. Create a new query")
    print("3. Paste the contents of: backend/scripts/community_schema.sql")
    print("4. Click 'Run' to execute")
    print()
    print("The schema file location:")
    print("  /home/harevasu/Projects/meru-coders/backend/scripts/community_schema.sql")
    print()
    
    # Print simplified SQL for quick copy
    print("=" * 60)
    print("QUICK SQL (Copy this to Supabase SQL Editor):")
    print("=" * 60)
    print("""
-- Posts table
CREATE TABLE IF NOT EXISTS posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    sanskrit_text TEXT,
    meter_analysis JSONB,
    likes_count INTEGER DEFAULT 0,
    comments_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

-- Post likes table
CREATE TABLE IF NOT EXISTS post_likes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    post_id UUID NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(post_id, user_id)
);

-- Post comments table  
CREATE TABLE IF NOT EXISTS post_comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    post_id UUID NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

-- Notifications table (for Phase 2)
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    actor_id UUID REFERENCES users(id) ON DELETE SET NULL,
    post_id UUID REFERENCES posts(id) ON DELETE CASCADE,
    comment_id UUID REFERENCES post_comments(id) ON DELETE CASCADE,
    content TEXT,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_posts_user_id ON posts(user_id);
CREATE INDEX IF NOT EXISTS idx_posts_created_at ON posts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_post_likes_post_id ON post_likes(post_id);
CREATE INDEX IF NOT EXISTS idx_post_likes_user_id ON post_likes(user_id);
CREATE INDEX IF NOT EXISTS idx_post_comments_post_id ON post_comments(post_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);

-- Helper functions for counters
CREATE OR REPLACE FUNCTION increment_likes_count(p_post_id UUID)
RETURNS VOID AS $$
BEGIN
    UPDATE posts SET likes_count = likes_count + 1 WHERE id = p_post_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION decrement_likes_count(p_post_id UUID)
RETURNS VOID AS $$
BEGIN
    UPDATE posts SET likes_count = GREATEST(0, likes_count - 1) WHERE id = p_post_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION increment_comments_count(p_post_id UUID)
RETURNS VOID AS $$
BEGIN
    UPDATE posts SET comments_count = comments_count + 1 WHERE id = p_post_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION decrement_comments_count(p_post_id UUID)
RETURNS VOID AS $$
BEGIN
    UPDATE posts SET comments_count = GREATEST(0, comments_count - 1) WHERE id = p_post_id;
END;
$$ LANGUAGE plpgsql;

-- Add avatar_url to users if not exists
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'users' AND column_name = 'avatar_url') THEN
        ALTER TABLE users ADD COLUMN avatar_url TEXT;
    END IF;
END $$;

SELECT 'Community tables created successfully!' as status;
""")

if __name__ == "__main__":
    main()
