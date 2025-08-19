// ABOUTME: Data transformation step for study initialization wizard
// ABOUTME: Allows users to create pipelines or skip transformation

import React, { useState, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { Dialog, DialogContent } from '@/components/ui/dialog';
import { useToast } from '@/hooks/use-toast';
import {
  ChevronRight,
  SkipForward,
  FileSpreadsheet,
  GitBranch,
  Plus,
  Play,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Info,
  Edit,
  Trash2,
  FlaskConical,
} from 'lucide-react';
import { dataUploadsApi } from '@/lib/api/data-uploads';
import { pipelinesApi, PipelineConfig, PipelineExecution, PipelineStatus } from '@/lib/api/pipelines';
import { PipelineBuilder } from '@/components/pipelines/PipelineBuilder';
import { formatBytes } from '@/lib/utils';

interface DataTransformationStepProps {
  studyId: string | null;
  data: any;
  onComplete: (data: any) => void;
  isLoading?: boolean;
}

interface UploadedDataset {
  dataset_name: string;
  rows: number;
  columns: number;
  size_bytes: number;
  file_type: string;
}

interface PipelineExecutionStatus {
  pipelineId: string;
  executionId: string;
  status: PipelineStatus;
  progress: number;
  message?: string;
}

export function DataTransformationStep({
  studyId,
  data,
  onComplete,
  isLoading,
}: DataTransformationStepProps) {
  const { toast } = useToast();
  const [showPipelineBuilder, setShowPipelineBuilder] = useState(false);
  const [editingPipelineId, setEditingPipelineId] = useState<string | null>(null);
  const [executionStatuses, setExecutionStatuses] = useState<Record<string, PipelineExecutionStatus>>({});
  const [isExecutingPipelines, setIsExecutingPipelines] = useState(false);

  // Fetch uploaded datasets
  const { data: uploads, isLoading: isLoadingDatasets } = useQuery({
    queryKey: ['dataUploads', studyId],
    queryFn: () => studyId ? dataUploadsApi.listUploads(studyId, { active_only: true }) : null,
    enabled: !!studyId,
  });

  // Fetch existing pipelines
  const { data: pipelines, refetch: refetchPipelines } = useQuery({
    queryKey: ['pipelines', studyId],
    queryFn: () => studyId ? pipelinesApi.listPipelines(studyId) : null,
    enabled: !!studyId,
  });

  // Extract datasets from uploads
  const uploadedDatasets: UploadedDataset[] = uploads?.data?.flatMap((upload: any) =>
    upload.files_extracted?.map((file: any) => ({
      dataset_name: file.dataset_name,
      rows: file.rows,
      columns: file.columns,
      size_bytes: file.size_bytes,
      file_type: file.file_type,
    })) || []
  ) || [];

  // Execute pipeline mutation
  const executePipelineMutation = useMutation({
    mutationFn: async (pipelineId: string) => {
      const response = await pipelinesApi.executePipeline({
        pipeline_config_id: pipelineId,
        triggered_by: 'initialization_wizard',
      });
      return { pipelineId, execution: response };
    },
    onSuccess: ({ pipelineId, execution }) => {
      setExecutionStatuses(prev => ({
        ...prev,
        [pipelineId]: {
          pipelineId,
          executionId: execution.id,
          status: PipelineStatus.RUNNING,
          progress: 0,
          message: 'Pipeline execution started',
        },
      }));
    },
    onError: (error: any, pipelineId) => {
      setExecutionStatuses(prev => ({
        ...prev,
        [pipelineId]: {
          pipelineId,
          executionId: '',
          status: PipelineStatus.FAILED,
          progress: 0,
          message: error.response?.data?.detail || 'Failed to execute pipeline',
        },
      }));
    },
  });

  // Poll for execution status
  useEffect(() => {
    const activeExecutions = Object.values(executionStatuses).filter(
      status => status.status === PipelineStatus.RUNNING
    );

    if (activeExecutions.length === 0) return;

    const interval = setInterval(async () => {
      for (const execution of activeExecutions) {
        try {
          const executionDetails = await pipelinesApi.getExecution(execution.executionId);
          
          // Calculate progress based on steps completed
          const totalSteps = executionDetails.execution_steps?.length || 1;
          const completedSteps = executionDetails.execution_steps?.filter(
            step => step.status === PipelineStatus.SUCCESS
          ).length || 0;
          const progress = (completedSteps / totalSteps) * 100;

          setExecutionStatuses(prev => ({
            ...prev,
            [execution.pipelineId]: {
              ...prev[execution.pipelineId],
              status: executionDetails.status,
              progress,
              message: executionDetails.error_message || 
                      `Processing ${completedSteps}/${totalSteps} steps`,
            },
          }));

          if (executionDetails.status !== PipelineStatus.RUNNING) {
            if (executionDetails.status === PipelineStatus.SUCCESS) {
              toast({
                title: 'Pipeline completed',
                description: `Successfully processed ${executionDetails.output_records} records`,
              });
            } else if (executionDetails.status === PipelineStatus.FAILED) {
              toast({
                title: 'Pipeline failed',
                description: executionDetails.error_message || 'Pipeline execution failed',
                variant: 'destructive',
              });
            }
          }
        } catch (error) {
          console.error('Error fetching execution status:', error);
        }
      }
    }, 2000); // Poll every 2 seconds

    return () => clearInterval(interval);
  }, [executionStatuses, toast]);

  const handleCreatePipeline = () => {
    setEditingPipelineId(null);
    setShowPipelineBuilder(true);
  };

  const handleEditPipeline = (pipelineId: string) => {
    setEditingPipelineId(pipelineId);
    setShowPipelineBuilder(true);
  };

  const handleDeletePipeline = async (pipelineId: string) => {
    // TODO: Implement pipeline deletion
    toast({
      title: 'Not implemented',
      description: 'Pipeline deletion will be implemented soon',
    });
  };

  const handleExecutePipelines = async () => {
    if (!pipelines?.data || pipelines.data.length === 0) {
      toast({
        title: 'No pipelines',
        description: 'Please create at least one pipeline before executing',
        variant: 'destructive',
      });
      return;
    }

    setIsExecutingPipelines(true);

    try {
      // Execute all pipelines
      for (const pipeline of pipelines.data) {
        await executePipelineMutation.mutateAsync(pipeline.id);
      }

      // Wait for all executions to complete
      await new Promise<void>((resolve) => {
        const checkInterval = setInterval(() => {
          const allStatuses = Object.values(executionStatuses);
          const allCompleted = allStatuses.every(
            status => status.status !== PipelineStatus.RUNNING
          );
          
          if (allCompleted && allStatuses.length === pipelines.data.length) {
            clearInterval(checkInterval);
            resolve();
          }
        }, 1000);

        // Timeout after 5 minutes
        setTimeout(() => {
          clearInterval(checkInterval);
          resolve();
        }, 300000);
      });

      // Check if all succeeded
      const allSucceeded = Object.values(executionStatuses).every(
        status => status.status === PipelineStatus.SUCCESS
      );

      if (allSucceeded) {
        onComplete({
          pipelines: pipelines.data.map((p: PipelineConfig) => p.id),
          executionResults: executionStatuses,
        });
      } else {
        toast({
          title: 'Some pipelines failed',
          description: 'Please review the execution results and fix any errors',
          variant: 'destructive',
        });
      }
    } catch (error) {
      console.error('Error executing pipelines:', error);
      toast({
        title: 'Execution failed',
        description: 'Failed to execute pipelines',
        variant: 'destructive',
      });
    } finally {
      setIsExecutingPipelines(false);
    }
  };

  const handleSkipTransformation = () => {
    onComplete({
      skipped: true,
      pipelines: [],
    });
  };

  const handleNextStep = () => {
    if (pipelines?.data && pipelines.data.length > 0) {
      handleExecutePipelines();
    } else {
      // If no pipelines created, treat as skip
      handleSkipTransformation();
    }
  };

  if (isLoadingDatasets) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium">Data Transformation (Optional)</h3>
        <p className="text-sm text-muted-foreground">
          Create pipelines to transform your data or skip this step
        </p>
      </div>

      {/* Uploaded Datasets */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Available Datasets</CardTitle>
          <CardDescription>
            These datasets were uploaded in the previous step
          </CardDescription>
        </CardHeader>
        <CardContent>
          {uploadedDatasets.length === 0 ? (
            <p className="text-sm text-muted-foreground">No datasets uploaded</p>
          ) : (
            <div className="space-y-2">
              {uploadedDatasets.map((dataset, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 border rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <FileSpreadsheet className="h-5 w-5 text-gray-400" />
                    <div>
                      <p className="font-medium">{dataset.dataset_name}</p>
                      <p className="text-sm text-muted-foreground">
                        {dataset.rows.toLocaleString()} rows × {dataset.columns} columns • {formatBytes(dataset.size_bytes)}
                      </p>
                    </div>
                  </div>
                  <Badge variant="secondary">{dataset.file_type}</Badge>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Skip Transformation Alert */}
      <Alert>
        <Info className="h-4 w-4" />
        <AlertDescription>
          <div className="space-y-2">
            <p className="font-medium">Data transformation is optional</p>
            <p>
              You can create pipelines to clean, filter, or transform your data before analysis.
              If your data is already in the correct format, you can skip this step.
            </p>
          </div>
        </AlertDescription>
      </Alert>

      {/* Pipelines Section */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-base">Data Pipelines</CardTitle>
              <CardDescription>
                Create transformation pipelines for your datasets
              </CardDescription>
            </div>
            <Button onClick={handleCreatePipeline} size="sm">
              <Plus className="mr-2 h-4 w-4" />
              Create Pipeline
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {pipelines?.data && pipelines.data.length > 0 ? (
            <div className="space-y-3">
              {pipelines.data.map((pipeline: PipelineConfig) => {
                const executionStatus = executionStatuses[pipeline.id];
                return (
                  <div
                    key={pipeline.id}
                    className="flex items-center justify-between p-4 border rounded-lg"
                  >
                    <div className="flex items-center gap-3 flex-1">
                      <GitBranch className="h-5 w-5 text-gray-400" />
                      <div className="flex-1">
                        <p className="font-medium">{pipeline.name}</p>
                        <p className="text-sm text-muted-foreground">
                          {pipeline.transformation_steps.length} transformation steps
                        </p>
                        {executionStatus && (
                          <div className="mt-2">
                            {executionStatus.status === PipelineStatus.RUNNING && (
                              <div className="space-y-1">
                                <div className="flex items-center gap-2">
                                  <Loader2 className="h-3 w-3 animate-spin" />
                                  <span className="text-sm">{executionStatus.message}</span>
                                </div>
                                <Progress value={executionStatus.progress} className="h-1" />
                              </div>
                            )}
                            {executionStatus.status === PipelineStatus.SUCCESS && (
                              <div className="flex items-center gap-2 text-green-600">
                                <CheckCircle2 className="h-3 w-3" />
                                <span className="text-sm">Completed successfully</span>
                              </div>
                            )}
                            {executionStatus.status === PipelineStatus.FAILED && (
                              <div className="flex items-center gap-2 text-red-600">
                                <AlertCircle className="h-3 w-3" />
                                <span className="text-sm">{executionStatus.message}</span>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleEditPipeline(pipeline.id)}
                        disabled={isExecutingPipelines}
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDeletePipeline(pipeline.id)}
                        disabled={isExecutingPipelines}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="text-center py-8">
              <GitBranch className="mx-auto h-12 w-12 text-gray-400 mb-3" />
              <p className="text-sm text-muted-foreground mb-4">
                No pipelines created yet
              </p>
              <Button onClick={handleCreatePipeline} variant="outline" size="sm">
                <Plus className="mr-2 h-4 w-4" />
                Create your first pipeline
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Actions */}
      <div className="flex justify-between pt-4 border-t">
        <Button
          variant="outline"
          onClick={handleSkipTransformation}
          disabled={isExecutingPipelines || isLoading}
          size="lg"
        >
          <SkipForward className="mr-2 h-4 w-4" />
          Skip Transformation
        </Button>
        <Button
          onClick={handleNextStep}
          disabled={isExecutingPipelines || isLoading}
          size="lg"
        >
          {isExecutingPipelines ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Executing Pipelines...
            </>
          ) : pipelines?.data && pipelines.data.length > 0 ? (
            <>
              <Play className="mr-2 h-4 w-4" />
              Execute & Continue
            </>
          ) : (
            <>
              Continue
              <ChevronRight className="ml-2 h-4 w-4" />
            </>
          )}
        </Button>
      </div>

      {/* Pipeline Builder Dialog */}
      <Dialog open={showPipelineBuilder} onOpenChange={setShowPipelineBuilder}>
        <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto">
          <PipelineBuilder
            studyId={studyId!}
            pipelineId={editingPipelineId}
            onClose={() => setShowPipelineBuilder(false)}
            onSave={() => {
              setShowPipelineBuilder(false);
              refetchPipelines();
            }}
          />
        </DialogContent>
      </Dialog>
    </div>
  );
}