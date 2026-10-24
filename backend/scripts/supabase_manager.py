#!/usr/bin/env python3
"""
Supabase Manager CLI
Manage your Supabase database without the Supabase CLI
Uses REST API with credentials from backend/.env
"""

import os
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir.parent))

import argparse
import json

from dotenv import load_dotenv
from supabase import Client, create_client
from tabulate import tabulate

# Load environment variables
env_path = backend_dir / '.env'
load_dotenv(env_path)

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("❌ Error: SUPABASE_URL or SUPABASE_SERVICE_KEY not found in backend/.env")
    sys.exit(1)

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def list_tables():
    """List all tables in the database"""
    print("\n📋 Fetching tables from Supabase...\n")

    # Common tables we expect
    tables = ['users', 'pending_contributions', 'approved_contributions']

    for table_name in tables:
        try:
            result = supabase.table(table_name).select('*', count='exact').limit(0).execute()
            count = result.count if hasattr(result, 'count') else 'N/A'
            print(f"✓ {table_name}: {count} rows")
        except Exception as e:
            print(f"✗ {table_name}: {str(e)}")


def view_table(table_name, limit=10):
    """View records from a table"""
    print(f"\n📊 Viewing {table_name} (limit: {limit})...\n")

    try:
        result = supabase.table(table_name).select('*').limit(limit).execute()

        if not result.data:
            print(f"No records found in {table_name}")
            return

        # Pretty print as table
        if result.data:
            headers = result.data[0].keys()
            rows = [list(record.values()) for record in result.data]
            print(tabulate(rows, headers=headers, tablefmt='grid'))
            print(f"\nShowing {len(result.data)} records")

    except Exception as e:
        print(f"❌ Error: {str(e)}")


def count_table(table_name):
    """Count records in a table"""
    try:
        result = supabase.table(table_name).select('*', count='exact').limit(0).execute()
        count = result.count if hasattr(result, 'count') else 'Unknown'
        print(f"\n📊 {table_name}: {count} total records")
    except Exception as e:
        print(f"❌ Error: {str(e)}")


def query_table(table_name, column, value):
    """Query table by column value"""
    print(f"\n🔍 Querying {table_name} WHERE {column} = '{value}'...\n")

    try:
        result = supabase.table(table_name).select('*').eq(column, value).execute()

        if not result.data:
            print("No records found")
            return

        print(json.dumps(result.data, indent=2))

    except Exception as e:
        print(f"❌ Error: {str(e)}")


def create_user(username, password, is_admin=False):
    """Create a new user"""
    import uuid

    import bcrypt

    print(f"\n➕ Creating user: {username}...")

    try:
        # Check if username exists
        existing = supabase.table('users').select('id').eq('username', username).execute()
        if existing.data:
            print(f"❌ Username '{username}' already exists")
            return

        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Create user
        user_data = {
            'id': str(uuid.uuid4()),
            'username': username,
            'password_hash': password_hash,
            'is_admin': is_admin
        }

        result = supabase.table('users').insert(user_data).execute()

        if result.data:
            print("✓ User created successfully!")
            print(f"  ID: {result.data[0]['id']}")
            print(f"  Username: {result.data[0]['username']}")
            print(f"  Admin: {result.data[0]['is_admin']}")
        else:
            print("❌ Failed to create user")

    except Exception as e:
        print(f"❌ Error: {str(e)}")


def delete_user(username):
    """Delete a user by username"""
    print(f"\n🗑️  Deleting user: {username}...")

    try:
        result = supabase.table('users').delete().eq('username', username).execute()

        if result.data:
            print(f"✓ User '{username}' deleted successfully")
        else:
            print(f"❌ User '{username}' not found")

    except Exception as e:
        print(f"❌ Error: {str(e)}")


def setup_oauth(provider='google'):
    """Check OAuth provider configuration"""
    print(f"\n🔑 Checking {provider.upper()} OAuth configuration...\n")
    print("To enable OAuth in Supabase:")
    print(f"1. Go to: {SUPABASE_URL.replace('https://', 'https://app.supabase.com/project/')}/auth/providers")
    print(f"2. Enable {provider.capitalize()} provider")
    print("3. Add OAuth credentials (Client ID, Secret)")
    print("4. Add redirect URL: http://localhost:5173/oauth/callback")
    print("\n✓ Your backend OAuth endpoints are already configured:")
    print("  - POST /api/auth/oauth/start")
    print("  - POST /api/auth/oauth/exchange")


def main():
    parser = argparse.ArgumentParser(
        description='Supabase Manager - Manage your database from CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s list                              # List all tables
  %(prog)s view users                        # View users table
  %(prog)s view pending_contributions -n 20  # View 20 contributions
  %(prog)s count users                       # Count users
  %(prog)s query users username john         # Find user by username
  %(prog)s create-user alice password123     # Create regular user
  %(prog)s create-user bob secret --admin    # Create admin user
  %(prog)s delete-user alice                 # Delete user
  %(prog)s oauth-setup google                # Check OAuth setup
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # List tables
    subparsers.add_parser('list', help='List all tables with row counts')

    # View table
    view_parser = subparsers.add_parser('view', help='View records from a table')
    view_parser.add_argument('table', help='Table name')
    view_parser.add_argument('-n', '--limit', type=int, default=10, help='Number of records (default: 10)')

    # Count table
    count_parser = subparsers.add_parser('count', help='Count records in a table')
    count_parser.add_argument('table', help='Table name')

    # Query table
    query_parser = subparsers.add_parser('query', help='Query table by column value')
    query_parser.add_argument('table', help='Table name')
    query_parser.add_argument('column', help='Column name')
    query_parser.add_argument('value', help='Value to search for')

    # Create user
    create_parser = subparsers.add_parser('create-user', help='Create a new user')
    create_parser.add_argument('username', help='Username')
    create_parser.add_argument('password', help='Password')
    create_parser.add_argument('--admin', action='store_true', help='Create as admin')

    # Delete user
    delete_parser = subparsers.add_parser('delete-user', help='Delete a user')
    delete_parser.add_argument('username', help='Username to delete')

    # OAuth setup
    oauth_parser = subparsers.add_parser('oauth-setup', help='Check OAuth configuration')
    oauth_parser.add_argument('provider', nargs='?', default='google', help='OAuth provider (default: google)')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Execute command
    if args.command == 'list':
        list_tables()
    elif args.command == 'view':
        view_table(args.table, args.limit)
    elif args.command == 'count':
        count_table(args.table)
    elif args.command == 'query':
        query_table(args.table, args.column, args.value)
    elif args.command == 'create-user':
        create_user(args.username, args.password, args.admin)
    elif args.command == 'delete-user':
        delete_user(args.username)
    elif args.command == 'oauth-setup':
        setup_oauth(args.provider)


if __name__ == '__main__':
    main()
