import React, { useState } from 'react';
import { Toaster } from 'react-hot-toast';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Login from './components/Login';
import Layout from './components/Layout';
import Settings from './components/Settings';
import Blacklist from './components/Blacklist';
import ApiKeysComponent from './components/ApiKeys';
import Projects from './components/Projects';
import EnhancedLeads from './components/EnhancedLeads';
import { Project } from './types';

const Dashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState('projects');
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);

  const handleSelectProject = (project: Project | null) => {
    setSelectedProject(project);
    if (project) {
      setActiveTab('leads'); // Automatically switch to leads when a project is selected
    }
  };

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
      case 'settings':
        return <Settings />;
      case 'apikeys':
        return <ApiKeysComponent />;
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