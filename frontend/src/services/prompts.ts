import apiClient, { SKIP_ERROR_TOAST_HEADER } from './api';
import { PromptBundle, PromptBundleSummary, PromptGenerateRequest, TaskPendingResponse } from '@/types';

export const promptsService = {
  async generatePrompts(
    projectId: string,
    request: PromptGenerateRequest
  ): Promise<PromptBundleSummary | TaskPendingResponse> {
    const { data } = await apiClient.post<PromptBundleSummary | TaskPendingResponse>(
      `/projects/${projectId}/prompts/generate`,
      request
    );
    return data;
  },

  async getLatestPrompts(projectId: string): Promise<PromptBundle> {
    const { data } = await apiClient.get<PromptBundle>(
      `/projects/${projectId}/prompts/latest`,
      { headers: { [SKIP_ERROR_TOAST_HEADER]: 'true' } }
    );
    return data;
  },

  async downloadBundle(projectId: string, bundleId: string): Promise<Blob> {
    const response = await apiClient.get(
      `/projects/${projectId}/prompts/bundles/${bundleId}/download`,
      { responseType: 'blob' }
    );
    return response.data;
  },
};
