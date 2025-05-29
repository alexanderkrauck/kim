# 🚀 KIM - Lead Generation System

A comprehensive AI-powered outreach platform for automated lead discovery, enrichment, and email campaigns.

## ✨ Overview

KIM is a production-ready lead generation system that combines:
- **AI-Powered Lead Discovery** via Apollo.io integration
- **Intelligent Lead Enrichment** using Perplexity AI research
- **Personalized Email Generation** with OpenAI
- **Automated Email Campaigns** with SMTP delivery
- **Firebase-Hosted Admin Dashboard** with real-time updates

Perfect for businesses looking to automate their outreach pipeline with AI assistance.

## 🎯 Key Features

### 📊 **Project Management**
- Create projects with detailed targeting criteria
- Project-specific email guidelines and AI prompts
- Lead organization by project with comprehensive filtering

### 🤖 **AI-Powered Lead Processing**
- **Discovery**: Apollo.io integration with location and role targeting
- **Enrichment**: Perplexity AI research for company and person insights
- **Email Generation**: OpenAI-powered personalized outreach and follow-ups

### 📧 **Email Automation**
- SMTP integration with scheduling and rate limiting
- Automated follow-up sequences with customizable delays
- Professional email templates with AI personalization

### ⚙️ **Configuration Management**
- Unified settings interface for all system configuration
- API key management with secure storage
- Global and project-specific prompt customization

### 🛡️ **Security & Reliability**
- Firebase Authentication with multi-layer protection
- Firestore database with automated maintenance
- Health monitoring with proactive issue detection

## 🏗️ Tech Stack

### Frontend
- **React 18** with TypeScript
- **Tailwind CSS** for styling
- **Firebase Hosting** for deployment

### Backend
- **Firebase Functions** (Python) for business logic
- **Firestore** for data storage
- **Firebase Authentication** for security

### Integrations
- **Apollo.io** - Lead discovery
- **Perplexity AI** - Lead enrichment
- **OpenAI** - Email generation
- **SMTP** - Email delivery

## 🚀 Quick Start

### Prerequisites
- Node.js 16+ and npm
- Python 3.9+ (for Firebase Functions)
- Firebase project with services enabled

### 1. Clone & Install
```bash
git clone <repository-url>
cd kim

# Install frontend dependencies
npm install

# Install backend dependencies  
cd functions
pip install -r requirements.txt
cd ..
```

### 2. Firebase Setup
```bash
# Install Firebase CLI
npm install -g firebase-tools

# Login and select project
firebase login
firebase use <your-project-id>
```

### 3. Environment Configuration
```bash
# Copy environment template
cp env.example .env

# Edit .env with your Firebase configuration
REACT_APP_FIREBASE_API_KEY=your_api_key
REACT_APP_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
REACT_APP_FIREBASE_PROJECT_ID=your_project_id
# ... add remaining Firebase config
```

### 4. Deploy & Initialize
```bash
# Deploy Firebase Functions
firebase deploy --only functions

# Start frontend development server
npm start

# Initialize database (run in browser console after login)
const functions = firebase.functions();
await functions.httpsCallable('database_initialize')();
```

### 5. Configure API Keys
1. Open the application and log in
2. Navigate to **Configuration** tab
3. Add your API keys:
   - OpenAI API Key (required)
   - Apollo.io API Key (required)
   - Perplexity API Key (optional)
4. Configure SMTP settings for email delivery

## 📋 Usage Guide

### Creating Your First Project
1. Go to **Projects** tab → **New Project**
2. Fill in project details:
   - **Name**: Descriptive project name
   - **Area Description**: Target location/market
   - **Project Details**: Comprehensive description
   - **Email Guidelines**: Special considerations for outreach
3. Configure AI prompts (or use global defaults)

### Finding Leads
1. Select your project → **View Leads**
2. Click **Add Lead** or use bulk import
3. For automated discovery:
   ```javascript
   // Via Firebase Functions
   const result = await functions.httpsCallable('find_leads')({
     project_id: 'your_project_id',
     num_leads: 25,
     auto_enrich: true
   });
   ```

### Email Campaigns
1. Select leads in **Leads** tab
2. Generate personalized emails:
   ```javascript
   await functions.httpsCallable('generate_emails')({
     project_id: 'project_id',
     lead_ids: ['lead1', 'lead2'],
     email_type: 'outreach'
   });
   ```
