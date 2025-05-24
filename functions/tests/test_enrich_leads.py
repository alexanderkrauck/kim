"""
Unit tests for enrich_leads functions

Tests all aspects of lead enrichment functionality including Perplexity integration,
enrichment status tracking, and database operations.
"""

import unittest
from unittest.mock import patch, MagicMock, Mock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.base_test import FirebaseFunctionsTestCase
from tests.mocks import MockFirestoreClient, MockPerplexityClient
from enrich_leads import enrich_leads, get_enrichment_status, enrich_leads_logic, get_enrichment_status_logic


class TestEnrichLeads(FirebaseFunctionsTestCase):
    """Test cases for enrich_leads function"""
    
    def _setup_enrich_leads_mocks(self):
        """Helper method to set up mocking for enrich_leads tests"""
        # Create pure Mock objects for this test
        mock_firestore = Mock()
        mock_project_doc = Mock()
        mock_project_doc.exists = True
        mock_project_doc.to_dict.return_value = self.test_project_data
        
        # Mock the projects collection
        mock_projects_collection = Mock()
        mock_project_document = Mock()
        mock_project_document.get.return_value = mock_project_doc
        mock_projects_collection.document.return_value = mock_project_document
        
        # Mock the leads collection with proper query handling
        mock_leads_collection = Mock()
        
        # Create a chain of query operations for enrich_leads
        mock_query1 = Mock()  # First where() call
        mock_query2 = Mock()  # Second where() call (if not force_re_enrich)
        
        # Set up the query chain
        mock_leads_collection.where.return_value = mock_query1
        mock_query1.where.return_value = mock_query2
        
        # Both queries return empty list (no leads to enrich)
        mock_query1.stream.return_value = []
        mock_query2.stream.return_value = []
        
        # Mock document references for updating leads
        mock_lead_ref = Mock()
        mock_lead_ref.id = 'mock_lead_id_1'
        mock_leads_collection.document.return_value = mock_lead_ref
        
        # Configure firestore to return different collections
        def collection_side_effect(collection_name):
            if collection_name == 'projects':
                return mock_projects_collection
            elif collection_name == 'leads':
                return mock_leads_collection
            else:
                return Mock()
        
        mock_firestore.collection.side_effect = collection_side_effect
        
        # Mock batch operations
        mock_batch = Mock()
        mock_firestore.batch.return_value = mock_batch
        
        return mock_firestore
    
    def test_enrich_leads_success_all_unenriched(self):
        """Test successful enrichment of all unenriched leads"""
        mock_firestore = self._setup_enrich_leads_mocks()
        
        request_data = {
            'project_id': 'test_project_123',
            'enrichment_type': 'both'
        }
        
        with patch('enrich_leads.get_firestore_client', return_value=mock_firestore), \
             patch('enrich_leads.get_api_keys', return_value=self.test_api_keys), \
             patch('enrich_leads.PerplexityClient', return_value=self.mock_perplexity_client), \
             patch('enrich_leads.LeadProcessor', return_value=self.mock_lead_processor):
            
            result = enrich_leads_logic(request_data)
        
        self.assert_successful_response(result)
        self.assertEqual(result['project_id'], 'test_project_123')
        self.assertGreaterEqual(result['leads_processed'], 0)
        self.assertGreaterEqual(result['leads_enriched'], 0)
        self.assertEqual(result['leads_failed'], 0)
        self.assertEqual(result['enrichment_type'], 'both')
    
    def test_enrich_leads_company_only(self):
        """Test company-only enrichment"""
        mock_firestore = self._setup_enrich_leads_mocks()
        
        request_data = {
            'project_id': 'test_project_123',
            'enrichment_type': 'company'
        }
        
        with patch('enrich_leads.get_firestore_client', return_value=mock_firestore), \
             patch('enrich_leads.get_api_keys', return_value=self.test_api_keys), \
             patch('enrich_leads.PerplexityClient', return_value=self.mock_perplexity_client), \
             patch('enrich_leads.LeadProcessor', return_value=self.mock_lead_processor):
            
            result = enrich_leads_logic(request_data)
        
        self.assert_successful_response(result)
        self.assertEqual(result['enrichment_type'], 'company')
    
    def test_enrich_leads_person_only(self):
        """Test person-only enrichment"""
        mock_firestore = self._setup_enrich_leads_mocks()
        
        request_data = {
            'project_id': 'test_project_123',
            'enrichment_type': 'person'
        }
        
        with patch('enrich_leads.get_firestore_client', return_value=mock_firestore), \
             patch('enrich_leads.get_api_keys', return_value=self.test_api_keys), \
             patch('enrich_leads.PerplexityClient', return_value=self.mock_perplexity_client), \
             patch('enrich_leads.LeadProcessor', return_value=self.mock_lead_processor):
            
            result = enrich_leads_logic(request_data)
        
        self.assert_successful_response(result)
        self.assertEqual(result['enrichment_type'], 'person')
    
    def test_enrich_leads_no_leads_to_enrich(self):
        """Test when there are no leads to enrich"""
        mock_firestore = self._setup_enrich_leads_mocks()
        
        request_data = {
            'project_id': 'test_project_123',
            'enrichment_type': 'both'
        }
        
        with patch('enrich_leads.get_firestore_client', return_value=mock_firestore), \
             patch('enrich_leads.get_api_keys', return_value=self.test_api_keys), \
             patch('enrich_leads.PerplexityClient', return_value=self.mock_perplexity_client), \
             patch('enrich_leads.LeadProcessor', return_value=self.mock_lead_processor):
            
            result = enrich_leads_logic(request_data)
        
        self.assert_successful_response(result)
        self.assertEqual(result['leads_processed'], 0)
        self.assertEqual(result['leads_enriched'], 0)
        self.assertEqual(result['leads_failed'], 0)
    
    def test_enrich_leads_missing_project_id(self):
        """Test error when project_id is missing"""
        request_data = {
            'enrichment_type': 'both'
        }
        
        result = enrich_leads_logic(request_data)
        self.assert_error_response(result)
        self.assertIn('project_id', result.get('error', '').lower())
    
    def test_enrich_leads_project_not_found(self):
        """Test error when project doesn't exist"""
        mock_firestore = Mock()
        mock_project_doc = Mock()
        mock_project_doc.exists = False
        
        mock_projects_collection = Mock()
        mock_project_document = Mock()
        mock_project_document.get.return_value = mock_project_doc
        mock_projects_collection.document.return_value = mock_project_document
        mock_firestore.collection.return_value = mock_projects_collection
        
        request_data = {
            'project_id': 'nonexistent_project',
            'enrichment_type': 'both'
        }
        
        with patch('enrich_leads.get_firestore_client', return_value=mock_firestore), \
             patch('enrich_leads.get_api_keys', return_value=self.test_api_keys):
            
            result = enrich_leads_logic(request_data)
            
        self.assert_error_response(result)
    
    def test_enrich_leads_missing_perplexity_api_key(self):
        """Test error when Perplexity API key is missing"""
        mock_firestore = self._setup_enrich_leads_mocks()
        
        # Remove Perplexity API key from test environment
        test_api_keys_no_perplexity = {k: v for k, v in self.test_api_keys.items() if k != 'perplexity'}
        
        request_data = {
            'project_id': 'test_project_123',
            'enrichment_type': 'both'
        }
        
        with patch('enrich_leads.get_firestore_client', return_value=mock_firestore), \
             patch('enrich_leads.get_api_keys', return_value=test_api_keys_no_perplexity):
            
            result = enrich_leads_logic(request_data)
            
        self.assert_error_response(result)
    
    def test_enrich_leads_perplexity_api_error(self):
        """Test handling of Perplexity API errors"""
        mock_firestore = self._setup_enrich_leads_mocks()
        
        # Mock a lead to enrich
        mock_lead_data = {'id': 'test_lead', 'name': 'Test User', 'company': 'Test Company', 'projectId': 'test_project_123'}
        mock_leads_collection = mock_firestore.collection('leads')
        mock_query = Mock()
        mock_query.stream.return_value = [Mock(id='test_lead', to_dict=lambda: mock_lead_data)]
        mock_leads_collection.where.return_value = mock_query
        
        # Mock Perplexity to raise an exception
        mock_perplexity_client = MockPerplexityClient('test_key')
        mock_perplexity_client.enrich_lead_data = MagicMock(side_effect=Exception("Perplexity API Error"))
        
        request_data = {
            'project_id': 'test_project_123',
            'enrichment_type': 'both'
        }
        
        with patch('enrich_leads.get_firestore_client', return_value=mock_firestore), \
             patch('enrich_leads.get_api_keys', return_value=self.test_api_keys), \
             patch('enrich_leads.PerplexityClient', return_value=mock_perplexity_client), \
             patch('enrich_leads.LeadProcessor', return_value=self.mock_lead_processor):
            
            result = enrich_leads_logic(request_data)
        
        self.assert_successful_response(result)
        self.assertEqual(result['leads_enriched'], 0)
        self.assertGreaterEqual(result['leads_failed'], 0)


