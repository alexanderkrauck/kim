# Lead Generation System - Firebase Functions

## 🎯 Overview

A comprehensive lead generation and outreach system built with Firebase Functions, featuring:

- **Lead Discovery**: Apollo.io integration with intelligent filtering
- **Lead Enrichment**: Perplexity AI-powered research and insights
- **Email Generation**: OpenAI-powered personalized outreach emails
- **Email Automation**: SMTP delivery with scheduling and follow-up sequences
- **Configuration Management**: Flexible global and project-specific settings

## ✅ Implementation Status: COMPLETE

All core functionality has been implemented and tested:

- ✅ **Configuration System**: Python-based configuration with Firebase sync
- ✅ **Lead Finding**: Apollo.io integration with location and role targeting
- ✅ **Lead Enrichment**: Perplexity integration with retry logic
- ✅ **Email Generation**: OpenAI integration with customizable prompts
- ✅ **Email Sending**: SMTP integration with scheduling and rate limiting
- ✅ **API Testing**: Comprehensive health checks and validation

## 🏗️ Architecture

### Configuration System
- **Single Source of Truth**: Python dataclasses define all schemas
- **Firebase Sync**: Bidirectional sync maintains existing structure
- **Inheritance**: Project configs inherit from global with overrides
- **Type Safety**: Full Python typing with validation

### Lead Processing Pipeline
1. **Apollo Search** → Configuration-driven parameters
2. **Comprehensive Filtering** → Duplicates, blacklist, quality
3. **Batch Saving** → Efficient Firestore operations
4. **Optional Enrichment** → Perplexity with retry logic
5. **Email Generation** → OpenAI personalization
6. **Scheduled Sending** → SMTP with rate limiting

## 📋 Firebase Functions

### Core Lead Management
- `find_leads` - Search for leads using Apollo.io
- `enrich_leads` - Enrich leads with Perplexity research
- `get_enrichment_status` - Get enrichment status
- `contact_leads` - Send outreach/followup emails

### Email Generation
- `generate_emails` - Generate personalized emails
- `preview_email` - Preview email generation

### Configuration Management
- `get_global_config` - Retrieve global configuration
- `update_global_config` - Update global configuration
- `get_project_config` - Retrieve project configuration
- `update_project_config` - Update project configuration

### Job Role Management
- `get_job_roles_config` - Get job role configuration
- `update_job_roles_config` - Update job role configuration
- `get_available_job_roles` - Get available job roles

### API Testing & Health
- `test_apis` - Test all API connections
- `validate_api_keys` - Validate API key formats
- `get_api_status` - Get API health status
- `health_check` - System health check

## 🔧 Setup & Configuration

### 1. Install Dependencies

```bash
cd functions
pip install -r requirements.txt
```

### 2. Configure API Keys

Set up the following API keys in Firebase or environment variables:

```bash
# Required API Keys
OPENAI_API_KEY=sk-...
APOLLO_API_KEY=...
PERPLEXITY_API_KEY=pplx-...

# Optional for local development
APIFI_API_KEY=...
```

