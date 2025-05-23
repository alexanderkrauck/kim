#!/usr/bin/env python3
"""
Comprehensive Apollo API test to check access and available endpoints
"""

import os
import sys
import requests
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path to import utils
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from utils.api_clients import ApolloClient

# Load environment variables
load_dotenv()

def test_basic_endpoints():
    """Test basic Apollo API endpoints to check access level"""
    
    api_key = os.getenv('APOLLO_API_KEY')
    if not api_key:
        print("❌ No Apollo API key found")
        return False
    
    print(f"🔑 Testing with API key: {api_key[:10]}...")
    
    # Initialize client with updated endpoint
    client = ApolloClient(api_key)
    
    # Test endpoints in order of likely accessibility
    endpoints_to_test = [
        {
            "name": "Users List",
            "method": "GET",
            "url": f"{client.base_url}/users",
            "description": "Basic endpoint to check API access"
        },
        {
            "name": "Email Accounts",
            "method": "GET", 
            "url": f"{client.base_url}/email_accounts",
            "description": "List email accounts"
        },
        {
            "name": "Custom Fields",
            "method": "GET",
            "url": f"{client.base_url}/typed_custom_fields",
            "description": "List custom fields"
        },
        {
            "name": "Contact Search",
            "method": "POST",
            "url": f"{client.base_url}/contacts/search",
            "description": "Search existing contacts (not people database)",
            "payload": {"page": 1, "per_page": 1}
        },
        {
            "name": "People Search",
            "method": "POST",
            "url": f"{client.base_url}/mixed_people/search",
            "description": "Search people database (requires paid plan)",
            "payload": {"page": 1, "per_page": 1, "person_titles": ["CEO"]}
        }
    ]
    
    working_endpoints = []
    
    for endpoint in endpoints_to_test:
        print(f"\n🧪 Testing: {endpoint['name']}")
        print(f"   URL: {endpoint['url']}")
        print(f"   Description: {endpoint['description']}")
        
        try:
            if endpoint['method'] == 'GET':
                response = requests.get(endpoint['url'], headers=client.headers)
            else:
                payload = endpoint.get('payload', {})
                response = requests.post(endpoint['url'], json=payload, headers=client.headers)
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ SUCCESS!")
                data = response.json()
                if isinstance(data, dict):
                    print(f"   Response keys: {list(data.keys())}")
                working_endpoints.append(endpoint['name'])
            elif response.status_code == 401:
                print(f"   ❌ Unauthorized - API key invalid")
            elif response.status_code == 403:
                print(f"   ❌ Forbidden - Endpoint not accessible with current plan")
                try:
                    error_data = response.json()
                    if 'error' in error_data:
                        print(f"   Error: {error_data['error']}")
                except:
                    pass
            else:
                print(f"   ❌ Failed: {response.status_code}")
                print(f"   Response: {response.text[:100]}...")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
    
    return working_endpoints

def test_people_enrichment():
    """Test people enrichment endpoint as alternative"""
    
    api_key = os.getenv('APOLLO_API_KEY')
    client = ApolloClient(api_key)
    
    print(f"\n🔍 Testing People Enrichment endpoint...")
    
    # Test with a well-known person
    url = f"{client.base_url}/people/match"
    payload = {
        "first_name": "Elon",
        "last_name": "Musk",
        "organization_name": "Tesla"
    }
    
    try:
        response = requests.post(url, json=payload, headers=client.headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ People Enrichment works!")
            print(f"Response keys: {list(data.keys())}")
            return True
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def main():
    """Run comprehensive Apollo API tests"""
    
    print("🧪 Comprehensive Apollo API Test\n")
    print("This will test various endpoints to determine what's accessible with your API key.\n")
    
    # Test basic endpoints
    working_endpoints = test_basic_endpoints()
    
    # Test enrichment as alternative
    enrichment_works = test_people_enrichment()
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    if working_endpoints:
        print(f"✅ Working endpoints ({len(working_endpoints)}):")
        for endpoint in working_endpoints:
            print(f"   - {endpoint}")
    else:
        print("❌ No endpoints are working")
    
    if enrichment_works:
        print("✅ People Enrichment endpoint works")
    
    print("\n💡 RECOMMENDATIONS:")
    
    if "People Search" in working_endpoints:
        print("✅ You have access to People Search - the notebook should work!")
    elif enrichment_works:
        print("⚠️  You have enrichment access but not search access.")
        print("   Consider upgrading your Apollo plan for search functionality.")
    elif working_endpoints:
        print("⚠️  You have basic API access but not search/enrichment.")
        print("   You may need to upgrade your Apollo plan.")
    else:
        print("❌ No API access detected. Check:")
        print("   1. API key validity")
        print("   2. Apollo account status")
        print("   3. Plan limitations")
    
    print(f"\n📚 For more info, visit: https://docs.apollo.io/docs/api-pricing")

if __name__ == "__main__":
    main() 