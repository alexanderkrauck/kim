"""
Find Leads Function

This function searches for leads using Apollo.io and optionally triggers enrichment.
Enrichment is now handled by the separate enrich_leads function.
"""

import sys
import time
from typing import Dict, List, Optional, Any
from firebase_functions import https_fn, options
from firebase_admin import firestore

# Configure logging for Firebase Functions
from utils.logging_config import get_logger
logger = get_logger(__file__)

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
    function_name = "find_leads_logic"
    start_time = time.time()
    
    try:
        logger.info(f"Starting find_leads for project: {request_data.get('project_id')}")
        # Extract parameters from request
        project_id = request_data.get('project_id')
        num_leads = request_data.get('num_leads', 25)
        search_params = request_data.get('search_params', {})
        auto_enrich = request_data.get('auto_enrich', True)
        save_without_enrichment = request_data.get('save_without_enrichment', True)
        
        if not project_id:
            raise ValueError("project_id is required")
        
        logger.info(f"Finding leads for project: {project_id}")
        
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
        
        # Process location parameters using project areaDescription and configuration
        location_params = _process_project_location(
            project_data, 
            effective_config.location,
            location_processor,
            api_keys
        )
        apollo_search_params.update(location_params)
        
        # Add job role parameters
        target_roles = effective_config.job_roles.get_all_roles()
        if target_roles:
            apollo_search_params['person_titles'] = target_roles
            logger.info(f"Targeting job roles: {target_roles}")
        
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
        
        # Validate that all required parameters have valid (non-empty) values
        validation_result = _validate_apollo_search_params(apollo_search_params)
        if not validation_result['valid']:
            raise ValueError(validation_result['error'])
        
        logger.info(f"Searching Apollo with params: {apollo_search_params}")
        
        # Search for leads using Apollo.io
        apollo_results = apollo_client.search_people(**apollo_search_params)
        
        logger.info(f"Apollo returned {len(apollo_results.get('people', []))} results")
        
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
        logger.info(f"Processed {len(processed_leads)} leads from Apollo")
        
        # Get existing leads for filtering
        existing_leads_query = db.collection('leads').where('projectId', '==', project_id).stream()
        existing_leads = [doc.to_dict() for doc in existing_leads_query]
        logger.info(f"Found {len(existing_leads)} existing leads in database")
        
        # Get blacklisted emails
        blacklisted_emails = []
        try:
            blacklist_ref = db.collection('blacklist').document('emails')
            blacklist_doc = blacklist_ref.get()
            if blacklist_doc.exists:
                blacklist_data = blacklist_doc.to_dict()
                blacklisted_emails = blacklist_data.get('list', [])
        except Exception as e:
            logger.warning(f"Could not load blacklist: {e}")
        
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
        logger.info(f"Filtered {original_count} leads down to {len(filtered_leads)}")
        
        # Final duplicate check (this is now mainly for cross-project duplicates)
        unique_leads = lead_processor.check_duplicate_leads(filtered_leads, existing_leads)
        logger.info(f"Found {len(unique_leads)} unique leads after filtering")
        
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
                logger.error(f"Failed to prepare lead for database: {e}")
        
        # Commit batch
        enrichment_triggered = False
        if saved_count > 0:
            batch.commit()
            logger.info(f"Saved {saved_count} leads to database")
            
            # Update project lead count
            current_count = len(existing_leads)
            new_count = current_count + saved_count
            project_ref.update({
                'leadCount': new_count,
                'lastLeadSearch': firestore.SERVER_TIMESTAMP
            })
            logger.info(f"Updated project lead count to {new_count}")
            
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
                    
                    logger.info(f"Enrichment triggered: {enrichment_result.get('message', 'Success')}")
                    
                except Exception as e:
                    logger.warning(f"Failed to trigger automatic enrichment: {e}")
                    if not save_without_enrichment:
                        # If we don't want to save without enrichment, rollback
                        # Note: This is complex with Firestore, so we'll just log the error
                        logger.error("Leads saved but enrichment failed - consider manual enrichment")
        
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
        
        logger.info(f"Find leads completed successfully: {saved_count} leads added")
        return result
        
    except Exception as e:
        logger.error(f"Error in find_leads: {str(e)}")
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
        logger.error(f"Error in find_leads Firebase Function: {str(e)}")
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message=f"Failed to find leads: {str(e)}"
        )


