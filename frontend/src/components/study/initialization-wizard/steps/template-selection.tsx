// ABOUTME: Template selection step for study initialization wizard
// ABOUTME: Shows dashboard templates with their data requirements

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';
import { Skeleton } from '@/components/ui/skeleton';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useToast } from '@/hooks/use-toast';
import { 
  ChevronRight, 
  Layout, 
  BarChart3, 
  Eye,
  Star,
  Loader2,
  Database,
  Info,
  FileText,
  CheckCircle2
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
  data_requirements?: any;
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
  const [templateRequirements, setTemplateRequirements] = useState<any>(null);
  const [loadingRequirements, setLoadingRequirements] = useState(false);

  useEffect(() => {
    if (studyId) {
      loadTemplates();
    }
  }, [studyId]);

  useEffect(() => {
    if (selectedTemplateId) {
      loadTemplateRequirements(selectedTemplateId);
    }
  }, [selectedTemplateId]);

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

  const loadTemplateRequirements = async (templateId: string) => {
    try {
      setLoadingRequirements(true);
      const response = await studiesApi.getTemplateRequirements(templateId);
      setTemplateRequirements(response);
    } catch (error) {
      console.error('Failed to load template requirements:', error);
      // Don't show error toast as this is optional
    } finally {
      setLoadingRequirements(false);
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
    
    const selectedTemplate = templates.find(t => t.id === selectedTemplateId);
    onComplete({ 
      templateId: selectedTemplateId,
      templateName: selectedTemplate?.name,
      dataRequirements: templateRequirements?.requirements
    });
  };

  // Extract unique required fields from template requirements
  const getUniqueRequiredFields = () => {
    if (!templateRequirements?.requirements) return [];
    
    const fieldSet = new Set<string>();
    templateRequirements.requirements.forEach((req: any) => {
      req.required_fields?.forEach((field: string) => {
        fieldSet.add(field);
      });
    });
    
    return Array.from(fieldSet);
  };

  // Map field names to common clinical data types
  const getFieldDescription = (field: string): string => {
    const fieldMap: Record<string, string> = {
      'subject_id': 'Subject/Patient identifier (USUBJID, SUBJID)',
      'site_id': 'Site identifier (SITEID, SITE)',
      'visit_date': 'Visit date (VISITDT, SVSTDTC)',
      'ae_term': 'Adverse event term (AETERM, AEDECOD)',
      'ae_severity': 'AE severity (AESEV, AESER)',
      'enrollment_date': 'Enrollment date (RFSTDTC, RANDDT)',
      'value_field': 'Numeric value (AVAL, STRESN, RESULT)',
      'date_field': 'Date field (DTC, DATE)',
      'status_field': 'Status (DSDECOD, STATUS)',
      'trend_field': 'Change/trend values (CHG, PCHG)'
    };
    
    return fieldMap[field] || field;
  };

  if (isLoadingTemplates) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-1/3" />
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-32 w-full" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium">Select Dashboard Template</h3>
        <p className="text-sm text-muted-foreground">
          Choose a template that matches your study requirements
        </p>
      </div>

      <RadioGroup value={selectedTemplateId} onValueChange={setSelectedTemplateId}>
        <div className="grid gap-4">
          {templates.map((template) => (
            <Card 
              key={template.id}
              className={cn(
                "cursor-pointer transition-all",
                selectedTemplateId === template.id && "border-primary ring-2 ring-primary ring-offset-2"
              )}
              onClick={() => setSelectedTemplateId(template.id)}
            >
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    <RadioGroupItem value={template.id} id={template.id} />
                    <div className="space-y-1">
                      <Label htmlFor={template.id} className="text-base font-medium cursor-pointer">
                        {template.name}
                        {template.is_recommended && (
                          <Badge variant="default" className="ml-2">
                            <Star className="h-3 w-3 mr-1" />
                            Recommended
                          </Badge>
                        )}
                      </Label>
                      {template.description && (
                        <CardDescription>{template.description}</CardDescription>
                      )}
                    </div>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="pt-0">
                <div className="flex gap-4 text-sm text-muted-foreground">
                  <div className="flex items-center gap-1">
                    <Layout className="h-4 w-4" />
                    {template.dashboard_count} dashboards
                  </div>
                  <div className="flex items-center gap-1">
                    <BarChart3 className="h-4 w-4" />
                    {template.widget_count} widgets
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </RadioGroup>

      {/* Show data requirements for selected template */}
      {selectedTemplateId && templateRequirements && (
        <Alert className="border-blue-200 bg-blue-50 dark:border-blue-800 dark:bg-blue-900/20">
          <Info className="h-4 w-4 text-blue-600 dark:text-blue-400" />
          <AlertDescription>
            <div className="space-y-3">
              <p className="font-medium text-blue-900 dark:text-blue-100">
                Data Requirements for This Template:
              </p>
              
              {/* Show widget requirements */}
              <div className="space-y-2">
                <p className="text-sm font-medium text-blue-800 dark:text-blue-200">
                  Widget Data Needs:
                </p>
                {templateRequirements.requirements?.map((req: any, idx: number) => (
                  <div key={idx} className="ml-4 text-sm text-blue-700 dark:text-blue-300">
                    <span className="font-medium">{req.widget_title}</span>
                    <span className="text-xs ml-2">({req.widget_type})</span>
                    {req.required_fields?.length > 0 && (
                      <div className="ml-4 mt-1 text-xs">
                        Fields: {req.required_fields.join(', ')}
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {/* Show unique required fields */}
              <div className="space-y-2 border-t pt-2">
                <p className="text-sm font-medium text-blue-800 dark:text-blue-200">
                  Required Data Fields:
                </p>
                <div className="grid gap-1">
                  {getUniqueRequiredFields().map((field, idx) => (
                    <div key={idx} className="ml-4 flex items-start gap-2 text-sm text-blue-700 dark:text-blue-300">
                      <CheckCircle2 className="h-3 w-3 mt-0.5 flex-shrink-0" />
                      <span>{getFieldDescription(field)}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="text-xs text-blue-600 dark:text-blue-400 italic mt-2">
                Make sure your data files contain these fields for optimal dashboard functionality.
              </div>
            </div>
          </AlertDescription>
        </Alert>
      )}

      {loadingRequirements && (
        <div className="flex items-center justify-center p-4">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      )}

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