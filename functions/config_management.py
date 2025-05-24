"""
Configuration Management Functions

This module provides Firebase Functions for managing global and project-specific configurations.
"""

import logging
from typing import Dict, List, Optional, Any
from firebase_functions import https_fn, options
from firebase_admin import firestore

# Configure European region
EUROPEAN_REGION = options.SupportedRegion.EUROPE_WEST1

from config_sync import get_config_sync
from config_model import GlobalConfig, ProjectConfig


def get_global_config_logic(request_data: Dict[str, Any], auth_uid: str = None) -> Dict[str, Any]:
    """
    Get global configuration
    
    Args:
        request_data: Dictionary (empty for this function)
        auth_uid: User ID from Firebase Auth (optional)
        
    Returns:
        Dict with success status and global configuration
    """
    try:
        config_sync = get_config_sync()
        global_config = config_sync.load_global_config_from_firebase()
        
        # Convert to dictionary for JSON serialization
        config_dict = {
            'api_keys': {
                'openai_api_key': global_config.api_keys.openai_api_key,
                'apollo_api_key': global_config.api_keys.apollo_api_key,
                'apifi_api_key': global_config.api_keys.apifi_api_key,
                'perplexity_api_key': global_config.api_keys.perplexity_api_key
            },
            'smtp': {
                'host': global_config.smtp.host,
                'port': global_config.smtp.port,
                'secure': global_config.smtp.secure,
                'username': global_config.smtp.username,
                'password': global_config.smtp.password,
                'from_email': global_config.smtp.from_email,
                'from_name': global_config.smtp.from_name,
                'reply_to_email': global_config.smtp.reply_to_email
            },
            'lead_filter': {
                'one_person_per_company': global_config.lead_filter.one_person_per_company,
                'require_email': global_config.lead_filter.require_email,
                'exclude_blacklisted': global_config.lead_filter.exclude_blacklisted,
                'min_company_size': global_config.lead_filter.min_company_size,
                'max_company_size': global_config.lead_filter.max_company_size
            },
            'job_roles': {
                'target_roles': [role.value for role in global_config.job_roles.target_roles],
                'custom_roles': global_config.job_roles.custom_roles
            },
            'enrichment': {
                'enabled': global_config.enrichment.enabled,
                'max_retries': global_config.enrichment.max_retries,
                'timeout_seconds': global_config.enrichment.timeout_seconds,
                'prompt_template': global_config.enrichment.prompt_template
            },
            'email_generation': {
                'model': global_config.email_generation.model,
                'max_tokens': global_config.email_generation.max_tokens,
                'temperature': global_config.email_generation.temperature,
                'outreach_prompt': global_config.email_generation.outreach_prompt,
                'followup_prompt': global_config.email_generation.followup_prompt
            },
            'scheduling': {
                'followup_delay_days': global_config.scheduling.followup_delay_days,
                'max_followups': global_config.scheduling.max_followups,
                'daily_email_limit': global_config.scheduling.daily_email_limit,
                'rate_limit_delay_seconds': global_config.scheduling.rate_limit_delay_seconds,
                'working_hours_start': global_config.scheduling.working_hours_start,
                'working_hours_end': global_config.scheduling.working_hours_end,
                'working_days': global_config.scheduling.working_days,
                'timezone': global_config.scheduling.timezone
            }
        }
        
        return {
            'success': True,
            'config': config_dict
        }
        
    except Exception as e:
        logging.error(f"Error getting global config: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        }


@https_fn.on_call(region=EUROPEAN_REGION)
def get_global_config(req: https_fn.CallableRequest) -> Dict[str, Any]:
    """
    Firebase Functions wrapper for getting global configuration
    """
    try:
        auth_uid = req.auth.uid if req.auth else None
        result = get_global_config_logic(req.data, auth_uid)
        
        if not result.get('success', True):
            raise https_fn.HttpsError(
                code=https_fn.FunctionsErrorCode.INTERNAL,
                message=result.get('error', 'Unknown error')
            )
        
        return result
        
    except https_fn.HttpsError:
        raise
    except Exception as e:
        logging.error(f"Error in get_global_config Firebase Function: {str(e)}")
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message=f"Failed to get global config: {str(e)}"
        )


