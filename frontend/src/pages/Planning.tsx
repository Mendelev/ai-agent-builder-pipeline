import React from 'react';
import { useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import toast from 'react-hot-toast';
import { Calendar, Clock, AlertTriangle, Users, RefreshCw } from 'lucide-react';

import { planService } from '@/services/plan';
import { LoadingSpinner } from '@/components/Common/LoadingSpinner';
import { formatPercentage } from '@/utils';

export const Planning: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const queryClient = useQueryClient();

  const planQuery = useQuery({
    queryKey: ['plan', projectId],
    enabled: !!projectId,
    queryFn: async () => {
      if (!projectId) return null;
      try {
        return await planService.getLatestPlan(projectId);
      } catch (error) {
        if (axios.isAxiosError(error) && error.response?.status === 404) {
          return null;
        }
        throw error;
      }
    },
  });

  const generateMutation = useMutation({
    mutationFn: () =>
      planService.generatePlan(projectId!, {
        source: 'requirements',
        use_code: false,
        include_checklist: true,
      }),
    onSuccess: (result) => {
      if ('task_id' in result) {
        toast.success('Plan generation queued');
      } else {
        toast.success('Plan generated');
      }
      queryClient.invalidateQueries({ queryKey: ['plan', projectId] });
    },
  });

  if (!projectId) {
    return (
      <div className="text-center py-12 text-gray-500">
        Select a project to review planning data.
      </div>
    );
  }

  if (planQuery.isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  const plan = planQuery.data;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Project Planning</h1>
          {plan && <p className="text-gray-600 mt-1">Version {plan.version}</p>}
        </div>
        <button
          onClick={() => generateMutation.mutate()}
          disabled={generateMutation.isPending}
          className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-blue-400"
        >
          <RefreshCw className="h-4 w-4" />
          Generate Plan
        </button>
      </div>

      {!plan && (
        <div className="rounded-md border border-gray-200 bg-white p-10 text-center shadow">
          <Calendar className="mx-auto mb-4 h-12 w-12 text-gray-400" />
          <p className="text-gray-600 mb-4">No plan generated yet for this project.</p>
          <p className="text-sm text-gray-500">
            Generate a plan to organize phases, dependencies, and risk levels based on your refined requirements.
          </p>
        </div>
      )}

      {plan && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Total Duration</p>
                  <p className="text-2xl font-semibold">
                    {plan.total_duration_days} days
                  </p>
                </div>
                <Clock className="h-8 w-8 text-blue-500" />
              </div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Coverage</p>
                  <p className="text-2xl font-semibold">
                    {formatPercentage(plan.coverage_percentage)}
                  </p>
                </div>
                <Calendar className="h-8 w-8 text-green-500" />
              </div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Risk Score</p>
                  <p className="text-2xl font-semibold">
                    {(plan.risk_score * 100).toFixed(0)}%
                  </p>
                </div>
                <AlertTriangle className="h-8 w-8 text-yellow-500" />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">Project Timeline</h2>
            <div className="space-y-4">
              {plan.phases.map((phase, index) => (
                <div key={phase.id} className="relative">
                  {index < plan.phases.length - 1 && (
                    <div className="absolute left-6 top-12 bottom-0 w-0.5 bg-gray-300" />
                  )}
                  <div className="flex items-start space-x-4">
                    <div className="flex-shrink-0 w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                      <span className="text-sm font-semibold text-blue-600">
                        {phase.sequence}
                      </span>
                    </div>
                    <div className="flex-1 bg-gray-50 rounded-lg p-4">
                      <div className="flex items-start justify-between">
                        <div>
                          <h3 className="font-semibold text-gray-900">
                            {phase.phase_id}: {phase.title}
                          </h3>
                          <p className="text-sm text-gray-600 mt-1">
                            {phase.objective}
                          </p>
                        </div>
                        <span
                          className={`px-2 py-1 rounded text-xs font-medium ${
                            phase.risk_level === 'critical'
                              ? 'bg-red-100 text-red-800'
                              : phase.risk_level === 'high'
                              ? 'bg-orange-100 text-orange-800'
                              : phase.risk_level === 'medium'
                              ? 'bg-yellow-100 text-yellow-800'
                              : 'bg-green-100 text-green-800'
                          }`}
                        >
                          {phase.risk_level}
                        </span>
                      </div>

                      <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div>
                          <span className="text-gray-500">Duration:</span>
                          <span className="ml-2 font-medium">{phase.estimated_days} days</span>
                        </div>
                        <div>
                          <span className="text-gray-500">Requirements:</span>
                          <span className="ml-2 font-medium">{phase.requirements_covered.length}</span>
                        </div>
                        <div>
                          <span className="text-gray-500">Activities:</span>
                          <span className="ml-2 font-medium">{phase.activities.length}</span>
                        </div>
                        <div>
                          <span className="text-gray-500">Dependencies:</span>
                          <span className="ml-2 font-medium">{phase.dependencies.length}</span>
                        </div>
                      </div>

                      {phase.resources_required && Object.keys(phase.resources_required).length > 0 && (
                        <div className="mt-3 flex items-center space-x-4">
                          <Users className="h-4 w-4 text-gray-500" />
                          {Object.entries(phase.resources_required).map(([role, count]) => (
                            <span key={role} className="text-xs text-gray-600">
                              {count} {role}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
};
