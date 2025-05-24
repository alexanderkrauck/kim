"""
Enrich Leads Function

This function enriches existing leads with Perplexity research and additional data.
Can be used to re-enrich leads or enrich leads that were added without enrichment.
"""

import logging
from typing import Dict, List, Optional, Any
from firebase_functions import https_fn, options

# Configure European region
EUROPEAN_REGION = options.SupportedRegion.EUROPE_WEST1
from firebase_admin import firestore

from utils import (
    PerplexityClient,
    LeadProcessor,
    get_firestore_client,
    get_api_keys,
    get_project_settings
)
from config_sync import get_config_sync


def enrich_leads_logic(request_data: Dict[str, Any], auth_uid: str = None) -> Dict[str, Any]:
    """
    Business logic for enriching leads - separated from Firebase Functions decorator
    
    Args:
        request_data: Dictionary containing:
        - project_id (str): ID of the project
        - lead_ids (list, optional): Specific lead IDs to enrich (if not provided, enriches all unenriched leads)
        - force_re_enrich (bool, optional): Re-enrich leads that already have enrichment data (default: False)
        - enrichment_type (str, optional): Type of enrichment ('company', 'person', 'both') (default: 'both')
        auth_uid: User ID from Firebase Auth (optional)
        
    Returns:
        Dict with success status, message, and enrichment results
    """
    try:
        # Extract parameters from request
        project_id = request_data.get('project_id')
        lead_ids = request_data.get('lead_ids', [])
        force_re_enrich = request_data.get('force_re_enrich', False)
        enrichment_type = request_data.get('enrichment_type', 'both')
        
        if not project_id:
            raise ValueError("project_id is required")
        
        logging.info(f"Enriching leads for project: {project_id}")
        
        # Get project details from Firestore
        db = get_firestore_client()
        project_ref = db.collection('projects').document(project_id)
        project_doc = project_ref.get()
        
        if not project_doc.exists:
            raise ValueError(f"Project {project_id} not found")
        
        project_data = project_doc.to_dict()
        
        # Load project configuration
        config_sync = get_config_sync()
        project_config = config_sync.load_project_config_from_firebase(project_id)
        global_config = config_sync.load_global_config_from_firebase()
        effective_config = project_config.get_effective_config(global_config)
        
        # Check if enrichment is enabled
        if not effective_config.enrichment.enabled:
            return {
                'success': False,
                'message': 'Lead enrichment is disabled for this project',
                'leads_processed': 0,
                'leads_enriched': 0,
                'leads_failed': 0
            }
        
        # Initialize API clients
        api_keys = get_api_keys()
        
        if not api_keys.get('perplexity'):
            raise ValueError("Perplexity API key not configured")
        
        perplexity_client = PerplexityClient(api_keys['perplexity'])
        lead_processor = LeadProcessor()
        
        # Get leads to enrich
        leads_to_enrich = []
        
        if lead_ids:
            # Enrich specific leads
            for lead_id in lead_ids:
                lead_doc = db.collection('leads').document(lead_id).get()
                if lead_doc.exists:
                    lead_data = lead_doc.to_dict()
                    lead_data['id'] = lead_id
                    
                    # Check if lead belongs to the project
                    if lead_data.get('projectId') == project_id:
                        leads_to_enrich.append(lead_data)
                    else:
                        logging.warning(f"Lead {lead_id} does not belong to project {project_id}")
                else:
                    logging.warning(f"Lead {lead_id} not found")
        else:
            # Get all leads for the project
            leads_query = db.collection('leads').where('projectId', '==', project_id)
            
            # Filter by enrichment status if not force re-enriching
            if not force_re_enrich:
                # Only get leads that haven't been enriched yet
                leads_query = leads_query.where('enrichmentStatus', '==', None)
            
            leads_docs = leads_query.stream()
            for doc in leads_docs:
                lead_data = doc.to_dict()
                lead_data['id'] = doc.id
                leads_to_enrich.append(lead_data)
        
        if not leads_to_enrich:
            return {
                'success': True,
                'message': 'No leads found to enrich',
                'leads_processed': 0,
                'leads_enriched': 0,
                'leads_failed': 0
            }
        
        logging.info(f"Found {len(leads_to_enrich)} leads to enrich")
        
        # Enrich leads
        enriched_count = 0
        failed_count = 0
        batch = db.batch()
        
        for lead in leads_to_enrich:
            enrichment_success = False
            enrichment_attempts = 0
            enrichment_error = None
            
            while enrichment_attempts < effective_config.enrichment.max_retries and not enrichment_success:
                enrichment_attempts += 1
                
                try:
                    enrichment_data = {}
                    
                    # Prepare enrichment prompt using configured template
                    company_name = lead.get('company', '')
                    person_name = lead.get('name', '')
                    person_title = lead.get('title', '')
                    
                    if company_name and (enrichment_type in ['company', 'both']):
                        # Format the enrichment prompt
                        formatted_prompt = effective_config.enrichment.prompt_template.format(
                            company=company_name,
                            name=person_name,
                            title=person_title
                        )
                        
                        # Add project context
                        if project_data.get('projectDetails'):
                            formatted_prompt += f"\n\nProject Context: {project_data['projectDetails']}"
                        
                        # Call Perplexity with configured timeout
                        enrichment_response = perplexity_client.enrich_lead_data(
                            company_name=company_name,
                            person_name=person_name if enrichment_type in ['person', 'both'] else None,
                            additional_context=formatted_prompt,
                            timeout=effective_config.enrichment.timeout_seconds
                        )
                        
                        if enrichment_response and enrichment_response.get('choices'):
                            content = enrichment_response['choices'][0]['message']['content']
                            
                            if validate_enrichment_data({'content': content}):
                                enrichment_data['enrichment_content'] = content
                                enrichment_data['enrichment_timestamp'] = firestore.SERVER_TIMESTAMP
                                enrichment_data['enrichment_source'] = 'perplexity'
                                enrichment_data['enrichment_prompt_used'] = formatted_prompt
                                enrichment_success = True
                            else:
                                logging.warning(f"Enrichment data failed validation for lead: {lead.get('email', 'Unknown')}")
                                enrichment_error = "Enrichment data failed quality validation"
                        else:
                            enrichment_error = "No response from Perplexity API"
                    else:
                        enrichment_error = "Missing required data for enrichment (company name)"
                        break  # Don't retry if we don't have the required data
                    
                except Exception as e:
                    enrichment_error = str(e)
                    logging.warning(f"Enrichment attempt {enrichment_attempts} failed for lead {lead.get('email', 'Unknown')}: {e}")
                    
                    if enrichment_attempts < effective_config.enrichment.max_retries:
                        logging.info(f"Retrying enrichment for lead {lead.get('email', 'Unknown')} (attempt {enrichment_attempts + 1})")
            
            # Update lead based on enrichment result
            try:
                if enrichment_success and enrichment_data:
                    update_data = {
                        **enrichment_data,
                        'enrichmentStatus': 'enriched',
                        'enrichmentType': enrichment_type,
                        'lastEnrichmentDate': firestore.SERVER_TIMESTAMP,
                        'enrichmentAttempts': enrichment_attempts
                    }
                    
                    # Add to batch update
                    lead_ref = db.collection('leads').document(lead['id'])
                    batch.update(lead_ref, update_data)
                    enriched_count += 1
                    
                    logging.info(f"Successfully enriched lead: {lead.get('email', lead.get('name', 'Unknown'))}")
                else:
                    # Mark as failed
                    update_data = {
                        'enrichmentStatus': 'failed',
                        'enrichmentError': enrichment_error or 'Unknown error',
                        'lastEnrichmentAttempt': firestore.SERVER_TIMESTAMP,
                        'enrichmentAttempts': enrichment_attempts
                    }
                    lead_ref = db.collection('leads').document(lead['id'])
                    batch.update(lead_ref, update_data)
                    failed_count += 1
                    
                    logging.warning(f"Failed to enrich lead after {enrichment_attempts} attempts: {lead.get('email', lead.get('name', 'Unknown'))}")
                    
            except Exception as batch_error:
                logging.error(f"Failed to update lead status: {batch_error}")
                failed_count += 1
        
        # Commit batch updates
        if enriched_count > 0 or failed_count > 0:
            batch.commit()
            logging.info(f"Committed batch updates for {enriched_count + failed_count} leads")
        
        # Update project enrichment statistics
        try:
            project_ref.update({
                'lastEnrichmentRun': firestore.SERVER_TIMESTAMP,
                'enrichmentStats': {
                    'totalEnriched': firestore.Increment(enriched_count),
                    'totalFailed': firestore.Increment(failed_count)
                }
            })
        except Exception as e:
            logging.warning(f"Failed to update project enrichment stats: {e}")
        
        # Return results
        result = {
            'success': True,
            'message': f'Successfully enriched {enriched_count} leads',
            'leads_processed': len(leads_to_enrich),
            'leads_enriched': enriched_count,
            'leads_failed': failed_count,
            'project_id': project_id,
            'enrichment_type': enrichment_type
        }
        
        logging.info(f"Enrich leads completed: {result}")
        return result
        
    except Exception as e:
        logging.error(f"Error in enrich_leads: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        }


@https_fn.on_call(region=EUROPEAN_REGION)
def enrich_leads(req: https_fn.CallableRequest) -> Dict[str, Any]:
    """
    Firebase Functions wrapper for enriching leads
    
    Args:
        req: Firebase Functions CallableRequest
        
    Returns:
        Dict with success status, message, and enrichment results
    """
    try:
        auth_uid = req.auth.uid if req.auth else None
        result = enrich_leads_logic(req.data, auth_uid)
        
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
        logging.error(f"Error in enrich_leads Firebase Function: {str(e)}")
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message=f"Failed to enrich leads: {str(e)}"
        )