def update_global_config_logic(request_data: Dict[str, Any], auth_uid: str = None) -> Dict[str, Any]:
    """
    Update global configuration
    
    Args:
        request_data: Dictionary containing:
        - config (dict): Updated configuration data
        auth_uid: User ID from Firebase Auth (optional)
        
    Returns:
        Dict with success status and message
    """
    try:
        config_data = request_data.get('config')
        if not config_data:
            raise ValueError("config data is required")
        
        config_sync = get_config_sync()
        
        # Load current config
        current_config = config_sync.load_global_config_from_firebase()
        
        # Update fields that are provided
        if 'api_keys' in config_data:
            api_keys_data = config_data['api_keys']
            if 'openai_api_key' in api_keys_data:
                current_config.api_keys.openai_api_key = api_keys_data['openai_api_key']
            if 'apollo_api_key' in api_keys_data:
                current_config.api_keys.apollo_api_key = api_keys_data['apollo_api_key']
            if 'apifi_api_key' in api_keys_data:
                current_config.api_keys.apifi_api_key = api_keys_data['apifi_api_key']
            if 'perplexity_api_key' in api_keys_data:
                current_config.api_keys.perplexity_api_key = api_keys_data['perplexity_api_key']
        
        if 'smtp' in config_data:
            smtp_data = config_data['smtp']
            for field in ['host', 'port', 'secure', 'username', 'password', 'from_email', 'from_name', 'reply_to_email']:
                if field in smtp_data:
                    setattr(current_config.smtp, field, smtp_data[field])
        
        if 'lead_filter' in config_data:
            filter_data = config_data['lead_filter']
            for field in ['one_person_per_company', 'require_email', 'exclude_blacklisted', 'min_company_size', 'max_company_size']:
                if field in filter_data:
                    setattr(current_config.lead_filter, field, filter_data[field])
        
        if 'enrichment' in config_data:
            enrich_data = config_data['enrichment']
            for field in ['enabled', 'max_retries', 'timeout_seconds', 'prompt_template']:
                if field in enrich_data:
                    setattr(current_config.enrichment, field, enrich_data[field])
        
        if 'email_generation' in config_data:
            email_data = config_data['email_generation']
            for field in ['model', 'max_tokens', 'temperature', 'outreach_prompt', 'followup_prompt']:
                if field in email_data:
                    setattr(current_config.email_generation, field, email_data[field])
        
        if 'scheduling' in config_data:
            sched_data = config_data['scheduling']
            for field in ['followup_delay_days', 'max_followups', 'daily_email_limit', 'rate_limit_delay_seconds', 
                         'working_hours_start', 'working_hours_end', 'working_days', 'timezone']:
                if field in sched_data:
                    setattr(current_config.scheduling, field, sched_data[field])
        
        # Sync updated config to Firebase
        success = config_sync.sync_global_config_to_firebase(current_config)
        
        if not success:
            raise Exception("Failed to sync configuration to Firebase")
        
        return {
            'success': True,
            'message': 'Global configuration updated successfully'
        }
        
    except Exception as e:
        logging.error(f"Error updating global config: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        }


@https_fn.on_call(region=EUROPEAN_REGION)
def update_global_config(req: https_fn.CallableRequest) -> Dict[str, Any]:
    """
    Firebase Functions wrapper for updating global configuration
    """
    try:
        auth_uid = req.auth.uid if req.auth else None
        result = update_global_config_logic(req.data, auth_uid)
        
        if not result.get('success', True):
            raise https_fn.HttpsError(
                code=https_fn.FunctionsErrorCode.INTERNAL,
                message=result.get('error', 'Unknown error')
            )
        
        return result
        
    except https_fn.HttpsError:
        raise
    except Exception as e:
        logging.error(f"Error in update_global_config Firebase Function: {str(e)}")
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message=f"Failed to update global config: {str(e)}"
        )


