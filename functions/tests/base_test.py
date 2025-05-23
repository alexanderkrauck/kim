"""
Base test class with common mocking setup

This module provides a base test class that all other tests can inherit from,
setting up consistent mocking for all external dependencies including Flask context.
"""

import unittest
from unittest.mock import patch, MagicMock, Mock
from typing import Dict, Any
from datetime import datetime
import os
import sys

from .mocks import (
    MockApolloClient,
    MockPerplexityClient,
    MockOpenAIClient,
    MockFirestoreClient,
    MockLeadProcessor,
    MOCK_API_KEYS,
    MOCK_PROJECT_DATA,
    MOCK_LEAD_DATA,
    # Import mock API testing functions
    test_apollo_api,
    test_perplexity_api,
    test_openai_api,
    test_all_apis,
    validate_api_key_format,
    get_api_health_summary,
    test_workflow_integration
)


class BaseTestCase(unittest.TestCase):
    """Base test class with common setup and mocking"""
    
    def setUp(self):
        """Set up common mocks and test data"""
        
        # Mock API clients
        self.mock_apollo_client = MockApolloClient(MOCK_API_KEYS['apollo'])
        self.mock_perplexity_client = MockPerplexityClient(MOCK_API_KEYS['perplexity'])
        self.mock_openai_client = MockOpenAIClient(MOCK_API_KEYS['openai'])
        
        # Mock Firestore
        self.mock_firestore = MockFirestoreClient()
        
        # Mock utilities
        self.mock_lead_processor = MockLeadProcessor()
        
        # Test data
        self.test_project_data = MOCK_PROJECT_DATA.copy()
        self.test_lead_data = MOCK_LEAD_DATA.copy()
        self.test_api_keys = MOCK_API_KEYS.copy()
        
        # Setup Firestore with test data
        self._setup_firestore_data()
        
        # Start patches
        self._start_patches()
    
    def tearDown(self):
        """Clean up after tests"""
        self._stop_patches()
    
    def _setup_firestore_data(self):
        """Setup mock Firestore with test data"""
        # Add test project
        projects_collection = self.mock_firestore.collection('projects')
        projects_collection.documents[self.test_project_data['id']] = self.test_project_data
        
        # Add test lead
        leads_collection = self.mock_firestore.collection('leads')
        leads_collection.documents[self.test_lead_data['id']] = self.test_lead_data
    
    def _start_patches(self):
        """Start all necessary patches"""
        
        # Patch API clients
        self.apollo_patch = patch('utils.api_clients.ApolloClient', return_value=self.mock_apollo_client)
        self.perplexity_patch = patch('utils.api_clients.PerplexityClient', return_value=self.mock_perplexity_client)
        self.openai_patch = patch('utils.api_clients.OpenAIClient', return_value=self.mock_openai_client)
        
        # Patch Firebase utilities
        self.firestore_patch = patch('utils.firebase_utils.get_firestore_client', return_value=self.mock_firestore)
        self.api_keys_patch = patch('utils.firebase_utils.get_api_keys', return_value=self.test_api_keys)
        
        # Patch lead processor
        self.lead_processor_patch = patch('utils.data_processing.LeadProcessor', return_value=self.mock_lead_processor)
        
        # Patch Firebase admin
        self.firestore_client_patch = patch('firebase_admin.firestore.client', return_value=self.mock_firestore)
        
        # Patch API testing utilities
        self.api_testing_patches = self._start_api_testing_patches()
        
        # Start all patches
        self.apollo_patch.start()
        self.perplexity_patch.start()
        self.openai_patch.start()
        self.firestore_patch.start()
        self.api_keys_patch.start()
        self.lead_processor_patch.start()
        self.firestore_client_patch.start()
    
    def _start_api_testing_patches(self):
        """Start API testing utility patches"""
        patches = []
        
        # Create a mock utils.api_testing module
        mock_api_testing = MagicMock()
        mock_api_testing.test_apollo_api = test_apollo_api
        mock_api_testing.test_perplexity_api = test_perplexity_api
        mock_api_testing.test_openai_api = test_openai_api
        mock_api_testing.test_all_apis = test_all_apis
        mock_api_testing.validate_api_key_format = validate_api_key_format
        mock_api_testing.get_api_health_summary = get_api_health_summary
        mock_api_testing.test_workflow_integration = test_workflow_integration
        
        # Add utils.api_testing to sys.modules if it doesn't exist
        if 'utils.api_testing' not in sys.modules:
            sys.modules['utils.api_testing'] = mock_api_testing
        
        # Individual function patches
        api_testing_functions = [
            'utils.api_testing.test_apollo_api',
            'utils.api_testing.test_perplexity_api',
            'utils.api_testing.test_openai_api',
            'utils.api_testing.test_all_apis',
            'utils.api_testing.validate_api_key_format',
            'utils.api_testing.get_api_health_summary',
            'utils.api_testing.test_workflow_integration'
        ]
        
        function_map = {
            'utils.api_testing.test_apollo_api': test_apollo_api,
            'utils.api_testing.test_perplexity_api': test_perplexity_api,
            'utils.api_testing.test_openai_api': test_openai_api,
            'utils.api_testing.test_all_apis': test_all_apis,
            'utils.api_testing.validate_api_key_format': validate_api_key_format,
            'utils.api_testing.get_api_health_summary': get_api_health_summary,
            'utils.api_testing.test_workflow_integration': test_workflow_integration
        }
        
        for func_path, func in function_map.items():
            try:
                patch_obj = patch(func_path, func)
                patch_obj.start()
                patches.append(patch_obj)
            except:
                # If patching fails, continue
                pass
        
        return patches
    
    def _stop_patches(self):
        """Stop all patches"""
        patches = [
            'apollo_patch',
            'perplexity_patch', 
            'openai_patch',
            'firestore_patch',
            'api_keys_patch',
            'lead_processor_patch',
            'firestore_client_patch'
        ]
        
        for patch_name in patches:
            if hasattr(self, patch_name):
                getattr(self, patch_name).stop()
        
        # Stop API testing patches
        if hasattr(self, 'api_testing_patches'):
            for patch_obj in self.api_testing_patches:
                try:
                    patch_obj.stop()
                except:
                    pass
    
    def create_mock_request(self, data: Dict[str, Any]) -> MagicMock:
        """Create a mock Firebase Functions request"""
        mock_request = MagicMock()
        mock_request.data = data
        mock_request.method = 'POST'
        mock_request.headers = {'Content-Type': 'application/json'}
        mock_request.get_json.return_value = data
        return mock_request
    
    def assert_successful_response(self, response: Dict[str, Any]):
        """Assert that a response indicates success"""
        self.assertTrue(response.get('success', False), f"Response was not successful: {response}")
    
    def assert_error_response(self, response: Dict[str, Any]):
        """Assert that a response indicates an error"""
        self.assertFalse(response.get('success', True), f"Response was successful when error expected: {response}")
    
    def add_leads_to_project(self, project_id: str, count: int = 5):
        """Add mock leads to a project for testing"""
        leads_collection = self.mock_firestore.collection('leads')
        
        for i in range(count):
            lead_data = {
                'id': f'test_lead_{i + 1}',
                'name': f'Test User {i + 1}',
                'email': f'test{i + 1}@example.com',
                'title': 'CEO' if i % 2 == 0 else 'CTO',
                'company': f'Test Company {i + 1}',
                'projectId': project_id,
                'status': 'new',
                'enrichmentStatus': 'pending' if i % 2 == 0 else None,
                'createdAt': datetime.utcnow()
            }
            leads_collection.documents[lead_data['id']] = lead_data
    
    def add_enriched_leads_to_project(self, project_id: str, count: int = 3):
        """Add mock enriched leads to a project for testing"""
        leads_collection = self.mock_firestore.collection('leads')
        
        for i in range(count):
            lead_data = {
                'id': f'enriched_lead_{i + 1}',
                'name': f'Enriched User {i + 1}',
                'email': f'enriched{i + 1}@example.com',
                'title': 'VP Sales',
                'company': f'Enriched Company {i + 1}',
                'projectId': project_id,
                'status': 'new',
                'enrichmentStatus': 'enriched',
                'enrichmentType': 'both',
                'company_research': f'Research data for {i + 1}...',
                'person_research': f'Person research for {i + 1}...',
                'lastEnrichmentDate': datetime.utcnow(),
                'createdAt': datetime.utcnow()
            }
            leads_collection.documents[lead_data['id']] = lead_data


