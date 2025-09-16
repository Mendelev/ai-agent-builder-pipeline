import apiClient from './api';
import { Plan, PlanGenerateRequest } from '@/types';

export const planService = {
  async generatePlan(
    projectId: string,
    request: PlanGenerateRequest
  ): Promise<{ id: string; version: number; total_phases: number }> {
    const { data } = await apiClient.post(
      `/projects/${projectId}/plan`,
      request
    );
    return data;
  },

  async getLatestPlan(projectId: string): Promise<Plan> {
    const { data } = await apiClient.get<Plan>(
      `/projects/${projectId}/plan/latest`
    );
    return data;
  },

  async getPlanById(projectId: string, planId: string): Promise<Plan> {
    const { data } = await apiClient.get<Plan>(
      `/projects/${projectId}/plan/${planId}`
    );
    return data;
  },
};