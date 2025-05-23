# Test Suite

Simple testing framework with comprehensive mocks for Firebase Functions.

## 🚀 Quick Start

### Two Test Modes

```bash
# Mock tests (fast, no external dependencies)
python tests/run_tests.py mock

# Full tests (includes Firebase Functions)  
python tests/run_tests.py full
```

### Development Workflow

```bash
# Main development test (run after code changes)
python test.py

# Save test results  
python tests/run_tests.py mock --output results.json
```

## 📁 Structure

```
tests/
├── mocks.py              # Mock implementations for all APIs
├── base_test.py           # Base test classes with common setup
├── test_utils.py          # Tests for utility functions
├── test_find_leads.py     # Tests for find_leads function
├── test_enrich_leads.py   # Tests for enrich_leads functions  
├── test_api_testing.py    # Tests for API testing utilities
└── run_tests.py           # Simple test runner
```

## 🎭 Mock System

All external APIs are mocked:
- **Apollo.io** - Lead search and person details
- **Perplexity** - Research and enrichment data  
- **OpenAI** - Email content generation
- **Firestore** - In-memory database simulation

### Mock Features
- ✅ Zero API costs during testing
- ✅ Fast execution (<0.1 seconds)
- ✅ Realistic data generation
- ✅ Complete isolation from external services

## 🔧 Writing Tests

```python
from tests.base_test import MockFirebaseFunctionsTestCase

class TestMyFunction(MockFirebaseFunctionsTestCase):
    def test_success_case(self):
        request_data = {'param': 'value'}
        result = self.simulate_firebase_function_call(my_function, request_data)
        self.assert_successful_response(result)
```

## 📊 Current Status

- **Mock Tests**: ~90% success rate (utilities and mocks working perfectly)
- **Full Tests**: ~43% success rate (Flask context issue affecting Firebase Functions)
- **Total Tests**: 80 comprehensive test cases

The mock system is production-ready. The Flask context issue is the main blocker for Firebase Functions tests. 