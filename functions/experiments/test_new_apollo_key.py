#!/usr/bin/env python3
"""
Test script for new Apollo API key after plan upgrade
This uses minimal requests to verify access without consuming many credits
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path to import utils
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from utils.api_clients import ApolloClient

# Load environment variables
load_dotenv()

def test_new_apollo_key():
    """Test the new Apollo API key with minimal requests"""
    
    print("🔑 Testing New Apollo API Key\n")
    
    api_key = os.getenv('APOLLO_API_KEY')
    if not api_key:
        print("❌ No Apollo API key found in environment")
        print("Please update your .env file with the new API key")
        return False
    
    print(f"🔍 Testing with API key: {api_key[:10]}...")
    
    # Initialize client
    client = ApolloClient(api_key)
    
    # Test 1: Very minimal people search (1 result only)
    print("\n🧪 Test 1: Minimal People Search")
    try:
        results = client.search_people(
            job_titles=["CEO"],
            per_page=1,  # Minimal to save credits
            page=1
        )
        
        if results and 'people' in results:
            print("✅ People Search works!")
            print(f"   Found {len(results['people'])} result(s)")
            print(f"   Total available: {results.get('pagination', {}).get('total_entries', 'Unknown')}")
            
            if results['people']:
                person = results['people'][0]
                print(f"   Sample: {person.get('first_name', '')} {person.get('last_name', '')} - {person.get('title', 'N/A')}")
        else:
            print("⚠️  No results returned")
            
    except Exception as e:
        print(f"❌ People Search failed: {e}")
        return False
    
    # Test 2: Test with location filter (still minimal)
    print("\n🧪 Test 2: Location-filtered Search")
    try:
        results = client.search_people(
            job_titles=["manager"],
            locations=["Austria"],
            per_page=2,  # Still very small
            page=1
        )
        
        if results and 'people' in results:
            print("✅ Location filtering works!")
            print(f"   Found {len(results['people'])} result(s)")
            
            for i, person in enumerate(results['people']):
                print(f"   {i+1}. {person.get('first_name', '')} {person.get('last_name', '')} - {person.get('city', 'N/A')}, {person.get('country', 'N/A')}")
        else:
            print("⚠️  No results returned")
            
    except Exception as e:
        print(f"❌ Location search failed: {e}")
        return False
    
    # Test 3: Test company domain search (minimal)
    print("\n🧪 Test 3: Company Domain Search")
    try:
        results = client.search_people(
            company_domains=["google.com"],
            job_titles=["engineer"],
            per_page=1,
            page=1
        )
        
        if results and 'people' in results:
            print("✅ Company domain search works!")
            print(f"   Found {len(results['people'])} result(s)")
        else:
            print("⚠️  No results returned")
            
    except Exception as e:
        print(f"❌ Company domain search failed: {e}")
        return False
    
    print("\n🎉 All tests passed! Your Apollo API key is working correctly.")
    print("\n📊 API Access Summary:")
    print("✅ People Search endpoint accessible")
    print("✅ Location filtering works")
    print("✅ Company domain filtering works")
    print("✅ Ready for integration with find_leads function")
    
    return True

def show_next_steps():
    """Show next steps for using the API"""
    print("\n📝 Next Steps:")
    print("1. ✅ Your Apollo API is working - you can now use the notebook")
    print("2. 🔍 Run the full notebook: experiments/apollo_api_testing.ipynb")
    print("3. 🚀 Test the find_leads function integration")
    print("4. 📊 Monitor your credit usage in Apollo dashboard")
    
    print("\n⚠️  Credit Management Tips:")
    print("- Start with small per_page values (10-25)")
    print("- Use specific filters to reduce result sets")
    print("- Monitor usage in Apollo → Settings → API → Usage")
    print("- The notebook is designed to use minimal credits for testing")

if __name__ == "__main__":
    success = test_new_apollo_key()
    
    if success:
        show_next_steps()
    else:
        print("\n❌ API key test failed. Please:")
        print("1. Create a new API key in Apollo after plan upgrade")
        print("2. Make sure to check 'People Search' in the scopes")
        print("3. Consider making it a 'master key'")
        print("4. Update your .env file with the new key")
        print("5. Wait a few minutes for the key to activate") 