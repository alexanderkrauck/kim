"""
API client utilities for external services
"""

import os
import requests
import logging
from typing import Dict, List, Optional, Any
from openai import OpenAI


class ApolloClient:
    """Client for Apollo.io API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.apollo.io/v1"
        self.headers = {
            "Cache-Control": "no-cache",
            "Content-Type": "application/json",
            "X-Api-Key": api_key
        }
    
    def search_people(self, 
                     company_domains: List[str] = None,
                     job_titles: List[str] = None,
                     locations: List[str] = None,
                     page: int = 1,
                     per_page: int = 25) -> Dict[str, Any]:
        """
        Search for people using Apollo.io API
        
        Args:
            company_domains: List of company domains to search
            job_titles: List of job titles to search for
            locations: List of locations to search in
            page: Page number for pagination
            per_page: Number of results per page
            
        Returns:
            Dict containing search results
        """
        url = f"{self.base_url}/mixed_people/search"
        
        payload = {
            "page": page,
            "per_page": per_page
        }
        
        if company_domains:
            payload["organization_domains"] = company_domains
        if job_titles:
            payload["person_titles"] = job_titles
        if locations:
            payload["person_locations"] = locations
            
        try:
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Apollo API error: {e}")
            raise
    
    def get_person_details(self, person_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific person"""
        url = f"{self.base_url}/people/{person_id}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Apollo API error getting person details: {e}")
            raise


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
            logging.error(f"Perplexity API error: {e}")
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
            logging.error(f"OpenAI API error: {e}")
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