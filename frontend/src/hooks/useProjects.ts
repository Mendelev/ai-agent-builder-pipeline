import { useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { projectsService } from '@/services/projects';
import { useProjectStore } from '@/store';
import toast from 'react-hot-toast';

export const useProjects = (projectId?: string) => {
  const queryClient = useQueryClient();
  const { setCurrentProject, setCurrentProjectId, reset } = useProjectStore();

  useEffect(() => {
    if (!projectId) {
      reset();
    } else {
      setCurrentProjectId(projectId);
    }
  }, [projectId, reset, setCurrentProjectId]);

  const projectQuery = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => projectsService.getProject(projectId!),
    enabled: !!projectId,
    onSuccess: (data) => {
      setCurrentProject(data ?? null);
    },
    onError: () => {
      setCurrentProject(null);
    },
  });

  const auditLogsQuery = useQuery({
    queryKey: ['audit', projectId],
    queryFn: () => projectsService.getAuditLogs(projectId!, 1, 50),
    enabled: !!projectId,
  });

  const retryAgentMutation = useMutation({
    mutationFn: ({ agent, force }: { agent: string; force?: boolean }) =>
      projectsService.retryAgent(projectId!, agent, force),
    onSuccess: () => {
      toast.success('Agent retry queued');
      queryClient.invalidateQueries({ queryKey: ['project', projectId] });
    },
  });

  return {
    project: projectQuery.data,
    isLoading: projectQuery.isLoading,
    auditLogs: auditLogsQuery.data,
    auditLogsLoading: auditLogsQuery.isLoading,
    retryAgent: retryAgentMutation.mutate,
  };
};
