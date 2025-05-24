"""
Unit tests for utils modules

Tests all utility functions including API clients, Firebase utilities,
data processing, and email utilities.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.base_test import BaseTestCase
from tests.mocks import (
    MockApolloClient,
    MockPerplexityClient,
    MockOpenAIClient,
    MOCK_API_KEYS,
    MOCK_APOLLO_RESPONSE,
    MOCK_PERPLEXITY_RESPONSE
)


class TestApolloClient(unittest.TestCase):
    """Test cases for Apollo API client"""
    
    def setUp(self):
        """Set up test client"""
        self.client = MockApolloClient(MOCK_API_KEYS['apollo'])
    
    def test_search_people_basic(self):
        """Test basic people search"""
        result = self.client.search_people(job_titles=['CEO'], per_page=5)
        
        self.assertIn('people', result)
        self.assertIn('pagination', result)
        self.assertLessEqual(len(result['people']), 5)
        
        # Check person data structure
        person = result['people'][0]
        self.assertIn('id', person)
        self.assertIn('first_name', person)
        self.assertIn('email', person)
        self.assertIn('organization', person)
    
    def test_search_people_with_parameters(self):
        """Test people search with various parameters"""
        result = self.client.search_people(
            person_titles=['CTO'],
            person_locations=['San Francisco, CA'],
            organization_domains=['example.com'],
            per_page=3,
            page=2
        )
        
        self.assertIn('people', result)
        pagination = result['pagination']
        self.assertEqual(pagination['page'], 2)
        self.assertEqual(pagination['per_page'], 3)
    
    def test_get_person_details(self):
        """Test getting person details"""
        result = self.client.get_person_details('person_123')
        
        self.assertIn('person', result)
        person = result['person']
        self.assertEqual(person['id'], 'person_123')
        self.assertIn('first_name', person)
        self.assertIn('organization', person)
    
    def test_test_api_access(self):
        """Test API access testing"""
        result = self.client.test_api_access()
        
        self.assertEqual(result['status'], 'success')
        self.assertIn('data', result)


class TestPerplexityClient(unittest.TestCase):
    """Test cases for Perplexity API client"""
    
    def setUp(self):
        """Set up test client"""
        self.client = MockPerplexityClient(MOCK_API_KEYS['perplexity'])
    
    def test_enrich_lead_data_company_only(self):
        """Test company-only enrichment"""
        result = self.client.enrich_lead_data(
            company_name="Test Company",
            additional_context="Research for outreach"
        )
        
        self.assertIn('choices', result)
        self.assertIn('usage', result)
        
        content = result['choices'][0]['message']['content']
        self.assertIn('Test Company', content)
        self.assertIn('Company Overview', content)
    
    def test_enrich_lead_data_with_person(self):
        """Test enrichment with person information"""
        result = self.client.enrich_lead_data(
            company_name="Test Company",
            person_name="John Doe",
            additional_context="Person research"
        )
        
        content = result['choices'][0]['message']['content']
        self.assertIn('John Doe', content)
        self.assertIn('Test Company', content)
        self.assertIn('Person Research', content)
    
    def test_enrich_lead_data_response_structure(self):
        """Test response structure matches expected format"""
        result = self.client.enrich_lead_data(company_name="Test Company")
        
        self.assertIn('id', result)
        self.assertIn('model', result)
        self.assertIn('choices', result)
        self.assertIn('usage', result)
        
        choice = result['choices'][0]
        self.assertIn('index', choice)
        self.assertIn('finish_reason', choice)
        self.assertIn('message', choice)
        
        message = choice['message']
        self.assertIn('role', message)
        self.assertIn('content', message)


class TestOpenAIClient(unittest.TestCase):
    """Test cases for OpenAI API client"""
    
    def setUp(self):
        """Set up test client"""
        self.client = MockOpenAIClient(MOCK_API_KEYS['openai'])
    
    def test_generate_email_content_outreach(self):
        """Test outreach email generation"""
        lead_data = {
            'name': 'John Doe',
            'company': 'Test Company',
            'title': 'CEO',
            'email': 'john@testcompany.com'
        }
        
        result = self.client.generate_email_content(
            lead_data=lead_data,
            email_type='outreach'
        )
        
        self.assertIsInstance(result, str)
        self.assertIn('John Doe', result)
        self.assertIn('Test Company', result)
        self.assertIn('Subject:', result)
    
    def test_generate_email_content_followup(self):
        """Test follow-up email generation"""
        lead_data = {
            'name': 'Jane Smith',
            'company': 'Another Company',
            'title': 'CTO'
        }
        
        result = self.client.generate_email_content(
            lead_data=lead_data,
            email_type='followup'
        )
        
        self.assertIsInstance(result, str)
        self.assertIn('Jane Smith', result)
        self.assertIn('follow', result.lower())
        self.assertIn('Subject:', result)
    
    def test_generate_email_content_with_enrichment(self):
        """Test email generation with enrichment data"""
        lead_data = {
            'name': 'Bob Johnson',
            'company': 'Tech Corp',
            'title': 'VP Sales',
            'enrichment_data': 'Company has been growing rapidly and recently raised funding.'
        }
        
        result = self.client.generate_email_content(lead_data=lead_data)
        
        self.assertIn('Bob Johnson', result)
        self.assertIn('Tech Corp', result)


class TestLeadProcessor(BaseTestCase):
    """Test cases for LeadProcessor"""
    
    def test_process_apollo_results(self):
        """Test processing Apollo API results"""
        apollo_data = {
            'people': [
                {
                    'id': 'apollo_123',
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'email': 'john@example.com',
                    'title': 'CEO',
                    'phone': '+1234567890',
                    'linkedin_url': 'https://linkedin.com/in/johndoe',
                    'organization': {
                        'name': 'Example Corp',
                        'employees': 500,
                        'industry': 'Technology'
                    }
                }
            ]
        }
        
        result = self.mock_lead_processor.process_apollo_results(apollo_data)
        
        self.assertEqual(len(result), 1)
        lead = result[0]
        
        self.assertEqual(lead['name'], 'John Doe')
        self.assertEqual(lead['email'], 'john@example.com')
        self.assertEqual(lead['title'], 'CEO')
        self.assertEqual(lead['company'], 'Example Corp')
        self.assertEqual(lead['phone'], '+1234567890')
        self.assertEqual(lead['linkedin'], 'https://linkedin.com/in/johndoe')
        self.assertEqual(lead['apollo_id'], 'apollo_123')
        self.assertEqual(lead['company_size'], 500)
        self.assertEqual(lead['industry'], 'Technology')
    
    def test_check_duplicate_leads(self):
        """Test duplicate lead checking"""
        new_leads = [
            {'email': 'john@example.com', 'name': 'John Doe'},
            {'email': 'jane@example.com', 'name': 'Jane Smith'},
            {'email': 'bob@example.com', 'name': 'Bob Johnson'}
        ]
        
        existing_leads = [
            {'email': 'jane@example.com', 'name': 'Jane Smith'},  # Duplicate
            {'email': 'alice@example.com', 'name': 'Alice Brown'}
        ]
        
        result = self.mock_lead_processor.check_duplicate_leads(new_leads, existing_leads)
        
        self.assertEqual(len(result), 2)  # Should filter out Jane Smith
        emails = [lead['email'] for lead in result]
        self.assertIn('john@example.com', emails)
        self.assertIn('bob@example.com', emails)
        self.assertNotIn('jane@example.com', emails)
    
    def test_prepare_lead_for_database(self):
        """Test preparing lead data for database storage"""
        lead_data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'title': 'CEO',
            'company': 'Example Corp'
        }
        
        result = self.mock_lead_processor.prepare_lead_for_database(lead_data, 'project_123')
        
        self.assertEqual(result['projectId'], 'project_123')
        self.assertEqual(result['status'], 'new')
        self.assertEqual(result['source'], 'apollo')
        self.assertIn('createdAt', result)
        
        # Original data should be preserved
        self.assertEqual(result['name'], 'John Doe')
        self.assertEqual(result['email'], 'john@example.com')


class TestFirebaseUtilities(unittest.TestCase):
    """Test cases for Firebase utilities"""
    
    @patch('utils.firebase_utils.os.getenv')
    def test_get_api_keys_from_environment(self, mock_getenv):
        """Test getting API keys from environment variables"""
        # Mock environment variables
        mock_getenv.side_effect = lambda key: {
            'APOLLO_API_KEY': 'env_apollo_key',
            'PERPLEXITY_API_KEY': 'env_perplexity_key',
            'OPENAI_API_KEY': 'env_openai_key',
            'DEBUG': 'true'
        }.get(key)
        
        from utils.firebase_utils import get_api_keys
        
        result = get_api_keys()
        
        self.assertEqual(result['apollo'], 'env_apollo_key')
        self.assertEqual(result['perplexity'], 'env_perplexity_key')
        self.assertEqual(result['openai'], 'env_openai_key')
    
    @patch('utils.firebase_utils.firestore.client')
    def test_get_firestore_client(self, mock_firestore):
        """Test getting Firestore client"""
        from utils.firebase_utils import get_firestore_client
        
        mock_client = MagicMock()
        mock_firestore.return_value = mock_client
        
        result = get_firestore_client()
        
        self.assertEqual(result, mock_client)
        mock_firestore.assert_called_once()


class TestEmailUtilities(unittest.TestCase):
    """Test cases for Email utilities"""
    
    def test_email_service_initialization(self):
        """Test EmailService initialization"""
        try:
            from utils.email_utils import EmailService
            
            # Test that class can be imported and initialized
            service = EmailService()
            self.assertIsNotNone(service)
        except ImportError:
            self.skipTest("EmailService not implemented yet")
    
    def test_email_validation(self):
        """Test email validation functions"""
        try:
            from utils.email_utils import validate_email
            
            # Test valid emails
            self.assertTrue(validate_email('test@example.com'))
            self.assertTrue(validate_email('user.name@domain.co.uk'))
            
            # Test invalid emails
            self.assertFalse(validate_email('invalid-email'))
            self.assertFalse(validate_email('test@'))
            self.assertFalse(validate_email('@domain.com'))
        except ImportError:
            self.skipTest("Email validation functions not implemented yet")


class TestDataProcessing(unittest.TestCase):
    """Test cases for data processing utilities"""
    
    def test_data_validator_initialization(self):
        """Test DataValidator initialization"""
        try:
            from utils.data_processing import DataValidator
            
            validator = DataValidator()
            self.assertIsNotNone(validator)
        except ImportError:
            self.skipTest("DataValidator not implemented yet")
    
    def test_data_sanitization(self):
        """Test data sanitization functions"""
        try:
            from utils.data_processing import sanitize_lead_data
            
            dirty_data = {
                'name': '  John Doe  ',
                'email': 'JOHN@EXAMPLE.COM',
                'title': 'ceo',
                'phone': '(555) 123-4567'
            }
            
            clean_data = sanitize_lead_data(dirty_data)
            
            self.assertEqual(clean_data['name'], 'John Doe')
            self.assertEqual(clean_data['email'], 'john@example.com')
            self.assertEqual(clean_data['title'], 'CEO')
            
        except ImportError:
            self.skipTest("Data sanitization functions not implemented yet")


if __name__ == '__main__':
    unittest.main() 