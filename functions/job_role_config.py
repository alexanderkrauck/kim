"""
Job Role Configuration Functions
Manages job role settings for projects and global configuration
"""

import logging
from typing import Dict, List, Any
from firebase_functions import https_fn, options
from firebase_admin import firestore

# Configure European region
EUROPEAN_REGION = options.SupportedRegion.EUROPE_WEST1

from config_model import JobRole, JobRoleConfig
from config_sync import config_sync


@https_fn.on_call(region=EUROPEAN_REGION)
def get_job_roles_config(req: https_fn.CallableRequest) -> Dict[str, Any]:
    """
    Get job roles configuration for a project or global
    
    Args:
        req.data should contain:
        - project_id (optional): If provided, get project-specific config
        
    Returns:
        Dict with job roles configuration
    """
    try:
        project_id = req.data.get('project_id')
        
        if project_id:
            # Get project-specific configuration
            project_config = config_sync.load_project_config_from_firebase(project_id)
            global_config = config_sync.load_global_config_from_firebase()
            effective_config = project_config.get_effective_config(global_config)
            
            return {
                'success': True,
                'config': {
                    'target_roles': [role.value for role in effective_config.job_roles.target_roles],
                    'custom_roles': effective_config.job_roles.custom_roles,
                    'use_global': project_config.use_global_job_roles,
                    'project_id': project_id
                }
            }
        else:
            # Get global configuration
            global_config = config_sync.load_global_config_from_firebase()
            
            return {
                'success': True,
                'config': {
                    'target_roles': [role.value for role in global_config.job_roles.target_roles],
                    'custom_roles': global_config.job_roles.custom_roles,
                    'is_global': True
                }
            }
            
    except Exception as e:
        logging.error(f"Error getting job roles config: {e}")
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message=f"Failed to get job roles configuration: {str(e)}"
        )


@https_fn.on_call(region=EUROPEAN_REGION)
def update_job_roles_config(req: https_fn.CallableRequest) -> Dict[str, Any]:
    """
    Update job roles configuration
    
    Args:
        req.data should contain:
        - project_id (optional): If provided, update project-specific config
        - target_roles: List of target job role strings
        - custom_roles: List of custom job role strings
        - use_global (optional): For project config, whether to use global settings
        
    Returns:
        Dict with success status
    """
    try:
        project_id = req.data.get('project_id')
        target_roles = req.data.get('target_roles', [])
        custom_roles = req.data.get('custom_roles', [])
        use_global = req.data.get('use_global', True)
        
        # Validate target roles
        valid_roles = []
        for role_str in target_roles:
            try:
                role = JobRole(role_str)
                valid_roles.append(role)
            except ValueError:
                logging.warning(f"Invalid job role: {role_str}")
        
        # Create job role config
        job_role_config = JobRoleConfig(
            target_roles=valid_roles,
            custom_roles=custom_roles
        )
        
        if not job_role_config.validate():
            raise ValueError("Invalid job role configuration - must have at least one role")
        
        if project_id:
            # Update project-specific configuration
            project_config = config_sync.load_project_config_from_firebase(project_id)
            project_config.use_global_job_roles = use_global
            
            if not use_global:
                project_config.job_roles = job_role_config
            
            success = config_sync.sync_project_config_to_firebase(project_config)
        else:
            # Update global configuration
            global_config = config_sync.load_global_config_from_firebase()
            global_config.job_roles = job_role_config
            
            success = config_sync.sync_global_config_to_firebase(global_config)
        
        if success:
            return {
                'success': True,
                'message': f"Job roles configuration updated successfully for {'project ' + project_id if project_id else 'global settings'}"
            }
        else:
            raise ValueError("Failed to save configuration to Firebase")
            
    except Exception as e:
        logging.error(f"Error updating job roles config: {e}")
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message=f"Failed to update job roles configuration: {str(e)}"
        )


@https_fn.on_call(region=EUROPEAN_REGION)
def get_available_job_roles(req: https_fn.CallableRequest) -> Dict[str, Any]:
    """
    Get list of available predefined job roles
    
    Returns:
        Dict with available job roles
    """
    try:
        predefined_roles = [
            {'value': role.value, 'label': role.value}
            for role in JobRole
        ]
        
        return {
            'success': True,
            'roles': predefined_roles
        }
        
    except Exception as e:
        logging.error(f"Error getting available job roles: {e}")
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message=f"Failed to get available job roles: {str(e)}"
        ) 