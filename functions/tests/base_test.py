"""
Base test class with Firebase Functions mocking setup

This module provides a base test class that all other tests can inherit from,
setting up consistent mocking for all external dependencies using proper Firebase Functions objects.
"""

import unittest
from unittest.mock import patch, MagicMock, Mock
from typing import Dict, Any
from datetime import datetime
import os
import sys
import json

# Import Firebase Functions types for proper mocking
from firebase_functions import https_fn

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
        
        # Patch API clients - update to match actual import paths
        self.apollo_patch = patch('utils.ApolloClient', return_value=self.mock_apollo_client)
        self.perplexity_patch = patch('utils.PerplexityClient', return_value=self.mock_perplexity_client)
        self.openai_patch = patch('utils.OpenAIClient', return_value=self.mock_openai_client)
        
        # Patch Firebase utilities - update to match actual import paths
        self.firestore_patch = patch('utils.get_firestore_client', return_value=self.mock_firestore)
        self.api_keys_patch = patch('utils.get_api_keys', return_value=self.test_api_keys)
        
        # Patch lead processor - update to match actual import paths
        self.lead_processor_patch = patch('utils.LeadProcessor', return_value=self.mock_lead_processor)
        
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


class FirebaseFunctionsTestCase(BaseTestCase):
    """Test class specifically for Firebase Functions with proper request/response mocking"""
    
    def setUp(self):
        """Set up Firebase Functions specific mocks"""
        super().setUp()
        
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
    
    def tearDown(self):
        """Clean up Firebase Functions mocks"""
        super().tearDown()
        
        # Stop additional patches
        if hasattr(self, 'env_patch'):
            self.env_patch.stop()
        if hasattr(self, 'logging_patch'):
            self.logging_patch.stop()
        if hasattr(self, 'timestamp_patch'):
            self.timestamp_patch.stop()
    
    def create_callable_request(self, data: Dict[str, Any], auth_uid: str = None) -> Mock:
        """Create a mock CallableRequest for testing"""
        request = Mock(spec=https_fn.CallableRequest)
        request.data = data
        
        # Setup auth mock
        if auth_uid:
            request.auth = Mock()
            request.auth.uid = auth_uid
            request.auth.token = {"sub": auth_uid, "email": f"{auth_uid}@test.com"}
        else:
            request.auth = None
        
        return request
    
    def create_http_request(self, data: Dict[str, Any], method: str = 'POST', headers: Dict[str, str] = None) -> Mock:
        """Create a mock HTTP Request for testing"""
        request = Mock(spec=https_fn.Request)
        request.method = method
        request.headers = headers or {'Content-Type': 'application/json'}
        request.get_json.return_value = data
        request.data = json.dumps(data).encode('utf-8')
        request.args = {}
        request.form = {}
        
        return request
    
    def create_mock_request(self, data: Dict[str, Any]) -> Mock:
        """Create a generic mock request for backward compatibility"""
        return self.create_callable_request(data)


# Alias for backward compatibility
MockFirebaseFunctionsTestCase = FirebaseFunctionsTestCase 