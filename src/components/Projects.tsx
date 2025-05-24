import React, { useState, useEffect, useCallback } from 'react';
import { collection, getDocs, addDoc, doc, updateDoc, query, orderBy, getDoc, setDoc } from 'firebase/firestore';
import { db } from '../firebase/config';
import { Project, ProjectPrompts, GlobalPrompts, GlobalSettings, ProjectSettings } from '../types';
import { 
  PlusIcon, 
  FolderIcon, 
  CalendarIcon, 
  MapPinIcon, 
  ArrowLeftIcon,
  Cog6ToothIcon,
  DocumentTextIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import { useAuth } from '../contexts/AuthContext';

interface ProjectsProps {
  onSelectProject: (project: Project | null) => void;
  selectedProject: Project | null;
}

const Projects: React.FC<ProjectsProps> = ({ onSelectProject, selectedProject }) => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showProjectSettings, setShowProjectSettings] = useState(false);
  const [creating, setCreating] = useState(false);
  const [activeTab, setActiveTab] = useState<'list' | 'global-settings'>('list');
  const [activeSettingsTab, setActiveSettingsTab] = useState<'details' | 'guidelines' | 'timing'>('details');
  const [activeGlobalTab, setActiveGlobalTab] = useState<'guidelines' | 'timing'>('guidelines');
  
  const [newProject, setNewProject] = useState<{
    name: string;
    areaDescription: string;
    projectDetails: string;
    location: {
      rawLocation: string;
      apolloLocationIds: string[];
      useLlmParsing: boolean;
    };
  }>({
    name: '',
    areaDescription: '',
    projectDetails: '',
    location: {
      rawLocation: '',
      apolloLocationIds: [] as string[],
      useLlmParsing: true
    }
  });

  const [editingProject, setEditingProject] = useState<Project | null>(null);
  const [projectPrompts, setProjectPrompts] = useState<ProjectPrompts>({
    outreachPrompt: '',
    followupPrompt: '',
    projectId: '',
    useGlobalPrompts: true,
  });
  const [globalPrompts, setGlobalPrompts] = useState<GlobalPrompts>({
    outreachPrompt: '',
    followupPrompt: '',
  });
  const [globalSettings, setGlobalSettings] = useState<GlobalSettings>({
    followupDelayDays: 7,
    maxFollowups: 3,
  });
  const [projectSettings, setProjectSettings] = useState<ProjectSettings>({
    followupDelayDays: 7,
    maxFollowups: 3,
    projectId: '',
    useGlobalSettings: true,
  });

  const auth = useAuth();

  const loadProjects = useCallback(async () => {
    if (!auth.currentUser) {
      console.error('User not authenticated');
      toast.error('Please log in to access projects');
      setLoading(false);
      return;
    }

    try {
      const q = query(collection(db, 'projects'), orderBy('createdAt', 'desc'));
      const querySnapshot = await getDocs(q);
      
      const projectsData: Project[] = [];
      querySnapshot.forEach((doc) => {
        const data = doc.data();
        projectsData.push({
          id: doc.id,
          name: data.name,
          areaDescription: data.areaDescription,
          projectDetails: data.projectDetails,
          emailConsiderations: data.emailConsiderations,
          followupConsiderations: data.followupConsiderations,
          createdAt: data.createdAt?.toDate() || new Date(),
          updatedAt: data.updatedAt?.toDate() || new Date(),
          isActive: data.isActive ?? true,
          leadCount: data.leadCount || 0,
        });
      });
      
      setProjects(projectsData);
    } catch (error) {
      console.error('Error loading projects:', error);
      toast.error('Failed to load projects');
    } finally {
      setLoading(false);
    }
  }, [auth.currentUser]);

  const loadGlobalPrompts = useCallback(async () => {
    try {
      const docRef = doc(db, 'prompts', 'global');
      const docSnap = await getDoc(docRef);
      
      if (docSnap.exists()) {
        setGlobalPrompts(docSnap.data() as GlobalPrompts);
      }
    } catch (error) {
      console.error('Error loading global prompts:', error);
      toast.error('Failed to load global prompts');
    }
  }, []);

  const loadGlobalSettings = useCallback(async () => {
    try {
      const docRef = doc(db, 'settings', 'global');
      const docSnap = await getDoc(docRef);
      
      if (docSnap.exists()) {
        setGlobalSettings(docSnap.data() as GlobalSettings);
      }
    } catch (error) {
      console.error('Error loading global settings:', error);
      toast.error('Failed to load global settings');
    }
  }, []);

  useEffect(() => {
    if (auth.currentUser) {
      loadProjects();
      loadGlobalPrompts();
      loadGlobalSettings();
    }
  }, [auth.currentUser, loadProjects, loadGlobalPrompts, loadGlobalSettings]);

  const loadProjectPrompts = useCallback(async () => {
    if (!editingProject) return;

    try {
      const docRef = doc(db, 'prompts', `project_${editingProject.id}`);
      const docSnap = await getDoc(docRef);
      
      if (docSnap.exists()) {
        setProjectPrompts(docSnap.data() as ProjectPrompts);
      } else {
        setProjectPrompts({
          outreachPrompt: '',
          followupPrompt: '',
          projectId: editingProject.id,
          useGlobalPrompts: true,
        });
      }
    } catch (error) {
      console.error('Error loading project prompts:', error);
      toast.error('Failed to load project prompts');
    }
  }, [editingProject]);

  const loadProjectSettings = useCallback(async () => {
    if (!editingProject) return;

    try {
      const docRef = doc(db, 'settings', `project_${editingProject.id}`);
      const docSnap = await getDoc(docRef);
      
      if (docSnap.exists()) {
        setProjectSettings(docSnap.data() as ProjectSettings);
      } else {
        setProjectSettings({
          followupDelayDays: globalSettings.followupDelayDays,
          maxFollowups: globalSettings.maxFollowups,
          projectId: editingProject.id,
          useGlobalSettings: true,
        });
      }
    } catch (error) {
      console.error('Error loading project settings:', error);
      toast.error('Failed to load project settings');
    }
  }, [editingProject, globalSettings]);

  const createProject = async () => {
    if (!newProject.name.trim()) {
      toast.error('Project name is required');
      return;
    }

    if (!newProject.areaDescription.trim()) {
      toast.error('Area description is required');
      return;
    }

    if (newProject.projectDetails.length > 5000) {
      toast.error('Project details must be under 5000 characters');
      return;
    }

    setCreating(true);
    try {
      const projectData = {
        name: newProject.name,
        areaDescription: newProject.areaDescription,
        projectDetails: newProject.projectDetails,
        emailConsiderations: '',
        followupConsiderations: '',
        createdAt: new Date(),
        updatedAt: new Date(),
        isActive: true,
        leadCount: 0,
      };

      const docRef = await addDoc(collection(db, 'projects'), projectData);
      
      // Save location configuration separately
      if (newProject.location.rawLocation || newProject.location.apolloLocationIds.length > 0) {
        const locationRef = doc(db, 'settings', `project_${docRef.id}_location`);
        await setDoc(locationRef, {
          rawLocation: newProject.location.rawLocation,
          apolloLocationIds: newProject.location.apolloLocationIds,
          useLlmParsing: newProject.location.useLlmParsing
        });
      }
      const createdProject: Project = {
        id: docRef.id,
        ...projectData,
      };

      setProjects(prev => [createdProject, ...prev]);
      setNewProject({
        name: '',
        areaDescription: '',
        projectDetails: '',
        location: {
          rawLocation: '',
          apolloLocationIds: [] as string[],
          useLlmParsing: true
        }
      });
      setShowCreateForm(false);
      toast.success('Project created successfully!');
    } catch (error) {
      console.error('Error creating project:', error);
      toast.error('Failed to create project');
    } finally {
      setCreating(false);
    }
  };

  const saveGlobalPrompts = async () => {
    setSaving(true);
    try {
      const docRef = doc(db, 'prompts', 'global');
      await setDoc(docRef, globalPrompts);
      toast.success('Global email guidelines saved successfully!');
    } catch (error) {
      console.error('Error saving global prompts:', error);
      toast.error('Failed to save global email guidelines');
    } finally {
      setSaving(false);
    }
  };

  const saveGlobalSettings = async () => {
    setSaving(true);
    try {
      const docRef = doc(db, 'settings', 'global');
      await setDoc(docRef, globalSettings);
      toast.success('Global timing settings saved successfully!');
    } catch (error) {
      console.error('Error saving global settings:', error);
      toast.error('Failed to save global timing settings');
    } finally {
      setSaving(false);
    }
  };

  const saveProjectSettings = async () => {
    if (!editingProject) return;

    setSaving(true);
    try {
      const docRef = doc(db, 'settings', `project_${editingProject.id}`);
      await setDoc(docRef, {
        ...projectSettings,
        projectId: editingProject.id,
      });
      toast.success('Project timing settings saved successfully!');
    } catch (error) {
      console.error('Error saving project settings:', error);
      toast.error('Failed to save project timing settings');
    } finally {
      setSaving(false);
    }
  };

  const saveProjectPrompts = async () => {
    if (!editingProject) return;

    setSaving(true);
    try {
      const docRef = doc(db, 'prompts', `project_${editingProject.id}`);
      await setDoc(docRef, {
        ...projectPrompts,
        projectId: editingProject.id,
      });
      toast.success('Project prompts saved successfully!');
    } catch (error) {
      console.error('Error saving project prompts:', error);
      toast.error('Failed to save project prompts');
    } finally {
      setSaving(false);
    }
  };

  const saveProjectDetails = async () => {
    if (!editingProject) return;

    setSaving(true);
    try {
      const projectRef = doc(db, 'projects', editingProject.id);
      await updateDoc(projectRef, {
        name: editingProject.name,
        areaDescription: editingProject.areaDescription,
        projectDetails: editingProject.projectDetails,
        updatedAt: new Date(),
      });

      // Update local projects list
      setProjects(prev => prev.map(p => 
        p.id === editingProject.id ? { ...editingProject, updatedAt: new Date() } : p
      ));

      toast.success('Project details saved successfully!');
    } catch (error) {
      console.error('Error saving project details:', error);
      toast.error('Failed to save project details');
    } finally {
      setSaving(false);
    }
  };

  useEffect(() => {
    if (editingProject && showProjectSettings) {
      loadProjectPrompts();
      loadProjectSettings();
    }
  }, [editingProject, showProjectSettings, loadProjectPrompts, loadProjectSettings]);

  const handleProjectSelect = (project: Project) => {
    setShowProjectSettings(true);
    setActiveSettingsTab('details');
    setEditingProject({ ...project });
    // Don't call onSelectProject here - we're staying in the Projects tab
  };

  const handleBackToList = () => {
    setShowProjectSettings(false);
    setEditingProject(null);
    // Don't call onSelectProject(null) - we're managing project selection locally now
  };

  const formatDate = (date: Date) => {
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-indigo-500"></div>
      </div>
    );
  }

  // Project Settings View
  if (showProjectSettings && editingProject) {
    return (
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <button
              onClick={handleBackToList}
              className="mr-4 p-2 text-gray-400 hover:text-gray-600"
            >
              <ArrowLeftIcon className="h-5 w-5" />
            </button>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">{editingProject.name}</h2>
              <p className="text-gray-600">Project Settings & Configuration</p>
            </div>
          </div>
          <div className="flex space-x-3">
            <button
              onClick={() => {
                onSelectProject(editingProject);
                // This will trigger the App.tsx logic to switch to leads tab
              }}
              className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md shadow-sm text-gray-700 bg-white hover:bg-gray-50"
            >
              View Leads
            </button>
            <button
              onClick={saveProjectSettings}
              disabled={saving}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </div>

        {/* Settings Tabs */}
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveSettingsTab('details')}
              className={`${
                activeSettingsTab === 'details'
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm inline-flex items-center`}
            >
              <Cog6ToothIcon className="h-5 w-5 mr-2" />
              Project Details
            </button>
            <button
              onClick={() => setActiveSettingsTab('guidelines')}
              className={`${
                activeSettingsTab === 'guidelines'
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm inline-flex items-center`}
            >
              <DocumentTextIcon className="h-5 w-5 mr-2" />
              Email Guidelines
            </button>
            <button
              onClick={() => setActiveSettingsTab('timing')}
              className={`${
                activeSettingsTab === 'timing'
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm inline-flex items-center`}
            >
              <Cog6ToothIcon className="h-5 w-5 mr-2" />
              Timing Settings
            </button>
          </nav>
        </div>

        {/* Project Details Tab */}
        {activeSettingsTab === 'details' && (
          <div className="bg-white shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                Project Information
              </h3>
              
              <div className="space-y-6">
                <div>
                  <label htmlFor="editProjectName" className="block text-sm font-medium text-gray-700">
                    Project Name *
                  </label>
                  <input
                    type="text"
                    id="editProjectName"
                    value={editingProject.name}
                    onChange={(e) => setEditingProject(prev => prev ? { ...prev, name: e.target.value } : null)}
                    className="mt-1 shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                  />
                </div>

                <div>
                  <label htmlFor="editAreaDescription" className="block text-sm font-medium text-gray-700">
                    Area Description *
                  </label>
                  <input
                    type="text"
                    id="editAreaDescription"
                    value={editingProject.areaDescription}
                    onChange={(e) => setEditingProject(prev => prev ? { ...prev, areaDescription: e.target.value } : null)}
                    className="mt-1 shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                    placeholder="Exact address and specification"
                  />
                  <p className="mt-1 text-sm text-gray-500">
                    Provide an exact address and specification of the target area for this project
                  </p>
                </div>

                <div>
                  <label htmlFor="editProjectDetails" className="block text-sm font-medium text-gray-700">
                    Project Details
                  </label>
                  <textarea
                    id="editProjectDetails"
                    rows={8}
                    value={editingProject.projectDetails}
                    onChange={(e) => setEditingProject(prev => prev ? { ...prev, projectDetails: e.target.value } : null)}
                    className="mt-1 shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                    placeholder="Describe your project in detail..."
                    maxLength={5000}
                  />
                  <p className="mt-1 text-sm text-gray-500">
                    {editingProject.projectDetails.length}/5000 characters
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Email Guidelines Tab */}
        {activeSettingsTab === 'guidelines' && (
          <div className="bg-white shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                Email Guidelines & AI Instructions
              </h3>
              <p className="text-sm text-gray-600 mb-6">
                Configure how AI should write emails for this project. These guidelines serve as instructions for AI email generation.
              </p>

              {/* Global vs Project-Specific Toggle */}
              <div className="mb-6">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={projectPrompts.useGlobalPrompts}
                    onChange={(e) => setProjectPrompts(prev => ({ ...prev, useGlobalPrompts: e.target.checked }))}
                    className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                  />
                  <span className="ml-2 text-sm text-gray-700">
                    Use global email guidelines (recommended for consistency)
                  </span>
                </label>
              </div>
              
              <div className="space-y-6">
                <div>
                  <label htmlFor="editEmailConsiderations" className="block text-sm font-medium text-gray-700 mb-2">
                    Outreach Email Guidelines
                  </label>
                  <div className="bg-gray-50 border border-gray-200 rounded-md p-3 mb-2">
                    <p className="text-xs text-gray-600">
                      <strong>AI Instructions for outreach emails:</strong> Tell the AI how to write initial outreach emails. 
                      Include tone, style, key points to mention, and call-to-action guidelines.
                    </p>
                  </div>
                  <textarea
                    id="editEmailConsiderations"
                    rows={6}
                    value={projectPrompts.useGlobalPrompts ? '' : projectPrompts.outreachPrompt}
                    onChange={(e) => setProjectPrompts(prev => ({ ...prev, outreachPrompt: e.target.value }))}
                    disabled={projectPrompts.useGlobalPrompts}
                    className={`shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md ${
                      projectPrompts.useGlobalPrompts ? 'bg-gray-100 text-gray-500 cursor-not-allowed' : ''
                    }`}
                    placeholder="Example: Write professional, personalized outreach emails. Keep them concise (under 150 words). Include a clear value proposition and specific call-to-action. Use a friendly but professional tone. Always personalize with the recipient's name and company."
                    maxLength={300}
                  />
                  <p className="mt-1 text-sm text-gray-500">
                    {projectPrompts.outreachPrompt.length}/300 characters
                  </p>
                </div>

                <div>
                  <label htmlFor="editFollowupConsiderations" className="block text-sm font-medium text-gray-700 mb-2">
                    Follow-up Email Guidelines
                  </label>
                  <div className="bg-gray-50 border border-gray-200 rounded-md p-3 mb-2">
                    <p className="text-xs text-gray-600">
                      <strong>AI Instructions for follow-up emails:</strong> Tell the AI how to write follow-up emails. 
                      Include timing approach, how to reference previous emails, and value-add strategies.
                    </p>
                  </div>
                  <textarea
                    id="editFollowupConsiderations"
                    rows={6}
                    value={projectPrompts.useGlobalPrompts ? '' : projectPrompts.followupPrompt}
                    onChange={(e) => setProjectPrompts(prev => ({ ...prev, followupPrompt: e.target.value }))}
                    disabled={projectPrompts.useGlobalPrompts}
                    className={`shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md ${
                      projectPrompts.useGlobalPrompts ? 'bg-gray-100 text-gray-500 cursor-not-allowed' : ''
                    }`}
                    placeholder="Example: Write follow-up emails that add value. Reference the previous email briefly. Provide additional insights or resources. Keep tone persistent but not pushy. Include social proof or case studies when relevant."
                    maxLength={300}
                  />
                  <p className="mt-1 text-sm text-gray-500">
                    {projectPrompts.followupPrompt.length}/300 characters
                  </p>
                </div>
              </div>

              <div className="mt-6">
                <button
                  onClick={saveProjectPrompts}
                  disabled={saving}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50"
                >
                  {saving ? 'Saving...' : 'Save Email Guidelines'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Timing Settings Tab */}
        {activeSettingsTab === 'timing' && (
          <div className="space-y-6">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex">
                <InformationCircleIcon className="h-5 w-5 text-blue-400 mt-0.5 mr-3 flex-shrink-0" />
                <div>
                  <h3 className="text-sm font-medium text-blue-800">Project Timing Settings</h3>
                  <div className="mt-1 text-sm text-blue-700">
                    <p>Configure follow-up timing for this project. You can use global defaults or customize timing specifically for this project.</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <div className="flex items-center">
                <input
                  id="useGlobalSettings"
                  type="checkbox"
                  checked={projectSettings.useGlobalSettings}
                  onChange={(e) => setProjectSettings(prev => ({ 
                    ...prev, 
                    useGlobalSettings: e.target.checked,
                    followupDelayDays: e.target.checked ? globalSettings.followupDelayDays : prev.followupDelayDays,
                    maxFollowups: e.target.checked ? globalSettings.maxFollowups : prev.maxFollowups,
                  }))}
                  className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                />
                <label htmlFor="useGlobalSettings" className="ml-2 block text-sm text-gray-900">
                  Use global timing settings
                </label>
              </div>

              {!projectSettings.useGlobalSettings && (
                <div className="space-y-4 pl-6 border-l-2 border-gray-200">
                  <div>
                    <label htmlFor="projectFollowupDelayDays" className="block text-sm font-medium text-gray-700">
                      Follow-up Delay (Days)
                    </label>
                    <div className="mt-1">
                      <input
                        type="number"
                        id="projectFollowupDelayDays"
                        min="1"
                        max="30"
                        value={projectSettings.followupDelayDays}
                        onChange={(e) => setProjectSettings(prev => ({ 
                          ...prev, 
                          followupDelayDays: parseInt(e.target.value) || 1 
                        }))}
                        className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                      />
                    </div>
                    <p className="mt-2 text-sm text-gray-500">
                      Number of days to wait before sending a follow-up email for this project
                    </p>
                  </div>

                  <div>
                    <label htmlFor="projectMaxFollowups" className="block text-sm font-medium text-gray-700">
                      Maximum Follow-ups
                    </label>
                    <div className="mt-1">
                      <input
                        type="number"
                        id="projectMaxFollowups"
                        min="1"
                        max="10"
                        value={projectSettings.maxFollowups}
                        onChange={(e) => setProjectSettings(prev => ({ 
                          ...prev, 
                          maxFollowups: parseInt(e.target.value) || 1 
                        }))}
                        className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                      />
                    </div>
                    <p className="mt-2 text-sm text-gray-500">
                      Maximum number of follow-up emails to send per lead for this project
                    </p>
                  </div>
                </div>
              )}

              {projectSettings.useGlobalSettings && (
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                  <h4 className="text-sm font-medium text-gray-900 mb-2">Current Global Settings</h4>
                  <div className="text-sm text-gray-600 space-y-1">
                    <p>• Follow-up Delay: {globalSettings.followupDelayDays} days</p>
                    <p>• Maximum Follow-ups: {globalSettings.maxFollowups}</p>
                  </div>
                </div>
              )}
            </div>

            <div className="flex justify-end">
              <button
                onClick={saveProjectSettings}
                disabled={saving}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {saving ? 'Saving...' : 'Save Timing Settings'}
              </button>
            </div>
          </div>
        )}

        <div className="flex justify-end">
          <button
            onClick={saveProjectDetails}
            disabled={saving}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {saving ? 'Saving...' : 'Save Project Details'}
          </button>
        </div>
      </div>
    );
  }

  // Projects List View
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Projects</h2>
          <p className="text-gray-600">Manage your outreach campaigns by project</p>
        </div>
        <button
          onClick={() => setShowCreateForm(true)}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
        >
          <PlusIcon className="h-4 w-4 mr-2" />
          New Project
        </button>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('list')}
            className={`${
              activeTab === 'list'
                ? 'border-indigo-500 text-indigo-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm inline-flex items-center`}
          >
            <FolderIcon className="h-5 w-5 mr-2" />
            Project List
          </button>
          <button
            onClick={() => setActiveTab('global-settings')}
            className={`${
              activeTab === 'global-settings'
                ? 'border-indigo-500 text-indigo-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm inline-flex items-center`}
          >
            <Cog6ToothIcon className="h-5 w-5 mr-2" />
            Global Project Settings
          </button>
        </nav>
      </div>

      {/* Project List Tab */}
      {activeTab === 'list' && (
        <>
          {/* Create Project Form */}
          {showCreateForm && (
            <div className="bg-white shadow rounded-lg p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Create New Project</h3>
              
              <div className="space-y-4">
                <div>
                  <label htmlFor="projectName" className="block text-sm font-medium text-gray-700">
                    Project Name *
                  </label>
                  <input
                    type="text"
                    id="projectName"
                    value={newProject.name}
                    onChange={(e) => setNewProject(prev => ({ ...prev, name: e.target.value }))}
                    className="mt-1 shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                    placeholder="Enter project name"
                  />
                </div>

                <div>
                  <label htmlFor="areaDescription" className="block text-sm font-medium text-gray-700">
                    Area Description *
                  </label>
                  <input
                    type="text"
                    id="areaDescription"
                    value={newProject.areaDescription}
                    onChange={(e) => setNewProject(prev => ({ ...prev, areaDescription: e.target.value }))}
                    className="mt-1 shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                    placeholder="Exact address and specification (e.g., Downtown San Francisco, 94105, Tech Startups)"
                  />
                  <p className="mt-1 text-sm text-gray-500">
                    Provide an exact address and specification of the target area for this project
                  </p>
                </div>

                <div>
                  <label htmlFor="projectDetails" className="block text-sm font-medium text-gray-700">
                    Project Details
                  </label>
                  <textarea
                    id="projectDetails"
                    rows={6}
                    value={newProject.projectDetails}
                    onChange={(e) => setNewProject(prev => ({ ...prev, projectDetails: e.target.value }))}
                    className="mt-1 shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                    placeholder="Describe your project in detail..."
                    maxLength={5000}
                  />
                  <p className="mt-1 text-sm text-gray-500">
                    {newProject.projectDetails.length}/5000 characters
                  </p>
                </div>

                {/* Location Configuration */}
                <div className="border-t border-gray-200 pt-4">
                  <h4 className="text-md font-medium text-gray-900 mb-3">Location Configuration</h4>
                  <p className="text-sm text-gray-600 mb-4">
                    Configure the target location for lead finding. This helps narrow down leads to specific geographic areas.
                  </p>
                  
                  <div className="space-y-4">
                    <div className="flex items-center">
                      <input
                        id="useLlmParsing"
                        type="checkbox"
                        checked={newProject.location.useLlmParsing}
                        onChange={(e) => setNewProject(prev => ({ 
                          ...prev, 
                          location: { ...prev.location, useLlmParsing: e.target.checked }
                        }))}
                        className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                      />
                      <label htmlFor="useLlmParsing" className="ml-2 block text-sm font-medium text-gray-700">
                        Use AI to parse location (recommended)
                      </label>
                    </div>

                    {newProject.location.useLlmParsing ? (
                      <div>
                        <label htmlFor="rawLocation" className="block text-sm font-medium text-gray-700">
                          Target Location
                        </label>
                        <input
                          type="text"
                          id="rawLocation"
                          value={newProject.location.rawLocation}
                          onChange={(e) => setNewProject(prev => ({ 
                            ...prev, 
                            location: { ...prev.location, rawLocation: e.target.value }
                          }))}
                          className="mt-1 shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                          placeholder="e.g., San Francisco Bay Area, California"
                        />
                        <p className="mt-1 text-sm text-gray-500">
                          Enter a natural location description (city, state, region, etc.). AI will parse this for lead targeting.
                        </p>
                      </div>
                    ) : (
                      <div>
                        <label htmlFor="apolloLocationIds" className="block text-sm font-medium text-gray-700">
                          Apollo Location IDs
                        </label>
                        <input
                          type="text"
                          id="apolloLocationIds"
                          value={newProject.location.apolloLocationIds.join(', ')}
                          onChange={(e) => setNewProject(prev => ({ 
                            ...prev, 
                            location: { 
                              ...prev.location, 
                              apolloLocationIds: e.target.value.split(',').map(id => id.trim()).filter(id => id) as string[]
                            }
                          }))}
                          className="mt-1 shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                          placeholder="e.g., 5391959, 5332921"
                        />
                        <p className="mt-1 text-sm text-gray-500">
                          Enter Apollo.io location IDs separated by commas. Find these in Apollo's location search.
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              <div className="mt-6 flex justify-end space-x-3">
                <button
                  onClick={() => setShowCreateForm(false)}
                  className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={createProject}
                  disabled={creating}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                >
                  {creating ? 'Creating...' : 'Create Project'}
                </button>
              </div>
            </div>
          )}

          {/* Projects List */}
          <div className="bg-white shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              {projects.length === 0 ? (
                <div className="text-center py-12">
                  <FolderIcon className="mx-auto h-12 w-12 text-gray-400" />
                  <h3 className="mt-2 text-sm font-medium text-gray-900">No projects yet</h3>
                  <p className="mt-1 text-sm text-gray-500">
                    Get started by creating your first project.
                  </p>
                </div>
              ) : (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                  {projects.map((project) => (
                    <div
                      key={project.id}
                      className={`rounded-lg border-2 p-4 transition-all ${
                        selectedProject?.id === project.id
                          ? 'border-indigo-500 bg-indigo-50'
                          : 'border-gray-200'
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h3 className="text-lg font-medium text-gray-900 truncate">
                            {project.name}
                          </h3>
                          <div className="mt-2 flex items-center text-sm text-gray-500">
                            <MapPinIcon className="h-4 w-4 mr-1" />
                            <span className="truncate">{project.areaDescription}</span>
                          </div>
                          <div className="mt-2 flex items-center text-sm text-gray-500">
                            <CalendarIcon className="h-4 w-4 mr-1" />
                            <span>{formatDate(project.createdAt)}</span>
                          </div>
                          <div className="mt-2">
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                              {project.leadCount} leads
                            </span>
                          </div>
                        </div>
                      </div>
                      {project.projectDetails && (
                        <p className="mt-3 text-sm text-gray-600 line-clamp-2">
                          {project.projectDetails}
                        </p>
                      )}
                      
                      {/* Action Buttons */}
                      <div className="mt-4 flex space-x-2">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleProjectSelect(project);
                          }}
                          className="flex-1 inline-flex justify-center items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                        >
                          <Cog6ToothIcon className="h-4 w-4 mr-1" />
                          Edit Project
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onSelectProject(project);
                          }}
                          className="flex-1 inline-flex justify-center items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
                        >
                          View Leads
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </>
      )}

      {/* Global Project Settings Tab */}
      {activeTab === 'global-settings' && (
        <div className="space-y-6">
          <div>
            <h3 className="text-lg font-medium text-gray-900">Global Project Settings</h3>
            <p className="text-gray-600 mt-1">
              Configure default settings that apply to all projects unless overridden
            </p>
          </div>

          {/* Global Settings Sub-tabs */}
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              <button
                onClick={() => setActiveGlobalTab('guidelines')}
                className={`${
                  activeGlobalTab === 'guidelines'
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm inline-flex items-center`}
              >
                <DocumentTextIcon className="h-5 w-5 mr-2" />
                Email Guidelines
              </button>
              <button
                onClick={() => setActiveGlobalTab('timing')}
                className={`${
                  activeGlobalTab === 'timing'
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm inline-flex items-center`}
              >
                <Cog6ToothIcon className="h-5 w-5 mr-2" />
                Timing Settings
              </button>
            </nav>
          </div>

          {/* Global Email Guidelines */}
          {activeGlobalTab === 'guidelines' && (
            <div className="space-y-6">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex">
                  <InformationCircleIcon className="h-5 w-5 text-blue-400 mt-0.5 mr-3 flex-shrink-0" />
                  <div>
                    <h3 className="text-sm font-medium text-blue-800">Global Email Guidelines</h3>
                    <div className="mt-1 text-sm text-blue-700">
                      <p>These guidelines serve as AI prompts for generating outreach and follow-up emails. They apply to all projects unless overridden at the project level.</p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <div>
                  <label htmlFor="globalOutreachPrompt" className="block text-sm font-medium text-gray-700">
                    Outreach Email Guidelines
                  </label>
                  <div className="mt-1">
                    <textarea
                      id="globalOutreachPrompt"
                      rows={6}
                      maxLength={300}
                      value={globalPrompts.outreachPrompt}
                      onChange={(e) => setGlobalPrompts(prev => ({ ...prev, outreachPrompt: e.target.value }))}
                      className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                      placeholder="Guidelines for AI to generate initial outreach emails..."
                    />
                  </div>
                  <p className="mt-1 text-xs text-gray-500">
                    {globalPrompts.outreachPrompt.length}/300 characters
                  </p>
                </div>

                <div>
                  <label htmlFor="globalFollowupPrompt" className="block text-sm font-medium text-gray-700">
                    Follow-up Email Guidelines
                  </label>
                  <div className="mt-1">
                    <textarea
                      id="globalFollowupPrompt"
                      rows={6}
                      maxLength={300}
                      value={globalPrompts.followupPrompt}
                      onChange={(e) => setGlobalPrompts(prev => ({ ...prev, followupPrompt: e.target.value }))}
                      className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                      placeholder="Guidelines for AI to generate follow-up emails..."
                    />
                  </div>
                  <p className="mt-1 text-xs text-gray-500">
                    {globalPrompts.followupPrompt.length}/300 characters
                  </p>
                </div>
              </div>

              <div className="flex justify-end">
                <button
                  onClick={saveGlobalPrompts}
                  disabled={saving}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {saving ? 'Saving...' : 'Save Global Guidelines'}
                </button>
              </div>
            </div>
          )}

          {/* Global Timing Settings */}
          {activeGlobalTab === 'timing' && (
            <div className="space-y-6">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex">
                  <InformationCircleIcon className="h-5 w-5 text-blue-400 mt-0.5 mr-3 flex-shrink-0" />
                  <div>
                    <h3 className="text-sm font-medium text-blue-800">Global Timing Settings</h3>
                    <div className="mt-1 text-sm text-blue-700">
                      <p>Default timing settings for follow-up emails. These apply to all projects unless overridden at the project level.</p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <div>
                  <label htmlFor="globalFollowupDelayDays" className="block text-sm font-medium text-gray-700">
                    Follow-up Delay (Days)
                  </label>
                  <div className="mt-1">
                    <input
                      type="number"
                      id="globalFollowupDelayDays"
                      min="1"
                      max="30"
                      value={globalSettings.followupDelayDays}
                      onChange={(e) => setGlobalSettings(prev => ({ 
                        ...prev, 
                        followupDelayDays: parseInt(e.target.value) || 1 
                      }))}
                      className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                    />
                  </div>
                  <p className="mt-2 text-sm text-gray-500">
                    Default number of days to wait before sending a follow-up email
                  </p>
                </div>

                <div>
                  <label htmlFor="globalMaxFollowups" className="block text-sm font-medium text-gray-700">
                    Maximum Follow-ups
                  </label>
                  <div className="mt-1">
                    <input
                      type="number"
                      id="globalMaxFollowups"
                      min="1"
                      max="10"
                      value={globalSettings.maxFollowups}
                      onChange={(e) => setGlobalSettings(prev => ({ 
                        ...prev, 
                        maxFollowups: parseInt(e.target.value) || 1 
                      }))}
                      className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                    />
                  </div>
                  <p className="mt-2 text-sm text-gray-500">
                    Default maximum number of follow-up emails to send per lead
                  </p>
                </div>
              </div>

              <div className="flex justify-end">
                <button
                  onClick={saveGlobalSettings}
                  disabled={saving}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {saving ? 'Saving...' : 'Save Global Settings'}
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Projects; 