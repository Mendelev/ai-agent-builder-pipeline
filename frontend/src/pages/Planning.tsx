import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { planService } from '@/services/plan';
import { LoadingSpinner } from '@/components/Common/LoadingSpinner';
import { Calendar, Clock, AlertTriangle, Users } from 'lucide-react';
import { formatPercentage } from '@/utils';

export const Planning: React.FC = () => {
  const projectId = 'test-project-id';

  const { data: plan, isLoading } = useQuery({
    queryKey: ['plan', projectId],
    queryFn: () => planService.getLatestPlan(projectId),
  });

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (!plan) {
    return (
      <div className="text-center py-12">
        <Calendar className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <p className="text-gray-600">No plan generated yet</p>
      </div>
    );
  }

  const getRiskColor = (level: string) => {
    const colors: Record<string, string> = {
      low: 'bg-green-100 text-green-800',
      medium: 'bg-yellow-100 text-yellow-800',
      high: 'bg-orange-100 text-orange-800',
      critical: 'bg-red-100 text-red-800',
    };
    return colors[level] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Project Planning</h1>
        <p className="text-gray-600 mt-1">Version {plan.version}</p>
      </div>

      {/* Metrics */}
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

      {/* Timeline */}
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
                    <span className={`px-2 py-1 rounded text-xs font-medium ${getRiskColor(phase.risk_level)}`}>
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
    </div>
  );
};