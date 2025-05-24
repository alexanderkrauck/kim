"""
Find Leads Function

This function searches for leads using Apollo.io and optionally triggers enrichment.
Enrichment is now handled by the separate enrich_leads function.
"""

import logging
from typing import Dict, List, Optional, Any
from firebase_functions import https_fn, options
from firebase_admin import firestore

# Configure European region
EUROPEAN_REGION = options.SupportedRegion.EUROPE_WEST1

from utils import (
    ApolloClient, 
    LeadProcessor,
    get_firestore_client,
    get_api_keys,
    get_project_settings
)
from config_sync import get_config_sync
from location_processor import location_processor


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
        
        # Load project configuration
        config_sync = get_config_sync()
        project_config = config_sync.load_project_config_from_firebase(project_id)
        global_config = config_sync.load_global_config_from_firebase()
        effective_config = project_config.get_effective_config(global_config)
        
        # Prepare search parameters based on project configuration
        apollo_search_params = {
            'per_page': min(num_leads, 100),  # Apollo API limit
            'page': 1
        }
        
        # Add location parameters
        location_params = location_processor.get_apollo_location_params(effective_config.location)
        apollo_search_params.update(location_params)
        
        # Add job role parameters
        target_roles = effective_config.job_roles.get_all_roles()
        if target_roles:
            apollo_search_params['person_titles'] = target_roles
            logging.info(f"Targeting job roles: {target_roles}")
        
        # Add lead filtering parameters
        if effective_config.lead_filter.min_company_size:
            apollo_search_params['organization_num_employees_ranges'] = [f"{effective_config.lead_filter.min_company_size}+"]
        
        if effective_config.lead_filter.max_company_size:
            if 'organization_num_employees_ranges' not in apollo_search_params:
                apollo_search_params['organization_num_employees_ranges'] = []
            # Apollo uses specific ranges, we'll simplify for now
            apollo_search_params['organization_num_employees_ranges'].append(f"1-{effective_config.lead_filter.max_company_size}")
        
        # Merge custom search parameters (these can override config)
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
        
        # Get existing leads for filtering
        existing_leads_query = db.collection('leads').where('projectId', '==', project_id).stream()
        existing_leads = [doc.to_dict() for doc in existing_leads_query]
        
        # Get blacklisted emails
        blacklisted_emails = []
        try:
            blacklist_ref = db.collection('blacklist').document('emails')
            blacklist_doc = blacklist_ref.get()
            if blacklist_doc.exists:
                blacklist_data = blacklist_doc.to_dict()
                blacklisted_emails = blacklist_data.get('list', [])
        except Exception as e:
            logging.warning(f"Could not load blacklist: {e}")
        
        # Apply comprehensive lead filtering
        original_count = len(processed_leads)
        filtered_leads = lead_processor.apply_lead_filters(
            processed_leads,
            effective_config.lead_filter,
            existing_leads,
            blacklisted_emails
        )
        
        # Get filtering statistics
        filter_stats = lead_processor.get_filtering_stats(
            original_count,
            len(filtered_leads),
            effective_config.lead_filter
        )
        logging.info(f"Lead filtering stats: {filter_stats}")
        
        # Final duplicate check (this is now mainly for cross-project duplicates)
        unique_leads = lead_processor.check_duplicate_leads(filtered_leads, existing_leads)
        logging.info(f"Found {len(unique_leads)} unique leads after all filtering")
        
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
            'leads_filtered': len(filtered_leads),
            'leads_added': saved_count,
            'duplicates_filtered': len(filtered_leads) - len(unique_leads),
            'total_filtered_out': len(processed_leads) - len(unique_leads),
            'project_id': project_id,
            'enrichment_triggered': enrichment_triggered,
            'saved_lead_ids': saved_lead_ids if auto_enrich else None,
            'filtering_stats': filter_stats
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


@https_fn.on_call(region=EUROPEAN_REGION)
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
    
    Parses common location formats and returns location strings for Apollo search.
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
    
    Analyzes project details and returns appropriate decision-maker titles.
    """
    # Basic implementation - default decision-maker titles
    default_titles = [
        'CEO', 'CTO', 'Founder', 'Co-Founder',
        'President', 'VP', 'Director',
        'Head of', 'Manager'
    ]
    
    # Could be enhanced with industry-specific logic based on project details
    return default_titles


def extract_company_criteria(project_details: str) -> Dict[str, Any]:
    """
    Extract company filtering criteria from project details
    
    Returns dict with Apollo-compatible filters based on project details.
    """
    # Basic implementation - return empty criteria
    # Could be enhanced to extract company size, industry, and tech stack from project details
    criteria = {}
    
    return criteria 