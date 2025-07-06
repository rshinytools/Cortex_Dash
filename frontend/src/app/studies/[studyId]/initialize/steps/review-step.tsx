// ABOUTME: Review step in study initialization wizard
// ABOUTME: Shows summary of all configuration before activation

'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Check, Database, GitBranch, Layout } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface ReviewStepProps {
  studyId: string;
  data: any;
  onDataChange: (data: any) => void;
}

export function ReviewStep({ studyId, data, onDataChange }: ReviewStepProps) {
  const dataSources = data['data-source']?.dataSources || [];
  const pipelineSteps = data['pipeline']?.steps || [];
  const dashboardWidgets = data['dashboard']?.widgets || [];

  return (
    <div className="space-y-6">
      <Alert>
        <AlertDescription>
          Please review your study configuration before activation. Once activated, the study will be ready to receive and process data.
        </AlertDescription>
      </Alert>

      {/* Data Sources Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            Data Sources
          </CardTitle>
        </CardHeader>
        <CardContent>
          {dataSources.length === 0 ? (
            <p className="text-muted-foreground">No data sources configured</p>
          ) : (
            <div className="space-y-2">
              {dataSources.map((source: any, index: number) => (
                <div key={index} className="flex items-center justify-between">
                  <div>
                    <span className="font-medium">{source.name || 'Unnamed Source'}</span>
                    <Badge variant="outline" className="ml-2">{source.type}</Badge>
                  </div>
                  {source.config.sync_schedule && (
                    <span className="text-sm text-muted-foreground">
                      Auto-sync: {source.config.sync_schedule}
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Pipeline Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <GitBranch className="h-5 w-5" />
            Data Pipeline
          </CardTitle>
        </CardHeader>
        <CardContent>
          {pipelineSteps.length === 0 ? (
            <p className="text-muted-foreground">No pipeline steps configured</p>
          ) : (
            <div className="space-y-2">
              <p className="text-sm text-muted-foreground mb-2">
                {pipelineSteps.length} transformation step(s) configured
              </p>
              {pipelineSteps.map((step: any, index: number) => (
                <div key={index} className="flex items-center gap-2">
                  <span className="text-sm font-mono bg-muted px-2 py-1 rounded">
                    {index + 1}
                  </span>
                  <span>{step.name || 'Unnamed Step'}</span>
                  <Badge variant="secondary">{step.type}</Badge>
                </div>
              ))}
              {data['pipeline']?.schedule && (
                <p className="text-sm text-muted-foreground mt-2">
                  Schedule: {data['pipeline'].schedule}
                </p>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Dashboard Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Layout className="h-5 w-5" />
            Dashboard Configuration
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span>Layout Type</span>
              <Badge>{data['dashboard']?.layout || 'Not selected'}</Badge>
            </div>
            <div className="flex items-center justify-between">
              <span>Number of Widgets</span>
              <span className="font-medium">{dashboardWidgets.length}</span>
            </div>
            {dashboardWidgets.length > 0 && (
              <div className="mt-2 space-y-1">
                {dashboardWidgets.map((widget: any, index: number) => (
                  <div key={index} className="text-sm text-muted-foreground">
                    • {widget.title} ({widget.type})
                  </div>
                ))}
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Activation Summary */}
      <Card className="border-green-200 bg-green-50 dark:bg-green-950">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-green-800 dark:text-green-200">
            <Check className="h-5 w-5" />
            Ready to Activate
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-green-700 dark:text-green-300">
            Your study configuration is complete. Click "Complete Setup" to activate the study and make it available for data collection and analysis.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}