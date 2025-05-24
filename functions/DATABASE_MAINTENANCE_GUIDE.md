# Database Maintenance & Initialization Guide

## 🎯 Overview

This guide covers the database cleanup, initialization, and maintenance system for the Lead Generation platform. The system handles:

1. **Database Cleanup** - Removes old patterns and deprecated documents
2. **Database Initialization** - Sets up default configuration structure
3. **Health Monitoring** - Comprehensive database health reports

## 🛠️ Available Tools

### 1. Firebase Functions (Production)
- `database_cleanup` - Clean up old database patterns
- `database_initialize` - Initialize default configuration  
- `database_health_check` - Generate health report
- `database_full_maintenance` - Complete maintenance workflow

### 2. Local Script (Development/Testing)
- `run_database_maintenance.py` - Local testing and maintenance script

## 🚀 Quick Start

### Initialize Database for New Project

```javascript
// In your frontend console or via Firebase Functions call
const functions = firebase.functions();

// 1. Check current health
const healthResult = await functions.httpsCallable('database_health_check')();
console.log('Health Report:', healthResult.data);

// 2. Initialize if needed
const initResult = await functions.httpsCallable('database_initialize')();
console.log('Initialization:', initResult.data);

// 3. Run cleanup (dry run first)
const cleanupResult = await functions.httpsCallable('database_cleanup')({
  dry_run: true
});
console.log('Cleanup Preview:', cleanupResult.data);
```

### Full Maintenance Workflow

```javascript
// Complete maintenance in one call
const maintenanceResult = await functions.httpsCallable('database_full_maintenance')({
  cleanup_dry_run: false,  // Set to true for dry run
  force_init: false        // Set to true to force reinitialize
});
console.log('Full Maintenance:', maintenanceResult.data);
```

## 📋 What Gets Cleaned Up

### Old Patterns Removed
- ❌ `config/apiKeys` (old API key structure)
- ❌ `config/api_keys` (alternative old structure)
- ❌ `settings/emailSettings` (deprecated email settings)
- ❌ `settings/globalSettings` (old global settings)
- ❌ `prompts/emailPrompts` (old prompt structure)
- ❌ Orphaned project configurations for deleted projects
- ❌ Old email records (>90 days) with deprecated structure
- ❌ Leads missing required fields (migrated to new structure)

### Current Structure Maintained
- ✅ `settings/apiKeys` (current API key structure)
- ✅ `settings/smtp` (SMTP configuration)
- ✅ `settings/global` (global settings)
- ✅ `settings/jobRoles` (job role configuration)
- ✅ `settings/enrichment` (enrichment settings)
- ✅ `settings/emailGeneration` (email generation settings)
- ✅ `prompts/global` (global prompts)
- ✅ `settings/project_{id}*` (project-specific settings)
- ✅ `prompts/project_{id}` (project-specific prompts)

## 🔧 Default Configuration Initialized

When running initialization, the system creates:

### Global Configuration Documents

1. **API Keys** (`settings/apiKeys`)
   ```json
   {
     "openaiApiKey": "",
     "apolloApiKey": "",
     "apifiApiKey": "",
     "perplexityApiKey": ""
   }
   ```

2. **SMTP Settings** (`settings/smtp`)
   ```json
   {
     "host": "smtp.gmail.com",
     "port": 587,
     "secure": false,
     "username": "",
     "password": "",
     "fromEmail": "",
     "fromName": "",
     "replyToEmail": null
   }
   ```

3. **Global Settings** (`settings/global`)
   ```json
   {
     "followupDelayDays": 7,
     "maxFollowups": 3,
     "dailyEmailLimit": 50,
     "rateLimitDelaySeconds": 60,
     "workingHoursStart": 9,
     "workingHoursEnd": 17,
     "workingDays": [0, 1, 2, 3, 4],
     "timezone": "UTC",
     "onePersonPerCompany": true,
     "requireEmail": true,
     "excludeBlacklisted": true,
     "minCompanySize": null,
     "maxCompanySize": null
   }
   ```

