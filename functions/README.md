# Firebase Functions for Lead Management

Clean, minimal Firebase Functions for lead discovery, enrichment, and management with comprehensive testing.

## 🚀 Quick Start

### Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp env.example .env
# Edit .env with your API keys
```

### Usage
```bash
# Main development test (run after code changes)
python test.py

# Mock tests only (fast, no API calls)
python tests/run_tests.py mock

# Complete test suite
python tests/run_tests.py full
```

## 📋 Functions

### Core Functions
- **`find_leads`** - Discover leads using Apollo.io API
- **`enrich_leads`** - Enrich leads with Perplexity research
- **`test_apis`** - Test and validate API connections
- **`contact_leads`** - Generate and send outreach emails

### API Integration
- **Apollo.io** - Lead discovery and contact information
- **Perplexity** - Company and person research
- **OpenAI** - Email content generation
- **Firestore** - Data storage and management

## 🎭 Testing

### Two Test Modes
```bash
# Mock tests (recommended for development)
# - Fast execution (<0.1s)
# - Zero API costs
# - No external dependencies
python tests/run_tests.py mock

# Full tests (for production validation)
# - Includes Firebase Functions
# - Requires proper setup
python tests/run_tests.py full
```

### Development Workflow
```bash
# Main development test (run after code changes)
python test.py

# Save test results
python tests/run_tests.py mock --output results.json
```

## 📁 Project Structure

```
├── find_leads.py          # Lead discovery function
├── enrich_leads.py        # Lead enrichment function  
├── test_apis.py           # API testing function
├── contact_leads.py       # Email outreach function
├── main.py               # Function router
├── utils/                # Utility modules
│   ├── api_clients.py    # API client classes
│   ├── firebase_utils.py # Firebase utilities
│   └── data_processing.py # Data processing utilities
├── tests/                # Test suite with mocks
└── .github/workflows/    # CI/CD automation
```

## 🔧 Configuration

### Environment Variables
```bash
APOLLO_API_KEY=your_apollo_key
PERPLEXITY_API_KEY=your_perplexity_key  
OPENAI_API_KEY=your_openai_key
DEBUG=true
```

### Firebase Setup
```bash
# Initialize Firebase (if needed)
firebase init

# Deploy functions
firebase deploy --only functions
```

## 📊 Status

- **Mock System**: ✅ 100% functional (all APIs mocked)
- **Utility Tests**: ✅ 90% success rate  
- **Firebase Functions**: ⚠️ 43% success rate (Flask context issue)
- **CI/CD**: ✅ Automated testing and deployment

The mock system is production-ready and provides fast, reliable testing without external dependencies. 