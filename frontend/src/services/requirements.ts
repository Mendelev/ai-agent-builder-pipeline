import apiClient from './api';
import { Requirement, RequirementBulkCreate } from '@/types';

export const requirementsService = {
  async createRequirements(
    projectId: string,
    requirements: Requirement[]
  ): Promise<Requirement[]> {
    const { data } = await apiClient.post<Requirement[]>(
      `/projects/${projectId}/requirements`,
      { requirements }
    );
    return data;
  },

  async listRequirements(projectId: string): Promise<Requirement[]> {
    const { data } = await apiClient.get<Requirement[]>(
      `/projects/${projectId}/requirements`
    );
    return data;
  },

  async refineRequirements(
    projectId: string,
    context?: string
  ): Promise<{ task_id: string; message: string }> {
    const { data } = await apiClient.post(
      `/projects/${projectId}/requirements/refine`,
      { context }
    );
    return data;
  },

  async finalizeRequirements(
    projectId: string,
    force = false
  ): Promise<{ success: boolean; message: string }> {
    const { data } = await apiClient.post(
      `/projects/${projectId}/requirements/finalize`,
      { force }
    );
    return data;
  },

  async exportRequirements(
    projectId: string,
    format: 'json' | 'md' = 'json'
  ): Promise<any> {
    const { data } = await apiClient.get(
      `/projects/${projectId}/requirements/export?format=${format}`
    );
    return data;
  },
};