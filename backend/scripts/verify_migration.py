#!/usr/bin/env python3
"""Verify Phase 2 database migration was successful."""

import sys
sys.path.insert(0, '/home/harevasu/Projects/meru-coders/backend')

from config.supabase_client import get_supabase_client

def main():
    supabase = get_supabase_client()

    print("=== Phase 2 Migration Verification ===")
    print()

    all_ok = True

    # Check tables
    tables = ["user_follows", "bookmarks", "reports", "user_blocks"]
    for t in tables:
        try:
            supabase.table(t).select("id").limit(1).execute()
            print(f"✅ Table {t}: OK")
        except Exception as e:
            print(f"❌ Table {t}: MISSING")
            all_ok = False

    # Check user columns
    try:
        supabase.table("users").select("bio, followers_count, following_count").limit(1).execute()
        print("✅ User columns (bio, followers_count, following_count): OK")
    except Exception as e:
        print(f"❌ User columns: MISSING")
        all_ok = False

    # Check post columns  
    try:
        supabase.table("posts").select("image_url").limit(1).execute()
        print("✅ Post column (image_url): OK")
    except Exception as e:
        print(f"❌ Post column image_url: MISSING")
        all_ok = False

    # Check comment parent_id
    try:
        supabase.table("post_comments").select("parent_id").limit(1).execute()
        print("✅ Comment column (parent_id): OK")
    except Exception as e:
        print(f"❌ Comment parent_id: MISSING")
        all_ok = False

    print()
    if all_ok:
        print("🎉 Migration Successful! All Phase 2 tables and columns exist.")
    else:
        print("⚠️  Migration Incomplete. Please run the SQL schema in Supabase.")

if __name__ == "__main__":
    main()
