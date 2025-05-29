#!/usr/bin/env python3
"""
Main Development Test Script

Primary test script for development workflow:
- File existence checks
- Syntax validation  
- Import testing
- Mock system validation

Run this after every code change.
"""

import sys
import os
import subprocess
from pathlib import Path

def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"   ✅ {description} - PASSED")
            return True
        else:
            print(f"   ❌ {description} - FAILED")
            return False
    except subprocess.TimeoutExpired:
        print(f"   ⏰ {description} - TIMEOUT")
        return False
    except Exception as e:
        print(f"   💥 {description} - ERROR: {e}")
        return False

def check_file_exists(filepath, description):
    """Check if a file exists"""
    if Path(filepath).exists():
        print(f"   ✅ {description} - EXISTS")
        return True
    else:
        print(f"   ❌ {description} - MISSING")
        return False

def main():
    """Main development test function"""
    print("🚀 Development Test Suite")
    print("=" * 40)
    
    success_count = 0
    total_checks = 0
    
    # 1. Check critical files exist
    print("\n📁 Checking critical files...")
    critical_files = [
        ('find_leads.py', 'Find Leads function'),
        ('enrich_leads.py', 'Enrich Leads function'), 
        ('test_apis.py', 'Test APIs function'),
        ('main.py', 'Main function router'),
        ('utils/__init__.py', 'Utils package'),
        ('tests/run_tests.py', 'Test runner')
    ]
    
    for filepath, description in critical_files:
        if check_file_exists(filepath, description):
            success_count += 1
        total_checks += 1
    
    # 2. Basic syntax check
    print("\n🔍 Checking Python syntax...")
    python_files = [
        'find_leads.py',
        'enrich_leads.py',
        'test_apis.py', 
        'main.py'
    ]
    
    for py_file in python_files:
        if Path(py_file).exists():
            if run_command(f"python -m py_compile {py_file}", f"Syntax check: {py_file}"):
                success_count += 1
            total_checks += 1
    
    # 3. Test imports
    print("\n📦 Testing imports...")
    test_imports = [
        ("from tests.mocks import MockApolloClient", "Mock Apollo Client"),
        ("from tests.mocks import MockPerplexityClient", "Mock Perplexity Client"),
        ("from tests.base_test import BaseTestCase", "Base Test Case"),
    ]
    
    for import_cmd, description in test_imports:
        if run_command(f"python -c \"{import_cmd}\"", f"Import test: {description}"):
            success_count += 1
        total_checks += 1
    
    # 4. Run mock tests
    print("\n🎭 Running mock test suite...")
    if run_command("python tests/run_tests.py mock", "Mock test suite"):
        success_count += 1
    total_checks += 1
    
    # Summary
    print("\n" + "=" * 40)
    print("📊 DEVELOPMENT TEST SUMMARY")
    print("=" * 40)
    
    success_rate = (success_count / total_checks * 100) if total_checks > 0 else 0
    
    print(f"✅ Passed:      {success_count}/{total_checks}")
    print(f"📈 Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("🎉 SYSTEM READY FOR DEVELOPMENT!")
        print(f"\n💡 Run 'python tests/run_tests.py mock' for mock tests only")
        print(f"💡 Run 'python tests/run_tests.py full' for complete test suite")
        exit_code = 0
    else:
        print("❌ SYSTEM HAS ISSUES - CHECK FAILURES ABOVE")
        exit_code = 1
    
    print("=" * 40)
    return exit_code

if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️  Development test interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Development test error: {e}")
        sys.exit(1) 