3. Send emails with scheduling:
   ```javascript
   await functions.httpsCallable('contact_leads')({
     project_id: 'project_id', 
     lead_ids: ['lead1', 'lead2'],
     dry_run: false
   });
   ```

## 🔧 Development

### Frontend Development
```bash
npm start              # Development server
npm run build          # Production build
npm test               # Run tests
```

### Backend Development
```bash
cd functions

# Local testing
python test_apis.py              # Test API connections
python run_database_maintenance.py --action health  # Health check

# Deploy functions
firebase deploy --only functions
```

### Available Scripts
- `npm start` - Start React development server
- `npm run build` - Build for production
- `firebase serve` - Serve locally with Firebase
- `firebase deploy` - Deploy to production

## 📊 API Reference

### Core Functions

#### Lead Management
```javascript
// Find leads using Apollo.io
await functions.httpsCallable('find_leads')({
  project_id: string,
  num_leads: number,
  auto_enrich?: boolean
});

// Enrich leads with Perplexity AI
await functions.httpsCallable('enrich_leads')({
  project_id: string,
  lead_ids: string[]
});
```

#### Email Operations
```javascript
// Generate personalized emails
await functions.httpsCallable('generate_emails')({
  project_id: string,
  lead_ids: string[],
  email_type: 'outreach' | 'followup'
});

// Send emails
await functions.httpsCallable('contact_leads')({
  project_id: string,
  lead_ids: string[],
  dry_run?: boolean
});
```

#### Configuration
```javascript
// Update global configuration
await functions.httpsCallable('update_global_config')(configData);

// Update project-specific configuration  
await functions.httpsCallable('update_project_config')({
  project_id: string,
  config: object
});
```

### Database Maintenance
```javascript
// Health check
await functions.httpsCallable('database_health_check')();

// Initialize database
await functions.httpsCallable('database_initialize')();

// Cleanup old data
await functions.httpsCallable('database_cleanup')({ dry_run: true });
```

## 🛡️ Security

### Authentication
- Firebase Authentication protects all routes
- Database rules require authentication for all operations
- Component-level authentication checks

### Data Protection
- API keys stored securely in Firestore
- SMTP credentials encrypted
- No sensitive data exposed in client-side code

### Best Practices
- All database operations require valid auth tokens
- Input validation on all functions
- Rate limiting for external API calls

## 🏥 Maintenance

### Database Health
```bash
# Check database health
python functions/run_database_maintenance.py --action health

# Clean up old patterns (dry run)
python functions/run_database_maintenance.py --action cleanup --dry-run

# Initialize default configuration
python functions/run_database_maintenance.py --action init
```

### Monitoring
- Automated health checks available
- Database maintenance functions
- Comprehensive logging throughout

## 📁 Project Structure

```
kim/
├── src/                    # React frontend
│   ├── components/         # React components
│   ├── contexts/          # React contexts
│   ├── hooks/             # Custom hooks
│   └── types/             # TypeScript types
├── functions/              # Firebase Functions (Python)
│   ├── main.py            # Function exports
│   ├── config_model.py    # Configuration schemas
│   ├── find_leads.py      # Lead discovery
│   ├── enrich_leads.py    # Lead enrichment
│   ├── email_generation.py # Email generation
│   ├── contact_leads.py   # Email sending
│   └── utils/             # Utility modules
├── public/                # Static assets
└── build/                 # Production build
```

## 🚢 Deployment

### Production Deployment
```bash
# Build and deploy everything
npm run build
firebase deploy

# Deploy only functions
firebase deploy --only functions

# Deploy only hosting
firebase deploy --only hosting
```

### Environment Variables
Required for production:
- Firebase configuration (via .env)
- API keys (configured in app)
- SMTP settings (configured in app)

## 📞 Support & Contributing

### Getting Help
1. Check the [functions README](functions/README.md) for detailed backend documentation
2. Check the [database maintenance guide](functions/DATABASE_MAINTENANCE_GUIDE.md) for operational procedures
3. Review Firebase console logs for debugging

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🎉 What's Included

✅ **Complete Lead Generation Pipeline** - Discovery to delivery  
✅ **AI-Powered Personalization** - OpenAI and Perplexity integration  
✅ **Production-Ready** - Firebase hosting with authentication  
✅ **Automated Maintenance** - Database health monitoring and cleanup  
✅ **Comprehensive Documentation** - Everything you need to get started  
✅ **Modern Tech Stack** - React, TypeScript, Firebase, Python  

Built with ❤️ for efficient, AI-powered outreach automation. 