def get_enrichment_status_logic(request_data: Dict[str, Any], auth_uid: str = None) -> Dict[str, Any]:
    """
    Business logic for getting enrichment status - separated from Firebase Functions decorator
    
    Args:
        request_data: Dictionary containing:
        - project_id (str): ID of the project
        - lead_ids (list, optional): Specific lead IDs to check
        auth_uid: User ID from Firebase Auth (optional)
        
    Returns:
        Dict with enrichment status information
    """
    try:
        project_id = request_data.get('project_id')
        lead_ids = request_data.get('lead_ids', [])
        
        if not project_id:
            raise ValueError("project_id is required")
        
        db = get_firestore_client()
        
        if lead_ids:
            # Get status for specific leads
            lead_statuses = []
            for lead_id in lead_ids:
                lead_doc = db.collection('leads').document(lead_id).get()
                if lead_doc.exists:
                    lead_data = lead_doc.to_dict()
                    if lead_data.get('projectId') == project_id:
                        lead_statuses.append({
                            'id': lead_id,
                            'email': lead_data.get('email'),
                            'name': lead_data.get('name'),
                            'enrichmentStatus': lead_data.get('enrichmentStatus'),
                            'enrichmentType': lead_data.get('enrichmentType'),
                            'lastEnrichmentDate': lead_data.get('lastEnrichmentDate'),
                            'enrichmentError': lead_data.get('enrichmentError')
                        })
            
            return {
                'success': True,
                'project_id': project_id,
                'lead_statuses': lead_statuses
            }
        else:
            # Get overall project enrichment status
            leads_query = db.collection('leads').where('projectId', '==', project_id)
            leads_docs = list(leads_query.stream())
            
            total_leads = len(leads_docs)
            enriched_leads = 0
            failed_leads = 0
            pending_leads = 0
            
            for doc in leads_docs:
                lead_data = doc.to_dict()
                status = lead_data.get('enrichmentStatus')
                
                if status == 'enriched':
                    enriched_leads += 1
                elif status == 'failed':
                    failed_leads += 1
                else:
                    pending_leads += 1
            
            return {
                'success': True,
                'project_id': project_id,
                'total_leads': total_leads,
                'enriched_leads': enriched_leads,
                'failed_leads': failed_leads,
                'pending_leads': pending_leads,
                'enrichment_percentage': (enriched_leads / total_leads * 100) if total_leads > 0 else 0
            }
        
    except Exception as e:
        logging.error(f"Error in get_enrichment_status: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        }


@https_fn.on_call(region=EUROPEAN_REGION)
def get_enrichment_status(req: https_fn.CallableRequest) -> Dict[str, Any]:
    """
    Firebase Functions wrapper for getting enrichment status
    
    Args:
        req: Firebase Functions CallableRequest
        
    Returns:
        Dict with enrichment status information
    """
    try:
        auth_uid = req.auth.uid if req.auth else None
        result = get_enrichment_status_logic(req.data, auth_uid)
        
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
        logging.error(f"Error in get_enrichment_status Firebase Function: {str(e)}")
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message=f"Failed to get enrichment status: {str(e)}"
        )