def get_project_config_logic(request_data: Dict[str, Any], auth_uid: str = None) -> Dict[str, Any]:
    """
    Get project-specific configuration
    
    Args:
        request_data: Dictionary containing:
        - project_id (str): ID of the project
        auth_uid: User ID from Firebase Auth (optional)
        
    Returns:
        Dict with success status and project configuration
    """
    try:
        project_id = request_data.get('project_id')
        if not project_id:
            raise ValueError("project_id is required")
        
        config_sync = get_config_sync()
        project_config = config_sync.load_project_config_from_firebase(project_id)
        global_config = config_sync.load_global_config_from_firebase()
        effective_config = project_config.get_effective_config(global_config)
        
        # Convert to dictionary for JSON serialization
        config_dict = {
            'project_id': project_config.project_id,
            'location': {
                'raw_location': project_config.location.raw_location,
                'apollo_location_ids': project_config.location.apollo_location_ids,
                'use_llm_parsing': project_config.location.use_llm_parsing
            },
            'use_global_lead_filter': project_config.use_global_lead_filter,
            'use_global_job_roles': project_config.use_global_job_roles,
            'use_global_enrichment': project_config.use_global_enrichment,
            'use_global_email_generation': project_config.use_global_email_generation,
            'use_global_scheduling': project_config.use_global_scheduling,
            'effective_config': {
                'lead_filter': {
                    'one_person_per_company': effective_config.lead_filter.one_person_per_company,
                    'require_email': effective_config.lead_filter.require_email,
                    'exclude_blacklisted': effective_config.lead_filter.exclude_blacklisted,
                    'min_company_size': effective_config.lead_filter.min_company_size,
                    'max_company_size': effective_config.lead_filter.max_company_size
                },
                'job_roles': {
                    'target_roles': [role.value for role in effective_config.job_roles.target_roles],
                    'custom_roles': effective_config.job_roles.custom_roles
                },
                'enrichment': {
                    'enabled': effective_config.enrichment.enabled,
                    'max_retries': effective_config.enrichment.max_retries,
                    'timeout_seconds': effective_config.enrichment.timeout_seconds,
                    'prompt_template': effective_config.enrichment.prompt_template
                },
                'email_generation': {
                    'model': effective_config.email_generation.model,
                    'max_tokens': effective_config.email_generation.max_tokens,
                    'temperature': effective_config.email_generation.temperature,
                    'outreach_prompt': effective_config.email_generation.outreach_prompt,
                    'followup_prompt': effective_config.email_generation.followup_prompt
                },
                'scheduling': {
                    'followup_delay_days': effective_config.scheduling.followup_delay_days,
                    'max_followups': effective_config.scheduling.max_followups,
                    'daily_email_limit': effective_config.scheduling.daily_email_limit,
                    'rate_limit_delay_seconds': effective_config.scheduling.rate_limit_delay_seconds,
                    'working_hours_start': effective_config.scheduling.working_hours_start,
                    'working_hours_end': effective_config.scheduling.working_hours_end,
                    'working_days': effective_config.scheduling.working_days,
                    'timezone': effective_config.scheduling.timezone
                }
            }
        }
        
        return {
            'success': True,
            'config': config_dict
        }
        
    except Exception as e:
        logging.error(f"Error getting project config: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        }


@https_fn.on_call(region=EUROPEAN_REGION)
def get_project_config(req: https_fn.CallableRequest) -> Dict[str, Any]:
    """
    Firebase Functions wrapper for getting project configuration
    """
    try:
        auth_uid = req.auth.uid if req.auth else None
        result = get_project_config_logic(req.data, auth_uid)
        
        if not result.get('success', True):
            raise https_fn.HttpsError(
                code=https_fn.FunctionsErrorCode.INTERNAL,
                message=result.get('error', 'Unknown error')
            )
        
        return result
        
    except https_fn.HttpsError:
        raise
    except Exception as e:
        logging.error(f"Error in get_project_config Firebase Function: {str(e)}")
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message=f"Failed to get project config: {str(e)}"
        )


def update_project_config_logic(request_data: Dict[str, Any], auth_uid: str = None) -> Dict[str, Any]:
    """
    Update project-specific configuration
    
    Args:
        request_data: Dictionary containing:
        - project_id (str): ID of the project
        - config (dict): Updated configuration data
        auth_uid: User ID from Firebase Auth (optional)
        
    Returns:
        Dict with success status and message
    """
    try:
        project_id = request_data.get('project_id')
        config_data = request_data.get('config')
        
        if not project_id:
            raise ValueError("project_id is required")
        if not config_data:
            raise ValueError("config data is required")
        
        config_sync = get_config_sync()
        
        # Load current project config
        current_config = config_sync.load_project_config_from_firebase(project_id)
        
        # Update location settings
        if 'location' in config_data:
            location_data = config_data['location']
            for field in ['raw_location', 'apollo_location_ids', 'use_llm_parsing']:
                if field in location_data:
                    setattr(current_config.location, field, location_data[field])
        
        # Update global usage flags
        for flag in ['use_global_lead_filter', 'use_global_job_roles', 'use_global_enrichment', 
                    'use_global_email_generation', 'use_global_scheduling']:
            if flag in config_data:
                setattr(current_config, flag, config_data[flag])
        
        # Sync updated config to Firebase
        success = config_sync.sync_project_config_to_firebase(current_config)
        
        if not success:
            raise Exception("Failed to sync project configuration to Firebase")
        
        return {
            'success': True,
            'message': f'Project {project_id} configuration updated successfully'
        }
        
    except Exception as e:
        logging.error(f"Error updating project config: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        }


@https_fn.on_call(region=EUROPEAN_REGION)
def update_project_config(req: https_fn.CallableRequest) -> Dict[str, Any]:
    """
    Firebase Functions wrapper for updating project configuration
    """
    try:
        auth_uid = req.auth.uid if req.auth else None
        result = update_project_config_logic(req.data, auth_uid)
        
        if not result.get('success', True):
            raise https_fn.HttpsError(
                code=https_fn.FunctionsErrorCode.INTERNAL,
                message=result.get('error', 'Unknown error')
            )
        
        return result
        
    except https_fn.HttpsError:
        raise
    except Exception as e:
        logging.error(f"Error in update_project_config Firebase Function: {str(e)}")
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message=f"Failed to update project config: {str(e)}"
        ) 