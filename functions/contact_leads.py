"""
Contact Leads Function

This function handles outreach and follow-up emails for leads in a project.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from firebase_functions import https_fn
from firebase_admin import firestore

from utils import (
    OpenAIClient,
    EmailService,
    get_firestore_client,
    get_api_keys,
    get_project_settings,
    get_project_prompts,
    format_email_content
)


@https_fn.on_call()
def contact_leads(req: https_fn.CallableRequest) -> Dict[str, Any]:
    """
    Send outreach or follow-up emails to leads in a project
    
    Args:
        req.data should contain:
        - project_id (str): ID of the project
        - email_type (str, optional): 'outreach' or 'followup' (default: 'auto')
        - lead_ids (list, optional): Specific lead IDs to contact
        - dry_run (bool, optional): If True, generate emails but don't send
        
    Returns:
        Dict with success status, message, and email statistics
    """
    try:
        # Extract parameters from request
        project_id = req.data.get('project_id')
        email_type = req.data.get('email_type', 'auto')  # 'outreach', 'followup', or 'auto'
        lead_ids = req.data.get('lead_ids', [])
        dry_run = req.data.get('dry_run', False)
        
        if not project_id:
            raise ValueError("project_id is required")
        
        logging.info(f"Contacting leads for project: {project_id}, type: {email_type}")
        
        # TODO: Get project details and settings
        # - Fetch project document
        # - Get project-specific or global settings (timing, prompts)
        # - Get project-specific or global email prompts
        db = get_firestore_client()
        project_ref = db.collection('projects').document(project_id)
        project_doc = project_ref.get()
        
        if not project_doc.exists:
            raise ValueError(f"Project {project_id} not found")
        
        project_data = project_doc.to_dict()
        project_settings = get_project_settings(project_id)
        project_prompts = get_project_prompts(project_id)
        
        # TODO: Initialize API clients
        # - Get API keys from Firebase or environment
        # - Initialize OpenAI client for email generation
        # - Initialize Email service for sending
        api_keys = get_api_keys()
        
        if not api_keys.get('openai'):
            raise ValueError("OpenAI API key not configured")
        
        openai_client = OpenAIClient(api_keys['openai'])
        email_service = EmailService()
        
        # Test email connection
        if not email_service.test_connection():
            raise ValueError("Failed to connect to email service")
        
        # TODO: Determine which leads to contact
        # - If lead_ids provided, use those specific leads
        # - If email_type is 'outreach', find leads with status 'new'
        # - If email_type is 'followup', find leads eligible for follow-up
        # - If email_type is 'auto', determine based on lead status and timing
        
        leads_to_contact = []
        
        if lead_ids:
            # Contact specific leads
            for lead_id in lead_ids:
                lead_doc = db.collection('leads').document(lead_id).get()
                if lead_doc.exists:
                    lead_data = lead_doc.to_dict()
                    lead_data['id'] = lead_id
                    leads_to_contact.append(lead_data)
        else:
            # Find leads based on email type and criteria
            leads_to_contact = find_eligible_leads(
                db, project_id, email_type, project_settings
            )
        
        logging.info(f"Found {len(leads_to_contact)} leads to contact")
        
        if not leads_to_contact:
            return {
                'success': True,
                'message': 'No eligible leads found for contact',
                'emails_sent': 0,
                'emails_failed': 0
            }
        
        # TODO: Check blacklist
        # - Load global blacklist
        # - Load project-specific blacklist
        # - Filter out blacklisted leads
        blacklisted_emails = get_blacklisted_emails(db, project_id)
        
        # Filter out blacklisted leads
        eligible_leads = []
        for lead in leads_to_contact:
            if lead.get('email', '').lower() not in blacklisted_emails:
                eligible_leads.append(lead)
            else:
                logging.info(f"Skipping blacklisted lead: {lead.get('email')}")
        
        logging.info(f"After blacklist filter: {len(eligible_leads)} eligible leads")
        
        # TODO: Generate emails for each lead
        # - Determine email type for each lead (outreach vs followup)
        # - Use OpenAI to generate personalized content
        # - Apply project-specific or global prompts
        # - Format emails with lead data
        
        emails_to_send = []
        generation_errors = []
        
        for lead in eligible_leads:
            try:
                # Determine actual email type for this lead
                actual_email_type = determine_email_type(lead, email_type)
                
                # Get appropriate prompt
                prompt = get_email_prompt(project_prompts, actual_email_type)
                
                # Generate email content
                email_content = openai_client.generate_email_content(
                    lead_data=lead,
                    email_type=actual_email_type,
                    custom_prompt=prompt
                )
                
                # Format email with lead data
                formatted_content = format_email_content(email_content, lead)
                
                # Create email record
                email_record = {
                    'lead_id': lead['id'],
                    'to_email': lead['email'],
                    'to_name': lead.get('name'),
                    'subject': generate_email_subject(lead, actual_email_type),
                    'content': formatted_content,
                    'email_type': actual_email_type,
                    'lead_data': lead
                }
                
                emails_to_send.append(email_record)
                
            except Exception as e:
                logging.error(f"Failed to generate email for lead {lead.get('email')}: {e}")
                generation_errors.append({
                    'lead_email': lead.get('email'),
                    'error': str(e)
                })
        
        logging.info(f"Generated {len(emails_to_send)} emails")
        
        # TODO: Send emails (unless dry_run)
        # - Send emails using EmailService
        # - Track success/failure for each email
        # - Update lead status and lastContacted
        # - Create email records in database
        
        sent_count = 0
        failed_count = 0
        
        if dry_run:
            logging.info("Dry run mode - emails not sent")
            sent_count = len(emails_to_send)
        else:
            # Send emails
            for email_data in emails_to_send:
                try:
                    # Send email
                    success = email_service.send_email(
                        to_email=email_data['to_email'],
                        subject=email_data['subject'],
                        content=email_data['content'],
                        to_name=email_data.get('to_name')
                    )
                    
                    if success:
                        # Update lead status
                        update_lead_after_email(
                            db, email_data['lead_id'], 
                            email_data['email_type'], project_id
                        )
                        
                        # Create email record
                        create_email_record(db, email_data, project_id)
                        
                        sent_count += 1
                        logging.info(f"Email sent successfully to {email_data['to_email']}")
                    else:
                        failed_count += 1
                        logging.error(f"Failed to send email to {email_data['to_email']}")
                        
                except Exception as e:
                    failed_count += 1
                    logging.error(f"Error sending email to {email_data['to_email']}: {e}")
        
        # TODO: Return results
        # - Summary of emails sent/failed
        # - Any generation errors
        # - Processing statistics
        
        result = {
            'success': True,
            'message': f'Email campaign completed: {sent_count} sent, {failed_count} failed',
            'emails_sent': sent_count,
            'emails_failed': failed_count,
            'generation_errors': len(generation_errors),
            'dry_run': dry_run,
            'project_id': project_id
        }
        
        if generation_errors:
            result['generation_errors_details'] = generation_errors
        
        logging.info(f"Contact leads completed: {result}")
        return result
        
    except Exception as e:
        logging.error(f"Error in contact_leads: {str(e)}")
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message=f"Failed to contact leads: {str(e)}"
        )


# TODO: Helper functions to implement:

def find_eligible_leads(db, project_id: str, email_type: str, settings: Dict) -> List[Dict]:
    """
    Find leads eligible for contact based on type and timing
    
    TODO: Implement lead eligibility logic
    - For 'outreach': leads with status 'new'
    - For 'followup': leads with status 'emailed' and past follow-up delay
    - For 'auto': determine based on status and timing
    - Respect max follow-up limits
    - Check timing constraints
    """
    eligible_leads = []
    
    if email_type in ['outreach', 'auto']:
        # Find new leads for outreach
        new_leads_query = db.collection('leads').where('projectId', '==', project_id).where('status', '==', 'new').stream()
        for doc in new_leads_query:
            lead_data = doc.to_dict()
            lead_data['id'] = doc.id
            eligible_leads.append(lead_data)
    
    if email_type in ['followup', 'auto']:
        # Find leads eligible for follow-up
        followup_delay_days = settings.get('followupDelayDays', 7)
        max_followups = settings.get('maxFollowups', 3)
        cutoff_date = datetime.now() - timedelta(days=followup_delay_days)
        
        # Query leads that might need follow-up
        emailed_leads_query = db.collection('leads').where('projectId', '==', project_id).where('status', '==', 'emailed').stream()
        
        for doc in emailed_leads_query:
            lead_data = doc.to_dict()
            lead_data['id'] = doc.id
            
            # Check follow-up eligibility
            followup_count = lead_data.get('followupCount', 0)
            last_contacted = lead_data.get('lastContacted')
            
            if (followup_count < max_followups and 
                last_contacted and 
                last_contacted.replace(tzinfo=None) <= cutoff_date):
                eligible_leads.append(lead_data)
    
    return eligible_leads


def get_blacklisted_emails(db, project_id: str) -> set:
    """
    Get all blacklisted emails (global + project-specific)
    
    TODO: Implement blacklist retrieval
    - Load global blacklist
    - Load project-specific blacklist
    - Return combined set of blacklisted emails
    """
    blacklisted = set()
    
    # Global blacklist
    try:
        global_blacklist_doc = db.collection('blacklist').document('emails').get()
        if global_blacklist_doc.exists:
            global_list = global_blacklist_doc.to_dict().get('list', [])
            blacklisted.update(email.lower() for email in global_list)
    except Exception as e:
        logging.warning(f"Failed to load global blacklist: {e}")
    
    # Project-specific blacklist
    try:
        project_blacklist_doc = db.collection('blacklist').document(f'project_{project_id}').get()
        if project_blacklist_doc.exists:
            project_list = project_blacklist_doc.to_dict().get('list', [])
            blacklisted.update(email.lower() for email in project_list)
    except Exception as e:
        logging.warning(f"Failed to load project blacklist: {e}")
    
    return blacklisted


def determine_email_type(lead: Dict, requested_type: str) -> str:
    """
    Determine actual email type based on lead status and request
    
    TODO: Implement email type determination logic
    - If requested_type is specific, validate against lead status
    - If 'auto', determine based on lead status and history
    - Return 'outreach' or 'followup'
    """
    if requested_type in ['outreach', 'followup']:
        return requested_type
    
    # Auto-determine based on lead status
    status = lead.get('status', 'new')
    followup_count = lead.get('followupCount', 0)
    
    if status == 'new' or followup_count == 0:
        return 'outreach'
    else:
        return 'followup'


def get_email_prompt(prompts: Dict, email_type: str) -> str:
    """
    Get appropriate email prompt based on type
    
    TODO: Implement prompt selection logic
    - Return outreachPrompt for outreach emails
    - Return followupPrompt for follow-up emails
    - Handle missing prompts gracefully
    """
    if email_type == 'followup':
        return prompts.get('followupPrompt', '')
    else:
        return prompts.get('outreachPrompt', '')


def generate_email_subject(lead: Dict, email_type: str) -> str:
    """
    Generate appropriate email subject line
    
    TODO: Implement subject line generation
    - Create personalized subject lines
    - Different patterns for outreach vs follow-up
    - Include company name when available
    """
    company = lead.get('company', '')
    name = lead.get('name', '').split()[0] if lead.get('name') else ''
    
    if email_type == 'followup':
        if company:
            return f"Following up on {company} partnership opportunity"
        else:
            return "Following up on our previous conversation"
    else:
        if company:
            return f"Partnership opportunity for {company}"
        elif name:
            return f"Hi {name}, quick question"
        else:
            return "Quick partnership question"


def update_lead_after_email(db, lead_id: str, email_type: str, project_id: str):
    """
    Update lead status after sending email
    
    TODO: Implement lead status update logic
    - Update status to 'emailed'
    - Set lastContacted to current time
    - Increment followupCount for follow-ups
    - Handle errors gracefully
    """
    try:
        lead_ref = db.collection('leads').document(lead_id)
        
        update_data = {
            'status': 'emailed',
            'lastContacted': datetime.now()
        }
        
        if email_type == 'followup':
            # Get current followup count and increment
            lead_doc = lead_ref.get()
            if lead_doc.exists:
                current_count = lead_doc.to_dict().get('followupCount', 0)
                update_data['followupCount'] = current_count + 1
        
        lead_ref.update(update_data)
        
    except Exception as e:
        logging.error(f"Failed to update lead {lead_id}: {e}")


def create_email_record(db, email_data: Dict, project_id: str):
    """
    Create email record in database
    
    TODO: Implement email record creation
    - Store email details for tracking
    - Link to lead and project
    - Include timestamp and status
    """
    try:
        email_record = {
            'type': email_data['email_type'],
            'subject': email_data['subject'],
            'content': email_data['content'],
            'sentAt': datetime.now(),
            'projectId': project_id,
            'leadId': email_data['lead_id'],
            'toEmail': email_data['to_email'],
            'status': 'sent'
        }
        
        db.collection('emails').add(email_record)
        
    except Exception as e:
        logging.error(f"Failed to create email record: {e}") 