def _process_project_location(
    project_data: Dict[str, Any], 
    location_config: Any,
    location_processor: Any,
    api_keys: Dict[str, str]
) -> Dict[str, Any]:
    """
    Process project location using areaDescription and LocationProcessor LLM capabilities
    
    Args:
        project_data: Project data from Firestore
        location_config: LocationConfig from effective config
        location_processor: LocationProcessor instance
        api_keys: Available API keys
        
    Returns:
        Dict with Apollo API location parameters (using clean location strings)
    """
    # Get areaDescription from project data
    area_description = project_data.get('areaDescription', '').strip()
    
    if not area_description:
        logger.warning("Project areaDescription is not set - this is required for proper location targeting")
        raise ValueError("Project areaDescription must be set for location targeting. Please update the project settings.")
    
    logger.info(f"Processing project areaDescription: '{area_description}'")
    
    # Check for OpenAI API key - now mandatory for location processing
    if not api_keys.get('openai'):
        raise ValueError("OpenAI API key is required for location processing. Please configure the OpenAI API key in your settings.")
    
    # Initialize OpenAI client for LLM parsing
    from openai import OpenAI
    location_processor.openai_client = OpenAI(api_key=api_keys['openai'])
    
    try:
        # Use LocationProcessor to parse areaDescription with LLM (now returns location strings)
        clean_locations, parsed_info = location_processor.parse_location_with_llm(area_description)
        
        if clean_locations:
            # Use clean location strings for both person and organization targeting
            location_params = {
                'person_locations': clean_locations,
                'organization_locations': clean_locations
            }
            
            logger.info(f"🎯 LOCATION TARGETING STRATEGY:")
            logger.info(f"📍 Original input: '{area_description}'")
            logger.info(f"🔍 Clean locations: {clean_locations}")
            logger.info(f"📊 Parsing method: {parsed_info.get('method', 'unknown')}")
            logger.info(f"🎚️ Confidence: {parsed_info.get('confidence', 'unknown')}")
            
            if parsed_info.get('ignored_details'):
                logger.info(f"🚫 Ignored broad areas: {parsed_info['ignored_details']}")
            
            # Validate that locations are appropriately narrow
            narrow_validation = _validate_location_narrowness(clean_locations, area_description)
            if narrow_validation['warning']:
                logger.warning(f"⚠️ LOCATION WARNING: {narrow_validation['warning']}")
            
            logger.info(f"✅ Location targeting ready: {len(clean_locations)} specific location(s)")
                
            return location_params
                
        else:
            raise ValueError(
                f"Could not extract valid locations from areaDescription: '{area_description}'. "
                "Please provide a clearer location description (e.g., 'San Francisco Bay Area, California' or 'London, UK')."
            )
            
    except ValueError:
        # Re-raise ValueError as-is (these are user-facing errors)
        raise
    except Exception as e:
        logger.error(f"Error processing location with LLM: {e}")
        raise ValueError(
            f"Failed to process location '{area_description}': {str(e)}. "
            "Please ensure the OpenAI API key is configured and the location description is clear."
        )


def _validate_location_narrowness(locations: List[str], original_input: str) -> Dict[str, Any]:
    """
    Validate that locations are appropriately narrow for effective targeting
    
    Args:
        locations: List of processed location strings
        original_input: Original area description input
        
    Returns:
        Dict with validation results and warnings
    """
    # Broad location indicators (countries, large states, etc.)
    broad_indicators = [
        'united states', 'usa', 'america', 'germany', 'austria', 'switzerland', 'france', 'italy',
        'california', 'texas', 'new york', 'florida', 'illinois', 'pennsylvania',
        'bavaria', 'baden-württemberg', 'north rhine-westphalia',
        'europe', 'north america', 'asia'
    ]
    
    warnings = []
    
    # Check for overly broad locations
    for location in locations:
        location_lower = location.lower().strip()
        for broad_term in broad_indicators:
            if location_lower == broad_term:
                warnings.append(f"'{location}' is too broad - will match entire country/state")
            elif broad_term in location_lower and len(location_lower) <= len(broad_term) + 10:
                # Allow things like "Linz, Austria" but flag standalone broad terms
                if not any(city_indicator in location_lower for city_indicator in [',', 'city', 'district']):
                    warnings.append(f"'{location}' may be too broad for effective targeting")
    
    # Check for mixed specificity levels
    city_count = 0
    country_count = 0
    
    for location in locations:
        location_lower = location.lower()
        # Simple heuristic: if it contains comma, likely city+country; if short and broad, likely country
        if ',' in location or any(indicator in location_lower for indicator in ['city', 'district', 'borough']):
            city_count += 1
        elif any(broad in location_lower for broad in broad_indicators):
            country_count += 1
    
    if city_count > 0 and country_count > 0:
        warnings.append("Mixed specificity levels detected - broad locations may make specific ones ineffective")
    
    # Check for too many variations that might be redundant
    if len(locations) > 5:
        warnings.append(f"Many locations ({len(locations)}) specified - consider reducing for more focused targeting")
    
    warning_text = "; ".join(warnings) if warnings else None
    
    return {
        'valid': len(warnings) == 0,
        'warning': warning_text,
        'city_count': city_count,
        'broad_count': country_count,
        'total_locations': len(locations)
    }


