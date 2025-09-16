import { useEffect, useCallback } from 'react';
import { sseClient } from '@/services/sse';
import { useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';

export const useSSE = (projectId?: string) => {
  const queryClient = useQueryClient();

  const handleEvent = useCallback(
    (data: any) => {
      switch (data.type) {
        case 'STATE_TRANSITION':
          queryClient.invalidateQueries({ queryKey: ['project', projectId] });
          toast.success(`State changed to ${data.to_state}`);
          break;
        
        case 'AGENT_COMPLETED':
          queryClient.invalidateQueries({ queryKey: ['project', projectId] });
          toast.success(`${data.agent} completed`);
          break;
        
        case 'AGENT_FAILED':
          toast.error(`${data.agent} failed: ${data.error}`);
          break;
        
        default:
          console.log('SSE event:', data);
      }
    },
    [projectId, queryClient]
  );

  useEffect(() => {
    if (!projectId) return;

    sseClient.connect(projectId);
    sseClient.on('*', handleEvent);

    return () => {
      sseClient.off('*', handleEvent);
      sseClient.disconnect();
    };
  }, [projectId, handleEvent]);
};