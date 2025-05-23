"""
Mock classes for API testing

This module provides mock implementations of all external APIs used in the system,
allowing for reliable testing without making actual API calls.
"""

from typing import Dict, List, Any, Optional
from unittest.mock import Mock, MagicMock
from datetime import datetime
import json


class MockApolloClient:
    """Mock implementation of Apollo.io API client"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.apollo.io/api/v1"
        
    def search_people(self, **kwargs) -> Dict[str, Any]:
        """Mock Apollo people search"""
        per_page = kwargs.get('per_page', 25)
        page = kwargs.get('page', 1)
        
        # Generate mock lead data
        mock_people = []
        for i in range(min(per_page, 10)):  # Limit to 10 for testing
            mock_person = {
                'id': f'apollo_person_{i + 1}',
                'first_name': f'John{i + 1}',
                'last_name': f'Doe{i + 1}',
                'email': f'john.doe{i + 1}@mockcompany{i + 1}.com',
                'title': 'CEO' if i % 3 == 0 else 'CTO' if i % 3 == 1 else 'VP Sales',
                'linkedin_url': f'https://linkedin.com/in/johndoe{i + 1}',
                'phone': f'+1555000{100 + i}',
                'organization': {
                    'id': f'apollo_org_{i + 1}',
                    'name': f'Mock Company {i + 1}',
                    'website_url': f'https://mockcompany{i + 1}.com',
                    'industry': 'Technology',
                    'employees': 100 + (i * 50),
                    'founded_year': 2010 + i
                }
            }
            mock_people.append(mock_person)
        
        return {
            'people': mock_people,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_entries': 1850,  # Mock total
                'total_pages': 74
            }
        }
    
    def get_person_details(self, person_id: str) -> Dict[str, Any]:
        """Mock getting person details"""
        return {
            'person': {
                'id': person_id,
                'first_name': 'John',
                'last_name': 'Doe',
                'email': 'john.doe@mockcompany.com',
                'title': 'CEO',
                'organization': {
                    'name': 'Mock Company',
                    'website_url': 'https://mockcompany.com'
                }
            }
        }
    
    def test_api_access(self) -> Dict[str, Any]:
        """Mock API access test"""
        return {
            'status': 'success',
            'data': {
                'user': {
                    'id': 'mock_user_123',
                    'email': 'test@example.com'
                }
            }
        }


class MockPerplexityClient:
    """Mock implementation of Perplexity API client"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.perplexity.ai"
        
    def enrich_lead_data(self, 
                        company_name: str,
                        person_name: str = None,
                        additional_context: str = None) -> Dict[str, Any]:
        """Mock lead enrichment"""
        
        # Generate different responses based on input
        if person_name:
            content = f"""
## Person Research: {person_name} at {company_name}

### Professional Background
{person_name} is a seasoned executive at {company_name} with extensive experience in the technology sector. 
They have been instrumental in driving innovation and growth at the company.

### Current Role
As a key leader at {company_name}, {person_name} oversees strategic initiatives and business development efforts.
They are known for their expertise in emerging technologies and market expansion.

### Recent Activities
- Led successful product launches in Q3 2024
- Spoke at major industry conferences
- Published thought leadership articles on industry trends

### Company Context
{company_name} is a forward-thinking organization that values innovation and customer success.
The company has been experiencing steady growth and is expanding into new markets.
            """.strip()
        else:
            content = f"""
## Company Research: {company_name}

### Company Overview
{company_name} is a leading technology company that specializes in innovative solutions for businesses.
Founded in 2015, the company has grown to serve over 1,000 customers worldwide.

### Recent Developments
- Raised $50M in Series B funding in 2024
- Launched new AI-powered product suite
- Expanded operations to European markets
- Achieved 150% year-over-year revenue growth

### Industry Position
{company_name} is positioned as an emerging leader in the technology sector, competing with established players
while maintaining a focus on innovation and customer service excellence.

### Technology Stack
The company utilizes modern cloud infrastructure and has invested heavily in AI and machine learning capabilities.
They are known for their scalable architecture and robust security practices.
            """.strip()
        
        return {
            'id': 'mock_perplexity_response',
            'model': 'llama-3.1-sonar-small-128k-online',
            'choices': [
                {
                    'index': 0,
                    'finish_reason': 'stop',
                    'message': {
                        'role': 'assistant',
                        'content': content
                    }
                }
            ],
            'usage': {
                'prompt_tokens': 50,
                'completion_tokens': 200,
                'total_tokens': 250
            }
        }


