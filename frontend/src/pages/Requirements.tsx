import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { requirementsService } from '@/services/requirements';
import { RequirementEditor } from '@/components/Requirements/RequirementEditor';
import { QuestionAnswerLoop } from '@/components/Requirements/QuestionAnswerLoop';
import { Table } from '@/components/Common/Table';
import { LoadingSpinner } from '@/components/Common/LoadingSpinner';
import { Plus, RefreshCw, Download, CheckCircle } from 'lucide-react';
import { Requirement } from '@/types';
import toast from 'react-hot-toast';

export const Requirements: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const queryClient = useQueryClient();
  const [showEditor, setShowEditor] = useState(false);
  const [editingRequirement, setEditingRequirement] = useState<Requirement | undefined>();
  const [activeTab, setActiveTab] = useState<'list' | 'qa'>('list');

  const { data: requirements = [], isLoading } = useQuery({
    queryKey: ['requirements', projectId],
    enabled: !!projectId,
    queryFn: () => requirementsService.listRequirements(projectId!),
  });

  const createMutation = useMutation({
    mutationFn: (reqs: Requirement[]) =>
      requirementsService.createRequirements(projectId!, reqs),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['requirements', projectId] });
      toast.success('Requirements saved');
      setShowEditor(false);
      setEditingRequirement(undefined);
    },
  });

  const refineMutation = useMutation({
    mutationFn: (context?: string) =>
      requirementsService.refineRequirements(projectId!, context),
    onSuccess: () => {
      toast.success('Refinement started');
    },
  });

  const finalizeMutation = useMutation({
    mutationFn: (force: boolean) =>
      requirementsService.finalizeRequirements(projectId!, force),
    onSuccess: () => {
      toast.success('Requirements finalized');
      queryClient.invalidateQueries({ queryKey: ['project', projectId] });
    },
  });

  const exportMutation = useMutation({
    mutationFn: (format: 'json' | 'md') =>
      requirementsService.exportRequirements(projectId!, format),
    onSuccess: (data, format) => {
      const blob = new Blob(
        [format === 'json' ? JSON.stringify(data, null, 2) : data],
        { type: format === 'json' ? 'application/json' : 'text/markdown' }
      );
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `requirements.${format}`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success('Export downloaded');
    },
  });

  const columns = [
    {
      key: 'key',
      label: 'Key',
      className: 'font-mono',
    },
    {
      key: 'title',
      label: 'Title',
    },
    {
      key: 'priority',
      label: 'Priority',
      render: (req: Requirement) => (
        <span
          className={`px-2 py-1 rounded text-xs font-medium ${
            req.priority === 'critical'
              ? 'bg-red-100 text-red-800'
              : req.priority === 'high'
              ? 'bg-orange-100 text-orange-800'
              : req.priority === 'medium'
              ? 'bg-yellow-100 text-yellow-800'
              : 'bg-gray-100 text-gray-800'
          }`}
        >
          {req.priority}
        </span>
      ),
    },
    {
      key: 'is_coherent',
      label: 'Status',
      render: (req: Requirement) =>
        req.is_coherent ? (
          <CheckCircle className="h-5 w-5 text-green-500" />
        ) : (
          <span className="text-xs text-gray-500">Needs refinement</span>
        ),
    },
    {
      key: 'dependencies',
      label: 'Dependencies',
      render: (req: Requirement) => (
        <span className="text-sm">{req.dependencies.length}</span>
      ),
    },
  ];

  if (!projectId) {
    return (
      <div className="text-center py-12 text-gray-500">
        Select a project to manage requirements.
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Requirements</h1>
        <div className="flex gap-2">
          <button
            onClick={() => refineMutation.mutate()}
            disabled={refineMutation.isPending}
            className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 flex items-center gap-2"
          >
            <RefreshCw className="h-4 w-4" />
            Refine
          </button>
          <button
            onClick={() => exportMutation.mutate('json')}
            className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 flex items-center gap-2"
          >
            <Download className="h-4 w-4" />
            Export
          </button>
          <button
            onClick={() => finalizeMutation.mutate(false)}
            disabled={finalizeMutation.isPending}
            className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 flex items-center gap-2"
          >
            <CheckCircle className="h-4 w-4" />
            Finalize
          </button>
          <button
            onClick={() => setShowEditor(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 flex items-center gap-2"
          >
            <Plus className="h-4 w-4" />
            Add Requirement
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('list')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'list'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Requirements List ({requirements.length})
          </button>
          <button
            onClick={() => setActiveTab('qa')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'qa'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Q&A Loop
          </button>
        </nav>
      </div>

      {/* Content */}
      {activeTab === 'list' ? (
        showEditor ? (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">
              {editingRequirement ? 'Edit Requirement' : 'New Requirement'}
            </h2>
            <RequirementEditor
              requirement={editingRequirement}
              onSave={(req) => createMutation.mutate([req])}
              onCancel={() => {
                setShowEditor(false);
                setEditingRequirement(undefined);
              }}
            />
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow">
            <Table
              columns={columns}
              data={requirements}
              keyExtractor={(req) => req.key}
              onRowClick={(req) => {
                setEditingRequirement(req);
                setShowEditor(true);
              }}
            />
          </div>
        )
      ) : (
        <div className="bg-white rounded-lg shadow p-6">
          <QuestionAnswerLoop
            questions={[]} // TODO: Fetch questions
            onAnswer={(questionId, answer) => {
              console.log('Answer:', questionId, answer);
              // TODO: Submit answer
            }}
          />
        </div>
      )}
    </div>
  );
};
