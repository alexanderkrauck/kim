# 🚀 Enhanced Outreach Admin Dashboard

A comprehensive Firebase-hosted admin dashboard for managing automated outreach campaigns with project-scoped architecture, advanced lead management, API key configuration, and complete workflow automation.

## ✨ Key Features

### 🔑 **API Keys Management**
- **OpenAI, Apollo, Apifi, Perplexity** API key storage
- **Global access** across all projects
- **Secure storage** with masked display
- **Show/hide functionality** for security

### 📁 **Project-Scoped Architecture**
- **Complete project management** with detailed configuration
- **Area specification** with exact address requirements
- **5,000-character project details** with real-time counter
- **Email & follow-up considerations** (300 chars each)
- **Project-specific lead isolation**

### 👥 **Advanced Lead Management**
- **Enhanced lead addition** with full data capture
- **CSV export** with comprehensive data
- **Sortable table views** (Simple & Detailed modes)
- **Project-scoped operations**
- **Rich data model** with interaction tracking

### 📊 **Enhanced Data Features**
- **Interaction summaries** per lead
- **Email chain tracking** structure
- **Status management** with visual badges
- **Real-time lead counts** per project
- **Project-specific blacklisting**

## 🚀 Quick Start

### Prerequisites
1. **Node.js** (v16 or higher)
2. **Firebase CLI** installed globally
3. **Firebase project** with Firestore enabled

### Installation

```bash
# Clone and install
git clone <repository-url>
cd kim
npm install

# Start development server
npm start
```

Visit `http://localhost:3000` to access the dashboard.

### Firebase Configuration

