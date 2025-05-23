"""
API Testing Utilities for Production Use

This module provides functions to test API connectivity and validate API keys
in a production environment. Can be used by Firebase Functions to check
API health and troubleshoot issues.
"""

import logging
import requests
from typing import Dict, Any, Optional
from .api_clients import ApolloClient, PerplexityClient, OpenAIClient


def test_apollo_api(api_key: str, minimal: bool = True) -> Dict[str, Any]:
    """
    Test Apollo API connectivity and functionality
    
    Args:
        api_key: Apollo API key to test
        minimal: If True, use minimal requests to save credits
        
    Returns:
        Dict with test results and status
    """
    try:
        client = ApolloClient(api_key)
        
        # Minimal test - just 1 result
        per_page = 1 if minimal else 5
        
        result = client.search_people(
            job_titles=["CEO"],
            per_page=per_page,
            page=1
        )
        
        if result and 'people' in result:
            return {
                'status': 'success',
                'api': 'apollo',
                'message': 'Apollo API is working correctly',
                'results_found': len(result['people']),
                'total_available': result.get('pagination', {}).get('total_entries', 0),
                'credits_used': per_page
            }
        else:
            return {
                'status': 'error',
                'api': 'apollo',
                'message': 'Apollo API returned unexpected response format',
                'error_details': 'No people array in response'
            }
            
    except Exception as e:
        logging.error(f"Apollo API test failed: {e}")
        return {
            'status': 'error',
            'api': 'apollo',
            'message': f'Apollo API test failed: {str(e)}',
            'error_type': type(e).__name__
        }


def test_perplexity_api(api_key: str, minimal: bool = True) -> Dict[str, Any]:
    """
    Test Perplexity API connectivity and functionality
    
    Args:
        api_key: Perplexity API key to test
        minimal: If True, use minimal requests to save credits
        
    Returns:
        Dict with test results and status
    """
    try:
        client = PerplexityClient(api_key)
        
        # Use a simple, well-known company for testing
        company_name = "Microsoft" if minimal else "Tesla"
        context = "Brief company overview for API testing"
        
        result = client.enrich_lead_data(
            company_name=company_name,
            additional_context=context
        )
        
        if result and 'choices' in result:
            content = result['choices'][0]['message']['content']
            return {
                'status': 'success',
                'api': 'perplexity',
                'message': 'Perplexity API is working correctly',
                'response_length': len(content),
                'company_tested': company_name,
                'credits_used': 1
            }
        else:
            return {
                'status': 'error',
                'api': 'perplexity',
                'message': 'Perplexity API returned unexpected response format',
                'error_details': 'No choices array in response'
            }
            
    except Exception as e:
        logging.error(f"Perplexity API test failed: {e}")
        return {
            'status': 'error',
            'api': 'perplexity',
            'message': f'Perplexity API test failed: {str(e)}',
            'error_type': type(e).__name__
        }


def test_openai_api(api_key: str, minimal: bool = True) -> Dict[str, Any]:
    """
    Test OpenAI API connectivity and functionality
    
    Args:
        api_key: OpenAI API key to test
        minimal: If True, use minimal requests to save tokens
        
    Returns:
        Dict with test results and status
    """
    # First test: Check basic API access with /v1/models (requires minimal permissions)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        # Test basic API access first
        response = requests.get("https://api.openai.com/v1/models", headers=headers)
        response.raise_for_status()
        models_data = response.json()
        
        # Check if GPT models are available
        available_models = [model['id'] for model in models_data.get('data', [])]
        gpt4_available = any(model.startswith('gpt-4') for model in available_models)
        gpt35_available = any(model.startswith('gpt-3.5') for model in available_models)
        
        # Now try chat completion (requires model.request scope)
        try:
            client = OpenAIClient(api_key)
            
            # Simple test data
            test_lead_data = {
                "name": "Test User",
                "company": "Test Company",
                "title": "Manager"
            }
            
            result = client.generate_email_content(
                lead_data=test_lead_data,
                email_type="outreach"
            )
            
            if result:
                return {
                    'status': 'success',
                    'api': 'openai',
                    'message': 'OpenAI API is working correctly',
                    'email_length': len(result),
                    'word_count': len(result.split()),
                    'tokens_used_approx': len(result.split()) * 1.3,
                    'models_available': len(available_models),
                    'gpt4_available': gpt4_available,
                    'gpt35_available': gpt35_available
                }
            else:
                return {
                    'status': 'error',
                    'api': 'openai',
                    'message': 'OpenAI API returned empty response',
                    'error_details': 'No email content generated',
                    'models_available': len(available_models),
                    'basic_access': True
                }
                
        except Exception as chat_error:
            # Chat completion failed, but basic API access works
            error_message = str(chat_error)
            
            if "insufficient permissions" in error_message.lower() or "missing scopes" in error_message.lower():
                return {
                    'status': 'partial',
                    'api': 'openai',
                    'message': 'OpenAI API key has limited permissions - can read models but cannot generate content',
                    'error_details': 'Missing model.request scope for chat completions',
                    'basic_access': True,
                    'models_available': len(available_models),
                    'gpt4_available': gpt4_available,
                    'gpt35_available': gpt35_available,
                    'permission_error': True,
                    'fix_suggestion': 'Create a new API key with full permissions or upgrade key scopes'
                }
            else:
                return {
                    'status': 'error',
                    'api': 'openai',
                    'message': f'OpenAI chat completion failed: {error_message}',
                    'error_type': type(chat_error).__name__,
                    'basic_access': True,
                    'models_available': len(available_models)
                }
            
    except Exception as e:
        logging.error(f"OpenAI API test failed: {e}")
        
        # Check if it's an authentication error
        if "401" in str(e) or "unauthorized" in str(e).lower():
            return {
                'status': 'error',
                'api': 'openai',
                'message': 'OpenAI API authentication failed - invalid API key',
                'error_type': 'AuthenticationError',
                'fix_suggestion': 'Check API key validity and format'
            }
        else:
            return {
                'status': 'error',
                'api': 'openai',
                'message': f'OpenAI API test failed: {str(e)}',
                'error_type': type(e).__name__
            }


