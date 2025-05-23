import React, { useState, useEffect } from 'react';
import { doc, getDoc, setDoc } from 'firebase/firestore';
import { db } from '../firebase/config';
import { Prompts as PromptsType } from '../types';
import toast from 'react-hot-toast';

const Prompts: React.FC = () => {
  const [prompts, setPrompts] = useState<PromptsType>({
    outreachPrompt: '',
    followupPrompt: '',
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadPrompts();
  }, []);

  const loadPrompts = async () => {
    try {
      const docRef = doc(db, 'prompts', 'default');
      const docSnap = await getDoc(docRef);
      
      if (docSnap.exists()) {
        setPrompts(docSnap.data() as PromptsType);
      }
    } catch (error) {
      console.error('Error loading prompts:', error);
      toast.error('Failed to load prompts');
    } finally {
      setLoading(false);
    }
  };

  const savePrompts = async () => {
    setSaving(true);
    try {
      const docRef = doc(db, 'prompts', 'default');
      await setDoc(docRef, prompts);
      toast.success('Prompts saved successfully!');
    } catch (error) {
      console.error('Error saving prompts:', error);
      toast.error('Failed to save prompts');
    } finally {
      setSaving(false);
    }
  };

  const handleInputChange = (field: keyof PromptsType, value: string) => {
    setPrompts(prev => ({
      ...prev,
      [field]: value,
    }));
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-indigo-500"></div>
      </div>
    );
  }

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="px-4 py-5 sm:p-6">
        <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
          Email Prompts
        </h3>
        
        <div className="space-y-6">
          <div>
            <label htmlFor="outreachPrompt" className="block text-sm font-medium text-gray-700">
              Outreach Email Template
            </label>
            <div className="mt-1">
              <textarea
                id="outreachPrompt"
                rows={8}
                value={prompts.outreachPrompt}
                onChange={(e) => handleInputChange('outreachPrompt', e.target.value)}
                className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                placeholder="Enter your initial outreach email template here..."
              />
            </div>
            <p className="mt-2 text-sm text-gray-500">
              Template for the initial outreach email. You can use variables like {'{name}'} and {'{company}'}.
            </p>
          </div>

          <div>
            <label htmlFor="followupPrompt" className="block text-sm font-medium text-gray-700">
              Follow-up Email Template
            </label>
            <div className="mt-1">
              <textarea
                id="followupPrompt"
                rows={8}
                value={prompts.followupPrompt}
                onChange={(e) => handleInputChange('followupPrompt', e.target.value)}
                className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                placeholder="Enter your follow-up email template here..."
              />
            </div>
            <p className="mt-2 text-sm text-gray-500">
              Template for follow-up emails. You can use variables like {'{name}'} and {'{company}'}.
            </p>
          </div>
        </div>

        <div className="mt-6">
          <button
            onClick={savePrompts}
            disabled={saving}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {saving ? 'Saving...' : 'Save Prompts'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default Prompts; 