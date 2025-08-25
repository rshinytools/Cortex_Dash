// ABOUTME: Hook for managing real-time transformation progress updates
// ABOUTME: Handles WebSocket connection or polling fallback for pipeline execution status

import { useState, useEffect, useCallback, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { secureApiClient } from '@/lib/api/secure-client';
import { useToast } from '@/hooks/use-toast';

export interface PipelineExecution {
  id: string;
  study_id: string;
  status: 'pending' | 'running' | 'success' | 'failed' | 'cancelled';
  progress: number;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
  pipelines: PipelineStatus[];
  logs: ExecutionLog[];
}

export interface PipelineStatus {
  id: string;
  name: string;
  type: string;
  status: 'pending' | 'running' | 'success' | 'failed' | 'skipped';
  progress: number;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
  output_summary?: {
    rows_processed?: number;
    rows_output?: number;
    execution_time_ms?: number;
  };
}

export interface ExecutionLog {
  id: string;
  timestamp: string;
  level: 'info' | 'warning' | 'error' | 'debug';
  pipeline_id?: string;
  message: string;
  details?: any;
}

interface UseTransformationProgressOptions {
  studyId: string;
  executionId?: string;
  pollingInterval?: number;
  enableWebSocket?: boolean;
}

export function useTransformationProgress({
  studyId,
  executionId,
  pollingInterval = 2000,
  enableWebSocket = true,
}: UseTransformationProgressOptions) {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const [isConnected, setIsConnected] = useState(false);
  const [execution, setExecution] = useState<PipelineExecution | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;

  // Query for current execution status (polling fallback)
  const { data: executionData, isLoading } = useQuery({
    queryKey: ['pipeline-execution', studyId, executionId],
    queryFn: async () => {
      if (!executionId) {
        // Get latest execution
        const response = await secureApiClient.get(`/studies/${studyId}/pipeline/executions/latest`);
        return response.data;
      }
      const response = await secureApiClient.get(`/studies/${studyId}/pipeline/executions/${executionId}`);
      return response.data;
    },
    enabled: !!studyId && (!enableWebSocket || !isConnected),
    refetchInterval: (!enableWebSocket || !isConnected) ? pollingInterval : false,
  });

  // Mutation to retry failed pipelines
  const retryPipeline = useMutation({
    mutationFn: async (pipelineId: string) => {
      const response = await secureApiClient.post(
        `/studies/${studyId}/pipeline/executions/${executionId || execution?.id}/retry`,
        { pipeline_id: pipelineId }
      );
      return response.data;
    },
    onSuccess: () => {
      toast({
        title: 'Pipeline retry started',
        description: 'The pipeline is being retried.',
      });
      queryClient.invalidateQueries({ queryKey: ['pipeline-execution', studyId] });
    },
    onError: (error) => {
      toast({
        title: 'Failed to retry pipeline',
        description: error instanceof Error ? error.message : 'An error occurred',
        variant: 'destructive',
      });
    },
  });

  // Mutation to cancel execution
  const cancelExecution = useMutation({
    mutationFn: async () => {
      const response = await secureApiClient.post(
        `/studies/${studyId}/pipeline/executions/${executionId || execution?.id}/cancel`
      );
      return response.data;
    },
    onSuccess: () => {
      toast({
        title: 'Execution cancelled',
        description: 'The pipeline execution has been cancelled.',
      });
      queryClient.invalidateQueries({ queryKey: ['pipeline-execution', studyId] });
    },
    onError: (error) => {
      toast({
        title: 'Failed to cancel execution',
        description: error instanceof Error ? error.message : 'An error occurred',
        variant: 'destructive',
      });
    },
  });

  // WebSocket connection management
  const connectWebSocket = useCallback(() => {
    if (!enableWebSocket || !studyId || typeof window === 'undefined') return;

    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws';
    const ws = new WebSocket(`${wsUrl}/studies/${studyId}/pipeline/progress`);

    ws.onopen = () => {
      console.log('WebSocket connected for pipeline progress');
      setIsConnected(true);
      reconnectAttemptsRef.current = 0;
      
      // Subscribe to execution updates
      if (executionId) {
        ws.send(JSON.stringify({ 
          type: 'subscribe', 
          execution_id: executionId 
        }));
      }
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.type === 'execution_update') {
          setExecution(data.execution);
          queryClient.setQueryData(
            ['pipeline-execution', studyId, data.execution.id],
            data.execution
          );
        } else if (data.type === 'log') {
          // Append log to existing logs
          setExecution((prev) => {
            if (!prev) return prev;
            return {
              ...prev,
              logs: [...prev.logs, data.log],
            };
          });
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
      
      // Attempt to reconnect
      if (reconnectAttemptsRef.current < maxReconnectAttempts) {
        reconnectAttemptsRef.current++;
        const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000);
        
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log(`Attempting to reconnect... (attempt ${reconnectAttemptsRef.current})`);
          connectWebSocket();
        }, delay);
      }
    };

    wsRef.current = ws;
  }, [studyId, executionId, enableWebSocket, queryClient]);

  // Initialize WebSocket connection
  useEffect(() => {
    connectWebSocket();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [connectWebSocket]);

  // Update execution state from polling data
  useEffect(() => {
    if (executionData && !isConnected) {
      setExecution(executionData);
    }
  }, [executionData, isConnected]);

  // Get execution logs
  const getLogs = useCallback(
    (pipelineId?: string, level?: string) => {
      if (!execution) return [];
      
      let logs = execution.logs;
      
      if (pipelineId) {
        logs = logs.filter((log) => log.pipeline_id === pipelineId);
      }
      
      if (level) {
        logs = logs.filter((log) => log.level === level);
      }
      
      return logs;
    },
    [execution]
  );

  // Get pipeline by ID
  const getPipeline = useCallback(
    (pipelineId: string) => {
      if (!execution) return null;
      return execution.pipelines.find((p) => p.id === pipelineId) || null;
    },
    [execution]
  );

  return {
    execution,
    isLoading,
    isConnected,
    retryPipeline: retryPipeline.mutate,
    cancelExecution: cancelExecution.mutate,
    isRetrying: retryPipeline.isPending,
    isCancelling: cancelExecution.isPending,
    getLogs,
    getPipeline,
  };
}