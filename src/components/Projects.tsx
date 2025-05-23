import React, { useState, useEffect, useCallback } from 'react';
import { collection, getDocs, addDoc, doc, updateDoc, query, orderBy, getDoc, setDoc } from 'firebase/firestore';
import { db } from '../firebase/config';
import { Project, ProjectPrompts, GlobalPrompts } from '../types';
import { 
  PlusIcon, 
  FolderIcon, 
  CalendarIcon, 
  MapPinIcon, 
  ArrowLeftIcon,
  Cog6ToothIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

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
  const [activeSettingsTab, setActiveSettingsTab] = useState<'details' | 'guidelines'>('details');
  
  const [newProject, setNewProject] = useState({
    name: '',
    areaDescription: '',
    projectDetails: '',
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

  useEffect(() => {
    loadProjects();
    loadGlobalPrompts();
  }, []);

  const loadProjects = async () => {
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
  };

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
    }
  };

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

  useEffect(() => {
    if (editingProject && showProjectSettings) {
      loadProjectPrompts();
    }
  }, [editingProject, showProjectSettings, loadProjectPrompts]);

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
        ...newProject,
        emailConsiderations: '',
        followupConsiderations: '',
        createdAt: new Date(),
        updatedAt: new Date(),
        isActive: true,
        leadCount: 0,
      };

      const docRef = await addDoc(collection(db, 'projects'), projectData);
      const createdProject: Project = {
        id: docRef.id,
        ...projectData,
      };

      setProjects(prev => [createdProject, ...prev]);
      setNewProject({
        name: '',
        areaDescription: '',
        projectDetails: '',
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

  const saveProjectSettings = async () => {
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

      toast.success('Project settings saved successfully!');
    } catch (error) {
      console.error('Error saving project settings:', error);
      toast.error('Failed to save project settings');
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
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <div className="flex justify-between items-start mb-6">
              <div>
                <h3 className="text-lg leading-6 font-medium text-gray-900">
                  Global Email Guidelines
                </h3>
                <p className="text-sm text-gray-600 mt-1">
                  Default AI instructions used across all projects unless overridden
                </p>
              </div>
              <button
                onClick={saveGlobalPrompts}
                disabled={saving}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50"
              >
                {saving ? 'Saving...' : 'Save Global Guidelines'}
              </button>
            </div>

            <div className="space-y-6">
              <div>
                <label htmlFor="globalOutreachPrompt" className="block text-sm font-medium text-gray-700 mb-2">
                  Default Outreach Email Guidelines
                </label>
                <div className="bg-blue-50 border border-blue-200 rounded-md p-3 mb-3">
                  <p className="text-xs text-blue-700">
                    <strong>AI Instructions for outreach emails:</strong> Tell the AI how to write initial outreach emails. 
                    Include tone, style, key points to mention, and call-to-action guidelines.
                  </p>
                </div>
                <textarea
                  id="globalOutreachPrompt"
                  rows={8}
                  value={globalPrompts.outreachPrompt}
                  onChange={(e) => setGlobalPrompts(prev => ({ ...prev, outreachPrompt: e.target.value }))}
                  className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                  placeholder="Example: Write professional, personalized outreach emails. Keep them concise (under 150 words). Include a clear value proposition and specific call-to-action. Use a friendly but professional tone. Always personalize with the recipient's name and company."
                  maxLength={300}
                />
                <p className="mt-1 text-sm text-gray-500">
                  {globalPrompts.outreachPrompt.length}/300 characters
                </p>
              </div>

              <div>
                <label htmlFor="globalFollowupPrompt" className="block text-sm font-medium text-gray-700 mb-2">
                  Default Follow-up Email Guidelines
                </label>
                <div className="bg-blue-50 border border-blue-200 rounded-md p-3 mb-3">
                  <p className="text-xs text-blue-700">
                    <strong>AI Instructions for follow-up emails:</strong> Tell the AI how to write follow-up emails. 
                    Include timing approach, how to reference previous emails, and value-add strategies.
                  </p>
                </div>
                <textarea
                  id="globalFollowupPrompt"
                  rows={8}
                  value={globalPrompts.followupPrompt}
                  onChange={(e) => setGlobalPrompts(prev => ({ ...prev, followupPrompt: e.target.value }))}
                  className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                  placeholder="Example: Write follow-up emails that add value. Reference the previous email briefly. Provide additional insights or resources. Keep tone persistent but not pushy. Include social proof or case studies when relevant."
                  maxLength={300}
                />
                <p className="mt-1 text-sm text-gray-500">
                  {globalPrompts.followupPrompt.length}/300 characters
                </p>
              </div>
            </div>

            <div className="mt-6 bg-gray-50 border border-gray-200 rounded-lg p-4">
              <h4 className="text-sm font-medium text-gray-900 mb-2">How Global Guidelines Work</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• These guidelines are used by default for all projects</li>
                <li>• Individual projects can override these with custom guidelines in their settings</li>
                <li>• Changes here affect all projects using global guidelines</li>
                <li>• Keep guidelines clear and specific for best AI performance</li>
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Projects; 