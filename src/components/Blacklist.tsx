import React, { useState, useEffect } from 'react';
import { doc, getDoc, setDoc } from 'firebase/firestore';
import { db } from '../firebase/config';
import { BlacklistEmails } from '../types';
import { TrashIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

const Blacklist: React.FC = () => {
  const [blacklist, setBlacklist] = useState<BlacklistEmails>({ list: [] });
  const [newEmail, setNewEmail] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadBlacklist();
  }, []);

  const loadBlacklist = async () => {
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
  };

  const saveBlacklist = async (updatedList: string[]) => {
    setSaving(true);
    try {
      const docRef = doc(db, 'blacklist', 'emails');
      const newBlacklist = { list: updatedList };
      await setDoc(docRef, newBlacklist);
      setBlacklist(newBlacklist);
      toast.success('Blacklist updated successfully!');
    } catch (error) {
      console.error('Error saving blacklist:', error);
      toast.error('Failed to update blacklist');
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
      toast.error('Email is already in the blacklist');
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
    <div className="bg-white shadow rounded-lg">
      <div className="px-4 py-5 sm:p-6">
        <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
          Email Blacklist
        </h3>
        
        {/* Add new email */}
        <div className="mb-6">
          <label htmlFor="newEmail" className="block text-sm font-medium text-gray-700 mb-2">
            Add Email to Blacklist
          </label>
          <div className="flex space-x-2">
            <input
              type="email"
              id="newEmail"
              value={newEmail}
              onChange={(e) => setNewEmail(e.target.value)}
              onKeyPress={handleKeyPress}
              className="flex-1 shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
              placeholder="Enter email address"
            />
            <button
              onClick={addEmail}
              disabled={saving}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Add
            </button>
          </div>
        </div>

        {/* Blacklist display */}
        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-3">
            Blacklisted Emails ({blacklist.list.length})
          </h4>
          
          {blacklist.list.length === 0 ? (
            <p className="text-sm text-gray-500 italic">No emails in blacklist</p>
          ) : (
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {blacklist.list.map((email, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-md"
                >
                  <span className="text-sm text-gray-900">{email}</span>
                  <button
                    onClick={() => removeEmail(email)}
                    disabled={saving}
                    className="text-red-600 hover:text-red-800 disabled:opacity-50 disabled:cursor-not-allowed"
                    title="Remove from blacklist"
                  >
                    <TrashIcon className="h-4 w-4" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {blacklist.list.length > 0 && (
          <div className="mt-4 text-sm text-gray-500">
            <p>
              Blacklisted emails will be automatically excluded from all outreach campaigns.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Blacklist; 