def test_all_apis(api_keys: Dict[str, str], minimal: bool = True) -> Dict[str, Any]:
    """
    Test all APIs and return comprehensive status
    
    Args:
        api_keys: Dict with keys 'apollo', 'perplexity', 'openai'
        minimal: If True, use minimal requests to save credits
        
    Returns:
        Dict with overall status and individual API results
    """
    results = {}
    overall_status = 'success'
    
    # Test Apollo
    if api_keys.get('apollo'):
        results['apollo'] = test_apollo_api(api_keys['apollo'], minimal)
        if results['apollo']['status'] != 'success':
            overall_status = 'partial'
    else:
        results['apollo'] = {
            'status': 'error',
            'api': 'apollo',
            'message': 'Apollo API key not provided'
        }
        overall_status = 'partial'
    
    # Test Perplexity
    if api_keys.get('perplexity'):
        results['perplexity'] = test_perplexity_api(api_keys['perplexity'], minimal)
        if results['perplexity']['status'] != 'success':
            overall_status = 'partial'
    else:
        results['perplexity'] = {
            'status': 'error',
            'api': 'perplexity',
            'message': 'Perplexity API key not provided'
        }
        overall_status = 'partial'
    
    # Test OpenAI
    if api_keys.get('openai'):
        results['openai'] = test_openai_api(api_keys['openai'], minimal)
        if results['openai']['status'] not in ['success', 'partial']:
            overall_status = 'partial'
    else:
        results['openai'] = {
            'status': 'error',
            'api': 'openai',
            'message': 'OpenAI API key not provided'
        }
        overall_status = 'partial'
    
    # Count successful APIs (including partial success)
    successful_apis = sum(1 for result in results.values() if result['status'] in ['success', 'partial'])
    fully_successful_apis = sum(1 for result in results.values() if result['status'] == 'success')
    total_apis = len(results)
    
    if successful_apis == 0:
        overall_status = 'error'
    elif fully_successful_apis < total_apis:
        overall_status = 'partial'
    
    return {
        'overall_status': overall_status,
        'successful_apis': successful_apis,
        'fully_successful_apis': fully_successful_apis,
        'total_apis': total_apis,
        'apis': results,
        'summary': f"{fully_successful_apis}/{total_apis} APIs fully working, {successful_apis}/{total_apis} APIs accessible"
    }