def _validate_apollo_search_params(apollo_search_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate that all Apollo search parameters have valid (non-empty) values
    
    Args:
        apollo_search_params: Dictionary of parameters to be sent to Apollo API
        
    Returns:
        Dict with 'valid' boolean and 'error' message if invalid
    """
    required_params = [
        'person_locations',
        'organization_locations', 
        'person_titles'
    ]
    
    # Check for required location parameters
    person_locations = apollo_search_params.get('person_locations', [])
    organization_locations = apollo_search_params.get('organization_locations', [])
    
    # Location validation - at least one location parameter must be present and non-empty
    if not person_locations and not organization_locations:
        return {
            'valid': False, 
            'error': 'Location parameters are required but not configured. Please ensure project areaDescription is properly set and contains valid location information.'
        }
    
    # Check if location arrays are empty or contain only empty strings
    if person_locations and all(not loc or not loc.strip() for loc in person_locations):
        return {
            'valid': False,
            'error': 'Person locations parameter contains only empty values. Please update project areaDescription with valid location information.'
        }
    
    if organization_locations and all(not loc or not loc.strip() for loc in organization_locations):
        return {
            'valid': False,
            'error': 'Organization locations parameter contains only empty values. Please update project areaDescription with valid location information.'
        }
    
    # Check for job titles
    person_titles = apollo_search_params.get('person_titles', [])
    if not person_titles or all(not title or not title.strip() for title in person_titles):
        return {
            'valid': False,
            'error': 'Job titles are required but not configured. Please ensure target job roles are set in project settings.'
        }
    
    # Check for contact email status (if present, must not be empty)
    contact_email_status = apollo_search_params.get('contact_email_status', [])
    if 'contact_email_status' in apollo_search_params and (
        not contact_email_status or 
        all(not status or not status.strip() for status in contact_email_status)
    ):
        return {
            'valid': False,
            'error': 'Contact email status parameter is present but empty.'
        }
    
    # Check organization size ranges (if present, must not be empty)
    org_size_ranges = apollo_search_params.get('organization_num_employees_ranges', [])
    if 'organization_num_employees_ranges' in apollo_search_params and (
        not org_size_ranges or
        all(not range_val or not str(range_val).strip() for range_val in org_size_ranges)
    ):
        return {
            'valid': False,
            'error': 'Organization size ranges parameter is present but empty.'
        }
    
    # Log validated parameters for debugging
    logger.info(f"✅ APOLLO SEARCH PARAMETERS VALIDATED:")
    logger.info(f"🎯 Person locations: {person_locations}")
    logger.info(f"🏢 Organization locations: {organization_locations}")
    logger.info(f"👔 Person titles: {person_titles}")
    if contact_email_status:
        logger.info(f"📧 Contact email status: {contact_email_status}")
    if org_size_ranges:
        logger.info(f"👥 Organization size ranges: {org_size_ranges}")
    
    # Show location targeting strategy
    total_locations = len(set(person_locations + organization_locations))
    logger.info(f"📊 TARGETING SCOPE: {total_locations} unique location(s), {len(person_titles)} job role(s)")
    logger.info(f"🎚️ Strategy: Narrow location targeting (avoids broad areas for precise results)")
    
    return {'valid': True, 'error': None}


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
    # Updated default titles to match the new default configuration
    default_titles = [
        'Human Resources', 'Office Manager', 'Secretary',
        'Assistant', 'Assistant Manager', 'Manager', 'Social Media'
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