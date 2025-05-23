# Welcome to Cloud Functions for Firebase for Python!
# To get started, simply uncomment the below code or create your own.
# Deploy with `firebase deploy`

from firebase_functions import https_fn, firestore_fn
from firebase_admin import initialize_app, firestore
from datetime import datetime, timedelta
import logging

# Import new functions
from find_leads import find_leads
from contact_leads import contact_leads

# Initialize Firebase Admin
initialize_app()

# Export the new functions
__all__ = ['find_leads', 'contact_leads', 'trigger_followup', 'process_all_followups', 'on_lead_created', 'health_check']

@https_fn.on_call()
def trigger_followup(req: https_fn.CallableRequest) -> dict:
    """
    Manually trigger a follow-up for a specific lead
    """
    try:
        # Get the lead ID from the request
        lead_id = req.data.get('leadId')
        if not lead_id:
            raise ValueError("Lead ID is required")
        
        db = firestore.client()
        
        # Get the lead document
        lead_ref = db.collection('leads').document(lead_id)
        lead_doc = lead_ref.get()
        
        if not lead_doc.exists:
            raise ValueError("Lead not found")
        
        lead_data = lead_doc.to_dict()
        
        # Check if lead is eligible for follow-up
        if lead_data.get('status') == 'blacklisted':
            raise ValueError("Cannot send follow-up to blacklisted lead")
        
        if lead_data.get('status') == 'responded':
            raise ValueError("Lead has already responded")
        
        # Get global settings
        settings_ref = db.collection('settings').document('global')
        settings_doc = settings_ref.get()
        max_followups = 3  # default
        
        if settings_doc.exists:
            max_followups = settings_doc.to_dict().get('maxFollowups', 3)
        
        current_followups = lead_data.get('followupCount', 0)
        
        if current_followups >= max_followups:
            raise ValueError(f"Maximum follow-ups ({max_followups}) already sent")
        
        # Update lead with follow-up info
        lead_ref.update({
            'status': 'emailed',
            'lastContacted': datetime.now(),
            'followupCount': current_followups + 1
        })
        
        # Here you would typically integrate with your email service
        # For now, we'll just log the action
        logging.info(f"Follow-up triggered for lead {lead_id} ({lead_data.get('email')})")
        
        return {
            'success': True,
            'message': f'Follow-up triggered successfully for {lead_data.get("email")}',
            'followupCount': current_followups + 1
        }
        
    except Exception as e:
        logging.error(f"Error triggering follow-up: {str(e)}")
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message=str(e)
        )

@https_fn.on_call()
def process_all_followups(req: https_fn.CallableRequest) -> dict:
    """
    Process all eligible leads for follow-ups based on delay settings
    """
    try:
        db = firestore.client()
        
        # Get global settings
        settings_ref = db.collection('settings').document('global')
        settings_doc = settings_ref.get()
        
        followup_delay_days = 7  # default
        max_followups = 3  # default
        
        if settings_doc.exists:
            settings_data = settings_doc.to_dict()
            followup_delay_days = settings_data.get('followupDelayDays', 7)
            max_followups = settings_data.get('maxFollowups', 3)
        
        # Calculate cutoff date
        cutoff_date = datetime.now() - timedelta(days=followup_delay_days)
        
        # Get leads eligible for follow-up
        leads_ref = db.collection('leads')
        leads_query = leads_ref.where('status', 'in', ['emailed', 'new']).stream()
        
        processed_count = 0
        
        for lead_doc in leads_query:
            lead_data = lead_doc.to_dict()
            lead_id = lead_doc.id
            
            # Check follow-up count
            current_followups = lead_data.get('followupCount', 0)
            if current_followups >= max_followups:
                continue
            
            # Check last contacted date
            last_contacted = lead_data.get('lastContacted')
            if last_contacted and last_contacted.replace(tzinfo=None) > cutoff_date:
                continue
            
            # Check blacklist
            email = lead_data.get('email', '').lower()
            blacklist_ref = db.collection('blacklist').document('emails')
            blacklist_doc = blacklist_ref.get()
            
            if blacklist_doc.exists:
                blacklist_data = blacklist_doc.to_dict()
                blacklisted_emails = blacklist_data.get('list', [])
                if email in blacklisted_emails:
                    # Update lead status to blacklisted
                    lead_doc.reference.update({'status': 'blacklisted'})
                    continue
            
            # Process follow-up
            lead_doc.reference.update({
                'status': 'emailed',
                'lastContacted': datetime.now(),
                'followupCount': current_followups + 1
            })
            
            processed_count += 1
            logging.info(f"Follow-up processed for lead {lead_id} ({email})")
        
        return {
            'success': True,
            'message': f'Processed {processed_count} follow-ups',
            'processedCount': processed_count
        }
        
    except Exception as e:
        logging.error(f"Error processing follow-ups: {str(e)}")
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message=str(e)
        )

@firestore_fn.on_document_created(document="leads/{leadId}")
def on_lead_created(event: firestore_fn.Event[firestore_fn.DocumentSnapshot]) -> None:
    """
    Triggered when a new lead is created
    """
    try:
        lead_data = event.data.to_dict()
        lead_id = event.params['leadId']
        
        logging.info(f"New lead created: {lead_id} ({lead_data.get('email')})")
        
        # Here you could trigger initial outreach email
        # For now, we'll just log the event
        
    except Exception as e:
        logging.error(f"Error processing new lead: {str(e)}")

@https_fn.on_request()
def health_check(req: https_fn.Request) -> https_fn.Response:
    """
    Simple health check endpoint
    """
    return https_fn.Response("Outreach system is running!")