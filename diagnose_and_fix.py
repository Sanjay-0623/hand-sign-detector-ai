#!/usr/bin/env python3
"""
Comprehensive diagnostic tool for Hand Sign Detector database configuration
Run this to identify and fix database connection issues with Neon
"""

import os
import sys
from pathlib import Path

def print_header(text):
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def print_success(text):
    print(f"✓ {text}")

def print_error(text):
    print(f"✗ {text}")

def print_warning(text):
    print(f"⚠ {text}")

def check_python_version():
    print_header("1. Checking Python Version")
    version = sys.version_info
    print(f"Python {version.major}.{version.minor}.{version.micro}")
    if version.major >= 3 and version.minor >= 7:
        print_success("Python version is compatible")
        return True
    else:
        print_error("Python 3.7+ required")
        return False

def check_dotenv_installed():
    print_header("2. Checking python-dotenv Package")
    try:
        import dotenv
        print_success("python-dotenv is installed")
        return True
    except ImportError:
        print_error("python-dotenv is NOT installed")
        print("\nTo fix, run:")
        print("  pip install python-dotenv")
        return False

def check_env_file():
    print_header("3. Checking .env File")
    
    # Check if .env exists
    env_path = Path('.env')
    if not env_path.exists():
        print_error(".env file does NOT exist")
        print("\nTo fix:")
        print("  1. Create a file named '.env' in the project root")
        print("  2. Add your Neon credentials:")
        print("\nExample .env file content:")
        print("-" * 40)
        print("DATABASE_URL=postgresql://user:pass@host.neon.tech/db?sslmode=require")
        print("SECRET_KEY=your-secret-key")
        print("-" * 40)
        return False
    
    print_success(".env file exists")
    
    # Check file location
    abs_path = env_path.resolve()
    print(f"Location: {abs_path}")
    
    # Check file is not empty
    content = env_path.read_text()
    if not content.strip():
        print_error(".env file is EMPTY")
        return False
    
    print_success(".env file has content")
    
    # Check for required variables
    lines = content.strip().split('\n')
    required_vars = ['DATABASE_URL', 'SECRET_KEY']
    found_vars = {}
    
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            if '=' in line:
                key = line.split('=')[0].strip()
                value = line.split('=', 1)[1].strip()
                found_vars[key] = value
    
    print("\nVariables found in .env:")
    all_found = True
    for var in required_vars:
        if var in found_vars:
            # Hide sensitive info
            if var == 'DATABASE_URL':
                print_success(f"{var} = postgresql://...***")
            else:
                value_preview = found_vars[var][:10] + "..." if len(found_vars[var]) > 10 else found_vars[var]
                print_success(f"{var} = {value_preview}")
        else:
            print_error(f"{var} is MISSING")
            all_found = False
    
    if not all_found:
        print("\nPlease add missing variables to .env file")
        return False
    
    return True

def check_env_loading():
    print_header("4. Testing Environment Variable Loading")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print_success("load_dotenv() executed successfully")
    except Exception as e:
        print_error(f"Failed to load .env: {e}")
        return False
    
    # Check if variables are accessible
    required_vars = {
        'DATABASE_URL': os.getenv('DATABASE_URL'),
        'SECRET_KEY': os.getenv('SECRET_KEY')
    }
    
    print("\nEnvironment variables loaded:")
    all_loaded = True
    for var_name, var_value in required_vars.items():
        if var_value:
            if var_name == 'DATABASE_URL':
                print_success(f"{var_name} = postgresql://...***")
            else:
                value_preview = var_value[:10] + "..." if len(var_value) > 10 else var_value
                print_success(f"{var_name} = {value_preview}")
        else:
            print_error(f"{var_name} is NOT loaded")
            all_loaded = False
    
    return all_loaded

def check_neon_connection():
    print_header("5. Testing Neon Database Connection")
    
    try:
        import psycopg2
        from dotenv import load_dotenv
        
        load_dotenv()
        
        url = os.getenv('DATABASE_URL')
        
        if not url:
            print_error("Cannot test connection - DATABASE_URL not loaded")
            return False
        
        print(f"Connecting to Neon PostgreSQL...")
        conn = psycopg2.connect(url)
        cursor = conn.cursor()
        
        # Try a simple query
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        
        # Check tables
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name IN ('users', 'training_data')
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        print_success("Successfully connected to Neon!")
        print_success(f"PostgreSQL {version.split()[1]}")
        
        if 'users' in tables:
            print_success("'users' table exists")
        else:
            print_warning("'users' table not found")
            
        if 'training_data' in tables:
            print_success("'training_data' table exists")
        else:
            print_warning("'training_data' table not found")
        
        return True
        
    except Exception as e:
        print_error(f"Connection failed: {str(e)}")
        print("\nPossible issues:")
        print("  - Invalid DATABASE_URL")
        print("  - Network connection problem")
        print("  - Missing ?sslmode=require in connection string")
        return False

def main():
    print("\n" + "="*60)
    print("  HAND SIGN DETECTOR - DATABASE DIAGNOSTIC TOOL")
    print("="*60)
    
    checks = [
        check_python_version(),
        check_dotenv_installed(),
        check_env_file(),
        check_env_loading(),
        check_neon_connection()
    ]
    
    print_header("DIAGNOSTIC SUMMARY")
    
    if all(checks):
        print_success("ALL CHECKS PASSED!")
        print("\nYour database is configured correctly.")
        print("\nNext steps:")
        print("  1. Make sure Flask server is stopped (Ctrl+C)")
        print("  2. Start Flask server: python app.py")
        print("  3. Open browser: http://localhost:5000")
        print("\nThe 'Database not configured' error should be gone.")
    else:
        print_error("SOME CHECKS FAILED")
        print("\nPlease fix the issues above and run this script again:")
        print("  python diagnose_and_fix.py")
    
    print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    main()
