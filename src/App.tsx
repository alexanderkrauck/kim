import React, { useState } from 'react';
import { Toaster } from 'react-hot-toast';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Login from './components/Login';
import Layout from './components/Layout';
import Blacklist from './components/Blacklist';
import Configuration from './components/Configuration';
import Projects from './components/Projects';
import EnhancedLeads from './components/EnhancedLeads';
import { Project } from './types';
import { useSystemInitialization } from './hooks/useSystemInitialization';

const Dashboard: React.FC = () => {
  const { currentUser } = useAuth();
  const [activeTab, setActiveTab] = useState('projects');
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  
  // Automatic database initialization
  const {
    isInitialized,
    isInitializing,
    initializationError,
    healthCheckComplete,
    retryInitialization
  } = useSystemInitialization(!!currentUser);

  const handleSelectProject = (project: Project | null) => {
    setSelectedProject(project);
    if (project) {
      setActiveTab('leads'); // Automatically switch to leads when a project is selected
    }
  };

  // Show initialization status
  if (isInitializing) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Setting up your workspace</h2>
          <p className="text-gray-600">
            {healthCheckComplete ? 
              'Initializing database with default configuration...' : 
              'Checking system health...'
            }
          </p>
          <div className="mt-4 text-sm text-gray-500">
            This only happens once when you first log in
          </div>
        </div>
      </div>
    );
  }

  // Show initialization error
  if (initializationError) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8 text-center">
          <div className="text-red-500 text-6xl mb-4">⚠️</div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Setup Failed</h2>
          <p className="text-gray-600 mb-4">{initializationError}</p>
          <div className="space-y-3">
            <button
              onClick={retryInitialization}
              className="w-full bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 transition-colors"
            >
              Try Again
            </button>
            <button
              onClick={() => setActiveTab('configuration')}
              className="w-full bg-gray-200 text-gray-800 px-4 py-2 rounded-md hover:bg-gray-300 transition-colors"
            >
              Configure Manually
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Wait for initialization to complete
  if (!isInitialized) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8 text-center">
          <div className="animate-pulse h-12 w-12 bg-indigo-200 rounded-full mx-auto mb-4"></div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Almost ready...</h2>
          <p className="text-gray-600">Finalizing workspace setup</p>
        </div>
      </div>
    );
  }

  const renderContent = () => {
    switch (activeTab) {
      case 'projects':
        return (
          <Projects 
            onSelectProject={handleSelectProject}
            selectedProject={selectedProject}
          />
        );
      case 'leads':
        return <EnhancedLeads selectedProject={selectedProject} />;
      case 'configuration':
        return <Configuration />;
      case 'blacklist':
        return <Blacklist />;
      default:
        return (
          <Projects 
            onSelectProject={handleSelectProject}
            selectedProject={selectedProject}
          />
        );
    }
  };

  return (
    <Layout activeTab={activeTab} onTabChange={setActiveTab}>
      {renderContent()}
    </Layout>
  );
};

const AppContent: React.FC = () => {
  const { currentUser } = useAuth();

  if (!currentUser) {
    return <Login />;
  }

  return <Dashboard />;
};

const App: React.FC = () => {
  return (
    <AuthProvider>
      <div className="App">
        <AppContent />
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#363636',
              color: '#fff',
            },
            success: {
              duration: 3000,
              iconTheme: {
                primary: '#4ade80',
                secondary: '#fff',
              },
            },
            error: {
              duration: 5000,
              iconTheme: {
                primary: '#ef4444',
                secondary: '#fff',
              },
            },
          }}
        />
      </div>
    </AuthProvider>
  );
};

export default App; 