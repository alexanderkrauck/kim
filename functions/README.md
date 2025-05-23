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

# Lead Generation Firebase Functions

A comprehensive lead generation and outreach system built with Firebase Functions, integrating Apollo.io for lead discovery, Perplexity for lead enrichment, and OpenAI for personalized email generation.

## 🚀 Features

### Core Functions
- **Lead Discovery** (`find_leads.py`) - Find potential leads using Apollo.io
- **Lead Enrichment** - Research companies and contacts using Perplexity
- **Email Generation** (`contact_leads.py`) - Create personalized outreach emails with OpenAI
- **Email Automation** - Send and track email campaigns

### API Integrations
- **Apollo.io** - Lead discovery and contact search
- **Perplexity** - Company and person research
- **OpenAI** - Email content generation
- **SMTP** - Email delivery

### Production Features
- **API Testing** (`test_apis.py`) - Production API health monitoring and testing
- **Error Handling** - Comprehensive error handling and logging
- **Rate Limiting** - Built-in rate limiting for API calls
- **Data Validation** - Input validation and data processing
- **Firestore Integration** - Data persistence and management

## 📁 Project Structure

```
├── main.py                 # Main function router
├── find_leads.py          # Lead discovery function
├── contact_leads.py       # Email generation and outreach
├── test_apis.py          # Production API testing functions
├── utils/
│   ├── api_clients.py     # API client implementations
│   ├── api_testing.py     # Production API testing utilities
│   ├── firebase_utils.py  # Firebase and configuration utilities
│   ├── email_utils.py     # Email sending utilities
│   └── data_processing.py # Data validation and processing
├── experiments/           # Development and testing scripts
└── requirements.txt       # Python dependencies
```

## 🔧 Setup

### 1. Prerequisites
- Python 3.9+
- Firebase CLI
- API keys for Apollo.io, Perplexity, and OpenAI

### 2. Installation
```bash
# Clone and setup
git clone <repository>
cd functions
pip install -r requirements.txt

# Setup environment
cp env.example .env
# Edit .env with your API keys
```

### 3. API Configuration

#### Apollo.io
- Enhanced plan required for API access
- Create API key with "People Search" scope enabled
- Set as master key for full access

#### Perplexity
- Valid API key with credits
- Used for company and person research

#### OpenAI
- Valid API key with model access
- Used for email content generation

### 4. Firebase Setup
```bash
# Initialize Firebase
firebase init functions

# Deploy functions
firebase deploy --only functions
```

## 🧪 API Testing

### Production API Testing
The system includes comprehensive API testing capabilities for production use:

```python
# Test all APIs
from utils import test_all_apis, get_api_keys

api_keys = get_api_keys()
results = test_all_apis(api_keys, minimal=True)
```

### Firebase Functions for API Testing

#### `test_apis` Function
Test API connectivity and health:
```javascript
// Test all APIs with minimal usage
const result = await testApis({
  test_type: 'all',
  minimal: true,
  save_results: true
});
```

#### `validate_api_keys` Function
Validate API key formats without making calls:
```javascript
const validation = await validateApiKeys({});
```

#### `get_api_status` Function
Get current API status and recent test history:
```javascript
const status = await getApiStatus({
  include_recent_tests: true,
  limit: 10
});
```

### Development Testing
For development and debugging, use the scripts in `experiments/`:

```bash
# Test individual APIs
python experiments/test_new_apollo_key.py
python experiments/test_perplexity_api.py
python experiments/test_openai_api.py

# Test complete workflow
python experiments/test_all_apis.py

# Test production utilities
python experiments/test_production_utils.py
```

## 📊 Usage

### 1. Find Leads
```javascript
const result = await findLeads({
  project_id: 'your-project-id',
  num_leads: 25,
  search_params: {
    job_titles: ['CEO', 'CTO', 'founder'],
    locations: ['Vienna, Austria']
  }
});
```

### 2. Contact Leads
```javascript
const result = await contactLeads({
  project_id: 'your-project-id',
  email_type: 'outreach',
  batch_size: 10
});
```

### 3. Test APIs
```javascript
// Quick health check
const health = await testApis({
  test_type: 'health'
});

// Full API testing
const fullTest = await testApis({
  test_type: 'all',
  minimal: true,
  save_results: true
});
```

## 🔍 Monitoring

### API Health Monitoring
- Real-time API status checking
- Historical test result tracking
- Credit usage monitoring
- Error rate tracking

### Logging
- Comprehensive function logging
- Error tracking and alerting
- Performance monitoring
- Usage analytics

## 🛠️ Development

### Local Development
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run local tests
python experiments/test_all_apis.py

# Start local emulator
firebase emulators:start
```

### Testing
- Unit tests for individual functions
- Integration tests for API workflows
- End-to-end testing capabilities
- Production API health monitoring

### Deployment
```bash
# Deploy all functions
firebase deploy --only functions

# Deploy specific function
firebase deploy --only functions:find_leads
```

## 📈 Best Practices

### Credit Management
- Use minimal API calls for testing
- Monitor usage across all platforms
- Implement caching where appropriate
- Set up usage alerts

### Error Handling
- Graceful degradation when APIs fail
- Comprehensive error logging
- User-friendly error messages
- Automatic retry logic

### Security
- Secure API key management
- Input validation and sanitization
- Rate limiting and abuse prevention
- Audit logging

## 🎯 Production Checklist

- [ ] All API keys configured and tested
- [ ] Firebase Functions deployed
- [ ] Error handling and logging set up
- [ ] Rate limiting implemented
- [ ] Monitoring and alerting configured
- [ ] Backup and recovery procedures
- [ ] Documentation updated
- [ ] Team training completed

## 📚 Documentation

- **API Testing Guide** - `experiments/README.md`
- **Apollo Setup Guide** - `experiments/apollo_api_key_setup_guide.md`
- **Function Documentation** - Inline documentation in each function
- **Utils Documentation** - Comprehensive utils module documentation

## 🤝 Contributing

1. Follow the existing code structure
2. Add comprehensive tests for new features
3. Update documentation
4. Test with minimal API usage
5. Ensure production readiness

## 📄 License

[Your License Here] 