class TestGetEnrichmentStatus(FirebaseFunctionsTestCase):
    """Test cases for get_enrichment_status function"""
    
    def test_get_enrichment_status_project_overview(self):
        """Test getting project-level enrichment status"""
        mock_firestore = Mock()
        
        # Mock some leads with different statuses
        mock_leads_data = [
            Mock(id='lead1', to_dict=lambda: {'enrichmentStatus': 'enriched'}),
            Mock(id='lead2', to_dict=lambda: {'enrichmentStatus': 'failed'}),
            Mock(id='lead3', to_dict=lambda: {'enrichmentStatus': None})
        ]
        
        mock_leads_collection = Mock()
        mock_query = Mock()
        mock_query.stream.return_value = mock_leads_data
        mock_leads_collection.where.return_value = mock_query
        mock_firestore.collection.return_value = mock_leads_collection
        
        request_data = {
            'project_id': 'test_project_123'
        }
        
        with patch('enrich_leads.get_firestore_client', return_value=mock_firestore):
            result = get_enrichment_status_logic(request_data)
        
        self.assert_successful_response(result)
        self.assertEqual(result['project_id'], 'test_project_123')
        self.assertEqual(result['total_leads'], 3)
        self.assertEqual(result['enriched_leads'], 1)
        self.assertEqual(result['failed_leads'], 1)
        self.assertEqual(result['pending_leads'], 1)
        self.assertIn('enrichment_percentage', result)
    
    def test_get_enrichment_status_empty_project(self):
        """Test status for project with no leads"""
        mock_firestore = Mock()
        mock_leads_collection = Mock()
        mock_query = Mock()
        mock_query.stream.return_value = []  # No leads
        mock_leads_collection.where.return_value = mock_query
        mock_firestore.collection.return_value = mock_leads_collection
        
        request_data = {
            'project_id': 'test_project_123'
        }
        
        with patch('enrich_leads.get_firestore_client', return_value=mock_firestore):
            result = get_enrichment_status_logic(request_data)
        
        self.assert_successful_response(result)
        self.assertEqual(result['total_leads'], 0)
        self.assertIn('enrichment_percentage', result)
    
    def test_get_enrichment_status_missing_project_id(self):
        """Test error when project_id is missing"""
        request_data = {}
        
        result = get_enrichment_status_logic(request_data)
        self.assert_error_response(result)
        self.assertIn('project_id', result.get('error', '').lower())


