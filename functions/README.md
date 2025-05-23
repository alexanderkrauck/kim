# Firebase Functions Backend

This directory contains the Firebase Functions backend for the automated outreach system. It provides API endpoints for lead generation, enrichment, and email outreach.

## Architecture

### Core Functions
- `find_leads.py` - Apollo.io integration for lead discovery and Perplexity enrichment
- `contact_leads.py` - Email outreach and follow-up automation
- `main.py` - Additional utility functions and Firebase triggers

### Utilities (`utils/`)
- `api_clients.py` - API clients for Apollo, Perplexity, and OpenAI
- `firebase_utils.py` - Firebase/Firestore helper functions
- `email_utils.py` - SMTP email service and utilities
- `data_processing.py` - Lead data validation and processing

### Development (`experiments/`)
- Interactive Jupyter notebooks for API testing and development
- Environment-based development workflow

## Setup

### 1. Install Dependencies

```bash
# Production dependencies
pip install -r requirements.txt

# Development dependencies (includes Jupyter)
pip install -r requirements-dev.txt
```

### 2. Environment Configuration

```bash
# Copy environment template
cp env.example .env

# Edit .env with your actual API keys
# - OPENAI_API_KEY
# - APOLLO_API_KEY  
# - PERPLEXITY_API_KEY
# - APIFI_API_KEY
```

### 3. Quick Setup Script

```bash
# Run automated setup
python setup_dev.py

# Test API connections
python setup_dev.py test
```

## Development Workflow

### Interactive Development
1. Start Jupyter Lab: `jupyter lab`
2. Open `experiments/api_testing.ipynb`
3. Test API integrations interactively
4. Develop and debug before implementing in functions

### Local Testing
- Functions use environment variables when `DEBUG=true`
- Production uses Firebase settings storage
- Seamless transition between local and production

## API Integration

### Apollo.io
- Lead search and discovery
- Company and contact information
- Configurable search parameters

### Perplexity
- Company research and enrichment
- Recent news and insights
- Contextual lead intelligence

### OpenAI
- Personalized email generation
- Custom prompt support
- Outreach and follow-up content

## Function Endpoints

### `find_leads`
```python
# Find and enrich leads for a project
{
    "project_id": "string",
    "num_leads": 25,  # optional
    "search_params": {}  # optional
}
```

### `contact_leads`
```python
# Send outreach or follow-up emails
{
    "project_id": "string",
    "email_type": "auto",  # 'outreach', 'followup', 'auto'
    "lead_ids": [],  # optional - specific leads
    "dry_run": false  # optional - test mode
}
```

## Data Flow

1. **Lead Discovery**: Apollo.io search → Lead processing → Duplicate filtering
2. **Enrichment**: Perplexity research → Company insights → Data enhancement
3. **Storage**: Firestore batch write → Project updates → Lead tracking
4. **Outreach**: Lead eligibility → Email generation → SMTP delivery → Status updates

## Security

- API keys stored securely in Firebase or environment variables
- Authentication required for all function calls
- Blacklist filtering for compliance
- Rate limiting and error handling

## Deployment

```bash
# Deploy all functions
firebase deploy --only functions

# Deploy specific function
firebase deploy --only functions:find_leads
```

## Monitoring

- Cloud Functions logs in Firebase Console
- Error tracking and performance monitoring
- Email delivery status tracking
- Lead conversion analytics

## Development Best Practices

1. **Test APIs First**: Use experiments folder for interactive development
2. **Environment Separation**: Local .env for development, Firebase for production  
3. **Error Handling**: Comprehensive logging and graceful failure handling
4. **Data Validation**: Input validation and sanitization
5. **Rate Limiting**: Respect API limits and implement backoff strategies 