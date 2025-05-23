import React, { useState, useEffect, useCallback } from 'react';
import { doc, getDoc, setDoc } from 'firebase/firestore';
import { db } from '../firebase/config';
import { BlacklistEmails } from '../types';
import { TrashIcon, ExclamationTriangleIcon, GlobeAltIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import { useAuth } from '../contexts/AuthContext';

const Blacklist: React.FC = () => {
  const [blacklist, setBlacklist] = useState<BlacklistEmails>({ list: [] });
  const [newEmail, setNewEmail] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const auth = useAuth();

  const loadBlacklist = useCallback(async () => {
    if (!auth.currentUser) {
      console.error('User not authenticated');
      toast.error('Please log in to access blacklist');
      setLoading(false);
      return;
    }

    try {
      const docRef = doc(db, 'blacklist', 'emails');
      const docSnap = await getDoc(docRef);
      
      if (docSnap.exists()) {
        setBlacklist(docSnap.data() as BlacklistEmails);
      }
    } catch (error) {
      console.error('Error loading blacklist:', error);
      toast.error('Failed to load blacklist');
    } finally {
      setLoading(false);
    }
  }, [auth.currentUser]);

  useEffect(() => {
    if (auth.currentUser) {
      loadBlacklist();
    }
  }, [auth.currentUser, loadBlacklist]);

  const saveBlacklist = async (updatedList: string[]) => {
    setSaving(true);
    try {
      const docRef = doc(db, 'blacklist', 'emails');
      const newBlacklist = { list: updatedList };
      await setDoc(docRef, newBlacklist);
      setBlacklist(newBlacklist);
      toast.success('Global blacklist updated successfully!');
    } catch (error) {
      console.error('Error saving blacklist:', error);
      toast.error('Failed to update global blacklist');
    } finally {
      setSaving(false);
    }
  };

  const addEmail = async () => {
    if (!newEmail.trim()) {
      toast.error('Please enter an email address');
      return;
    }

    const email = newEmail.trim().toLowerCase();
    
    // Basic email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      toast.error('Please enter a valid email address');
      return;
    }

    if (blacklist.list.includes(email)) {
      toast.error('Email is already in the global blacklist');
      return;
    }

    const updatedList = [...blacklist.list, email];
    await saveBlacklist(updatedList);
    setNewEmail('');
  };

  const removeEmail = async (emailToRemove: string) => {
    const updatedList = blacklist.list.filter(email => email !== emailToRemove);
    await saveBlacklist(updatedList);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      addEmail();
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
      <div>
        <h2 className="text-2xl font-bold text-gray-900 flex items-center">
          <GlobeAltIcon className="h-6 w-6 mr-2" />
          Global Email Blacklist
        </h2>
        <p className="text-gray-600 mt-1">
          Permanently block email addresses across all projects and campaigns
        </p>
      </div>

      {/* Warning Notice */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <div className="flex">
          <ExclamationTriangleIcon className="h-5 w-5 text-yellow-400 mt-0.5 mr-3 flex-shrink-0" />
          <div>
            <h3 className="text-sm font-medium text-yellow-800">Global Blacklist Impact</h3>
            <div className="mt-1 text-sm text-yellow-700">
              <p>Emails added here will be:</p>
              <ul className="list-disc list-inside mt-1 space-y-1">
                <li>Blocked from <strong>all projects</strong> and campaigns</li>
                <li>Automatically excluded from future outreach</li>
                <li>Unable to receive any emails from this system</li>
                <li>Permanently blocked until manually removed</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          {/* Add new email */}
          <div className="mb-6">
            <label htmlFor="newEmail" className="block text-sm font-medium text-gray-700 mb-2">
              Add Email to Global Blacklist
            </label>
            <div className="flex space-x-2">
              <input
                type="email"
                id="newEmail"
                value={newEmail}
                onChange={(e) => setNewEmail(e.target.value)}
                onKeyPress={handleKeyPress}
                className="flex-1 shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                placeholder="Enter email address to block globally"
              />
              <button
                onClick={addEmail}
                disabled={saving}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Block Globally
              </button>
            </div>
            <p className="mt-1 text-xs text-gray-500">
              This will block the email address from all current and future projects
            </p>
          </div>

          {/* Blacklist display */}
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-3 flex items-center">
              <GlobeAltIcon className="h-4 w-4 mr-1" />
              Globally Blacklisted Emails ({blacklist.list.length})
            </h4>
            
            {blacklist.list.length === 0 ? (
              <div className="text-center py-8">
                <GlobeAltIcon className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">No globally blacklisted emails</h3>
                <p className="mt-1 text-sm text-gray-500">
                  Add email addresses that should be blocked across all projects
                </p>
              </div>
            ) : (
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {blacklist.list.map((email, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 bg-red-50 border border-red-200 rounded-md"
                  >
                    <div className="flex items-center">
                      <GlobeAltIcon className="h-4 w-4 text-red-500 mr-2" />
                      <span className="text-sm text-gray-900">{email}</span>
                      <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">
                        Global
                      </span>
                    </div>
                    <button
                      onClick={() => removeEmail(email)}
                      disabled={saving}
                      className="text-red-600 hover:text-red-800 disabled:opacity-50 disabled:cursor-not-allowed"
                      title="Remove from global blacklist"
                    >
                      <TrashIcon className="h-4 w-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {blacklist.list.length > 0 && (
            <div className="mt-6 bg-gray-50 border border-gray-200 rounded-lg p-4">
              <h4 className="text-sm font-medium text-gray-900 mb-2">How Global Blacklist Works</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• These emails are blocked across <strong>all projects</strong></li>
                <li>• They cannot receive any outreach emails from this system</li>
                <li>• Individual projects can also blacklist emails separately</li>
                <li>• To un-blacklist someone from a specific project only, go to that project's leads</li>
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Blacklist; 