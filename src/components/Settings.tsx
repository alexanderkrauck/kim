import React, { useState, useEffect } from 'react';
import { doc, getDoc, setDoc } from 'firebase/firestore';
import { db } from '../firebase/config';
import { GlobalSettings } from '../types';
import toast from 'react-hot-toast';

const Settings: React.FC = () => {
  const [settings, setSettings] = useState<GlobalSettings>({
    followupDelayDays: 7,
    maxFollowups: 3,
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const docRef = doc(db, 'settings', 'global');
      const docSnap = await getDoc(docRef);
      
      if (docSnap.exists()) {
        setSettings(docSnap.data() as GlobalSettings);
      }
    } catch (error) {
      console.error('Error loading settings:', error);
      toast.error('Failed to load settings');
    } finally {
      setLoading(false);
    }
  };

  const saveSettings = async () => {
    setSaving(true);
    try {
      const docRef = doc(db, 'settings', 'global');
      await setDoc(docRef, settings);
      toast.success('Settings saved successfully!');
    } catch (error) {
      console.error('Error saving settings:', error);
      toast.error('Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const handleInputChange = (field: keyof GlobalSettings, value: number) => {
    setSettings(prev => ({
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
          Global Settings
        </h3>
        
        <div className="space-y-6">
          <div>
            <label htmlFor="followupDelayDays" className="block text-sm font-medium text-gray-700">
              Follow-up Delay (Days)
            </label>
            <div className="mt-1">
              <input
                type="number"
                id="followupDelayDays"
                min="1"
                max="30"
                value={settings.followupDelayDays}
                onChange={(e) => handleInputChange('followupDelayDays', parseInt(e.target.value) || 1)}
                className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
              />
            </div>
            <p className="mt-2 text-sm text-gray-500">
              Number of days to wait before sending a follow-up email
            </p>
          </div>

          <div>
            <label htmlFor="maxFollowups" className="block text-sm font-medium text-gray-700">
              Maximum Follow-ups
            </label>
            <div className="mt-1">
              <input
                type="number"
                id="maxFollowups"
                min="1"
                max="10"
                value={settings.maxFollowups}
                onChange={(e) => handleInputChange('maxFollowups', parseInt(e.target.value) || 1)}
                className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
              />
            </div>
            <p className="mt-2 text-sm text-gray-500">
              Maximum number of follow-up emails to send per lead
            </p>
          </div>
        </div>

        <div className="mt-6">
          <button
            onClick={saveSettings}
            disabled={saving}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {saving ? 'Saving...' : 'Save Settings'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default Settings; 