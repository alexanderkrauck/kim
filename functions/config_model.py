"""
Configuration Model - Single Source of Truth
Defines all configuration schemas with validation rules and defaults
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union, Literal
from enum import Enum
import re


class EmailStatus(Enum):
    NEW = "new"
    EMAILED = "emailed"
    RESPONDED = "responded"
    BOUNCED = "bounced"
    BLACKLISTED = "blacklisted"


class EmailType(Enum):
    OUTREACH = "outreach"
    FOLLOWUP = "followup"
    RESPONSE = "response"


class JobRole(Enum):
    CEO = "CEO"
    CTO = "CTO"
    FOUNDER = "Founder"
    COFOUNDER = "Co-Founder"
    PRESIDENT = "President"
    VP_ENGINEERING = "VP Engineering"
    VP_TECHNOLOGY = "VP Technology"
    HEAD_OF_ENGINEERING = "Head of Engineering"
    ENGINEERING_MANAGER = "Engineering Manager"
    TECHNICAL_DIRECTOR = "Technical Director"
    # New default job roles as shown in the image
    HUMAN_RESOURCES = "Human Resources"
    OFFICE_MANAGER = "Office Manager"
    SECRETARY = "Secretary"
    ASSISTANT = "Assistant"
    ASSISTANT_MANAGER = "Assistant Manager"
    MANAGER = "Manager"
    SOCIAL_MEDIA = "Social Media"


@dataclass
class SmtpConfig:
    """SMTP configuration for email sending"""
    host: str = "smtp.gmail.com"
    port: int = 587
    secure: bool = False  # True for 465, False for other ports
    username: str = ""
    password: str = ""
    from_email: str = ""
    from_name: str = ""
    reply_to_email: Optional[str] = None
    
    def validate(self) -> bool:
        """Validate SMTP configuration"""
        if not self.host or not self.username or not self.password:
            return False
        if not self.from_email or not self._is_valid_email(self.from_email):
            return False
        if self.reply_to_email and not self._is_valid_email(self.reply_to_email):
            return False
        return True
    
    @staticmethod
    def _is_valid_email(email: str) -> bool:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None


@dataclass
class ApiKeysConfig:
    """API keys configuration"""
    openai_api_key: str = ""
    apollo_api_key: str = ""
    apifi_api_key: str = ""
    perplexity_api_key: str = ""
    
    def validate(self) -> bool:
        """Validate that required API keys are present"""
        # At minimum, we need OpenAI and Apollo for basic functionality
        return bool(self.openai_api_key and self.apollo_api_key)


@dataclass
class LeadFilterConfig:
    """Configuration for lead filtering"""
    one_person_per_company: bool = True
    require_email: bool = True
    exclude_blacklisted: bool = True
    min_company_size: Optional[int] = None
    max_company_size: Optional[int] = None
    
    def validate(self) -> bool:
        """Validate lead filter configuration"""
        if self.min_company_size and self.max_company_size:
            return self.min_company_size <= self.max_company_size
        return True


@dataclass
class LocationConfig:
    """Location configuration for Apollo API"""
    raw_location: str = ""
    apollo_location_ids: List[str] = field(default_factory=list)
    use_llm_parsing: bool = True
    
    def validate(self) -> bool:
        """Validate location configuration"""
        if self.use_llm_parsing:
            return bool(self.raw_location.strip())
        else:
            return bool(self.apollo_location_ids)


@dataclass
class JobRoleConfig:
    """Job role configuration for lead finding"""
    target_roles: List[JobRole] = field(default_factory=lambda: [
        JobRole.HUMAN_RESOURCES, JobRole.OFFICE_MANAGER, JobRole.SECRETARY,
        JobRole.ASSISTANT, JobRole.ASSISTANT_MANAGER, JobRole.MANAGER, JobRole.SOCIAL_MEDIA
    ])
    custom_roles: List[str] = field(default_factory=list)
    
    def get_all_roles(self) -> List[str]:
        """Get all roles as strings"""
        roles = [role.value for role in self.target_roles]
        roles.extend(self.custom_roles)
        return roles
    
    def validate(self) -> bool:
        """Validate job role configuration"""
        return len(self.target_roles) > 0 or len(self.custom_roles) > 0


@dataclass
class EnrichmentConfig:
    """Configuration for lead enrichment using Perplexity"""
    enabled: bool = True
    max_retries: int = 3
    timeout_seconds: int = 30
    prompt_template: str = """
Research the following company and person for a business outreach email:

Company: {company}
Person: {name} ({title})

Please provide:
1. Brief company overview and recent news
2. Person's background and role
3. Any recent achievements or initiatives
4. Relevant industry trends affecting them

Keep the response concise and professional.
"""
    
    def validate(self) -> bool:
        """Validate enrichment configuration"""
        return (self.max_retries > 0 and 
                self.timeout_seconds > 0 and 
                "{company}" in self.prompt_template and 
                "{name}" in self.prompt_template)


@dataclass
class EmailGenerationConfig:
    """Configuration for email generation using OpenAI"""
    model: str = "gpt-4"
    max_tokens: int = 500
    temperature: float = 0.7
    outreach_prompt: str = """
You are writing a professional outreach email for a business proposal.

Context:
- Project: {project_name}
- Project Description: {project_description}
- Target: {name} at {company}
- Enrichment Data: {enrichment_data}
- Email Considerations: {email_considerations}

