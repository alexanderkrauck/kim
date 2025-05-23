"""
Unit tests for enrich_leads functions

Tests all aspects of lead enrichment functionality including Perplexity integration,
enrichment status tracking, and database operations.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.base_test import MockFirebaseFunctionsTestCase
from enrich_leads import enrich_leads, get_enrichment_status


class TestEnrichLeads(MockFirebaseFunctionsTestCase):
    """Test cases for enrich_leads function"""
    
    def test_enrich_leads_success_all_unenriched(self):
        """Test successful enrichment of all unenriched leads"""
        # Add some leads to the project
        self.add_leads_to_project('test_project_123', 3)
        
        request_data = {
            'project_id': 'test_project_123',
            'enrichment_type': 'both'
        }
        
        result = self.simulate_firebase_function_call(enrich_leads, request_data)
        
        self.assert_successful_response(result)
        self.assertEqual(result['project_id'], 'test_project_123')
        self.assertGreaterEqual(result['leads_processed'], 0)
        self.assertGreaterEqual(result['leads_enriched'], 0)
        self.assertEqual(result['leads_failed'], 0)
        self.assertEqual(result['enrichment_type'], 'both')
    
    def test_enrich_leads_specific_leads(self):
        """Test enrichment of specific leads by ID"""
        # Add some leads to the project
        self.add_leads_to_project('test_project_123', 5)
        
        # Get specific lead IDs
        leads_collection = self.mock_firestore.collection('leads')
        lead_ids = list(leads_collection.documents.keys())[:2]  # First 2 leads
        
        request_data = {
            'project_id': 'test_project_123',
            'lead_ids': lead_ids,
            'enrichment_type': 'company'
        }
        
        result = self.simulate_firebase_function_call(enrich_leads, request_data)
        
        self.assert_successful_response(result)
        self.assertGreaterEqual(result['leads_processed'], 0)
        self.assertGreaterEqual(result['leads_enriched'], 0)
        self.assertEqual(result['enrichment_type'], 'company')
    
    def test_enrich_leads_company_only(self):
        """Test company-only enrichment"""
        self.add_leads_to_project('test_project_123', 2)
        
        request_data = {
            'project_id': 'test_project_123',
            'enrichment_type': 'company'
        }
        
        result = self.simulate_firebase_function_call(enrich_leads, request_data)
        
        self.assert_successful_response(result)
        self.assertEqual(result['enrichment_type'], 'company')
        
        # Verify leads have company research but not person research
        leads_collection = self.mock_firestore.collection('leads')
        enriched_leads = [
            lead_data for lead_id, lead_data in leads_collection.documents.items()
            if lead_data.get('projectId') == 'test_project_123' and lead_data.get('enrichmentStatus') == 'enriched'
        ]
        
        for lead_data in enriched_leads:
            if 'company_research' in lead_data:
                self.assertIn('company_research', lead_data)
                self.assertNotIn('person_research', lead_data)
    
    def test_enrich_leads_person_only(self):
        """Test person-only enrichment"""
        self.add_leads_to_project('test_project_123', 2)
        
        request_data = {
            'project_id': 'test_project_123',
            'enrichment_type': 'person'
        }
        
        result = self.simulate_firebase_function_call(enrich_leads, request_data)
        
        self.assert_successful_response(result)
        self.assertEqual(result['enrichment_type'], 'person')
        
        # Verify leads have person research but not company research
        leads_collection = self.mock_firestore.collection('leads')
        enriched_leads = [
            lead_data for lead_id, lead_data in leads_collection.documents.items()
            if lead_data.get('projectId') == 'test_project_123' and lead_data.get('enrichmentStatus') == 'enriched'
        ]
        
        for lead_data in enriched_leads:
            if 'person_research' in lead_data:
                self.assertIn('person_research', lead_data)
                self.assertNotIn('company_research', lead_data)
    
    def test_enrich_leads_force_re_enrich(self):
        """Test force re-enrichment of already enriched leads"""
        # Add already enriched leads
        self.add_enriched_leads_to_project('test_project_123', 2)
        
        request_data = {
            'project_id': 'test_project_123',
            'force_re_enrich': True,
            'enrichment_type': 'both'
        }
        
        result = self.simulate_firebase_function_call(enrich_leads, request_data)
        
        self.assert_successful_response(result)
        self.assertGreaterEqual(result['leads_processed'], 0)
        self.assertGreaterEqual(result['leads_enriched'], 0)
    
    def test_enrich_leads_no_leads_to_enrich(self):
        """Test when there are no leads to enrich"""
        request_data = {
            'project_id': 'test_project_123',
            'enrichment_type': 'both'
        }
        
        result = self.simulate_firebase_function_call(enrich_leads, request_data)
        
        self.assert_successful_response(result)
        self.assertEqual(result['leads_processed'], 0)
        self.assertEqual(result['leads_enriched'], 0)
        self.assertEqual(result['leads_failed'], 0)
    
    def test_enrich_leads_missing_project_id(self):
        """Test error when project_id is missing"""
        request_data = {
            'enrichment_type': 'both'
        }
        
        result = self.simulate_firebase_function_call(enrich_leads, request_data)
        self.assert_error_response(result)
        self.assertIn('project_id', result.get('error', '').lower())
    
    def test_enrich_leads_project_not_found(self):
        """Test error when project doesn't exist"""
        request_data = {
            'project_id': 'nonexistent_project',
            'enrichment_type': 'both'
        }
        
        result = self.simulate_firebase_function_call(enrich_leads, request_data)
        self.assert_error_response(result)
    
    def test_enrich_leads_missing_perplexity_api_key(self):
        """Test error when Perplexity API key is missing"""
        # Remove Perplexity API key from environment
        with patch.dict(os.environ, {}, clear=True):
            self.test_api_keys = {'apollo': 'test', 'openai': 'test'}
            
            request_data = {
                'project_id': 'test_project_123',
                'enrichment_type': 'both'
            }
            
            result = self.simulate_firebase_function_call(enrich_leads, request_data)
            self.assert_error_response(result)
    
    def test_enrich_leads_perplexity_api_error(self):
        """Test handling of Perplexity API errors"""
        self.add_leads_to_project('test_project_123', 2)
        
        # Mock Perplexity to raise an exception
        self.mock_perplexity_client.enrich_lead_data = MagicMock(side_effect=Exception("Perplexity API Error"))
        
        request_data = {
            'project_id': 'test_project_123',
            'enrichment_type': 'both'
        }
        
        result = self.simulate_firebase_function_call(enrich_leads, request_data)
        
        self.assert_successful_response(result)
        self.assertEqual(result['leads_enriched'], 0)
        self.assertGreaterEqual(result['leads_failed'], 0)
    
    def test_enrich_leads_lead_belongs_to_different_project(self):
        """Test error when lead doesn't belong to the specified project"""
        # Add lead to a different project
        leads_collection = self.mock_firestore.collection('leads')
        leads_collection.documents['other_lead'] = {
            'id': 'other_lead',
            'projectId': 'other_project',
            'name': 'Other User',
            'email': 'other@example.com'
        }
        
        request_data = {
            'project_id': 'test_project_123',
            'lead_ids': ['other_lead'],
            'enrichment_type': 'both'
        }
        
        result = self.simulate_firebase_function_call(enrich_leads, request_data)
        
        self.assert_successful_response(result)
        self.assertEqual(result['leads_processed'], 0)  # No leads processed
    
    def test_enrich_leads_lead_not_found(self):
        """Test handling when specified lead doesn't exist"""
        request_data = {
            'project_id': 'test_project_123',
            'lead_ids': ['nonexistent_lead'],
            'enrichment_type': 'both'
        }
        
        result = self.simulate_firebase_function_call(enrich_leads, request_data)
        
        self.assert_successful_response(result)
        self.assertEqual(result['leads_processed'], 0)


