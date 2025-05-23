#!/usr/bin/env python3
"""
Comprehensive Test Runner for Firebase Functions

This script runs all unit tests and provides detailed reporting.
It should be executed after every code change to ensure system integrity.
"""

import unittest
import sys
import os
import argparse
from io import StringIO
import json
from datetime import datetime
import traceback

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestResult:
    """Enhanced test result tracking"""
    
    def __init__(self):
        self.tests_run = 0
        self.failures = []
        self.errors = []
        self.skipped = []
        self.successes = []
        self.start_time = None
        self.end_time = None
    
    def add_success(self, test):
        self.successes.append(test)
    
    def add_failure(self, test, err):
        self.failures.append((test, err))
    
    def add_error(self, test, err):
        self.errors.append((test, err))
    
    def add_skip(self, test, reason):
        self.skipped.append((test, reason))
    
    def get_summary(self):
        return {
            'total_tests': self.tests_run,
            'successes': len(self.successes),
            'failures': len(self.failures),
            'errors': len(self.errors),
            'skipped': len(self.skipped),
            'success_rate': (len(self.successes) / max(self.tests_run, 1)) * 100,
            'duration': (self.end_time - self.start_time).total_seconds() if self.start_time and self.end_time else 0
        }


class VerboseTestResult(unittest.TestResult):
    """Enhanced test result class with detailed reporting"""
    
    def __init__(self, verbosity=1):
        super().__init__()
        self.verbosity = verbosity
        self.test_results = TestResult()
        self.current_test = None
        
    def startTest(self, test):
        super().startTest(test)
        self.current_test = test
        self.test_results.tests_run += 1
        if self.verbosity >= 2:
            print(f"  Running: {test._testMethodName}")
    
    def addSuccess(self, test):
        super().addSuccess(test)
        self.test_results.add_success(test)
        if self.verbosity >= 2:
            print(f"    ✅ PASS")
    
    def addError(self, test, err):
        super().addError(test, err)
        self.test_results.add_error(test, err)
        if self.verbosity >= 1:
            print(f"    ❌ ERROR: {test._testMethodName}")
            if self.verbosity >= 2:
                print(f"       {err[1]}")
    
    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.test_results.add_failure(test, err)
        if self.verbosity >= 1:
            print(f"    ❌ FAIL: {test._testMethodName}")
            if self.verbosity >= 2:
                print(f"       {err[1]}")
    
    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.test_results.add_skip(test, reason)
        if self.verbosity >= 2:
            print(f"    ⏭️  SKIP: {test._testMethodName} - {reason}")


def discover_test_modules():
    """Discover all test modules in the tests directory"""
    test_modules = [
        'tests.test_find_leads',
        'tests.test_enrich_leads',
        'tests.test_api_testing',
        'tests.test_utils'
    ]
    
    available_modules = []
    for module_name in test_modules:
        try:
            __import__(module_name)
            available_modules.append(module_name)
        except ImportError as e:
            print(f"Warning: Could not import {module_name}: {e}")
    
    return available_modules


def run_test_suite(test_modules=None, verbosity=1, pattern=None):
    """Run the complete test suite"""
    
    if test_modules is None:
        test_modules = discover_test_modules()
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    for module_name in test_modules:
        try:
            module = __import__(module_name, fromlist=[''])
            if pattern:
                # Filter tests by pattern
                module_suite = loader.loadTestsFromModule(module)
                filtered_suite = unittest.TestSuite()
                
                for test_group in module_suite:
                    for test in test_group:
                        if pattern.lower() in test._testMethodName.lower():
                            filtered_suite.addTest(test)
                
                suite.addTest(filtered_suite)
            else:
                suite.addTest(loader.loadTestsFromModule(module))
                
        except ImportError as e:
            print(f"Error importing {module_name}: {e}")
            continue
    
    # Run tests
    runner = unittest.TextTestRunner(
        verbosity=0,  # We handle our own verbosity
        stream=StringIO()  # Suppress default output
    )
    
    # Use our custom result class
    result = VerboseTestResult(verbosity)
    result.test_results.start_time = datetime.now()
    
    print(f"🧪 Running Test Suite")
    print(f"📁 Test modules: {len(test_modules)}")
    print(f"🔍 Test pattern: {pattern if pattern else 'All tests'}")
    print("-" * 60)
    
    for module_name in test_modules:
        print(f"\n📋 {module_name}")
        try:
            module = __import__(module_name, fromlist=[''])
            module_suite = loader.loadTestsFromModule(module)
            
            # Run this module's tests
            for test_case in module_suite:
                test_case.run(result)
                
        except Exception as e:
            print(f"  ❌ Error running module: {e}")
            traceback.print_exc()
    
    result.test_results.end_time = datetime.now()
    
    return result.test_results