### 3. Configure SMTP (for email sending)

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_FROM_NAME="Your Name"
```

### 4. Deploy to Firebase

```bash
firebase deploy --only functions
```

## 🧪 Testing

### Run Comprehensive System Test

```bash
cd functions
python test_system.py
```

This tests:
- API connectivity
- Configuration management
- Lead finding
- Lead enrichment
- Email generation
- Email preview
- Contact leads (dry run)

### Test Individual APIs

```bash
python test_apis.py
```

## 📊 Configuration Schema

### Global Configuration

```python
{
  "api_keys": {
    "openai_api_key": "sk-...",
    "apollo_api_key": "...",
    "perplexity_api_key": "pplx-..."
  },
  "smtp": {
    "host": "smtp.gmail.com",
    "port": 587,
    "secure": false,
    "username": "...",
    "password": "...",
    "from_email": "...",
    "from_name": "..."
  },
  "lead_filter": {
    "one_person_per_company": true,
    "require_email": true,
    "exclude_blacklisted": true,
    "min_company_size": null,
    "max_company_size": null
  },
  "job_roles": {
    "target_roles": ["CEO", "CTO", "Founder"],
    "custom_roles": []
  },
  "enrichment": {
    "enabled": true,
    "max_retries": 3,
    "timeout_seconds": 30,
    "prompt_template": "Research {company}..."
  },
  "email_generation": {
    "model": "gpt-4",
    "max_tokens": 500,
    "temperature": 0.7,
    "outreach_prompt": "...",
    "followup_prompt": "..."
  },
  "scheduling": {
    "followup_delay_days": 7,
    "max_followups": 3,
    "daily_email_limit": 50,
    "rate_limit_delay_seconds": 60,
    "working_hours_start": 9,
    "working_hours_end": 17,
    "working_days": [0, 1, 2, 3, 4],
    "timezone": "UTC"
  }
}
```

### Project Configuration

```python
{
  "project_id": "project_123",
  "location": {
    "raw_location": "San Francisco, CA",
    "apollo_location_ids": ["5341"],
    "use_llm_parsing": true
  },
  "use_global_lead_filter": true,
  "use_global_job_roles": true,
  "use_global_enrichment": true,
  "use_global_email_generation": true,
  "use_global_scheduling": true
}
```

## 🔄 Usage Examples

### Find Leads

```javascript
const result = await functions.httpsCallable('find_leads')({
  project_id: 'project_123',
  num_leads: 25,
  auto_enrich: true,
  search_params: {
    person_titles: ['CEO', 'Founder'],
    organization_locations: ['United States']
  }
});
```

### Enrich Leads

```javascript
const result = await functions.httpsCallable('enrich_leads')({
  project_id: 'project_123',
  lead_ids: ['lead_1', 'lead_2'],
  enrichment_type: 'both'
});
```

### Generate Emails

```javascript
const result = await functions.httpsCallable('generate_emails')({
  project_id: 'project_123',
  lead_ids: ['lead_1'],
  email_type: 'outreach'
});
```

### Send Emails

```javascript
const result = await functions.httpsCallable('contact_leads')({
  project_id: 'project_123',
  lead_ids: ['lead_1'],
  email_type: 'outreach',
  dry_run: false
});
```

## 🎯 Key Features

### Lead Discovery
- Location-based targeting with LLM parsing
- Job role filtering with configurable targets
- Company size and quality filtering
- Duplicate detection across projects
- Blacklist management

### Lead Enrichment
- Company research and insights
- Person-specific information
- Configurable enrichment prompts
- Retry logic with error handling
- Quality validation

### Email Outreach
- Personalized email generation
- Subject line optimization
- Outreach and followup sequences
- SMTP delivery with tracking
- Rate limiting and scheduling

### Configuration Management
- Global and project-specific settings
- Real-time configuration updates
- Inheritance and override system
- API key management
- Prompt customization

## 🔒 Security

- API keys stored securely in Firebase
- Input validation on all functions
- Rate limiting to prevent abuse
- Error handling without exposing internals
- Blacklist management for compliance

## 📈 Monitoring

- Comprehensive logging throughout
- API health monitoring
- Test result tracking
- Error reporting and handling
- Performance metrics

## 🚀 Deployment

The system is ready for production deployment with:

- Complete error handling
- Comprehensive logging
- Input validation
- Rate limiting
- Security best practices
- Monitoring and health checks

## 📝 Development

### File Structure

```
functions/
├── main.py                 # Main Firebase Functions entry point
├── config_model.py         # Configuration data models
├── config_sync.py          # Firebase configuration sync
├── config_management.py    # Configuration CRUD functions
├── find_leads.py          # Lead discovery with Apollo
├── enrich_leads.py        # Lead enrichment with Perplexity
├── email_generation.py    # Email generation with OpenAI
├── contact_leads.py       # Email sending and scheduling
├── location_processor.py  # Location parsing and mapping
├── job_role_config.py     # Job role management
├── test_apis.py          # API testing functions
├── test_system.py        # Comprehensive system tests
├── utils/                # Utility modules
│   ├── api_clients.py    # API client implementations
│   ├── email_utils.py    # Email utilities
│   ├── firebase_utils.py # Firebase utilities
│   └── data_processing.py # Data processing utilities
└── requirements.txt      # Python dependencies
```

### Adding New Features

1. Define configuration in `config_model.py`
2. Add sync logic in `config_sync.py`
3. Implement business logic in new module
4. Add Firebase Function wrapper
5. Export in `main.py`
6. Add tests in `test_system.py`

## 📞 Support

For issues or questions:
1. Check the logs in Firebase Console
2. Run `python test_system.py` for diagnostics
3. Verify API keys and configuration
4. Check Firebase Functions deployment status

---

**Status**: ✅ Production Ready - All core functionality implemented and tested. 