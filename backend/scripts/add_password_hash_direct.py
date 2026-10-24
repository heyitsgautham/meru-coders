#!/usr/bin/env python3
"""
Direct SQL migration to add password_hash column using psycopg2.
This bypasses the supabase-py library incompatibility.
"""

import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

# Load environment variables
from dotenv import load_dotenv

load_dotenv(backend_path / '.env')

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("❌ ERROR: Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in .env")
    sys.exit(1)

# Extract database connection string
# Supabase URL format: https://xxxxx.supabase.co
# Database URL format: postgresql://postgres:[PASSWORD]@db.xxxxx.supabase.co:5432/postgres?sslmode=require

project_ref = SUPABASE_URL.replace('https://', '').replace('.supabase.co', '')

# Try to get database password from environment or use service key
db_password = os.getenv('SUPABASE_DB_PASSWORD') or os.getenv('DB_PASSWORD')

if not db_password:
    print("❌ ERROR: Need SUPABASE_DB_PASSWORD in .env file")
    print("   Get it from: Supabase Dashboard → Settings → Database → Connection string")
    sys.exit(1)

DB_URL = f"postgresql://postgres:{db_password}@db.{project_ref}.supabase.co:5432/postgres?sslmode=require"

print("=" * 70)
print("🔧 Adding password_hash column to users table")
print("=" * 70)

try:
    import psycopg2
except ImportError:
    print("❌ psycopg2 not installed. Installing...")
    os.system("pip install psycopg2-binary")
    import psycopg2

try:
    # Connect to database
    print("📡 Connecting to database...")
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()

    # Add password_hash column
    print("📝 Adding password_hash column...")
    cursor.execute("""
        ALTER TABLE users 
        ADD COLUMN IF NOT EXISTS password_hash TEXT;
    """)

    # Create index on username
    print("📝 Creating index on username...")
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_username 
        ON users(username);
    """)

    # Commit changes
    conn.commit()

    # Verify column exists
    print("✅ Verifying column...")
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'users' 
        AND column_name = 'password_hash';
    """)

    result = cursor.fetchone()
    if result:
        print(f"✅ SUCCESS! Column 'password_hash' exists with type '{result[1]}'")
    else:
        print("⚠️  WARNING: Could not verify column creation")

    cursor.close()
    conn.close()

    print("=" * 70)
    print("✅ Migration completed successfully!")
    print("=" * 70)

except Exception as e:
    print(f"❌ ERROR: {e}")
    print("\nTroubleshooting:")
    print("1. Check your .env file has SUPABASE_DB_PASSWORD")
    print("2. Get password from: Supabase Dashboard → Settings → Database")
    print("3. Or run SQL manually in Supabase SQL Editor")
    sys.exit(1)
