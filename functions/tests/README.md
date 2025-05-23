# Comprehensive Test Suite

This directory contains a complete unit testing framework for the Firebase Functions codebase, with comprehensive mocks for all external APIs and extensive test coverage.

## 🎯 Overview

The test suite provides:

- **Complete API Mocking** - No real API calls during testing
- **Comprehensive Coverage** - Tests for all functions and utilities
- **Detailed Reporting** - Rich test results and coverage reports
- **CI/CD Integration** - GitHub Actions workflow for automated testing
- **Performance Testing** - Optional performance and memory profiling

## 📁 Test Structure

```
tests/
├── __init__.py              # Test package initialization
├── mocks.py                 # Mock implementations for all APIs
├── base_test.py             # Base test classes with common setup
├── test_find_leads.py       # Tests for find_leads function
├── test_enrich_leads.py     # Tests for enrich_leads functions
├── test_api_testing.py      # Tests for API testing utilities
├── test_utils.py            # Tests for utility modules
├── run_tests.py             # Comprehensive test runner script
├── requirements-test.txt    # Testing dependencies
└── README.md               # This documentation
```

## 🚀 Quick Start

### 1. Install Test Dependencies

```bash
# Install testing requirements
pip install -r tests/requirements-test.txt
```

### 2. Run All Tests

```bash
# Run complete test suite
python tests/run_tests.py

# Run with verbose output
python tests/run_tests.py -vv

# Run quietly (minimal output)
python tests/run_tests.py -q
```

### 3. Run Specific Tests

```bash
# Run specific test module
python tests/run_tests.py --modules tests.test_find_leads

# Run tests matching pattern
python tests/run_tests.py -p "enrich"

# Run specific test class or method
python tests/run_tests.py -t tests.test_find_leads.TestFindLeads.test_success
```

## 🧪 Test Categories

### Core Function Tests

- **`test_find_leads.py`** - Lead discovery functionality
  - Apollo integration tests
  - Duplicate filtering
  - Database operations
  - Error handling scenarios

- **`test_enrich_leads.py`** - Lead enrichment functionality  
  - Perplexity integration tests
  - Enrichment types (company/person/both)
  - Status tracking
  - Batch processing

- **`test_api_testing.py`** - API testing utilities
  - Health monitoring
  - Individual API tests
  - Workflow integration
  - Key validation

### Utility Tests

- **`test_utils.py`** - Utility module tests
  - API client functionality
  - Firebase utilities
  - Data processing
  - Email utilities

## 🎭 Mock System

### Mock API Clients

All external APIs are mocked to provide consistent, predictable responses:

#### Apollo.io Mock
```python
from tests.mocks import MockApolloClient

# Returns realistic lead data without API calls
client = MockApolloClient('mock_key')
results = client.search_people(job_titles=['CEO'])
```

#### Perplexity Mock
```python
from tests.mocks import MockPerplexityClient

# Returns formatted research data
client = MockPerplexityClient('mock_key')
research = client.enrich_lead_data('Company Name')
```

#### OpenAI Mock
```python
from tests.mocks import MockOpenAIClient

# Returns formatted email content
client = MockOpenAIClient('mock_key')
email = client.generate_email_content(lead_data, 'outreach')
```

#### Firestore Mock
```python
from tests.mocks import MockFirestoreClient

# In-memory database simulation
db = MockFirestoreClient()
collection = db.collection('leads')
```

### Mock Features

- **Realistic Data** - Mocks return properly structured, realistic data
- **Configurable Responses** - Easy to customize for specific test scenarios
- **Error Simulation** - Can simulate API failures and edge cases
- **Performance** - Fast execution without network calls
- **Consistency** - Deterministic responses for reliable testing

## 📊 Test Runner Features

### Command Line Options

```bash
python tests/run_tests.py [OPTIONS]

Options:
  -v, --verbose         Increase verbosity (-vv for very verbose)
  -q, --quiet          Minimal output
  -p, --pattern PATTERN Run tests matching pattern
  -t, --tests TESTS    Run specific tests
  -o, --output FILE    Save detailed report to JSON file
  --modules MODULES    Run specific test modules
  --list              List available test modules
```

### Output Formats

#### Standard Output
```
🧪 Running Test Suite
📁 Test modules: 4
🔍 Test pattern: All tests
------------------------------------------------------------

📋 tests.test_find_leads
  Running: test_find_leads_success_with_auto_enrich
    ✅ PASS
  Running: test_find_leads_success_without_auto_enrich
    ✅ PASS
...

============================================================
📊 TEST RESULTS SUMMARY
============================================================
Total Tests:    47
✅ Passed:      45
❌ Failed:      1
💥 Errors:      0
⏭️  Skipped:     1
⏱️  Duration:    2.34s
📈 Success Rate: 95.7%
```

#### JSON Report
```json
{
  "timestamp": "2024-01-15T10:30:00",
  "summary": {
    "total_tests": 47,
    "successes": 45,
    "failures": 1,
    "errors": 0,
    "skipped": 1,
    "success_rate": 95.7,
    "duration": 2.34
  },
  "failures": [...],
  "errors": [...],
  "skipped": [...]
}
```

## 🏗️ Base Test Classes

### BaseTestCase
Provides common mocking setup for all tests:

```python
from tests.base_test import BaseTestCase

class MyTest(BaseTestCase):
    def test_something(self):
        # All mocks are automatically available
        result = self.mock_apollo_client.search_people()
        self.assert_successful_response(result)
```

### MockFirebaseFunctionsTestCase
Extended base class for Firebase Functions:

