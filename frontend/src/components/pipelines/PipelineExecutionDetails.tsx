// ABOUTME: Component for displaying pipeline execution details and logs
// ABOUTME: Shows real-time execution progress and step-by-step results

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  ArrowLeft,
  CheckCircle,
  XCircle,
  Clock,
  RefreshCw,
  AlertCircle,
  FileText,
  Download,
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
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';
import { pipelinesApi, PipelineStatus } from '@/lib/api/pipelines';

interface PipelineExecutionDetailsProps {
  executionId: string;
  onClose: () => void;
}

const STATUS_CONFIG: Record<PipelineStatus, { label: string; color: string; icon: any }> = {
  [PipelineStatus.PENDING]: { label: 'Pending', color: 'default', icon: Clock },
  [PipelineStatus.RUNNING]: { label: 'Running', color: 'default', icon: RefreshCw },
  [PipelineStatus.SUCCESS]: { label: 'Success', color: 'success', icon: CheckCircle },
  [PipelineStatus.FAILED]: { label: 'Failed', color: 'destructive', icon: XCircle },
  [PipelineStatus.CANCELLED]: { label: 'Cancelled', color: 'secondary', icon: XCircle },
  [PipelineStatus.SCHEDULED]: { label: 'Scheduled', color: 'default', icon: Clock },
};

export function PipelineExecutionDetails({
  executionId,
  onClose,
}: PipelineExecutionDetailsProps) {
  // Fetch execution details with polling for running status
  const { data: execution, isLoading } = useQuery({
    queryKey: ['execution', executionId],
    queryFn: () => pipelinesApi.getExecution(executionId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === PipelineStatus.RUNNING || status === PipelineStatus.PENDING ? 2000 : false;
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

  const calculateProgress = () => {
    if (!execution?.execution_steps) return 0;
    const completed = execution.execution_steps.filter(
      (step) => step.status === PipelineStatus.SUCCESS || step.status === PipelineStatus.FAILED
    ).length;
    return (completed / execution.execution_steps.length) * 100;
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return '-';
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${Math.floor(seconds % 60)}s`;
    return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-64" />
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <Skeleton className="h-32 w-full" />
            <Skeleton className="h-48 w-full" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!execution) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Execution Not Found</CardTitle>
        </CardHeader>
        <CardContent>
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              The execution details could not be loaded.
            </AlertDescription>
          </Alert>
          <Button className="mt-4" onClick={onClose}>
            Go Back
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button variant="ghost" size="icon" onClick={onClose}>
                <ArrowLeft className="h-4 w-4" />
              </Button>
              <div>
                <CardTitle>{execution.pipeline_name}</CardTitle>
                <CardDescription>
                  Execution ID: {executionId}
                  <Badge variant="outline" className="ml-2">
                    v{execution.pipeline_version}
                  </Badge>
                </CardDescription>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {renderStatus(execution.status)}
              {execution.output_path && (
                <Button variant="outline" size="sm">
                  <Download className="mr-2 h-4 w-4" />
                  Download Output
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-gray-500">Started</p>
              <p className="font-medium">
                {execution.started_at
                  ? format(new Date(execution.started_at), 'MMM d, yyyy HH:mm:ss')
                  : '-'}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Duration</p>
              <p className="font-medium">{formatDuration(execution.duration_seconds)}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Input Records</p>
              <p className="font-medium">
                {execution.input_records?.toLocaleString() || '-'}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Output Records</p>
              <p className="font-medium">
                {execution.output_records?.toLocaleString() || '-'}
              </p>
            </div>
          </div>

          {(execution.status === PipelineStatus.RUNNING || execution.status === PipelineStatus.PENDING) && (
            <div className="mt-4 space-y-2">
              <div className="flex justify-between text-sm">
                <span>Progress</span>
                <span>{Math.round(calculateProgress())}%</span>
              </div>
              <Progress value={calculateProgress()} />
            </div>
          )}

          {execution.error_message && (
            <Alert variant="destructive" className="mt-4">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{execution.error_message}</AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      <Tabs defaultValue="steps" className="space-y-4">
        <TabsList>
          <TabsTrigger value="steps">Execution Steps</TabsTrigger>
          <TabsTrigger value="logs">Execution Logs</TabsTrigger>
        </TabsList>

        <TabsContent value="steps">
          <Card>
            <CardHeader>
              <CardTitle>Transformation Steps</CardTitle>
              <CardDescription>
                Step-by-step execution progress and results
              </CardDescription>
            </CardHeader>
            <CardContent>
              {execution.execution_steps && execution.execution_steps.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Step</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Duration</TableHead>
                      <TableHead>Input → Output</TableHead>
                      <TableHead>Error</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {execution.execution_steps.map((step, idx) => (
                      <TableRow key={idx}>
                        <TableCell className="font-medium">{step.step_name}</TableCell>
                        <TableCell>
                          <Badge variant="outline">{step.step_type}</Badge>
                        </TableCell>
                        <TableCell>{renderStatus(step.status)}</TableCell>
                        <TableCell>{formatDuration(step.duration_seconds)}</TableCell>
                        <TableCell>
                          {step.input_records?.toLocaleString() || '-'} →{' '}
                          {step.output_records?.toLocaleString() || '-'}
                        </TableCell>
                        <TableCell>
                          {step.error_message && (
                            <span className="text-sm text-red-600">{step.error_message}</span>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  No execution steps available
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="logs">
          <Card>
            <CardHeader>
              <CardTitle>Execution Logs</CardTitle>
              <CardDescription>
                Detailed logs from the pipeline execution
              </CardDescription>
            </CardHeader>
            <CardContent>
              {execution.execution_log && execution.execution_log.length > 0 ? (
                <div className="space-y-2">
                  {execution.execution_log.map((log, idx) => (
                    <div key={idx} className="border rounded-lg p-3 text-sm">
                      <div className="flex items-center justify-between mb-1">
                        <Badge variant="outline">{log.step}</Badge>
                        <span className="text-xs text-gray-500">
                          {format(new Date(log.timestamp), 'HH:mm:ss.SSS')}
                        </span>
                      </div>
                      <p className="font-mono text-sm">{log.message}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  No execution logs available
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}