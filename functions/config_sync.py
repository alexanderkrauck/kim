"""
Configuration Sync Utilities
Syncs Python configuration schema to Firebase and vice versa
"""

import logging
from typing import Dict, Any, Optional
from firebase_admin import firestore
from dataclasses import asdict
import json

from config_model import (
    GlobalConfig, ProjectConfig, SmtpConfig, ApiKeysConfig, 
    LeadFilterConfig, LocationConfig, JobRoleConfig, EnrichmentConfig,
    EmailGenerationConfig, SchedulingConfig, JobRole
)


class ConfigSyncManager:
    """Manages synchronization between Python config model and Firebase"""
    
    def __init__(self):
        self.db = firestore.client()
    
    def sync_global_config_to_firebase(self, config: GlobalConfig) -> bool:
        """
        Sync global configuration to Firebase
        Maintains existing Firebase structure
        """
        try:
            # Sync API Keys
            api_keys_dict = {
                'openaiApiKey': config.api_keys.openai_api_key,
                'apolloApiKey': config.api_keys.apollo_api_key,
                'apifiApiKey': config.api_keys.apifi_api_key,
                'perplexityApiKey': config.api_keys.perplexity_api_key
            }
            self.db.collection('settings').document('apiKeys').set(api_keys_dict)
            
            # Sync SMTP Settings
            smtp_dict = {
                'host': config.smtp.host,
                'port': config.smtp.port,
                'secure': config.smtp.secure,
                'username': config.smtp.username,
                'password': config.smtp.password,
                'fromEmail': config.smtp.from_email,
                'fromName': config.smtp.from_name,
                'replyToEmail': config.smtp.reply_to_email
            }
            self.db.collection('settings').document('smtp').set(smtp_dict)
            
            # Sync Global Settings (scheduling and lead filter)
            global_settings_dict = {
                'followupDelayDays': config.scheduling.followup_delay_days,
                'maxFollowups': config.scheduling.max_followups,
                'dailyEmailLimit': config.scheduling.daily_email_limit,
                'rateLimitDelaySeconds': config.scheduling.rate_limit_delay_seconds,
                'workingHoursStart': config.scheduling.working_hours_start,
                'workingHoursEnd': config.scheduling.working_hours_end,
                'workingDays': config.scheduling.working_days,
                'timezone': config.scheduling.timezone,
                'onePersonPerCompany': config.lead_filter.one_person_per_company,
                'requireEmail': config.lead_filter.require_email,
                'excludeBlacklisted': config.lead_filter.exclude_blacklisted,
                'minCompanySize': config.lead_filter.min_company_size,
                'maxCompanySize': config.lead_filter.max_company_size
            }
            self.db.collection('settings').document('global').set(global_settings_dict)
            
            # Sync Job Roles Configuration
            job_roles_dict = {
                'targetRoles': [role.value for role in config.job_roles.target_roles],
                'customRoles': config.job_roles.custom_roles
            }
            self.db.collection('settings').document('jobRoles').set(job_roles_dict)
            
            # Sync Enrichment Configuration
            enrichment_dict = {
                'enabled': config.enrichment.enabled,
                'maxRetries': config.enrichment.max_retries,
                'timeoutSeconds': config.enrichment.timeout_seconds,
                'promptTemplate': config.enrichment.prompt_template
            }
            self.db.collection('settings').document('enrichment').set(enrichment_dict)
            
            # Sync Email Generation Configuration
            email_gen_dict = {
                'model': config.email_generation.model,
                'maxTokens': config.email_generation.max_tokens,
                'temperature': config.email_generation.temperature
            }
            self.db.collection('settings').document('emailGeneration').set(email_gen_dict)
            
            # Sync Global Prompts
            prompts_dict = {
                'outreachPrompt': config.email_generation.outreach_prompt,
                'followupPrompt': config.email_generation.followup_prompt
            }
            self.db.collection('prompts').document('global').set(prompts_dict)
            
            logging.info("Global configuration synced to Firebase successfully")
            return True
            
        except Exception as e:
            logging.error(f"Error syncing global config to Firebase: {e}")
            return False
    
    def sync_project_config_to_firebase(self, config: ProjectConfig) -> bool:
        """
        Sync project-specific configuration to Firebase
        """
        try:
            project_id = config.project_id
            
            # Sync project location settings
            location_dict = {
                'rawLocation': config.location.raw_location,
                'apolloLocationIds': config.location.apollo_location_ids,
                'useLlmParsing': config.location.use_llm_parsing
            }
            self.db.collection('settings').document(f'project_{project_id}_location').set(location_dict)
            
            # Sync project override settings
            project_settings_dict = {
                'projectId': project_id,
                'useGlobalLeadFilter': config.use_global_lead_filter,
                'useGlobalJobRoles': config.use_global_job_roles,
                'useGlobalEnrichment': config.use_global_enrichment,
                'useGlobalEmailGeneration': config.use_global_email_generation,
                'useGlobalScheduling': config.use_global_scheduling
            }
            
            # Add overrides if they exist
            if not config.use_global_lead_filter and config.lead_filter:
                project_settings_dict.update({
                    'onePersonPerCompany': config.lead_filter.one_person_per_company,
                    'requireEmail': config.lead_filter.require_email,
                    'excludeBlacklisted': config.lead_filter.exclude_blacklisted,
                    'minCompanySize': config.lead_filter.min_company_size,
                    'maxCompanySize': config.lead_filter.max_company_size
                })
            
            if not config.use_global_scheduling and config.scheduling:
                project_settings_dict.update({
                    'followupDelayDays': config.scheduling.followup_delay_days,
                    'maxFollowups': config.scheduling.max_followups,
                    'dailyEmailLimit': config.scheduling.daily_email_limit,
                    'rateLimitDelaySeconds': config.scheduling.rate_limit_delay_seconds,
                    'workingHoursStart': config.scheduling.working_hours_start,
                    'workingHoursEnd': config.scheduling.working_hours_end,
                    'workingDays': config.scheduling.working_days,
                    'timezone': config.scheduling.timezone
                })
            
            self.db.collection('settings').document(f'project_{project_id}').set(project_settings_dict)
            
            # Sync project job roles if overridden
            if not config.use_global_job_roles and config.job_roles:
                job_roles_dict = {
                    'projectId': project_id,
                    'useGlobalJobRoles': False,
                    'targetRoles': [role.value for role in config.job_roles.target_roles],
                    'customRoles': config.job_roles.custom_roles
                }
                self.db.collection('settings').document(f'project_{project_id}_jobRoles').set(job_roles_dict)
            
            # Sync project prompts if overridden
            if not config.use_global_email_generation and config.email_generation:
                prompts_dict = {
                    'projectId': project_id,
                    'useGlobalPrompts': False,
                    'outreachPrompt': config.email_generation.outreach_prompt,
                    'followupPrompt': config.email_generation.followup_prompt
                }
                self.db.collection('prompts').document(f'project_{project_id}').set(prompts_dict)
            
            # Sync project enrichment if overridden
            if not config.use_global_enrichment and config.enrichment:
                enrichment_dict = {
                    'projectId': project_id,
                    'enabled': config.enrichment.enabled,
                    'maxRetries': config.enrichment.max_retries,
                    'timeoutSeconds': config.enrichment.timeout_seconds,
                    'promptTemplate': config.enrichment.prompt_template
                }
                self.db.collection('settings').document(f'project_{project_id}_enrichment').set(enrichment_dict)
            
            logging.info(f"Project {project_id} configuration synced to Firebase successfully")
            return True
            
        except Exception as e:
            logging.error(f"Error syncing project config to Firebase: {e}")
            return False
    
    def load_global_config_from_firebase(self) -> GlobalConfig:
        """
        Load global configuration from Firebase
        """
        try:
            config = GlobalConfig()
            
            # Load API Keys
            api_keys_doc = self.db.collection('settings').document('apiKeys').get()
            if api_keys_doc.exists:
                api_data = api_keys_doc.to_dict()
                config.api_keys = ApiKeysConfig(
                    openai_api_key=api_data.get('openaiApiKey', ''),
                    apollo_api_key=api_data.get('apolloApiKey', ''),
                    apifi_api_key=api_data.get('apifiApiKey', ''),
                    perplexity_api_key=api_data.get('perplexityApiKey', '')
                )
            
            # Load SMTP Settings
            smtp_doc = self.db.collection('settings').document('smtp').get()
            if smtp_doc.exists:
                smtp_data = smtp_doc.to_dict()
                config.smtp = SmtpConfig(
                    host=smtp_data.get('host', 'smtp.gmail.com'),
                    port=smtp_data.get('port', 587),
                    secure=smtp_data.get('secure', False),
                    username=smtp_data.get('username', ''),
                    password=smtp_data.get('password', ''),
                    from_email=smtp_data.get('fromEmail', ''),
                    from_name=smtp_data.get('fromName', ''),
                    reply_to_email=smtp_data.get('replyToEmail')
                )
            
            # Load Global Settings
            global_doc = self.db.collection('settings').document('global').get()
            if global_doc.exists:
                global_data = global_doc.to_dict()
                
                config.scheduling = SchedulingConfig(
                    followup_delay_days=global_data.get('followupDelayDays', 7),
                    max_followups=global_data.get('maxFollowups', 3),
                    daily_email_limit=global_data.get('dailyEmailLimit', 50),
                    rate_limit_delay_seconds=global_data.get('rateLimitDelaySeconds', 60),
                    working_hours_start=global_data.get('workingHoursStart', 9),
                    working_hours_end=global_data.get('workingHoursEnd', 17),
                    working_days=global_data.get('workingDays', [0, 1, 2, 3, 4]),
                    timezone=global_data.get('timezone', 'UTC')
                )
                
                config.lead_filter = LeadFilterConfig(
                    one_person_per_company=global_data.get('onePersonPerCompany', True),
                    require_email=global_data.get('requireEmail', True),
                    exclude_blacklisted=global_data.get('excludeBlacklisted', True),
                    min_company_size=global_data.get('minCompanySize'),
                    max_company_size=global_data.get('maxCompanySize')
                )
            
            # Load Job Roles
            job_roles_doc = self.db.collection('settings').document('jobRoles').get()
            if job_roles_doc.exists:
                job_data = job_roles_doc.to_dict()
                target_roles = []
                for role_str in job_data.get('targetRoles', []):
                    try:
                        role = JobRole(role_str)
                        target_roles.append(role)
                    except ValueError:
                        # Skip invalid roles
                        pass
                
                config.job_roles = JobRoleConfig(
                    target_roles=target_roles,
                    custom_roles=job_data.get('customRoles', [])
                )
            
            # Load Enrichment Config
            enrichment_doc = self.db.collection('settings').document('enrichment').get()
            if enrichment_doc.exists:
                enrich_data = enrichment_doc.to_dict()
                config.enrichment = EnrichmentConfig(
                    enabled=enrich_data.get('enabled', True),
                    max_retries=enrich_data.get('maxRetries', 3),
                    timeout_seconds=enrich_data.get('timeoutSeconds', 30),
                    prompt_template=enrich_data.get('promptTemplate', config.enrichment.prompt_template)
                )
            
            # Load Email Generation Config
            email_gen_doc = self.db.collection('settings').document('emailGeneration').get()
            if email_gen_doc.exists:
                email_data = email_gen_doc.to_dict()
                config.email_generation.model = email_data.get('model', 'gpt-4')
                config.email_generation.max_tokens = email_data.get('maxTokens', 500)
                config.email_generation.temperature = email_data.get('temperature', 0.7)
            
            # Load Global Prompts
            prompts_doc = self.db.collection('prompts').document('global').get()
            if prompts_doc.exists:
                prompts_data = prompts_doc.to_dict()
                config.email_generation.outreach_prompt = prompts_data.get('outreachPrompt', config.email_generation.outreach_prompt)
                config.email_generation.followup_prompt = prompts_data.get('followupPrompt', config.email_generation.followup_prompt)
            
            logging.info("Global configuration loaded from Firebase successfully")
            return config
            
        except Exception as e:
            logging.error(f"Error loading global config from Firebase: {e}")
            return GlobalConfig()  # Return default config
    
    def load_project_config_from_firebase(self, project_id: str) -> ProjectConfig:
        """
        Load project-specific configuration from Firebase
        """
        try:
            config = ProjectConfig(project_id=project_id)
            
            # Load project location settings
            location_doc = self.db.collection('settings').document(f'project_{project_id}_location').get()
            if location_doc.exists:
                location_data = location_doc.to_dict()
                config.location = LocationConfig(
                    raw_location=location_data.get('rawLocation', ''),
                    apollo_location_ids=location_data.get('apolloLocationIds', []),
                    use_llm_parsing=location_data.get('useLlmParsing', True)
                )
            
            # Load project settings
            project_doc = self.db.collection('settings').document(f'project_{project_id}').get()
            if project_doc.exists:
                project_data = project_doc.to_dict()
                
                config.use_global_lead_filter = project_data.get('useGlobalLeadFilter', True)
                config.use_global_job_roles = project_data.get('useGlobalJobRoles', True)
                config.use_global_enrichment = project_data.get('useGlobalEnrichment', True)
                config.use_global_email_generation = project_data.get('useGlobalEmailGeneration', True)
                config.use_global_scheduling = project_data.get('useGlobalScheduling', True)
                
                # Load overrides if they exist
                if not config.use_global_lead_filter:
                    config.lead_filter = LeadFilterConfig(
                        one_person_per_company=project_data.get('onePersonPerCompany', True),
                        require_email=project_data.get('requireEmail', True),
                        exclude_blacklisted=project_data.get('excludeBlacklisted', True),
                        min_company_size=project_data.get('minCompanySize'),
                        max_company_size=project_data.get('maxCompanySize')
                    )
                
                if not config.use_global_scheduling:
                    config.scheduling = SchedulingConfig(
                        followup_delay_days=project_data.get('followupDelayDays', 7),
                        max_followups=project_data.get('maxFollowups', 3),
                        daily_email_limit=project_data.get('dailyEmailLimit', 50),
                        rate_limit_delay_seconds=project_data.get('rateLimitDelaySeconds', 60),
                        working_hours_start=project_data.get('workingHoursStart', 9),
                        working_hours_end=project_data.get('workingHoursEnd', 17),
                        working_days=project_data.get('workingDays', [0, 1, 2, 3, 4]),
                        timezone=project_data.get('timezone', 'UTC')
                    )
            
            # Load project job roles if overridden
            if not config.use_global_job_roles:
                job_roles_doc = self.db.collection('settings').document(f'project_{project_id}_jobRoles').get()
                if job_roles_doc.exists:
                    job_data = job_roles_doc.to_dict()
                    target_roles = []
                    for role_str in job_data.get('targetRoles', []):
                        try:
                            role = JobRole(role_str)
                            target_roles.append(role)
                        except ValueError:
                            pass
                    
                    config.job_roles = JobRoleConfig(
                        target_roles=target_roles,
                        custom_roles=job_data.get('customRoles', [])
                    )
            
            # Load project prompts if overridden
            if not config.use_global_email_generation:
                prompts_doc = self.db.collection('prompts').document(f'project_{project_id}').get()
                if prompts_doc.exists:
                    prompts_data = prompts_doc.to_dict()
                    config.email_generation = EmailGenerationConfig()
                    config.email_generation.outreach_prompt = prompts_data.get('outreachPrompt', config.email_generation.outreach_prompt)
                    config.email_generation.followup_prompt = prompts_data.get('followupPrompt', config.email_generation.followup_prompt)
            
            # Load project enrichment if overridden
            if not config.use_global_enrichment:
                enrichment_doc = self.db.collection('settings').document(f'project_{project_id}_enrichment').get()
                if enrichment_doc.exists:
                    enrich_data = enrichment_doc.to_dict()
                    config.enrichment = EnrichmentConfig(
                        enabled=enrich_data.get('enabled', True),
                        max_retries=enrich_data.get('maxRetries', 3),
                        timeout_seconds=enrich_data.get('timeoutSeconds', 30),
                        prompt_template=enrich_data.get('promptTemplate', config.enrichment.prompt_template)
                    )
            
            logging.info(f"Project {project_id} configuration loaded from Firebase successfully")
            return config
            
        except Exception as e:
            logging.error(f"Error loading project config from Firebase: {e}")
            return ProjectConfig(project_id=project_id)  # Return default config


# Global instance - initialized lazily
config_sync = None

def get_config_sync():
    """Get or create the global config sync instance"""
    global config_sync
    if config_sync is None:
        config_sync = ConfigSyncManager()
    return config_sync 