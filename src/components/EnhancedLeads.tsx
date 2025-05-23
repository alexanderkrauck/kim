import React, { useState, useEffect } from 'react';
import { collection, getDocs, addDoc, doc, updateDoc, query, where, orderBy, getDoc, setDoc } from 'firebase/firestore';
import { httpsCallable } from 'firebase/functions';
import { db, functions, auth } from '../firebase/config';
import { Lead, Project, LeadImport } from '../types';
import { 
  NoSymbolIcon, 
  PaperAirplaneIcon,
  ExclamationTriangleIcon,
  PlusIcon,
  ArrowDownTrayIcon,
  EyeIcon,
  ChevronUpIcon,
  ChevronDownIcon
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import { useAuth } from '../contexts/AuthContext';

interface EnhancedLeadsProps {
  selectedProject: Project | null;
}

const EnhancedLeads: React.FC<EnhancedLeadsProps> = ({ selectedProject }) => {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [showDetailedView, setShowDetailedView] = useState(false);
  const [sortField, setSortField] = useState<keyof Lead>('createdAt');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');
  const [retryCount, setRetryCount] = useState(0);
  const { currentUser } = useAuth();
  const [newLead, setNewLead] = useState<LeadImport>({
    email: '',
    name: '',
    company: '',
    source: '',
    notes: '',
  });

  useEffect(() => {
    if (selectedProject && currentUser) {
      setRetryCount(0);
      loadLeads();
    }
  }, [selectedProject, currentUser]);

  const loadLeads = async () => {
    if (!selectedProject) return;
    
    // Check authentication
    if (!currentUser) {
      console.error('User not authenticated');
      toast.error('Please log in to view leads');
      setLoading(false);
      return;
    }

    setLoading(true);
    try {
      console.log('Loading leads for project:', selectedProject.id);
      console.log('Current user:', currentUser.uid);
      
      // First, try a simple query without orderBy to avoid index issues
      const q = query(
        collection(db, 'leads'), 
        where('projectId', '==', selectedProject.id)
      );
      
      console.log('Executing Firestore query...');
      const querySnapshot = await getDocs(q);
      console.log('Query successful, documents found:', querySnapshot.size);
      
      const leadsData: Lead[] = [];
      querySnapshot.forEach((doc) => {
        try {
          const data = doc.data();
          console.log('Processing document:', doc.id, data);
          
          leadsData.push({
            id: doc.id,
            email: data.email || '',
            name: data.name || '',
            company: data.company || '',
            status: data.status || 'new',
            lastContacted: data.lastContacted?.toDate() || null,
            followupCount: data.followupCount || 0,
            createdAt: data.createdAt?.toDate() || new Date(),
            projectId: data.projectId || selectedProject.id,
            interactionSummary: data.interactionSummary || '',
            emailChain: data.emailChain || [],
            source: data.source || '',
            notes: data.notes || '',
          });
        } catch (docError) {
          console.error('Error processing document:', doc.id, docError);
        }
      });
      
      // Sort the data locally instead of in the query
      leadsData.sort((a, b) => {
        const aTime = a.createdAt?.getTime() || 0;
        const bTime = b.createdAt?.getTime() || 0;
        return bTime - aTime; // Descending order (newest first)
      });
      
      console.log('Successfully loaded leads:', leadsData.length);
      setLeads(leadsData);
      setRetryCount(0); // Reset retry count on success
    } catch (error: any) {
      console.error('Error loading leads:', error);
      
      // Provide more specific error messages
      let errorMessage = 'Failed to load leads';
      let shouldRetry = false;
      
      if (error.code === 'permission-denied') {
        errorMessage = 'Permission denied. Please check your authentication and Firestore rules.';
      } else if (error.code === 'failed-precondition') {
        errorMessage = 'Database index required. Please check the console for index creation instructions.';
      } else if (error.code === 'unavailable') {
        errorMessage = 'Database temporarily unavailable. Please try again.';
        shouldRetry = true;
      } else if (error.code === 'deadline-exceeded' || error.code === 'timeout') {
        errorMessage = 'Request timed out. Please try again.';
        shouldRetry = true;
      } else if (error.message) {
        errorMessage = `Failed to load leads: ${error.message}`;
        shouldRetry = true;
      }
      
      // Retry logic for transient errors
      if (shouldRetry && retryCount < 3) {
        console.log(`Retrying... Attempt ${retryCount + 1}/3`);
        setRetryCount(prev => prev + 1);
        setTimeout(() => {
          loadLeads();
        }, 1000 * (retryCount + 1)); // Exponential backoff
        return;
      }
      
      toast.error(errorMessage);
      
      // Set empty array so UI doesn't show loading state forever
      setLeads([]);
    } finally {
      setLoading(false);
    }
  };

  const addLead = async () => {
    if (!selectedProject) {
      toast.error('Please select a project first');
      return;
    }

    if (!newLead.email.trim()) {
      toast.error('Email is required');
      return;
    }

    // Basic email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(newLead.email)) {
      toast.error('Please enter a valid email address');
      return;
    }

    try {
      const leadData = {
        ...newLead,
        email: newLead.email.toLowerCase(),
        status: 'new' as const,
        lastContacted: null,
        followupCount: 0,
        createdAt: new Date(),
        projectId: selectedProject.id,
        interactionSummary: '',
        emailChain: [],
      };

      const docRef = await addDoc(collection(db, 'leads'), leadData);
      const createdLead: Lead = {
        id: docRef.id,
        ...leadData,
      };

      setLeads(prev => [createdLead, ...prev]);
      setNewLead({
        email: '',
        name: '',
        company: '',
        source: '',
        notes: '',
      });
      setShowAddForm(false);
      toast.success('Lead added successfully!');

      // Update project lead count
      const projectRef = doc(db, 'projects', selectedProject.id);
      await updateDoc(projectRef, {
        leadCount: leads.length + 1,
        updatedAt: new Date(),
      });
    } catch (error) {
      console.error('Error adding lead:', error);
      toast.error('Failed to add lead');
    }
  };

  const blacklistLead = async (leadId: string, email: string) => {
    setActionLoading(leadId);
    try {
      // Update lead status
      const leadRef = doc(db, 'leads', leadId);
      await updateDoc(leadRef, { status: 'blacklisted' });

      // Add to project-specific blacklist
      const blacklistRef = doc(db, 'blacklist', `project_${selectedProject?.id}`);
      const blacklistDoc = await getDoc(blacklistRef);
      let currentList: string[] = [];
      
      if (blacklistDoc.exists()) {
        const blacklistData = blacklistDoc.data();
        currentList = blacklistData.list || [];
      }

      if (!currentList.includes(email.toLowerCase())) {
        currentList.push(email.toLowerCase());
        await setDoc(blacklistRef, { 
          list: currentList,
          projectId: selectedProject?.id 
        });
      }

      // Update local state
      setLeads(prev => prev.map(lead => 
        lead.id === leadId ? { ...lead, status: 'blacklisted' as const } : lead
      ));

      toast.success('Lead blacklisted successfully');
    } catch (error) {
      console.error('Error blacklisting lead:', error);
      toast.error('Failed to blacklist lead');
    } finally {
      setActionLoading(null);
    }
  };

  const triggerFollowup = async (leadId: string) => {
    setActionLoading(leadId);
    try {
      const triggerFollowupFunction = httpsCallable(functions, 'triggerFollowup');
      await triggerFollowupFunction({ leadId });
      
      toast.success('Follow-up triggered successfully');
      await loadLeads();
    } catch (error) {
      console.error('Error triggering follow-up:', error);
      toast.error('Failed to trigger follow-up');
    } finally {
      setActionLoading(null);
    }
  };

  const exportToCSV = () => {
    if (leads.length === 0) {
      toast.error('No leads to export');
      return;
    }

    const headers = [
      'Email',
      'Name',
      'Company',
      'Status',
      'Last Contacted',
      'Follow-up Count',
      'Created At',
      'Source',
      'Notes',
      'Interaction Summary'
    ];

    const csvData = leads.map(lead => [
      lead.email,
      lead.name || '',
      lead.company || '',
      lead.status,
      lead.lastContacted ? lead.lastContacted.toISOString() : '',
      lead.followupCount.toString(),
      lead.createdAt.toISOString(),
      lead.source || '',
      lead.notes || '',
      lead.interactionSummary || ''
    ]);

    const csvContent = [headers, ...csvData]
      .map(row => row.map(field => `"${field}"`).join(','))
      .join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `leads_${selectedProject?.name || 'export'}_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    toast.success('Leads exported to CSV');
  };

  const handleSort = (field: keyof Lead) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const sortedLeads = [...leads].sort((a, b) => {
    const aValue = a[sortField];
    const bValue = b[sortField];
    
    if (aValue === null || aValue === undefined) return 1;
    if (bValue === null || bValue === undefined) return -1;
    
    if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1;
    if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1;
    return 0;
  });

  const getStatusBadge = (status: Lead['status']) => {
    const baseClasses = "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium";
    
    switch (status) {
      case 'new':
        return `${baseClasses} bg-blue-100 text-blue-800`;
      case 'emailed':
        return `${baseClasses} bg-yellow-100 text-yellow-800`;
      case 'responded':
        return `${baseClasses} bg-green-100 text-green-800`;
      case 'bounced':
        return `${baseClasses} bg-red-100 text-red-800`;
      case 'blacklisted':
        return `${baseClasses} bg-gray-100 text-gray-800`;
      default:
        return `${baseClasses} bg-gray-100 text-gray-800`;
    }
  };

  const formatDate = (date: Date | null) => {
    if (!date) return 'Never';
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  if (!selectedProject) {
    return (
      <div className="text-center py-12">
        <ExclamationTriangleIcon className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">No project selected</h3>
        <p className="mt-1 text-sm text-gray-500">
          Please select a project to view and manage leads.
        </p>
      </div>
    );
  }

  if (!currentUser) {
    return (
      <div className="text-center py-12">
        <ExclamationTriangleIcon className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">Authentication required</h3>
        <p className="mt-1 text-sm text-gray-500">
          Please log in to view and manage leads.
        </p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-indigo-500"></div>
        {retryCount > 0 && (
          <p className="ml-4 text-sm text-gray-600">
            Retrying... ({retryCount}/3)
          </p>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">
            Leads - {selectedProject.name}
          </h2>
          <p className="text-gray-600">
            {leads.length} leads in this project
          </p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={() => setShowDetailedView(!showDetailedView)}
            className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
          >
            <EyeIcon className="h-4 w-4 mr-2" />
            {showDetailedView ? 'Simple View' : 'Detailed View'}
          </button>
          <button
            onClick={exportToCSV}
            disabled={leads.length === 0}
            className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
          >
            <ArrowDownTrayIcon className="h-4 w-4 mr-2" />
            Export CSV
          </button>
          <button
            onClick={() => setShowAddForm(true)}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700"
          >
            <PlusIcon className="h-4 w-4 mr-2" />
            Add Lead
          </button>
        </div>
      </div>

      {/* Add Lead Form */}
      {showAddForm && (
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Add New Lead</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label htmlFor="leadEmail" className="block text-sm font-medium text-gray-700">
                Email *
              </label>
              <input
                type="email"
                id="leadEmail"
                value={newLead.email}
                onChange={(e) => setNewLead(prev => ({ ...prev, email: e.target.value }))}
                className="mt-1 shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                placeholder="lead@example.com"
              />
            </div>

            <div>
              <label htmlFor="leadName" className="block text-sm font-medium text-gray-700">
                Name
              </label>
              <input
                type="text"
                id="leadName"
                value={newLead.name}
                onChange={(e) => setNewLead(prev => ({ ...prev, name: e.target.value }))}
                className="mt-1 shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                placeholder="John Doe"
              />
            </div>

            <div>
              <label htmlFor="leadCompany" className="block text-sm font-medium text-gray-700">
                Company
              </label>
              <input
                type="text"
                id="leadCompany"
                value={newLead.company}
                onChange={(e) => setNewLead(prev => ({ ...prev, company: e.target.value }))}
                className="mt-1 shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                placeholder="Acme Corp"
              />
            </div>

            <div>
              <label htmlFor="leadSource" className="block text-sm font-medium text-gray-700">
                Source
              </label>
              <input
                type="text"
                id="leadSource"
                value={newLead.source}
                onChange={(e) => setNewLead(prev => ({ ...prev, source: e.target.value }))}
                className="mt-1 shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                placeholder="LinkedIn, Website, etc."
              />
            </div>

            <div className="md:col-span-2">
              <label htmlFor="leadNotes" className="block text-sm font-medium text-gray-700">
                Notes
              </label>
              <textarea
                id="leadNotes"
                rows={3}
                value={newLead.notes}
                onChange={(e) => setNewLead(prev => ({ ...prev, notes: e.target.value }))}
                className="mt-1 shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                placeholder="Additional notes about this lead..."
              />
            </div>
          </div>

          <div className="mt-6 flex justify-end space-x-3">
            <button
              onClick={() => setShowAddForm(false)}
              className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              onClick={addLead}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700"
            >
              Add Lead
            </button>
          </div>
        </div>
      )}

      {/* Leads Table */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          {leads.length === 0 ? (
            <div className="text-center py-12">
              <ExclamationTriangleIcon className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No leads found</h3>
              <p className="mt-1 text-sm text-gray-500">
                Get started by adding your first lead to this project.
              </p>
              {retryCount > 0 && (
                <div className="mt-4">
                  <button
                    onClick={() => {
                      setRetryCount(0);
                      loadLeads();
                    }}
                    className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                  >
                    Try Again
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-300">
                <thead className="bg-gray-50">
                  <tr>
                    {[
                      { key: 'email', label: 'Email' },
                      { key: 'name', label: 'Name' },
                      { key: 'company', label: 'Company' },
                      { key: 'status', label: 'Status' },
                      { key: 'lastContacted', label: 'Last Contacted' },
                      { key: 'followupCount', label: 'Follow-ups' },
                      ...(showDetailedView ? [
                        { key: 'source', label: 'Source' },
                        { key: 'createdAt', label: 'Created' },
                      ] : []),
                    ].map((column) => (
                      <th
                        key={column.key}
                        onClick={() => handleSort(column.key as keyof Lead)}
                        className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                      >
                        <div className="flex items-center space-x-1">
                          <span>{column.label}</span>
                          {sortField === column.key && (
                            sortDirection === 'asc' ? 
                              <ChevronUpIcon className="h-4 w-4" /> : 
                              <ChevronDownIcon className="h-4 w-4" />
                          )}
                        </div>
                      </th>
                    ))}
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {sortedLeads.map((lead) => (
                    <tr key={lead.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {lead.email}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {lead.name || '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {lead.company || '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={getStatusBadge(lead.status)}>
                          {lead.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatDate(lead.lastContacted)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {lead.followupCount}
                      </td>
                      {showDetailedView && (
                        <>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {lead.source || '-'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {formatDate(lead.createdAt)}
                          </td>
                        </>
                      )}
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                        {lead.status !== 'blacklisted' && (
                          <>
                            <button
                              onClick={() => blacklistLead(lead.id, lead.email)}
                              disabled={actionLoading === lead.id}
                              className="text-red-600 hover:text-red-900 disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center"
                              title="Blacklist this lead"
                            >
                              <NoSymbolIcon className="h-4 w-4 mr-1" />
                              Blacklist
                            </button>
                            
                            {(lead.status === 'emailed' || lead.status === 'new') && (
                              <button
                                onClick={() => triggerFollowup(lead.id)}
                                disabled={actionLoading === lead.id}
                                className="text-indigo-600 hover:text-indigo-900 disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center"
                                title="Send follow-up email"
                              >
                                <PaperAirplaneIcon className="h-4 w-4 mr-1" />
                                Follow-up
                              </button>
                            )}
                          </>
                        )}
                        
                        {actionLoading === lead.id && (
                          <span className="text-gray-500">Processing...</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default EnhancedLeads; 