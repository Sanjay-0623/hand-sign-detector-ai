#!/usr/bin/env python3
"""
Verify that all environment variables and dependencies are correctly configured
Run this before starting the Flask app
"""

import os
import sys

def check_env_file():
    """Check if .env file exists"""
    if os.path.exists('.env'):
        print("✓ .env file found")
        return True
    else:
        print("✗ .env file NOT FOUND")
        print("  → Create a .env file in the project root directory")
        return False

def check_dotenv_installed():
    """Check if python-dotenv is installed"""
    try:
        import dotenv
        print("✓ python-dotenv is installed")
        return True
    except ImportError:
        print("✗ python-dotenv is NOT installed")
        print("  → Run: pip install python-dotenv")
        return False

def check_env_variables():
    """Check if environment variables are set"""
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = {
        'DATABASE_URL': os.environ.get('DATABASE_URL'),
    }
    
    optional_vars = {
        'SECRET_KEY': os.environ.get('SECRET_KEY'),
    }
    
    all_good = True
    
    print("\nRequired Environment Variables:")
    for var, value in required_vars.items():
        if value:
            # Hide sensitive parts
            if 'postgresql://' in value:
                safe_value = value.split('@')[0].split(':')[:2]
                print(f"✓ {var}: postgresql://{safe_value[1]}:***@...")
            else:
                print(f"✓ {var}: {value[:20]}...")
        else:
            print(f"✗ {var}: NOT SET")
            all_good = False
    
    print("\nOptional Environment Variables:")
    for var, value in optional_vars.items():
        if value:
            print(f"✓ {var}: Set")
        else:
            print(f"⚠ {var}: Not set (will use default)")
    
    return all_good

def test_neon_connection():
    """Test connection to Neon PostgreSQL"""
    from dotenv import load_dotenv
    
    load_dotenv()
    
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        print("\n✗ Cannot test Neon connection - DATABASE_URL missing")
        return False
    
    try:
        import psycopg2
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        
        print("\n✓ Neon database connection successful!")
        return True
    except Exception as e:
        print(f"\n✗ Neon connection error: {e}")
        return False

def main():
    print("="*60)
    print("HAND SIGN DETECTOR - SETUP VERIFICATION")
    print("="*60)
    
    checks = []
    
    # Check .env file
    checks.append(check_env_file())
    
    # Check python-dotenv
    checks.append(check_dotenv_installed())
    
    # Check environment variables
    if checks[-1]:  # Only if dotenv is installed
        checks.append(check_env_variables())
        
        # Test Neon connection
        if checks[-1]:  # Only if env vars are set
            checks.append(test_neon_connection())
    
    print("\n" + "="*60)
    if all(checks):
        print("✓ ALL CHECKS PASSED - Ready to run!")
        print("\nYou can now start the Flask app:")
        print("  python app.py")
    else:
        print("✗ SOME CHECKS FAILED - Please fix the issues above")
        print("\nQuick Fix Guide:")
        print("1. Create .env file in project root")
        print("2. Add these lines to .env:")
        print("   DATABASE_URL=postgresql://user:pass@host.neon.tech/db?sslmode=require")
        print("   SECRET_KEY=any-random-string")
        print("3. Run: pip install python-dotenv psycopg2-binary")
        print("4. Run this script again: python verify_setup.py")
    print("="*60)
    
    return all(checks)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
