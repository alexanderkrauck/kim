"""
Database Maintenance Firebase Functions

Provides Firebase Functions for database cleanup and initialization
"""

from typing import Dict, Any
from firebase_functions import https_fn, options

# Configure European region
EUROPEAN_REGION = options.SupportedRegion.EUROPE_WEST1

# Configure logging for Firebase Functions
from utils.logging_config import get_logger
logger = get_logger(__file__)

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
        # Safely get request data
        dry_run = True
        if req.data is not None:
            dry_run = req.data.get('dry_run', True)
        
        logger.info(f"Database cleanup requested (dry_run={dry_run})")
        
        result = cleanup_database(dry_run=dry_run)
        
        return {
            'success': True,
            'cleanup_results': result
        }
        
    except Exception as e:
        logger.error(f"Error in database_cleanup: {str(e)}")
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
        # Safely get request data
        force = False
        if req.data is not None:
            force = req.data.get('force', False)
        
        logger.info(f"Database initialization requested (force={force})")
        
        result = initialize_database(force=force)
        
        return {
            'success': True,
            'initialization_results': result
        }
        
    except Exception as e:
        logger.error(f"Error in database_initialize: {str(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
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
        logger.info("Database health check requested")
        
        health_report = get_database_health()
        
        return {
            'success': True,
            'health_report': health_report
        }
        
    except Exception as e:
        logger.error(f"Error in database_health_check: {str(e)}")
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
        # Safely get request data
        cleanup_dry_run = True
        force_init = False
        if req.data is not None:
            cleanup_dry_run = req.data.get('cleanup_dry_run', True)
            force_init = req.data.get('force_init', False)
        
        logger.info(f"Full database maintenance requested (cleanup_dry_run={cleanup_dry_run}, force_init={force_init})")
        
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
            logger.info("Health check completed")
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            maintenance_results['health_check'] = {'error': str(e)}
        
        # Step 2: Cleanup
        try:
            cleanup_result = cleanup_database(dry_run=cleanup_dry_run)
            maintenance_results['cleanup'] = cleanup_result
            maintenance_results['completed_steps'].append('cleanup')
            logger.info(f"Cleanup completed (dry_run={cleanup_dry_run})")
        except Exception as e:
            logger.warning(f"Cleanup failed: {e}")
            maintenance_results['cleanup'] = {'error': str(e)}
        
        # Step 3: Initialization (if needed)
        try:
            # Check if initialization is needed based on health report
            health_check_data = maintenance_results.get('health_check', {})
            config_status = health_check_data.get('configuration_status', {}) if health_check_data else {}
            config_complete = config_status.get('global_config_complete', False) if config_status else False
            
            if not config_complete or force_init:
                init_result = initialize_database(force=force_init)
                maintenance_results['initialization'] = init_result
                maintenance_results['completed_steps'].append('initialization')
                logger.info(f"Initialization completed (force={force_init})")
            else:
                maintenance_results['initialization'] = {'skipped': 'Configuration already complete'}
                maintenance_results['completed_steps'].append('initialization_skipped')
                logger.info("Initialization skipped - configuration already complete")
        except Exception as e:
            logger.warning(f"Initialization failed: {e}")
            maintenance_results['initialization'] = {'error': str(e)}
        
        return {
            'success': True,
            'maintenance_results': maintenance_results
        }
        
    except Exception as e:
        logger.error(f"Error in database_full_maintenance: {str(e)}")
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message=f"Failed to perform full maintenance: {str(e)}"
        ) 