```python
from tests.base_test import MockFirebaseFunctionsTestCase

class MyFunctionTest(MockFirebaseFunctionsTestCase):
    def test_function(self):
        request_data = {'project_id': 'test_123'}
        result = self.simulate_firebase_function_call(my_function, request_data)
        self.assert_successful_response(result)
```

## 🔧 Writing New Tests

### 1. Create Test File

```python
"""
Unit tests for new_feature function

Description of what this test module covers.
"""

import unittest
from tests.base_test import MockFirebaseFunctionsTestCase
from new_feature import new_function

class TestNewFunction(MockFirebaseFunctionsTestCase):
    """Test cases for new_function"""
    
    def test_new_function_success(self):
        """Test successful execution"""
        request_data = {'param': 'value'}
        result = self.simulate_firebase_function_call(new_function, request_data)
        self.assert_successful_response(result)
    
    def test_new_function_error(self):
        """Test error handling"""
        request_data = {'invalid': 'data'}
        with self.assertRaises(Exception):
            self.simulate_firebase_function_call(new_function, request_data)
```

### 2. Add to Test Runner

Update `tests/run_tests.py` to include your new test module:

```python
def discover_test_modules():
    test_modules = [
        'tests.test_find_leads',
        'tests.test_enrich_leads',
        'tests.test_api_testing',
        'tests.test_utils',
        'tests.test_new_feature'  # Add your new module
    ]
```

### 3. Test Your Tests

```bash
# Run just your new tests
python tests/run_tests.py --modules tests.test_new_feature

# Run with verbose output to debug
python tests/run_tests.py --modules tests.test_new_feature -vv
```

## 🚀 CI/CD Integration

### GitHub Actions Workflow

The `.github/workflows/test.yml` file provides:

- **Multi-Python Testing** - Tests on Python 3.9, 3.10, 3.11
- **Comprehensive Checks** - Linting, formatting, security scans
- **Coverage Reports** - Code coverage analysis and reporting
- **Performance Testing** - Optional performance profiling
- **Security Scanning** - Bandit and Safety vulnerability checks

### Running Locally

```bash
# Simulate CI environment
export APOLLO_API_KEY=mock_apollo_key_for_testing
export PERPLEXITY_API_KEY=mock_perplexity_key_for_testing  
export OPENAI_API_KEY=mock_openai_key_for_testing
export DEBUG=true

# Run full test suite
python tests/run_tests.py -vv --output ci-results.json
```

## 📈 Best Practices

### 1. Test Naming

```python
def test_function_name_scenario(self):
    """Test function_name with specific scenario"""
    pass

# Good examples:
def test_find_leads_success_with_auto_enrich(self):
def test_enrich_leads_missing_project_id(self):
def test_apollo_api_connection_timeout(self):
```

### 2. Test Structure

```python
def test_something(self):
    """Test description"""
    
    # Arrange - Set up test data
    request_data = {'project_id': 'test_123'}
    
    # Act - Execute the function
    result = self.simulate_firebase_function_call(function, request_data)
    
    # Assert - Verify results
    self.assert_successful_response(result)
    self.assertEqual(result['project_id'], 'test_123')
```

### 3. Mock Customization

```python
def test_api_failure(self):
    """Test handling of API failures"""
    
    # Customize mock behavior for this test
    self.mock_apollo_client.search_people = MagicMock(
        side_effect=Exception("API Error")
    )
    
    # Test error handling
    with self.assertRaises(Exception):
        self.simulate_firebase_function_call(find_leads, request_data)
```

### 4. Data Validation

```python
def test_data_structure(self):
    """Test that response has correct structure"""
    
    result = self.simulate_firebase_function_call(function, request_data)
    
    # Verify required fields
    self.assertIn('success', result)
    self.assertIn('message', result)
    self.assertIn('data', result)
    
    # Verify data types
    self.assertIsInstance(result['success'], bool)
    self.assertIsInstance(result['data'], list)
```

## 🐛 Troubleshooting

### Common Issues

#### Import Errors
```bash
# Ensure parent directory is in path
export PYTHONPATH=$PYTHONPATH:$(pwd)
python tests/run_tests.py
```

#### Mock Not Working
```python
# Verify patches are applied correctly
def setUp(self):
    super().setUp()
    # Check that mocks are properly initialized
    self.assertIsInstance(self.mock_apollo_client, MockApolloClient)
```

#### Test Isolation
```python
# Ensure tests don't affect each other
def setUp(self):
    super().setUp()
    # Reset any shared state
    self.mock_firestore.collections.clear()
```

### Debugging Tests

```bash
# Run with maximum verbosity
python tests/run_tests.py -vv

# Run specific failing test
python tests/run_tests.py -t tests.test_module.TestClass.test_method -vv

# Save detailed report for analysis
python tests/run_tests.py --output debug-report.json
```

## 📚 Resources

- [unittest Documentation](https://docs.python.org/3/library/unittest.html)
- [unittest.mock Documentation](https://docs.python.org/3/library/unittest.mock.html)
- [Firebase Testing Guide](https://firebase.google.com/docs/functions/unit-testing)
- [Python Testing Best Practices](https://docs.python-guide.org/writing/tests/)

## 🤝 Contributing

When adding new functionality:

1. **Write Tests First** - Follow TDD principles
2. **Mock External Dependencies** - Don't make real API calls
3. **Test Error Cases** - Include failure scenarios
4. **Update Documentation** - Keep this README current
5. **Run Full Suite** - Ensure all tests pass before committing

## 📄 License

This test suite is part of the Firebase Functions project and follows the same license terms. 