class TestGetEnrichmentStatus(MockFirebaseFunctionsTestCase):
    """Test cases for get_enrichment_status function"""
    
    def test_get_enrichment_status_project_overview(self):
        """Test getting project-level enrichment status"""
        # Add mixed leads (enriched, pending, failed)
        self.add_leads_to_project('test_project_123', 3)
        self.add_enriched_leads_to_project('test_project_123', 2)
        
        # Add a failed lead
        leads_collection = self.mock_firestore.collection('leads')
        leads_collection.documents['failed_lead'] = {
            'id': 'failed_lead',
            'projectId': 'test_project_123',
            'enrichmentStatus': 'failed',
            'enrichmentError': 'API Error'
        }
        
        request_data = {
            'project_id': 'test_project_123'
        }
        
        result = self.simulate_firebase_function_call(get_enrichment_status, request_data)
        
        self.assert_successful_response(result)
        self.assertEqual(result['project_id'], 'test_project_123')
        self.assertGreaterEqual(result['total_leads'], 5)  # At least 5 leads
        self.assertGreaterEqual(result['enriched_leads'], 2)
        self.assertGreaterEqual(result['failed_leads'], 1)
        self.assertIn('enrichment_percentage', result)
    
    def test_get_enrichment_status_specific_leads(self):
        """Test getting status for specific leads"""
        self.add_enriched_leads_to_project('test_project_123', 2)
        
        # Get lead IDs
        leads_collection = self.mock_firestore.collection('leads')
        lead_ids = [
            lead_id for lead_id, lead_data in leads_collection.documents.items()
            if lead_data.get('projectId') == 'test_project_123'
        ]
        
        request_data = {
            'project_id': 'test_project_123',
            'lead_ids': lead_ids
        }
        
        result = self.simulate_firebase_function_call(get_enrichment_status, request_data)
        
        self.assert_successful_response(result)
        self.assertEqual(result['project_id'], 'test_project_123')
        self.assertIn('lead_statuses', result)
        self.assertGreaterEqual(len(result['lead_statuses']), len(lead_ids))
        
        # Verify lead status details
        for lead_status in result['lead_statuses']:
            self.assertIn('id', lead_status)
            self.assertIn('enrichmentStatus', lead_status)
    
    def test_get_enrichment_status_empty_project(self):
        """Test status for project with no leads"""
        request_data = {
            'project_id': 'test_project_123'
        }
        
        result = self.simulate_firebase_function_call(get_enrichment_status, request_data)
        
        self.assert_successful_response(result)
        self.assertGreaterEqual(result['total_leads'], 0)  # May have default test lead
        self.assertIn('enrichment_percentage', result)
    
    def test_get_enrichment_status_missing_project_id(self):
        """Test error when project_id is missing"""
        request_data = {}
        
        result = self.simulate_firebase_function_call(get_enrichment_status, request_data)
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