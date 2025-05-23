import React, { useState, useEffect } from 'react';
import { doc, getDoc, setDoc } from 'firebase/firestore';
import { db } from '../firebase/config';
import { ApiKeys } from '../types';
import { EyeIcon, EyeSlashIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

const ApiKeysComponent: React.FC = () => {
  const [apiKeys, setApiKeys] = useState<ApiKeys>({
    openaiApiKey: '',
    apolloApiKey: '',
    apifiApiKey: '',
    perplexityApiKey: '',
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showKeys, setShowKeys] = useState({
    openai: false,
    apollo: false,
    apifi: false,
    perplexity: false,
  });

  useEffect(() => {
    loadApiKeys();
  }, []);

  const loadApiKeys = async () => {
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
  };

  const saveApiKeys = async () => {
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
  );
};

export default ApiKeysComponent; 