def print_detailed_report(test_results):
    """Print detailed test results"""
    
    summary = test_results.get_summary()
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    print(f"Total Tests:    {summary['total_tests']}")
    print(f"✅ Passed:      {summary['successes']}")
    print(f"❌ Failed:      {summary['failures']}")
    print(f"💥 Errors:      {summary['errors']}")
    print(f"⏭️  Skipped:     {summary['skipped']}")
    print(f"⏱️  Duration:    {summary['duration']:.2f}s")
    print(f"📈 Success Rate: {summary['success_rate']:.1f}%")
    
    # Print failures and errors
    if test_results.failures:
        print(f"\n❌ FAILURES ({len(test_results.failures)}):")
        print("-" * 40)
        for test, error in test_results.failures:
            print(f"• {test}")
            print(f"  {error[1]}")
    
    if test_results.errors:
        print(f"\n💥 ERRORS ({len(test_results.errors)}):")
        print("-" * 40)
        for test, error in test_results.errors:
            print(f"• {test}")
            print(f"  {error[1]}")
    
    if test_results.skipped:
        print(f"\n⏭️  SKIPPED ({len(test_results.skipped)}):")
        print("-" * 40)
        for test, reason in test_results.skipped:
            print(f"• {test}: {reason}")
    
    # Overall status
    print("\n" + "=" * 60)
    if summary['failures'] == 0 and summary['errors'] == 0:
        print("🎉 ALL TESTS PASSED!")
        exit_code = 0
    else:
        print("❌ SOME TESTS FAILED!")
        exit_code = 1
    
    print("=" * 60)
    
    return exit_code


def save_test_report(test_results, output_file):
    """Save test results to a JSON file"""
    
    summary = test_results.get_summary()
    
    report_data = {
        'timestamp': datetime.now().isoformat(),
        'summary': summary,
        'failures': [
            {
                'test': str(test),
                'error': str(error[1])
            }
            for test, error in test_results.failures
        ],
        'errors': [
            {
                'test': str(test),
                'error': str(error[1])
            }
            for test, error in test_results.errors
        ],
        'skipped': [
            {
                'test': str(test),
                'reason': reason
            }
            for test, reason in test_results.skipped
        ]
    }
    
    try:
        with open(output_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        print(f"📄 Test report saved to: {output_file}")
    except Exception as e:
        print(f"❌ Failed to save report: {e}")


def run_specific_tests(test_names, verbosity=1):
    """Run specific test classes or methods"""
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    for test_name in test_names:
        try:
            # Try to load as a specific test
            suite.addTest(loader.loadTestsFromName(test_name))
        except Exception as e:
            print(f"❌ Could not load test '{test_name}': {e}")
    
    if suite.countTestCases() == 0:
        print("❌ No valid tests found!")
        return 1
    
    result = VerboseTestResult(verbosity)
    result.test_results.start_time = datetime.now()
    
    print(f"🧪 Running Specific Tests: {', '.join(test_names)}")
    print("-" * 60)
    
    suite.run(result)
    
    result.test_results.end_time = datetime.now()
    
    return print_detailed_report(result.test_results)


def main():
    """Main test runner entry point"""
    
    parser = argparse.ArgumentParser(description='Firebase Functions Test Runner')
    parser.add_argument('-v', '--verbose', action='count', default=1,
                       help='Increase verbosity (use -vv for very verbose)')
    parser.add_argument('-q', '--quiet', action='store_true',
                       help='Minimal output')
    parser.add_argument('-p', '--pattern',
                       help='Run tests matching pattern')
    parser.add_argument('-t', '--tests', nargs='+',
                       help='Run specific tests (e.g., tests.test_find_leads.TestFindLeads.test_success)')
    parser.add_argument('-o', '--output',
                       help='Save detailed report to JSON file')
    parser.add_argument('--modules', nargs='+',
                       help='Run specific test modules',
                       default=None)
    parser.add_argument('--list', action='store_true',
                       help='List available test modules and exit')
    
    args = parser.parse_args()
    
    if args.quiet:
        args.verbose = 0
    
    # List available modules
    if args.list:
        modules = discover_test_modules()
        print("Available test modules:")
        for module in modules:
            print(f"  • {module}")
        return 0
    
    # Run specific tests
    if args.tests:
        return run_specific_tests(args.tests, args.verbose)
    
    # Run full test suite
    try:
        test_results = run_test_suite(
            test_modules=args.modules,
            verbosity=args.verbose,
            pattern=args.pattern
        )
        
        exit_code = print_detailed_report(test_results)
        
        # Save report if requested
        if args.output:
            save_test_report(test_results, args.output)
        
        return exit_code
        
    except KeyboardInterrupt:
        print("\n⏹️  Test run interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Test runner error: {e}")
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code) 