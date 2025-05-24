"""
Find Leads Function

This function searches for leads using Apollo.io and optionally triggers enrichment.
Enrichment is now handled by the separate enrich_leads function.
"""

import logging
from typing import Dict, List, Optional, Any
from firebase_functions import https_fn
from firebase_admin import firestore

from utils import (
    ApolloClient, 
    LeadProcessor,
    get_firestore_client,
    get_api_keys,
    get_project_settings
)


def find_leads_logic(request_data: Dict[str, Any], auth_uid: str = None) -> Dict[str, Any]:
    """
    Business logic for finding leads - separated from Firebase Functions decorator
    
    Args:
        request_data: Dictionary containing:
        - project_id (str): ID of the project
        - num_leads (int, optional): Number of leads to find (default: 25)
        - search_params (dict, optional): Custom search parameters
        - auto_enrich (bool, optional): Automatically trigger enrichment after finding leads (default: True)
        - save_without_enrichment (bool, optional): Save leads even if enrichment fails (default: True)
        auth_uid: User ID from Firebase Auth (optional)
        
    Returns:
        Dict with success status, message, and lead data
    """
    try:
        # Extract parameters from request
        project_id = request_data.get('project_id')
        num_leads = request_data.get('num_leads', 25)
        search_params = request_data.get('search_params', {})
        auto_enrich = request_data.get('auto_enrich', True)
        save_without_enrichment = request_data.get('save_without_enrichment', True)
        
        if not project_id:
            raise ValueError("project_id is required")
        
        logging.info(f"Finding leads for project: {project_id}")
        
        # Get project details from Firestore
        db = get_firestore_client()
        project_ref = db.collection('projects').document(project_id)
        project_doc = project_ref.get()
        
        if not project_doc.exists:
            raise ValueError(f"Project {project_id} not found")
        
        project_data = project_doc.to_dict()
        
        # Initialize API clients
        api_keys = get_api_keys()
        
        if not api_keys.get('apollo'):
            raise ValueError("Apollo API key not configured")
        
        apollo_client = ApolloClient(api_keys['apollo'])
        lead_processor = LeadProcessor()
        
        # Prepare search parameters based on project
        apollo_search_params = {
            'per_page': min(num_leads, 100),  # Apollo API limit
            'page': 1
        }
        
        # Extract search criteria from project data
        # TODO: Implement more sophisticated parameter extraction
        # For now, use basic logic and merge with custom search_params
        
        # Merge custom search parameters
        apollo_search_params.update(search_params)
        
        logging.info(f"Apollo search parameters: {apollo_search_params}")
        
        # Search for leads using Apollo.io
        apollo_results = apollo_client.search_people(**apollo_search_params)
        
        if not apollo_results.get('people'):
            return {
                'success': True,
                'message': 'No leads found matching search criteria',
                'leads_found': 0,
                'leads_added': 0,
                'enrichment_triggered': False
            }
        
        # Process Apollo results
        processed_leads = lead_processor.process_apollo_results(apollo_results)
        logging.info(f"Processed {len(processed_leads)} leads from Apollo")
        
        # Check for existing leads to avoid duplicates
        existing_leads_query = db.collection('leads').where('projectId', '==', project_id).stream()
        existing_leads = [doc.to_dict() for doc in existing_leads_query]
        
        unique_leads = lead_processor.check_duplicate_leads(processed_leads, existing_leads)
        logging.info(f"Found {len(unique_leads)} unique leads after duplicate check")
        
        # Save leads to Firestore
        saved_count = 0
        batch = db.batch()
        saved_lead_ids = []
        
        for lead in unique_leads:
            try:
                # Prepare lead for database (without enrichment)
                db_lead = lead_processor.prepare_lead_for_database(lead, project_id)
                
                # Set initial enrichment status
                db_lead['enrichmentStatus'] = 'pending' if auto_enrich else None
                db_lead['createdAt'] = firestore.SERVER_TIMESTAMP
                
                # Add to batch
                lead_ref = db.collection('leads').document()
                batch.set(lead_ref, db_lead)
                saved_lead_ids.append(lead_ref.id)
                saved_count += 1
                
            except Exception as e:
                logging.error(f"Failed to prepare lead for database: {e}")
        
        # Commit batch
        enrichment_triggered = False
        if saved_count > 0:
            batch.commit()
            
            # Update project lead count
            current_count = len(existing_leads)
            new_count = current_count + saved_count
            project_ref.update({
                'leadCount': new_count,
                'lastLeadSearch': firestore.SERVER_TIMESTAMP
            })
            
            # Trigger enrichment if requested
            if auto_enrich and api_keys.get('perplexity'):
                try:
                    # Import here to avoid circular imports
                    from enrich_leads import enrich_leads_logic
                    
                    # Create enrichment request data
                    enrichment_data = {
                        'project_id': project_id,
                        'lead_ids': saved_lead_ids,
                        'enrichment_type': 'both'
                    }
                    
                    # Trigger enrichment
                    enrichment_result = enrich_leads_logic(enrichment_data, auth_uid)
                    enrichment_triggered = True
                    
                    logging.info(f"Enrichment triggered: {enrichment_result.get('message', 'Success')}")
                    
                except Exception as e:
                    logging.warning(f"Failed to trigger automatic enrichment: {e}")
                    if not save_without_enrichment:
                        # If we don't want to save without enrichment, rollback
                        # Note: This is complex with Firestore, so we'll just log the error
                        logging.error("Leads saved but enrichment failed - consider manual enrichment")
        
        # Return results
        result = {
            'success': True,
            'message': f'Successfully found and added {saved_count} new leads',
            'leads_found': len(processed_leads),
            'leads_added': saved_count,
            'duplicates_filtered': len(processed_leads) - len(unique_leads),
            'project_id': project_id,
            'enrichment_triggered': enrichment_triggered,
            'saved_lead_ids': saved_lead_ids if auto_enrich else None
        }
        
        logging.info(f"Find leads completed: {result}")
        return result
        
    except Exception as e:
        logging.error(f"Error in find_leads: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        }


@https_fn.on_call()
def find_leads(req: https_fn.CallableRequest) -> Dict[str, Any]:
    """
    Firebase Functions wrapper for finding leads
    
    Args:
        req: Firebase Functions CallableRequest
        
    Returns:
        Dict with success status, message, and lead data
    """
    try:
        auth_uid = req.auth.uid if req.auth else None
        result = find_leads_logic(req.data, auth_uid)
        
        # If there was an error in business logic, convert to HttpsError
        if not result.get('success', True):
            raise https_fn.HttpsError(
                code=https_fn.FunctionsErrorCode.INTERNAL,
                message=result.get('error', 'Unknown error')
            )
        
        return result
        
    except https_fn.HttpsError:
        # Re-raise HttpsError as-is
        raise
    except Exception as e:
        logging.error(f"Error in find_leads Firebase Function: {str(e)}")
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message=f"Failed to find leads: {str(e)}"
        )


