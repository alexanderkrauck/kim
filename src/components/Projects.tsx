import React, { useState, useEffect, useCallback } from 'react';
import { collection, getDocs, addDoc, doc, updateDoc, query, orderBy, getDoc, setDoc } from 'firebase/firestore';
import { db } from '../firebase/config';
import { Project, ProjectPrompts } from '../types';
import { 
  PlusIcon, 
  FolderIcon, 
  CalendarIcon, 
  MapPinIcon, 
  ArrowLeftIcon,
  Cog6ToothIcon,
  DocumentTextIcon,
  ChatBubbleLeftRightIcon
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
  const [activeSettingsTab, setActiveSettingsTab] = useState<'details' | 'prompts' | 'guidelines'>('details');
  
  const [newProject, setNewProject] = useState({
    name: '',
    areaDescription: '',
    projectDetails: '',
    emailConsiderations: '',
    followupConsiderations: '',
  });

  const [editingProject, setEditingProject] = useState<Project | null>(null);
  const [projectPrompts, setProjectPrompts] = useState<ProjectPrompts>({
    outreachPrompt: '',
    followupPrompt: '',
    projectId: '',
    useGlobalPrompts: true,
  });

  useEffect(() => {
    loadProjects();
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

    if (newProject.emailConsiderations.length > 300) {
      toast.error('Email considerations must be under 300 characters');
      return;
    }

    if (newProject.followupConsiderations.length > 300) {
      toast.error('Follow-up considerations must be under 300 characters');
      return;
    }

    setCreating(true);
    try {
      const projectData = {
        ...newProject,
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
        emailConsiderations: '',
        followupConsiderations: '',
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
        emailConsiderations: editingProject.emailConsiderations,
        followupConsiderations: editingProject.followupConsiderations,
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
              <ChatBubbleLeftRightIcon className="h-5 w-5 mr-2" />
              Email Guidelines
            </button>
            <button
              onClick={() => setActiveSettingsTab('prompts')}
              className={`${
                activeSettingsTab === 'prompts'
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm inline-flex items-center`}
            >
              <DocumentTextIcon className="h-5 w-5 mr-2" />
              AI Prompts
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
                Email Guidelines & Considerations
              </h3>
              <p className="text-sm text-gray-600 mb-6">
                These guidelines provide additional context for AI when generating emails for this project.
              </p>
              
              <div className="space-y-6">
                <div>
                  <label htmlFor="editEmailConsiderations" className="block text-sm font-medium text-gray-700 mb-2">
                    Email Considerations
                  </label>
                  <div className="bg-gray-50 border border-gray-200 rounded-md p-3 mb-2">
                    <p className="text-xs text-gray-600">
                      <strong>Special instructions for emails:</strong> Industry-specific language, 
                      compliance requirements, cultural considerations, or unique value propositions.
                    </p>
                  </div>
                  <textarea
                    id="editEmailConsiderations"
                    rows={4}
                    value={editingProject.emailConsiderations}
                    onChange={(e) => setEditingProject(prev => prev ? { ...prev, emailConsiderations: e.target.value } : null)}
                    className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                    placeholder="Example: This is a healthcare project - use HIPAA-compliant language. Emphasize our medical device expertise. Avoid overly technical jargon."
                    maxLength={300}
                  />
                  <p className="mt-1 text-sm text-gray-500">
                    {editingProject.emailConsiderations.length}/300 characters
                  </p>
                </div>

                <div>
                  <label htmlFor="editFollowupConsiderations" className="block text-sm font-medium text-gray-700 mb-2">
                    Follow-up Strategy
                  </label>
                  <div className="bg-gray-50 border border-gray-200 rounded-md p-3 mb-2">
                    <p className="text-xs text-gray-600">
                      <strong>Follow-up timing and approach:</strong> How often to follow up, 
                      what additional value to provide, and when to stop following up.
                    </p>
                  </div>
                  <textarea
                    id="editFollowupConsiderations"
                    rows={4}
                    value={editingProject.followupConsiderations}
                    onChange={(e) => setEditingProject(prev => prev ? { ...prev, followupConsiderations: e.target.value } : null)}
                    className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                    placeholder="Example: Follow up every 7 days, max 3 attempts. In 2nd follow-up, share case study. In 3rd follow-up, offer free consultation."
                    maxLength={300}
                  />
                  <p className="mt-1 text-sm text-gray-500">
                    {editingProject.followupConsiderations.length}/300 characters
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* AI Prompts Tab */}
        {activeSettingsTab === 'prompts' && (
          <div className="bg-white shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                Project-Specific AI Prompts
              </h3>
              <p className="text-sm text-gray-600 mb-6">
                Override global AI prompts for this specific project. Leave unchecked to use global defaults.
              </p>

              <div className="mb-6">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={projectPrompts.useGlobalPrompts}
                    onChange={(e) => setProjectPrompts(prev => ({ ...prev, useGlobalPrompts: e.target.checked }))}
                    className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                  />
                  <span className="ml-2 text-sm text-gray-700">
                    Use global AI prompts (recommended for consistency)
                  </span>
                </label>
              </div>

              <div className="space-y-6">
                <div>
                  <label htmlFor="projectOutreachPrompt" className="block text-sm font-medium text-gray-700 mb-2">
                    Project-Specific Outreach Instructions
                  </label>
                  <textarea
                    id="projectOutreachPrompt"
                    rows={6}
                    value={projectPrompts.outreachPrompt}
                    onChange={(e) => setProjectPrompts(prev => ({ ...prev, outreachPrompt: e.target.value }))}
                    disabled={projectPrompts.useGlobalPrompts}
                    className={`shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md ${
                      projectPrompts.useGlobalPrompts ? 'bg-gray-100 text-gray-500 cursor-not-allowed' : ''
                    }`}
                    placeholder="Custom AI instructions for outreach emails in this project..."
                  />
                </div>

                <div>
                  <label htmlFor="projectFollowupPrompt" className="block text-sm font-medium text-gray-700 mb-2">
                    Project-Specific Follow-up Instructions
                  </label>
                  <textarea
                    id="projectFollowupPrompt"
                    rows={6}
                    value={projectPrompts.followupPrompt}
                    onChange={(e) => setProjectPrompts(prev => ({ ...prev, followupPrompt: e.target.value }))}
                    disabled={projectPrompts.useGlobalPrompts}
                    className={`shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md ${
                      projectPrompts.useGlobalPrompts ? 'bg-gray-100 text-gray-500 cursor-not-allowed' : ''
                    }`}
                    placeholder="Custom AI instructions for follow-up emails in this project..."
                  />
                </div>
              </div>

              <div className="mt-6">
                <button
                  onClick={saveProjectPrompts}
                  disabled={saving}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50"
                >
                  {saving ? 'Saving...' : 'Save AI Prompts'}
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

            <div>
              <label htmlFor="emailConsiderations" className="block text-sm font-medium text-gray-700">
                Email Considerations
              </label>
              <textarea
                id="emailConsiderations"
                rows={3}
                value={newProject.emailConsiderations}
                onChange={(e) => setNewProject(prev => ({ ...prev, emailConsiderations: e.target.value }))}
                className="mt-1 shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                placeholder="Special considerations for emails in this project..."
                maxLength={300}
              />
              <p className="mt-1 text-sm text-gray-500">
                {newProject.emailConsiderations.length}/300 characters
              </p>
            </div>

            <div>
              <label htmlFor="followupConsiderations" className="block text-sm font-medium text-gray-700">
                Follow-up Considerations
              </label>
              <textarea
                id="followupConsiderations"
                rows={3}
                value={newProject.followupConsiderations}
                onChange={(e) => setNewProject(prev => ({ ...prev, followupConsiderations: e.target.value }))}
                className="mt-1 shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                placeholder="Schedule and considerations for follow-ups..."
                maxLength={300}
              />
              <p className="mt-1 text-sm text-gray-500">
                {newProject.followupConsiderations.length}/300 characters
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
    </div>
  );
};

export default Projects; 