def test_workflow_integration(api_keys: Dict[str, str]) -> Dict[str, Any]:
    """
    Test the complete workflow integration (Apollo -> Perplexity -> OpenAI)
    
    Args:
        api_keys: Dict with keys 'apollo', 'perplexity', 'openai'
        
    Returns:
        Dict with workflow test results
    """
    try:
        # Check if all APIs are available
        missing_keys = []
        for api_name in ['apollo', 'perplexity', 'openai']:
            if not api_keys.get(api_name):
                missing_keys.append(api_name)
        
        if missing_keys:
            return {
                'status': 'error',
                'message': f'Missing API keys: {missing_keys}',
                'workflow_stage': 'initialization'
            }
        
        # Initialize clients
        apollo_client = ApolloClient(api_keys['apollo'])
        perplexity_client = PerplexityClient(api_keys['perplexity'])
        openai_client = OpenAIClient(api_keys['openai'])
        
        # Step 1: Apollo search
        apollo_result = apollo_client.search_people(
            job_titles=["CEO"],
            per_page=1
        )
        
        if not apollo_result or not apollo_result.get('people'):
            return {
                'status': 'error',
                'message': 'Apollo search returned no results',
                'workflow_stage': 'apollo_search'
            }
        
        lead = apollo_result['people'][0]
        company_name = lead.get('organization', {}).get('name', 'Test Company')
        person_name = f"{lead.get('first_name', 'Test')} {lead.get('last_name', 'User')}"
        
        # Step 2: Perplexity enrichment
        perplexity_result = perplexity_client.enrich_lead_data(
            company_name=company_name,
            person_name=person_name,
            additional_context="Brief research for workflow testing"
        )
        
        if not perplexity_result or not perplexity_result.get('choices'):
            return {
                'status': 'error',
                'message': 'Perplexity enrichment failed',
                'workflow_stage': 'perplexity_enrichment'
            }
        
        enrichment_data = perplexity_result['choices'][0]['message']['content']
        
        # Step 3: OpenAI email generation
        lead_data = {
            'name': person_name,
            'company': company_name,
            'title': lead.get('title', 'Executive'),
            'enrichment_data': enrichment_data
        }
        
        email_result = openai_client.generate_email_content(
            lead_data=lead_data,
            email_type="outreach"
        )
        
        if not email_result:
            return {
                'status': 'error',
                'message': 'OpenAI email generation failed',
                'workflow_stage': 'openai_generation'
            }
        
        return {
            'status': 'success',
            'message': 'Complete workflow test successful',
            'workflow_stage': 'completed',
            'lead_found': person_name,
            'company': company_name,
            'enrichment_length': len(enrichment_data),
            'email_length': len(email_result),
            'credits_used': {
                'apollo': 1,
                'perplexity': 1,
                'openai_tokens_approx': len(email_result.split()) * 1.3
            }
        }
        
    except Exception as e:
        logging.error(f"Workflow integration test failed: {e}")
        return {
            'status': 'error',
            'message': f'Workflow test failed: {str(e)}',
            'error_type': type(e).__name__,
            'workflow_stage': 'unknown'
        }


def validate_api_key_format(api_key: str, api_type: str) -> Dict[str, Any]:
    """
    Validate API key format without making API calls
    
    Args:
        api_key: The API key to validate
        api_type: Type of API ('apollo', 'perplexity', 'openai')
        
    Returns:
        Dict with validation results
    """
    if not api_key:
        return {
            'valid': False,
            'message': 'API key is empty or None'
        }
    
    if api_type == 'openai':
        if not api_key.startswith('sk-'):
            return {
                'valid': False,
                'message': 'OpenAI API key should start with "sk-"'
            }
        if len(api_key) < 20:
            return {
                'valid': False,
                'message': 'OpenAI API key appears too short'
            }
    
    elif api_type == 'perplexity':
        if not api_key.startswith('pplx-'):
            return {
                'valid': False,
                'message': 'Perplexity API key should start with "pplx-"'
            }
    
    elif api_type == 'apollo':
        if len(api_key) < 10:
            return {
                'valid': False,
                'message': 'Apollo API key appears too short'
            }
    
    return {
        'valid': True,
        'message': f'{api_type.title()} API key format appears valid'
    }


def get_api_health_summary(api_keys: Dict[str, str]) -> Dict[str, Any]:
    """
    Get a quick health summary of all APIs without extensive testing
    
    Args:
        api_keys: Dict with API keys
        
    Returns:
        Dict with health summary
    """
    health_summary = {
        'timestamp': None,  # Would be set by calling function
        'overall_health': 'unknown',
        'apis': {}
    }
    
    # Validate key formats
    for api_type in ['apollo', 'perplexity', 'openai']:
        api_key = api_keys.get(api_type)
        
        if api_key:
            validation = validate_api_key_format(api_key, api_type)
            health_summary['apis'][api_type] = {
                'key_present': True,
                'key_format_valid': validation['valid'],
                'message': validation['message']
            }
        else:
            health_summary['apis'][api_type] = {
                'key_present': False,
                'key_format_valid': False,
                'message': f'{api_type.title()} API key not configured'
            }
    
    # Determine overall health
    valid_keys = sum(1 for api_info in health_summary['apis'].values() 
                    if api_info['key_present'] and api_info['key_format_valid'])
    
    if valid_keys == 3:
        health_summary['overall_health'] = 'good'
    elif valid_keys > 0:
        health_summary['overall_health'] = 'partial'
    else:
        health_summary['overall_health'] = 'poor'
    
    health_summary['valid_keys_count'] = valid_keys
    health_summary['total_keys_count'] = 3
    
    return health_summary 