# Helper functions for lead discovery

def extract_location_from_description(description: str) -> List[str]:
    """
    Extract location keywords from project area description
    
    TODO: Implement location extraction logic
    - Parse common location formats (city, state, country)
    - Handle abbreviations and variations
    - Return list of location strings for Apollo search
    """
    # Basic implementation - extract common location patterns
    import re
    
    locations = []
    
    # Simple patterns for cities, states, countries
    location_patterns = [
        r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]{2}\b',  # City, State
        r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z][a-z]+\b',  # City, Country
        r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b'  # Two-word locations
    ]
    
    for pattern in location_patterns:
        matches = re.findall(pattern, description)
        locations.extend(matches)
    
    return list(set(locations))  # Remove duplicates


def determine_target_job_titles(project_details: str) -> List[str]:
    """
    Determine appropriate job titles based on project details
    
    TODO: Implement job title determination logic
    - Analyze project details for industry keywords
    - Map to appropriate decision-maker titles
    - Return list of job titles for Apollo search
    """
    # Basic implementation - default decision-maker titles
    default_titles = [
        'CEO', 'CTO', 'Founder', 'Co-Founder',
        'President', 'VP', 'Director',
        'Head of', 'Manager'
    ]
    
    # TODO: Add industry-specific logic
    # For now, return default titles
    return default_titles


def extract_company_criteria(project_details: str) -> Dict[str, Any]:
    """
    Extract company filtering criteria from project details
    
    TODO: Implement company criteria extraction
    - Company size preferences
    - Industry filters
    - Technology stack requirements
    - Return dict with Apollo-compatible filters
    """
    # Basic implementation - return empty criteria
    criteria = {}
    
    # TODO: Add logic to extract:
    # - Company size from keywords like "startup", "enterprise", "SMB"
    # - Industry from project description
    # - Technology stack from project details
    
    return criteria 