class MockOpenAIClient:
    """Mock implementation of OpenAI API client"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = Mock()
        
    def generate_email_content(self,
                              lead_data: Dict[str, Any],
                              email_type: str = "outreach",
                              custom_prompt: str = None) -> str:
        """Mock email generation"""
        
        name = lead_data.get('name', 'there')
        company = lead_data.get('company', 'your company')
        title = lead_data.get('title', 'your role')
        
        if email_type == "followup":
            email_content = f"""Subject: Following up on our conversation

Hi {name},

I hope this email finds you well. I wanted to follow up on our previous conversation about how we can help {company} achieve its goals.

Given your role as {title}, I believe our solution could provide significant value to your team. We've helped similar companies reduce costs by 30% while improving efficiency.

Would you be available for a brief 15-minute call next week to discuss this further?

Best regards,
Alex"""
        else:
            email_content = f"""Subject: Helping {company} scale efficiently

Hi {name},

I hope this email finds you well. I came across {company} and was impressed by your recent growth and innovation in the industry.

As {title}, I imagine you're always looking for ways to optimize operations and drive results. We specialize in helping companies like {company} achieve their goals more efficiently.

Our solution has helped similar organizations:
- Reduce operational costs by 25-40%
- Improve team productivity by 60%
- Streamline workflows and processes

Would you be open to a brief 15-minute conversation to explore how we might be able to help {company}?

