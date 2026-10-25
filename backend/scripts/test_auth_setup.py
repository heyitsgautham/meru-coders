#!/usr/bin/env python3
"""
Quick test script to verify authentication and database setup.
"""

import sys

from backend.config.settings import settings


def test_environment():
    """Test environment variables."""
    print("🔍 Testing Environment Variables...")

    required_vars = ['SUPABASE_URL', 'SUPABASE_ANON_KEY', 'SUPABASE_SERVICE_KEY', 'SECRET_KEY']

    missing = []
    for var in required_vars:
        value = getattr(settings, var, None)
        if not value or value == 'your-secret-key-here-change-in-production':
            missing.append(var)
            print(f"  ❌ {var}: Not set")
        else:
            print(f"  ✅ {var}: Set ({value[:20]}...)")

    if missing:
        print(f"\n⚠️  Missing variables: {', '.join(missing)}")
        print("   Please update backend/.env file")
        return False

    print("✅ All environment variables set\n")
    return True


def test_supabase_connection():
    """Test Supabase connection."""
    print("🔍 Testing Supabase Connection...")

    try:
        from supabase import create_client

        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)

        # Test query
        response = supabase.table('users').select('count', count='exact').execute()
        user_count = response.count

        print("  ✅ Connected to Supabase")
        print(f"  ℹ️  Users in database: {user_count}\n")
        return True

    except Exception as e:
        print(f"  ❌ Connection failed: {str(e)}\n")
        return False


def test_tables_exist():
    """Test that required tables exist."""
    print("🔍 Testing Database Tables...")

    try:
        from supabase import create_client

        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)

        required_tables = ['users', 'verses', 'meter_definitions', 'pending_contributions']

        for table in required_tables:
            try:
                response = supabase.table(table).select('count', count='exact').limit(1).execute()
                print(f"  ✅ Table '{table}' exists (count: {response.count})")
            except Exception as e:
                print(f"  ❌ Table '{table}' missing or inaccessible: {str(e)}")
                return False

        print("✅ All required tables exist\n")
        return True

    except Exception as e:
        print(f"  ❌ Table check failed: {str(e)}\n")
        return False


def test_admin_user():
    """Test if admin user exists."""
    print("🔍 Testing Admin User...")

    try:
        from supabase import create_client

        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)

        # Check for admin user
        response = supabase.table('users').select('*').eq('username', 'admin-erase-sure').execute()

        if response.data and len(response.data) > 0:
            admin = response.data[0]
            if admin.get('is_admin'):
                print("  ✅ Admin user exists and is_admin=true")
                print(f"  ℹ️  Admin ID: {admin['id']}\n")
                return True
            else:
                print("  ⚠️  Admin user exists but is_admin=false")
                print("     Run: UPDATE users SET is_admin=true WHERE username='admin-erase-sure'\n")
                return False
        else:
            print("  ⚠️  Admin user not found")
            print("     Create admin user following AUTH_SETUP.md instructions\n")
            return False

    except Exception as e:
        print(f"  ❌ Admin check failed: {str(e)}\n")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("   AUTHENTICATION & DATABASE SETUP VERIFICATION")
    print("=" * 60)
    print()

    results = []

    results.append(('Environment Variables', test_environment()))
    results.append(('Supabase Connection', test_supabase_connection()))
    results.append(('Database Tables', test_tables_exist()))
    results.append(('Admin User', test_admin_user()))

    print("=" * 60)
    print("   SUMMARY")
    print("=" * 60)

    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False

    print()

    if all_passed:
        print("🎉 All tests passed! Setup is complete.")
        print("\nNext steps:")
        print("  1. Run migration: python backend/scripts/migrate_to_supabase.py")
        print("  2. Start backend: cd backend && python run.py")
        print("  3. Start frontend: cd frontend && npm run dev")
    else:
        print("⚠️  Some tests failed. Please fix the issues above.")
        print("\nRefer to AUTH_SETUP.md for detailed instructions.")

    print()
    sys.exit(0 if all_passed else 1)


if __name__ == '__main__':
    main()
