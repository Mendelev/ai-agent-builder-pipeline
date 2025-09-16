import apiClient from './api';
import { Project, ProjectStatus, AuditLogEntry, PaginatedResponse } from '@/types';

export const projectsService = {
  async getProject(projectId: string): Promise<ProjectStatus> {
    const { data } = await apiClient.get<ProjectStatus>(`/projects/${projectId}`);
    return data;
  },

  async getAuditLogs(
    projectId: string,
    page = 1,
    pageSize = 50,
    eventType?: string
  ): Promise<PaginatedResponse<AuditLogEntry>> {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });
    
    if (eventType) {
      params.append('event_type', eventType);
    }
    
    const { data } = await apiClient.get<PaginatedResponse<AuditLogEntry>>(
      `/projects/${projectId}/audit?${params}`
    );
    return data;
  },

  async retryAgent(
    projectId: string,
    agent: string,
    force = false,
    metadata?: Record<string, any>
  ): Promise<{ task_id: string; status: string; message: string }> {
    const { data } = await apiClient.post(`/projects/${projectId}/retry/${agent}`, {
      agent,
      force,
      metadata,
    });
    return data;
  },
};