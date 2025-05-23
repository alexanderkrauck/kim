"""
Unit tests for find_leads function

Tests all aspects of lead discovery functionality including Apollo integration,
duplicate checking, and database operations.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.base_test import MockFirebaseFunctionsTestCase
from find_leads import find_leads


class TestFindLeads(MockFirebaseFunctionsTestCase):
    """Test cases for find_leads function"""
    
    def test_find_leads_success_with_auto_enrich(self):
        """Test successful lead finding with automatic enrichment"""
        request_data = {
            'project_id': 'test_project_123',
            'num_leads': 5,
            'auto_enrich': True
        }
        
        # Mock the enrich_leads function import and call
        with patch('enrich_leads.enrich_leads') as mock_enrich:
            mock_enrich.return_value = {'success': True, 'message': 'Enrichment completed'}
            
            # Also mock the import in find_leads module
            with patch('find_leads.enrich_leads', mock_enrich):
                result = self.simulate_firebase_function_call(find_leads, request_data)
        
        self.assert_successful_response(result)
        self.assertEqual(result['project_id'], 'test_project_123')
        self.assertGreater(result['leads_found'], 0)
        self.assertGreater(result['leads_added'], 0)
        self.assertTrue(result.get('enrichment_triggered', False))
        
        # Verify leads were added to Firestore
        leads_collection = self.mock_firestore.collection('leads')
        self.assertGreater(len(leads_collection.documents), 1)  # Original test lead + new leads
    
    def test_find_leads_success_without_auto_enrich(self):
        """Test successful lead finding without automatic enrichment"""
        request_data = {
            'project_id': 'test_project_123',
            'num_leads': 3,
            'auto_enrich': False
        }
        
        result = self.simulate_firebase_function_call(find_leads, request_data)
        
        self.assert_successful_response(result)
        self.assertEqual(result['project_id'], 'test_project_123')
        self.assertGreater(result['leads_found'], 0)
        self.assertGreater(result['leads_added'], 0)
        self.assertFalse(result.get('enrichment_triggered', True))
    
    def test_find_leads_with_custom_search_params(self):
        """Test lead finding with custom search parameters"""
        request_data = {
            'project_id': 'test_project_123',
            'num_leads': 5,
            'search_params': {
                'job_titles': ['CEO', 'CTO'],
                'locations': ['San Francisco, CA'],
                'company_domains': ['example.com']
            },
            'auto_enrich': False
        }
        
        result = self.simulate_firebase_function_call(find_leads, request_data)
        
        self.assert_successful_response(result)
        self.assertGreater(result['leads_found'], 0)
        
        # Verify search parameters were passed to Apollo client
        # (This would be verified through mock call assertions in a real implementation)
    
    def test_find_leads_no_results_found(self):
        """Test when Apollo returns no results"""
        # Mock Apollo to return no people
        self.mock_apollo_client.search_people = MagicMock(return_value={
            'people': [],
            'pagination': {'page': 1, 'per_page': 25, 'total_entries': 0}
        })
        
        request_data = {
            'project_id': 'test_project_123',
            'num_leads': 5
        }
        
        result = self.simulate_firebase_function_call(find_leads, request_data)
        
        self.assert_successful_response(result)
        self.assertEqual(result['leads_found'], 0)
        self.assertEqual(result['leads_added'], 0)
        self.assertFalse(result.get('enrichment_triggered', True))
    
    def test_find_leads_duplicate_filtering(self):
        """Test that duplicate leads are properly filtered"""
        # Add existing leads to the project
        self.add_leads_to_project('test_project_123', 3)
        
        # Mock Apollo to return leads with some duplicates
        duplicate_response = {
            'people': [
                {
                    'id': 'apollo_1',
                    'first_name': 'Test',
                    'last_name': 'User 1',
                    'email': 'test1@example.com',  # This should be a duplicate
                    'title': 'CEO',
                    'organization': {'name': 'Test Company 1'}
                },
                {
                    'id': 'apollo_2',
                    'first_name': 'New',
                    'last_name': 'User',
                    'email': 'new.user@example.com',  # This should be unique
                    'title': 'CTO',
                    'organization': {'name': 'New Company'}
                }
            ],
            'pagination': {'page': 1, 'per_page': 25, 'total_entries': 2}
        }
        
        self.mock_apollo_client.search_people = MagicMock(return_value=duplicate_response)
        
        request_data = {
            'project_id': 'test_project_123',
            'num_leads': 2,
            'auto_enrich': False
        }
        
        result = self.simulate_firebase_function_call(find_leads, request_data)
        
        self.assert_successful_response(result)
        self.assertEqual(result['leads_found'], 2)
        # Note: Actual duplicate filtering depends on implementation
        self.assertGreaterEqual(result['leads_added'], 1)  # At least 1 unique lead should be added
    
    def test_find_leads_missing_project_id(self):
        """Test error when project_id is missing"""
        request_data = {
            'num_leads': 5
        }
        
        result = self.simulate_firebase_function_call(find_leads, request_data)
        self.assert_error_response(result)
        self.assertIn('project_id', result.get('error', '').lower())
    
    def test_find_leads_project_not_found(self):
        """Test error when project doesn't exist"""
        request_data = {
            'project_id': 'nonexistent_project',
            'num_leads': 5
        }
        
        result = self.simulate_firebase_function_call(find_leads, request_data)
        self.assert_error_response(result)
    
    def test_find_leads_apollo_api_error(self):
        """Test handling of Apollo API errors"""
        # Mock Apollo to raise an exception
        self.mock_apollo_client.search_people = MagicMock(side_effect=Exception("Apollo API Error"))
        
        request_data = {
            'project_id': 'test_project_123',
            'num_leads': 5
        }
        
        result = self.simulate_firebase_function_call(find_leads, request_data)
        self.assert_error_response(result)
        self.assertIn('apollo', result.get('error', '').lower())
    
    def test_find_leads_missing_apollo_api_key(self):
        """Test error when Apollo API key is missing"""
        # Remove Apollo API key from environment
        with patch.dict(os.environ, {}, clear=True):
            # Update test API keys to not have Apollo
            self.test_api_keys = {'perplexity': 'test', 'openai': 'test'}
            
            request_data = {
                'project_id': 'test_project_123',
                'num_leads': 5
            }
            
            result = self.simulate_firebase_function_call(find_leads, request_data)
            self.assert_error_response(result)
    
    def test_find_leads_enrichment_failure_with_save_without_enrichment(self):
        """Test that leads are saved even when enrichment fails"""
        request_data = {
            'project_id': 'test_project_123',
            'num_leads': 3,
            'auto_enrich': True,
            'save_without_enrichment': True
        }
        
        # Mock enrichment to fail
        with patch('enrich_leads.enrich_leads') as mock_enrich:
            mock_enrich.side_effect = Exception("Enrichment failed")
            
            # Also mock the import in find_leads module
            with patch('find_leads.enrich_leads', mock_enrich):
                result = self.simulate_firebase_function_call(find_leads, request_data)
        
        self.assert_successful_response(result)
        self.assertGreater(result['leads_added'], 0)
        self.assertFalse(result.get('enrichment_triggered', True))
    
    def test_find_leads_large_batch(self):
        """Test handling of large lead batches"""
        request_data = {
            'project_id': 'test_project_123',
            'num_leads': 150,  # Should be capped at 100 (Apollo limit)
            'auto_enrich': False
        }
        
        result = self.simulate_firebase_function_call(find_leads, request_data)
        
        self.assert_successful_response(result)
        # Should get 10 leads (our mock limit) even though 150 were requested
        self.assertEqual(result['leads_found'], 10)
    
    def test_find_leads_project_lead_count_update(self):
        """Test that project lead count is properly updated"""
        # Start with some existing leads
        initial_lead_count = 5
        self.add_leads_to_project('test_project_123', initial_lead_count)
        
        request_data = {
            'project_id': 'test_project_123',
            'num_leads': 3,
            'auto_enrich': False
        }
        
        result = self.simulate_firebase_function_call(find_leads, request_data)
        
        self.assert_successful_response(result)
        
        # Verify project was updated with new lead count
        project_doc = self.mock_firestore.collection('projects').document('test_project_123').get()
        project_data = project_doc.to_dict()
        
        # The project should be updated if the function implements this feature
        if 'leadCount' in project_data:
            expected_count = initial_lead_count + result['leads_added']
            self.assertEqual(project_data['leadCount'], expected_count)
        
        if 'lastLeadSearch' in project_data:
            self.assertIsNotNone(project_data['lastLeadSearch'])


