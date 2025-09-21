import React from 'react';
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { CheckCircle2, AlertCircle, ListChecks } from 'lucide-react';

import { requirementsService } from '@/services/requirements';
import { LoadingSpinner } from '@/components/Common/LoadingSpinner';

const CodeChecklist: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();

  const { data: requirements = [], isLoading } = useQuery({
    queryKey: ['requirements', projectId, 'checklist'],
    enabled: !!projectId,
    queryFn: () => requirementsService.listRequirements(projectId!),
  });

  if (!projectId) {
    return (
      <div className="text-center py-12 text-gray-500">
        Select a project to review code preparation tasks.
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

  const coherent = requirements.filter((req) => req.is_coherent).length;
  const highPriority = requirements.filter((req) => req.priority === 'high' || req.priority === 'critical');
  const highWithCriteria = highPriority.filter((req) => req.acceptance_criteria.length >= 2).length;

  const checklist = [
    {
      title: 'Requirements refined and coherent',
      completed: coherent === requirements.length && requirements.length > 0,
      detail: `${coherent} of ${requirements.length} requirements marked coherent`,
    },
    {
      title: 'High priority requirements with acceptance criteria',
      completed: highWithCriteria === highPriority.length,
      detail:
        highPriority.length === 0
          ? 'No high or critical requirements'
          : `${highWithCriteria} of ${highPriority.length} high/critical requirements have detailed criteria`,
    },
    {
      title: 'Dependencies mapped',
      completed: requirements.every((req) => req.dependencies.length > 0 || req.priority !== 'critical'),
      detail: 'Critical requirements have at least one dependency or explicit confirmation',
    },
  ];

  const completedCount = checklist.filter((item) => item.completed).length;
  const progress = checklist.length > 0 ? Math.round((completedCount / checklist.length) * 100) : 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Code Readiness Checklist</h1>
          <p className="text-gray-600">
            Use this checklist to ensure the project is ready to move into implementation and automated code generation.
          </p>
        </div>
        <div className="flex items-center gap-2 rounded-full bg-blue-50 px-4 py-2 text-blue-700">
          <ListChecks className="h-5 w-5" />
          {progress}% ready
        </div>
      </div>

      <div className="bg-gray-100 h-3 rounded-full">
        <div className="bg-blue-600 h-3 rounded-full transition-all duration-300" style={{ width: `${progress}%` }} />
      </div>

      <div className="space-y-3">
        {checklist.map((item) => (
          <div
            key={item.title}
            className={`flex items-start gap-4 rounded-lg border p-4 ${
              item.completed ? 'border-green-200 bg-green-50' : 'border-gray-200 bg-white'
            }`}
          >
            {item.completed ? (
              <CheckCircle2 className="h-5 w-5 text-green-500 mt-1" />
            ) : (
              <AlertCircle className="h-5 w-5 text-yellow-500 mt-1" />
            )}
            <div>
              <h3 className="text-sm font-semibold text-gray-900">{item.title}</h3>
              <p className="text-sm text-gray-600">{item.detail}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default CodeChecklist;
