#!/usr/bin/env python3
"""
Database Maintenance Runner

Script to run database cleanup and initialization for the lead generation system.
Can be run locally for testing or as part of deployment process.
"""

import os
import sys
import json
import logging
from datetime import datetime

# Add the functions directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Firebase Admin (only if not already initialized)
try:
    import firebase_admin
    from firebase_admin import credentials
    
    if not firebase_admin._apps:
        # Try to use application default credentials
        try:
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred)
            logger.info("Firebase initialized with application default credentials")
        except Exception as e:
            logger.warning(f"Could not initialize Firebase: {e}")
            logger.info("Some operations may fail without Firebase connection")
    
except ImportError:
    logger.error("Firebase Admin SDK not installed")
    sys.exit(1)

# Import our database maintenance functions
try:
    from database_maintenance import (
        DatabaseMaintenanceManager,
        cleanup_database,
        initialize_database,
        get_database_health
    )
    logger.info("Database maintenance modules imported successfully")
except ImportError as e:
    logger.error(f"Failed to import database maintenance modules: {e}")
    sys.exit(1)


def run_health_check():
    """Run database health check"""
    logger.info("🔍 Running database health check...")
    try:
        health_report = get_database_health()
        
        print("\n" + "="*60)
        print("📊 DATABASE HEALTH REPORT")
        print("="*60)
        print(f"Timestamp: {health_report['timestamp']}")
        
        # Configuration Status
        config_status = health_report.get('configuration_status', {})
        print(f"\n🔧 Configuration Status:")
        print(f"  Global Config Complete: {'✅' if config_status.get('global_config_complete') else '❌'}")
        
        missing_docs = config_status.get('missing_documents', [])
        if missing_docs:
            print(f"  Missing Documents: {len(missing_docs)}")
            for doc in missing_docs:
                print(f"    - {doc}")
        else:
            print(f"  Missing Documents: None ✅")
        
        # Data Integrity
        integrity = health_report.get('data_integrity', {})
        print(f"\n🔍 Data Integrity:")
        print(f"  Orphaned Configs: {integrity.get('orphaned_configs', 0)}")
        print(f"  Invalid Leads: {integrity.get('invalid_leads', 0)}")
        
        # Statistics
        stats = health_report.get('statistics', {})
        print(f"\n📈 Statistics:")
        for key, value in stats.items():
            if key.endswith('_count'):
                collection_name = key.replace('_count', '').title()
                print(f"  {collection_name}: {value}")
        
        # Recommendations
        recommendations = health_report.get('recommendations', [])
        if recommendations:
            print(f"\n💡 Recommendations:")
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec}")
        else:
            print(f"\n💡 Recommendations: None - Database looks healthy! ✅")
        
        print("="*60)
        return health_report
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return None


def run_cleanup(dry_run=True):
    """Run database cleanup"""
    mode = "DRY RUN" if dry_run else "ACTUAL CLEANUP"
    logger.info(f"🧹 Running database cleanup ({mode})...")
    
    try:
        cleanup_result = cleanup_database(dry_run=dry_run)
        
        print(f"\n" + "="*60)
        print(f"🧹 DATABASE CLEANUP RESULTS ({mode})")
        print("="*60)
        
        print(f"Documents to delete: {len(cleanup_result.get('documents_to_delete', []))}")
        for doc in cleanup_result.get('documents_to_delete', []):
            print(f"  - {doc}")
        
        print(f"\nDocuments to migrate: {len(cleanup_result.get('documents_to_migrate', []))}")
        for doc in cleanup_result.get('documents_to_migrate', []):
            print(f"  - {doc}")
        
        if not dry_run:
            print(f"\nActions taken: {len(cleanup_result.get('actions_taken', []))}")
            for action in cleanup_result.get('actions_taken', []):
                print(f"  ✅ {action}")
        
        print("="*60)
        return cleanup_result
        
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        return None


