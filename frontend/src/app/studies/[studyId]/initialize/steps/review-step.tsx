// ABOUTME: Review step for study initialization wizard
// ABOUTME: Shows summary of template selection and field mappings before activation

'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { CheckCircle, AlertCircle, Layout, Map, Database } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ReviewStepProps {
  studyId: string;
  data: {
    template?: {
      templateId?: string;
      templateDetails?: any;
    };
    mapping?: {
      fieldMappings?: Record<string, string>;
    };
  };
  onDataChange: (data: any) => void;
}

export function ReviewStep({ studyId, data, onDataChange }: ReviewStepProps) {
  const templateData = data.template || {};
  const mappingData = data.mapping || {};
  
  const isTemplateConfigured = !!templateData.templateId;
  const isMappingConfigured = mappingData.fieldMappings && Object.keys(mappingData.fieldMappings).length > 0;
  const isReadyToActivate = isTemplateConfigured && isMappingConfigured;

  // Count mapped fields
  const mappedFieldsCount = Object.keys(mappingData.fieldMappings || {}).length;

  return (
    <div className="space-y-6">
      {/* Overall status */}
      <Alert className={isReadyToActivate ? 'border-green-500' : 'border-yellow-500'}>
        {isReadyToActivate ? (
          <CheckCircle className="h-4 w-4 text-green-500" />
        ) : (
          <AlertCircle className="h-4 w-4 text-yellow-500" />
        )}
        <AlertDescription>
          {isReadyToActivate ? (
            'Your study is ready to be activated! Review the configuration below and click "Complete Setup" to proceed.'
          ) : (
            'Please complete all required steps before activating the study.'
          )}
        </AlertDescription>
      </Alert>

      {/* Template selection summary */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span className="flex items-center gap-2">
              <Layout className="h-5 w-5" />
              Dashboard Template
            </span>
            {isTemplateConfigured ? (
              <CheckCircle className="h-5 w-5 text-green-500" />
            ) : (
              <AlertCircle className="h-5 w-5 text-yellow-500" />
            )}
          </CardTitle>
          <CardDescription>
            Selected dashboard template for this study
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isTemplateConfigured ? (
            <div className="space-y-3">
              <div>
                <p className="font-medium text-lg">{templateData.templateDetails?.name}</p>
                <p className="text-sm text-muted-foreground">{templateData.templateDetails?.description}</p>
              </div>
              <div className="flex gap-4 text-sm">
                <div>
                  <span className="text-muted-foreground">Category:</span>{' '}
                  <Badge variant="secondary" className="capitalize">
                    {templateData.templateDetails?.category}
                  </Badge>
                </div>
                <div>
                  <span className="text-muted-foreground">Version:</span>{' '}
                  <span className="font-medium">v{templateData.templateDetails?.version}</span>
                </div>
              </div>
              <Separator />
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-muted-foreground">Dashboards:</span>{' '}
                  <span className="font-medium">{templateData.templateDetails?.dashboard_count}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">Widgets:</span>{' '}
                  <span className="font-medium">{templateData.templateDetails?.widget_count}</span>
                </div>
              </div>
            </div>
          ) : (
            <p className="text-muted-foreground">No template selected</p>
          )}
        </CardContent>
      </Card>

      {/* Field mappings summary */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span className="flex items-center gap-2">
              <Map className="h-5 w-5" />
              Field Mappings
            </span>
            {isMappingConfigured ? (
              <CheckCircle className="h-5 w-5 text-green-500" />
            ) : (
              <AlertCircle className="h-5 w-5 text-yellow-500" />
            )}
          </CardTitle>
          <CardDescription>
            Data field mappings for the selected template
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isMappingConfigured ? (
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <Database className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm">
                  <strong>{mappedFieldsCount}</strong> fields mapped successfully
                </span>
              </div>
              
              {/* Show first few mappings as examples */}
              <div className="space-y-2">
                <p className="text-sm font-medium">Sample mappings:</p>
                <div className="space-y-1">
                  {Object.entries(mappingData.fieldMappings || {})
                    .slice(0, 5)
                    .map(([templateField, studyField]) => (
                      <div key={templateField} className="text-sm flex items-center gap-2">
                        <code className="bg-muted px-2 py-0.5 rounded text-xs">
                          {templateField}
                        </code>
                        <span className="text-muted-foreground">→</span>
                        <code className="bg-muted px-2 py-0.5 rounded text-xs">
                          {studyField}
                        </code>
                      </div>
                    ))}
                  {mappedFieldsCount > 5 && (
                    <p className="text-sm text-muted-foreground">
                      ...and {mappedFieldsCount - 5} more mappings
                    </p>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <p className="text-muted-foreground">No field mappings configured</p>
          )}
        </CardContent>
      </Card>

      {/* Next steps */}
      <Card>
        <CardHeader>
          <CardTitle>Next Steps</CardTitle>
          <CardDescription>
            What happens after you complete the setup
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2 text-sm">
            <li className="flex items-start gap-2">
              <span className="text-primary mt-0.5">1.</span>
              <span>The selected dashboard template will be applied to your study</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-primary mt-0.5">2.</span>
              <span>Field mappings will be configured to connect your data</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-primary mt-0.5">3.</span>
              <span>You'll be redirected to the study dashboard</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-primary mt-0.5">4.</span>
              <span>You can start uploading data and viewing insights immediately</span>
            </li>
          </ul>
        </CardContent>
      </Card>

      {!isReadyToActivate && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Please complete the following before activating:
            <ul className="list-disc list-inside mt-2">
              {!isTemplateConfigured && <li>Select a dashboard template</li>}
              {!isMappingConfigured && <li>Configure field mappings</li>}
            </ul>
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
}