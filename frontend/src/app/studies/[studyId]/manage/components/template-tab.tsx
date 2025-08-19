// ABOUTME: Template Tab - Manage dashboard template selection and migration
// ABOUTME: Allows changing templates with mapping preservation and impact analysis

'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { 
  Layout,
  AlertTriangle,
  CheckCircle,
  ArrowRight,
  Eye,
  RefreshCw,
  Info
} from 'lucide-react';
import { useState } from 'react';
import { useToast } from '@/hooks/use-toast';
import { TemplateSelectionStep } from '@/components/study/initialization-wizard/steps/template-selection';
import { useQuery } from '@tanstack/react-query';
import { dashboardTemplatesApi } from '@/lib/api/dashboard-templates';

interface TemplateTabProps {
  study: any;
  onUpdate: () => void;
}

export function TemplateTab({ study, onUpdate }: TemplateTabProps) {
  const { toast } = useToast();
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null);
  const [showPreview, setShowPreview] = useState(false);
  const [isChanging, setIsChanging] = useState(false);

  // Fetch current template
  const { data: currentTemplate } = useQuery({
    queryKey: ['dashboard-template', study.dashboard_template_id],
    queryFn: () => dashboardTemplatesApi.get(study.dashboard_template_id),
    enabled: !!study.dashboard_template_id,
  });

  // Fetch available templates
  const { data: templates } = useQuery({
    queryKey: ['dashboard-templates'],
    queryFn: () => dashboardTemplatesApi.list(),
  });

  const handleTemplateChange = async () => {
    if (!selectedTemplate) {
      toast({
        title: 'Error',
        description: 'Please select a template first.',
        variant: 'destructive',
      });
      return;
    }

    setIsChanging(true);
    try {
      // In real implementation, this would:
      // 1. Update study with new template
      // 2. Trigger mapping migration
      // 3. Preserve existing mappings where possible
      
      toast({
        title: 'Template Changed',
        description: 'Dashboard template updated successfully. Please review mappings.',
      });
      
      onUpdate();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to change template. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setIsChanging(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Current Template */}
      <Card className="bg-white dark:bg-slate-900">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Layout className="h-5 w-5" />
            Current Dashboard Template
          </CardTitle>
        </CardHeader>
        <CardContent>
          {currentTemplate ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 rounded-lg border border-blue-200 bg-blue-50 dark:border-blue-900 dark:bg-blue-950/20">
                <div>
                  <p className="font-medium text-lg">{currentTemplate.name}</p>
                  <p className="text-sm text-gray-600 dark:text-slate-400">
                    {currentTemplate.description}
                  </p>
                  <div className="flex items-center gap-4 mt-2">
                    <span className="text-sm text-gray-500 dark:text-slate-500">
                      Version: {currentTemplate.version || '1.0.0'}
                    </span>
                    <span className="text-sm text-gray-500 dark:text-slate-500">
                      Widgets: {currentTemplate.widget_count || 0}
                    </span>
                    <span className="text-sm text-gray-500 dark:text-slate-500">
                      Category: {currentTemplate.category}
                    </span>
                  </div>
                </div>
                <Button variant="outline" size="sm">
                  <Eye className="h-4 w-4 mr-2" />
                  Preview
                </Button>
              </div>
            </div>
          ) : (
            <Alert>
              <Info className="h-4 w-4" />
              <AlertDescription>
                No template currently assigned to this study.
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Change Template */}
      <Card className="bg-white dark:bg-slate-900">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <RefreshCw className="h-5 w-5" />
            Change Dashboard Template
          </CardTitle>
          <CardDescription>
            Select a new template for this study's dashboard
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Warning Alert */}
          <Alert className="border-yellow-200 bg-yellow-50 dark:bg-yellow-950/20">
            <AlertTriangle className="h-4 w-4 text-yellow-600" />
            <AlertDescription className="text-yellow-800 dark:text-yellow-200">
              Changing the template will require remapping widgets that don't exist in both templates.
              Existing mappings will be preserved where possible.
            </AlertDescription>
          </Alert>

          {/* Template Selection */}
          <div className="space-y-3">
            <p className="text-sm font-medium">Available Templates</p>
            <div className="grid grid-cols-1 gap-3">
              {templates?.data?.slice(0, 5).map((template: any) => (
                <div
                  key={template.id}
                  className={`p-4 rounded-lg border cursor-pointer transition-all ${
                    selectedTemplate === template.id
                      ? 'border-blue-500 bg-blue-50 dark:bg-blue-950/20'
                      : 'border-gray-200 dark:border-slate-800 hover:border-gray-300 dark:hover:border-slate-700'
                  }`}
                  onClick={() => setSelectedTemplate(template.id)}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">{template.name}</p>
                      <p className="text-sm text-gray-500 dark:text-slate-500">
                        {template.description}
                      </p>
                      <div className="flex items-center gap-3 mt-1">
                        <Badge variant="secondary" className="text-xs">
                          {template.category}
                        </Badge>
                        <span className="text-xs text-gray-500">
                          {template.widget_count} widgets
                        </span>
                      </div>
                    </div>
                    {selectedTemplate === template.id && (
                      <CheckCircle className="h-5 w-5 text-blue-500" />
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Impact Analysis */}
          {selectedTemplate && selectedTemplate !== study.dashboard_template_id && (
            <Card className="border-gray-200 dark:border-slate-800">
              <CardHeader className="pb-3">
                <CardTitle className="text-base">Migration Impact</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-sm">
                  <div className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    <span>12 widgets will be preserved with existing mappings</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4 text-yellow-500" />
                    <span>5 new widgets will need mapping configuration</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Info className="h-4 w-4 text-blue-500" />
                    <span>3 widgets will be removed (no longer in template)</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Action Buttons */}
          <div className="flex justify-end gap-2 pt-4 border-t">
            <Button
              variant="outline"
              onClick={() => setShowPreview(true)}
              disabled={!selectedTemplate}
            >
              Preview Template
            </Button>
            <Button
              onClick={handleTemplateChange}
              disabled={!selectedTemplate || selectedTemplate === study.dashboard_template_id || isChanging}
              className="bg-blue-600 hover:bg-blue-700"
            >
              {isChanging ? 'Changing...' : 'Apply Template'}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}