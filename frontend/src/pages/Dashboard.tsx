import React from 'react';
import { useParams } from 'react-router-dom';
import { useProjects, useSSE } from '@/hooks';
import { LoadingSpinner } from '@/components/Common/LoadingSpinner';
import { formatDateTime, formatPercentage } from '@/utils';
import {
Activity,
  CheckCircle,
  AlertCircle,
  Clock,
  TrendingUp,
  FileText,
  Calendar,
  MessageSquare,
} from 'lucide-react';

export const Dashboard: React.FC = () => {
  const { projectId = 'test-project-id' } = useParams();
  const { project, isLoading, auditLogs } = useProjects(projectId);
  useSSE(projectId);

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  const getStateColor = (state: string) => {
    const colors: Record<string, string> = {
      DRAFT: 'bg-gray-100 text-gray-800',
      REQS_REFINING: 'bg-yellow-100 text-yellow-800',
      REQS_READY: 'bg-green-100 text-green-800',
      PLAN_READY: 'bg-blue-100 text-blue-800',
      PROMPTS_READY: 'bg-purple-100 text-purple-800',
      DONE: 'bg-green-100 text-green-800',
      BLOCKED: 'bg-red-100 text-red-800',
    };
    return colors[state] || 'bg-gray-100 text-gray-800';
  };

  const stats = [
    {
      label: 'Current State',
      value: project?.state || 'N/A',
      icon: Activity,
      color: 'blue',
    },
    {
      label: 'Recent Events',
      value: project?.recent_events?.length || 0,
      icon: Clock,
      color: 'yellow',
    },
    {
      label: 'Success Rate',
      value: formatPercentage(
        ((project?.recent_events?.filter(e => e.success).length || 0) /
          (project?.recent_events?.length || 1)) * 100
      ),
      icon: TrendingUp,
      color: 'green',
    },
    {
      label: 'Total Audits',
      value: auditLogs?.total || 0,
      icon: FileText,
      color: 'purple',
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Project Dashboard</h1>
        <p className="text-gray-600 mt-1">
          Monitor your project status and recent activities
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => (
          <div
            key={stat.label}
            className="bg-white rounded-lg shadow p-6 border border-gray-200"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">{stat.label}</p>
                <p className="text-2xl font-semibold mt-1">
                  {stat.label === 'Current State' ? (
                    <span className={`px-2 py-1 rounded text-sm ${getStateColor(stat.value)}`}>
                      {stat.value}
                    </span>
                  ) : (
                    stat.value
                  )}
                </p>
              </div>
              <stat.icon className={`h-8 w-8 text-${stat.color}-500`} />
            </div>
          </div>
        ))}
      </div>

      {/* Project Info */}
      {project && (
        <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
          <h2 className="text-lg font-semibold mb-4">Project Information</h2>
          <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <dt className="text-sm text-gray-600">Name</dt>
              <dd className="text-sm font-medium">{project.name}</dd>
            </div>
            <div>
              <dt className="text-sm text-gray-600">Created</dt>
              <dd className="text-sm font-medium">
                {formatDateTime(project.created_at)}
              </dd>
            </div>
            <div>
              <dt className="text-sm text-gray-600">Last Updated</dt>
              <dd className="text-sm font-medium">
                {formatDateTime(project.updated_at)}
              </dd>
            </div>
            <div>
              <dt className="text-sm text-gray-600">Project ID</dt>
              <dd className="text-sm font-mono">{project.id}</dd>
            </div>
          </dl>
        </div>
      )}

      {/* Recent Events */}
      <div className="bg-white rounded-lg shadow border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold">Recent Events</h2>
        </div>
        <div className="divide-y divide-gray-200">
          {project?.recent_events?.slice(0, 5).map((event, index) => (
            <div key={index} className="px-6 py-4 flex items-center justify-between">
              <div className="flex items-center space-x-3">
                {event.success ? (
                  <CheckCircle className="h-5 w-5 text-green-500" />
                ) : (
                  <AlertCircle className="h-5 w-5 text-red-500" />
                )}
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    {event.action}
                  </p>
                  <p className="text-xs text-gray-500">{event.type}</p>
                </div>
              </div>
              <span className="text-xs text-gray-500">
                {formatDateTime(event.created_at)}
              </span>
            </div>
          ))}
          {(!project?.recent_events || project.recent_events.length === 0) && (
            <div className="px-6 py-8 text-center text-gray-500">
              No recent events
            </div>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
        <h2 className="text-lg font-semibold mb-4">Quick Actions</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <button className="p-4 border border-gray-300 rounded-lg hover:bg-gray-50 flex flex-col items-center">
            <FileText className="h-6 w-6 text-gray-600 mb-2" />
            <span className="text-sm">Requirements</span>
          </button>
          <button className="p-4 border border-gray-300 rounded-lg hover:bg-gray-50 flex flex-col items-center">
            <Calendar className="h-6 w-6 text-gray-600 mb-2" />
            <span className="text-sm">Planning</span>
          </button>
          <button className="p-4 border border-gray-300 rounded-lg hover:bg-gray-50 flex flex-col items-center">
            <MessageSquare className="h-6 w-6 text-gray-600 mb-2" />
            <span className="text-sm">Prompts</span>
          </button>
          <button className="p-4 border border-gray-300 rounded-lg hover:bg-gray-50 flex flex-col items-center">
            <Activity className="h-6 w-6 text-gray-600 mb-2" />
            <span className="text-sm">Audit</span>
          </button>
        </div>
      </div>
    </div>
  );
};