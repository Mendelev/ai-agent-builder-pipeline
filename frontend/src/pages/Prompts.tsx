import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import toast from 'react-hot-toast';
import { Download, RefreshCw } from 'lucide-react';

import { promptsService } from '@/services/prompts';
import { planService } from '@/services/plan';
import { LoadingSpinner } from '@/components/Common/LoadingSpinner';
import { formatDateTime } from '@/utils';
import { PromptBundle } from '@/types';

const Prompts: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const queryClient = useQueryClient();
  const [includeCode, setIncludeCode] = useState(false);

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

  const promptsQuery = useQuery({
    queryKey: ['prompts', projectId],
    enabled: !!projectId,
    queryFn: async () => {
      if (!projectId) return null;
      try {
        return await promptsService.getLatestPrompts(projectId);
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
      promptsService.generatePrompts(projectId!, {
        include_code: includeCode,
        plan_id: planQuery.data?.id,
      }),
    onSuccess: (result) => {
      if ('task_id' in result) {
        toast.success('Prompt generation queued');
      } else {
        toast.success('Prompt bundle ready');
      }
      queryClient.invalidateQueries({ queryKey: ['prompts', projectId] });
    },
  });

  const handleDownload = async (bundle: PromptBundle) => {
    if (!projectId) return;
    const blob = await promptsService.downloadBundle(projectId, bundle.id);
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `prompts_${bundle.version}.zip`;
    link.click();
    URL.revokeObjectURL(url);
  };

  if (!projectId) {
    return (
      <div className="text-center py-12 text-gray-500">
        Select a project to view prompts.
      </div>
    );
  }

  if (promptsQuery.isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  const bundle = promptsQuery.data;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Prompt Bundles</h1>
          <p className="text-gray-600">
            Generate and review AI prompt packages derived from the execution plan.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <label className="flex items-center text-sm text-gray-600 gap-2">
            <input
              type="checkbox"
              checked={includeCode}
              onChange={(event) => setIncludeCode(event.target.checked)}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            Include code generation guidance
          </label>
          <button
            onClick={() => generateMutation.mutate()}
            disabled={generateMutation.isPending || !planQuery.data}
            className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-blue-400"
          >
            <RefreshCw className="h-4 w-4" />
            Generate Prompts
          </button>
        </div>
      </div>

      {!planQuery.data && (
        <div className="rounded-md border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
          Generate a plan before requesting prompts. Visit the planning section to create one.
        </div>
      )}

      {bundle ? (
        <div className="space-y-4">
          <div className="flex items-center justify-between rounded-lg border border-gray-200 bg-white p-6 shadow">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Latest Bundle</h2>
              <p className="text-sm text-gray-600">
                Version {bundle.version} • {bundle.total_prompts} prompts • Generated {formatDateTime(bundle.created_at)}
              </p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => handleDownload(bundle)}
                className="inline-flex items-center gap-2 rounded-md border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
              >
                <Download className="h-4 w-4" />
                Download ZIP
              </button>
            </div>
          </div>

          <div className="rounded-lg border border-gray-200 bg-white p-6 shadow">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Project Context</h3>
            <div className="prose max-w-none">
              <pre className="whitespace-pre-wrap break-words text-sm text-gray-700">
                {bundle.context_md}
              </pre>
            </div>
          </div>

          <div className="space-y-4">
            {(bundle.prompts ?? []).map((prompt) => (
              <div key={prompt.id} className="rounded-lg border border-gray-200 bg-white p-6 shadow">
                <div className="flex items-start justify-between">
                  <div>
                    <h4 className="text-base font-semibold text-gray-900">{prompt.title}</h4>
                    <p className="text-xs text-gray-500">Phase {prompt.phase_id} • Sequence {prompt.sequence}</p>
                  </div>
                  <span className="text-xs text-gray-500">
                    Est. tokens: {Math.round(prompt.metadata?.estimated_tokens ?? 0)}
                  </span>
                </div>
                <pre className="mt-4 whitespace-pre-wrap break-words rounded bg-gray-50 p-4 text-sm text-gray-700">
                  {prompt.content_md}
                </pre>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="rounded-md border border-gray-200 bg-white p-8 text-center text-gray-500 shadow">
          No prompt bundle generated yet.
        </div>
      )}
    </div>
  );
};

export default Prompts;
