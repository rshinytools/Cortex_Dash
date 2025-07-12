// ABOUTME: Main component for managing data pipelines
// ABOUTME: Displays pipeline list, creation, and execution monitoring

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Plus,
  Play,
  Pause,
  RefreshCw,
  Settings,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  GitBranch,
  Code,
  Filter,
  Database,
} from 'lucide-react';
import { format } from 'date-fns';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useToast } from '@/hooks/use-toast';
import { pipelinesApi, PipelineStatus, TransformationType } from '@/lib/api/pipelines';
import { PipelineBuilder } from './PipelineBuilder';
import { PipelineExecutionDetails } from './PipelineExecutionDetails';
import { Skeleton } from '@/components/ui/skeleton';

interface PipelineManagerProps {
  studyId: string;
}

const STATUS_CONFIG = {
  [PipelineStatus.PENDING]: { label: 'Pending', color: 'default', icon: Clock },
  [PipelineStatus.RUNNING]: { label: 'Running', color: 'default', icon: RefreshCw },
  [PipelineStatus.SUCCESS]: { label: 'Success', color: 'success', icon: CheckCircle },
  [PipelineStatus.FAILED]: { label: 'Failed', color: 'destructive', icon: XCircle },
  [PipelineStatus.CANCELLED]: { label: 'Cancelled', color: 'secondary', icon: XCircle },
  [PipelineStatus.SCHEDULED]: { label: 'Scheduled', color: 'outline', icon: Clock },
};

const TRANSFORMATION_ICONS = {
  [TransformationType.PYTHON_SCRIPT]: Code,
  [TransformationType.SQL_QUERY]: Database,
  [TransformationType.FILTER]: Filter,
  [TransformationType.MAPPING]: GitBranch,
  [TransformationType.AGGREGATION]: Database,
  [TransformationType.PIVOT]: GitBranch,
  [TransformationType.JOIN]: GitBranch,
  [TransformationType.CUSTOM]: Code,
};

export function PipelineManager({ studyId }: PipelineManagerProps) {
  const [showBuilder, setShowBuilder] = useState(false);
  const [selectedPipeline, setSelectedPipeline] = useState<string | null>(null);
  const [selectedExecution, setSelectedExecution] = useState<string | null>(null);
  const { toast } = useToast();
  const queryClient = useQueryClient();

  // Fetch pipelines
  const { data: pipelines, isLoading } = useQuery({
    queryKey: ['pipelines', studyId],
    queryFn: () => pipelinesApi.listPipelines(studyId),
  });

  // Execute pipeline mutation
  const executeMutation = useMutation({
    mutationFn: (pipelineId: string) =>
      pipelinesApi.executePipeline({
        pipeline_config_id: pipelineId,
        triggered_by: 'manual',
      }),
    onSuccess: (data) => {
      toast({
        title: 'Pipeline execution started',
        description: `Task ID: ${data.task_id}`,
      });
      queryClient.invalidateQueries({ queryKey: ['pipelines', studyId] });
      setSelectedExecution(data.execution_id);
    },
    onError: (err: any) => {
      toast({
        title: 'Execution failed',
        description: err.response?.data?.detail || 'Failed to start pipeline',
        variant: 'destructive',
      });
    },
  });

  const renderStatus = (status: PipelineStatus) => {
    const config = STATUS_CONFIG[status];
    const Icon = config.icon;

    return (
      <Badge variant={config.color as any} className="gap-1">
        {status === PipelineStatus.RUNNING ? (
          <Icon className="h-3 w-3 animate-spin" />
        ) : (
          <Icon className="h-3 w-3" />
        )}
        {config.label}
      </Badge>
    );
  };

  const renderTransformationSteps = (steps: any[]) => {
    return (
      <div className="flex items-center gap-1">
        {steps.map((step, idx) => {
          const Icon = TRANSFORMATION_ICONS[step.type as keyof typeof TRANSFORMATION_ICONS] || Code;
          return (
            <div key={idx} className="group relative">
              <Icon className="h-4 w-4 text-muted-foreground" />
              <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block">
                <div className="bg-gray-900 text-white text-xs rounded px-2 py-1 whitespace-nowrap">
                  {step.name}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Data Pipelines</CardTitle>
          <CardDescription>Loading pipelines...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (selectedExecution) {
    return (
      <PipelineExecutionDetails
        executionId={selectedExecution}
        onClose={() => setSelectedExecution(null)}
      />
    );
  }

  if (showBuilder) {
    return (
      <PipelineBuilder
        studyId={studyId}
        pipelineId={selectedPipeline}
        onClose={() => {
          setShowBuilder(false);
          setSelectedPipeline(null);
        }}
        onSave={() => {
          setShowBuilder(false);
          setSelectedPipeline(null);
          queryClient.invalidateQueries({ queryKey: ['pipelines', studyId] });
        }}
      />
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Data Pipelines</CardTitle>
            <CardDescription>
              Configure and execute data transformation pipelines
            </CardDescription>
          </div>
          <Button onClick={() => setShowBuilder(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Create Pipeline
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {pipelines?.length === 0 ? (
          <div className="text-center py-12">
            <Database className="mx-auto h-12 w-12 text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              No pipelines configured
            </h3>
            <p className="text-sm text-gray-500 mb-4">
              Create a pipeline to transform and process your data
            </p>
            <Button onClick={() => setShowBuilder(true)}>
              <Plus className="mr-2 h-4 w-4" />
              Create Your First Pipeline
            </Button>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Version</TableHead>
                <TableHead>Transformation Steps</TableHead>
                <TableHead>Schedule</TableHead>
                <TableHead>Last Execution</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {pipelines?.map((pipeline: any) => (
                <TableRow key={pipeline.id}>
                  <TableCell>
                    <div>
                      <div className="font-medium">{pipeline.name}</div>
                      {pipeline.description && (
                        <div className="text-sm text-gray-500">
                          {pipeline.description}
                        </div>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline">v{pipeline.version}</Badge>
                  </TableCell>
                  <TableCell>{renderTransformationSteps(pipeline.transformation_steps || [])}</TableCell>
                  <TableCell>
                    {pipeline.schedule_cron ? (
                      <Badge variant="outline">
                        <Clock className="mr-1 h-3 w-3" />
                        Scheduled
                      </Badge>
                    ) : (
                      <span className="text-sm text-gray-500">Manual</span>
                    )}
                  </TableCell>
                  <TableCell>
                    {pipeline.last_execution ? (
                      <div className="text-sm">
                        <div>{format(new Date(pipeline.last_execution.created_at), 'MMM d, HH:mm')}</div>
                        {renderStatus(pipeline.last_execution.status)}
                      </div>
                    ) : (
                      <span className="text-sm text-gray-500">Never run</span>
                    )}
                  </TableCell>
                  <TableCell className="text-right">
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="sm">
                          <Settings className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuLabel>Actions</DropdownMenuLabel>
                        <DropdownMenuItem
                          onClick={() => executeMutation.mutate(pipeline.id)}
                          disabled={!pipeline.is_active}
                        >
                          <Play className="mr-2 h-4 w-4" />
                          Execute Now
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          onClick={() => {
                            setSelectedPipeline(pipeline.id);
                            setShowBuilder(true);
                          }}
                        >
                          <Settings className="mr-2 h-4 w-4" />
                          Edit Configuration
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem className="text-red-600">
                          <Pause className="mr-2 h-4 w-4" />
                          {pipeline.is_active ? 'Disable' : 'Enable'} Pipeline
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}