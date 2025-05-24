"""
Data processing utilities for lead management
"""

import re
from typing import Dict, List, Optional, Any
from datetime import datetime
from config_model import LeadFilterConfig
from utils.logging_config import get_logger

logger = get_logger(__file__)


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
                    logger.warning(f"Invalid lead data: {validation['errors']}")
            
        except Exception as e:
            logger.error(f"Error processing Apollo results: {e}")
        
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
            logger.error(f"Error enriching lead with Perplexity data: {e}")
        
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
                logger.info(f"Duplicate lead found: {lead.get('email')}")
        
        return unique_leads
    
    def apply_lead_filters(self, 
                          leads: List[Dict[str, Any]], 
                          filter_config: LeadFilterConfig,
                          existing_leads: List[Dict[str, Any]] = None,
                          blacklisted_emails: List[str] = None) -> List[Dict[str, Any]]:
        """
        Apply comprehensive lead filtering based on configuration
        
        Args:
            leads: List of leads to filter
            filter_config: Lead filter configuration
            existing_leads: Existing leads for duplicate checking
            blacklisted_emails: List of blacklisted email addresses
            
        Returns:
            List of filtered leads
        """
        if not leads:
            return []
        
        filtered_leads = []
        company_tracker = {}
        
        existing_leads = existing_leads or []
        blacklisted_emails = blacklisted_emails or []
        blacklisted_set = {email.lower() for email in blacklisted_emails}
        
        for lead in leads:
            # Filter by email requirement
            if filter_config.require_email and not lead.get('email'):
                logger.debug(f"Filtered lead without email: {lead.get('name', 'Unknown')}")
                continue
            
            # Filter blacklisted emails
            if filter_config.exclude_blacklisted and lead.get('email'):
                if lead['email'].lower() in blacklisted_set:
                    logger.debug(f"Filtered blacklisted email: {lead['email']}")
                    continue
            
            # Filter one person per company
            if filter_config.one_person_per_company and lead.get('company'):
                company_name = self._normalize_company_name(lead['company'])
                
                # Check if we already have someone from this company
                if company_name in company_tracker:
                    logger.debug(f"Filtered duplicate company: {lead['company']}")
                    continue
                
                # Check against existing leads
                if any(self._normalize_company_name(existing_lead.get('company', '')) == company_name 
                       for existing_lead in existing_leads):
                    logger.debug(f"Filtered company already in existing leads: {lead['company']}")
                    continue
                
                company_tracker[company_name] = True
            
            # Filter by company size (if data is available)
            if self._should_filter_by_company_size(lead, filter_config):
                logger.debug(f"Filtered by company size: {lead.get('company', 'Unknown')}")
                continue
            
            # Add additional quality filters
            if not self._passes_quality_filters(lead):
                logger.debug(f"Filtered by quality checks: {lead.get('email', 'Unknown')}")
                continue
            
            filtered_leads.append(lead)
        
        logger.info(f"Lead filtering results: {len(leads)} -> {len(filtered_leads)} after applying filters")
        return filtered_leads
    
    def _normalize_company_name(self, company_name: str) -> str:
        """
        Normalize company name for comparison
        
        Args:
            company_name: Raw company name
            
        Returns:
            Normalized company name
        """
        if not company_name:
            return ""
        
        # Convert to lowercase and strip whitespace
        normalized = company_name.lower().strip()
        
        # Remove common suffixes and prefixes
        suffixes = ['inc', 'corp', 'corporation', 'llc', 'ltd', 'limited', 'co', 'company']
        prefixes = ['the ']
        
        for prefix in prefixes:
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix):]
        
        for suffix in suffixes:
            patterns = [f' {suffix}', f' {suffix}.', f', {suffix}', f', {suffix}.']
            for pattern in patterns:
                if normalized.endswith(pattern):
                    normalized = normalized[:-len(pattern)]
                    break
        
        return normalized.strip()
    
    def _should_filter_by_company_size(self, lead: Dict[str, Any], filter_config: LeadFilterConfig) -> bool:
        """
        Check if lead should be filtered based on company size
        
        Args:
            lead: Lead data
            filter_config: Filter configuration
            
        Returns:
            True if lead should be filtered out
        """
        # If no size filters configured, don't filter
        if not filter_config.min_company_size and not filter_config.max_company_size:
            return False
        
        # Try to extract company size from raw Apollo data
        company_size = None
        raw_data = lead.get('raw_data', {})
        
        if raw_data and isinstance(raw_data, dict):
            organization = raw_data.get('organization', {})
            if organization:
                # Apollo provides estimated employee count
                company_size = organization.get('estimated_num_employees')
                
                # Also check for employee range
                if not company_size:
                    emp_ranges = organization.get('num_employees_ranges', [])
                    if emp_ranges:
                        # Parse range like "1-10" or "11-50"
                        range_str = emp_ranges[0]
                        if '-' in range_str:
                            try:
                                min_emp = int(range_str.split('-')[0])
                                company_size = min_emp
                            except (ValueError, IndexError):
                                pass
        
        # If we couldn't determine size, don't filter
        if company_size is None:
            return False
        
        # Apply size filters
        if filter_config.min_company_size and company_size < filter_config.min_company_size:
            return True
        
        if filter_config.max_company_size and company_size > filter_config.max_company_size:
            return True
        
        return False
    
    def _passes_quality_filters(self, lead: Dict[str, Any]) -> bool:
        """
        Apply basic quality filters to leads
        
        Args:
            lead: Lead data
            
        Returns:
            True if lead passes quality checks
        """
        # Filter out generic/role emails
        email = lead.get('email', '').lower()
        generic_patterns = [
            'info@', 'contact@', 'support@', 'help@', 'sales@',
            'admin@', 'webmaster@', 'postmaster@', 'noreply@',
            'no-reply@', 'donotreply@', 'marketing@'
        ]
        
        if any(email.startswith(pattern) for pattern in generic_patterns):
            return False
        
        # Filter out temporary/disposable email domains
        disposable_domains = [
            '10minutemail.com', 'guerrillamail.com', 'tempmail.org',
            'mailinator.com', 'dispostable.com'
        ]
        
        email_domain = email.split('@')[-1] if '@' in email else ''
        if email_domain in disposable_domains:
            return False
        
        # Require minimum name length (if name is provided)
        name = lead.get('name', '').strip()
        if name and len(name) < 2:
            return False
        
        # Filter out obviously invalid names
        if name:
            # Check for common test names
            test_names = ['test', 'demo', 'sample', 'example', 'admin', 'user']
            if name.lower() in test_names:
                return False
            
            # Check for names that are too generic
            if len(name.split()) == 1 and len(name) < 3:
                return False
        
        return True
    
    def get_filtering_stats(self, 
                           original_count: int, 
                           filtered_count: int,
                           filter_config: LeadFilterConfig) -> Dict[str, Any]:
        """
        Generate filtering statistics
        
        Args:
            original_count: Number of leads before filtering
            filtered_count: Number of leads after filtering
            filter_config: Filter configuration used
            
        Returns:
            Dictionary with filtering statistics
        """
        filtered_out = original_count - filtered_count
        filter_rate = (filtered_out / original_count * 100) if original_count > 0 else 0
        
        return {
            'original_count': original_count,
            'filtered_count': filtered_count,
            'filtered_out': filtered_out,
            'filter_rate_percent': round(filter_rate, 2),
            'filters_applied': {
                'require_email': filter_config.require_email,
                'exclude_blacklisted': filter_config.exclude_blacklisted,
                'one_person_per_company': filter_config.one_person_per_company,
                'company_size_filter': bool(filter_config.min_company_size or filter_config.max_company_size)
            }
        } 