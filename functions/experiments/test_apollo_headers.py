#!/usr/bin/env python3
"""
Test different Apollo API header formats to determine the correct one
"""

import os
import sys
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_apollo_headers():
    """Test different header formats for Apollo API"""
    
    api_key = os.getenv('APOLLO_API_KEY')
    if not api_key:
        print("❌ No Apollo API key found")
        return
    
    base_url = "https://api.apollo.io/v1"
    endpoint = f"{base_url}/mixed_people/search"
    
    # Test payload - very minimal to avoid using credits
    payload = {
        "page": 1,
        "per_page": 1,
        "person_titles": ["CEO"]
    }
    
    # Test different header formats
    header_formats = [
        {
            "name": "X-Api-Key format (current)",
            "headers": {
                "Cache-Control": "no-cache",
                "Content-Type": "application/json",
                "X-Api-Key": api_key
            }
        },
        {
            "name": "Authorization Bearer format (from original notebook)",
            "headers": {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
        },
        {
            "name": "Simple X-Api-Key only",
            "headers": {
                "X-Api-Key": api_key,
                "Content-Type": "application/json"
            }
        }
    ]
    
    for test_case in header_formats:
        print(f"\n🧪 Testing: {test_case['name']}")
        print(f"Headers: {test_case['headers']}")
        
        try:
            response = requests.post(endpoint, json=payload, headers=test_case['headers'])
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ SUCCESS! Found {len(data.get('people', []))} results")
                print(f"Response keys: {list(data.keys())}")
                return test_case['headers']  # Return working headers
            else:
                print(f"❌ Failed: {response.status_code}")
                print(f"Response: {response.text[:200]}...")
                
        except Exception as e:
            print(f"❌ Exception: {e}")
    
    print("\n❌ None of the header formats worked")
    return None

if __name__ == "__main__":
    print("🔍 Testing Apollo API Header Formats\n")
    working_headers = test_apollo_headers()
    
    if working_headers:
        print(f"\n✅ Working headers found:")
        for key, value in working_headers.items():
            if key == "X-Api-Key" or key == "Authorization":
                print(f"  {key}: {value[:20]}...")
            else:
                print(f"  {key}: {value}")
    else:
        print("\n❌ No working header format found. Check:")
        print("1. API key validity")
        print("2. Apollo API documentation for current header format")
        print("3. Account status and permissions") 