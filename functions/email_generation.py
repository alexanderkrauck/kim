"""
Email Generation Function

This function handles generating personalized emails using OpenAI and the configuration system.
"""

import logging
from typing import Dict, List, Optional, Any
from firebase_functions import https_fn, options
from firebase_admin import firestore

# Configure European region
EUROPEAN_REGION = options.SupportedRegion.EUROPE_WEST1

from utils import (
    OpenAIClient,
    get_firestore_client,
    get_api_keys
)
from config_sync import get_config_sync


def generate_emails_logic(request_data: Dict[str, Any], auth_uid: str = None) -> Dict[str, Any]:
    """
    Business logic for generating emails - separated from Firebase Functions decorator
    
    Args:
        request_data: Dictionary containing:
        - project_id (str): ID of the project
        - lead_ids (list): Lead IDs to generate emails for
        - email_type (str): 'outreach' or 'followup'
        - custom_prompt (str, optional): Custom prompt to override config
        auth_uid: User ID from Firebase Auth (optional)
        
    Returns:
        Dict with success status, message, and generated emails
    """
    try:
        # Extract parameters from request
        project_id = request_data.get('project_id')
        lead_ids = request_data.get('lead_ids', [])
        email_type = request_data.get('email_type', 'outreach')
        custom_prompt = request_data.get('custom_prompt')
        
        if not project_id:
            raise ValueError("project_id is required")
        
        if not lead_ids:
            raise ValueError("lead_ids is required")
        
        logging.info(f"Generating {email_type} emails for project: {project_id}")
        
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
        
        # Initialize OpenAI client
        api_keys = get_api_keys()
        
        if not api_keys.get('openai'):
            raise ValueError("OpenAI API key not configured")
        
        openai_client = OpenAIClient(api_keys['openai'])
        
        # Get leads to generate emails for
        leads_to_process = []
        
        for lead_id in lead_ids:
            lead_doc = db.collection('leads').document(lead_id).get()
            if lead_doc.exists:
                lead_data = lead_doc.to_dict()
                lead_data['id'] = lead_id
                
                # Check if lead belongs to the project
                if lead_data.get('projectId') == project_id:
                    leads_to_process.append(lead_data)
                else:
                    logging.warning(f"Lead {lead_id} does not belong to project {project_id}")
            else:
                logging.warning(f"Lead {lead_id} not found")
        
        if not leads_to_process:
            return {
                'success': False,
                'message': 'No valid leads found for email generation',
                'generated_emails': []
            }
        
        logging.info(f"Found {len(leads_to_process)} leads to process")
        
        # Generate emails
        generated_emails = []
        generation_errors = []
        
        for lead in leads_to_process:
            try:
                # Get appropriate prompt
                if custom_prompt:
                    prompt = custom_prompt
                elif email_type == 'followup':
                    prompt = effective_config.email_generation.followup_prompt
                else:
                    prompt = effective_config.email_generation.outreach_prompt
                
                # Add project context to lead data
                enhanced_lead_data = {
                    **lead,
                    'project_details': project_data.get('projectDetails', ''),
                    'project_name': project_data.get('name', '')
                }
                
                # Generate email content
                email_content = openai_client.generate_email_content(
                    lead_data=enhanced_lead_data,
                    email_type=email_type,
                    custom_prompt=prompt
                )
                
                # Generate subject line
                subject = generate_email_subject(lead, email_type, project_data)
                
                # Create email record
                email_record = {
                    'lead_id': lead['id'],
                    'to_email': lead['email'],
                    'to_name': lead.get('name'),
                    'subject': subject,
                    'content': email_content,
                    'email_type': email_type,
                    'generated_at': firestore.SERVER_TIMESTAMP,
                    'project_id': project_id,
                    'status': 'generated'
                }
                
                generated_emails.append(email_record)
                
                logging.info(f"Successfully generated {email_type} email for lead: {lead.get('email', lead.get('name', 'Unknown'))}")
                
            except Exception as e:
                logging.error(f"Failed to generate email for lead {lead.get('email')}: {e}")
                generation_errors.append({
                    'lead_id': lead['id'],
                    'lead_email': lead.get('email'),
                    'error': str(e)
                })
        
        # Return results
        result = {
            'success': True,
            'message': f'Successfully generated {len(generated_emails)} emails',
            'generated_emails': generated_emails,
            'generation_errors': generation_errors,
            'project_id': project_id,
            'email_type': email_type
        }
        
        logging.info(f"Email generation completed: {result['message']}")
        return result
        
    except Exception as e:
        logging.error(f"Error in generate_emails: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        }


@https_fn.on_call(region=EUROPEAN_REGION)
def generate_emails(req: https_fn.CallableRequest) -> Dict[str, Any]:
    """
    Firebase Functions wrapper for generating emails
    
    Args:
        req: Firebase Functions CallableRequest
        
    Returns:
        Dict with success status, message, and generated emails
    """
    try:
        auth_uid = req.auth.uid if req.auth else None
        result = generate_emails_logic(req.data, auth_uid)
        
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
        logging.error(f"Error in generate_emails Firebase Function: {str(e)}")
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message=f"Failed to generate emails: {str(e)}"
        )


