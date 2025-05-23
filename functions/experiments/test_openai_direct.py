#!/usr/bin/env python3
"""
Direct OpenAI API Test - Compare direct API calls with our client implementation
"""

import os
import sys
import requests
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path to import utils
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from utils.api_clients import OpenAIClient
from utils.api_testing import test_openai_api

# Load environment variables
load_dotenv()

def test_direct_openai_api():
    """Test OpenAI API directly like the user did"""
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        print("❌ No OpenAI API key found in environment")
        return False
    
    print("🔍 Testing OpenAI API directly (like user's test)...")
    
    # Test 1: Direct API call to /v1/models (what user tested)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get("https://api.openai.com/v1/models", headers=headers)
        response.raise_for_status()
        models_data = response.json()
        
        print(f"✅ Direct /v1/models call successful")
        print(f"   Found {len(models_data.get('data', []))} models")
        
        # Check if GPT-4 is available
        gpt4_available = any(model['id'].startswith('gpt-4') for model in models_data.get('data', []))
        print(f"   GPT-4 models available: {gpt4_available}")
        
    except Exception as e:
        print(f"❌ Direct /v1/models call failed: {e}")
        return False
    
    # Test 2: Direct chat completion call (what our client does)
    print(f"\n🔍 Testing direct chat completion call...")
    
    payload = {
        "model": "gpt-4",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say hello in exactly 5 words."}
        ],
        "max_tokens": 50,
        "temperature": 0.7
    }
    
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            json=payload,
            headers=headers
        )
        response.raise_for_status()
        completion_data = response.json()
        
        content = completion_data['choices'][0]['message']['content']
        print(f"✅ Direct chat completion successful")
        print(f"   Response: {content}")
        
    except Exception as e:
        print(f"❌ Direct chat completion failed: {e}")
        print(f"   This might indicate insufficient permissions or credits")
        return False
    
    return True

def test_our_openai_client():
    """Test our OpenAI client implementation"""
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        print("❌ No OpenAI API key found in environment")
        return False
    
    print(f"\n🔍 Testing our OpenAI client implementation...")
    
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
            print(f"✅ Our OpenAI client successful")
            print(f"   Generated email length: {len(result)} characters")
            print(f"   First 100 chars: {result[:100]}...")
            return True
        else:
            print(f"❌ Our OpenAI client returned empty result")
            return False
            
    except Exception as e:
        print(f"❌ Our OpenAI client failed: {e}")
        return False

def test_our_testing_utility():
    """Test our API testing utility"""
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        print("❌ No OpenAI API key found in environment")
        return False
    
    print(f"\n🔍 Testing our API testing utility...")
    
    try:
        result = test_openai_api(api_key, minimal=True)
        
        print(f"   Status: {result['status']}")
        print(f"   Message: {result['message']}")
        
        if result['status'] == 'success':
            print(f"   Email length: {result.get('email_length', 'N/A')}")
            print(f"   Word count: {result.get('word_count', 'N/A')}")
            print(f"✅ Our API testing utility working correctly")
            return True
        elif result['status'] == 'partial':
            print(f"   Models available: {result.get('models_available', 'N/A')}")
            print(f"   GPT-4 available: {result.get('gpt4_available', 'N/A')}")
            print(f"   Permission error: {result.get('permission_error', 'N/A')}")
            print(f"   Fix suggestion: {result.get('fix_suggestion', 'N/A')}")
            print(f"✅ Our API testing utility correctly detected permission issue")
            return True
        else:
            print(f"❌ Our API testing utility reported error")
            if 'error_type' in result:
                print(f"   Error type: {result['error_type']}")
            return False
            
    except Exception as e:
        print(f"❌ Our API testing utility failed: {e}")
        return False

def main():
    """Run all OpenAI tests and compare results"""
    print("🧪 OpenAI API Testing Verification\n")
    
    # Test 1: Direct API call (what user verified works)
    direct_success = test_direct_openai_api()
    
    # Test 2: Our client implementation
    client_success = test_our_openai_client()
    
    # Test 3: Our testing utility
    testing_success = test_our_testing_utility()
    
    print(f"\n📊 Test Results Summary:")
    print(f"   Direct API call: {'✅ Success' if direct_success else '❌ Failed'}")
    print(f"   Our OpenAI client: {'✅ Success' if client_success else '❌ Failed'}")
    print(f"   Our testing utility: {'✅ Success' if testing_success else '❌ Failed'}")
    
    if direct_success and not (client_success and testing_success):
        print(f"\n⚠️  Issue detected:")
        print(f"   Direct API works but our implementation has issues")
        print(f"   This suggests a problem with our client or testing code")
    elif direct_success and client_success and testing_success:
        print(f"\n🎉 All tests passed!")
        print(f"   OpenAI API is working correctly with our implementation")
    elif not direct_success:
        print(f"\n⚠️  OpenAI API access issue:")
        print(f"   Even direct API calls are failing")
        print(f"   Check API key permissions, credits, or rate limits")

if __name__ == "__main__":
    main() 