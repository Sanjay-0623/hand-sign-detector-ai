// <CHANGE> Updated to test Neon PostgreSQL connection instead of Supabase
"""
Test script to verify .env file loading and Neon database connection
Run this with: python test_db_connection.py
"""

import os
import sys

print("=" * 60)
print("DATABASE CONNECTION TEST - NEON")
print("=" * 60)

# Step 1: Check if python-dotenv is installed
print("\n1. Checking python-dotenv installation...")
try:
    from dotenv import load_dotenv
    print("   ✓ python-dotenv is installed")
except ImportError:
    print("   ✗ python-dotenv is NOT installed")
    print("   → Run: pip install python-dotenv")
    sys.exit(1)

# Step 2: Load .env file
print("\n2. Loading .env file...")
load_dotenv()
print("   ✓ load_dotenv() executed")

# Step 3: Check if environment variables are loaded
print("\n3. Checking environment variables...")
database_url = os.environ.get('DATABASE_URL')
secret_key = os.environ.get('SECRET_KEY')

if database_url:
    # Hide password in output
    safe_url = database_url.split('@')[0].split(':')[0:2]
    print(f"   ✓ DATABASE_URL: postgresql://{safe_url[1]}:***@...")
else:
    print("   ✗ DATABASE_URL: NOT FOUND")
    print("   → Add DATABASE_URL to your .env file")

if secret_key:
    print(f"   ✓ SECRET_KEY: {secret_key[:10]}...")
else:
    print("   ✗ SECRET_KEY: NOT FOUND")

# Step 4: Test Neon PostgreSQL connection
if database_url:
    print("\n4. Testing Neon database connection...")
    try:
        import psycopg2
        
        # Test connection
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Test query
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        print(f"   ✓ Successfully connected to Neon!")
        print(f"   ✓ PostgreSQL version: {version.split()[0]} {version.split()[1]}")
        
        # Check if tables exist
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('users', 'training_data')
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        if 'users' in tables:
            print("   ✓ 'users' table exists")
        else:
            print("   ⚠ 'users' table not found")
            
        if 'training_data' in tables:
            print("   ✓ 'training_data' table exists")
        else:
            print("   ⚠ 'training_data' table not found")
        
        cursor.close()
        conn.close()
            
    except Exception as e:
        print(f"   ✗ Connection error: {str(e)}")
        print("   → Check your DATABASE_URL is correct")
        print("   → Ensure it includes ?sslmode=require")
else:
    print("\n4. Skipping connection test (DATABASE_URL not set)")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
