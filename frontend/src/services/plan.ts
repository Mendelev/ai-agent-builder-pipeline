import apiClient, { SKIP_ERROR_TOAST_HEADER } from './api';
import { Plan, PlanGenerateRequest, PlanSummary, TaskPendingResponse } from '@/types';

export const planService = {
  async generatePlan(
    projectId: string,
    request: PlanGenerateRequest
  ): Promise<PlanSummary | TaskPendingResponse> {
    const { data } = await apiClient.post<PlanSummary | TaskPendingResponse>(
      `/projects/${projectId}/plan`,
      request
    );
    return data;
  },

  async getLatestPlan(projectId: string): Promise<Plan> {
    const { data } = await apiClient.get<Plan>(
      `/projects/${projectId}/plan/latest`,
      { headers: { [SKIP_ERROR_TOAST_HEADER]: 'true' } }
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
