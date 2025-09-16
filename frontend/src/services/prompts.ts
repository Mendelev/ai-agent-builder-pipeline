import apiClient from './api';
import { PromptBundle, PromptGenerateRequest } from '@/types';

export const promptsService = {
  async generatePrompts(
    projectId: string,
    request: PromptGenerateRequest
  ): Promise<{ id: string; version: number; total_prompts: number }> {
    const { data } = await apiClient.post(
      `/projects/${projectId}/prompts/generate`,
      request
    );
    return data;
  },

  async getLatestPrompts(projectId: string): Promise<PromptBundle> {
    const { data } = await apiClient.get<PromptBundle>(
      `/projects/${projectId}/prompts/latest`
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