def run_initialization(force=False):
    """Run database initialization"""
    mode = "FORCE INITIALIZATION" if force else "INITIALIZATION"
    logger.info(f"🚀 Running database {mode.lower()}...")
    
    try:
        init_result = initialize_database(force=force)
        
        print(f"\n" + "="*60)
        print(f"🚀 DATABASE {mode} RESULTS")
        print("="*60)
        
        initialized = init_result.get('initialized', [])
        if initialized:
            print(f"Initialized: {len(initialized)} items")
            for item in initialized:
                print(f"  ✅ {item}")
        
        skipped = init_result.get('skipped', [])
        if skipped:
            print(f"\nSkipped: {len(skipped)} items")
            for item in skipped:
                print(f"  ⏭️ {item}")
        
        errors = init_result.get('errors', [])
        if errors:
            print(f"\nErrors: {len(errors)}")
            for error in errors:
                print(f"  ❌ {error}")
        
        print("="*60)
        return init_result
        
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        return None


def run_full_maintenance(cleanup_dry_run=True, force_init=False):
    """Run complete database maintenance"""
    logger.info("🔧 Running FULL database maintenance...")
    
    results = {
        'health_check': None,
        'cleanup': None,
        'initialization': None
    }
    
    # Step 1: Health Check
    print("\n🔍 STEP 1: Health Check")
    results['health_check'] = run_health_check()
    
    # Step 2: Cleanup
    print(f"\n🧹 STEP 2: Cleanup ({'DRY RUN' if cleanup_dry_run else 'ACTUAL'})")
    results['cleanup'] = run_cleanup(dry_run=cleanup_dry_run)
    
    # Step 3: Initialization (if needed)
    print(f"\n🚀 STEP 3: Initialization ({'FORCE' if force_init else 'AUTO'})")
    
    # Check if initialization is needed
    needs_init = False
    if results['health_check']:
        config_complete = results['health_check'].get('configuration_status', {}).get('global_config_complete', False)
        needs_init = not config_complete or force_init
    
    if needs_init:
        results['initialization'] = run_initialization(force=force_init)
    else:
        print("  ⏭️ Initialization skipped - configuration already complete")
        results['initialization'] = {'skipped': ['Configuration already complete']}
    
    print(f"\n" + "="*60)
    print("🎉 FULL MAINTENANCE COMPLETED")
    print("="*60)
    
    return results


def save_results(results, filename=None):
    """Save maintenance results to a JSON file"""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"database_maintenance_{timestamp}.json"
    
    try:
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"Results saved to {filename}")
    except Exception as e:
        logger.error(f"Failed to save results: {e}")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Database Maintenance Runner")
    parser.add_argument('--action', choices=['health', 'cleanup', 'init', 'full'], 
                       default='health', help='Action to perform')
    parser.add_argument('--dry-run', action='store_true', default=True,
                       help='Perform dry run for cleanup (default: True)')
    parser.add_argument('--actual', action='store_true', 
                       help='Perform actual cleanup (overrides --dry-run)')
    parser.add_argument('--force', action='store_true', 
                       help='Force initialization even if config exists')
    parser.add_argument('--save-results', action='store_true',
                       help='Save results to JSON file')
    
    args = parser.parse_args()
    
    # Override dry_run if --actual is specified
    if args.actual:
        args.dry_run = False
    
    print("🔧 Database Maintenance Tool")
    print("="*60)
    print(f"Action: {args.action}")
    if args.action in ['cleanup', 'full']:
        print(f"Cleanup Mode: {'DRY RUN' if args.dry_run else 'ACTUAL'}")
    if args.action in ['init', 'full']:
        print(f"Initialize: {'FORCE' if args.force else 'AUTO'}")
    print("="*60)
    
    results = None
    
    try:
        if args.action == 'health':
            results = run_health_check()
        elif args.action == 'cleanup':
            results = run_cleanup(dry_run=args.dry_run)
        elif args.action == 'init':
            results = run_initialization(force=args.force)
        elif args.action == 'full':
            results = run_full_maintenance(cleanup_dry_run=args.dry_run, force_init=args.force)
        
        if args.save_results and results:
            save_results(results)
            
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 