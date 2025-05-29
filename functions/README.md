# Firebase Functions - Backend API

Python-based Firebase Functions providing the backend API for the lead generation system.

## 🎯 Overview

This backend handles:
- **Lead Discovery** via Apollo.io integration
- **Lead Enrichment** using Perplexity AI
- **Email Generation** with OpenAI
- **Email Delivery** via SMTP
- **Configuration Management** with Firebase sync
- **Database Maintenance** and health monitoring

## 🚀 Quick Setup

### Prerequisites
- Python 3.9+
- Firebase CLI
- API keys for external services

### Installation
```bash
cd functions
pip install -r requirements.txt

# Deploy to Firebase
firebase deploy --only functions
```

### Required API Keys
Set these in your application's Configuration tab:
- **OpenAI API Key** (for email generation)
- **Apollo.io API Key** (for lead discovery)
- **Perplexity API Key** (for lead enrichment - optional)

## 📋 Available Functions

### Lead Management
- `find_leads` - Search and save leads using Apollo.io
- `enrich_leads` - Enhance leads with Perplexity research
- `get_enrichment_status` - Check enrichment progress

### Email Operations
- `generate_emails` - Create personalized emails with OpenAI
- `preview_email` - Preview email generation
- `contact_leads` - Send emails via SMTP

### Configuration
- `get_global_config` / `update_global_config` - Global settings
- `get_project_config` / `update_project_config` - Project settings
- `get_job_roles_config` / `update_job_roles_config` - Job role settings

### Maintenance
- `database_health_check` - Check database status
- `database_initialize` - Setup default configuration
- `database_cleanup` - Remove old/deprecated data
- `database_full_maintenance` - Complete maintenance workflow

### Testing & Health
- `test_apis` - Test all external API connections
- `validate_api_keys` - Validate API key formats
- `get_api_status` - Get API health status

## 🔧 Usage Examples

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

### Generate & Send Emails
```javascript
// Generate personalized emails
await functions.httpsCallable('generate_emails')({
  project_id: 'project_123',
  lead_ids: ['lead_1'],
  email_type: 'outreach'
});

// Send emails
await functions.htttsCallable('contact_leads')({
  project_id: 'project_123',
  lead_ids: ['lead_1'],
  dry_run: false
});
```

### Configuration Management
```javascript
// Update global settings
await functions.httpsCallable('update_global_config')({
  followupDelayDays: 7,
  dailyEmailLimit: 50
});

// Update project settings
await functions.httpsCallable('update_project_config')({
  project_id: 'project_123',
  config: { location: { raw_location: 'San Francisco, CA' } }
});
```

## 🏗️ Architecture

### Configuration System
- **Python dataclasses** define all configuration schemas
- **Firebase sync** maintains data consistency
- **Inheritance model** - projects inherit from global with overrides

### Lead Processing Pipeline
1. **Apollo Search** → Find leads based on criteria
2. **Filtering & Deduplication** → Remove duplicates and apply filters
3. **Batch Saving** → Efficient Firestore operations
4. **Optional Enrichment** → Perplexity research with retry logic
5. **Email Generation** → OpenAI personalization
6. **Scheduled Delivery** → SMTP with rate limiting

### Error Handling
- Comprehensive input validation
- Graceful API failure handling
- Detailed error logging
- Retry logic for external APIs

## 🧪 Testing

### Test All APIs
```bash
cd functions
python test_apis.py
```

### Test Individual Functions
```python
# Test in Python console
from main import find_leads
result = find_leads({'project_id': 'test', 'num_leads': 5})
```

### Database Maintenance
```bash
# Health check
python run_database_maintenance.py --action health

# Cleanup (dry run)
python run_database_maintenance.py --action cleanup --dry-run

# Initialize defaults
python run_database_maintenance.py --action init
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
    "username": "...",
    "password": "..."
  },
  "lead_filter": {
    "one_person_per_company": true,
    "require_email": true,
    "exclude_blacklisted": true
  },
  "scheduling": {
    "followup_delay_days": 7,
    "max_followups": 3,
    "daily_email_limit": 50
  }
}
```

### Project Configuration
```python
{
  "project_id": "project_123",
  "location": {
    "raw_location": "San Francisco, CA",
    "apollo_location_ids": ["5341"]
  },
  "use_global_lead_filter": true,
  "use_global_email_generation": true
}
```

## 🔒 Security

- API keys stored securely in Firestore
- Input validation on all functions
- Authentication required for all operations
- Rate limiting for external API calls
- Error handling without exposing internals

## 📁 File Structure

```
functions/
├── main.py                 # Function exports
├── config_model.py         # Configuration schemas
├── config_sync.py          # Firebase sync utilities
├── find_leads.py          # Lead discovery
├── enrich_leads.py        # Lead enrichment
├── email_generation.py    # Email generation
├── contact_leads.py       # Email sending
├── database_maintenance.py # Maintenance operations
├── test_apis.py           # API testing
├── utils/                 # Utility modules
│   ├── api_clients.py     # External API clients
│   ├── firebase_utils.py  # Firebase utilities
│   └── data_processing.py # Data processing
└── requirements.txt       # Dependencies
```

## 🚀 Deployment

```bash
# Deploy all functions
firebase deploy --only functions

# Deploy specific function
firebase deploy --only functions:find_leads

# Check deployment status
firebase functions:log
```

## 📝 Development

### Adding New Functions
1. Create function in appropriate file
2. Add to `main.py` exports
3. Update this README
4. Deploy with `firebase deploy --only functions`

### Local Development
- Use `run_database_maintenance.py` for local testing
- Test API connections with `test_apis.py`
- Use Firebase emulator for local development

## 📞 Support

- Check Firebase Functions logs for errors
- Run health checks for system status
- Review [Database Maintenance Guide](DATABASE_MAINTENANCE_GUIDE.md) for operational procedures

---

**Status**: ✅ Production-ready with 24 deployed functions 