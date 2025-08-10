// ABOUTME: Component for displaying real-time pipeline transformation progress
// ABOUTME: Shows execution status, progress bars, logs, and error handling UI

import React, { useState } from 'react';
import { 
  CheckCircle2, 
  Circle, 
  AlertCircle, 
  Clock, 
  XCircle,
  ChevronDown,
  ChevronRight,
  RefreshCw,
  StopCircle,
  FileText,
  Loader2,
  Play,
  Zap
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { cn } from '@/lib/utils';
import { 
  useTransformationProgress, 
  PipelineStatus, 
  ExecutionLog 
} from '@/hooks/use-transformation-progress';

interface TransformationProgressProps {
  studyId: string;
  executionId?: string;
  onComplete?: () => void;
  className?: string;
}

const statusConfig = {
  pending: { icon: Circle, color: 'text-gray-400', bgColor: 'bg-gray-100' },
  running: { icon: Loader2, color: 'text-blue-500', bgColor: 'bg-blue-100' },
  success: { icon: CheckCircle2, color: 'text-green-500', bgColor: 'bg-green-100' },
  failed: { icon: XCircle, color: 'text-red-500', bgColor: 'bg-red-100' },
  cancelled: { icon: StopCircle, color: 'text-orange-500', bgColor: 'bg-orange-100' },
  skipped: { icon: Circle, color: 'text-gray-400', bgColor: 'bg-gray-100' },
};

const logLevelConfig = {
  info: { color: 'text-blue-600', bgColor: 'bg-blue-50' },
  warning: { color: 'text-yellow-600', bgColor: 'bg-yellow-50' },
  error: { color: 'text-red-600', bgColor: 'bg-red-50' },
  debug: { color: 'text-gray-600', bgColor: 'bg-gray-50' },
};

export function TransformationProgress({
  studyId,
  executionId,
  onComplete,
  className,
}: TransformationProgressProps) {
  const {
    execution,
    isLoading,
    isConnected,
    retryPipeline,
    cancelExecution,
    isRetrying,
    isCancelling,
    getLogs,
  } = useTransformationProgress({ studyId, executionId });

  const [expandedPipelines, setExpandedPipelines] = useState<Set<string>>(new Set());
  const [selectedLogLevel, setSelectedLogLevel] = useState<string>('all');

  if (isLoading) {
    return (
      <Card className={className}>
        <CardContent className="flex items-center justify-center py-8">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }

  if (!execution) {
    return (
      <Card className={className}>
        <CardContent className="text-center py-8">
          <p className="text-muted-foreground">No active pipeline execution</p>
        </CardContent>
      </Card>
    );
  }

  const togglePipeline = (pipelineId: string) => {
    const newExpanded = new Set(expandedPipelines);
    if (newExpanded.has(pipelineId)) {
      newExpanded.delete(pipelineId);
    } else {
      newExpanded.add(pipelineId);
    }
    setExpandedPipelines(newExpanded);
  };

  const formatDuration = (start?: string, end?: string) => {
    if (!start) return '-';
    const startTime = new Date(start).getTime();
    const endTime = end ? new Date(end).getTime() : Date.now();
    const duration = endTime - startTime;
    
    if (duration < 1000) return `${duration}ms`;
    if (duration < 60000) return `${(duration / 1000).toFixed(1)}s`;
    return `${Math.floor(duration / 60000)}m ${((duration % 60000) / 1000).toFixed(0)}s`;
  };

  const filteredLogs = selectedLogLevel === 'all' 
    ? getLogs() 
    : getLogs(undefined, selectedLogLevel);

  const StatusIcon = statusConfig[execution.status]?.icon || Circle;
  const isRunning = execution.status === 'running';
  const canCancel = execution.status === 'pending' || execution.status === 'running';

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              Pipeline Execution
              {isConnected && (
                <Badge variant="outline" className="gap-1">
                  <Zap className="h-3 w-3" />
                  Live
                </Badge>
              )}
            </CardTitle>
            <CardDescription>
              Started {new Date(execution.started_at || '').toLocaleString()}
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            {canCancel && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => cancelExecution()}
                disabled={isCancelling}
              >
                {isCancelling ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <StopCircle className="h-4 w-4" />
                )}
                Cancel
              </Button>
            )}
            <Badge
              className={cn(
                'gap-1',
                statusConfig[execution.status]?.bgColor,
                statusConfig[execution.status]?.color
              )}
            >
              <StatusIcon 
                className={cn(
                  'h-3 w-3',
                  isRunning && 'animate-spin'
                )}
              />
              {execution.status}
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Overall Progress */}
        <div>
          <div className="flex justify-between text-sm mb-2">
            <span>Overall Progress</span>
            <span>{execution.progress}%</span>
          </div>
          <Progress value={execution.progress} className="h-2" />
        </div>

        {/* Error Alert */}
        {execution.status === 'failed' && execution.error_message && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Execution Failed</AlertTitle>
            <AlertDescription>{execution.error_message}</AlertDescription>
          </Alert>
        )}

        {/* Pipeline Steps */}
        <div className="space-y-2">
          <h4 className="text-sm font-medium">Pipeline Steps</h4>
          {execution.pipelines.map((pipeline) => {
            const PipelineIcon = statusConfig[pipeline.status]?.icon || Circle;
            const isExpanded = expandedPipelines.has(pipeline.id);
            const isPipelineRunning = pipeline.status === 'running';

            return (
              <Collapsible
                key={pipeline.id}
                open={isExpanded}
                onOpenChange={() => togglePipeline(pipeline.id)}
              >
                <div
                  className={cn(
                    'rounded-lg border p-3',
                    pipeline.status === 'failed' && 'border-red-200 bg-red-50',
                    pipeline.status === 'success' && 'border-green-200 bg-green-50',
                    pipeline.status === 'running' && 'border-blue-200 bg-blue-50'
                  )}
                >
                  <CollapsibleTrigger className="w-full">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {isExpanded ? (
                          <ChevronDown className="h-4 w-4" />
                        ) : (
                          <ChevronRight className="h-4 w-4" />
                        )}
                        <PipelineIcon
                          className={cn(
                            'h-4 w-4',
                            statusConfig[pipeline.status]?.color,
                            isPipelineRunning && 'animate-spin'
                          )}
                        />
                        <span className="font-medium">{pipeline.name}</span>
                        <Badge variant="outline" className="text-xs">
                          {pipeline.type}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-2">
                        {pipeline.status === 'failed' && (
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={(e) => {
                              e.stopPropagation();
                              retryPipeline(pipeline.id);
                            }}
                            disabled={isRetrying}
                          >
                            <RefreshCw className="h-3 w-3" />
                            Retry
                          </Button>
                        )}
                        <span className="text-sm text-muted-foreground">
                          {formatDuration(pipeline.started_at, pipeline.completed_at)}
                        </span>
                      </div>
                    </div>
                    {isPipelineRunning && (
                      <Progress value={pipeline.progress} className="h-1 mt-2" />
                    )}
                  </CollapsibleTrigger>
                  <CollapsibleContent className="pt-3">
                    <div className="space-y-3">
                      {pipeline.error_message && (
                        <Alert variant="destructive" className="py-2">
                          <AlertDescription className="text-sm">
                            {pipeline.error_message}
                          </AlertDescription>
                        </Alert>
                      )}
                      {pipeline.output_summary && (
                        <div className="grid grid-cols-3 gap-2 text-sm">
                          <div className="bg-muted rounded p-2">
                            <div className="text-muted-foreground text-xs">Rows Processed</div>
                            <div className="font-medium">
                              {pipeline.output_summary.rows_processed?.toLocaleString() || '-'}
                            </div>
                          </div>
                          <div className="bg-muted rounded p-2">
                            <div className="text-muted-foreground text-xs">Rows Output</div>
                            <div className="font-medium">
                              {pipeline.output_summary.rows_output?.toLocaleString() || '-'}
                            </div>
                          </div>
                          <div className="bg-muted rounded p-2">
                            <div className="text-muted-foreground text-xs">Execution Time</div>
                            <div className="font-medium">
                              {pipeline.output_summary.execution_time_ms 
                                ? `${(pipeline.output_summary.execution_time_ms / 1000).toFixed(2)}s`
                                : '-'}
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </CollapsibleContent>
                </div>
              </Collapsible>
            );
          })}
        </div>

        {/* Execution Logs */}
        <Tabs defaultValue="logs" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="logs">Execution Logs</TabsTrigger>
            <TabsTrigger value="summary">Summary</TabsTrigger>
          </TabsList>
          <TabsContent value="logs" className="space-y-2">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-medium">Logs</h4>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant={selectedLogLevel === 'all' ? 'default' : 'outline'}
                  onClick={() => setSelectedLogLevel('all')}
                >
                  All
                </Button>
                <Button
                  size="sm"
                  variant={selectedLogLevel === 'error' ? 'default' : 'outline'}
                  onClick={() => setSelectedLogLevel('error')}
                >
                  Errors
                </Button>
                <Button
                  size="sm"
                  variant={selectedLogLevel === 'warning' ? 'default' : 'outline'}
                  onClick={() => setSelectedLogLevel('warning')}
                >
                  Warnings
                </Button>
              </div>
            </div>
            <ScrollArea className="h-[200px] w-full rounded-md border p-2">
              <div className="space-y-1">
                {filteredLogs.length === 0 ? (
                  <p className="text-sm text-muted-foreground text-center py-4">
                    No logs to display
                  </p>
                ) : (
                  filteredLogs.map((log: ExecutionLog) => (
                    <div
                      key={log.id}
                      className={cn(
                        'flex items-start gap-2 text-xs p-2 rounded',
                        logLevelConfig[log.level]?.bgColor
                      )}
                    >
                      <span className="text-muted-foreground whitespace-nowrap">
                        {new Date(log.timestamp).toLocaleTimeString()}
                      </span>
                      <Badge
                        variant="outline"
                        className={cn(
                          'text-xs',
                          logLevelConfig[log.level]?.color
                        )}
                      >
                        {log.level}
                      </Badge>
                      <span className="flex-1">{log.message}</span>
                    </div>
                  ))
                )}
              </div>
            </ScrollArea>
          </TabsContent>
          <TabsContent value="summary" className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Total Duration</p>
                <p className="text-lg font-medium">
                  {formatDuration(execution.started_at, execution.completed_at)}
                </p>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Pipelines</p>
                <div className="flex gap-2">
                  <Badge variant="outline" className="gap-1">
                    <CheckCircle2 className="h-3 w-3 text-green-500" />
                    {execution.pipelines.filter(p => p.status === 'success').length}
                  </Badge>
                  <Badge variant="outline" className="gap-1">
                    <XCircle className="h-3 w-3 text-red-500" />
                    {execution.pipelines.filter(p => p.status === 'failed').length}
                  </Badge>
                  <Badge variant="outline" className="gap-1">
                    <Clock className="h-3 w-3 text-blue-500" />
                    {execution.pipelines.filter(p => ['pending', 'running'].includes(p.status)).length}
                  </Badge>
                </div>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}