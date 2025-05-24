"""
Test APIs Function

This function tests API connectivity and health for Apollo, Perplexity, and OpenAI APIs.
Can be used to validate API keys and troubleshoot issues in production.
"""

import logging
from datetime import datetime
from typing import Dict, Any
from firebase_functions import https_fn, options
from firebase_admin import firestore

# Configure European region
EUROPEAN_REGION = options.SupportedRegion.EUROPE_WEST1

from utils import (
    get_api_keys,
    test_all_apis,
    test_workflow_integration,
    get_api_health_summary,
    validate_api_key_format
)


@https_fn.on_call(region=EUROPEAN_REGION)
def test_apis(req: https_fn.CallableRequest) -> Dict[str, Any]:
    """
    Test API connectivity and health
    
    Args:
        req.data should contain:
        - test_type (str): 'health', 'individual', 'workflow', or 'all' (default: 'health')
        - minimal (bool): Use minimal requests to save credits (default: True)
        - save_results (bool): Save test results to Firestore (default: False)
        
    Returns:
        Dict with test results and API status
    """
    try:
        # Extract parameters
        test_type = req.data.get('test_type', 'health')
        minimal = req.data.get('minimal', True)
        save_results = req.data.get('save_results', False)
        
        logging.info(f"Testing APIs with type: {test_type}, minimal: {minimal}")
        
        # Get API keys
        api_keys = get_api_keys()
        
        # Validate we have the required keys
        required_keys = ['apollo', 'perplexity', 'openai']
        missing_keys = [key for key in required_keys if not api_keys.get(key)]
        
        if missing_keys:
            return {
                'success': False,
                'message': f'Missing API keys: {missing_keys}',
                'test_type': test_type,
                'timestamp': datetime.utcnow().isoformat()
            }
        
        # Perform tests based on type
        if test_type == 'health':
            # Quick health check without API calls
            results = get_api_health_summary(api_keys)
            results['test_type'] = 'health'
            results['timestamp'] = datetime.utcnow().isoformat()
            
        elif test_type == 'individual':
            # Test each API individually
            results = test_all_apis(api_keys, minimal=minimal)
            results['test_type'] = 'individual'
            results['timestamp'] = datetime.utcnow().isoformat()
            
        elif test_type == 'workflow':
            # Test complete workflow integration
            results = test_workflow_integration(api_keys)
            results['test_type'] = 'workflow'
            results['timestamp'] = datetime.utcnow().isoformat()
            
        elif test_type == 'all':
            # Comprehensive testing
            health_results = get_api_health_summary(api_keys)
            individual_results = test_all_apis(api_keys, minimal=minimal)
            workflow_results = test_workflow_integration(api_keys)
            
            results = {
                'test_type': 'all',
                'timestamp': datetime.utcnow().isoformat(),
                'health_check': health_results,
                'individual_tests': individual_results,
                'workflow_test': workflow_results,
                'overall_status': 'success' if (
                    individual_results.get('overall_status') == 'success' and
                    workflow_results.get('status') == 'success'
                ) else 'partial'
            }
            
        else:
            return {
                'success': False,
                'message': f'Invalid test_type: {test_type}. Use: health, individual, workflow, or all',
                'timestamp': datetime.utcnow().isoformat()
            }
        
        # Save results to Firestore if requested
        if save_results:
            try:
                db = firestore.client()
                test_results_ref = db.collection('api_test_results').document()
                test_results_ref.set({
                    **results,
                    'created_at': firestore.SERVER_TIMESTAMP,
                    'test_parameters': {
                        'test_type': test_type,
                        'minimal': minimal
                    }
                })
                results['saved_to_firestore'] = True
                results['document_id'] = test_results_ref.id
            except Exception as e:
                logging.warning(f"Failed to save test results to Firestore: {e}")
                results['saved_to_firestore'] = False
                results['save_error'] = str(e)
        
        # Add success flag
        results['success'] = True
        
        logging.info(f"API tests completed successfully: {test_type}")
        return results
        
    except Exception as e:
        logging.error(f"Error in test_apis: {str(e)}")
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message=f"Failed to test APIs: {str(e)}"
        )


@https_fn.on_call(region=EUROPEAN_REGION)
def validate_api_keys(req: https_fn.CallableRequest) -> Dict[str, Any]:
    """
    Validate API key formats without making API calls
    
    Args:
        req.data should contain:
        - api_keys (dict, optional): Dict with API keys to validate
                                   If not provided, uses configured keys
        
    Returns:
        Dict with validation results for each API key
    """
    try:
        # Get API keys to validate
        if req.data.get('api_keys'):
            api_keys = req.data['api_keys']
        else:
            api_keys = get_api_keys()
        
        validation_results = {}
        
        # Validate each API key format
        for api_type in ['apollo', 'perplexity', 'openai']:
            api_key = api_keys.get(api_type)
            
            if api_key:
                validation = validate_api_key_format(api_key, api_type)
                validation_results[api_type] = {
                    'key_present': True,
                    'format_valid': validation['valid'],
                    'message': validation['message'],
                    'key_preview': f"{api_key[:10]}..." if len(api_key) > 10 else api_key
                }
            else:
                validation_results[api_type] = {
                    'key_present': False,
                    'format_valid': False,
                    'message': f'{api_type.title()} API key not configured',
                    'key_preview': None
                }
        
        # Overall validation status
        valid_keys = sum(1 for result in validation_results.values() 
                        if result['key_present'] and result['format_valid'])
        total_keys = len(validation_results)
        
        return {
            'success': True,
            'timestamp': datetime.utcnow().isoformat(),
            'validation_results': validation_results,
            'summary': {
                'valid_keys': valid_keys,
                'total_keys': total_keys,
                'all_valid': valid_keys == total_keys,
                'status': 'all_valid' if valid_keys == total_keys else 'partial' if valid_keys > 0 else 'none_valid'
            }
        }
        
    except Exception as e:
        logging.error(f"Error in validate_api_keys: {str(e)}")
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message=f"Failed to validate API keys: {str(e)}"
        )


@https_fn.on_call(region=EUROPEAN_REGION)
def get_api_status(req: https_fn.CallableRequest) -> Dict[str, Any]:
    """
    Get current API status and recent test results
    
    Args:
        req.data should contain:
        - include_recent_tests (bool): Include recent test results (default: True)
        - limit (int): Number of recent tests to include (default: 5)
        
    Returns:
        Dict with current API status and recent test history
    """
    try:
        include_recent_tests = req.data.get('include_recent_tests', True)
        limit = req.data.get('limit', 5)
        
        # Get current API health
        api_keys = get_api_keys()
        current_health = get_api_health_summary(api_keys)
        current_health['timestamp'] = datetime.utcnow().isoformat()
        
        result = {
            'success': True,
            'current_health': current_health,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Get recent test results if requested
        if include_recent_tests:
            try:
                db = firestore.client()
                recent_tests_query = (
                    db.collection('api_test_results')
                    .order_by('created_at', direction=firestore.Query.DESCENDING)
                    .limit(limit)
                )
                
                recent_tests = []
                for doc in recent_tests_query.stream():
                    test_data = doc.to_dict()
                    test_data['document_id'] = doc.id
                    recent_tests.append(test_data)
                
                result['recent_tests'] = recent_tests
                result['recent_tests_count'] = len(recent_tests)
                
            except Exception as e:
                logging.warning(f"Failed to get recent test results: {e}")
                result['recent_tests'] = []
                result['recent_tests_error'] = str(e)
        
        return result
        
    except Exception as e:
        logging.error(f"Error in get_api_status: {str(e)}")
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message=f"Failed to get API status: {str(e)}"
        ) 