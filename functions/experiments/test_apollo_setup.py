#!/usr/bin/env python3
"""
Simple test script to verify Apollo API setup
Run this before using the notebook to ensure everything is configured correctly.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path to import utils
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

def test_environment():
    """Test environment setup"""
    print("🔧 Testing environment setup...")
    
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ python-dotenv loaded successfully")
    except ImportError:
        print("❌ python-dotenv not installed. Run: pip install python-dotenv")
        return False
    
    # Check for .env file
    env_file = parent_dir / ".env"
    if env_file.exists():
        print("✅ .env file found")
    else:
        print("⚠️  .env file not found. Copy env.example to .env and add your API keys")
        return False
    
    # Check Apollo API key
    apollo_key = os.getenv('APOLLO_API_KEY')
    if apollo_key:
        print("✅ APOLLO_API_KEY found in environment")
        print(f"   Key starts with: {apollo_key[:10]}...")
    else:
        print("❌ APOLLO_API_KEY not found in environment")
        return False
    
    return True

def test_imports():
    """Test importing the utils modules"""
    print("\n📦 Testing imports...")
    
    try:
        from utils.api_clients import ApolloClient
        print("✅ ApolloClient imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import ApolloClient: {e}")
        return False
    
    try:
        import requests
        print("✅ requests library available")
    except ImportError:
        print("❌ requests library not available")
        return False
    
    return True

def test_apollo_client():
    """Test Apollo client initialization"""
    print("\n🚀 Testing Apollo client...")
    
    try:
        from utils.api_clients import ApolloClient
        apollo_key = os.getenv('APOLLO_API_KEY')
        
        if not apollo_key:
            print("❌ No Apollo API key available for testing")
            return False
        
        client = ApolloClient(apollo_key)
        print("✅ Apollo client initialized successfully")
        
        # Test a simple search (very small to avoid using credits)
        print("🔍 Testing basic API call...")
        results = client.search_people(
            job_titles=["CEO"],
            per_page=1,
            page=1
        )
        
        if results and 'people' in results:
            print(f"✅ API call successful! Found {len(results['people'])} result(s)")
            return True
        else:
            print("⚠️  API call returned no results (this might be normal)")
            return True
            
    except Exception as e:
        print(f"❌ Apollo client test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Apollo API Setup Test\n")
    
    tests = [
        ("Environment Setup", test_environment),
        ("Module Imports", test_imports),
        ("Apollo Client", test_apollo_client)
    ]
    
    all_passed = True
    
    for test_name, test_func in tests:
        try:
            if not test_func():
                all_passed = False
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            all_passed = False
    
    print("\n" + "="*50)
    if all_passed:
        print("🎉 All tests passed! You can now run the notebook.")
        print("\nNext steps:")
        print("1. Open experiments/apollo_api_testing.ipynb")
        print("2. Run the cells to test Apollo API integration")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("1. Copy env.example to .env")
        print("2. Add your Apollo API key to .env")
        print("3. Install requirements: pip install -r requirements.txt")

if __name__ == "__main__":
    main() 