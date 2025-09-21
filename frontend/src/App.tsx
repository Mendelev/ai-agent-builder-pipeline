import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom';

import Layout from '@/components/Layout/Layout';
import { ErrorBoundary } from '@/components/Common/ErrorBoundary';
import { Dashboard } from '@/pages/Dashboard';
import { Requirements } from '@/pages/Requirements';
import { Planning } from '@/pages/Planning';
import Prompts from '@/pages/Prompts';
import Audit from '@/pages/Audit';
import CodeChecklist from '@/pages/CodeChecklist';
import { DEFAULT_PROJECT_ID } from '@/config';

const ProjectLayout: React.FC = () => (
  <Layout>
    <Outlet />
  </Layout>
);

const MissingProjectMessage: React.FC = () => (
  <div className="flex flex-col items-center justify-center min-h-[60vh] text-center space-y-4">
    <h1 className="text-2xl font-bold text-gray-900">Project not configured</h1>
    <p className="max-w-lg text-gray-600">
      Set <code className="px-2 py-1 bg-gray-100 rounded">VITE_DEFAULT_PROJECT_ID</code> in your environment or
      navigate directly to <code className="px-2 py-1 bg-gray-100 rounded">/projects/[projectId]</code> to load data
      from the backend.
    </p>
  </div>
);

const NotFound: React.FC = () => (
  <div className="flex flex-col items-center justify-center min-h-[60vh] text-center space-y-4">
    <h1 className="text-2xl font-bold text-gray-900">Page not found</h1>
    <p className="text-gray-600">The page you are looking for does not exist.</p>
  </div>
);

function App() {
  const hasDefaultProject = Boolean(DEFAULT_PROJECT_ID);

  return (
    <BrowserRouter>
      <ErrorBoundary>
        <Routes>
          <Route
            path="/"
            element={
              hasDefaultProject ? (
                <Navigate to={`/projects/${DEFAULT_PROJECT_ID}`} replace />
              ) : (
                <MissingProjectMessage />
              )
            }
          />

          <Route element={<ProjectLayout />}>
            <Route path="/projects/:projectId">
              <Route index element={<Dashboard />} />
              <Route path="requirements" element={<Requirements />} />
              <Route path="planning" element={<Planning />} />
              <Route path="prompts" element={<Prompts />} />
              <Route path="code-checklist" element={<CodeChecklist />} />
              <Route path="audit" element={<Audit />} />
            </Route>
          </Route>

          <Route path="*" element={<NotFound />} />
        </Routes>
      </ErrorBoundary>
    </BrowserRouter>
  );
}

export default App;
