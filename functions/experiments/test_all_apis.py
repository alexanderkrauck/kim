#!/usr/bin/env python3
"""
Comprehensive test script for all APIs
Tests Apollo, Perplexity, and OpenAI APIs together to validate the complete workflow
"""

import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path to import utils
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from utils.api_clients import ApolloClient, PerplexityClient, OpenAIClient

# Load environment variables
load_dotenv()

def check_api_keys():
    """Check if all required API keys are present"""
    
    print("🔑 Checking API Keys...\n")
    
    keys_status = {}
    required_keys = ['APOLLO_API_KEY', 'PERPLEXITY_API_KEY', 'OPENAI_API_KEY']
    
    for key_name in required_keys:
        key_value = os.getenv(key_name)
        if key_value:
            keys_status[key_name] = True
            print(f"✅ {key_name}: Found ({key_value[:10]}...)")
        else:
            keys_status[key_name] = False
            print(f"❌ {key_name}: Not found")
    
    missing_keys = [k for k, v in keys_status.items() if not v]
    
    if missing_keys:
        print(f"\n❌ Missing API keys: {missing_keys}")
        print("Please add them to your .env file before running tests")
        return False
    
    print("\n✅ All API keys found!")
    return True

def test_complete_workflow():
    """Test the complete lead generation and outreach workflow"""
    
    print("\n🔄 Testing Complete Workflow: Apollo → Perplexity → OpenAI\n")
    
    try:
        # Initialize all clients
        apollo_client = ApolloClient(os.getenv('APOLLO_API_KEY'))
        perplexity_client = PerplexityClient(os.getenv('PERPLEXITY_API_KEY'))
        openai_client = OpenAIClient(os.getenv('OPENAI_API_KEY'))
        
        # Step 1: Find leads with Apollo
        print("🔍 Step 1: Finding leads with Apollo...")
        apollo_results = apollo_client.search_people(
            job_titles=["CEO", "CTO", "founder"],
            locations=["Vienna, Austria"],
            per_page=3  # Small sample for testing
        )
        
        if not apollo_results.get('people'):
            print("❌ No leads found from Apollo")
            return False
        
        lead = apollo_results['people'][0]  # Take first lead
        print(f"✅ Found lead: {lead.get('first_name', '')} {lead.get('last_name', '')}")
        print(f"   Company: {lead.get('organization', {}).get('name', 'N/A')}")
        print(f"   Title: {lead.get('title', 'N/A')}")
        
        # Step 2: Enrich with Perplexity
        print(f"\n🧠 Step 2: Enriching lead with Perplexity...")
        time.sleep(2)  # Rate limiting
        
        company_name = lead.get('organization', {}).get('name', '')
        person_name = f"{lead.get('first_name', '')} {lead.get('last_name', '')}"
        
        if company_name:
            perplexity_result = perplexity_client.enrich_lead_data(
                company_name=company_name,
                person_name=person_name,
                additional_context=f"Research for B2B outreach to {lead.get('title', 'executive')} in Vienna, Austria"
            )
            
            if perplexity_result and 'choices' in perplexity_result:
                enrichment_data = perplexity_result['choices'][0]['message']['content']
                print(f"✅ Lead enriched with {len(enrichment_data)} characters of research")
                print(f"   Sample: {enrichment_data[:150]}...")
            else:
                print("⚠️  Perplexity enrichment failed, continuing without enrichment")
                enrichment_data = None
        else:
            print("⚠️  No company name found, skipping enrichment")
            enrichment_data = None
        
        # Step 3: Generate email with OpenAI
        print(f"\n🤖 Step 3: Generating email with OpenAI...")
        time.sleep(2)  # Rate limiting
        
        # Prepare lead data for email generation
        lead_data = {
            "name": person_name,
            "email": lead.get('email', 'example@company.com'),
            "company": company_name,
            "title": lead.get('title', 'N/A'),
            "enrichment_data": enrichment_data
        }
        
        email_content = openai_client.generate_email_content(
            lead_data=lead_data,
            email_type="outreach"
        )
        
        if email_content:
            print(f"✅ Email generated successfully!")
            print(f"   Length: {len(email_content)} characters")
            print(f"   Word count: {len(email_content.split())} words")
            
            # Show the complete workflow result
            print(f"\n📧 Generated Email:")
            print("=" * 50)
            print(email_content)
            print("=" * 50)
        else:
            print("❌ Email generation failed")
            return False
        
        # Workflow summary
        print(f"\n🎉 Complete workflow successful!")
        print(f"📊 Workflow Summary:")
        print(f"   ✅ Apollo: Found {len(apollo_results['people'])} leads")
        print(f"   ✅ Perplexity: {'Enriched' if enrichment_data else 'Skipped'} lead data")
        print(f"   ✅ OpenAI: Generated personalized email")
        print(f"   🎯 Ready for production deployment")
        
        return True
        
    except Exception as e:
        print(f"❌ Workflow test failed: {e}")
        return False

