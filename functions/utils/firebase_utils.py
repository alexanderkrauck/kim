"""
Firebase utility functions
"""

import os
import logging
from typing import Dict, Optional
from firebase_admin import firestore
from dotenv import load_dotenv

# Load environment variables for local development
load_dotenv()


def get_firestore_client():
    """Get Firestore client instance"""
    return firestore.client()


def get_api_keys(use_env: bool = False) -> Dict[str, str]:
    """
    Get API keys from Firebase or environment variables
    
    Args:
        use_env: If True, use environment variables (for local development)
        
    Returns:
        Dictionary containing API keys
    """
    if use_env or os.getenv('DEBUG') == 'true':
        # Use environment variables for local development
        return {
            'openai': os.getenv('OPENAI_API_KEY'),
            'apollo': os.getenv('APOLLO_API_KEY'),
            'apifi': os.getenv('APIFI_API_KEY'),
            'perplexity': os.getenv('PERPLEXITY_API_KEY')
        }
    else:
        # Use Firebase for production
        try:
            db = get_firestore_client()
            api_keys_doc = db.collection('settings').document('apiKeys').get()
            
            if api_keys_doc.exists:
                data = api_keys_doc.to_dict()
                return {
                    'openai': data.get('openaiApiKey'),
                    'apollo': data.get('apolloApiKey'),
                    'apifi': data.get('apifiApiKey'),
                    'perplexity': data.get('perplexityApiKey')
                }
            else:
                logging.warning("API keys document not found in Firebase")
                return {}
        except Exception as e:
            logging.error(f"Error getting API keys from Firebase: {e}")
            return {}


def get_smtp_settings(use_env: bool = False) -> Dict[str, any]:
    """
    Get SMTP settings from Firebase or environment variables
    
    Args:
        use_env: If True, use environment variables (for local development)
        
    Returns:
        Dictionary containing SMTP settings
    """
    if use_env or os.getenv('DEBUG') == 'true':
        # Use environment variables for local development
        return {
            'host': os.getenv('SMTP_HOST', 'smtp.gmail.com'),
            'port': int(os.getenv('SMTP_PORT', '587')),
            'secure': os.getenv('SMTP_SECURE', 'false').lower() == 'true',
            'username': os.getenv('SMTP_USERNAME'),
            'password': os.getenv('SMTP_PASSWORD'),
            'fromEmail': os.getenv('SMTP_FROM_EMAIL'),
            'fromName': os.getenv('SMTP_FROM_NAME'),
            'replyToEmail': os.getenv('SMTP_REPLY_TO_EMAIL')
        }
    else:
        # Use Firebase for production
        try:
            db = get_firestore_client()
            smtp_doc = db.collection('settings').document('smtp').get()
            
            if smtp_doc.exists:
                return smtp_doc.to_dict()
            else:
                logging.warning("SMTP settings document not found in Firebase")
                return {}
        except Exception as e:
            logging.error(f"Error getting SMTP settings from Firebase: {e}")
            return {}


def get_project_settings(project_id: str) -> Dict[str, any]:
    """
    Get project-specific settings from Firebase
    
    Args:
        project_id: ID of the project
        
    Returns:
        Dictionary containing project settings
    """
    try:
        db = get_firestore_client()
        
        # Get project-specific settings
        project_settings_doc = db.collection('settings').document(f'project_{project_id}').get()
        
        if project_settings_doc.exists:
            project_settings = project_settings_doc.to_dict()
            
            # If project uses global settings, merge with global
            if project_settings.get('useGlobalSettings', True):
                global_settings_doc = db.collection('settings').document('global').get()
                if global_settings_doc.exists:
                    global_settings = global_settings_doc.to_dict()
                    # Project settings override global settings
                    global_settings.update(project_settings)
                    return global_settings
            
            return project_settings
        else:
            # Return global settings as fallback
            global_settings_doc = db.collection('settings').document('global').get()
            if global_settings_doc.exists:
                return global_settings_doc.to_dict()
            else:
                # Return default settings
                return {
                    'followupDelayDays': 7,
                    'maxFollowups': 3
                }
                
    except Exception as e:
        logging.error(f"Error getting project settings: {e}")
        return {
            'followupDelayDays': 7,
            'maxFollowups': 3
        }


def get_project_prompts(project_id: str) -> Dict[str, str]:
    """
    Get project-specific prompts from Firebase
    
    Args:
        project_id: ID of the project
        
    Returns:
        Dictionary containing prompts
    """
    try:
        db = get_firestore_client()
        
        # Get project-specific prompts
        project_prompts_doc = db.collection('prompts').document(f'project_{project_id}').get()
        
        if project_prompts_doc.exists:
            project_prompts = project_prompts_doc.to_dict()
            
            # If project uses global prompts, use global
            if project_prompts.get('useGlobalPrompts', True):
                global_prompts_doc = db.collection('prompts').document('global').get()
                if global_prompts_doc.exists:
                    return global_prompts_doc.to_dict()
            else:
                return {
                    'outreachPrompt': project_prompts.get('outreachPrompt', ''),
                    'followupPrompt': project_prompts.get('followupPrompt', '')
                }
        
        # Return global prompts as fallback
        global_prompts_doc = db.collection('prompts').document('global').get()
        if global_prompts_doc.exists:
            return global_prompts_doc.to_dict()
        else:
            return {
                'outreachPrompt': '',
                'followupPrompt': ''
            }
            
    except Exception as e:
        logging.error(f"Error getting project prompts: {e}")
        return {
            'outreachPrompt': '',
            'followupPrompt': ''
        } 