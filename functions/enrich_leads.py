"""
Enrich Leads Function

This function enriches existing leads with Perplexity research and additional data.
Can be used to re-enrich leads or enrich leads that were added without enrichment.
"""

import logging
from typing import Dict, List, Optional, Any
from firebase_functions import https_fn
from firebase_admin import firestore

from utils import (
    PerplexityClient,
    LeadProcessor,
    get_firestore_client,
    get_api_keys,
    get_project_settings
)


@https_fn.on_call()
def enrich_leads(req: https_fn.CallableRequest) -> Dict[str, Any]:
    """
    Enrich existing leads with additional research and data
    
    Args:
        req.data should contain:
        - project_id (str): ID of the project
        - lead_ids (list, optional): Specific lead IDs to enrich (if not provided, enriches all unenriched leads)
        - force_re_enrich (bool, optional): Re-enrich leads that already have enrichment data (default: False)
        - enrichment_type (str, optional): Type of enrichment ('company', 'person', 'both') (default: 'both')
        
    Returns:
        Dict with success status, message, and enrichment results
    """
    try:
        # Extract parameters from request
        project_id = req.data.get('project_id')
        lead_ids = req.data.get('lead_ids', [])
        force_re_enrich = req.data.get('force_re_enrich', False)
        enrichment_type = req.data.get('enrichment_type', 'both')
        
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
            try:
                enrichment_data = {}
                
                # Company enrichment
                if enrichment_type in ['company', 'both'] and lead.get('company'):
                    company_research = perplexity_client.enrich_lead_data(
                        company_name=lead['company'],
                        additional_context=f"Research for lead generation project: {project_data.get('projectDetails', '')}"
                    )
                    
                    if company_research and company_research.get('choices'):
                        enrichment_data['company_research'] = company_research['choices'][0]['message']['content']
                        enrichment_data['company_research_timestamp'] = firestore.SERVER_TIMESTAMP
                
                # Person enrichment
                if enrichment_type in ['person', 'both'] and lead.get('name') and lead.get('company'):
                    person_research = perplexity_client.enrich_lead_data(
                        company_name=lead['company'],
                        person_name=lead['name'],
                        additional_context=f"Research about this person for outreach: {project_data.get('projectDetails', '')}"
                    )
                    
                    if person_research and person_research.get('choices'):
                        enrichment_data['person_research'] = person_research['choices'][0]['message']['content']
                        enrichment_data['person_research_timestamp'] = firestore.SERVER_TIMESTAMP
                
                # Update lead with enrichment data
                if enrichment_data:
                    update_data = {
                        **enrichment_data,
                        'enrichmentStatus': 'enriched',
                        'enrichmentType': enrichment_type,
                        'lastEnrichmentDate': firestore.SERVER_TIMESTAMP
                    }
                    
                    # Add to batch update
                    lead_ref = db.collection('leads').document(lead['id'])
                    batch.update(lead_ref, update_data)
                    enriched_count += 1
                    
                    logging.info(f"Enriched lead: {lead.get('email', lead.get('name', 'Unknown'))}")
                else:
                    logging.warning(f"No enrichment data generated for lead: {lead.get('email', lead.get('name', 'Unknown'))}")
                    failed_count += 1
                    
            except Exception as e:
                logging.error(f"Failed to enrich lead {lead.get('email', lead.get('name', 'Unknown'))}: {e}")
                failed_count += 1
                
                # Mark lead as failed enrichment
                try:
                    update_data = {
                        'enrichmentStatus': 'failed',
                        'enrichmentError': str(e),
                        'lastEnrichmentAttempt': firestore.SERVER_TIMESTAMP
                    }
                    lead_ref = db.collection('leads').document(lead['id'])
                    batch.update(lead_ref, update_data)
                except Exception as batch_error:
                    logging.error(f"Failed to update lead with error status: {batch_error}")
        
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
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message=f"Failed to enrich leads: {str(e)}"
        )


@https_fn.on_call()
def get_enrichment_status(req: https_fn.CallableRequest) -> Dict[str, Any]:
    """
    Get enrichment status for a project or specific leads
    
    Args:
        req.data should contain:
        - project_id (str): ID of the project
        - lead_ids (list, optional): Specific lead IDs to check
        
    Returns:
        Dict with enrichment status information
    """
    try:
        project_id = req.data.get('project_id')
        lead_ids = req.data.get('lead_ids', [])
        
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
    company_research = enrichment_data.get('company_research', '')
    person_research = enrichment_data.get('person_research', '')
    
    if len(company_research) < 100 and len(person_research) < 100:
        return False
    
    # Check for generic/error responses
    generic_phrases = [
        'i don\'t have information',
        'i cannot find',
        'no information available',
        'unable to provide',
        'insufficient data'
    ]
    
    combined_text = (company_research + ' ' + person_research).lower()
    if any(phrase in combined_text for phrase in generic_phrases):
        return False
    
    return True 