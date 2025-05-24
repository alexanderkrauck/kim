import React, { useState, useEffect } from 'react';
import { toast } from 'react-hot-toast';
import {
  ChevronDownIcon,
  ChevronRightIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  CogIcon,
  GlobeAltIcon,
  FolderIcon,
  KeyIcon,
  EnvelopeIcon,
  ClockIcon,
  UserGroupIcon,
  ChatBubbleLeftRightIcon,
  MagnifyingGlassIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline';
import { doc, getDoc, setDoc, updateDoc } from 'firebase/firestore';
import { db, functions } from '../firebase/config';
import { httpsCallable } from 'firebase/functions';

interface ConfigSection {
  id: string;
  title: string;
  description: string;
  icon: React.ComponentType<any>;
  isExpanded?: boolean;
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

interface GlobalConfig {
  // API Keys
  openaiApiKey: string;
  apolloApiKey: string;
  apifiApiKey: string;
  perplexityApiKey: string;
  
  // SMTP Settings
  smtpHost: string;
  smtpPort: number;
  smtpSecure: boolean;
  smtpUsername: string;
  smtpPassword: string;
  smtpFromEmail: string;
  smtpFromName: string;
  smtpReplyToEmail: string;
  
  // Global Settings
  followupDelayDays: number;
  maxFollowups: number;
  dailyEmailLimit: number;
  rateLimitDelaySeconds: number;
  workingHoursStart: number;
  workingHoursEnd: number;
  workingDays: number[];
  timezone: string;
  
  // Lead Filter Settings
  onePersonPerCompany: boolean;
  requireEmail: boolean;
  excludeBlacklisted: boolean;
  minCompanySize: number | null;
  maxCompanySize: number | null;
  
  // Job Roles
  targetRoles: string[];
  customRoles: string[];
  
  // Enrichment Settings
  enrichmentEnabled: boolean;
  enrichmentMaxRetries: number;
  enrichmentTimeoutSeconds: number;
  enrichmentPromptTemplate: string;
  
  // Email Generation Settings
  emailModel: string;
  emailMaxTokens: number;
  emailTemperature: number;
  
  // Global Prompts
  outreachPrompt: string;
  followupPrompt: string;
}

// Empty config interface for initialization
const EMPTY_CONFIG: GlobalConfig = {
  // API Keys
  openaiApiKey: '',
  apolloApiKey: '',
  apifiApiKey: '',
  perplexityApiKey: '',
  
  // SMTP Settings
  smtpHost: '',
  smtpPort: 587,
  smtpSecure: false,
  smtpUsername: '',
  smtpPassword: '',
  smtpFromEmail: '',
  smtpFromName: '',
  smtpReplyToEmail: '',
  
  // Global Settings
  followupDelayDays: 0,
  maxFollowups: 0,
  dailyEmailLimit: 0,
  rateLimitDelaySeconds: 0,
  workingHoursStart: 0,
  workingHoursEnd: 0,
  workingDays: [],
  timezone: '',
  
  // Lead Filter Settings
  onePersonPerCompany: false,
  requireEmail: false,
  excludeBlacklisted: false,
  minCompanySize: null,
  maxCompanySize: null,
  
  // Job Roles
  targetRoles: [],
  customRoles: [],
  
  // Enrichment Settings
  enrichmentEnabled: false,
  enrichmentMaxRetries: 0,
  enrichmentTimeoutSeconds: 0,
  enrichmentPromptTemplate: '',
  
  // Email Generation Settings
  emailModel: '',
  emailMaxTokens: 0,
  emailTemperature: 0,
  
  // Global Prompts
  outreachPrompt: '',
  followupPrompt: ''
};

const Configuration: React.FC = () => {
  const [config, setConfig] = useState<GlobalConfig>(EMPTY_CONFIG);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['apiKeys']));
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [rawConfigMode, setRawConfigMode] = useState(false);
  const [rawConfigText, setRawConfigText] = useState('');
  const [isInitializing, setIsInitializing] = useState(false);
  const [configExists, setConfigExists] = useState(false);

  const configSections: ConfigSection[] = [
    {
      id: 'apiKeys',
      title: 'API Keys',
      description: 'Configure external API keys for services',
      icon: KeyIcon
    },
    {
      id: 'smtp',
      title: 'Email Settings',
      description: 'SMTP configuration for sending emails',
      icon: EnvelopeIcon
    },
    {
      id: 'scheduling',
      title: 'Scheduling & Limits',
      description: 'Email timing and rate limiting settings',
      icon: ClockIcon
    },
    {
      id: 'leadFilter',
      title: 'Lead Filtering',
      description: 'Configure how leads are filtered and selected',
      icon: UserGroupIcon
    },
    {
      id: 'jobRoles',
      title: 'Target Job Roles',
      description: 'Define target positions for lead finding',
      icon: UserGroupIcon
    },
    {
      id: 'enrichment',
      title: 'Lead Enrichment',
      description: 'Configure Perplexity integration for lead research',
      icon: MagnifyingGlassIcon
    },
    {
      id: 'emailGeneration',
      title: 'Email Generation',
      description: 'OpenAI settings for email content generation',
      icon: ChatBubbleLeftRightIcon
    },
    {
      id: 'prompts',
      title: 'Email Prompts',
      description: 'Templates for outreach and follow-up emails',
      icon: DocumentTextIcon
    }
  ];

  useEffect(() => {
    loadConfiguration();
  }, []);

  const initializeConfiguration = async () => {
    try {
      setIsInitializing(true);
      toast.loading('Initializing configuration...', { id: 'config-init' });

      const initializeDb = httpsCallable(functions, 'database_initialize');
      const result = await initializeDb();
      const data = result.data as InitializationResponse;

      if (data?.success) {
        toast.success('Configuration initialized successfully', { id: 'config-init' });
        // Reload configuration after initialization
        await loadConfiguration();
      } else {
        throw new Error(data?.error || 'Failed to initialize configuration');
      }
    } catch (error) {
      console.error('Error initializing configuration:', error);
      toast.error('Failed to initialize configuration', { id: 'config-init' });
    } finally {
      setIsInitializing(false);
    }
  };

  const checkConfigurationExists = (docs: any[]) => {
    // Check if at least the core configuration documents exist and have data
    const [apiKeysDoc, smtpDoc, globalDoc, jobRolesDoc, enrichmentDoc, emailGenDoc, promptsDoc] = docs;
    
    return apiKeysDoc.exists() && smtpDoc.exists() && globalDoc.exists() && 
           jobRolesDoc.exists() && enrichmentDoc.exists() && emailGenDoc.exists() && promptsDoc.exists();
  };

  const loadConfiguration = async () => {
    try {
      setIsLoading(true);
      
      // Load from multiple Firebase documents
      const [apiKeysDoc, smtpDoc, globalDoc, jobRolesDoc, enrichmentDoc, emailGenDoc, promptsDoc] = await Promise.all([
        getDoc(doc(db, 'settings', 'apiKeys')),
        getDoc(doc(db, 'settings', 'smtp')),
        getDoc(doc(db, 'settings', 'global')),
        getDoc(doc(db, 'settings', 'jobRoles')),
        getDoc(doc(db, 'settings', 'enrichment')),
        getDoc(doc(db, 'settings', 'emailGeneration')),
        getDoc(doc(db, 'prompts', 'global'))
      ]);

      // Check if configuration exists
      const configExistsCheck = checkConfigurationExists([apiKeysDoc, smtpDoc, globalDoc, jobRolesDoc, enrichmentDoc, emailGenDoc, promptsDoc]);
      setConfigExists(configExistsCheck);

      if (!configExistsCheck) {
        console.log('Configuration not found, will need initialization');
        setConfig(EMPTY_CONFIG);
        setRawConfigText(JSON.stringify(EMPTY_CONFIG, null, 2));
        return;
      }

      const newConfig = { ...EMPTY_CONFIG };

      if (apiKeysDoc.exists()) {
        const data = apiKeysDoc.data();
        newConfig.openaiApiKey = data.openaiApiKey || '';
        newConfig.apolloApiKey = data.apolloApiKey || '';
        newConfig.apifiApiKey = data.apifiApiKey || '';
        newConfig.perplexityApiKey = data.perplexityApiKey || '';
      }

      if (smtpDoc.exists()) {
        const data = smtpDoc.data();
        newConfig.smtpHost = data.host || '';
        newConfig.smtpPort = data.port || 587;
        newConfig.smtpSecure = data.secure || false;
        newConfig.smtpUsername = data.username || '';
        newConfig.smtpPassword = data.password || '';
        newConfig.smtpFromEmail = data.fromEmail || '';
        newConfig.smtpFromName = data.fromName || '';
        newConfig.smtpReplyToEmail = data.replyToEmail || '';
      }

      if (globalDoc.exists()) {
        const data = globalDoc.data();
        newConfig.followupDelayDays = data.followupDelayDays ?? 0;
        newConfig.maxFollowups = data.maxFollowups ?? 0;
        newConfig.dailyEmailLimit = data.dailyEmailLimit ?? 0;
        newConfig.rateLimitDelaySeconds = data.rateLimitDelaySeconds ?? 0;
        newConfig.workingHoursStart = data.workingHoursStart ?? 0;
        newConfig.workingHoursEnd = data.workingHoursEnd ?? 0;
        newConfig.workingDays = data.workingDays ?? [];
        newConfig.timezone = data.timezone || '';
        newConfig.onePersonPerCompany = data.onePersonPerCompany ?? false;
        newConfig.requireEmail = data.requireEmail ?? false;
        newConfig.excludeBlacklisted = data.excludeBlacklisted ?? false;
        newConfig.minCompanySize = data.minCompanySize;
        newConfig.maxCompanySize = data.maxCompanySize;
      }

      if (jobRolesDoc.exists()) {
        const data = jobRolesDoc.data();
        newConfig.targetRoles = data.targetRoles || [];
        newConfig.customRoles = data.customRoles || [];
      }

      if (enrichmentDoc.exists()) {
        const data = enrichmentDoc.data();
        newConfig.enrichmentEnabled = data.enabled ?? false;
        newConfig.enrichmentMaxRetries = data.maxRetries ?? 0;
        newConfig.enrichmentTimeoutSeconds = data.timeoutSeconds ?? 0;
        newConfig.enrichmentPromptTemplate = data.promptTemplate || '';
      }

      if (emailGenDoc.exists()) {
        const data = emailGenDoc.data();
        newConfig.emailModel = data.model || '';
        newConfig.emailMaxTokens = data.maxTokens ?? 0;
        newConfig.emailTemperature = data.temperature ?? 0;
      }

      if (promptsDoc.exists()) {
        const data = promptsDoc.data();
        newConfig.outreachPrompt = data.outreachPrompt || '';
        newConfig.followupPrompt = data.followupPrompt || '';
      }

      setConfig(newConfig);
      setRawConfigText(JSON.stringify(newConfig, null, 2));
    } catch (error) {
      console.error('Error loading configuration:', error);
      toast.error('Failed to load configuration');
      setConfigExists(false);
    } finally {
      setIsLoading(false);
    }
  };

  const saveConfiguration = async () => {
    try {
      setIsSaving(true);

      // Save to multiple Firebase documents
      await Promise.all([
        setDoc(doc(db, 'settings', 'apiKeys'), {
          openaiApiKey: config.openaiApiKey,
          apolloApiKey: config.apolloApiKey,
          apifiApiKey: config.apifiApiKey,
          perplexityApiKey: config.perplexityApiKey
        }),
        
        setDoc(doc(db, 'settings', 'smtp'), {
          host: config.smtpHost,
          port: config.smtpPort,
          secure: config.smtpSecure,
          username: config.smtpUsername,
          password: config.smtpPassword,
          fromEmail: config.smtpFromEmail,
          fromName: config.smtpFromName,
          replyToEmail: config.smtpReplyToEmail
        }),
        
        setDoc(doc(db, 'settings', 'global'), {
          followupDelayDays: config.followupDelayDays,
          maxFollowups: config.maxFollowups,
          dailyEmailLimit: config.dailyEmailLimit,
          rateLimitDelaySeconds: config.rateLimitDelaySeconds,
          workingHoursStart: config.workingHoursStart,
          workingHoursEnd: config.workingHoursEnd,
          workingDays: config.workingDays,
          timezone: config.timezone,
          onePersonPerCompany: config.onePersonPerCompany,
          requireEmail: config.requireEmail,
          excludeBlacklisted: config.excludeBlacklisted,
          minCompanySize: config.minCompanySize,
          maxCompanySize: config.maxCompanySize
        }),
        
        setDoc(doc(db, 'settings', 'jobRoles'), {
          targetRoles: config.targetRoles,
          customRoles: config.customRoles
        }),
        
        setDoc(doc(db, 'settings', 'enrichment'), {
          enabled: config.enrichmentEnabled,
          maxRetries: config.enrichmentMaxRetries,
          timeoutSeconds: config.enrichmentTimeoutSeconds,
          promptTemplate: config.enrichmentPromptTemplate
        }),
        
        setDoc(doc(db, 'settings', 'emailGeneration'), {
          model: config.emailModel,
          maxTokens: config.emailMaxTokens,
          temperature: config.emailTemperature
        }),
        
        setDoc(doc(db, 'prompts', 'global'), {
          outreachPrompt: config.outreachPrompt,
          followupPrompt: config.followupPrompt
        })
      ]);

      toast.success('Configuration saved successfully');
    } catch (error) {
      console.error('Error saving configuration:', error);
      toast.error('Failed to save configuration');
    } finally {
      setIsSaving(false);
    }
  };

  const saveRawConfiguration = async () => {
    try {
      setIsSaving(true);
      const parsedConfig = JSON.parse(rawConfigText);
      setConfig(parsedConfig);
      
      // Save the parsed config
      await saveConfiguration();
      setRawConfigMode(false);
    } catch (error) {
      console.error('Error parsing raw configuration:', error);
      toast.error('Invalid JSON configuration');
    } finally {
      setIsSaving(false);
    }
  };

  const toggleSection = (sectionId: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(sectionId)) {
      newExpanded.delete(sectionId);
    } else {
      newExpanded.add(sectionId);
    }
    setExpandedSections(newExpanded);
  };

  const updateConfig = (key: keyof GlobalConfig, value: any) => {
    setConfig(prev => ({ ...prev, [key]: value }));
  };

  const addCustomRole = () => {
    const role = prompt('Enter custom job role:');
    if (role && role.trim()) {
      updateConfig('customRoles', [...config.customRoles, role.trim()]);
    }
  };

  const removeCustomRole = (index: number) => {
    updateConfig('customRoles', config.customRoles.filter((_, i) => i !== index));
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  // Show initialization prompt if config doesn't exist
  if (!configExists && !isLoading) {
    return (
      <div className="space-y-6">
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center">
              <CogIcon className="h-8 w-8 text-indigo-600 mr-3" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">System Configuration</h1>
                <p className="text-sm text-gray-600">Initialize your system configuration</p>
              </div>
            </div>
          </div>

          <div className="p-6">
            <div className="text-center">
              <ExclamationTriangleIcon className="mx-auto h-12 w-12 text-amber-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">Configuration Not Found</h3>
              <p className="mt-1 text-sm text-gray-500">
                Your system configuration hasn't been initialized yet. This is required before you can use the lead generation features.
              </p>
              <div className="mt-6">
                <button
                  onClick={initializeConfiguration}
                  disabled={isInitializing}
                  className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                >
                  {isInitializing ? (
                    <>
                      <div className="animate-spin -ml-1 mr-3 h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
                      Initializing...
                    </>
                  ) : (
                    <>
                      <CheckCircleIcon className="-ml-1 mr-2 h-4 w-4" />
                      Initialize Configuration
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <CogIcon className="h-8 w-8 text-indigo-600 mr-3" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">System Configuration</h1>
                <p className="text-sm text-gray-600">Manage all system settings and configurations</p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="px-3 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                {showAdvanced ? 'Hide Advanced' : 'Show Advanced'}
              </button>
              <button
                onClick={() => setRawConfigMode(!rawConfigMode)}
                className="px-3 py-2 text-sm font-medium text-indigo-700 bg-indigo-100 border border-indigo-300 rounded-md hover:bg-indigo-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                {rawConfigMode ? 'Visual Mode' : 'Raw JSON Mode'}
              </button>
              <button
                onClick={initializeConfiguration}
                disabled={isInitializing}
                className="px-3 py-2 text-sm font-medium text-amber-700 bg-amber-100 border border-amber-300 rounded-md hover:bg-amber-200 focus:outline-none focus:ring-2 focus:ring-amber-500 disabled:opacity-50"
              >
                {isInitializing ? 'Initializing...' : 'Reinitialize'}
              </button>
              <button
                onClick={rawConfigMode ? saveRawConfiguration : saveConfiguration}
                disabled={isSaving || !configExists}
                className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
              >
                {isSaving ? 'Saving...' : 'Save Configuration'}
              </button>
            </div>
          </div>
        </div>

        {/* Status Banner */}
        {configExists ? (
          <div className="bg-green-50 border-l-4 border-green-400 p-4">
            <div className="flex">
              <CheckCircleIcon className="h-5 w-5 text-green-400" />
              <div className="ml-3">
                <p className="text-sm text-green-700">
                  <strong>Configuration Loaded:</strong> System configuration loaded from Firestore successfully. 
                  Changes will be saved back to the database.
                </p>
              </div>
            </div>
          </div>
        ) : (
          <div className="bg-amber-50 border-l-4 border-amber-400 p-4">
            <div className="flex">
              <ExclamationTriangleIcon className="h-5 w-5 text-amber-400" />
              <div className="ml-3">
                <p className="text-sm text-amber-700">
                  <strong>Warning:</strong> Configuration not fully loaded. Please initialize the configuration 
                  before making changes.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {rawConfigMode ? (
        /* Raw JSON Editor */
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Raw Configuration (JSON)</h2>
            <p className="text-sm text-gray-600">Edit the complete configuration as JSON</p>
          </div>
          <div className="p-6">
            <textarea
              value={rawConfigText}
              onChange={(e) => setRawConfigText(e.target.value)}
              className="w-full h-96 font-mono text-sm border border-gray-300 rounded-md p-3 focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="Enter configuration JSON..."
            />
          </div>
        </div>
      ) : (
        /* Visual Configuration Sections */
        <div className="space-y-4">
          {configSections.map((section) => {
            const isExpanded = expandedSections.has(section.id);
            const Icon = section.icon;

            return (
              <div key={section.id} className="bg-white shadow rounded-lg">
                <button
                  onClick={() => toggleSection(section.id)}
                  className="w-full px-6 py-4 text-left focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <Icon className="h-6 w-6 text-indigo-600 mr-3" />
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900">{section.title}</h3>
                        <p className="text-sm text-gray-600">{section.description}</p>
                      </div>
                    </div>
                    {isExpanded ? (
                      <ChevronDownIcon className="h-5 w-5 text-gray-500" />
                    ) : (
                      <ChevronRightIcon className="h-5 w-5 text-gray-500" />
                    )}
                  </div>
                </button>

                {isExpanded && (
                  <div className="border-t border-gray-200 px-6 py-4">
                    {/* Render section content based on section.id */}
                    {section.id === 'apiKeys' && (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            OpenAI API Key
                          </label>
                          <input
                            type="password"
                            value={config.openaiApiKey}
                            onChange={(e) => updateConfig('openaiApiKey', e.target.value)}
                            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-indigo-500 focus:border-indigo-500"
                            placeholder="sk-..."
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Apollo API Key
                          </label>
                          <input
                            type="password"
                            value={config.apolloApiKey}
                            onChange={(e) => updateConfig('apolloApiKey', e.target.value)}
                            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-indigo-500 focus:border-indigo-500"
                            placeholder="Enter Apollo API key"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Perplexity API Key
                          </label>
                          <input
                            type="password"
                            value={config.perplexityApiKey}
                            onChange={(e) => updateConfig('perplexityApiKey', e.target.value)}
                            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-indigo-500 focus:border-indigo-500"
                            placeholder="pplx-..."
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            APIFI API Key
                          </label>
                          <input
                            type="password"
                            value={config.apifiApiKey}
                            onChange={(e) => updateConfig('apifiApiKey', e.target.value)}
                            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-indigo-500 focus:border-indigo-500"
                            placeholder="Enter APIFI API key"
                          />
                        </div>
                      </div>
                    )}

                    {section.id === 'smtp' && (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            SMTP Host
                          </label>
                          <input
                            type="text"
                            value={config.smtpHost}
                            onChange={(e) => updateConfig('smtpHost', e.target.value)}
                            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-indigo-500 focus:border-indigo-500"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            SMTP Port
                          </label>
                          <input
                            type="number"
                            value={config.smtpPort}
                            onChange={(e) => updateConfig('smtpPort', parseInt(e.target.value))}
                            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-indigo-500 focus:border-indigo-500"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Username
                          </label>
                          <input
                            type="text"
                            value={config.smtpUsername}
                            onChange={(e) => updateConfig('smtpUsername', e.target.value)}
                            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-indigo-500 focus:border-indigo-500"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Password
                          </label>
                          <input
                            type="password"
                            value={config.smtpPassword}
                            onChange={(e) => updateConfig('smtpPassword', e.target.value)}
                            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-indigo-500 focus:border-indigo-500"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            From Email
                          </label>
                          <input
                            type="email"
                            value={config.smtpFromEmail}
                            onChange={(e) => updateConfig('smtpFromEmail', e.target.value)}
                            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-indigo-500 focus:border-indigo-500"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            From Name
                          </label>
                          <input
                            type="text"
                            value={config.smtpFromName}
                            onChange={(e) => updateConfig('smtpFromName', e.target.value)}
                            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-indigo-500 focus:border-indigo-500"
                          />
                        </div>
                        <div className="md:col-span-2">
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Reply-To Email (Optional)
                          </label>
                          <input
                            type="email"
                            value={config.smtpReplyToEmail}
                            onChange={(e) => updateConfig('smtpReplyToEmail', e.target.value)}
                            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-indigo-500 focus:border-indigo-500"
                          />
                        </div>
                        <div className="md:col-span-2">
                          <label className="flex items-center">
                            <input
                              type="checkbox"
                              checked={config.smtpSecure}
                              onChange={(e) => updateConfig('smtpSecure', e.target.checked)}
                              className="mr-2 h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                            />
                            <span className="text-sm font-medium text-gray-700">Use SSL/TLS (port 465)</span>
                          </label>
                        </div>
                      </div>
                    )}

                    {section.id === 'scheduling' && (
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Follow-up Delay (Days)
                          </label>
                          <input
                            type="number"
                            value={config.followupDelayDays}
                            onChange={(e) => updateConfig('followupDelayDays', parseInt(e.target.value))}
                            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-indigo-500 focus:border-indigo-500"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Max Follow-ups
                          </label>
                          <input
                            type="number"
                            value={config.maxFollowups}
                            onChange={(e) => updateConfig('maxFollowups', parseInt(e.target.value))}
                            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-indigo-500 focus:border-indigo-500"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Daily Email Limit
                          </label>
                          <input
                            type="number"
                            value={config.dailyEmailLimit}
                            onChange={(e) => updateConfig('dailyEmailLimit', parseInt(e.target.value))}
                            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-indigo-500 focus:border-indigo-500"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Working Hours Start (24h)
                          </label>
                          <input
                            type="number"
                            min="0"
                            max="23"
                            value={config.workingHoursStart}
                            onChange={(e) => updateConfig('workingHoursStart', parseInt(e.target.value))}
                            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-indigo-500 focus:border-indigo-500"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Working Hours End (24h)
                          </label>
                          <input
                            type="number"
                            min="0"
                            max="23"
                            value={config.workingHoursEnd}
                            onChange={(e) => updateConfig('workingHoursEnd', parseInt(e.target.value))}
                            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-indigo-500 focus:border-indigo-500"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Timezone
                          </label>
                          <select
                            value={config.timezone}
                            onChange={(e) => updateConfig('timezone', e.target.value)}
                            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-indigo-500 focus:border-indigo-500"
                          >
                            <option value="UTC">UTC</option>
                            <option value="America/New_York">Eastern Time</option>
                            <option value="America/Chicago">Central Time</option>
                            <option value="America/Denver">Mountain Time</option>
                            <option value="America/Los_Angeles">Pacific Time</option>
                            <option value="Europe/London">London</option>
                            <option value="Europe/Paris">Paris</option>
                            <option value="Asia/Tokyo">Tokyo</option>
                          </select>
                        </div>
                      </div>
                    )}

                    {section.id === 'leadFilter' && (
                      <div className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div>
                            <label className="flex items-center">
                              <input
                                type="checkbox"
                                checked={config.onePersonPerCompany}
                                onChange={(e) => updateConfig('onePersonPerCompany', e.target.checked)}
                                className="mr-2 h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                              />
                              <span className="text-sm font-medium text-gray-700">One person per company</span>
                            </label>
                          </div>
                          <div>
                            <label className="flex items-center">
                              <input
                                type="checkbox"
                                checked={config.requireEmail}
                                onChange={(e) => updateConfig('requireEmail', e.target.checked)}
                                className="mr-2 h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                              />
                              <span className="text-sm font-medium text-gray-700">Require email address</span>
                            </label>
                          </div>
                          <div>
                            <label className="flex items-center">
                              <input
                                type="checkbox"
                                checked={config.excludeBlacklisted}
                                onChange={(e) => updateConfig('excludeBlacklisted', e.target.checked)}
                                className="mr-2 h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                              />
                              <span className="text-sm font-medium text-gray-700">Exclude blacklisted emails</span>
                            </label>
                          </div>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                              Min Company Size
                            </label>
                            <input
                              type="number"
                              value={config.minCompanySize || ''}
                              onChange={(e) => updateConfig('minCompanySize', e.target.value ? parseInt(e.target.value) : null)}
                              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-indigo-500 focus:border-indigo-500"
                              placeholder="No minimum"
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                              Max Company Size
                            </label>
                            <input
                              type="number"
                              value={config.maxCompanySize || ''}
                              onChange={(e) => updateConfig('maxCompanySize', e.target.value ? parseInt(e.target.value) : null)}
                              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-indigo-500 focus:border-indigo-500"
                              placeholder="No maximum"
                            />
                          </div>
                        </div>
                      </div>
                    )}

                    {section.id === 'jobRoles' && (
                      <div className="space-y-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Target Job Roles
                          </label>
                          <div className="grid grid-cols-2 md:grid-cols-3 gap-2 mb-4">
                            {['CEO', 'CTO', 'Founder', 'Co-Founder', 'President', 'VP Engineering', 'VP Technology', 'Head of Engineering', 'Engineering Manager', 'Technical Director'].map((role) => (
                              <label key={role} className="flex items-center">
                                <input
                                  type="checkbox"
                                  checked={config.targetRoles.includes(role)}
                                  onChange={(e) => {
                                    if (e.target.checked) {
                                      updateConfig('targetRoles', [...config.targetRoles, role]);
                                    } else {
                                      updateConfig('targetRoles', config.targetRoles.filter(r => r !== role));
                                    }
                                  }}
                                  className="mr-2 h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                                />
                                <span className="text-sm text-gray-700">{role}</span>
                              </label>
                            ))}
                          </div>
                        </div>
                        
                        <div>
                          <div className="flex items-center justify-between mb-2">
                            <label className="block text-sm font-medium text-gray-700">
                              Custom Roles
                            </label>
                            <button
                              onClick={addCustomRole}
                              className="px-3 py-1 text-xs font-medium text-indigo-700 bg-indigo-100 border border-indigo-300 rounded-md hover:bg-indigo-200"
                            >
                              Add Custom Role
                            </button>
                          </div>
                          <div className="space-y-2">
                            {config.customRoles.map((role, index) => (
                              <div key={index} className="flex items-center justify-between bg-gray-50 p-2 rounded">
                                <span className="text-sm text-gray-700">{role}</span>
                                <button
                                  onClick={() => removeCustomRole(index)}
                                  className="text-red-600 hover:text-red-800 text-sm"
                                >
                                  Remove
                                </button>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    )}

                    {section.id === 'enrichment' && (
                      <div className="space-y-4">
                        <div className="flex items-center">
                          <label className="flex items-center">
                            <input
                              type="checkbox"
                              checked={config.enrichmentEnabled}
                              onChange={(e) => updateConfig('enrichmentEnabled', e.target.checked)}
                              className="mr-2 h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                            />
                            <span className="text-sm font-medium text-gray-700">Enable lead enrichment</span>
                          </label>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                              Max Retries
                            </label>
                            <input
                              type="number"
                              value={config.enrichmentMaxRetries}
                              onChange={(e) => updateConfig('enrichmentMaxRetries', parseInt(e.target.value))}
                              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-indigo-500 focus:border-indigo-500"
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                              Timeout (Seconds)
                            </label>
                            <input
                              type="number"
                              value={config.enrichmentTimeoutSeconds}
                              onChange={(e) => updateConfig('enrichmentTimeoutSeconds', parseInt(e.target.value))}
                              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-indigo-500 focus:border-indigo-500"
                            />
                          </div>
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Enrichment Prompt Template
                          </label>
                          <textarea
                            value={config.enrichmentPromptTemplate}
                            onChange={(e) => updateConfig('enrichmentPromptTemplate', e.target.value)}
                            rows={8}
                            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-indigo-500 focus:border-indigo-500"
                            placeholder="Enter enrichment prompt template..."
                          />
                          <p className="text-xs text-gray-500 mt-1">
                            Use {'{company}'}, {'{name}'}, and {'{title}'} as placeholders
                          </p>
                        </div>
                      </div>
                    )}

                    {section.id === 'emailGeneration' && (
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Model
                          </label>
                          <select
                            value={config.emailModel}
                            onChange={(e) => updateConfig('emailModel', e.target.value)}
                            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-indigo-500 focus:border-indigo-500"
                          >
                            <option value="gpt-4">GPT-4</option>
                            <option value="gpt-4-turbo">GPT-4 Turbo</option>
                            <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                          </select>
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Max Tokens
                          </label>
                          <input
                            type="number"
                            value={config.emailMaxTokens}
                            onChange={(e) => updateConfig('emailMaxTokens', parseInt(e.target.value))}
                            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-indigo-500 focus:border-indigo-500"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Temperature (0-2)
                          </label>
                          <input
                            type="number"
                            step="0.1"
                            min="0"
                            max="2"
                            value={config.emailTemperature}
                            onChange={(e) => updateConfig('emailTemperature', parseFloat(e.target.value))}
                            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-indigo-500 focus:border-indigo-500"
                          />
                        </div>
                      </div>
                    )}

                    {section.id === 'prompts' && (
                      <div className="space-y-6">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Outreach Email Prompt
                          </label>
                          <textarea
                            value={config.outreachPrompt}
                            onChange={(e) => updateConfig('outreachPrompt', e.target.value)}
                            rows={12}
                            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-indigo-500 focus:border-indigo-500"
                            placeholder="Enter outreach email prompt..."
                          />
                          <p className="text-xs text-gray-500 mt-1">
                            Available variables: {'{project_name}'}, {'{project_description}'}, {'{name}'}, {'{company}'}, {'{enrichment_data}'}, {'{email_considerations}'}
                          </p>
                        </div>
                        
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Follow-up Email Prompt
                          </label>
                          <textarea
                            value={config.followupPrompt}
                            onChange={(e) => updateConfig('followupPrompt', e.target.value)}
                            rows={12}
                            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-indigo-500 focus:border-indigo-500"
                            placeholder="Enter follow-up email prompt..."
                          />
                          <p className="text-xs text-gray-500 mt-1">
                            Available variables: {'{days_ago}'}, {'{project_name}'}, {'{name}'}, {'{company}'}, {'{original_email}'}, {'{followup_considerations}'}
                          </p>
                        </div>
                      </div>
                    )}

                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default Configuration; 