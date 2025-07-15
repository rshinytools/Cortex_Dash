// ABOUTME: Study initialization progress component with real-time updates
// ABOUTME: Displays step-by-step progress with visual indicators

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { 
  CheckCircle2, 
  Circle, 
  Loader2, 
  XCircle,
  AlertCircle,
  RefreshCw,
  X
} from 'lucide-react';
import { InitializationState, InitializationStep } from '@/hooks/use-study-initialization';
import { cn } from '@/lib/utils';

interface InitializationProgressProps {
  state: InitializationState;
  isConnected: boolean;
  onRetry?: () => void;
  onCancel?: () => void;
  className?: string;
}

export function InitializationProgress({
  state,
  isConnected,
  onRetry,
  onCancel,
  className,
}: InitializationProgressProps) {
  const getStepIcon = (step: InitializationStep) => {
    switch (step.status) {
      case 'completed':
        return <CheckCircle2 className="h-5 w-5 text-green-500" />;
      case 'in_progress':
        return <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />;
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-500" />;
      default:
        return <Circle className="h-5 w-5 text-gray-400" />;
    }
  };

  const getStatusColor = (status: InitializationState['status']) => {
    switch (status) {
      case 'completed':
        return 'bg-green-500';
      case 'failed':
        return 'bg-red-500';
      case 'cancelled':
        return 'bg-yellow-500';
      case 'initializing':
      case 'pending':
        return 'bg-blue-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getStatusText = (status: InitializationState['status']) => {
    switch (status) {
      case 'not_started':
        return 'Not Started';
      case 'pending':
        return 'Queued';
      case 'initializing':
        return 'In Progress';
      case 'completed':
        return 'Completed';
      case 'failed':
        return 'Failed';
      case 'cancelled':
        return 'Cancelled';
      default:
        return status;
    }
  };

  const canRetry = state.status === 'failed' && onRetry;
  const canCancel = ['pending', 'initializing'].includes(state.status) && onCancel;

  return (
    <Card className={cn('w-full', className)}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Study Initialization</CardTitle>
            <CardDescription>
              {state.currentStep ? `Current: ${state.currentStep}` : 'Preparing to initialize'}
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Badge className={cn('text-white', getStatusColor(state.status))}>
              {getStatusText(state.status)}
            </Badge>
            {!isConnected && state.status === 'initializing' && (
              <Badge variant="outline" className="text-yellow-600 border-yellow-600">
                <AlertCircle className="h-3 w-3 mr-1" />
                Reconnecting
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Overall Progress */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Overall Progress</span>
            <span className="font-medium">{state.progress}%</span>
          </div>
          <Progress value={state.progress} className="h-2" />
        </div>

        {/* Steps */}
        <div className="space-y-4">
          {Object.entries(state.steps).map(([key, step], index) => (
            <div key={key} className="space-y-2">
              <div className="flex items-center gap-3">
                {getStepIcon(step)}
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <span className={cn(
                      'text-sm font-medium',
                      step.status === 'in_progress' && 'text-blue-600',
                      step.status === 'completed' && 'text-green-600',
                      step.status === 'failed' && 'text-red-600'
                    )}>
                      {step.name}
                    </span>
                    {step.status === 'in_progress' && (
                      <span className="text-sm text-muted-foreground">{step.progress}%</span>
                    )}
                  </div>
                  {step.details?.current_file && (
                    <p className="text-xs text-muted-foreground mt-1">
                      Processing: {step.details.current_file}
                    </p>
                  )}
                </div>
              </div>
              {step.status === 'in_progress' && (
                <Progress value={step.progress} className="h-1 ml-8" />
              )}
              {step.error && (
                <Alert variant="destructive" className="ml-8">
                  <AlertDescription className="text-xs">
                    {step.error}
                  </AlertDescription>
                </Alert>
              )}
            </div>
          ))}
        </div>

        {/* Error Message */}
        {state.error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{state.error}</AlertDescription>
          </Alert>
        )}

        {/* Actions */}
        {(canRetry || canCancel) && (
          <div className="flex justify-end gap-2 pt-4 border-t">
            {canCancel && (
              <Button
                variant="outline"
                size="sm"
                onClick={onCancel}
                disabled={!isConnected}
              >
                <X className="h-4 w-4 mr-2" />
                Cancel
              </Button>
            )}
            {canRetry && (
              <Button
                variant="default"
                size="sm"
                onClick={onRetry}
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Retry
              </Button>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}