import { useState, useEffect } from 'react';
import { functions } from '../firebase/config';
import { httpsCallable } from 'firebase/functions';
import toast from 'react-hot-toast';

// TypeScript interfaces for Firebase Function responses
interface HealthCheckResponse {
  success: boolean;
  health_report: {
    timestamp: string;
    configuration_status: {
      global_config_complete: boolean;
      missing_documents: string[];
      invalid_documents: string[];
    };
    data_integrity: {
      orphaned_configs: number;
      invalid_leads: number;
      missing_project_configs: number;
    };
    statistics: {
      [key: string]: number;
    };
    recommendations: string[];
  };
}

interface InitializationResponse {
  success: boolean;
  initialization_results: {
    initialized: string[];
    skipped: string[];
    errors: string[];
    force: boolean;
  };
  error?: string;
}

interface InitializationStatus {
  isInitialized: boolean;
  isInitializing: boolean;
  initializationError: string | null;
  healthCheckComplete: boolean;
}

export const useSystemInitialization = (isAuthenticated: boolean) => {
  const [status, setStatus] = useState<InitializationStatus>({
    isInitialized: false,
    isInitializing: false,
    initializationError: null,
    healthCheckComplete: false,
  });

  useEffect(() => {
    if (!isAuthenticated) {
      // Reset status when user logs out
      setStatus({
        isInitialized: false,
        isInitializing: false,
        initializationError: null,
        healthCheckComplete: false,
      });
      return;
    }

    const checkAndInitializeDatabase = async () => {
      try {
        setStatus(prev => ({ ...prev, isInitializing: true, initializationError: null }));

        // Use European region for functions
        const euroFunctions = functions;

        // Step 1: Check database health
        console.log('🔍 Checking database health...');
        const healthCheck = httpsCallable(euroFunctions, 'database_health_check');
        const healthResult = await healthCheck();

        const healthData = healthResult.data as HealthCheckResponse;
        setStatus(prev => ({ ...prev, healthCheckComplete: true }));

        // Step 2: Check if initialization is needed
        const configComplete = healthData?.health_report?.configuration_status?.global_config_complete;
        
        if (configComplete) {
          console.log('✅ Database already initialized');
          setStatus(prev => ({
            ...prev,
            isInitialized: true,
            isInitializing: false,
          }));
          return;
        }

        // Step 3: Initialize database if needed
        console.log('🚀 Initializing database...');
        toast.loading('Setting up your workspace...', { id: 'initialization' });

        const initializeDb = httpsCallable(euroFunctions, 'database_initialize');
        const initResult = await initializeDb();

        const initData = initResult.data as InitializationResponse;

        if (initData?.success) {
          console.log('✅ Database initialized successfully');
          toast.success('Workspace ready!', { id: 'initialization' });
          
          setStatus(prev => ({
            ...prev,
            isInitialized: true,
            isInitializing: false,
          }));

          // Show initialization summary
          const initialized = initData.initialization_results?.initialized || [];
          if (initialized.length > 0) {
            console.log('📋 Initialized:', initialized);
          }
        } else {
          throw new Error(initData?.error || 'Failed to initialize database');
        }

      } catch (error: any) {
        console.error('❌ Database initialization failed:', error);
        
        const errorMessage = error?.message || 'Failed to initialize workspace';
        toast.error(`Setup failed: ${errorMessage}`, { id: 'initialization' });
        
        setStatus(prev => ({
          ...prev,
          isInitializing: false,
          initializationError: errorMessage,
        }));
      }
    };

    // Only run initialization check once per session
    const hasRunInitialization = sessionStorage.getItem('initialization_attempted');
    
    if (!hasRunInitialization) {
      sessionStorage.setItem('initialization_attempted', 'true');
      checkAndInitializeDatabase();
    } else {
      // If we've already attempted initialization this session, assume it's ready
      setStatus(prev => ({
        ...prev,
        isInitialized: true,
        healthCheckComplete: true,
      }));
    }

  }, [isAuthenticated]);

  // Manual retry function
  const retryInitialization = async () => {
    sessionStorage.removeItem('initialization_attempted');
    setStatus(prev => ({
      ...prev,
      initializationError: null,
      isInitializing: false,
    }));
    
    // Trigger re-initialization
    window.location.reload();
  };

  return {
    ...status,
    retryInitialization,
  };
}; 