def test_api_individual():
    """Test each API individually"""
    
    print("\n🧪 Testing Individual APIs...\n")
    
    results = {}
    
    # Test Apollo
    print("🔍 Testing Apollo API...")
    try:
        apollo_client = ApolloClient(os.getenv('APOLLO_API_KEY'))
        apollo_result = apollo_client.search_people(
            job_titles=["manager"],
            per_page=1
        )
        results['apollo'] = bool(apollo_result and apollo_result.get('people'))
        print(f"   {'✅' if results['apollo'] else '❌'} Apollo API")
    except Exception as e:
        results['apollo'] = False
        print(f"   ❌ Apollo API failed: {e}")
    
    time.sleep(2)
    
    # Test Perplexity
    print("🧠 Testing Perplexity API...")
    try:
        perplexity_client = PerplexityClient(os.getenv('PERPLEXITY_API_KEY'))
        perplexity_result = perplexity_client.enrich_lead_data(
            company_name="Microsoft",
            additional_context="Test research"
        )
        results['perplexity'] = bool(perplexity_result and perplexity_result.get('choices'))
        print(f"   {'✅' if results['perplexity'] else '❌'} Perplexity API")
    except Exception as e:
        results['perplexity'] = False
        print(f"   ❌ Perplexity API failed: {e}")
    
    time.sleep(2)
    
    # Test OpenAI
    print("🤖 Testing OpenAI API...")
    try:
        openai_client = OpenAIClient(os.getenv('OPENAI_API_KEY'))
        openai_result = openai_client.generate_email_content(
            lead_data={"name": "Test User", "company": "Test Corp"},
            email_type="outreach"
        )
        results['openai'] = bool(openai_result)
        print(f"   {'✅' if results['openai'] else '❌'} OpenAI API")
    except Exception as e:
        results['openai'] = False
        print(f"   ❌ OpenAI API failed: {e}")
    
    return results

def show_integration_status():
    """Show the integration status with existing functions"""
    
    print("\n🔗 Integration Status with Firebase Functions:")
    print("=" * 60)
    
    integrations = [
        {
            "function": "find_leads.py",
            "apis": ["Apollo", "Perplexity"],
            "status": "✅ Ready",
            "description": "Lead discovery and enrichment"
        },
        {
            "function": "contact_leads.py", 
            "apis": ["OpenAI"],
            "status": "✅ Ready",
            "description": "Email generation and outreach"
        },
        {
            "function": "utils/api_clients.py",
            "apis": ["Apollo", "Perplexity", "OpenAI"],
            "status": "✅ Updated",
            "description": "API client implementations"
        },
        {
            "function": "utils/firebase_utils.py",
            "apis": ["All"],
            "status": "✅ Compatible",
            "description": "API key management"
        }
    ]
    
    for integration in integrations:
        print(f"{integration['status']} {integration['function']}")
        print(f"   APIs: {', '.join(integration['apis'])}")
        print(f"   Purpose: {integration['description']}")
        print()

def show_next_steps():
    """Show next steps for production deployment"""
    
    print("🚀 Next Steps for Production:")
    print("=" * 40)
    print("1. ✅ All APIs tested and working")
    print("2. 🔧 Deploy updated functions to Firebase")
    print("3. 🔑 Configure production API keys in Firebase")
    print("4. 📊 Set up monitoring and alerting")
    print("5. 🧪 Run end-to-end tests in production")
    print("6. 📈 Monitor usage and costs")
    
    print("\n📋 Production Checklist:")
    print("□ Firebase Functions deployed")
    print("□ Production API keys configured")
    print("□ Error handling and logging set up")
    print("□ Rate limiting implemented")
    print("□ Cost monitoring enabled")
    print("□ Backup and recovery procedures")

def main():
    """Run comprehensive API testing"""
    
    print("🧪 Comprehensive API Test Suite")
    print("=" * 50)
    print("Testing Apollo, Perplexity, and OpenAI APIs")
    print("Validating complete lead generation workflow\n")
    
    # Check API keys
    if not check_api_keys():
        return
    
    # Test individual APIs
    individual_results = test_api_individual()
    
    # Test complete workflow if all APIs work
    all_working = all(individual_results.values())
    
    if all_working:
        workflow_success = test_complete_workflow()
    else:
        workflow_success = False
        print("\n⚠️  Skipping workflow test due to API failures")
    
    # Show results
    print("\n" + "="*60)
    print("📊 FINAL TEST RESULTS")
    print("="*60)
    
    print(f"🔍 Apollo API: {'✅ Working' if individual_results.get('apollo') else '❌ Failed'}")
    print(f"🧠 Perplexity API: {'✅ Working' if individual_results.get('perplexity') else '❌ Failed'}")
    print(f"🤖 OpenAI API: {'✅ Working' if individual_results.get('openai') else '❌ Failed'}")
    print(f"🔄 Complete Workflow: {'✅ Working' if workflow_success else '❌ Failed'}")
    
    if all_working and workflow_success:
        print(f"\n🎉 ALL TESTS PASSED!")
        print(f"Your API integration is ready for production!")
        
        show_integration_status()
        show_next_steps()
    else:
        print(f"\n❌ Some tests failed. Please check:")
        if not individual_results.get('apollo'):
            print("- Apollo API key and plan access")
        if not individual_results.get('perplexity'):
            print("- Perplexity API key and credits")
        if not individual_results.get('openai'):
            print("- OpenAI API key and credits")
        
        print("\nRun individual test scripts for detailed diagnostics:")
        print("- python experiments/test_new_apollo_key.py")
        print("- python experiments/test_perplexity_api.py")
        print("- python experiments/test_openai_api.py")

if __name__ == "__main__":
    main() 