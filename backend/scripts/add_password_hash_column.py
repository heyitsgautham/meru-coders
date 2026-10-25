#!/usr/bin/env python3
"""
Add password_hash column to users table for bcrypt authentication.
Run this script to update the database schema.
"""

import os
import sys

from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env")
    sys.exit(1)

print("=" * 70)
print("🔧 Adding password_hash column to users table")
print("=" * 70)

# Initialize Supabase client with service role key (admin access)
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

try:
    # Execute the SQL migration
    sql = """
    -- Add password_hash column to users table for bcrypt authentication
    ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash TEXT;
    
    -- Add index for faster username lookups
    CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
    """

    # Supabase Python client doesn't support direct SQL execution
    # We need to use the REST API or run this in Supabase SQL editor
    print("\n⚠️  Please run the following SQL in Supabase SQL Editor:")
    print("\n" + "=" * 70)
    print(sql)
    print("=" * 70)
    print("\n📍 Go to: https://supabase.com/dashboard/project/_/sql/new")
    print("📝 Copy and paste the SQL above")
    print("▶️  Click 'Run' to execute")
    print("\n✅ After running, your users table will have the password_hash column")

except Exception as e:
    print(f"\n❌ Error: {e}")
    sys.exit(1)
