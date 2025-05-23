import React, { useState, useEffect } from 'react';
import { doc, getDoc, setDoc } from 'firebase/firestore';
import { db } from '../firebase/config';
import { GlobalPrompts } from '../types';
import { 
  DocumentTextIcon,
  InformationCircleIcon,
  LightBulbIcon
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

const Prompts: React.FC = () => {
  const [globalPrompts, setGlobalPrompts] = useState<GlobalPrompts>({
    outreachPrompt: '',
    followupPrompt: '',
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadGlobalPrompts();
  }, []);

  const loadGlobalPrompts = async () => {
    try {
      const docRef = doc(db, 'prompts', 'global');
      const docSnap = await getDoc(docRef);
      
      if (docSnap.exists()) {
        setGlobalPrompts(docSnap.data() as GlobalPrompts);
      }
    } catch (error) {
      console.error('Error loading global prompts:', error);
      toast.error('Failed to load global prompts');
    } finally {
      setLoading(false);
    }
  };

  const saveGlobalPrompts = async () => {
    setSaving(true);
    try {
      const docRef = doc(db, 'prompts', 'global');
      await setDoc(docRef, globalPrompts);
      toast.success('Global AI prompts saved successfully!');
    } catch (error) {
      console.error('Error saving global prompts:', error);
      toast.error('Failed to save global prompts');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-indigo-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">AI Prompt Templates</h2>
          <p className="text-gray-600 mt-1">
            Configure global AI instructions for email generation across all projects
          </p>
        </div>
        <button
          onClick={saveGlobalPrompts}
          disabled={saving}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50"
        >
          {saving ? 'Saving...' : 'Save Templates'}
        </button>
      </div>

      {/* Information Box */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex">
          <InformationCircleIcon className="h-5 w-5 text-blue-400 mt-0.5 mr-3 flex-shrink-0" />
          <div>
            <h3 className="text-sm font-medium text-blue-800">About AI Prompt Templates</h3>
            <p className="mt-1 text-sm text-blue-700">
              These are the default AI instructions used across all projects. Individual projects can override 
              these templates with project-specific instructions in their settings.
            </p>
          </div>
        </div>
      </div>

      {/* Global Templates */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900 mb-6 flex items-center">
            <DocumentTextIcon className="h-5 w-5 mr-2" />
            Global AI Instructions
          </h3>
          
          <div className="space-y-6">
            <div>
              <label htmlFor="globalOutreachPrompt" className="block text-sm font-medium text-gray-700 mb-2">
                Default Outreach Email Instructions
              </label>
              <div className="bg-gray-50 border border-gray-200 rounded-md p-3 mb-3">
                <div className="flex items-start">
                  <LightBulbIcon className="h-4 w-4 text-yellow-500 mt-0.5 mr-2 flex-shrink-0" />
                  <p className="text-xs text-gray-600">
                    <strong>Example:</strong> "Write professional, personalized outreach emails. Keep them concise (under 150 words). 
                    Include a clear value proposition and specific call-to-action. Use a friendly but professional tone. 
                    Always personalize with the recipient's name and company."
                  </p>
                </div>
              </div>
              <textarea
                id="globalOutreachPrompt"
                rows={8}
                value={globalPrompts.outreachPrompt}
                onChange={(e) => setGlobalPrompts(prev => ({ ...prev, outreachPrompt: e.target.value }))}
                className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                placeholder="Enter default AI instructions for generating outreach emails..."
              />
            </div>

            <div>
              <label htmlFor="globalFollowupPrompt" className="block text-sm font-medium text-gray-700 mb-2">
                Default Follow-up Email Instructions
              </label>
              <div className="bg-gray-50 border border-gray-200 rounded-md p-3 mb-3">
                <div className="flex items-start">
                  <LightBulbIcon className="h-4 w-4 text-yellow-500 mt-0.5 mr-2 flex-shrink-0" />
                  <p className="text-xs text-gray-600">
                    <strong>Example:</strong> "Write follow-up emails that add value. Reference the previous email briefly. 
                    Provide additional insights or resources. Keep tone persistent but not pushy. 
                    Include social proof or case studies when relevant."
                  </p>
                </div>
              </div>
              <textarea
                id="globalFollowupPrompt"
                rows={8}
                value={globalPrompts.followupPrompt}
                onChange={(e) => setGlobalPrompts(prev => ({ ...prev, followupPrompt: e.target.value }))}
                className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                placeholder="Enter default AI instructions for generating follow-up emails..."
              />
            </div>
          </div>
        </div>
      </div>

      {/* Usage Information */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <h4 className="text-sm font-medium text-gray-900 mb-2">How These Templates Work</h4>
        <ul className="text-sm text-gray-600 space-y-1">
          <li>• These instructions are used by default for all projects</li>
          <li>• Projects can override these with custom instructions in their individual settings</li>
          <li>• Changes here affect all projects using global templates</li>
          <li>• Keep instructions clear and specific for best AI performance</li>
        </ul>
      </div>
    </div>
  );
};

export default Prompts; 