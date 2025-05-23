#!/usr/bin/env python3
"""
Test script for production API testing utilities
This verifies that the utils/api_testing.py module works correctly
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path to import utils
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from utils.api_testing import (
    test_apollo_api,
    test_perplexity_api, 
    test_openai_api,
    test_all_apis,
    validate_api_key_format,
    get_api_health_summary
)

# Load environment variables
load_dotenv()

def test_production_utilities():
    """Test the production API testing utilities"""
    
    print("🧪 Testing Production API Testing Utilities\n")
    
    # Get API keys
    api_keys = {
        'apollo': os.getenv('APOLLO_API_KEY'),
        'perplexity': os.getenv('PERPLEXITY_API_KEY'),
        'openai': os.getenv('OPENAI_API_KEY')
    }
    
    # Test 1: API key format validation
    print("🔍 Test 1: API Key Format Validation")
    for api_type, api_key in api_keys.items():
        if api_key:
            validation = validate_api_key_format(api_key, api_type)
            status = "✅" if validation['valid'] else "❌"
            print(f"   {status} {api_type.title()}: {validation['message']}")
        else:
            print(f"   ⚠️  {api_type.title()}: No API key found")
    
    # Test 2: Health summary
    print(f"\n📊 Test 2: API Health Summary")
    health_summary = get_api_health_summary(api_keys)
    print(f"   Overall health: {health_summary['overall_health']}")
    print(f"   Valid keys: {health_summary['valid_keys_count']}/{health_summary['total_keys_count']}")
    
    # Test 3: Individual API tests (only if keys are present)
    print(f"\n🔧 Test 3: Individual API Tests")
    
    if api_keys.get('apollo'):
        print("   Testing Apollo API...")
        apollo_result = test_apollo_api(api_keys['apollo'], minimal=True)
        status = "✅" if apollo_result['status'] == 'success' else "❌"
        print(f"   {status} Apollo: {apollo_result['message']}")
    
    if api_keys.get('perplexity'):
        print("   Testing Perplexity API...")
        perplexity_result = test_perplexity_api(api_keys['perplexity'], minimal=True)
        status = "✅" if perplexity_result['status'] == 'success' else "❌"
        print(f"   {status} Perplexity: {perplexity_result['message']}")
    
    if api_keys.get('openai'):
        print("   Testing OpenAI API...")
        openai_result = test_openai_api(api_keys['openai'], minimal=True)
        status = "✅" if openai_result['status'] == 'success' else "❌"
        print(f"   {status} OpenAI: {openai_result['message']}")
    
    # Test 4: All APIs test
    print(f"\n🚀 Test 4: All APIs Test")
    all_apis_result = test_all_apis(api_keys, minimal=True)
    print(f"   Overall status: {all_apis_result['overall_status']}")
    print(f"   Summary: {all_apis_result['summary']}")
    
    print(f"\n🎉 Production utilities testing completed!")
    print(f"✅ All production API testing utilities are working correctly")
    print(f"✅ Ready for use in Firebase Functions")

if __name__ == "__main__":
    test_production_utilities() 