# Helper functions for enrichment

def determine_enrichment_priority(lead: Dict[str, Any]) -> int:
    """
    Determine enrichment priority for a lead based on various factors
    
    Args:
        lead: Lead data dictionary
        
    Returns:
        Priority score (higher = more important to enrich)
    """
    priority = 0
    
    # Higher priority for leads with more complete data
    if lead.get('email'):
        priority += 10
    if lead.get('phone'):
        priority += 5
    if lead.get('company'):
        priority += 10
    if lead.get('title'):
        priority += 5
    
    # Higher priority for decision-maker titles
    title = lead.get('title', '').lower()
    if any(keyword in title for keyword in ['ceo', 'founder', 'president', 'director']):
        priority += 15
    elif any(keyword in title for keyword in ['manager', 'head', 'lead']):
        priority += 10
    
    # Higher priority for larger companies (if company size data available)
    company_size = lead.get('companySize', 0)
    if company_size > 1000:
        priority += 10
    elif company_size > 100:
        priority += 5
    
    return priority


def validate_enrichment_data(enrichment_data: Dict[str, Any]) -> bool:
    """
    Validate that enrichment data meets quality standards
    
    Args:
        enrichment_data: Enrichment data to validate
        
    Returns:
        True if data meets quality standards, False otherwise
    """
    # Check for minimum content length
    content = enrichment_data.get('content', '')
    company_research = enrichment_data.get('company_research', '')
    person_research = enrichment_data.get('person_research', '')
    
    # Use the new unified content format or fall back to legacy format
    text_to_validate = content or (company_research + ' ' + person_research)
    
    if len(text_to_validate) < 100:
        return False
    
    # Check for generic/error responses
    generic_phrases = [
        'i don\'t have information',
        'i cannot find',
        'no information available',
        'unable to provide',
        'insufficient data',
        'i apologize',
        'i\'m sorry',
        'i don\'t know',
        'error occurred',
        'failed to retrieve'
    ]
    
    text_lower = text_to_validate.lower()
    if any(phrase in text_lower for phrase in generic_phrases):
        return False
    
    # Check for very repetitive content (possible API issue)
    words = text_to_validate.split()
    if len(set(words)) < len(words) * 0.3:  # Less than 30% unique words
        return False
    
    # Check for minimum number of sentences (rough validation)
    sentences = text_to_validate.split('.')
    if len(sentences) < 3:
        return False
    
    return True 