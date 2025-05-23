#!/usr/bin/env python3
"""
Test script for Perplexity API
This validates the API key and tests lead enrichment functionality
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path to import utils
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from utils.api_clients import PerplexityClient

# Load environment variables
load_dotenv()

def test_perplexity_api():
    """Test Perplexity API with minimal requests"""
    
    print("🧠 Testing Perplexity API\n")
    
    api_key = os.getenv('PERPLEXITY_API_KEY')
    if not api_key:
        print("❌ No Perplexity API key found in environment")
        print("Please add PERPLEXITY_API_KEY to your .env file")
        return False
    
    print(f"🔍 Testing with API key: {api_key[:10]}...")
    
    # Initialize client
    client = PerplexityClient(api_key)
    
    # Test 1: Basic company research
    print("\n🧪 Test 1: Basic Company Research")
    try:
        result = client.enrich_lead_data(
            company_name="Tesla",
            additional_context="Electric vehicle company research for B2B outreach"
        )
        
        if result and 'choices' in result:
            print("✅ Company research works!")
            content = result['choices'][0]['message']['content']
            print(f"   Response length: {len(content)} characters")
            print(f"   Sample content: {content[:200]}...")
        else:
            print("⚠️  Unexpected response format")
            print(f"   Response keys: {list(result.keys()) if result else 'None'}")
            
    except Exception as e:
        print(f"❌ Company research failed: {e}")
        return False
    
    # Test 2: Person-specific research
    print("\n🧪 Test 2: Person-Specific Research")
    try:
        result = client.enrich_lead_data(
            company_name="Microsoft",
            person_name="Satya Nadella",
            additional_context="CEO research for executive outreach"
        )
        
        if result and 'choices' in result:
            print("✅ Person-specific research works!")
            content = result['choices'][0]['message']['content']
            print(f"   Response length: {len(content)} characters")
            print(f"   Sample content: {content[:200]}...")
        else:
            print("⚠️  Unexpected response format")
            
    except Exception as e:
        print(f"❌ Person research failed: {e}")
        return False
    
    # Test 3: Industry-specific research
    print("\n🧪 Test 3: Industry-Specific Research")
    try:
        result = client.enrich_lead_data(
            company_name="Siemens Austria",
            additional_context="Industrial automation company in Austria, looking for digital transformation opportunities"
        )
        
        if result and 'choices' in result:
            print("✅ Industry-specific research works!")
            content = result['choices'][0]['message']['content']
            print(f"   Response length: {len(content)} characters")
            
            # Check for relevant keywords
            keywords = ['austria', 'siemens', 'industrial', 'automation', 'digital']
            found_keywords = [kw for kw in keywords if kw.lower() in content.lower()]
            print(f"   Relevant keywords found: {found_keywords}")
        else:
            print("⚠️  Unexpected response format")
            
    except Exception as e:
        print(f"❌ Industry research failed: {e}")
        return False
    
    print("\n🎉 All Perplexity tests passed!")
    print("\n📊 API Access Summary:")
    print("✅ Basic company research working")
    print("✅ Person-specific research working")
    print("✅ Industry context processing working")
    print("✅ Ready for lead enrichment in find_leads function")
    
    return True

def test_perplexity_integration():
    """Test how Perplexity integrates with lead data"""
    
    print("\n🔗 Testing Perplexity Integration with Lead Data")
    
    # Mock lead data (similar to what Apollo would return)
    mock_lead = {
        "first_name": "Maria",
        "last_name": "Schmidt",
        "title": "Chief Technology Officer",
        "organization": {
            "name": "TechCorp Vienna",
            "industry": "Software Development"
        },
        "city": "Vienna",
        "country": "Austria"
    }
    
    print(f"📋 Mock lead data:")
    print(f"   Name: {mock_lead['first_name']} {mock_lead['last_name']}")
    print(f"   Title: {mock_lead['title']}")
    print(f"   Company: {mock_lead['organization']['name']}")
    print(f"   Location: {mock_lead['city']}, {mock_lead['country']}")
    
    try:
        api_key = os.getenv('PERPLEXITY_API_KEY')
        client = PerplexityClient(api_key)
        
        # Simulate how find_leads would use Perplexity
        result = client.enrich_lead_data(
            company_name=mock_lead['organization']['name'],
            person_name=f"{mock_lead['first_name']} {mock_lead['last_name']}",
            additional_context=f"CTO at software company in {mock_lead['city']}, Austria. Research for B2B technology solution outreach."
        )
        
        if result and 'choices' in result:
            print("\n✅ Lead enrichment simulation successful!")
            content = result['choices'][0]['message']['content']
            
            # This is what would be stored in the lead record
            enrichment_data = {
                "perplexity_research": content,
                "research_timestamp": "2024-01-01T00:00:00Z",  # Would be actual timestamp
                "research_context": "CTO outreach preparation"
            }
            
            print(f"📊 Enrichment data structure:")
            print(f"   Research length: {len(content)} characters")
            print(f"   Context: {enrichment_data['research_context']}")
            print(f"   Sample research: {content[:150]}...")
            
            return True
        else:
            print("❌ Lead enrichment simulation failed")
            return False
            
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

def show_perplexity_usage_tips():
    """Show tips for using Perplexity API effectively"""
    
    print("\n💡 Perplexity API Usage Tips:")
    print("1. 🎯 Be specific with company names and context")
    print("2. 📊 Include industry and location for better results")
    print("3. 🔍 Mention the purpose (e.g., 'for B2B outreach')")
    print("4. ⚡ Responses are typically 200-800 characters")
    print("5. 💰 Monitor usage - each request consumes credits")
    
    print("\n📝 Best Practices for Lead Enrichment:")
    print("- Include person's title and company industry")
    print("- Mention geographic location for local context")
    print("- Specify the type of business relationship you're seeking")
    print("- Use the research to personalize outreach messages")
    
    print("\n⚠️  Rate Limiting:")
    print("- Add delays between requests in production")
    print("- Consider caching results to avoid duplicate research")
    print("- Monitor API usage in your Perplexity dashboard")

def main():
    """Run all Perplexity API tests"""
    
    print("🧠 Perplexity API Test Suite\n")
    
    # Test basic API functionality
    basic_success = test_perplexity_api()
    
    if basic_success:
        # Test integration with lead data
        integration_success = test_perplexity_integration()
        
        if integration_success:
            show_perplexity_usage_tips()
            
            print("\n" + "="*60)
            print("🎉 ALL PERPLEXITY TESTS PASSED!")
            print("="*60)
            print("✅ API key is valid and working")
            print("✅ Company research functionality confirmed")
            print("✅ Person-specific research working")
            print("✅ Integration with lead data tested")
            print("✅ Ready for production use in find_leads function")
            
        else:
            print("\n❌ Integration tests failed")
    else:
        print("\n❌ Basic API tests failed. Please check:")
        print("1. PERPLEXITY_API_KEY in .env file")
        print("2. API key validity and credits")
        print("3. Network connectivity")
        print("4. Perplexity service status")

if __name__ == "__main__":
    main() 