4. **Job Roles** (`settings/jobRoles`)
   ```json
   {
     "targetRoles": ["Human Resources", "Office Manager", "Secretary", "Assistant", "Assistant Manager", "Manager", "Social Media"],
     "customRoles": []
   }
   ```

5. **Enrichment Config** (`settings/enrichment`)
   ```json
   {
     "enabled": true,
     "maxRetries": 3,
     "timeoutSeconds": 30,
     "promptTemplate": "Research the following company..."
   }
   ```

6. **Email Generation** (`settings/emailGeneration`)
   ```json
   {
     "model": "gpt-4",
     "maxTokens": 500,
     "temperature": 0.7
   }
   ```

7. **Global Prompts** (`prompts/global`)
   ```json
   {
     "outreachPrompt": "You are writing a professional outreach email...",
     "followupPrompt": "You are writing a follow-up email..."
   }
   ```

### System Documents

1. **Global Blacklist** (`blacklist/emails`)
   ```json
   {
     "list": [],
     "createdAt": "timestamp",
     "lastUpdated": "timestamp"
   }
   ```

2. **System Metadata** (`system/metadata`)
   ```json
   {
     "version": "1.0.0",
     "initialized_at": "timestamp",
     "last_maintenance": "timestamp",
     "configuration_version": "1.0",
     "database_schema_version": "1.0"
   }
   ```

## 🏥 Health Check Report

The health check generates a comprehensive report including:

### Configuration Status
- ✅ Global configuration completeness
- 📋 Missing documents list
- ⚠️ Invalid document detection

### Data Integrity
- 🔍 Orphaned configurations count
- 📊 Invalid leads count
- 🔗 Missing project configurations

### Statistics
- 📈 Document counts per collection
- 📊 Database size metrics

### Recommendations
- 💡 Actionable cleanup suggestions
- 🎯 Performance improvement tips
- 🔧 Configuration fix recommendations

## 🚀 Deployment Setup

### 1. Deploy Functions
```bash
cd functions
firebase deploy --only functions
```

### 2. Run Initial Setup
```javascript
// In your frontend console after deployment
const functions = firebase.functions();

// Initialize database with defaults
await functions.httpsCallable('database_initialize')();

// Run health check to verify
const health = await functions.httpsCallable('database_health_check')();
console.log('Setup complete:', health.data);
```

### 3. Configure API Keys
Navigate to Configuration tab in your admin dashboard and add:
- OpenAI API Key
- Apollo API Key  
- Perplexity API Key
- SMTP Settings

## 🧪 Local Testing (Optional)

If you have Firebase credentials configured locally:

```bash
cd functions

# Health check
python run_database_maintenance.py --action health

# Dry run cleanup
python run_database_maintenance.py --action cleanup --dry-run

# Actual cleanup
python run_database_maintenance.py --action cleanup --actual

# Initialize
python run_database_maintenance.py --action init

# Full maintenance
python run_database_maintenance.py --action full --actual
```

## 🔄 Maintenance Schedule

### Recommended Schedule
- **Weekly**: Health check
- **Monthly**: Cleanup (dry run first)
- **Quarterly**: Full maintenance
- **As needed**: After major updates or migrations

### Automated Monitoring
The system tracks:
- Last maintenance timestamp
- Configuration version
- Database schema version
- Health status trends

## ⚠️ Important Notes

1. **Always run cleanup in dry-run mode first** to preview changes
2. **Backup important data** before running actual cleanup
3. **Test in development** before running in production
4. **Monitor health reports** for early issue detection
5. **Initialize immediately** after deployment for new projects

## 🎯 Benefits

✅ **Clean Database**: Removes deprecated and orphaned data  
✅ **Proper Structure**: Ensures consistent configuration schema  
✅ **Health Monitoring**: Proactive issue detection  
✅ **Easy Maintenance**: Automated cleanup and initialization  
✅ **Performance**: Optimized database structure  
✅ **Reliability**: Validated configuration and data integrity

---

**Status**: ✅ Database maintenance system ready for production use! 