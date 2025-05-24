# React Hooks

## `useSystemInitialization`

Automatically checks and initializes the database on first user login.

### Features
- **Automatic Health Check**: Verifies database configuration completeness
- **Smart Initialization**: Only initializes if needed
- **Session Tracking**: Prevents repeated initialization attempts  
- **European Functions**: Uses `europe-west1` region for optimal performance
- **Error Handling**: Provides retry mechanism for failed initialization
- **User Feedback**: Shows loading states and success/error messages

### Usage

```typescript
import { useSystemInitialization } from './hooks/useSystemInitialization';

const { 
  isInitialized, 
  isInitializing, 
  initializationError,
  retryInitialization 
} = useSystemInitialization(isAuthenticated);
```

### Return Values

- `isInitialized`: Boolean indicating if database is ready
- `isInitializing`: Boolean indicating if initialization is in progress
- `initializationError`: String with error message if initialization failed
- `healthCheckComplete`: Boolean indicating if health check completed
- `retryInitialization`: Function to retry failed initialization

### Initialization Flow

1. **Authentication Check**: Only runs when user is authenticated
2. **Health Check**: Calls `database_health_check` function
3. **Conditional Init**: Calls `database_initialize` if needed
4. **Session Cache**: Prevents repeated attempts within same session
5. **Error Recovery**: Provides manual retry capability

### What Gets Initialized

- Global API Keys configuration
- SMTP settings for email delivery
- Global settings (scheduling, lead filtering)
- Job roles configuration
- Enrichment settings
- Email generation settings
- Global prompts
- System metadata
- Global blacklist

The system only initializes missing configuration - existing data is preserved. 