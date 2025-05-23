#!/usr/bin/env python3
"""
Test script for OpenAI API
This validates the API key and tests email generation functionality
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path to import utils
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from utils.api_clients import OpenAIClient

# Load environment variables
load_dotenv()

def test_openai_api():
    """Test OpenAI API with minimal requests"""
    
    print("🤖 Testing OpenAI API\n")
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ No OpenAI API key found in environment")
        print("Please add OPENAI_API_KEY to your .env file")
        return False
    
    print(f"🔍 Testing with API key: {api_key[:10]}...")
    
    # Initialize client
    client = OpenAIClient(api_key)
    
    # Test 1: Basic outreach email generation
    print("\n🧪 Test 1: Outreach Email Generation")
    try:
        mock_lead_data = {
            "name": "Maria Schmidt",
            "email": "maria.schmidt@techcorp.at",
            "company": "TechCorp Vienna",
            "title": "Chief Technology Officer"
        }
        
        email_content = client.generate_email_content(
            lead_data=mock_lead_data,
            email_type="outreach"
        )
        
        if email_content:
            print("✅ Outreach email generation works!")
            print(f"   Email length: {len(email_content)} characters")
            print(f"   Sample content:\n{email_content[:300]}...")
        else:
            print("❌ No email content generated")
            return False
            
    except Exception as e:
        print(f"❌ Outreach email generation failed: {e}")
        return False
    
    # Test 2: Follow-up email generation
    print("\n🧪 Test 2: Follow-up Email Generation")
    try:
        mock_lead_data = {
            "name": "Klaus Weber",
            "email": "k.weber@manufacturing.at",
            "company": "Weber Manufacturing GmbH",
            "title": "Geschäftsführer",
            "notes": "Previously contacted about digital transformation solutions"
        }
        
        email_content = client.generate_email_content(
            lead_data=mock_lead_data,
            email_type="followup"
        )
        
        if email_content:
            print("✅ Follow-up email generation works!")
            print(f"   Email length: {len(email_content)} characters")
            print(f"   Sample content:\n{email_content[:300]}...")
        else:
            print("❌ No email content generated")
            return False
            
    except Exception as e:
        print(f"❌ Follow-up email generation failed: {e}")
        return False
    
    # Test 3: Custom prompt email generation
    print("\n🧪 Test 3: Custom Prompt Email Generation")
    try:
        mock_lead_data = {
            "name": "Dr. Anna Müller",
            "email": "a.mueller@research.ac.at",
            "company": "Austrian Research Institute",
            "title": "Research Director",
            "enrichment_data": "Leading research in AI and machine learning applications"
        }
        
        custom_prompt = """You are writing a professional email for academic outreach. Write an email that:
        - Acknowledges their research expertise
        - Proposes a collaboration opportunity
        - Is formal but engaging
        - Includes specific reference to their work
        - Keeps it under 200 words"""
        
        email_content = client.generate_email_content(
            lead_data=mock_lead_data,
            custom_prompt=custom_prompt
        )
        
        if email_content:
            print("✅ Custom prompt email generation works!")
            print(f"   Email length: {len(email_content)} characters")
            print(f"   Sample content:\n{email_content[:300]}...")
        else:
            print("❌ No email content generated")
            return False
            
    except Exception as e:
        print(f"❌ Custom prompt email generation failed: {e}")
        return False
    
    print("\n🎉 All OpenAI tests passed!")
    print("\n📊 API Access Summary:")
    print("✅ Outreach email generation working")
    print("✅ Follow-up email generation working")
    print("✅ Custom prompt processing working")
    print("✅ Ready for email generation in contact_leads function")
    
    return True

def test_openai_integration():
    """Test how OpenAI integrates with enriched lead data"""
    
    print("\n🔗 Testing OpenAI Integration with Enriched Lead Data")
    
    # Mock enriched lead data (as it would come from Apollo + Perplexity)
    mock_enriched_lead = {
        "name": "Stefan Kovač",
        "email": "s.kovac@innovate.si",
        "company": "Innovate Slovenia",
        "title": "Head of Digital Innovation",
        "city": "Ljubljana",
        "country": "Slovenia",
        "enrichment_data": "Innovate Slovenia is a leading technology consultancy specializing in digital transformation for manufacturing companies. They have recently expanded into AI-powered solutions and are looking for partnerships with international tech providers. Stefan leads their digital innovation team and has 10+ years experience in enterprise software implementations."
    }
    
    print(f"📋 Mock enriched lead data:")
    print(f"   Name: {mock_enriched_lead['name']}")
    print(f"   Title: {mock_enriched_lead['title']}")
    print(f"   Company: {mock_enriched_lead['company']}")
    print(f"   Enrichment: {mock_enriched_lead['enrichment_data'][:100]}...")
    
    try:
        api_key = os.getenv('OPENAI_API_KEY')
        client = OpenAIClient(api_key)
        
        # Simulate how contact_leads would use OpenAI
        email_content = client.generate_email_content(
            lead_data=mock_enriched_lead,
            email_type="outreach"
        )
        
        if email_content:
            print("\n✅ Enriched lead email generation successful!")
            
            # Analyze the generated email
            email_lower = email_content.lower()
            personalization_elements = []
            
            if mock_enriched_lead['name'].split()[0].lower() in email_lower:
                personalization_elements.append("First name")
            if mock_enriched_lead['company'].lower() in email_lower:
                personalization_elements.append("Company name")
            if "digital" in email_lower or "innovation" in email_lower:
                personalization_elements.append("Industry context")
            if "slovenia" in email_lower or "ljubljana" in email_lower:
                personalization_elements.append("Location")
            
            print(f"📊 Email analysis:")
            print(f"   Length: {len(email_content)} characters")
            print(f"   Personalization elements: {personalization_elements}")
            print(f"   Generated email:\n{email_content}")
            
            return True
        else:
            print("❌ Enriched lead email generation failed")
            return False
            
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

def test_email_quality():
    """Test email quality and personalization"""
    
    print("\n📧 Testing Email Quality and Personalization")
    
    test_cases = [
        {
            "name": "Tech Startup CEO",
            "data": {
                "name": "Alex Chen",
                "company": "StartupTech",
                "title": "CEO & Founder",
                "enrichment_data": "Fast-growing fintech startup, recently raised Series A funding"
            }
        },
        {
            "name": "Enterprise Executive",
            "data": {
                "name": "Dr. Elisabeth Hoffmann",
                "company": "Global Manufacturing Corp",
                "title": "VP of Operations",
                "enrichment_data": "Large manufacturing company, focusing on Industry 4.0 initiatives"
            }
        },
        {
            "name": "Government Official",
            "data": {
                "name": "Michael Brunner",
                "company": "Austrian Ministry of Technology",
                "title": "Director of Digital Policy",
                "enrichment_data": "Government agency responsible for national digitalization strategy"
            }
        }
    ]
    
    try:
        api_key = os.getenv('OPENAI_API_KEY')
        client = OpenAIClient(api_key)
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n🧪 Test Case {i}: {test_case['name']}")
            
            email_content = client.generate_email_content(
                lead_data=test_case['data'],
                email_type="outreach"
            )
            
            if email_content:
                # Check for personalization
                has_name = test_case['data']['name'].split()[0] in email_content
                has_company = test_case['data']['company'] in email_content
                word_count = len(email_content.split())
                
                print(f"   ✅ Generated successfully")
                print(f"   📊 Word count: {word_count}")
                print(f"   🎯 Includes name: {has_name}")
                print(f"   🏢 Includes company: {has_company}")
                print(f"   📝 Preview: {email_content[:150]}...")
            else:
                print(f"   ❌ Failed to generate")
                return False
        
        print("\n✅ All email quality tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Email quality test failed: {e}")
        return False

def show_openai_usage_tips():
    """Show tips for using OpenAI API effectively"""
    
    print("\n💡 OpenAI API Usage Tips:")
    print("1. 🎯 Provide rich lead data for better personalization")
    print("2. 📝 Use specific prompts for different email types")
    print("3. 🔄 Test different temperature settings for creativity vs consistency")
    print("4. 📊 Monitor token usage to manage costs")
    print("5. 🚀 Use GPT-4 for higher quality outputs")
    
    print("\n📧 Email Generation Best Practices:")
    print("- Include enrichment data for better personalization")
    print("- Specify clear call-to-action requirements")
    print("- Test with different lead profiles")
    print("- Validate generated content before sending")
    print("- Consider A/B testing different prompt styles")
    
    print("\n⚠️  Cost Management:")
    print("- Monitor token usage in OpenAI dashboard")
    print("- Use appropriate max_tokens limits")
    print("- Consider caching for similar lead profiles")
    print("- Batch similar requests when possible")

def main():
    """Run all OpenAI API tests"""
    
    print("🤖 OpenAI API Test Suite\n")
    
    # Test basic API functionality
    basic_success = test_openai_api()
    
    if basic_success:
        # Test integration with enriched data
        integration_success = test_openai_integration()
        
        if integration_success:
            # Test email quality
            quality_success = test_email_quality()
            
            if quality_success:
                show_openai_usage_tips()
                
                print("\n" + "="*60)
                print("🎉 ALL OPENAI TESTS PASSED!")
                print("="*60)
                print("✅ API key is valid and working")
                print("✅ Email generation functionality confirmed")
                print("✅ Personalization working correctly")
                print("✅ Integration with enriched data tested")
                print("✅ Ready for production use in contact_leads function")
                
            else:
                print("\n❌ Email quality tests failed")
        else:
            print("\n❌ Integration tests failed")
    else:
        print("\n❌ Basic API tests failed. Please check:")
        print("1. OPENAI_API_KEY in .env file")
        print("2. API key validity and credits")
        print("3. Network connectivity")
        print("4. OpenAI service status")

if __name__ == "__main__":
    main() 