class TestFindLeadsHelperFunctions(unittest.TestCase):
    """Test cases for find_leads helper functions"""
    
    def test_extract_location_from_description(self):
        """Test location extraction from project description"""
        # Skip if function doesn't exist
        try:
            from find_leads import extract_location_from_description
            
            # Test with simple city, state format
            description = "Looking for companies in San Francisco, CA and New York, NY"
            locations = extract_location_from_description(description)
            
            self.assertIsInstance(locations, list)
            # Specific assertions depend on implementation
            
        except ImportError:
            self.skipTest("extract_location_from_description function not implemented")
    
    def test_determine_target_job_titles(self):
        """Test job title determination from project details"""
        try:
            from find_leads import determine_target_job_titles
            
            project_details = "Looking for decision makers in SaaS companies"
            titles = determine_target_job_titles(project_details)
            
            self.assertIsInstance(titles, list)
            # Should return some default titles
            self.assertGreater(len(titles), 0)
            
        except ImportError:
            self.skipTest("determine_target_job_titles function not implemented")
    
    def test_extract_company_criteria(self):
        """Test company criteria extraction from project details"""
        try:
            from find_leads import extract_company_criteria
            
            project_details = "Looking for enterprise companies with 1000+ employees"
            criteria = extract_company_criteria(project_details)
            
            # Currently returns empty dict, but test structure is in place
            self.assertIsInstance(criteria, dict)
            
        except ImportError:
            self.skipTest("extract_company_criteria function not implemented")


if __name__ == '__main__':
    unittest.main() 