Best regards,
Alex"""
        
        return email_content


class MockFirestoreClient:
    """Mock implementation of Firestore client"""
    
    def __init__(self):
        self.collections = {}
        self.server_timestamp = datetime.utcnow()
        
    def collection(self, collection_name: str):
        """Mock collection access"""
        return MockCollection(collection_name, self)
    
    def batch(self):
        """Mock batch operations"""
        return MockBatch()


class MockCollection:
    """Mock Firestore collection"""
    
    def __init__(self, name: str, client: MockFirestoreClient):
        self.name = name
        self.client = client
        self.documents = {}
        
    def document(self, doc_id: str = None):
        """Mock document access"""
        if doc_id is None:
            doc_id = f"mock_doc_{len(self.documents) + 1}"
        return MockDocument(doc_id, self)
    
    def where(self, field: str, operator: str, value: Any):
        """Mock where query"""
        return MockQuery(self, field, operator, value)
    
    def stream(self):
        """Mock streaming documents"""
        for doc_id, data in self.documents.items():
            yield MockDocumentSnapshot(doc_id, data)


class MockDocument:
    """Mock Firestore document"""
    
    def __init__(self, doc_id: str, collection: MockCollection):
        self.id = doc_id
        self.collection = collection
        
    def get(self):
        """Mock getting document"""
        data = self.collection.documents.get(self.id, None)
        return MockDocumentSnapshot(self.id, data)
    
    def set(self, data: Dict[str, Any]):
        """Mock setting document"""
        self.collection.documents[self.id] = data
        
    def update(self, updates: Dict[str, Any]):
        """Mock updating document"""
        if self.id in self.collection.documents:
            self.collection.documents[self.id].update(updates)
        else:
            self.collection.documents[self.id] = updates


class MockDocumentSnapshot:
    """Mock Firestore document snapshot"""
    
    def __init__(self, doc_id: str, data: Optional[Dict[str, Any]]):
        self.id = doc_id
        self._data = data
        
    @property
    def exists(self) -> bool:
        return self._data is not None
    
    def to_dict(self) -> Dict[str, Any]:
        return self._data or {}


class MockQuery:
    """Mock Firestore query"""
    
    def __init__(self, collection: MockCollection, field: str, operator: str, value: Any):
        self.collection = collection
        self.field = field
        self.operator = operator
        self.value = value
        
    def stream(self):
        """Mock query streaming"""
        for doc_id, data in self.collection.documents.items():
            if self._matches_query(data):
                yield MockDocumentSnapshot(doc_id, data)
    
    def _matches_query(self, data: Dict[str, Any]) -> bool:
        """Check if document matches query"""
        field_value = data.get(self.field)
        
        if self.operator == '==':
            return field_value == self.value
        elif self.operator == 'in':
            return field_value in self.value
        # Add more operators as needed
        
        return False


class MockBatch:
    """Mock Firestore batch"""
    
    def __init__(self):
        self.operations = []
        
    def set(self, doc_ref: MockDocument, data: Dict[str, Any]):
        """Mock batch set"""
        self.operations.append(('set', doc_ref, data))
        
    def update(self, doc_ref: MockDocument, updates: Dict[str, Any]):
        """Mock batch update"""
        self.operations.append(('update', doc_ref, updates))
        
    def commit(self):
        """Mock batch commit"""
        for operation, doc_ref, data in self.operations:
            if operation == 'set':
                doc_ref.set(data)
            elif operation == 'update':
                doc_ref.update(data)


class MockFirebaseApp:
    """Mock Firebase app"""
    
    def __init__(self):
        self.name = 'mock-app'


class MockLeadProcessor:
    """Mock lead processor"""
    
    def process_apollo_results(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Mock processing Apollo results"""
        people = results.get('people', [])
        processed = []
        
        for person in people:
            processed_lead = {
                'name': f"{person.get('first_name', '')} {person.get('last_name', '')}".strip(),
                'email': person.get('email'),
                'title': person.get('title'),
                'company': person.get('organization', {}).get('name'),
                'phone': person.get('phone'),
                'linkedin': person.get('linkedin_url'),
                'apollo_id': person.get('id'),
                'company_size': person.get('organization', {}).get('employees'),
                'industry': person.get('organization', {}).get('industry')
            }
            processed.append(processed_lead)
            
        return processed
    
    def check_duplicate_leads(self, new_leads: List[Dict[str, Any]], 
                            existing_leads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Mock duplicate checking"""
        existing_emails = {lead.get('email') for lead in existing_leads if lead.get('email')}
        
        unique_leads = []
        for lead in new_leads:
            if lead.get('email') not in existing_emails:
                unique_leads.append(lead)
                
        return unique_leads
    
    def prepare_lead_for_database(self, lead: Dict[str, Any], project_id: str) -> Dict[str, Any]:
        """Mock preparing lead for database"""
        return {
            **lead,
            'projectId': project_id,
            'status': 'new',
            'createdAt': datetime.utcnow(),
            'source': 'apollo'
        }


# Mock API Testing Utilities
def test_apollo_api(api_key: str) -> Dict[str, Any]:
    """Mock Apollo API test"""
    return {
        'status': 'success',
        'api': 'apollo',
        'results_found': 100,
        'response_time': 1.2,
        'message': 'Apollo API working correctly'
    }

def test_perplexity_api(api_key: str) -> Dict[str, Any]:
    """Mock Perplexity API test"""
    return {
        'status': 'success',
        'api': 'perplexity',
        'response_length': 500,
        'response_time': 2.1,
        'message': 'Perplexity API working correctly'
    }

def test_openai_api(api_key: str) -> Dict[str, Any]:
    """Mock OpenAI API test"""
    return {
        'status': 'success',
        'api': 'openai',
        'email_length': 300,
        'response_time': 3.5,
        'message': 'OpenAI API working correctly'
    }

def test_all_apis(api_keys: Dict[str, str]) -> Dict[str, Any]:
    """Mock all APIs test"""
    return {
        'overall_status': 'success',
        'successful_apis': 3,
        'total_apis': 3,
        'fully_successful_apis': 3,
        'apis': {
            'apollo': test_apollo_api(api_keys.get('apollo', '')),
            'perplexity': test_perplexity_api(api_keys.get('perplexity', '')),
            'openai': test_openai_api(api_keys.get('openai', ''))
        }
    }

def validate_api_key_format(api_key: str, api_type: str) -> Dict[str, Any]:
    """Mock API key format validation"""
    valid = False
    
    if api_type == 'openai' and api_key.startswith('sk-'):
        valid = len(api_key) > 10
    elif api_type == 'perplexity' and api_key.startswith('pplx-'):
        valid = len(api_key) > 10
    elif api_type == 'apollo':
        valid = len(api_key) > 10
    
    return {
        'valid': valid,
        'api_type': api_type,
        'format_check': 'passed' if valid else 'failed'
    }

def get_api_health_summary(api_keys: Dict[str, str]) -> Dict[str, Any]:
    """Mock API health summary"""
    return {
        'overall_health': 'healthy',
        'apis': {
            'apollo': {'status': 'healthy', 'last_check': datetime.utcnow()},
            'perplexity': {'status': 'healthy', 'last_check': datetime.utcnow()},
            'openai': {'status': 'healthy', 'last_check': datetime.utcnow()}
        },
        'valid_keys_count': len(api_keys),
        'total_keys_count': 3
    }

def test_workflow_integration(api_keys: Dict[str, str]) -> Dict[str, Any]:
    """Mock workflow integration test"""
    required_keys = ['apollo', 'perplexity', 'openai']
    missing_keys = [key for key in required_keys if key not in api_keys]
    
    if missing_keys:
        return {
            'status': 'error',
            'workflow_stage': 'initialization',
            'message': f'Missing API keys: {", ".join(missing_keys)}'
        }
    
    return {
        'status': 'success',
        'workflow_stage': 'completed',
        'lead_found': True,
        'company': 'Test Company',
        'person': 'John Doe',
        'enrichment_complete': True,
        'email_generated': True
    }


# Mock data fixtures
MOCK_API_KEYS = {
    'apollo': 'mock_apollo_key_123',
    'perplexity': 'mock_perplexity_key_456',
    'openai': 'mock_openai_key_789'
}

MOCK_PROJECT_DATA = {
    'id': 'test_project_123',
    'name': 'Test Project',
    'projectDetails': 'Looking for SaaS companies in the US',
    'areaDescription': 'San Francisco, CA',
    'status': 'active',
    'created_at': datetime.utcnow()
}

MOCK_LEAD_DATA = {
    'id': 'test_lead_123',
    'name': 'John Doe',
    'email': 'john.doe@testcompany.com',
    'title': 'CEO',
    'company': 'Test Company',
    'phone': '+1555000123',
    'projectId': 'test_project_123',
    'status': 'new',
    'enrichmentStatus': 'pending'
}

# Mock API responses
MOCK_APOLLO_RESPONSE = {
    'people': [
        {
            'id': 'apollo_123',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'title': 'CEO',
            'organization': {
                'name': 'Example Corp',
                'website_url': 'https://example.com'
            }
        }
    ],
    'pagination': {
        'page': 1,
        'per_page': 25,
        'total_entries': 100
    }
}

MOCK_PERPLEXITY_RESPONSE = {
    'choices': [
        {
            'message': {
                'content': 'Example Corp is a leading technology company...'
            }
        }
    ]
}

MOCK_OPENAI_RESPONSE = "Subject: Partnership Opportunity\n\nHi John,\n\nI hope this email finds you well..." 