class MockFirebaseFunctionsTestCase(BaseTestCase):
    """Extended base class for Firebase Functions testing with Flask context mocking"""
    
    def setUp(self):
        """Set up Firebase Functions specific mocks"""
        super().setUp()
        
        # Create mock Flask app and context
        self.mock_app = MagicMock()
        self.mock_app_context = MagicMock()
        self.mock_request_context = MagicMock()
        
        # Setup Flask context managers
        self.mock_app.app_context.return_value = self.mock_app_context
        self.mock_app.test_request_context.return_value = self.mock_request_context
        self.mock_app_context.__enter__ = MagicMock(return_value=self.mock_app_context)
        self.mock_app_context.__exit__ = MagicMock(return_value=None)
        self.mock_request_context.__enter__ = MagicMock(return_value=self.mock_request_context)
        self.mock_request_context.__exit__ = MagicMock(return_value=None)
        
        # Mock Firebase Functions decorators and Flask
        self._start_firebase_patches()
    
    def tearDown(self):
        """Clean up Firebase Functions mocks"""
        self._stop_firebase_patches()
        super().tearDown()
    
    def _start_firebase_patches(self):
        """Start Firebase Functions specific patches"""
        
        # Mock Firebase Functions decorators
        self.functions_patch = patch('firebase_functions.https_fn.on_request')
        self.mock_decorator = self.functions_patch.start()
        self.mock_decorator.return_value = lambda func: func  # Pass through decorator
        
        # Mock Flask imports and current_app
        self.flask_patch = patch('flask.Flask', return_value=self.mock_app)
        self.current_app_patch = patch('flask.current_app', self.mock_app)
        self.request_patch = patch('flask.request')
        
        self.flask_patch.start()
        self.current_app_patch.start()
        self.mock_request = self.request_patch.start()
        
        # Setup mock request
        self.mock_request.method = 'POST'
        self.mock_request.headers = {'Content-Type': 'application/json'}
        self.mock_request.data = b'{}'
        
        # Mock environment variables
        self.env_patch = patch.dict(os.environ, {
            'APOLLO_API_KEY': MOCK_API_KEYS['apollo'],
            'PERPLEXITY_API_KEY': MOCK_API_KEYS['perplexity'],
            'OPENAI_API_KEY': MOCK_API_KEYS['openai'],
            'DEBUG': 'true'
        })
        self.env_patch.start()
        
        # Mock logging to prevent spam
        self.logging_patch = patch('logging.getLogger')
        self.mock_logger = self.logging_patch.start()
        self.mock_logger.return_value = MagicMock()
        
        # Mock firestore SERVER_TIMESTAMP
        self.timestamp_patch = patch('firebase_admin.firestore.SERVER_TIMESTAMP', datetime.utcnow())
        self.timestamp_patch.start()
    
    def _stop_firebase_patches(self):
        """Stop Firebase Functions patches"""
        patches = [
            'functions_patch',
            'flask_patch',
            'current_app_patch', 
            'request_patch',
            'env_patch',
            'logging_patch',
            'timestamp_patch'
        ]
        
        for patch_name in patches:
            if hasattr(self, patch_name):
                getattr(self, patch_name).stop()
    
    def simulate_firebase_function_call(self, function, request_data: Dict[str, Any]):
        """Simulate calling a Firebase Function with proper context"""
        
        # Create mock request with data
        mock_request = self.create_mock_request(request_data)
        
        # Update the global mock request
        self.mock_request.get_json.return_value = request_data
        self.mock_request.data = request_data
        
        try:
            # Call the function with mock Flask context
            with self.mock_app.app_context():
                with self.mock_app.test_request_context():
                    result = function(mock_request)
                    
                    # Handle different return types
                    if hasattr(result, 'data'):
                        # Flask Response object
                        return result.get_json() if hasattr(result, 'get_json') else result.data
                    elif isinstance(result, dict):
                        # Direct dictionary response
                        return result
                    else:
                        # Other response types
                        return {'success': True, 'data': result}
                        
        except Exception as e:
            # Return error response in expected format
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
    
    def mock_function_with_error(self, function_name: str, error_message: str):
        """Helper to mock a function to raise an error"""
        def error_function(*args, **kwargs):
            raise Exception(error_message)
        
        return patch(function_name, side_effect=error_function) 