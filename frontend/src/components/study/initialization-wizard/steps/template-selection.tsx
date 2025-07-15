// ABOUTME: Template selection step for study initialization wizard
// ABOUTME: Allows users to select from available dashboard templates

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';
import { Skeleton } from '@/components/ui/skeleton';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useToast } from '@/hooks/use-toast';
import { 
  ChevronRight, 
  Layout, 
  BarChart3, 
  Eye,
  Star,
  Loader2
} from 'lucide-react';
import { studiesApi } from '@/lib/api/studies';
import { dashboardTemplatesApi } from '@/lib/api/dashboard-templates';
import { cn } from '@/lib/utils';

interface TemplateOption {
  id: string;
  name: string;
  description?: string;
  preview_url?: string;
  widget_count: number;
  dashboard_count: number;
  is_recommended: boolean;
}

interface TemplateSelectionStepProps {
  studyId: string | null;
  data: { templateId?: string };
  onComplete: (data: { 
    templateId: string;
    templateName?: string;
    dataRequirements?: any[];
  }) => void;
  isLoading?: boolean;
}

export function TemplateSelectionStep({ 
  studyId, 
  data, 
  onComplete, 
  isLoading 
}: TemplateSelectionStepProps) {
  const { toast } = useToast();
  const [templates, setTemplates] = useState<TemplateOption[]>([]);
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>(data.templateId || '');
  const [isLoadingTemplates, setIsLoadingTemplates] = useState(true);
  const [previewingTemplate, setPreviewingTemplate] = useState<string | null>(null);

  useEffect(() => {
    if (studyId) {
      loadTemplates();
    }
  }, [studyId]);

  const loadTemplates = async () => {
    if (!studyId) return;
    
    try {
      setIsLoadingTemplates(true);
      const response = await studiesApi.getAvailableTemplates(studyId);
      setTemplates(response);
    } catch (error: any) {
      toast({
        title: 'Error',
        description: 'Failed to load templates',
        variant: 'destructive',
      });
    } finally {
      setIsLoadingTemplates(false);
    }
  };

  const handleSubmit = async () => {
    if (!selectedTemplateId) {
      toast({
        title: 'Error',
        description: 'Please select a template',
        variant: 'destructive',
      });
      return;
    }
    
    // Find the selected template to pass its data requirements
    const selectedTemplate = templates.find(t => t.id === selectedTemplateId);
    if (selectedTemplate) {
      try {
        // Fetch full template details to get template_structure
        const fullTemplate = await dashboardTemplatesApi.get(selectedTemplateId);
        const dataRequirements = extractDataRequirements(fullTemplate);
        onComplete({ 
          templateId: selectedTemplateId,
          templateName: selectedTemplate.name,
          dataRequirements 
        });
      } catch (error) {
        console.error('Failed to fetch template details:', error);
        // Fallback to just passing the template ID
        onComplete({ 
          templateId: selectedTemplateId,
          templateName: selectedTemplate.name,
          dataRequirements: []
        });
      }
    } else {
      onComplete({ templateId: selectedTemplateId });
    }
  };
  
  const extractDataRequirements = (template: any) => {
    const requirements: any[] = [];
    
    // Extract from template_structure
    const templateStructure = template.template_structure || {};
    
    // Check for dashboardTemplates in template_structure
    const dashboards = templateStructure.dashboardTemplates || [];
    dashboards.forEach((dashboard: any) => {
      const widgets = dashboard.widgets || [];
      widgets.forEach((widget: any) => {
        const dataReq = widget.config?.dataRequirements;
        if (dataReq) {
          requirements.push({
            widgetId: widget.id,
            widgetTitle: widget.config?.title || 'Untitled Widget',
            dataset: dataReq.primaryDataset,
            fields: dataReq.fields || [],
            secondaryDatasets: dataReq.secondaryDatasets || []
          });
        }
      });
    });
    
    // Check for menu_structure with embedded dashboards
    const menuData = templateStructure.menu_structure || templateStructure.menu || {};
    const menuItems = menuData.items || [];
    const extractFromMenuItems = (items: any[]) => {
      items.forEach((item: any) => {
        // Check both 'dashboard' and 'dashboardConfig' keys
        const dashboardData = item.dashboard || item.dashboardConfig;
        if (dashboardData) {
          const widgets = dashboardData.widgets || [];
          widgets.forEach((widget: any) => {
            // Extract data requirements from widget instance
            const widgetInstance = widget.widgetInstance || widget;
            const widgetDef = widgetInstance.widgetDefinition;
            const dataReq = widgetDef?.data_requirements;
            const config = widgetInstance.config || {};
            
            if (dataReq) {
              requirements.push({
                widgetId: widget.widgetInstanceId || widget.id,
                widgetTitle: config.title || widgetDef?.name || 'Untitled Widget',
                dataset: dataReq.primaryDataset || 'ADSL',
                fields: dataReq.fields || [],
                secondaryDatasets: dataReq.secondaryDatasets || []
              });
            }
          });
        }
        if (item.children) {
          extractFromMenuItems(item.children);
        }
      });
    };
    extractFromMenuItems(menuItems);
    
    return requirements;
  };

  const handlePreview = (templateId: string) => {
    setPreviewingTemplate(templateId);
    // In a real implementation, this would open a preview modal/drawer
    toast({
      title: 'Preview',
      description: 'Template preview functionality coming soon',
    });
  };

  if (isLoadingTemplates) {
    return (
      <div className="space-y-6">
        <div>
          <h3 className="text-lg font-medium">Select Dashboard Template</h3>
          <p className="text-sm text-muted-foreground">
            Choose a template that best fits your study design
          </p>
        </div>
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-32 w-full" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium">Select Dashboard Template</h3>
        <p className="text-sm text-muted-foreground">
          Choose a template that best fits your study design
        </p>
      </div>

      <ScrollArea className="h-[400px] pr-4">
        <RadioGroup 
          value={selectedTemplateId} 
          onValueChange={setSelectedTemplateId}
          className="space-y-4"
        >
          {templates.map((template) => (
            <div key={template.id}>
              <Label 
                htmlFor={template.id}
                className="cursor-pointer"
              >
                <Card className={cn(
                  'transition-all hover:shadow-md',
                  selectedTemplateId === template.id && 'ring-2 ring-primary'
                )}>
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-3">
                        <RadioGroupItem 
                          value={template.id} 
                          id={template.id}
                          className="mt-1"
                        />
                        <div className="space-y-1">
                          <CardTitle className="text-base flex items-center gap-2">
                            {template.name}
                            {template.is_recommended && (
                              <Badge variant="secondary" className="text-xs">
                                <Star className="h-3 w-3 mr-1" />
                                Recommended
                              </Badge>
                            )}
                          </CardTitle>
                          {template.description && (
                            <CardDescription className="text-sm">
                              {template.description}
                            </CardDescription>
                          )}
                        </div>
                      </div>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.preventDefault();
                          handlePreview(template.id);
                        }}
                        disabled={previewingTemplate === template.id}
                      >
                        {previewingTemplate === template.id ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Eye className="h-4 w-4" />
                        )}
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      <div className="flex items-center gap-1">
                        <Layout className="h-4 w-4" />
                        <span>{template.dashboard_count} Dashboard{template.dashboard_count !== 1 ? 's' : ''}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <BarChart3 className="h-4 w-4" />
                        <span>{template.widget_count} Widget{template.widget_count !== 1 ? 's' : ''}</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </Label>
            </div>
          ))}
        </RadioGroup>
      </ScrollArea>

      <div className="flex justify-end pt-4 border-t">
        <Button 
          onClick={handleSubmit} 
          disabled={!selectedTemplateId || isLoading}
        >
          Next
          <ChevronRight className="ml-2 h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}