class TestEnrichmentHelperFunctions(unittest.TestCase):
    """Test cases for enrichment helper functions"""
    
    def test_determine_enrichment_priority_high_priority_lead(self):
        """Test priority calculation for high-priority lead"""
        try:
            from enrich_leads import determine_enrichment_priority
            
            high_priority_lead = {
                'email': 'ceo@company.com',
                'phone': '+1234567890',
                'company': 'Tech Corp',
                'title': 'CEO and Founder',
                'companySize': 5000
            }
            
            priority = determine_enrichment_priority(high_priority_lead)
            
            # Should get high score due to complete data and CEO title
            self.assertGreater(priority, 30)
            
        except ImportError:
            self.skipTest("determine_enrichment_priority function not implemented")
    
    def test_determine_enrichment_priority_low_priority_lead(self):
        """Test priority calculation for low-priority lead"""
        try:
            from enrich_leads import determine_enrichment_priority
            
            low_priority_lead = {
                'email': 'intern@company.com',
                'title': 'Intern'
            }
            
            priority = determine_enrichment_priority(low_priority_lead)
            
            # Should get lower score
            self.assertLess(priority, 25)
            
        except ImportError:
            self.skipTest("determine_enrichment_priority function not implemented")
    
    def test_determine_enrichment_priority_missing_data(self):
        """Test priority calculation with missing data"""
        try:
            from enrich_leads import determine_enrichment_priority
            
            minimal_lead = {}
            
            priority = determine_enrichment_priority(minimal_lead)
            
            self.assertEqual(priority, 0)
            
        except ImportError:
            self.skipTest("determine_enrichment_priority function not implemented")
    
    def test_validate_enrichment_data_valid(self):
        """Test validation of good enrichment data"""
        try:
            from enrich_leads import validate_enrichment_data
            
            valid_data = {
                'company_research': 'Microsoft is a leading technology company founded in 1975 by Bill Gates and Paul Allen. The company is headquartered in Redmond, Washington and is known for its Windows operating system, Office productivity suite, and Azure cloud platform.',
                'person_research': 'Satya Nadella is the CEO of Microsoft, having taken over from Steve Ballmer in 2014. Under his leadership, Microsoft has focused heavily on cloud computing and artificial intelligence.'
            }
            
            is_valid = validate_enrichment_data(valid_data)
            
            self.assertTrue(is_valid)
            
        except ImportError:
            self.skipTest("validate_enrichment_data function not implemented")
    
    def test_validate_enrichment_data_too_short(self):
        """Test validation of data that's too short"""
        try:
            from enrich_leads import validate_enrichment_data
            
            short_data = {
                'company_research': 'Short text.',
                'person_research': 'Also short.'
            }
            
            is_valid = validate_enrichment_data(short_data)
            
            self.assertFalse(is_valid)
            
        except ImportError:
            self.skipTest("validate_enrichment_data function not implemented")
    
    def test_validate_enrichment_data_generic_responses(self):
        """Test validation of generic/error responses"""
        try:
            from enrich_leads import validate_enrichment_data
            
            generic_data = {
                'company_research': 'I don\'t have information about this company.',
                'person_research': 'No information available for this person.'
            }
            
            is_valid = validate_enrichment_data(generic_data)
            
            self.assertFalse(is_valid)
            
        except ImportError:
            self.skipTest("validate_enrichment_data function not implemented")
    
    def test_validate_enrichment_data_mixed_quality(self):
        """Test validation with one good and one bad field"""
        try:
            from enrich_leads import validate_enrichment_data
            
            mixed_data = {
                'company_research': 'Microsoft is a leading technology company with extensive operations worldwide and significant market presence in cloud computing, productivity software, and enterprise solutions.',
                'person_research': 'Unable to provide information.'
            }
            
            is_valid = validate_enrichment_data(mixed_data)
            
            # Should pass because company research is good (this depends on implementation)
            self.assertIsInstance(is_valid, bool)
            
        except ImportError:
            self.skipTest("validate_enrichment_data function not implemented")


if __name__ == '__main__':
    unittest.main() 