#!/usr/bin/env python3
"""
Test script for the new enrich_leads Firebase function
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path to import utils
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from utils import get_api_keys, PerplexityClient

# Load environment variables
load_dotenv()

def test_enrich_leads_function():
    """Test the enrich_leads function logic"""
    
    print("🧪 Testing Enrich Leads Function Logic\n")
    
    # Test 1: Check API keys
    print("🔑 Test 1: Checking API Keys")
    api_keys = get_api_keys()
    
    if api_keys.get('perplexity'):
        print("   ✅ Perplexity API key found")
    else:
        print("   ❌ Perplexity API key not found")
        return False
    
    # Test 2: Test Perplexity client
    print("\n🧠 Test 2: Testing Perplexity Client")
    try:
        perplexity_client = PerplexityClient(api_keys['perplexity'])
        
        # Test company enrichment
        company_research = perplexity_client.enrich_lead_data(
            company_name="Microsoft",
            additional_context="Research for lead generation project: Software development services"
        )
        
        if company_research and company_research.get('choices'):
            content = company_research['choices'][0]['message']['content']
            print(f"   ✅ Company research successful ({len(content)} characters)")
            print(f"   📄 Sample: {content[:100]}...")
        else:
            print("   ❌ Company research failed")
            return False
            
    except Exception as e:
        print(f"   ❌ Perplexity client error: {e}")
        return False
    
    # Test 3: Test person enrichment
    print("\n👤 Test 3: Testing Person Enrichment")
    try:
        person_research = perplexity_client.enrich_lead_data(
            company_name="Microsoft",
            person_name="Satya Nadella",
            additional_context="Research about this person for outreach: Cloud services partnership"
        )
        
        if person_research and person_research.get('choices'):
            content = person_research['choices'][0]['message']['content']
            print(f"   ✅ Person research successful ({len(content)} characters)")
            print(f"   📄 Sample: {content[:100]}...")
        else:
            print("   ❌ Person research failed")
            return False
            
    except Exception as e:
        print(f"   ❌ Person enrichment error: {e}")
        return False
    
    # Test 4: Test enrichment data validation
    print("\n✅ Test 4: Testing Enrichment Data Validation")
    
    # Import the validation function
    from enrich_leads import validate_enrichment_data
    
    # Test valid data
    valid_data = {
        'company_research': 'Microsoft is a leading technology company founded in 1975 by Bill Gates and Paul Allen. The company is headquartered in Redmond, Washington and is known for its Windows operating system, Office productivity suite, and Azure cloud platform.',
        'person_research': 'Satya Nadella is the CEO of Microsoft, having taken over from Steve Ballmer in 2014. Under his leadership, Microsoft has focused heavily on cloud computing and artificial intelligence.'
    }
    
    if validate_enrichment_data(valid_data):
        print("   ✅ Valid enrichment data passed validation")
    else:
        print("   ❌ Valid enrichment data failed validation")
        return False
    
    # Test invalid data
    invalid_data = {
        'company_research': 'I don\'t have information about this company.',
        'person_research': 'No information available for this person.'
    }
    
    if not validate_enrichment_data(invalid_data):
        print("   ✅ Invalid enrichment data correctly rejected")
    else:
        print("   ❌ Invalid enrichment data incorrectly accepted")
        return False
    
    # Test 5: Test priority scoring
    print("\n📊 Test 5: Testing Priority Scoring")
    
    from enrich_leads import determine_enrichment_priority
    
    # High priority lead
    high_priority_lead = {
        'email': 'ceo@company.com',
        'phone': '+1234567890',
        'company': 'Tech Corp',
        'title': 'CEO and Founder',
        'companySize': 5000
    }
    
    high_score = determine_enrichment_priority(high_priority_lead)
    print(f"   📈 High priority lead score: {high_score}")
    
    # Low priority lead
    low_priority_lead = {
        'email': 'intern@company.com',
        'title': 'Intern',
        'companySize': 10
    }
    
    low_score = determine_enrichment_priority(low_priority_lead)
    print(f"   📉 Low priority lead score: {low_score}")
    
    if high_score > low_score:
        print("   ✅ Priority scoring working correctly")
    else:
        print("   ❌ Priority scoring not working correctly")
        return False
    
    print(f"\n🎉 All tests passed!")
    print(f"✅ Enrich leads function is ready for use")
    
    return True

def simulate_enrichment_workflow():
    """Simulate the enrichment workflow"""
    
    print("\n" + "="*50)
    print("🔄 SIMULATING ENRICHMENT WORKFLOW")
    print("="*50)
    
    # Sample lead data
    sample_leads = [
        {
            'id': 'lead_001',
            'name': 'John Smith',
            'email': 'john.smith@techcorp.com',
            'company': 'TechCorp',
            'title': 'CTO',
            'projectId': 'project_123'
        },
        {
            'id': 'lead_002',
            'name': 'Jane Doe',
            'email': 'jane.doe@innovate.com',
            'company': 'Innovate Inc',
            'title': 'VP of Engineering',
            'projectId': 'project_123'
        }
    ]
    
    print(f"📋 Processing {len(sample_leads)} sample leads...")
    
    api_keys = get_api_keys()
    perplexity_client = PerplexityClient(api_keys['perplexity'])
    
    for i, lead in enumerate(sample_leads, 1):
        print(f"\n🔍 Lead {i}: {lead['name']} at {lead['company']}")
        
        try:
            # Company enrichment
            company_research = perplexity_client.enrich_lead_data(
                company_name=lead['company'],
                additional_context="Research for lead generation project: Software development services"
            )
            
            if company_research and company_research.get('choices'):
                company_content = company_research['choices'][0]['message']['content']
                print(f"   ✅ Company research: {len(company_content)} characters")
            
            # Person enrichment
            person_research = perplexity_client.enrich_lead_data(
                company_name=lead['company'],
                person_name=lead['name'],
                additional_context="Research about this person for outreach"
            )
            
            if person_research and person_research.get('choices'):
                person_content = person_research['choices'][0]['message']['content']
                print(f"   ✅ Person research: {len(person_content)} characters")
            
            print(f"   🎯 Lead {lead['name']} enriched successfully")
            
        except Exception as e:
            print(f"   ❌ Failed to enrich {lead['name']}: {e}")
    
    print(f"\n✅ Enrichment workflow simulation completed!")

if __name__ == "__main__":
    print("🚀 Testing Enrich Leads Function")
    print("="*50)
    
    success = test_enrich_leads_function()
    
    if success:
        simulate_enrichment_workflow()
    else:
        print("\n❌ Tests failed - fix issues before proceeding")
        sys.exit(1) 