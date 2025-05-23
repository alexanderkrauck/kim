#!/usr/bin/env python3
"""
Quick Test Script

Run this script after every code change to ensure basic functionality.
This is a lightweight alternative to the full test suite for rapid development.
"""

import sys
import os
import subprocess
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"   ✅ {description} - PASSED")
            return True
        else:
            print(f"   ❌ {description} - FAILED")
            if result.stderr:
                print(f"   Error: {result.stderr.strip()}")
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

def remove_outdated_files():
    """Remove outdated files as requested in custom instructions"""
    outdated_files = [
        'experiments/api_testing.ipynb',
        'experiments/apollo_api_testing_updated.ipynb'
    ]
    
    removed_count = 0
    for file_path in outdated_files:
        if Path(file_path).exists():
            try:
                os.remove(file_path)
                print(f"   🗑️  Removed outdated file: {file_path}")
                removed_count += 1
            except Exception as e:
                print(f"   ❌ Failed to remove {file_path}: {e}")
    
    if removed_count > 0:
        print(f"   ✅ Cleaned up {removed_count} outdated files")
    else:
        print(f"   ✅ No outdated files to remove")

def check_todo_tags():
    """Check for TODO tags in the codebase"""
    print("🔍 Checking for TODO tags...")
    
    # Find TODO and FIXME comments
    cmd = "find . -name '*.py' -not -path './venv/*' -not -path './.git/*' -exec grep -Hn 'TODO\\|FIXME' {} \\; | head -10"
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.stdout.strip():
            print("   ⚠️  Found TODO/FIXME tags:")
            for line in result.stdout.strip().split('\n')[:5]:  # Show first 5
                print(f"      {line}")
            if len(result.stdout.strip().split('\n')) > 5:
                print(f"      ... and {len(result.stdout.strip().split('\n')) - 5} more")
        else:
            print("   ✅ No TODO/FIXME tags found")
    except Exception as e:
        print(f"   ❌ Error checking TODO tags: {e}")

def main():
    """Main quick test function"""
    print("🚀 Quick Test Suite")
    print("=" * 50)
    
    # Track overall success
    success_count = 0
    total_checks = 0
    
    # 1. Remove outdated files (as per custom instructions)
    print("\n🗑️  Cleaning up outdated files...")
    remove_outdated_files()
    
    # 2. Check critical files exist
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
    
    # 3. Basic syntax check
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
    
    # 4. Quick import test
    print("\n📦 Testing imports...")
    
    # Test that critical modules can be imported
    test_imports = [
        ("from tests.mocks import MockApolloClient", "Mock Apollo Client"),
        ("from tests.mocks import MockPerplexityClient", "Mock Perplexity Client"),
        ("from tests.base_test import BaseTestCase", "Base Test Case"),
    ]
    
    for import_cmd, description in test_imports:
        if run_command(f"python -c \"{import_cmd}\"", f"Import test: {description}"):
            success_count += 1
        total_checks += 1
    
    # 5. Run a few critical tests
    print("\n🧪 Running critical tests...")
    
    critical_tests = [
        ("python tests/run_tests.py --modules tests.test_find_leads -q", "Find Leads Tests"),
        ("python tests/run_tests.py --modules tests.test_enrich_leads -q", "Enrich Leads Tests"),
    ]
    
    for test_cmd, description in critical_tests:
        if run_command(test_cmd, description):
            success_count += 1
        total_checks += 1
    
    # 6. Check for TODO tags
    check_todo_tags()
    
    # 7. Check if system runs
    print("\n🏃 Testing basic system functionality...")
    if run_command("python -c \"from test_apis import validate_api_keys; print('System can run basic functions')\"", "Basic system test"):
        success_count += 1
    total_checks += 1
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 QUICK TEST SUMMARY")
    print("=" * 50)
    
    success_rate = (success_count / total_checks * 100) if total_checks > 0 else 0
    
    print(f"✅ Passed:      {success_count}/{total_checks}")
    print(f"📈 Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("🎉 SYSTEM READY FOR DEVELOPMENT!")
        exit_code = 0
    else:
        print("❌ SYSTEM HAS ISSUES - CHECK FAILURES ABOVE")
        exit_code = 1
    
    print("=" * 50)
    
    if exit_code == 0:
        print("\n💡 To run full test suite: python tests/run_tests.py")
        print("💡 To run specific tests: python tests/run_tests.py -p \"test_name\"")
    
    return exit_code

if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️  Quick test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Quick test error: {e}")
        sys.exit(1) 