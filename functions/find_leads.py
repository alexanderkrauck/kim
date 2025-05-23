"""
Find Leads Function

This function searches for leads using Apollo.io and enriches them with Perplexity research.
"""

import logging
from typing import Dict, List, Optional, Any
from firebase_functions import https_fn
from firebase_admin import firestore

from utils import (
    ApolloClient, 
    PerplexityClient, 
    LeadProcessor,
    get_firestore_client,
    get_api_keys,
    get_project_settings
)


@https_fn.on_call()
def find_leads(req: https_fn.CallableRequest) -> Dict[str, Any]:
    """
    Find and enrich leads for a specific project
    
    Args:
        req.data should contain:
        - project_id (str): ID of the project
        - num_leads (int, optional): Number of leads to find (default: 25)
        - search_params (dict, optional): Custom search parameters
        
    Returns:
        Dict with success status, message, and lead data
    """
    try:
        # Extract parameters from request
        project_id = req.data.get('project_id')
        num_leads = req.data.get('num_leads', 25)
        search_params = req.data.get('search_params', {})
        
        if not project_id:
            raise ValueError("project_id is required")
        
        logging.info(f"Finding leads for project: {project_id}")
        
        # TODO: Get project details from Firestore
        # - Fetch project document to get area description and project details
        # - Use project details to inform search parameters
        db = get_firestore_client()
        project_ref = db.collection('projects').document(project_id)
        project_doc = project_ref.get()
        
        if not project_doc.exists:
            raise ValueError(f"Project {project_id} not found")
        
        project_data = project_doc.to_dict()
        
        # TODO: Initialize API clients
        # - Get API keys from Firebase or environment
        # - Initialize Apollo and Perplexity clients
        api_keys = get_api_keys()
        
        if not api_keys.get('apollo'):
            raise ValueError("Apollo API key not configured")
        
        if not api_keys.get('perplexity'):
            raise ValueError("Perplexity API key not configured")
        
        apollo_client = ApolloClient(api_keys['apollo'])
        perplexity_client = PerplexityClient(api_keys['perplexity'])
        lead_processor = LeadProcessor()
        
        # TODO: Prepare search parameters based on project
        # - Extract location/area from project.areaDescription
        # - Determine target job titles based on project type
        # - Set company size filters if specified
        # - Merge with any custom search_params provided
        
        # Default search parameters (to be enhanced based on project)
        apollo_search_params = {
            'per_page': min(num_leads, 100),  # Apollo API limit
            'page': 1
        }
        
        # TODO: Extract search criteria from project data
        # Example logic (to be implemented):
        # - Parse areaDescription for location keywords
        # - Analyze projectDetails for industry/company type hints
        # - Set appropriate job titles based on project type
        
        # Merge custom search parameters
        apollo_search_params.update(search_params)
        
        logging.info(f"Apollo search parameters: {apollo_search_params}")
        
        # TODO: Search for leads using Apollo.io
        # - Execute search with prepared parameters
        # - Handle pagination if needed
        # - Process and validate results
        apollo_results = apollo_client.search_people(**apollo_search_params)
        
        if not apollo_results.get('people'):
            return {
                'success': True,
                'message': 'No leads found matching search criteria',
                'leads_found': 0,
                'leads_added': 0
            }
        
        # Process Apollo results
        processed_leads = lead_processor.process_apollo_results(apollo_results)
        logging.info(f"Processed {len(processed_leads)} leads from Apollo")
        
        # TODO: Check for existing leads to avoid duplicates
        # - Query existing leads in the project
        # - Filter out duplicates based on email
        existing_leads_query = db.collection('leads').where('projectId', '==', project_id).stream()
        existing_leads = [doc.to_dict() for doc in existing_leads_query]
        
        unique_leads = lead_processor.check_duplicate_leads(processed_leads, existing_leads)
        logging.info(f"Found {len(unique_leads)} unique leads after duplicate check")
        
        # TODO: Enrich leads with Perplexity research
        # - For each lead, research the company
        # - Extract key insights and recent news
        # - Add enrichment data to lead record
        enriched_leads = []
        
        for lead in unique_leads:
            try:
                if lead.get('company'):
                    # Research the company
                    perplexity_response = perplexity_client.enrich_lead_data(
                        company_name=lead['company'],
                        person_name=lead.get('name'),
                        additional_context=project_data.get('projectDetails', '')
                    )
                    
                    # Enrich lead with research data
                    enriched_lead = lead_processor.enrich_lead_with_perplexity(
                        lead, perplexity_response
                    )
                    enriched_leads.append(enriched_lead)
                else:
                    # No company info, add lead without enrichment
                    enriched_leads.append(lead)
                    
            except Exception as e:
                logging.warning(f"Failed to enrich lead {lead.get('email')}: {e}")
                # Add lead without enrichment
                enriched_leads.append(lead)
        
        # TODO: Save leads to Firestore
        # - Prepare lead documents for database
        # - Batch write to Firestore
        # - Update project lead count
        saved_count = 0
        batch = db.batch()
        
        for lead in enriched_leads:
            try:
                # Prepare lead for database
                db_lead = lead_processor.prepare_lead_for_database(lead, project_id)
                
                # Add to batch
                lead_ref = db.collection('leads').document()
                batch.set(lead_ref, db_lead)
                saved_count += 1
                
            except Exception as e:
                logging.error(f"Failed to prepare lead for database: {e}")
        
        # Commit batch
        if saved_count > 0:
            batch.commit()
            
            # Update project lead count
            current_count = len(existing_leads)
            new_count = current_count + saved_count
            project_ref.update({'leadCount': new_count})
        
        # TODO: Return results
        # - Summary of leads found and added
        # - Any errors or warnings
        # - Processing statistics
        
        result = {
            'success': True,
            'message': f'Successfully found and added {saved_count} new leads',
            'leads_found': len(processed_leads),
            'leads_added': saved_count,
            'duplicates_filtered': len(processed_leads) - len(unique_leads),
            'project_id': project_id
        }
        
        logging.info(f"Find leads completed: {result}")
        return result
        
    except Exception as e:
        logging.error(f"Error in find_leads: {str(e)}")
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message=f"Failed to find leads: {str(e)}"
        )


# TODO: Additional helper functions to implement:

def extract_location_from_description(description: str) -> List[str]:
    """
    Extract location keywords from project area description
    
    TODO: Implement location extraction logic
    - Parse common location formats (city, state, country)
    - Handle abbreviations and variations
    - Return list of location strings for Apollo search
    """
    pass


def determine_target_job_titles(project_details: str) -> List[str]:
    """
    Determine appropriate job titles based on project details
    
    TODO: Implement job title determination logic
    - Analyze project details for industry keywords
    - Map to appropriate decision-maker titles
    - Return list of job titles for Apollo search
    """
    pass


def extract_company_criteria(project_details: str) -> Dict[str, Any]:
    """
    Extract company filtering criteria from project details
    
    TODO: Implement company criteria extraction
    - Company size preferences
    - Industry filters
    - Technology stack requirements
    - Return dict with Apollo-compatible filters
    """
    pass 