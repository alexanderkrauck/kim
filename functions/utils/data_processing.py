"""
Data processing utilities for lead management
"""

import re
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime


class DataValidator:
    """Utility class for data validation"""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Validate email address format
        
        Args:
            email: Email address to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not email:
            return False
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email.strip()))
    
    @staticmethod
    def validate_lead_data(lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and clean lead data
        
        Args:
            lead_data: Raw lead data
            
        Returns:
            Dictionary with 'valid' boolean and 'errors' list
        """
        errors = []
        
        # Required fields
        if not lead_data.get('email'):
            errors.append("Email is required")
        elif not DataValidator.validate_email(lead_data['email']):
            errors.append("Invalid email format")
        
        # Optional field validation
        if lead_data.get('name') and len(lead_data['name'].strip()) < 2:
            errors.append("Name must be at least 2 characters")
        
        if lead_data.get('company') and len(lead_data['company'].strip()) < 2:
            errors.append("Company name must be at least 2 characters")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    @staticmethod
    def clean_lead_data(lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean and normalize lead data
        
        Args:
            lead_data: Raw lead data
            
        Returns:
            Cleaned lead data
        """
        cleaned = {}
        
        # Clean email
        if lead_data.get('email'):
            cleaned['email'] = lead_data['email'].strip().lower()
        
        # Clean name
        if lead_data.get('name'):
            cleaned['name'] = ' '.join(lead_data['name'].strip().split())
        
        # Clean company
        if lead_data.get('company'):
            cleaned['company'] = lead_data['company'].strip()
        
        # Copy other fields
        for key in ['source', 'notes', 'projectId']:
            if lead_data.get(key):
                cleaned[key] = lead_data[key]
        
        return cleaned


class LeadProcessor:
    """Utility class for processing lead data"""
    
    def __init__(self):
        self.validator = DataValidator()
    
    def process_apollo_results(self, apollo_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Process Apollo.io search results into lead format
        
        Args:
            apollo_response: Response from Apollo.io API
            
        Returns:
            List of processed lead dictionaries
        """
        leads = []
        
        try:
            people = apollo_response.get('people', [])
            
            for person in people:
                lead_data = {
                    'email': person.get('email'),
                    'name': person.get('name'),
                    'company': person.get('organization', {}).get('name') if person.get('organization') else None,
                    'source': 'Apollo.io',
                    'apollo_id': person.get('id'),
                    'title': person.get('title'),
                    'linkedin_url': person.get('linkedin_url'),
                    'raw_data': person  # Store raw data for reference
                }
                
                # Validate and clean
                validation = self.validator.validate_lead_data(lead_data)
                if validation['valid']:
                    cleaned_lead = self.validator.clean_lead_data(lead_data)
                    leads.append(cleaned_lead)
                else:
                    logging.warning(f"Invalid lead data: {validation['errors']}")
            
        except Exception as e:
            logging.error(f"Error processing Apollo results: {e}")
        
        return leads
    
    def enrich_lead_with_perplexity(self, 
                                   lead_data: Dict[str, Any], 
                                   perplexity_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich lead data with Perplexity research
        
        Args:
            lead_data: Original lead data
            perplexity_response: Response from Perplexity API
            
        Returns:
            Enriched lead data
        """
        try:
            enriched_lead = lead_data.copy()
            
            # Extract content from Perplexity response
            if perplexity_response.get('choices'):
                content = perplexity_response['choices'][0].get('message', {}).get('content', '')
                
                enriched_lead['enrichment_data'] = content
                enriched_lead['enriched_at'] = datetime.now().isoformat()
                
                # Try to extract structured data from the content
                enriched_lead['company_insights'] = self._extract_company_insights(content)
            
        except Exception as e:
            logging.error(f"Error enriching lead with Perplexity data: {e}")
        
        return enriched_lead
    
    def _extract_company_insights(self, content: str) -> Dict[str, Any]:
        """
        Extract structured insights from Perplexity content
        
        Args:
            content: Text content from Perplexity
            
        Returns:
            Dictionary with extracted insights
        """
        insights = {}
        
        # Simple keyword extraction (can be enhanced with NLP)
        content_lower = content.lower()
        
        # Company size indicators
        if any(word in content_lower for word in ['startup', 'small', 'early-stage']):
            insights['company_size'] = 'small'
        elif any(word in content_lower for word in ['enterprise', 'large', 'fortune']):
            insights['company_size'] = 'large'
        elif any(word in content_lower for word in ['medium', 'mid-size', 'growing']):
            insights['company_size'] = 'medium'
        
        # Industry indicators
        industries = ['technology', 'healthcare', 'finance', 'education', 'retail', 'manufacturing']
        for industry in industries:
            if industry in content_lower:
                insights['industry'] = industry
                break
        
        # Recent news indicators
        if any(word in content_lower for word in ['funding', 'investment', 'raised']):
            insights['recent_funding'] = True
        
        if any(word in content_lower for word in ['acquisition', 'acquired', 'merger']):
            insights['recent_acquisition'] = True
        
        return insights
    
    def prepare_lead_for_database(self, 
                                 lead_data: Dict[str, Any], 
                                 project_id: str) -> Dict[str, Any]:
        """
        Prepare lead data for database insertion
        
        Args:
            lead_data: Processed lead data
            project_id: ID of the project
            
        Returns:
            Database-ready lead document
        """
        db_lead = {
            'email': lead_data['email'],
            'name': lead_data.get('name', ''),
            'company': lead_data.get('company', ''),
            'status': 'new',
            'lastContacted': None,
            'followupCount': 0,
            'createdAt': datetime.now(),
            'projectId': project_id,
            'interactionSummary': '',
            'emailChain': [],
            'source': lead_data.get('source', 'API'),
            'notes': lead_data.get('notes', '')
        }
        
        # Add enrichment data if available
        if lead_data.get('enrichment_data'):
            db_lead['enrichmentData'] = lead_data['enrichment_data']
            db_lead['enrichedAt'] = lead_data.get('enriched_at')
        
        # Add company insights if available
        if lead_data.get('company_insights'):
            db_lead['companyInsights'] = lead_data['company_insights']
        
        # Add Apollo-specific data if available
        if lead_data.get('apollo_id'):
            db_lead['apolloId'] = lead_data['apollo_id']
        
        if lead_data.get('title'):
            db_lead['title'] = lead_data['title']
        
        if lead_data.get('linkedin_url'):
            db_lead['linkedinUrl'] = lead_data['linkedin_url']
        
        return db_lead
    
    def check_duplicate_leads(self, 
                             new_leads: List[Dict[str, Any]], 
                             existing_leads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter out duplicate leads based on email
        
        Args:
            new_leads: List of new leads to check
            existing_leads: List of existing leads in the project
            
        Returns:
            List of unique new leads
        """
        existing_emails = {lead.get('email', '').lower() for lead in existing_leads}
        
        unique_leads = []
        for lead in new_leads:
            if lead.get('email', '').lower() not in existing_emails:
                unique_leads.append(lead)
            else:
                logging.info(f"Duplicate lead found: {lead.get('email')}")
        
        return unique_leads 