# API Testing - Experiments

This directory contains comprehensive testing scripts and notebooks for all API integrations (Apollo, Perplexity, OpenAI) with the existing Firebase Functions.

## 📁 Files Overview

### 🔧 Individual API Test Scripts
- **`test_new_apollo_key.py`** - Tests Apollo API with minimal requests
- **`test_perplexity_api.py`** - Tests Perplexity API for lead enrichment
- **`test_openai_api.py`** - Tests OpenAI API for email generation
- **`test_all_apis.py`** - Comprehensive test of all APIs and complete workflow

### 🔧 Legacy/Diagnostic Scripts
- **`test_apollo_setup.py`** - Basic environment and import testing
- **`test_apollo_headers.py`** - Tests different API authentication formats
- **`test_apollo_comprehensive.py`** - Comprehensive endpoint access testing

### 📓 Testing Notebook
- **`apollo_api_testing.ipynb`** - Interactive Apollo API testing notebook

### 📋 Documentation
- **`apollo_api_key_setup_guide.md`** - Detailed guide for setting up Apollo API keys
- **`README.md`** - This file

### 📊 Generated Data
- **`apollo_sample_data.json`** - Sample API response data (generated when tests run)

## 🚀 Quick Start

### 1. Prerequisites
- **Apollo**: Enhanced plan with properly scoped API key
- **Perplexity**: Valid API key with credits
- **OpenAI**: Valid API key with credits
- Python environment with requirements installed

### 2. Setup API Keys
Add all API keys to your `.env` file:
```bash
APOLLO_API_KEY=your_apollo_key_here
PERPLEXITY_API_KEY=your_perplexity_key_here
OPENAI_API_KEY=your_openai_key_here
```

### 3. Test All APIs
```bash
# Test all APIs and complete workflow
python experiments/test_all_apis.py
```

### 4. Test Individual APIs
```bash
# Test Apollo API
python experiments/test_new_apollo_key.py

# Test Perplexity API
python experiments/test_perplexity_api.py

# Test OpenAI API
python experiments/test_openai_api.py
```

## 🔗 API Integration Overview

### 🔍 Apollo API (Lead Discovery)
- **Purpose**: Find potential leads based on job titles, locations, company domains
- **Integration**: `find_leads.py` function
- **Test Script**: `test_new_apollo_key.py`
- **Requirements**: Enhanced Apollo plan, properly scoped API key

### 🧠 Perplexity API (Lead Enrichment)
- **Purpose**: Research companies and people for personalized outreach
- **Integration**: `find_leads.py` function (enrichment step)
- **Test Script**: `test_perplexity_api.py`
- **Requirements**: Valid API key with credits

### 🤖 OpenAI API (Email Generation)
- **Purpose**: Generate personalized outreach and follow-up emails
- **Integration**: `contact_leads.py` function
- **Test Script**: `test_openai_api.py`
- **Requirements**: Valid API key with credits

## 📊 Complete Workflow Testing

The `test_all_apis.py` script tests the complete lead generation workflow:

1. **🔍 Apollo**: Find leads matching criteria
2. **🧠 Perplexity**: Enrich lead data with company research
3. **🤖 OpenAI**: Generate personalized outreach email
4. **📧 Result**: Complete lead with personalized email ready to send

## 🛠️ Troubleshooting

### Apollo API Issues
- **403 Forbidden**: Follow `apollo_api_key_setup_guide.md`
- **No Results**: Check search criteria and location formats
- **Rate Limiting**: Add delays between requests

### Perplexity API Issues
- **Authentication**: Verify API key in .env file
- **Credits**: Check remaining credits in Perplexity dashboard
- **Response Format**: Ensure 'choices' key exists in response

### OpenAI API Issues
- **Authentication**: Verify API key format (starts with sk-)
- **Credits**: Check billing and usage in OpenAI dashboard
- **Model Access**: Ensure access to GPT-4 model

### General Issues
- **Import Errors**: Ensure all requirements are installed
- **Environment**: Check .env file exists and has correct keys
- **Network**: Verify internet connectivity and API service status

## 📈 Production Deployment

After all tests pass:

### 1. Firebase Functions Integration
- ✅ `find_leads.py` - Apollo + Perplexity integration
- ✅ `contact_leads.py` - OpenAI integration
- ✅ `utils/api_clients.py` - All API client implementations
- ✅ `utils/firebase_utils.py` - API key management

### 2. Production Checklist
- [ ] Deploy updated functions to Firebase
- [ ] Configure production API keys in Firebase
- [ ] Set up error handling and logging
- [ ] Implement rate limiting
- [ ] Enable cost monitoring
- [ ] Set up backup and recovery

### 3. Monitoring
- **Apollo**: Monitor credit usage and search effectiveness
- **Perplexity**: Track enrichment quality and credit consumption
- **OpenAI**: Monitor token usage and email generation quality
- **Overall**: Track conversion rates and ROI

## 💡 Best Practices

### Credit Management
- Use moderate `per_page` values (10-25) for Apollo
- Cache Perplexity research to avoid duplicate requests
- Optimize OpenAI prompts for token efficiency
- Monitor usage across all platforms

### Quality Assurance
- Validate Apollo search results for relevance
- Review Perplexity enrichment for accuracy
- Test OpenAI emails for personalization quality
- Implement feedback loops for continuous improvement

### Error Handling
- Graceful degradation when APIs are unavailable
- Retry logic with exponential backoff
- Comprehensive logging for debugging
- User-friendly error messages

## 🎯 Success Metrics

✅ **API Connectivity**: All APIs accessible and responding  
✅ **Data Quality**: Relevant leads with accurate enrichment  
✅ **Email Quality**: Personalized, professional outreach emails  
✅ **Integration**: Seamless workflow from lead discovery to outreach  
✅ **Performance**: Efficient credit usage and response times  
✅ **Reliability**: Robust error handling and recovery  

The complete API testing suite ensures your lead generation and outreach workflow is production-ready! 