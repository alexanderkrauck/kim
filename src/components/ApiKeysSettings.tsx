import React, { useState, useEffect, useCallback } from 'react';
import { doc, getDoc, setDoc } from 'firebase/firestore';
import { db } from '../firebase/config';
import { ApiKeys, SmtpSettings } from '../types';
import { EyeIcon, EyeSlashIcon, KeyIcon, EnvelopeIcon, ExclamationTriangleIcon, ShieldExclamationIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import { useAuth } from '../contexts/AuthContext';

const ApiKeysSettings: React.FC = () => {
  const [apiKeys, setApiKeys] = useState<ApiKeys>({
    openaiApiKey: '',
    apolloApiKey: '',
    apifiApiKey: '',
    perplexityApiKey: '',
  });
  const [smtpSettings, setSmtpSettings] = useState<SmtpSettings>({
    host: '',
    port: 587,
    secure: false,
    username: '',
    password: '',
    fromEmail: '',
    fromName: '',
    replyToEmail: '',
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState<'api-keys' | 'smtp'>('api-keys');
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [originalSmtpSettings, setOriginalSmtpSettings] = useState<SmtpSettings | null>(null);
  const [showKeys, setShowKeys] = useState({
    openai: false,
    apollo: false,
    apifi: false,
    perplexity: false,
    smtpPassword: false,
  });

  const auth = useAuth();

  const loadApiKeys = useCallback(async () => {
    if (!auth.currentUser) {
      console.error('User not authenticated');
      toast.error('Please log in to access API keys');
      setLoading(false);
      return;
    }

    try {
      const docRef = doc(db, 'settings', 'apiKeys');
      const docSnap = await getDoc(docRef);
      
      if (docSnap.exists()) {
        setApiKeys(docSnap.data() as ApiKeys);
      }
    } catch (error) {
      console.error('Error loading API keys:', error);
      toast.error('Failed to load API keys');
    } finally {
      setLoading(false);
    }
  }, [auth.currentUser]);

  const loadSmtpSettings = useCallback(async () => {
    if (!auth.currentUser) {
      console.error('User not authenticated');
      toast.error('Please log in to access SMTP settings');
      return;
    }

    try {
      const docRef = doc(db, 'settings', 'smtp');
      const docSnap = await getDoc(docRef);
      
      if (docSnap.exists()) {
        setSmtpSettings(docSnap.data() as SmtpSettings);
        setOriginalSmtpSettings(docSnap.data() as SmtpSettings);
      }
    } catch (error) {
      console.error('Error loading SMTP settings:', error);
      toast.error('Failed to load SMTP settings');
    }
  }, [auth.currentUser]);

  useEffect(() => {
    if (auth.currentUser) {
      loadApiKeys();
      loadSmtpSettings();
    }
  }, [auth.currentUser, loadApiKeys, loadSmtpSettings]);

  const saveApiKeys = async () => {
    if (!auth.currentUser) {
      toast.error('Please log in to save API keys');
      return;
    }

    setSaving(true);
    try {
      const docRef = doc(db, 'settings', 'apiKeys');
      await setDoc(docRef, apiKeys);
      toast.success('API keys saved successfully!');
    } catch (error) {
      console.error('Error saving API keys:', error);
      toast.error('Failed to save API keys');
    } finally {
      setSaving(false);
    }
  };

  const handleInputChange = (field: keyof ApiKeys, value: string) => {
    setApiKeys(prev => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleSmtpInputChange = (field: keyof SmtpSettings, value: string | number | boolean) => {
    setSmtpSettings(prev => ({
      ...prev,
      [field]: value,
    }));
    setHasUnsavedChanges(true);
  };

  const handleSaveSmtpSettings = () => {
    setShowConfirmation(true);
  };

  const confirmSaveSmtpSettings = async () => {
    if (!auth.currentUser) {
      toast.error('Please log in to save SMTP settings');
      return;
    }

    setSaving(true);
    setShowConfirmation(false);
    try {
      const docRef = doc(db, 'settings', 'smtp');
      await setDoc(docRef, smtpSettings);
      setOriginalSmtpSettings({ ...smtpSettings });
      setHasUnsavedChanges(false);
      toast.success('SMTP settings saved successfully!');
    } catch (error) {
      console.error('Error saving SMTP settings:', error);
      toast.error('Failed to save SMTP settings');
    } finally {
      setSaving(false);
    }
  };

  const cancelSaveSmtpSettings = () => {
    setShowConfirmation(false);
  };

  const resetSmtpSettings = () => {
    if (originalSmtpSettings) {
      setSmtpSettings({ ...originalSmtpSettings });
      setHasUnsavedChanges(false);
    }
  };

  const toggleShowKey = (key: keyof typeof showKeys) => {
    setShowKeys(prev => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  const maskKey = (key: string) => {
    if (!key) return '';
    if (key.length <= 8) return '*'.repeat(key.length);
    return key.substring(0, 4) + '*'.repeat(key.length - 8) + key.substring(key.length - 4);
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-indigo-500"></div>
      </div>
    );
  }

  const apiKeyFields = [
    {
      key: 'openaiApiKey' as keyof ApiKeys,
      label: 'OpenAI API Key',
      placeholder: 'sk-...',
      description: 'Used for AI-powered email generation and content analysis',
      showKey: 'openai' as keyof typeof showKeys,
    },
    {
      key: 'apolloApiKey' as keyof ApiKeys,
      label: 'Apollo API Key',
      placeholder: 'apollo_...',
      description: 'Used for lead enrichment and contact discovery',
      showKey: 'apollo' as keyof typeof showKeys,
    },
    {
      key: 'apifiApiKey' as keyof ApiKeys,
      label: 'Apifi API Key',
      placeholder: 'apifi_...',
      description: 'Used for additional data enrichment services',
      showKey: 'apifi' as keyof typeof showKeys,
    },
    {
      key: 'perplexityApiKey' as keyof ApiKeys,
      label: 'Perplexity API Key',
      placeholder: 'pplx-...',
      description: 'Used for research and content generation',
      showKey: 'perplexity' as keyof typeof showKeys,
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 flex items-center">
          <KeyIcon className="h-6 w-6 mr-2" />
          Settings
        </h2>
        <p className="text-gray-600 mt-1">
          Configure API keys and system settings
        </p>
      </div>

      {/* Critical Warning Section - General */}
      <div className="p-4 bg-red-50 border-2 border-red-200 rounded-lg">
        <div className="flex">
          <ShieldExclamationIcon className="h-6 w-6 text-red-500 mt-0.5 mr-3 flex-shrink-0" />
          <div>
            <h3 className="text-sm font-bold text-red-800 mb-2">
              ⚠️ CRITICAL SYSTEM CONFIGURATION
            </h3>
            <div className="text-sm text-red-700 space-y-2">
              <p><strong>WARNING:</strong> These settings control core system functionality!</p>
              <ul className="list-disc list-inside space-y-1 ml-4">
                <li>SMTP settings control all email sending capabilities</li>
                <li>API keys enable AI-powered features and integrations</li>
                <li>Incorrect configuration will break system functionality</li>
                <li>Changes take effect immediately across the entire application</li>
              </ul>
              <p className="font-semibold">
                Only modify these settings if you are certain of the configuration. 
                Test thoroughly before deploying to production.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('api-keys')}
            className={`${
              activeTab === 'api-keys'
                ? 'border-indigo-500 text-indigo-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm inline-flex items-center`}
          >
            <KeyIcon className="h-5 w-5 mr-2" />
            API Keys
          </button>
          <button
            onClick={() => setActiveTab('smtp')}
            className={`${
              activeTab === 'smtp'
                ? 'border-indigo-500 text-indigo-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm inline-flex items-center`}
          >
            <EnvelopeIcon className="h-5 w-5 mr-2" />
            SMTP Email Settings
          </button>
        </nav>
      </div>

      {/* API Keys Tab */}
      {activeTab === 'api-keys' && (
    <div className="bg-white shadow rounded-lg">
      <div className="px-4 py-5 sm:p-6">
        <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
          API Keys Configuration
        </h3>
        <p className="text-sm text-gray-600 mb-6">
          Configure your API keys for various services. These keys are stored securely and used globally across all projects.
        </p>
        
        <div className="space-y-6">
          {apiKeyFields.map((field) => (
            <div key={field.key}>
              <label htmlFor={field.key} className="block text-sm font-medium text-gray-700">
                {field.label}
              </label>
              <div className="mt-1 relative">
                <input
                  type={showKeys[field.showKey] ? 'text' : 'password'}
                  id={field.key}
                  value={apiKeys[field.key]}
                  onChange={(e) => handleInputChange(field.key, e.target.value)}
                  className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full pr-10 sm:text-sm border-gray-300 rounded-md"
                  placeholder={field.placeholder}
                />
                <button
                  type="button"
                  onClick={() => toggleShowKey(field.showKey)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center"
                >
                  {showKeys[field.showKey] ? (
                    <EyeSlashIcon className="h-4 w-4 text-gray-400" />
                  ) : (
                    <EyeIcon className="h-4 w-4 text-gray-400" />
                  )}
                </button>
              </div>
              <p className="mt-2 text-sm text-gray-500">
                {field.description}
                {apiKeys[field.key] && !showKeys[field.showKey] && (
                  <span className="ml-2 text-green-600">
                    ✓ Key configured: {maskKey(apiKeys[field.key])}
                  </span>
                )}
              </p>
            </div>
          ))}
        </div>

        <div className="mt-6">
          <button
            onClick={saveApiKeys}
            disabled={saving}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {saving ? 'Saving...' : 'Save API Keys'}
          </button>
        </div>

        <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-md">
          <div className="flex">
            <div className="ml-3">
              <h3 className="text-sm font-medium text-yellow-800">
                Security Notice
              </h3>
              <div className="mt-2 text-sm text-yellow-700">
                <p>
                  API keys are stored securely in your Firebase project. Never share these keys publicly or commit them to version control.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
        </div>
      )}

      {/* SMTP Settings Tab */}
      {activeTab === 'smtp' && (
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              SMTP Email Configuration
            </h3>
            <p className="text-sm text-gray-600 mb-6">
              Configure your SMTP server settings for sending outreach emails. These settings are used for all email communications.
            </p>
            
            <div className="space-y-6">
              {/* Server Settings */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label htmlFor="smtpHost" className="block text-sm font-medium text-gray-700">
                    SMTP Host *
                  </label>
                  <input
                    type="text"
                    id="smtpHost"
                    value={smtpSettings.host}
                    onChange={(e) => handleSmtpInputChange('host', e.target.value)}
                    className="mt-1 shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                    placeholder="smtp.gmail.com"
                  />
                  <p className="mt-1 text-xs text-gray-500">
                    Your SMTP server hostname
                  </p>
                </div>

                <div>
                  <label htmlFor="smtpPort" className="block text-sm font-medium text-gray-700">
                    Port *
                  </label>
                  <input
                    type="number"
                    id="smtpPort"
                    value={smtpSettings.port}
                    onChange={(e) => handleSmtpInputChange('port', parseInt(e.target.value) || 587)}
                    className="mt-1 shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                    placeholder="587"
                  />
                  <p className="mt-1 text-xs text-gray-500">
                    Common ports: 587 (TLS), 465 (SSL), 25 (unsecured)
                  </p>
                </div>
              </div>

              <div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={smtpSettings.secure}
                    onChange={(e) => handleSmtpInputChange('secure', e.target.checked)}
                    className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                  />
                  <span className="ml-2 text-sm text-gray-700">
                    Use SSL/TLS encryption (recommended for port 465)
                  </span>
                </label>
              </div>

              {/* Authentication */}
              <div className="border-t border-gray-200 pt-6">
                <h4 className="text-md font-medium text-gray-900 mb-4">Authentication</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label htmlFor="smtpUsername" className="block text-sm font-medium text-gray-700">
                      Username *
                    </label>
                    <input
                      type="text"
                      id="smtpUsername"
                      value={smtpSettings.username}
                      onChange={(e) => handleSmtpInputChange('username', e.target.value)}
                      className="mt-1 shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                      placeholder="your-email@domain.com"
                    />
                  </div>

                  <div>
                    <label htmlFor="smtpPassword" className="block text-sm font-medium text-gray-700">
                      Password *
                    </label>
                    <div className="mt-1 relative">
                      <input
                        type={showKeys.smtpPassword ? 'text' : 'password'}
                        id="smtpPassword"
                        value={smtpSettings.password}
                        onChange={(e) => handleSmtpInputChange('password', e.target.value)}
                        className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full pr-10 sm:text-sm border-gray-300 rounded-md"
                        placeholder="Your SMTP password"
                      />
                      <button
                        type="button"
                        onClick={() => toggleShowKey('smtpPassword')}
                        className="absolute inset-y-0 right-0 pr-3 flex items-center"
                      >
                        {showKeys.smtpPassword ? (
                          <EyeSlashIcon className="h-4 w-4 text-gray-400" />
                        ) : (
                          <EyeIcon className="h-4 w-4 text-gray-400" />
                        )}
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              {/* Email Settings */}
              <div className="border-t border-gray-200 pt-6">
                <h4 className="text-md font-medium text-gray-900 mb-4">Email Settings</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label htmlFor="fromEmail" className="block text-sm font-medium text-gray-700">
                      From Email *
                    </label>
                    <input
                      type="email"
                      id="fromEmail"
                      value={smtpSettings.fromEmail}
                      onChange={(e) => handleSmtpInputChange('fromEmail', e.target.value)}
                      className="mt-1 shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                      placeholder="outreach@yourcompany.com"
                    />
                    <p className="mt-1 text-xs text-gray-500">
                      Email address that appears as sender
                    </p>
                  </div>

                  <div>
                    <label htmlFor="fromName" className="block text-sm font-medium text-gray-700">
                      From Name *
                    </label>
                    <input
                      type="text"
                      id="fromName"
                      value={smtpSettings.fromName}
                      onChange={(e) => handleSmtpInputChange('fromName', e.target.value)}
                      className="mt-1 shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                      placeholder="Your Company Name"
                    />
                    <p className="mt-1 text-xs text-gray-500">
                      Display name that appears as sender
                    </p>
                  </div>

                  <div className="md:col-span-2">
                    <label htmlFor="replyToEmail" className="block text-sm font-medium text-gray-700">
                      Reply-To Email (Optional)
                    </label>
                    <input
                      type="email"
                      id="replyToEmail"
                      value={smtpSettings.replyToEmail || ''}
                      onChange={(e) => handleSmtpInputChange('replyToEmail', e.target.value)}
                      className="mt-1 shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                      placeholder="replies@yourcompany.com"
                    />
                    <p className="mt-1 text-xs text-gray-500">
                      Email address for replies (defaults to From Email if not specified)
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-6">
              {hasUnsavedChanges && (
                <div className="mb-4 p-3 bg-amber-50 border border-amber-200 rounded-md">
                  <div className="flex">
                    <ExclamationTriangleIcon className="h-5 w-5 text-amber-400 mt-0.5 mr-2 flex-shrink-0" />
                    <div className="text-sm text-amber-700">
                      <p><strong>You have unsaved changes!</strong> These changes will affect all email sending immediately upon saving.</p>
                    </div>
                  </div>
                </div>
              )}
              
              <div className="flex space-x-3">
                {hasUnsavedChanges && (
                  <button
                    onClick={resetSmtpSettings}
                    disabled={saving}
                    className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Reset Changes
                  </button>
                )}
                <button
                  onClick={handleSaveSmtpSettings}
                  disabled={saving || !hasUnsavedChanges}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <ShieldExclamationIcon className="h-4 w-4 mr-2" />
                  {saving ? 'Saving...' : 'Save SMTP Settings'}
                </button>
              </div>
            </div>

            <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-md">
              <div className="flex">
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-blue-800">
                    SMTP Configuration Help
                  </h3>
                  <div className="mt-2 text-sm text-blue-700">
                    <p className="mb-2"><strong>Common SMTP Providers:</strong></p>
                    <ul className="list-disc list-inside space-y-1">
                      <li><strong>Gmail:</strong> smtp.gmail.com, Port 587 (TLS) or 465 (SSL)</li>
                      <li><strong>Outlook:</strong> smtp-mail.outlook.com, Port 587 (TLS)</li>
                      <li><strong>Yahoo:</strong> smtp.mail.yahoo.com, Port 587 (TLS) or 465 (SSL)</li>
                      <li><strong>SendGrid:</strong> smtp.sendgrid.net, Port 587 (TLS)</li>
                    </ul>
                    <p className="mt-2">
                      <strong>Note:</strong> For Gmail, you may need to use an App Password instead of your regular password.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Confirmation Dialog */}
      {showConfirmation && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex items-center justify-center mx-auto w-12 h-12 rounded-full bg-red-100">
                <ShieldExclamationIcon className="h-6 w-6 text-red-600" />
              </div>
              <div className="mt-4 text-center">
                <h3 className="text-lg font-medium text-gray-900">
                  Confirm SMTP Configuration Changes
                </h3>
                <div className="mt-2 px-7 py-3">
                  <p className="text-sm text-gray-500 mb-3">
                    You are about to save critical email system settings. This will immediately affect:
                  </p>
                  <ul className="text-sm text-red-600 text-left space-y-1">
                    <li>• All outreach email sending</li>
                    <li>• Follow-up email automation</li>
                    <li>• System email notifications</li>
                  </ul>
                  <p className="text-sm text-gray-700 mt-3 font-semibold">
                    Are you absolutely certain these settings are correct?
                  </p>
                </div>
                <div className="flex justify-center space-x-3 mt-4">
                  <button
                    onClick={cancelSaveSmtpSettings}
                    className="px-4 py-2 bg-gray-300 text-gray-800 text-sm font-medium rounded-md hover:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-300"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={confirmSaveSmtpSettings}
                    disabled={saving}
                    className="px-4 py-2 bg-red-600 text-white text-sm font-medium rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 disabled:opacity-50"
                  >
                    {saving ? 'Saving...' : 'Yes, Save Settings'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ApiKeysSettings; 