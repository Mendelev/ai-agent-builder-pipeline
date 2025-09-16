import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { useUIStore } from '@/store/uiStore';

// Layout simples
function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const { sidebarOpen, toggleSidebar } = useUIStore();
  
  const navigation = [
    { name: 'Dashboard', href: '/', icon: '📊' },
    { name: 'Requirements', href: '/requirements', icon: '📋' },
    { name: 'Planning', href: '/planning', icon: '🗓️' },
    { name: 'Prompts', href: '/prompts', icon: '💬' },
    { name: 'Code Checklist', href: '/code-checklist', icon: '✅' },
    { name: 'Audit', href: '/audit', icon: '🔍' },
  ];

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="px-6 py-4 flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900">AI Agent Builder Pipeline</h1>
          <button
            onClick={toggleSidebar}
            className="md:hidden p-2 rounded-md text-gray-600 hover:bg-gray-100"
          >
            ☰
          </button>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar */}
        <nav className={`${sidebarOpen ? 'w-64' : 'w-16'} transition-all duration-200 bg-white shadow-sm min-h-screen`}>
          <div className="p-4">
            <ul className="space-y-2">
              {navigation.map((item) => {
                const isActive = location.pathname === item.href;
                return (
                  <li key={item.name}>
                    <Link
                      to={item.href}
                      className={`flex items-center px-3 py-2 rounded-md text-sm font-medium ${
                        isActive
                          ? 'bg-blue-100 text-blue-700'
                          : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                      }`}
                      title={item.name}
                    >
                      <span className={`${sidebarOpen ? 'mr-3' : 'mx-auto'}`}>{item.icon}</span>
                      {sidebarOpen && item.name}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        </nav>

        {/* Main content */}
        <main className="flex-1">
          {children}
        </main>
      </div>
    </div>
  );
}

// Componentes de página simples
function Dashboard() {
  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-4">Dashboard</h2>
      <div className="bg-white rounded-lg shadow p-6">
        <p className="text-gray-600">Welcome to the AI Agent Builder Pipeline Dashboard.</p>
        <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-blue-50 p-4 rounded-lg">
            <h3 className="font-semibold text-blue-800">Active Projects</h3>
            <p className="text-2xl font-bold text-blue-600">0</p>
          </div>
          <div className="bg-green-50 p-4 rounded-lg">
            <h3 className="font-semibold text-green-800">Completed</h3>
            <p className="text-2xl font-bold text-green-600">0</p>
          </div>
          <div className="bg-yellow-50 p-4 rounded-lg">
            <h3 className="font-semibold text-yellow-800">In Progress</h3>
            <p className="text-2xl font-bold text-yellow-600">0</p>
          </div>
        </div>
      </div>
    </div>
  );
}

function Requirements() {
  const [requirements, setRequirements] = React.useState([
    { id: '1', title: 'User Authentication', description: 'Implement user login and registration', status: 'draft' },
    { id: '2', title: 'Dashboard Analytics', description: 'Create analytics dashboard with charts', status: 'in-progress' },
  ]);

  const addRequirement = () => {
    const newReq = {
      id: Date.now().toString(),
      title: 'New Requirement',
      description: 'Description here...',
      status: 'draft'
    };
    setRequirements([...requirements, newReq]);
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-800">Requirements</h2>
        <button 
          onClick={addRequirement}
          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
        >
          Add New Requirement
        </button>
      </div>
      
      <div className="grid gap-4">
        {requirements.map((req) => (
          <div key={req.id} className="bg-white rounded-lg shadow p-6">
            <div className="flex justify-between items-start mb-2">
              <h3 className="text-lg font-semibold text-gray-800">{req.title}</h3>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                req.status === 'draft' ? 'bg-gray-100 text-gray-800' :
                req.status === 'in-progress' ? 'bg-blue-100 text-blue-800' :
                'bg-green-100 text-green-800'
              }`}>
                {req.status}
              </span>
            </div>
            <p className="text-gray-600">{req.description}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function Planning() {
  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-4">Planning</h2>
      <div className="bg-white rounded-lg shadow p-6">
        <p className="text-gray-600">Plan your project development here.</p>
      </div>
    </div>
  );
}

function CodeChecklist() {
  const [checklistItems, setChecklistItems] = React.useState([
    { id: 1, title: 'Code Review Completed', completed: false, priority: 'high' },
    { id: 2, title: 'Unit Tests Written', completed: true, priority: 'critical' },
    { id: 3, title: 'Integration Tests Passing', completed: false, priority: 'high' },
    { id: 4, title: 'Security Scan Completed', completed: false, priority: 'medium' },
    { id: 5, title: 'Performance Tests Executed', completed: false, priority: 'medium' },
    { id: 6, title: 'Documentation Updated', completed: true, priority: 'low' },
  ]);

  const toggleItem = (id: number) => {
    setChecklistItems(items =>
      items.map(item =>
        item.id === id ? { ...item, completed: !item.completed } : item
      )
    );
  };

  const completedCount = checklistItems.filter(item => item.completed).length;
  const progressPercentage = (completedCount / checklistItems.length) * 100;

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-800">Code Checklist</h2>
        <div className="text-sm text-gray-600">
          {completedCount}/{checklistItems.length} completed ({Math.round(progressPercentage)}%)
        </div>
      </div>

      {/* Progress Bar */}
      <div className="bg-gray-200 rounded-full h-3 mb-6">
        <div 
          className="bg-blue-600 h-3 rounded-full transition-all duration-300"
          style={{ width: `${progressPercentage}%` }}
        ></div>
      </div>

      {/* Checklist Items */}
      <div className="space-y-3">
        {checklistItems.map((item) => (
          <div 
            key={item.id} 
            className={`flex items-center p-4 bg-white rounded-lg shadow ${
              item.completed ? 'bg-green-50 border-l-4 border-green-500' : 'border-l-4 border-gray-300'
            }`}
          >
            <input
              type="checkbox"
              checked={item.completed}
              onChange={() => toggleItem(item.id)}
              className="h-5 w-5 text-blue-600 rounded focus:ring-blue-500"
            />
            <span 
              className={`ml-3 flex-1 ${
                item.completed ? 'line-through text-gray-500' : 'text-gray-800'
              }`}
            >
              {item.title}
            </span>
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
              item.priority === 'critical' ? 'bg-red-100 text-red-800' :
              item.priority === 'high' ? 'bg-orange-100 text-orange-800' :
              item.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' :
              'bg-gray-100 text-gray-800'
            }`}>
              {item.priority}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function Prompts() {
  const [promptBundles] = React.useState([
    {
      id: 1,
      title: 'Phase 1: Authentication Setup',
      version: 1,
      generatedAt: '2024-01-15',
      totalPrompts: 3,
      status: 'ready'
    },
    {
      id: 2,
      title: 'Phase 2: Dashboard Implementation',
      version: 1,
      generatedAt: '2024-01-10',
      totalPrompts: 5,
      status: 'in-progress'
    },
  ]);

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-800">AI Prompts</h2>
        <button className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">
          Generate New Bundle
        </button>
      </div>

      <div className="grid gap-4">
        {promptBundles.map((bundle) => (
          <div key={bundle.id} className="bg-white rounded-lg shadow p-6">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="text-lg font-semibold text-gray-800">{bundle.title}</h3>
                <p className="text-sm text-gray-600">
                  Version {bundle.version} • Generated on {bundle.generatedAt}
                </p>
              </div>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                bundle.status === 'ready' ? 'bg-green-100 text-green-800' :
                bundle.status === 'in-progress' ? 'bg-blue-100 text-blue-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {bundle.status}
              </span>
            </div>
            
            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-600">
                <span className="font-medium">{bundle.totalPrompts}</span> prompts in bundle
              </div>
              <div className="space-x-2">
                <button className="text-blue-600 hover:text-blue-800 text-sm font-medium">
                  View Details
                </button>
                <button className="text-blue-600 hover:text-blue-800 text-sm font-medium">
                  Download
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function Audit() {
  const [auditHistory] = React.useState([
    {
      id: 1,
      date: '2024-01-15',
      type: 'Security Audit',
      status: 'completed',
      findings: 3,
      severity: 'medium'
    },
    {
      id: 2,
      date: '2024-01-10',
      type: 'Code Quality Audit',
      status: 'completed',
      findings: 7,
      severity: 'low'
    },
    {
      id: 3,
      date: '2024-01-08',
      type: 'Performance Audit',
      status: 'in-progress',
      findings: 0,
      severity: 'none'
    },
  ]);

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-800">Audit History</h2>
        <button className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">
          Run New Audit
        </button>
      </div>

      <div className="grid gap-4">
        {auditHistory.map((audit) => (
          <div key={audit.id} className="bg-white rounded-lg shadow p-6">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="text-lg font-semibold text-gray-800">{audit.type}</h3>
                <p className="text-sm text-gray-600">{audit.date}</p>
              </div>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                audit.status === 'completed' ? 'bg-green-100 text-green-800' :
                audit.status === 'in-progress' ? 'bg-blue-100 text-blue-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {audit.status}
              </span>
            </div>
            
            <div className="flex items-center space-x-4 text-sm">
              <div className="flex items-center">
                <span className="font-medium text-gray-600">Findings:</span>
                <span className="ml-1 text-gray-800">{audit.findings}</span>
              </div>
              {audit.severity !== 'none' && (
                <div className="flex items-center">
                  <span className="font-medium text-gray-600">Severity:</span>
                  <span className={`ml-1 ${
                    audit.severity === 'high' ? 'text-red-600' :
                    audit.severity === 'medium' ? 'text-yellow-600' :
                    'text-green-600'
                  }`}>
                    {audit.severity}
                  </span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/requirements" element={<Requirements />} />
          <Route path="/planning" element={<Planning />} />
          <Route path="/prompts" element={<Prompts />} />
          <Route path="/code-checklist" element={<CodeChecklist />} />
          <Route path="/audit" element={<Audit />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;