import React, { useState, useEffect } from 'react';
import { collection, getDocs, addDoc, doc, updateDoc, query, orderBy } from 'firebase/firestore';
import { db } from '../firebase/config';
import { Project } from '../types';
import { PlusIcon, FolderIcon, CalendarIcon, MapPinIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

interface ProjectsProps {
  onSelectProject: (project: Project) => void;
  selectedProject: Project | null;
}

const Projects: React.FC<ProjectsProps> = ({ onSelectProject, selectedProject }) => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [creating, setCreating] = useState(false);
  const [newProject, setNewProject] = useState({
    name: '',
    areaDescription: '',
    projectDetails: '',
    emailConsiderations: '',
    followupConsiderations: '',
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
                  onClick={() => onSelectProject(project)}
                  className={`cursor-pointer rounded-lg border-2 p-4 hover:shadow-md transition-all ${
                    selectedProject?.id === project.id
                      ? 'border-indigo-500 bg-indigo-50'
                      : 'border-gray-200 hover:border-gray-300'
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