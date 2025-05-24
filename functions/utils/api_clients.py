"""
API client utilities for external services
"""

import os
import requests
from typing import Dict, List, Optional, Any
from openai import OpenAI
from utils.logging_config import get_logger

logger = get_logger(__file__)


class ApolloClient:
    """Client for Apollo.io API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.apollo.io/api/v1"
        self.headers = {
            "accept": "application/json",
            "Cache-Control": "no-cache", 
            "Content-Type": "application/json",
            "x-api-key": api_key  # Apollo uses lowercase header
        }
    
    def search_people(self, 
                     organization_domains: List[str] = None,
                     person_titles: List[str] = None,
                     person_locations: List[str] = None,
                     organization_locations: List[str] = None,
                     contact_email_status: List[str] = None,
                     page: int = 1,
                     per_page: int = 25,
                     **kwargs) -> Dict[str, Any]:
        """
        Search for people using Apollo.io API
        
        Args:
            organization_domains: List of company domains to search
            person_titles: List of job titles to search for
            person_locations: List of person locations to search in
            organization_locations: List of organization locations to search in
            contact_email_status: List of email status filters
            page: Page number for pagination
            per_page: Number of results per page
            **kwargs: Additional search parameters
            
        Returns:
            Dict containing search results
        """
        import urllib.parse
        
        base_url = f"{self.base_url}/mixed_people/search"
        
        # Build query parameters
        params = []
        
        # Add pagination parameters
        params.append(f"page={page}")
        params.append(f"per_page={per_page}")
        
        # Add array parameters - Apollo expects array format like: param[]=value1&param[]=value2
        if organization_domains:
            for domain in organization_domains:
                params.append(f"organization_domains[]={urllib.parse.quote(str(domain))}")
        
        if person_titles:
            for title in person_titles:
                params.append(f"person_titles[]={urllib.parse.quote(str(title))}")
        
        if person_locations:
            for location in person_locations:
                params.append(f"person_locations[]={urllib.parse.quote(str(location))}")
                
        if organization_locations:
            for location in organization_locations:
                params.append(f"organization_locations[]={urllib.parse.quote(str(location))}")
                
        if contact_email_status:
            for status in contact_email_status:
                params.append(f"contact_email_status[]={urllib.parse.quote(str(status))}")
        
        # Handle additional parameters from kwargs
        for key, value in kwargs.items():
            if isinstance(value, list):
                # Handle array parameters
                for item in value:
                    params.append(f"{key}[]={urllib.parse.quote(str(item))}")
            else:
                # Handle single value parameters
                params.append(f"{key}={urllib.parse.quote(str(value))}")
        
        # Build final URL with query parameters
        if params:
            url = f"{base_url}?{'&'.join(params)}"
        else:
            url = base_url
            
        try:
            # Log the complete API call details
            logger.info("🚀 APOLLO API CALL:")
            logger.info(f"📋 Method: POST")
            logger.info(f"🔗 URL: {url}")
            logger.info(f"📤 Headers: {self.headers}")
            logger.info(f"📦 Body: None (query parameters only)")
            
            # POST request with query parameters, no JSON body
            response = requests.post(url, headers=self.headers)
            
            # Log response details
            logger.info(f"📥 Response Status: {response.status_code}")
            logger.info(f"📊 Response Size: {len(response.content)} bytes")
            
            response.raise_for_status()
            result = response.json()
            
            # Log result summary
            people_count = len(result.get('people', []))
            total_available = result.get('pagination', {}).get('total_entries', 0)
            logger.info(f"✅ Apollo Success: {people_count} people returned, {total_available} total available")
            
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Apollo API error: {e}")
            logger.error(f"🔗 Failed URL: {url}")
            logger.error(f"📤 Headers used: {self.headers}")
            raise
    
    def get_person_details(self, person_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific person"""
        url = f"{self.base_url}/people/{person_id}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Apollo API error getting person details: {e}")
            raise
    
    def test_api_access(self) -> Dict[str, Any]:
        """Test API access and return account information"""
        # Try to get users list as a simple test
        url = f"{self.base_url}/users"
        
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return {"status": "success", "data": response.json()}
            else:
                return {
                    "status": "error", 
                    "code": response.status_code,
                    "message": response.text
                }
        except requests.exceptions.RequestException as e:
            return {"status": "error", "message": str(e)}


class PerplexityClient:
    """Client for Perplexity API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.perplexity.ai"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def enrich_lead_data(self, 
                        company_name: str,
                        person_name: str = None,
                        additional_context: str = None) -> Dict[str, Any]:
        """
        Use Perplexity to enrich lead data with additional context
        
        Args:
            company_name: Name of the company
            person_name: Name of the person (optional)
            additional_context: Additional context for enrichment
            
        Returns:
            Dict containing enriched data
        """
        prompt = f"Research the company '{company_name}'"
        
        if person_name:
            prompt += f" and specifically information about {person_name}"
        
        if additional_context:
            prompt += f". Additional context: {additional_context}"
            
        prompt += ". Provide key business information, recent news, company size, industry, and any relevant contact insights."
        
        payload = {
            "model": "llama-3.1-sonar-small-128k-online",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a business research assistant. Provide concise, factual information about companies and people for sales outreach purposes."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            "max_tokens": 1000,
            "temperature": 0.2
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Perplexity API error: {e}")
            raise


class OpenAIClient:
    """Client for OpenAI API"""
    
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
    
    def generate_email_content(self,
                              lead_data: Dict[str, Any],
                              email_type: str = "outreach",
                              custom_prompt: str = None) -> str:
        """
        Generate email content using OpenAI
        
        Args:
            lead_data: Dictionary containing lead information
            email_type: Type of email ('outreach' or 'followup')
            custom_prompt: Custom prompt for email generation
            
        Returns:
            Generated email content
        """
        if custom_prompt:
            system_prompt = custom_prompt
        else:
            system_prompt = self._get_default_prompt(email_type)
        
        user_content = self._format_lead_data(lead_data)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    def _get_default_prompt(self, email_type: str) -> str:
        """Get default prompt based on email type"""
        if email_type == "followup":
            return """You are a professional sales email writer. Write a follow-up email that:
            - References the previous email briefly
            - Adds value with new insights or information
            - Maintains a professional but friendly tone
            - Includes a clear call to action
            - Keeps it concise (under 150 words)"""
        else:
            return """You are a professional sales email writer. Write an outreach email that:
            - Is personalized and relevant to the recipient
            - Clearly states the value proposition
            - Is professional but conversational
            - Includes a specific call to action
            - Keeps it concise (under 150 words)"""
    
    def _format_lead_data(self, lead_data: Dict[str, Any]) -> str:
        """Format lead data for prompt"""
        formatted = f"Lead Information:\n"
        formatted += f"Name: {lead_data.get('name', 'N/A')}\n"
        formatted += f"Email: {lead_data.get('email', 'N/A')}\n"
        formatted += f"Company: {lead_data.get('company', 'N/A')}\n"
        
        if lead_data.get('enrichment_data'):
            formatted += f"Company Research: {lead_data['enrichment_data']}\n"
        
        if lead_data.get('notes'):
            formatted += f"Additional Notes: {lead_data['notes']}\n"
            
        return formatted 