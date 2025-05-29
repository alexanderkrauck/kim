#!/usr/bin/env python3
"""
Test Live Firebase Function

This script tests the deployed Firebase Function to generate execution logs.
"""

import requests
import json
import os
from google.auth.transport.requests import Request
from google.oauth2 import service_account

def get_id_token():
    """Get Firebase ID token for authentication"""
    try:
        # Try to use service account if available
        if os.path.exists('service-account.json'):
            credentials = service_account.Credentials.from_service_account_file(
                'service-account.json',
                scopes=['https://www.googleapis.com/auth/cloud-platform']
            )
            request = Request()
            credentials.refresh(request)
            return credentials.token
        else:
            print("⚠️  No service account found - testing without authentication")
            return None
    except Exception as e:
        print(f"⚠️  Could not get auth token: {e}")
        return None

def test_find_leads_function():
    """Test the deployed find_leads function"""
    
    # Function URL - update if your region is different
    function_url = "https://europe-west1-krauck-systems-kim.cloudfunctions.net/find_leads"
    
    # Test data
    test_data = {
        "data": {
            "project_id": "test-project-debug-123",
            "num_leads": 3,
            "search_params": {
                "organization_locations": ["San Francisco, CA"],
                "person_titles": ["CEO", "Founder"]
            },
            "auto_enrich": False,
            "save_without_enrichment": True
        }
    }
    
    # Get authentication token
    token = get_id_token()
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    if token:
        headers['Authorization'] = f'Bearer {token}'
    
    print("🚀 Testing deployed find_leads function...")
    print(f"📍 URL: {function_url}")
    print(f"📝 Test data: {json.dumps(test_data, indent=2)}")
    
    try:
        # Make the request
        response = requests.post(function_url, json=test_data, headers=headers, timeout=60)
        
        print(f"\n📊 Response Status: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success! Response: {json.dumps(result, indent=2)}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
        return response
        
    except requests.exceptions.Timeout:
        print("⏰ Request timed out - this might indicate the function is working but taking time")
        print("💡 Check the Firebase Console logs for execution details")
        return None
    except Exception as e:
        print(f"❌ Request failed: {str(e)}")
        return None

def monitor_logs_after_test():
    """Instructions for monitoring logs"""
    print("\n" + "="*60)
    print("📊 HOW TO SEE THE EXECUTION LOGS:")
    print("="*60)
    print("1. 🌐 Firebase Console (EASIEST):")
    print("   - Browser tab should be open from earlier")
    print("   - Refresh the page to see new logs")
    print("   - Look for logs with 🚀 🔍 📊 ✅ emojis")
    print("")
    print("2. 📱 Command Line:")
    print("   firebase functions:log --only find_leads -n 20")
    print("")
    print("3. 🔄 Auto-refresh logs:")
    print("   ./quick_debug.sh follow find_leads")
    print("")
    print("4. 🌐 Open logs in browser:")
    print("   firebase functions:log --open")
    print("="*60)

if __name__ == "__main__":
    print("🧪 Firebase Function Live Test")
    print("This will trigger your deployed function and generate execution logs.")
    
    # Test the function
    response = test_find_leads_function()
    
    # Show how to monitor logs
    monitor_logs_after_test()
    
    if response:
        print(f"\n✅ Test completed! Check logs to see the detailed execution flow.")
    else:
        print(f"\n⚠️  Test had issues, but the function might still be working.")
        print("Check the Firebase Console logs for details.") 