"""
Database Maintenance Utilities
Handles cleanup of old database patterns and initialization of proper configuration structure
"""

from typing import Dict, List, Any, Optional
from firebase_admin import firestore
from datetime import datetime, timedelta
from utils.logging_config import get_logger

logger = get_logger(__file__)

from config_model import GlobalConfig, DEFAULT_GLOBAL_CONFIG
from config_sync import get_config_sync


class DatabaseMaintenanceManager:
    """Manages database cleanup and initialization"""
    
    def __init__(self):
        self.db = firestore.client()
        self.config_sync = get_config_sync()
    
    def cleanup_old_patterns(self, dry_run: bool = True) -> Dict[str, Any]:
        """
        Clean up old database patterns and deprecated documents
        
        Args:
            dry_run: If True, only report what would be cleaned up
            
        Returns:
            Dictionary with cleanup results
        """
        cleanup_results = {
            'documents_to_delete': [],
            'documents_to_migrate': [],
            'deprecated_collections': [],
            'actions_taken': [],
            'dry_run': dry_run
        }
        
        try:
            logger.info(f"Starting database cleanup (dry_run={dry_run})")
            
            # 1. Clean up old API key documents (if they exist separately)
            old_api_patterns = [
                'apiKeys',  # Old structure
                'api_keys',  # Alternative old structure
            ]
            
            for pattern in old_api_patterns:
                try:
                    doc_ref = self.db.collection('config').document(pattern)
                    if doc_ref.get().exists:
                        cleanup_results['documents_to_delete'].append(f'config/{pattern}')
                        if not dry_run:
                            doc_ref.delete()
                            cleanup_results['actions_taken'].append(f'Deleted config/{pattern}')
                except Exception as e:
                    logger.warning(f"Could not process {pattern}: {e}")
            
            # 2. Clean up old settings structure
            old_settings_patterns = [
                'emailSettings',
                'email_settings', 
                'globalSettings',
                'global_settings',
                'leadSettings',
                'lead_settings'
            ]
            
            for pattern in old_settings_patterns:
                try:
                    # Check in both 'settings' and 'config' collections
                    for collection_name in ['settings', 'config']:
                        doc_ref = self.db.collection(collection_name).document(pattern)
                        if doc_ref.get().exists:
                            cleanup_results['documents_to_delete'].append(f'{collection_name}/{pattern}')
                            if not dry_run:
                                doc_ref.delete()
                                cleanup_results['actions_taken'].append(f'Deleted {collection_name}/{pattern}')
                except Exception as e:
                    logger.warning(f"Could not process {pattern}: {e}")
            
            # 3. Clean up old prompt structures
            old_prompt_patterns = [
                'emailPrompts',
                'email_prompts',
                'globalPrompts',
                'global_prompts'
            ]
            
            for pattern in old_prompt_patterns:
                try:
                    doc_ref = self.db.collection('prompts').document(pattern)
                    if doc_ref.get().exists:
                        cleanup_results['documents_to_delete'].append(f'prompts/{pattern}')
                        if not dry_run:
                            doc_ref.delete()
                            cleanup_results['actions_taken'].append(f'Deleted prompts/{pattern}')
                except Exception as e:
                    logger.warning(f"Could not process {pattern}: {e}")
            
            # 4. Clean up orphaned project documents
            self._cleanup_orphaned_project_configs(cleanup_results, dry_run)
            
            # 5. Clean up old email records with deprecated structure
            self._cleanup_old_email_records(cleanup_results, dry_run)
            
            # 6. Validate and fix leads with missing fields
            self._validate_lead_structure(cleanup_results, dry_run)
            
            logger.info(f"Database cleanup completed. Results: {cleanup_results}")
            return cleanup_results
            
        except Exception as e:
            logger.error(f"Error during database cleanup: {e}")
            cleanup_results['error'] = str(e)
            return cleanup_results
    
    def _cleanup_orphaned_project_configs(self, results: Dict, dry_run: bool):
        """Clean up project configurations for deleted projects"""
        try:
            # Get all existing projects
            projects_ref = self.db.collection('projects')
            existing_projects = set()
            
            for doc in projects_ref.stream():
                existing_projects.add(doc.id)
            
            # Check settings documents for orphaned project configs
            settings_ref = self.db.collection('settings')
            for doc in settings_ref.stream():
                doc_id = doc.id
                if doc_id.startswith('project_'):
                    # Extract project ID from various patterns
                    if '_location' in doc_id:
                        project_id = doc_id.replace('project_', '').replace('_location', '')
                    elif '_jobRoles' in doc_id:
                        project_id = doc_id.replace('project_', '').replace('_jobRoles', '')
                    elif '_enrichment' in doc_id:
                        project_id = doc_id.replace('project_', '').replace('_enrichment', '')
                    else:
                        project_id = doc_id.replace('project_', '')
                    
                    if project_id not in existing_projects:
                        results['documents_to_delete'].append(f'settings/{doc_id}')
                        if not dry_run:
                            doc.reference.delete()
                            results['actions_taken'].append(f'Deleted orphaned settings/{doc_id}')
            
            # Check prompts documents for orphaned project configs
            prompts_ref = self.db.collection('prompts')
            for doc in prompts_ref.stream():
                doc_id = doc.id
                if doc_id.startswith('project_'):
                    project_id = doc_id.replace('project_', '')
                    if project_id not in existing_projects:
                        results['documents_to_delete'].append(f'prompts/{doc_id}')
                        if not dry_run:
                            doc.reference.delete()
                            results['actions_taken'].append(f'Deleted orphaned prompts/{doc_id}')
                            
        except Exception as e:
            logger.warning(f"Error cleaning up orphaned project configs: {e}")
    
    def _cleanup_old_email_records(self, results: Dict, dry_run: bool):
        """Clean up old email records with deprecated structure"""
        try:
            # Clean up emails older than 90 days with old structure
            cutoff_date = datetime.now() - timedelta(days=90)
            
            emails_ref = self.db.collection('emails')
            old_emails_query = emails_ref.where('sentAt', '<', cutoff_date).limit(100)
            
            old_emails_count = 0
            for doc in old_emails_query.stream():
                email_data = doc.to_dict()
                
                # Check if it has old structure (missing required fields)
                if not email_data.get('type') or not email_data.get('projectId'):
                    results['documents_to_delete'].append(f'emails/{doc.id}')
                    if not dry_run:
                        doc.reference.delete()
                        results['actions_taken'].append(f'Deleted old email record {doc.id}')
                    old_emails_count += 1
            
            if old_emails_count > 0:
                logger.info(f"Found {old_emails_count} old email records to clean up")
                
        except Exception as e:
            logger.warning(f"Error cleaning up old email records: {e}")
    
    def _validate_lead_structure(self, results: Dict, dry_run: bool):
        """Validate and fix lead documents with missing required fields"""
        try:
            leads_ref = self.db.collection('leads')
            
            # Check recent leads for structure issues
            recent_leads_query = leads_ref.limit(100)
            
            for doc in recent_leads_query.stream():
                lead_data = doc.to_dict()
                needs_update = False
                updates = {}
                
                # Ensure required fields exist
                required_fields = {
                    'status': 'new',
                    'followupCount': 0,
                    'createdAt': firestore.SERVER_TIMESTAMP,
                    'lastContacted': None,
                    'interactionSummary': '',
                    'emailChain': []
                }
                
                for field, default_value in required_fields.items():
                    if field not in lead_data:
                        updates[field] = default_value
                        needs_update = True
                
                if needs_update:
                    results['documents_to_migrate'].append(f'leads/{doc.id}')
                    if not dry_run:
                        doc.reference.update(updates)
                        results['actions_taken'].append(f'Updated lead structure for {doc.id}')
                        
        except Exception as e:
            logger.warning(f"Error validating lead structure: {e}")
    
    def initialize_default_configuration(self, force: bool = False) -> Dict[str, Any]:
        """
        Initialize the database with default configuration if it doesn't exist
        
        Args:
            force: If True, overwrite existing configuration
            
        Returns:
            Dictionary with initialization results
        """
        init_results = {
            'initialized': [],
            'skipped': [],
            'errors': [],
            'force': force
        }
        
        try:
            logger.info(f"Initializing default configuration (force={force})")
            
            # Check if global configuration already exists
            config_exists = self._check_configuration_exists()
            
            if config_exists and not force:
                init_results['skipped'].append('Global configuration already exists')
                logger.info("Global configuration already exists, skipping initialization")
                return init_results
            
            # Initialize with default global configuration
            default_config = DEFAULT_GLOBAL_CONFIG
            
            success = self.config_sync.sync_global_config_to_firebase(default_config)
            
            if success:
                init_results['initialized'].append('Global configuration')
                
                # Initialize blacklist if it doesn't exist
                self._initialize_blacklist(init_results, force)
                
                # Initialize system metadata
                self._initialize_system_metadata(init_results, force)
                
                logger.info("Default configuration initialized successfully")
            else:
                init_results['errors'].append('Failed to sync global configuration')
                
        except Exception as e:
            logger.error(f"Error initializing default configuration: {e}")
            init_results['errors'].append(str(e))
        
        return init_results
    
    def _check_configuration_exists(self) -> bool:
        """Check if global configuration exists in Firebase"""
        try:
            # Check for key configuration documents
            required_docs = [
                ('settings', 'global'),
                ('settings', 'apiKeys'),
                ('prompts', 'global')
            ]
            
            for collection, document in required_docs:
                doc_ref = self.db.collection(collection).document(document)
                if not doc_ref.get().exists:
                    return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Error checking configuration existence: {e}")
            return False
    
    def _initialize_blacklist(self, results: Dict, force: bool):
        """Initialize global blacklist if it doesn't exist"""
        try:
            blacklist_ref = self.db.collection('blacklist').document('emails')
            
            if not blacklist_ref.get().exists or force:
                blacklist_data = {
                    'list': [],
                    'createdAt': firestore.SERVER_TIMESTAMP,
                    'lastUpdated': firestore.SERVER_TIMESTAMP
                }
                blacklist_ref.set(blacklist_data)
                results['initialized'].append('Global blacklist')
            else:
                results['skipped'].append('Global blacklist already exists')
                
        except Exception as e:
            logger.warning(f"Error initializing blacklist: {e}")
            results['errors'].append(f'Blacklist initialization failed: {e}')
    
    def _initialize_system_metadata(self, results: Dict, force: bool):
        """Initialize system metadata"""
        try:
            metadata_ref = self.db.collection('system').document('metadata')
            
            if not metadata_ref.get().exists or force:
                metadata = {
                    'version': '1.0.0',
                    'initialized_at': firestore.SERVER_TIMESTAMP,
                    'last_maintenance': firestore.SERVER_TIMESTAMP,
                    'configuration_version': '1.0',
                    'database_schema_version': '1.0'
                }
                metadata_ref.set(metadata)
                results['initialized'].append('System metadata')
            else:
                results['skipped'].append('System metadata already exists')
                
        except Exception as e:
            logger.warning(f"Error initializing system metadata: {e}")
            results['errors'].append(f'System metadata initialization failed: {e}')
    
    def get_database_health_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive health report of the database
        
        Returns:
            Dictionary with health report
        """
        health_report = {
            'timestamp': datetime.now().isoformat(),
            'configuration_status': {},
            'data_integrity': {},
            'statistics': {},
            'recommendations': []
        }
        
        try:
            # Check configuration completeness
            health_report['configuration_status'] = self._check_configuration_health()
            
            # Check data integrity
            health_report['data_integrity'] = self._check_data_integrity()
            
            # Generate statistics
            health_report['statistics'] = self._generate_statistics()
            
            # Generate recommendations
            health_report['recommendations'] = self._generate_recommendations(health_report)
            
        except Exception as e:
            logger.error(f"Error generating health report: {e}")
            health_report['error'] = str(e)
        
        return health_report
    
    def _check_configuration_health(self) -> Dict[str, Any]:
        """Check health of configuration documents"""
        config_health = {
            'global_config_complete': False,
            'missing_documents': [],
            'invalid_documents': []
        }
        
        try:
            # Check required configuration documents
            required_configs = [
                ('settings', 'apiKeys'),
                ('settings', 'smtp'),
                ('settings', 'global'),
                ('settings', 'jobRoles'),
                ('settings', 'enrichment'),
                ('settings', 'emailGeneration'),
                ('prompts', 'global')
            ]
            
            missing_count = 0
            for collection, document in required_configs:
                doc_ref = self.db.collection(collection).document(document)
                if not doc_ref.get().exists:
                    config_health['missing_documents'].append(f'{collection}/{document}')
                    missing_count += 1
            
            config_health['global_config_complete'] = missing_count == 0
            
        except Exception as e:
            logger.warning(f"Error checking configuration health: {e}")
            config_health['error'] = str(e)
        
        return config_health
    
    def _check_data_integrity(self) -> Dict[str, Any]:
        """Check data integrity across collections"""
        integrity_report = {
            'orphaned_configs': 0,
            'invalid_leads': 0,
            'missing_project_configs': 0
        }
        
        try:
            # Check for orphaned project configurations
            projects_ref = self.db.collection('projects')
            existing_projects = set(doc.id for doc in projects_ref.stream())
            
            # Check settings for orphaned project configs
            settings_ref = self.db.collection('settings')
            for doc in settings_ref.stream():
                if doc.id.startswith('project_'):
                    project_id = doc.id.split('_')[1]
                    if project_id not in existing_projects:
                        integrity_report['orphaned_configs'] += 1
            
            # Check leads for required fields
            leads_ref = self.db.collection('leads')
            for doc in leads_ref.limit(50).stream():
                lead_data = doc.to_dict()
                if not all(field in lead_data for field in ['email', 'status', 'projectId']):
                    integrity_report['invalid_leads'] += 1
            
        except Exception as e:
            logger.warning(f"Error checking data integrity: {e}")
            integrity_report['error'] = str(e)
        
        return integrity_report
    
    def _generate_statistics(self) -> Dict[str, Any]:
        """Generate database statistics"""
        stats = {}
        
        try:
            # Count documents in each collection
            collections = ['projects', 'leads', 'emails', 'settings', 'prompts', 'blacklist']
            
            for collection_name in collections:
                try:
                    collection_ref = self.db.collection(collection_name)
                    count = len(list(collection_ref.stream()))
                    stats[f'{collection_name}_count'] = count
                except Exception as e:
                    logger.warning(f"Error counting {collection_name}: {e}")
                    stats[f'{collection_name}_count'] = -1
            
        except Exception as e:
            logger.warning(f"Error generating statistics: {e}")
            stats['error'] = str(e)
        
        return stats
    
    def _generate_recommendations(self, health_report: Dict) -> List[str]:
        """Generate recommendations based on health report"""
        recommendations = []
        
        try:
            config_status = health_report.get('configuration_status', {})
            data_integrity = health_report.get('data_integrity', {})
            
            if not config_status.get('global_config_complete', False):
                recommendations.append("Initialize missing global configuration documents")
            
            if config_status.get('missing_documents'):
                recommendations.append("Run database initialization to create missing configuration")
            
            if data_integrity.get('orphaned_configs', 0) > 0:
                recommendations.append("Clean up orphaned project configurations")
            
            if data_integrity.get('invalid_leads', 0) > 0:
                recommendations.append("Fix invalid lead documents missing required fields")
            
            # Performance recommendations
            stats = health_report.get('statistics', {})
            if stats.get('emails_count', 0) > 1000:
                recommendations.append("Consider archiving old email records for better performance")
            
        except Exception as e:
            logger.warning(f"Error generating recommendations: {e}")
        
        return recommendations


# Convenience functions
def cleanup_database(dry_run: bool = True) -> Dict[str, Any]:
    """Convenience function to clean up database"""
    manager = DatabaseMaintenanceManager()
    return manager.cleanup_old_patterns(dry_run=dry_run)


def initialize_database(force: bool = False) -> Dict[str, Any]:
    """Convenience function to initialize database"""
    manager = DatabaseMaintenanceManager()
    return manager.initialize_default_configuration(force=force)


def get_database_health() -> Dict[str, Any]:
    """Convenience function to get database health report"""
    manager = DatabaseMaintenanceManager()
    return manager.get_database_health_report() 