// ABOUTME: Hook for managing study initialization with real-time progress
// ABOUTME: Handles WebSocket connection and initialization state management

import { useState, useCallback, useEffect } from 'react';
import { useWebSocket } from './use-websocket';
import { studiesApi } from '@/lib/api/studies';
import { toast } from '@/hooks/use-toast';

export interface InitializationStep {
  name: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  progress: number;
  error?: string;
  details?: any;
}

export interface InitializationState {
  status: 'not_started' | 'pending' | 'initializing' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  currentStep: string;
  steps: {
    template_application: InitializationStep;
    data_upload: InitializationStep;
    data_conversion: InitializationStep;
    field_mapping: InitializationStep;
  };
  error?: string;
  taskId?: string;
}

const initialSteps: InitializationState['steps'] = {
  template_application: {
    name: 'Applying Template',
    status: 'pending',
    progress: 0,
  },
  data_upload: {
    name: 'Processing Data Files',
    status: 'pending',
    progress: 0,
  },
  data_conversion: {
    name: 'Converting to Parquet',
    status: 'pending',
    progress: 0,
  },
  field_mapping: {
    name: 'Configuring Field Mappings',
    status: 'pending',
    progress: 0,
  },
};

export function useStudyInitialization(studyId: string | null) {
  const [state, setState] = useState<InitializationState>({
    status: 'not_started',
    progress: 0,
    currentStep: '',
    steps: initialSteps,
  });

  const [isInitializing, setIsInitializing] = useState(false);

  // WebSocket connection for progress updates
  const wsUrl = studyId ? `/ws/studies/${studyId}/initialization` : null;
  
  const { isConnected, sendMessage } = useWebSocket(wsUrl, {
    onMessage: (message) => {
      console.log('Initialization progress:', message);
      
      switch (message.type) {
        case 'current_status':
          // Initial status when connecting
          setState(prev => ({
            ...prev,
            status: message.initialization_status || 'not_started',
            progress: message.initialization_progress || 0,
            steps: message.initialization_steps?.steps 
              ? mapStepsFromBackend(message.initialization_steps.steps)
              : prev.steps,
          }));
          break;
          
        case 'progress':
          // Progress update
          setState(prev => ({
            ...prev,
            progress: message.progress || message.overall_progress || prev.progress,
            currentStep: message.step || prev.currentStep,
            steps: updateStepProgress(
              prev.steps,
              message.step,
              message.step_progress,
              message.step_status
            ),
          }));
          break;
          
        case 'status_change':
          // Status change
          setState(prev => ({
            ...prev,
            status: message.status,
            progress: message.progress || prev.progress,
          }));
          
          if (message.status === 'completed') {
            toast({
              title: 'Study Initialized',
              description: 'Study has been successfully initialized',
            });
          } else if (message.status === 'failed') {
            toast({
              title: 'Initialization Failed',
              description: message.error || 'An error occurred during initialization',
              variant: 'destructive',
            });
          }
          break;
          
        case 'error':
          // Error message
          setState(prev => ({
            ...prev,
            status: 'failed',
            error: message.error || message.message,
          }));
          
          toast({
            title: 'Initialization Error',
            description: message.error || message.message,
            variant: 'destructive',
          });
          break;
      }
    },
    onOpen: () => {
      // Request current status when connected
      sendMessage({ type: 'request_status' });
    },
  });

  // Initialize study
  const initializeStudy = useCallback(async (
    templateId: string,
    skipDataUpload = false
  ) => {
    if (!studyId) return;
    
    setIsInitializing(true);
    setState(prev => ({
      ...prev,
      status: 'pending',
      error: undefined,
    }));
    
    try {
      const response = await studiesApi.initializeStudyWithProgress(studyId, {
        template_id: templateId,
        skip_data_upload: skipDataUpload,
      });
      
      setState(prev => ({
        ...prev,
        status: 'pending',
        taskId: response.task_id,
      }));
      
      toast({
        title: 'Initialization Started',
        description: 'Study initialization has been queued',
      });
      
      return response;
    } catch (error: any) {
      setState(prev => ({
        ...prev,
        status: 'failed',
        error: error.message || 'Failed to start initialization',
      }));
      
      toast({
        title: 'Initialization Failed',
        description: error.message || 'Failed to start initialization',
        variant: 'destructive',
      });
      
      throw error;
    } finally {
      setIsInitializing(false);
    }
  }, [studyId]);

  // Upload study data files
  const uploadFiles = useCallback(async (files: File[]) => {
    if (!studyId) return;
    
    try {
      const formData = new FormData();
      files.forEach(file => {
        formData.append('files', file);
      });
      
      const response = await studiesApi.uploadStudyData(studyId, formData);
      
      toast({
        title: 'Files Uploaded',
        description: `Successfully uploaded ${response.total_files} files`,
      });
      
      return response;
    } catch (error: any) {
      toast({
        title: 'Upload Failed',
        description: error.message || 'Failed to upload files',
        variant: 'destructive',
      });
      
      throw error;
    }
  }, [studyId]);

  // Get initialization status
  const getStatus = useCallback(async () => {
    if (!studyId) return;
    
    try {
      const response = await studiesApi.getInitializationStatus(studyId);
      
      setState({
        status: response.initialization_status as InitializationState['status'],
        progress: response.initialization_progress,
        currentStep: response.initialization_steps?.current_step || '',
        steps: response.initialization_steps?.steps 
          ? mapStepsFromBackend(response.initialization_steps.steps)
          : initialSteps,
      });
      
      return response;
    } catch (error) {
      console.error('Failed to get initialization status:', error);
    }
  }, [studyId]);

  // Retry failed initialization
  const retryInitialization = useCallback(async () => {
    if (!studyId) return;
    
    try {
      const response = await studiesApi.retryInitialization(studyId);
      
      setState(prev => ({
        ...prev,
        status: 'pending',
        error: undefined,
        taskId: response.task_id,
      }));
      
      toast({
        title: 'Retry Started',
        description: 'Retrying study initialization',
      });
      
      return response;
    } catch (error: any) {
      toast({
        title: 'Retry Failed',
        description: error.message || 'Failed to retry initialization',
        variant: 'destructive',
      });
      
      throw error;
    }
  }, [studyId]);

  // Cancel initialization
  const cancelInitialization = useCallback(async () => {
    if (!studyId) return;
    
    try {
      await studiesApi.cancelInitialization(studyId);
      
      setState(prev => ({
        ...prev,
        status: 'cancelled',
      }));
      
      toast({
        title: 'Initialization Cancelled',
        description: 'Study initialization has been cancelled',
      });
    } catch (error: any) {
      toast({
        title: 'Cancel Failed',
        description: error.message || 'Failed to cancel initialization',
        variant: 'destructive',
      });
      
      throw error;
    }
  }, [studyId]);

  // Fetch initial status on mount
  useEffect(() => {
    if (studyId) {
      getStatus();
    }
  }, [studyId, getStatus]);

  return {
    state,
    isConnected,
    isInitializing,
    initializeStudy,
    uploadFiles,
    retryInitialization,
    cancelInitialization,
    refreshStatus: getStatus,
  };
}

// Helper functions
function mapStepsFromBackend(backendSteps: any): InitializationState['steps'] {
  const steps = { ...initialSteps };
  
  Object.entries(backendSteps).forEach(([key, value]: [string, any]) => {
    if (key in steps) {
      steps[key as keyof typeof steps] = {
        name: steps[key as keyof typeof steps].name,
        status: value.status || 'pending',
        progress: value.progress || 0,
        error: value.error,
        details: value,
      };
    }
  });
  
  return steps;
}

function updateStepProgress(
  steps: InitializationState['steps'],
  stepName: string,
  progress?: number,
  status?: string
): InitializationState['steps'] {
  const updatedSteps = { ...steps };
  
  if (stepName in updatedSteps) {
    const step = updatedSteps[stepName as keyof typeof updatedSteps];
    updatedSteps[stepName as keyof typeof updatedSteps] = {
      ...step,
      progress: progress ?? step.progress,
      status: (status as InitializationStep['status']) ?? step.status,
    };
  }
  
  return updatedSteps;
}