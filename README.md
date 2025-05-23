# 🚀 Outreach Admin Dashboard

A comprehensive Firebase-hosted admin dashboard for managing automated outreach campaigns with AI-powered email generation.

## ✨ Features

### 🔑 **API Key Management**
- **Global API Keys**: OpenAI, Apollo, Apifi, Perplexity
- **Secure Storage**: Masked display with show/hide functionality
- **Firebase Integration**: Encrypted storage in Firestore

### 📁 **Project Management**
- **Project Creation**: Name, area description, detailed project info
- **Email Guidelines**: Project-specific email considerations (300 chars)
- **Follow-up Strategy**: Custom follow-up timing and approach (300 chars)
- **AI Prompt Overrides**: Project-specific AI instructions or use global defaults
- **Project Settings**: Comprehensive configuration in dedicated settings view

### 👥 **Lead Management**
- **Project-Scoped Leads**: All leads belong to specific projects
- **Rich Data Model**: Email, name, company, status, source, notes, interaction history
- **Lead Addition**: Simple form with validation
- **CSV Export**: Complete lead data export with project-specific filenames
- **Enhanced Table**: Sortable columns, simple/detailed view modes
- **Status Tracking**: New, emailed, responded, bounced, blacklisted

### 🤖 **AI Prompt Templates**
- **Global Templates**: Default AI instructions for all projects
- **Project Overrides**: Custom AI instructions per project
- **Clear Guidance**: Examples and best practices for writing effective prompts
- **Smart Defaults**: Projects use global templates unless overridden

### 🚫 **Blacklist Management**
- **Global Blacklist**: Email addresses blocked across all projects
- **Easy Management**: Add/remove emails with validation

### ⚙️ **Settings**
- **Global Configuration**: Follow-up delays and maximum follow-up attempts
- **User Preferences**: Customizable dashboard settings

## 🏗️ Architecture

### **Project-Centric Design**
- All operations are scoped to specific projects
- Projects contain leads, settings, and AI prompt overrides
- Clear separation between global settings and project-specific configuration

### **Smart Navigation**
- **Projects Tab**: Create, edit, and manage projects
- **Leads Tab**: Manage leads for selected project
- **Prompts Tab**: Configure global AI templates
- **API Keys Tab**: Manage service API keys
- **Settings Tab**: Global dashboard configuration

### **Data Flow**
1. Create projects with detailed configuration
2. Add leads to specific projects
3. Configure AI prompts (global or project-specific)
4. Export lead data for external use

## 🛠️ Tech Stack

- **Frontend**: React 18 + TypeScript
- **Styling**: Tailwind CSS
- **Icons**: Heroicons
- **Backend**: Firebase (Firestore + Authentication + Hosting)
- **Build Tool**: Create React App
- **State Management**: React Hooks + Context API

## 🚀 Getting Started

### Prerequisites
- Node.js 16+ and npm
- Firebase project with Firestore and Authentication enabled

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd kim
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Configure Firebase**
   ```bash
   # Copy environment template
   cp env.example .env
   
   # Add your Firebase configuration to .env
   ```

4. **Start development server**
   ```bash
   npm start
   ```

5. **Deploy to Firebase** (optional)
   ```bash
   npm run build
   firebase deploy
   ```

### Environment Variables
Create a `.env` file with your Firebase configuration:
```
REACT_APP_FIREBASE_API_KEY=your_api_key
REACT_APP_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
REACT_APP_FIREBASE_PROJECT_ID=your_project_id
REACT_APP_FIREBASE_STORAGE_BUCKET=your_project.appspot.com
REACT_APP_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
REACT_APP_FIREBASE_APP_ID=your_app_id
```

## 📊 Data Models

### Project
```typescript
interface Project {
  id: string;
  name: string;
  areaDescription: string;        // Target area specification
  projectDetails: string;         // Detailed description (5k chars)
  emailConsiderations: string;    // Email guidelines (300 chars)
  followupConsiderations: string; // Follow-up strategy (300 chars)
  createdAt: Date;
  updatedAt: Date;
  isActive: boolean;
  leadCount: number;
}
```

### Lead
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

## 🎯 Usage Guide

### Creating a Project
1. Navigate to **Projects** tab
2. Click **"New Project"**
3. Fill in project details:
   - **Name**: Descriptive project name
   - **Area Description**: Target location/specification
   - **Project Details**: Comprehensive project description
   - **Email Considerations**: Special email guidelines
   - **Follow-up Considerations**: Follow-up strategy
4. Click **"Create Project"**

### Managing Project Settings
1. In **Projects** tab, click **"Edit Project"** on any project
2. Use the three tabs to configure:
   - **Project Details**: Basic information
   - **Email Guidelines**: Email and follow-up considerations
   - **AI Prompts**: Custom AI instructions or use global defaults
3. Save changes in each section

### Adding Leads
1. Click **"View Leads"** on a project or select project and go to **Leads** tab
2. Click **"Add Lead"**
3. Fill in lead information (email required)
4. Lead is automatically associated with the selected project

### Configuring AI Prompts
1. **Global Templates**: Go to **Prompts** tab to set default AI instructions
2. **Project Overrides**: In project settings, go to **AI Prompts** tab to customize

## 🔧 Development

### Available Scripts
- `npm start` - Start development server
- `npm run build` - Build for production
- `npm test` - Run tests
- `npm run eject` - Eject from Create React App

### Firebase Commands
- `firebase serve` - Serve locally
- `firebase deploy` - Deploy to production
- `firebase deploy --only firestore:indexes` - Deploy database indexes

## 🛡️ Security

- **Authentication Required**: All operations require user authentication
- **Firestore Rules**: Secure database access with proper rules
- **API Key Protection**: Sensitive keys are masked in UI
- **Input Validation**: All forms include proper validation

## 📝 License

This project is licensed under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For questions or issues, please create an issue in the repository or contact the development team.

---

**Built with ❤️ for efficient outreach campaign management** 