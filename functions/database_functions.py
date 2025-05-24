"""
Database Maintenance Firebase Functions

Provides Firebase Functions for database cleanup and initialization
"""

import logging
from typing import Dict, Any
from firebase_functions import https_fn, options

# Configure European region
EUROPEAN_REGION = options.SupportedRegion.EUROPE_WEST1

from database_maintenance import (
    DatabaseMaintenanceManager, 
    cleanup_database, 
    initialize_database, 
    get_database_health
)


@https_fn.on_call(region=EUROPEAN_REGION)
def database_cleanup(req: https_fn.CallableRequest) -> Dict[str, Any]:
    """
    Clean up old database patterns and deprecated documents
    
    Args:
        req.data should contain:
        - dry_run (bool, optional): If True, only report what would be cleaned up (default: True)
        
    Returns:
        Dict with cleanup results
    """
    try:
        dry_run = req.data.get('dry_run', True)
        
        logging.info(f"Database cleanup requested (dry_run={dry_run})")
        
        result = cleanup_database(dry_run=dry_run)
        
        return {
            'success': True,
            'cleanup_results': result
        }
        
    except Exception as e:
        logging.error(f"Error in database_cleanup: {str(e)}")
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message=f"Failed to clean up database: {str(e)}"
        )


@https_fn.on_call(region=EUROPEAN_REGION)
def database_initialize(req: https_fn.CallableRequest) -> Dict[str, Any]:
    """
    Initialize database with default configuration
    
    Args:
        req.data should contain:
        - force (bool, optional): If True, overwrite existing configuration (default: False)
        
    Returns:
        Dict with initialization results
    """
    try:
        force = req.data.get('force', False)
        
        logging.info(f"Database initialization requested (force={force})")
        
        result = initialize_database(force=force)
        
        return {
            'success': True,
            'initialization_results': result
        }
        
    except Exception as e:
        logging.error(f"Error in database_initialize: {str(e)}")
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message=f"Failed to initialize database: {str(e)}"
        )


@https_fn.on_call(region=EUROPEAN_REGION)
def database_health_check(req: https_fn.CallableRequest) -> Dict[str, Any]:
    """
    Generate comprehensive database health report
    
    Returns:
        Dict with health report
    """
    try:
        logging.info("Database health check requested")
        
        health_report = get_database_health()
        
        return {
            'success': True,
            'health_report': health_report
        }
        
    except Exception as e:
        logging.error(f"Error in database_health_check: {str(e)}")
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message=f"Failed to generate health report: {str(e)}"
        )


@https_fn.on_call(region=EUROPEAN_REGION)
def database_full_maintenance(req: https_fn.CallableRequest) -> Dict[str, Any]:
    """
    Perform full database maintenance: health check, cleanup, and initialization
    
    Args:
        req.data should contain:
        - cleanup_dry_run (bool, optional): Dry run for cleanup (default: True)
        - force_init (bool, optional): Force initialization (default: False)
        
    Returns:
        Dict with complete maintenance results
    """
    try:
        cleanup_dry_run = req.data.get('cleanup_dry_run', True)
        force_init = req.data.get('force_init', False)
        
        logging.info(f"Full database maintenance requested (cleanup_dry_run={cleanup_dry_run}, force_init={force_init})")
        
        maintenance_results = {
            'health_check': {},
            'cleanup': {},
            'initialization': {},
            'completed_steps': []
        }
        
        # Step 1: Health check
        try:
            health_report = get_database_health()
            maintenance_results['health_check'] = health_report
            maintenance_results['completed_steps'].append('health_check')
            logging.info("Health check completed")
        except Exception as e:
            logging.warning(f"Health check failed: {e}")
            maintenance_results['health_check'] = {'error': str(e)}
        
        # Step 2: Cleanup
        try:
            cleanup_result = cleanup_database(dry_run=cleanup_dry_run)
            maintenance_results['cleanup'] = cleanup_result
            maintenance_results['completed_steps'].append('cleanup')
            logging.info(f"Cleanup completed (dry_run={cleanup_dry_run})")
        except Exception as e:
            logging.warning(f"Cleanup failed: {e}")
            maintenance_results['cleanup'] = {'error': str(e)}
        
        # Step 3: Initialization (if needed)
        try:
            # Check if initialization is needed based on health report
            config_complete = maintenance_results['health_check'].get('configuration_status', {}).get('global_config_complete', False)
            
            if not config_complete or force_init:
                init_result = initialize_database(force=force_init)
                maintenance_results['initialization'] = init_result
                maintenance_results['completed_steps'].append('initialization')
                logging.info(f"Initialization completed (force={force_init})")
            else:
                maintenance_results['initialization'] = {'skipped': 'Configuration already complete'}
                maintenance_results['completed_steps'].append('initialization_skipped')
                logging.info("Initialization skipped - configuration already complete")
        except Exception as e:
            logging.warning(f"Initialization failed: {e}")
            maintenance_results['initialization'] = {'error': str(e)}
        
        return {
            'success': True,
            'maintenance_results': maintenance_results
        }
        
    except Exception as e:
        logging.error(f"Error in database_full_maintenance: {str(e)}")
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message=f"Failed to perform full maintenance: {str(e)}"
        ) 