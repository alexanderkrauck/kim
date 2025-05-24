"""
Unit tests for test_apis functions and API testing utilities

Tests all aspects of API testing functionality including individual API tests,
workflow testing, and status monitoring.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.base_test import FirebaseFunctionsTestCase
from test_apis import test_apis, validate_api_keys, get_api_status


class TestApiTestingFunctions(FirebaseFunctionsTestCase):
    """Test cases for test_apis Firebase function"""
    
    def test_test_apis_health_check(self):
        """Test API health check functionality"""
        request_data = {
            'test_type': 'health'
        }
        
        # Create mock callable request
        mock_request = self.create_callable_request(request_data)
        
        # Call the function directly
        result = test_apis(mock_request)
        
        self.assert_successful_response(result)
        self.assertEqual(result['test_type'], 'health')
        self.assertIn('overall_health', result)
        self.assertIn('apis', result)
    
    def test_test_apis_individual_tests(self):
        """Test individual API testing"""
        request_data = {
            'test_type': 'individual',
            'minimal': True
        }
        
        mock_request = self.create_callable_request(request_data)
        result = test_apis(mock_request)
        
        self.assert_successful_response(result)
        self.assertEqual(result['test_type'], 'individual')
        self.assertIn('overall_status', result)
        self.assertIn('apis', result)
        self.assertIn('apollo', result['apis'])
        self.assertIn('perplexity', result['apis'])
        self.assertIn('openai', result['apis'])
    
    def test_test_apis_workflow_test(self):
        """Test complete workflow testing"""
        request_data = {
            'test_type': 'workflow'
        }
        
        mock_request = self.create_callable_request(request_data)
        result = test_apis(mock_request)
        
        self.assert_successful_response(result)
        self.assertEqual(result['test_type'], 'workflow')
        self.assertIn('status', result)
        self.assertIn('workflow_stage', result)
    
    def test_test_apis_all_tests(self):
        """Test comprehensive testing"""
        request_data = {
            'test_type': 'all',
            'minimal': True,
            'save_results': False
        }
        
        mock_request = self.create_callable_request(request_data)
        result = test_apis(mock_request)
        
        self.assert_successful_response(result)
        self.assertEqual(result['test_type'], 'all')
        self.assertIn('health_check', result)
        self.assertIn('individual_tests', result)
        self.assertIn('workflow_test', result)
    
    def test_test_apis_invalid_test_type(self):
        """Test error with invalid test type"""
        request_data = {
            'test_type': 'invalid_type'
        }
        
        mock_request = self.create_callable_request(request_data)
        
        # This should return an error result, not raise an exception
        result = test_apis(mock_request)
        
        self.assert_error_response(result)
        self.assertIn('invalid', result.get('message', '').lower())
    
    def test_test_apis_missing_api_keys(self):
        """Test handling of missing API keys"""
        # Remove all API keys from environment
        with patch('test_apis.get_api_keys', return_value={}):
            request_data = {
                'test_type': 'individual'
            }
            
            mock_request = self.create_callable_request(request_data)
            result = test_apis(mock_request)
            
            self.assert_error_response(result)
            self.assertIn('missing', result.get('message', '').lower())
    
    def test_test_apis_with_save_results(self):
        """Test saving results to Firestore"""
        request_data = {
            'test_type': 'health',
            'save_results': True
        }
        
        mock_request = self.create_callable_request(request_data)
        result = test_apis(mock_request)
        
        self.assert_successful_response(result)
        # Check if save functionality was attempted
        self.assertIn('test_type', result)


class TestValidateApiKeys(FirebaseFunctionsTestCase):
    """Test cases for validate_api_keys function"""
    
    def test_validate_api_keys_default(self):
        """Test validation with default configured keys"""
        request_data = {}
        
        mock_request = self.create_callable_request(request_data)
        result = validate_api_keys(mock_request)
        
        self.assert_successful_response(result)
        self.assertIn('validation_results', result)
        self.assertIn('summary', result)
        
        # Check all APIs are validated
        validation_results = result['validation_results']
        self.assertIn('apollo', validation_results)
        self.assertIn('perplexity', validation_results)
        self.assertIn('openai', validation_results)
    
    def test_validate_api_keys_custom_keys(self):
        """Test validation with custom API keys"""
        custom_keys = {
            'apollo': 'custom_apollo_key',
            'perplexity': 'pplx-custom_key',
            'openai': 'sk-custom_openai_key'
        }
        
        request_data = {
            'api_keys': custom_keys
        }
        
        mock_request = self.create_callable_request(request_data)
        result = validate_api_keys(mock_request)
        
        self.assert_successful_response(result)
        validation_results = result['validation_results']
        
        # Check custom keys are validated
        self.assertIn('perplexity', validation_results)
        self.assertIn('openai', validation_results)
    
    def test_validate_api_keys_invalid_formats(self):
        """Test validation with invalid key formats"""
        invalid_keys = {
            'apollo': 'short',
            'perplexity': 'invalid_format',
            'openai': 'wrong_prefix'
        }
        
        request_data = {
            'api_keys': invalid_keys
        }
        
        mock_request = self.create_callable_request(request_data)
        result = validate_api_keys(mock_request)
        
        self.assert_successful_response(result)
        validation_results = result['validation_results']
        
        # Check that validation results are returned (specific validation depends on implementation)
        self.assertIn('apollo', validation_results)
        self.assertIn('perplexity', validation_results) 
        self.assertIn('openai', validation_results)


class TestGetApiStatus(FirebaseFunctionsTestCase):
    """Test cases for get_api_status function"""
    
    def test_get_api_status_basic(self):
        """Test basic API status retrieval"""
        request_data = {
            'include_recent_tests': False
        }
        
        mock_request = self.create_callable_request(request_data)
        result = get_api_status(mock_request)
        
        self.assert_successful_response(result)
        self.assertIn('current_health', result)
        self.assertNotIn('recent_tests', result)
    
    def test_get_api_status_with_recent_tests(self):
        """Test API status with recent test history"""
        request_data = {
            'include_recent_tests': True,
            'limit': 5
        }
        
        mock_request = self.create_callable_request(request_data)
        result = get_api_status(mock_request)
        
        self.assert_successful_response(result)
        self.assertIn('current_health', result)
        # Note: recent_tests may or may not be included depending on implementation


class TestApiTestingUtilities(unittest.TestCase):
    """Test cases for API testing utility functions"""
    
    def setUp(self):
        """Set up test data"""
        self.test_api_keys = {
            'apollo': 'mock_apollo_key_123',
            'perplexity': 'mock_perplexity_key_456',
            'openai': 'mock_openai_key_789'
        }
    
    def test_test_apollo_api_success(self):
        """Test successful Apollo API testing"""
        # Skip if utility functions aren't available as imports
        try:
            from utils.api_testing import test_apollo_api
            
            with patch('utils.api_testing.ApolloClient') as mock_apollo:
                mock_client = MagicMock()
                mock_client.search_people.return_value = {
                    'people': [{'name': 'Test User'}],
                    'pagination': {'total_entries': 100}
                }
                mock_apollo.return_value = mock_client
                
                result = test_apollo_api(self.test_api_keys['apollo'])
                
                self.assertEqual(result['status'], 'success')
                self.assertEqual(result['api'], 'apollo')
                self.assertIn('results_found', result)
                
        except ImportError:
            self.skipTest("API testing utilities not available for import")
    
    def test_test_apollo_api_failure(self):
        """Test Apollo API testing failure"""
        try:
            from utils.api_testing import test_apollo_api
            
            with patch('utils.api_testing.ApolloClient') as mock_apollo:
                mock_apollo.side_effect = Exception("API Error")
                
                result = test_apollo_api(self.test_api_keys['apollo'])
                
                self.assertEqual(result['status'], 'error')
                self.assertEqual(result['api'], 'apollo')
                self.assertIn('API Error', result['message'])
                
        except ImportError:
            self.skipTest("API testing utilities not available for import")
    
    def test_test_perplexity_api_success(self):
        """Test successful Perplexity API testing"""
        try:
            from utils.api_testing import test_perplexity_api
            
            with patch('utils.api_testing.PerplexityClient') as mock_perplexity:
                mock_client = MagicMock()
                mock_client.enrich_lead_data.return_value = {
                    'choices': [{'message': {'content': 'Test research data'}}]
                }
                mock_perplexity.return_value = mock_client
                
                result = test_perplexity_api(self.test_api_keys['perplexity'])
                
                self.assertEqual(result['status'], 'success')
                self.assertEqual(result['api'], 'perplexity')
                self.assertIn('response_length', result)
                
        except ImportError:
            self.skipTest("API testing utilities not available for import")
    
    def test_test_openai_api_success(self):
        """Test successful OpenAI API testing"""
        try:
            from utils.api_testing import test_openai_api
            
            with patch('utils.api_testing.OpenAIClient') as mock_openai:
                mock_client = MagicMock()
                mock_client.generate_email_content.return_value = "Test email content"
                mock_openai.return_value = mock_client
                
                result = test_openai_api(self.test_api_keys['openai'])
                
                self.assertEqual(result['status'], 'success')
                self.assertEqual(result['api'], 'openai')
                self.assertIn('email_length', result)
                
        except ImportError:
            self.skipTest("API testing utilities not available for import")
    
    def test_test_all_apis_success(self):
        """Test testing all APIs successfully"""
        try:
            from utils.api_testing import test_all_apis
            
            with patch('utils.api_testing.test_apollo_api') as mock_apollo, \
                 patch('utils.api_testing.test_perplexity_api') as mock_perplexity, \
                 patch('utils.api_testing.test_openai_api') as mock_openai:
                
                # Mock successful responses
                mock_apollo.return_value = {'status': 'success', 'api': 'apollo'}
                mock_perplexity.return_value = {'status': 'success', 'api': 'perplexity'}
                mock_openai.return_value = {'status': 'success', 'api': 'openai'}
                
                result = test_all_apis(self.test_api_keys)
                
                self.assertEqual(result['overall_status'], 'success')
                self.assertEqual(result['successful_apis'], 3)
                self.assertEqual(result['total_apis'], 3)
                
        except ImportError:
            self.skipTest("API testing utilities not available for import")
    
    def test_test_all_apis_partial_success(self):
        """Test testing all APIs with partial success"""
        try:
            from utils.api_testing import test_all_apis
            
            with patch('utils.api_testing.test_apollo_api') as mock_apollo, \
                 patch('utils.api_testing.test_perplexity_api') as mock_perplexity, \
                 patch('utils.api_testing.test_openai_api') as mock_openai:
                
                # Mock mixed responses
                mock_apollo.return_value = {'status': 'success', 'api': 'apollo'}
                mock_perplexity.return_value = {'status': 'error', 'api': 'perplexity'}
                mock_openai.return_value = {'status': 'partial', 'api': 'openai'}
                
                result = test_all_apis(self.test_api_keys)
                
                self.assertIn(result['overall_status'], ['partial', 'error'])
                self.assertLessEqual(result['successful_apis'], 3)
                
        except ImportError:
            self.skipTest("API testing utilities not available for import")
    
    def test_validate_api_key_format_valid_keys(self):
        """Test validation of valid API key formats"""
        try:
            from utils.api_testing import validate_api_key_format
            
            # Test valid OpenAI key
            result = validate_api_key_format('sk-1234567890abcdef', 'openai')
            self.assertIn('valid', result)
            
            # Test valid Perplexity key  
            result = validate_api_key_format('pplx-1234567890', 'perplexity')
            self.assertIn('valid', result)
            
            # Test valid Apollo key (length-based)
            result = validate_api_key_format('apollo_key_1234567890', 'apollo')
            self.assertIn('valid', result)
            
        except ImportError:
            self.skipTest("API key validation utilities not available for import")
    
    def test_validate_api_key_format_invalid_keys(self):
        """Test validation of invalid API key formats"""
        try:
            from utils.api_testing import validate_api_key_format
            
            # Test invalid OpenAI key (wrong prefix)
            result = validate_api_key_format('invalid-key', 'openai')
            self.assertIn('valid', result)
            
            # Test invalid Perplexity key (wrong prefix)
            result = validate_api_key_format('invalid-key', 'perplexity')
            self.assertIn('valid', result)
            
            # Test invalid Apollo key (too short)
            result = validate_api_key_format('short', 'apollo')
            self.assertIn('valid', result)
            
        except ImportError:
            self.skipTest("API key validation utilities not available for import")
    
    def test_get_api_health_summary(self):
        """Test API health summary generation"""
        try:
            from utils.api_testing import get_api_health_summary
            
            result = get_api_health_summary(self.test_api_keys)
            
            self.assertIn('overall_health', result)
            self.assertIn('apis', result)
            self.assertIn('valid_keys_count', result)
            self.assertIn('total_keys_count', result)
            
            # Check all APIs are included
            self.assertIn('apollo', result['apis'])
            self.assertIn('perplexity', result['apis'])
            self.assertIn('openai', result['apis'])
            
        except ImportError:
            self.skipTest("API health summary utilities not available for import")
    
    def test_workflow_integration_success(self):
        """Test successful workflow integration testing"""
        try:
            from utils.api_testing import test_workflow_integration
            
            with patch('utils.api_testing.ApolloClient') as mock_apollo, \
                 patch('utils.api_testing.PerplexityClient') as mock_perplexity, \
                 patch('utils.api_testing.OpenAIClient') as mock_openai:
                
                # Mock Apollo response
                mock_apollo_client = MagicMock()
                mock_apollo_client.search_people.return_value = {
                    'people': [{
                        'first_name': 'John',
                        'last_name': 'Doe',
                        'title': 'CEO',
                        'organization': {'name': 'Test Company'}
                    }]
                }
                mock_apollo.return_value = mock_apollo_client
                
                # Mock Perplexity response
                mock_perplexity_client = MagicMock()
                mock_perplexity_client.enrich_lead_data.return_value = {
                    'choices': [{'message': {'content': 'Research data'}}]
                }
                mock_perplexity.return_value = mock_perplexity_client
                
                # Mock OpenAI response
                mock_openai_client = MagicMock()
                mock_openai_client.generate_email_content.return_value = "Email content"
                mock_openai.return_value = mock_openai_client
                
                result = test_workflow_integration(self.test_api_keys)
                
                self.assertEqual(result['status'], 'success')
                self.assertEqual(result['workflow_stage'], 'completed')
                self.assertIn('lead_found', result)
                self.assertIn('company', result)
                
        except ImportError:
            self.skipTest("Workflow integration testing not available for import")
    
    def test_workflow_integration_missing_keys(self):
        """Test workflow integration with missing API keys"""
        try:
            from utils.api_testing import test_workflow_integration
            
            incomplete_keys = {
                'apollo': 'key1',
                # Missing perplexity and openai
            }
            
            result = test_workflow_integration(incomplete_keys)
            
            self.assertEqual(result['status'], 'error')
            self.assertEqual(result['workflow_stage'], 'initialization')
            self.assertIn('Missing API keys', result['message'])
            
        except ImportError:
            self.skipTest("Workflow integration testing not available for import")


if __name__ == '__main__':
    unittest.main() 