Write a personalized, professional email that:
1. Is concise (under 150 words)
2. Clearly states the value proposition
3. Includes a specific call to action
4. Uses the enrichment data naturally
5. Feels personal, not template-like

Subject line and email body:
"""
    
    followup_prompt: str = """
You are writing a follow-up email for a business proposal.

Context:
- Previous email sent {days_ago} days ago
- Project: {project_name}
- Target: {name} at {company}
- Original email: {original_email}
- Followup Considerations: {followup_considerations}

Write a brief, professional follow-up that:
1. Acknowledges the previous email
2. Adds new value or perspective
3. Is even more concise (under 100 words)
4. Maintains professionalism
5. Includes a clear call to action

Subject line and email body:
"""
    
    def validate(self) -> bool:
        """Validate email generation configuration"""
        return (self.max_tokens > 0 and 
                0 <= self.temperature <= 2 and
                "{project_name}" in self.outreach_prompt and
                "{name}" in self.outreach_prompt)


@dataclass
class SchedulingConfig:
    """Configuration for email scheduling and follow-ups"""
    followup_delay_days: int = 7
    max_followups: int = 3
    daily_email_limit: int = 50
    rate_limit_delay_seconds: int = 60
    working_hours_start: int = 9  # 9 AM
    working_hours_end: int = 17   # 5 PM
    working_days: List[int] = field(default_factory=lambda: [0, 1, 2, 3, 4])  # Mon-Fri
    timezone: str = "UTC"
    
    def validate(self) -> bool:
        """Validate scheduling configuration"""
        return (self.followup_delay_days > 0 and 
                self.max_followups >= 0 and
                self.daily_email_limit > 0 and
                0 <= self.working_hours_start < 24 and
                0 <= self.working_hours_end < 24 and
                self.working_hours_start < self.working_hours_end and
                all(0 <= day <= 6 for day in self.working_days))


@dataclass
class GlobalConfig:
    """Global configuration that serves as defaults"""
    smtp: SmtpConfig = field(default_factory=SmtpConfig)
    api_keys: ApiKeysConfig = field(default_factory=ApiKeysConfig)
    lead_filter: LeadFilterConfig = field(default_factory=LeadFilterConfig)
    job_roles: JobRoleConfig = field(default_factory=JobRoleConfig)
    enrichment: EnrichmentConfig = field(default_factory=EnrichmentConfig)
    email_generation: EmailGenerationConfig = field(default_factory=EmailGenerationConfig)
    scheduling: SchedulingConfig = field(default_factory=SchedulingConfig)
    
    def validate(self) -> bool:
        """Validate entire global configuration"""
        return (self.smtp.validate() and
                self.api_keys.validate() and
                self.lead_filter.validate() and
                self.job_roles.validate() and
                self.enrichment.validate() and
                self.email_generation.validate() and
                self.scheduling.validate())


@dataclass
class ProjectConfig:
    """Project-specific configuration that can override global settings"""
    project_id: str
    location: LocationConfig = field(default_factory=LocationConfig)
    
    # Override flags
    use_global_lead_filter: bool = True
    use_global_job_roles: bool = True
    use_global_enrichment: bool = True
    use_global_email_generation: bool = True
    use_global_scheduling: bool = True
    
    # Project-specific overrides (only used if use_global_* is False)
    lead_filter: Optional[LeadFilterConfig] = None
    job_roles: Optional[JobRoleConfig] = None
    enrichment: Optional[EnrichmentConfig] = None
    email_generation: Optional[EmailGenerationConfig] = None
    scheduling: Optional[SchedulingConfig] = None
    
    def get_effective_config(self, global_config: GlobalConfig) -> 'EffectiveProjectConfig':
        """Get the effective configuration by merging with global config"""
        return EffectiveProjectConfig(
            project_id=self.project_id,
            location=self.location,
            lead_filter=global_config.lead_filter if self.use_global_lead_filter else self.lead_filter,
            job_roles=global_config.job_roles if self.use_global_job_roles else self.job_roles,
            enrichment=global_config.enrichment if self.use_global_enrichment else self.enrichment,
            email_generation=global_config.email_generation if self.use_global_email_generation else self.email_generation,
            scheduling=global_config.scheduling if self.use_global_scheduling else self.scheduling
        )
    
    def validate(self) -> bool:
        """Validate project configuration"""
        if not self.location.validate():
            return False
        
        # Validate overrides if they're being used
        if not self.use_global_lead_filter and self.lead_filter and not self.lead_filter.validate():
            return False
        if not self.use_global_job_roles and self.job_roles and not self.job_roles.validate():
            return False
        if not self.use_global_enrichment and self.enrichment and not self.enrichment.validate():
            return False
        if not self.use_global_email_generation and self.email_generation and not self.email_generation.validate():
            return False
        if not self.use_global_scheduling and self.scheduling and not self.scheduling.validate():
            return False
        
        return True


@dataclass
class EffectiveProjectConfig:
    """The effective configuration for a project after merging with global config"""
    project_id: str
    location: LocationConfig
    lead_filter: LeadFilterConfig
    job_roles: JobRoleConfig
    enrichment: EnrichmentConfig
    email_generation: EmailGenerationConfig
    scheduling: SchedulingConfig


# Default configuration instances
DEFAULT_GLOBAL_CONFIG = GlobalConfig()

def get_default_config() -> GlobalConfig:
    """Get the default global configuration"""
    return DEFAULT_GLOBAL_CONFIG 