def generate_email_subject(lead: Dict, email_type: str, project_data: Dict) -> str:
    """
    Generate appropriate email subject line based on lead and project data
    
    Args:
        lead: Lead data dictionary
        email_type: Type of email ('outreach' or 'followup')
        project_data: Project data dictionary
        
    Returns:
        Generated email subject line
    """
    company = lead.get('company', '')
    name = lead.get('name', '').split()[0] if lead.get('name') else ''
    project_name = project_data.get('name', '')
    
    if email_type == 'followup':
        if company and project_name:
            return f"Following up: {project_name} x {company}"
        elif company:
            return f"Following up on {company} partnership opportunity"
        elif name:
            return f"Following up, {name}"
        else:
            return "Following up on our previous conversation"
    else:
        # Outreach email
        if company and project_name:
            return f"{project_name} x {company} - Partnership opportunity"
        elif company:
            return f"Partnership opportunity for {company}"
        elif name and project_name:
            return f"Hi {name}, {project_name} partnership"
        elif name:
            return f"Hi {name}, quick question"
        else:
            return "Partnership opportunity"


def preview_email_logic(request_data: Dict[str, Any], auth_uid: str = None) -> Dict[str, Any]:
    """
    Preview email generation without saving - for testing prompts
    
    Args:
        request_data: Dictionary containing:
        - project_id (str): ID of the project
        - lead_id (str): Lead ID to preview email for
        - email_type (str): 'outreach' or 'followup'
        - custom_prompt (str, optional): Custom prompt to test
        auth_uid: User ID from Firebase Auth (optional)
        
    Returns:
        Dict with success status and preview email
    """
    try:
        # Extract parameters from request
        project_id = request_data.get('project_id')
        lead_id = request_data.get('lead_id')
        email_type = request_data.get('email_type', 'outreach')
        custom_prompt = request_data.get('custom_prompt')
        
        if not project_id or not lead_id:
            raise ValueError("project_id and lead_id are required")
        
        logging.info(f"Previewing {email_type} email for lead: {lead_id}")
        
        # Get project and lead data
        db = get_firestore_client()
        
        project_doc = db.collection('projects').document(project_id).get()
        if not project_doc.exists:
            raise ValueError(f"Project {project_id} not found")
        project_data = project_doc.to_dict()
        
        lead_doc = db.collection('leads').document(lead_id).get()
        if not lead_doc.exists:
            raise ValueError(f"Lead {lead_id} not found")
        lead_data = lead_doc.to_dict()
        
        if lead_data.get('projectId') != project_id:
            raise ValueError(f"Lead {lead_id} does not belong to project {project_id}")
        
        # Load configuration
        config_sync = get_config_sync()
        project_config = config_sync.load_project_config_from_firebase(project_id)
        global_config = config_sync.load_global_config_from_firebase()
        effective_config = project_config.get_effective_config(global_config)
        
        # Initialize OpenAI client
        api_keys = get_api_keys()
        if not api_keys.get('openai'):
            raise ValueError("OpenAI API key not configured")
        
        openai_client = OpenAIClient(api_keys['openai'])
        
        # Get appropriate prompt
        if custom_prompt:
            prompt = custom_prompt
        elif email_type == 'followup':
            prompt = effective_config.email_generation.followup_prompt
        else:
            prompt = effective_config.email_generation.outreach_prompt
        
        # Add project context to lead data
        enhanced_lead_data = {
            **lead_data,
            'project_details': project_data.get('projectDetails', ''),
            'project_name': project_data.get('name', '')
        }
        
        # Generate email content
        email_content = openai_client.generate_email_content(
            lead_data=enhanced_lead_data,
            email_type=email_type,
            custom_prompt=prompt
        )
        
        # Generate subject line
        subject = generate_email_subject(lead_data, email_type, project_data)
        
        # Return preview
        result = {
            'success': True,
            'preview_email': {
                'to_email': lead_data['email'],
                'to_name': lead_data.get('name'),
                'subject': subject,
                'content': email_content,
                'email_type': email_type,
                'prompt_used': prompt
            },
            'lead_data': {
                'name': lead_data.get('name'),
                'email': lead_data.get('email'),
                'company': lead_data.get('company'),
                'title': lead_data.get('title')
            }
        }
        
        logging.info(f"Email preview generated successfully for lead: {lead_data.get('email')}")
        return result
        
    except Exception as e:
        logging.error(f"Error in preview_email: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        }


@https_fn.on_call(region=EUROPEAN_REGION)
def preview_email(req: https_fn.CallableRequest) -> Dict[str, Any]:
    """
    Firebase Functions wrapper for previewing emails
    
    Args:
        req: Firebase Functions CallableRequest
        
    Returns:
        Dict with success status and preview email
    """
    try:
        auth_uid = req.auth.uid if req.auth else None
        result = preview_email_logic(req.data, auth_uid)
        
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
        logging.error(f"Error in preview_email Firebase Function: {str(e)}")
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message=f"Failed to preview email: {str(e)}"
        ) 