#!/usr/bin/env python3
"""
Direct PostgreSQL connection to create community tables in Supabase.
"""

import os
import sys

import psycopg2
from dotenv import load_dotenv
from psycopg2 import sql

# Supabase PostgreSQL connection details, read from the environment.
# Direct connection (not pooler), for example db.<project-ref>.supabase.co
load_dotenv()
DB_HOST = os.environ.get("SUPABASE_DB_HOST", "")
DB_PORT = int(os.environ.get("SUPABASE_DB_PORT", "5432"))
DB_NAME = os.environ.get("SUPABASE_DB_NAME", "postgres")
DB_USER = os.environ.get("SUPABASE_DB_USER", "postgres")
DB_PASSWORD = os.environ.get("SUPABASE_DB_PASSWORD", "")
if not DB_HOST or not DB_PASSWORD:
    sys.exit("Set SUPABASE_DB_HOST and SUPABASE_DB_PASSWORD before running this script.")

# SQL statements to create tables
CREATE_TABLES_SQL = """
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
"""

CREATE_INDEXES_SQL = """
-- Indexes
CREATE INDEX IF NOT EXISTS idx_posts_user_id ON posts(user_id);
CREATE INDEX IF NOT EXISTS idx_posts_created_at ON posts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_post_likes_post_id ON post_likes(post_id);
CREATE INDEX IF NOT EXISTS idx_post_likes_user_id ON post_likes(user_id);
CREATE INDEX IF NOT EXISTS idx_post_comments_post_id ON post_comments(post_id);
CREATE INDEX IF NOT EXISTS idx_post_comments_user_id ON post_comments(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(user_id, is_read);
"""

CREATE_FUNCTIONS_SQL = """
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
"""

ADD_AVATAR_COLUMN_SQL = """
-- Add avatar_url to users if not exists
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'users' AND column_name = 'avatar_url') THEN
        ALTER TABLE users ADD COLUMN avatar_url TEXT;
    END IF;
END $$;
"""

def main():
    print("=" * 60)
    print("Community Tables Creation - Direct PostgreSQL Connection")
    print("=" * 60)
    print()
    
    try:
        # Connect to database
        print(f"Connecting to Supabase PostgreSQL...")
        print(f"  Host: {DB_HOST}")
        print(f"  Port: {DB_PORT}")
        print(f"  Database: {DB_NAME}")
        print()
        
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            sslmode='require'
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("✅ Connected to Supabase PostgreSQL!")
        print()
        
        # Create tables
        print("Creating tables...")
        cursor.execute(CREATE_TABLES_SQL)
        print("✅ Tables created (posts, post_likes, post_comments, notifications)")
        
        # Create indexes
        print("Creating indexes...")
        cursor.execute(CREATE_INDEXES_SQL)
        print("✅ Indexes created")
        
        # Create helper functions
        print("Creating helper functions...")
        cursor.execute(CREATE_FUNCTIONS_SQL)
        print("✅ Helper functions created")
        
        # Add avatar_url column to users
        print("Adding avatar_url column to users table...")
        cursor.execute(ADD_AVATAR_COLUMN_SQL)
        print("✅ Avatar column added (if not exists)")
        
        # Verify tables exist
        print()
        print("Verifying tables...")
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('posts', 'post_likes', 'post_comments', 'notifications')
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        print(f"✅ Verified {len(tables)} community tables:")
        for table in tables:
            print(f"   - {table[0]}")
        
        # Close connection
        cursor.close()
        conn.close()
        
        print()
        print("=" * 60)
        print("✅ ALL COMMUNITY TABLES CREATED SUCCESSFULLY!")
        print("=" * 60)
        print()
        print("You can now:")
        print("1. Start the backend: cd backend && python run.py")
        print("2. Start the frontend: cd frontend && npm run dev")
        print("3. Visit /community to see the community page")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print()
        print("If connection failed, you may need to:")
        print("1. Check your Supabase database password in .env")
        print("2. Enable database access in Supabase dashboard")
        print("3. Or run the SQL manually in Supabase SQL Editor")
        raise

if __name__ == "__main__":
    main()
