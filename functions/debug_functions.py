#!/usr/bin/env python3
"""
Local Debug Script for Firebase Functions

This script allows you to test Firebase Functions locally without deployment.
Run with: python debug_functions.py
"""

import os
import sys
import json
import logging
from typing import Dict, Any, Optional

# Add the functions directory to path
sys.path.append(os.path.dirname(__file__))

# Set up logging for debug mode
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Mock Firebase environment for local testing
os.environ.setdefault('GOOGLE_APPLICATION_CREDENTIALS', './service-account.json')

def mock_firestore_client():
    """Mock Firestore client for local testing"""
    print("⚠️  Using mock Firestore client - no actual database operations")
    return None

def test_find_leads():
    """Test find_leads function locally"""
    print("\n🧪 Testing find_leads function...")
    
    try:
        from find_leads import find_leads_logic
        
        # Sample test data - modify as needed
        test_data = {
            "project_id": "test-project-123",
            "num_leads": 5,
            "search_params": {
                # Add any custom search parameters here
                "organization_locations": ["San Francisco, CA"],
                "person_titles": ["CEO", "CTO", "Founder"]
            },
            "auto_enrich": False,  # Disable enrichment for testing
            "save_without_enrichment": True
        }
        
        print(f"📝 Test data: {json.dumps(test_data, indent=2)}")
        
        # Execute function
        result = find_leads_logic(test_data, auth_uid="test-user-123")
        
        print("✅ Function executed successfully!")
        print(f"📊 Result: {json.dumps(result, indent=2)}")
        
        return result
        
    except Exception as e:
        print(f"❌ Function failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def test_enrich_leads():
    """Test enrich_leads function locally"""
    print("\n🧪 Testing enrich_leads function...")
    
    try:
        from enrich_leads import enrich_leads_logic
        
        # Sample test data
        test_data = {
            "project_id": "test-project-123",
            "lead_ids": ["test-lead-1", "test-lead-2"],
            "enrichment_type": "both"  # company, person, or both
        }
        
        print(f"📝 Test data: {json.dumps(test_data, indent=2)}")
        
        result = enrich_leads_logic(test_data, auth_uid="test-user-123")
        
        print("✅ Function executed successfully!")
        print(f"📊 Result: {json.dumps(result, indent=2)}")
        
        return result
        
    except Exception as e:
        print(f"❌ Function failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def test_contact_leads():
    """Test contact_leads function locally"""
    print("\n🧪 Testing contact_leads function...")
    
    try:
        from contact_leads import contact_leads_logic
        
        # Sample test data
        test_data = {
            "project_id": "test-project-123",
            "lead_ids": ["test-lead-1", "test-lead-2"],
            "email_template_type": "initial_outreach",
            "send_immediately": False  # Don't actually send emails in test
        }
        
        print(f"📝 Test data: {json.dumps(test_data, indent=2)}")
        
        result = contact_leads_logic(test_data, auth_uid="test-user-123")
        
        print("✅ Function executed successfully!")
        print(f"📊 Result: {json.dumps(result, indent=2)}")
        
        return result
        
    except Exception as e:
        print(f"❌ Function failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def test_config_management():
    """Test configuration management functions"""
    print("\n🧪 Testing config management...")
    
    try:
        from config_management import get_project_config_logic, update_project_config_logic
        
        # Test getting config
        print("📖 Testing get_project_config...")
        get_result = get_project_config_logic({
            "project_id": "test-project-123"
        }, auth_uid="test-user-123")
        
        print(f"✅ Get config result: {json.dumps(get_result, indent=2)}")
        
        # Test updating config
        print("📝 Testing update_project_config...")
        update_data = {
            "project_id": "test-project-123",
            "config": {
                "location": {
                    "type": "city",
                    "value": "San Francisco, CA"
                },
                "job_roles": {
                    "primary_roles": ["CEO", "CTO"],
                    "secondary_roles": ["VP", "Director"]
                }
            }
        }
        
        update_result = update_project_config_logic(update_data, auth_uid="test-user-123")
        
        print(f"✅ Update config result: {json.dumps(update_result, indent=2)}")
        
        return {"get": get_result, "update": update_result}
        
    except Exception as e:
        print(f"❌ Config management test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def test_apollo_client():
    """Test Apollo client connection and basic search"""
    print("\n🧪 Testing Apollo client...")
    
    try:
        from utils import ApolloClient, get_api_keys
        
        api_keys = get_api_keys()
        if not api_keys.get('apollo'):
            print("⚠️  No Apollo API key found - skipping Apollo test")
            return None
        
        client = ApolloClient(api_keys['apollo'])
        
        # Simple test search
        search_params = {
            'person_titles': ['CEO'],
            'organization_locations': ['San Francisco, CA'],
            'per_page': 3
        }
        
        print(f"🔍 Testing Apollo search with params: {search_params}")
        
        result = client.search_people(**search_params)
        
        print(f"✅ Apollo search successful!")
        print(f"📊 Found {len(result.get('people', []))} people")
        print(f"📈 Total available: {result.get('total_entries', 0)}")
        
        return result
        
    except Exception as e:
        print(f"❌ Apollo test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def check_environment():
    """Check if all required environment variables and dependencies are available"""
    print("\n🔍 Checking environment...")
    
    # Check Python packages
    required_packages = [
        'firebase_functions', 'firebase_admin', 'requests', 
        'google-cloud-firestore', 'google-cloud-logging'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} - NOT FOUND")
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("Run: pip install -r requirements.txt")
    
    # Check environment files
    env_files = ['env.example', '.env', 'service-account.json']
    for file in env_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - NOT FOUND")
    
    # Check API keys (if .env exists)
    if os.path.exists('.env'):
        try:
            from utils import get_api_keys
            api_keys = get_api_keys()
            
            for key_name in ['apollo', 'perplexity']:
                if api_keys.get(key_name):
                    print(f"✅ {key_name.upper()} API key configured")
                else:
                    print(f"❌ {key_name.upper()} API key missing")
        except Exception as e:
            print(f"⚠️  Could not check API keys: {e}")
    
    print("✅ Environment check complete")

def interactive_menu():
    """Interactive menu for testing different functions"""
    while True:
        print("\n" + "="*50)
        print("🛠️  Firebase Functions Debug Menu")
        print("="*50)
        print("1. Check Environment")
        print("2. Test find_leads")
        print("3. Test enrich_leads")
        print("4. Test contact_leads")
        print("5. Test config_management")
        print("6. Test Apollo client")
        print("7. Run all tests")
        print("0. Exit")
        
        choice = input("\nSelect an option (0-7): ").strip()
        
        if choice == '0':
            print("👋 Goodbye!")
            break
        elif choice == '1':
            check_environment()
        elif choice == '2':
            test_find_leads()
        elif choice == '3':
            test_enrich_leads()
        elif choice == '4':
            test_contact_leads()
        elif choice == '5':
            test_config_management()
        elif choice == '6':
            test_apollo_client()
        elif choice == '7':
            print("🚀 Running all tests...")
            check_environment()
            test_apollo_client()
            test_config_management()
            test_find_leads()
            test_enrich_leads()
            test_contact_leads()
            print("✅ All tests completed!")
        else:
            print("❌ Invalid choice. Please try again.")

def main():
    """Main function"""
    print("🚀 Firebase Functions Local Debug Tool")
    print("This tool helps you test your functions locally without deployment.")
    
    if len(sys.argv) > 1:
        # Command line mode
        command = sys.argv[1].lower()
        if command == 'find-leads':
            test_find_leads()
        elif command == 'enrich-leads':
            test_enrich_leads()
        elif command == 'contact-leads':
            test_contact_leads()
        elif command == 'config':
            test_config_management()
        elif command == 'apollo':
            test_apollo_client()
        elif command == 'env':
            check_environment()
        elif command == 'all':
            check_environment()
            test_apollo_client()
            test_config_management()
            test_find_leads()
            test_enrich_leads()
            test_contact_leads()
        else:
            print(f"❌ Unknown command: {command}")
            print("Available commands: find-leads, enrich-leads, contact-leads, config, apollo, env, all")
    else:
        # Interactive mode
        interactive_menu()

if __name__ == "__main__":
    main() 