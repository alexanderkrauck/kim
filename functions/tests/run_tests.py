#!/usr/bin/env python3
"""
Simple Test Runner for Firebase Functions

Two test modes only:
- mock: Run tests that use mocks (fast, no external dependencies)
- full: Run all tests including Firebase Functions (requires proper setup)
"""

import unittest
import sys
import os
import argparse
from io import StringIO
import json
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class SimpleTestResult(unittest.TestResult):
    """Simple test result tracking"""
    
    def __init__(self):
        super().__init__()
        self.tests_run = 0
        self.successes = []
        self.failures = []
        self.errors = []
        self.skipped = []
        self.start_time = datetime.now()
        self.end_time = None
    
    def startTest(self, test):
        super().startTest(test)
        self.tests_run += 1
        print(f"  Running: {test._testMethodName}")
    
    def addSuccess(self, test):
        super().addSuccess(test)
        self.successes.append(test)
        print(f"    ✅ PASS")
    
    def addError(self, test, err):
        super().addError(test, err)
        self.errors.append((test, err))
        print(f"    ❌ ERROR: {test._testMethodName}")
    
    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.failures.append((test, err))
        print(f"    ❌ FAIL: {test._testMethodName}")
    
    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.skipped.append((test, reason))
        print(f"    ⏭️  SKIP: {test._testMethodName}")


def run_mock_tests():
    """Run tests that use mocks only (fast, no external dependencies)"""
    
    print("🎭 Running Mock Tests")
    print("=" * 50)
    
    # Only run utility tests and mock-specific tests
    test_modules = [
        'tests.test_utils'  # All utility and mock tests
    ]
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    for module_name in test_modules:
        try:
            module = __import__(module_name, fromlist=[''])
            suite.addTest(loader.loadTestsFromModule(module))
        except ImportError as e:
            print(f"❌ Could not import {module_name}: {e}")
    
    # Run tests
    result = SimpleTestResult()
    suite.run(result)
    result.end_time = datetime.now()
    
    return result


def run_full_tests():
    """Run all tests including Firebase Functions (requires proper setup)"""
    
    print("🚀 Running Full Test Suite")
    print("=" * 50)
    
    # Run all test modules
    test_modules = [
        'tests.test_find_leads',
        'tests.test_enrich_leads', 
        'tests.test_api_testing',
        'tests.test_utils'
    ]
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    for module_name in test_modules:
        try:
            module = __import__(module_name, fromlist=[''])
            suite.addTest(loader.loadTestsFromModule(module))
        except ImportError as e:
            print(f"❌ Could not import {module_name}: {e}")
    
    # Run tests
    result = SimpleTestResult()
    suite.run(result)
    result.end_time = datetime.now()
    
    return result


def print_results(result):
    """Print test results summary"""
    
    duration = (result.end_time - result.start_time).total_seconds()
    success_rate = (len(result.successes) / max(result.tests_run, 1)) * 100
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS")
    print("=" * 50)
    print(f"Total Tests:    {result.tests_run}")
    print(f"✅ Passed:      {len(result.successes)}")
    print(f"❌ Failed:      {len(result.failures)}")
    print(f"💥 Errors:      {len(result.errors)}")
    print(f"⏭️  Skipped:     {len(result.skipped)}")
    print(f"⏱️  Duration:    {duration:.2f}s")
    print(f"📈 Success Rate: {success_rate:.1f}%")
    
    # Show failures and errors
    if result.failures:
        print(f"\n❌ FAILURES ({len(result.failures)}):")
        for test, error in result.failures:
            print(f"• {test}: {str(error[1]).split('AssertionError: ')[-1]}")
    
    if result.errors:
        print(f"\n💥 ERRORS ({len(result.errors)}):")
        for test, error in result.errors:
            print(f"• {test}: {str(error[1]).split('RuntimeError: ')[-1]}")
    
    print("=" * 50)
    
    if len(result.failures) == 0 and len(result.errors) == 0:
        print("🎉 ALL TESTS PASSED!")
        return 0
    else:
        print("❌ SOME TESTS FAILED!")
        return 1


def main():
    """Main test runner entry point"""
    
    parser = argparse.ArgumentParser(description='Simple Firebase Functions Test Runner')
    parser.add_argument('mode', choices=['mock', 'full'], 
                       help='Test mode: mock (fast, mocks only) or full (all tests)')
    parser.add_argument('--output', help='Save results to JSON file')
    
    args = parser.parse_args()
    
    try:
        if args.mode == 'mock':
            result = run_mock_tests()
        else:
            result = run_full_tests()
        
        exit_code = print_results(result)
        
        # Save results if requested
        if args.output:
            save_results(result, args.output)
        
        return exit_code
        
    except KeyboardInterrupt:
        print("\n⏹️  Test run interrupted")
        return 1
    except Exception as e:
        print(f"\n💥 Test runner error: {e}")
        return 1


def save_results(result, output_file):
    """Save test results to JSON file"""
    
    duration = (result.end_time - result.start_time).total_seconds()
    success_rate = (len(result.successes) / max(result.tests_run, 1)) * 100
    
    report_data = {
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'total_tests': result.tests_run,
            'successes': len(result.successes),
            'failures': len(result.failures),
            'errors': len(result.errors),
            'skipped': len(result.skipped),
            'success_rate': success_rate,
            'duration': duration
        }
    }
    
    try:
        with open(output_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        print(f"📄 Results saved to: {output_file}")
    except Exception as e:
        print(f"❌ Failed to save results: {e}")


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code) 