1. **Get Firebase Config**:
   - Go to [Firebase Console](https://console.firebase.google.com)
   - Select your project → Settings → General
   - Copy web app configuration

2. **Create Environment File**:
   ```bash
   cp env.example .env
   # Edit .env with your Firebase configuration
   ```

3. **Enable Firebase Services**:
   - **Authentication**: Enable Email/Password provider
   - **Firestore**: Create database in production mode
   - **Functions**: Upgrade to Blaze plan (optional)

## 📋 Usage Guide

### 1. **Initial Setup**
- Create admin account using sign-up feature
- Configure API keys in the API Keys tab
- Set up global settings (follow-up delays, etc.)

### 2. **Project Management**
- Create projects with detailed specifications
- Define area descriptions with exact addresses
- Set email and follow-up considerations
- Configure project-specific prompts

### 3. **Lead Management**
- Add leads to specific projects
- Use enhanced table features (sorting, filtering)
- Export lead data to CSV
- Track interaction history

### 4. **Workflow Automation**
- Configure email templates (global/project-specific)
- Set up automated follow-up schedules
- Manage blacklists (global/project-specific)
- Monitor lead status progression

## 🏗️ Architecture

### **Frontend (React + TypeScript)**
```
src/
├── components/
│   ├── ApiKeys.tsx          # API key management
│   ├── Projects.tsx         # Project creation & selection
│   ├── EnhancedLeads.tsx    # Advanced lead management
│   ├── Settings.tsx         # Global configuration
│   ├── Prompts.tsx          # Email templates
│   ├── Blacklist.tsx        # Email blacklisting
│   ├── Login.tsx            # Authentication
│   └── Layout.tsx           # Navigation & layout
├── contexts/
│   └── AuthContext.tsx      # Authentication state
├── types/
│   └── index.ts             # TypeScript definitions
└── firebase/
    └── config.ts            # Firebase configuration
```

### **Backend (Firebase)**
```
functions/
└── main.py                  # Python Firebase Functions
    ├── trigger_followup     # Manual follow-up trigger
    ├── process_all_followups # Batch processing
    ├── on_lead_created      # Lead creation handler
    └── health_check         # System health
```

### **Data Structure**
```
Firestore Collections:
├── projects/               # Project configurations
├── leads/                  # Project-scoped leads
├── settings/
│   ├── global             # Global settings
│   └── apiKeys            # API key storage
├── prompts/
│   ├── default            # Global prompts
│   └── project_{id}       # Project-specific prompts
└── blacklist/
    ├── emails             # Global blacklist
    └── project_{id}       # Project blacklists
```

## 🔧 Development

### **Local Development**
```bash
# Start development server
npm start

# Run Firebase emulators
firebase emulators:start

# Type checking
npx tsc --noEmit

# Build for production
npm run build
```

### **Testing**
Follow the comprehensive [Testing Guide](TESTING_GUIDE.md) to verify all features.

### **Deployment**
```bash
# Deploy hosting only
firebase deploy --only hosting

# Deploy everything (requires Blaze plan)
firebase deploy
```

## 📊 Data Models

### **Project Interface**
```typescript
interface Project {
  id: string;
  name: string;
  areaDescription: string;        // Exact address specification
  projectDetails: string;         // Max 5k characters
  emailConsiderations: string;    // Max 300 characters
  followupConsiderations: string; // Max 300 characters
  createdAt: Date;
  updatedAt: Date;
  isActive: boolean;
  leadCount: number;
}
```

### **Enhanced Lead Interface**
```typescript
interface Lead {
  id: string;
  email: string;
  name?: string;
  company?: string;
  status: 'new' | 'emailed' | 'responded' | 'bounced' | 'blacklisted';
  lastContacted: Date | null;
  followupCount: number;
  createdAt: Date;
  projectId: string;
  interactionSummary: string;
  emailChain: EmailRecord[];
  source?: string;
  notes?: string;
}
```

### **API Keys Interface**
```typescript
interface ApiKeys {
  openaiApiKey: string;
  apolloApiKey: string;
  apifiApiKey: string;
  perplexityApiKey: string;
}
```

## 🎯 Features Overview

### ✅ **Implemented Features**
- [x] Project-scoped architecture with full configuration
- [x] API key management (OpenAI, Apollo, Apifi, Perplexity)
- [x] Enhanced lead management with rich data
- [x] CSV export with comprehensive data
- [x] Sortable table views (Simple & Detailed)
- [x] Real-time form validation
- [x] Character counters for limited fields
- [x] Project-specific blacklisting
- [x] Interaction summary tracking
- [x] Email chain structure (ready for integration)
- [x] Modern responsive UI with Tailwind CSS
- [x] Toast notifications and loading states
- [x] TypeScript safety throughout

### 🔄 **Ready for Integration**
- [ ] Email service integration using stored API keys
- [ ] Automated follow-up processing
- [ ] Lead enrichment via Apollo/Apifi APIs
- [ ] AI-powered email generation via OpenAI
- [ ] Research integration via Perplexity

## 📚 Documentation

- **[Feature Implementation Summary](FEATURE_IMPLEMENTATION_SUMMARY.md)** - Complete feature overview
- **[Testing Guide](TESTING_GUIDE.md)** - Comprehensive testing instructions

## 🛠️ Tech Stack

- **Frontend**: React 18, TypeScript, Tailwind CSS
- **Backend**: Firebase (Auth, Firestore, Functions, Hosting)
- **Functions**: Python 3.10
- **Build Tools**: Create React App, PostCSS
- **UI Components**: Heroicons, React Hot Toast

## 🔒 Security

- **Authentication**: Firebase Auth with email/password
- **Database**: Firestore with security rules
- **API Keys**: Encrypted storage with masked display
- **Access Control**: Authenticated users only

## 📈 Performance

- **Optimized builds** with Create React App
- **Lazy loading** for large datasets
- **Efficient queries** with Firestore indexing
- **Responsive design** for all screen sizes

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

---

**Built with ❤️ using React, TypeScript, and Firebase**

*For detailed feature documentation, see [FEATURE_IMPLEMENTATION_SUMMARY.md](FEATURE_IMPLEMENTATION_SUMMARY.md)* 