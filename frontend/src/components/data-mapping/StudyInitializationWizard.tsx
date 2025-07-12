// ABOUTME: Study initialization wizard for configuring data mappings
// ABOUTME: Multi-step wizard to guide users through data setup and widget configuration

import React, { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Checkbox } from '@/components/ui/checkbox';
import {
  ChevronLeft,
  ChevronRight,
  CheckCircle,
  Upload,
  Database,
  GitBranch,
  MapPin,
  Settings,
  AlertCircle,
  FileText,
} from 'lucide-react';
import { mappingApi } from '@/lib/api/mapping';
import { widgetsApi } from '@/lib/api/widgets';
import { dataUploadsApi } from '@/lib/api/data-uploads';
import { dashboardTemplatesApi } from '@/lib/api/dashboard-templates';
import { FieldMappingBuilder } from './FieldMappingBuilder';
import { MappingPreview } from './MappingPreview';
import { DataSourceUpload } from '../data-sources/DataSourceUpload';
import { cn } from '@/lib/utils';

interface StudyInitializationWizardProps {
  studyId: string;
  templateId?: string;
  onComplete?: () => void;
}

enum WizardStep {
  UPLOAD_DATA = 0,
  ANALYZE_DATA = 1,
  SELECT_WIDGETS = 2,
  CONFIGURE_MAPPINGS = 3,
  PREVIEW_VALIDATE = 4,
  FINALIZE = 5,
}

const STEP_TITLES = {
  [WizardStep.UPLOAD_DATA]: 'Upload Data',
  [WizardStep.ANALYZE_DATA]: 'Analyze Data',
  [WizardStep.SELECT_WIDGETS]: 'Select Widgets',
  [WizardStep.CONFIGURE_MAPPINGS]: 'Configure Mappings',
  [WizardStep.PREVIEW_VALIDATE]: 'Preview & Validate',
  [WizardStep.FINALIZE]: 'Finalize Setup',
};

const STEP_DESCRIPTIONS = {
  [WizardStep.UPLOAD_DATA]: 'Upload your clinical data files',
  [WizardStep.ANALYZE_DATA]: 'Analyzing data structure and content',
  [WizardStep.SELECT_WIDGETS]: 'Choose widgets to display on dashboards',
  [WizardStep.CONFIGURE_MAPPINGS]: 'Map data fields to widget requirements',
  [WizardStep.PREVIEW_VALIDATE]: 'Review and validate your configuration',
  [WizardStep.FINALIZE]: 'Complete study initialization',
};

export function StudyInitializationWizard({
  studyId,
  templateId,
  onComplete,
}: StudyInitializationWizardProps) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [currentStep, setCurrentStep] = useState(WizardStep.UPLOAD_DATA);
  const [uploadedDatasets, setUploadedDatasets] = useState<string[]>([]);
  const [selectedWidgets, setSelectedWidgets] = useState<string[]>([]);
  const [widgetMappings, setWidgetMappings] = useState<Record<string, any>>({});
  const [validationResults, setValidationResults] = useState<Record<string, any>>({});
  const [showUploadDialog, setShowUploadDialog] = useState(false);

  // Fetch template widgets if template is provided
  const { data: template } = useQuery({
    queryKey: ['dashboard-template', templateId],
    queryFn: () => dashboardTemplatesApi.get(templateId!),
    enabled: !!templateId,
  });

  // Fetch available widgets
  const { data: availableWidgets } = useQuery({
    queryKey: ['widgets'],
    queryFn: () => widgetsApi.getWidgets(),
  });

  // Initialize study data mutation
  const initializeDataMutation = useMutation({
    mutationFn: (uploadIds: string[]) =>
      mappingApi.initializeStudyData({
        study_id: studyId,
        dataset_uploads: uploadIds,
        auto_detect_mappings: true,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['study-data-config', studyId] });
      setCurrentStep(WizardStep.SELECT_WIDGETS);
    },
  });

  // Validate all mappings mutation
  const validateAllMutation = useMutation({
    mutationFn: () => mappingApi.validateAllMappings(studyId),
    onSuccess: (results) => {
      setValidationResults(results);
      setCurrentStep(WizardStep.FINALIZE);
    },
  });

  const handleDataUploadComplete = (uploadIds: string[]) => {
    setUploadedDatasets(uploadIds);
    setCurrentStep(WizardStep.ANALYZE_DATA);
    // Auto-start analysis
    initializeDataMutation.mutate(uploadIds);
  };

  const handleWidgetSelection = (widgetId: string, selected: boolean) => {
    if (selected) {
      setSelectedWidgets([...selectedWidgets, widgetId]);
    } else {
      setSelectedWidgets(selectedWidgets.filter((id) => id !== widgetId));
    }
  };

  const handleMappingComplete = (widgetId: string, mapping: any) => {
    setWidgetMappings({
      ...widgetMappings,
      [widgetId]: mapping,
    });
  };

  const handleValidationResult = (widgetId: string, result: any) => {
    setValidationResults({
      ...validationResults,
      [widgetId]: result,
    });
  };

  const handleFinalize = async () => {
    // Mark study as initialized
    // This would typically update a study status in the backend
    onComplete?.();
    router.push(`/studies/${studyId}/dashboard`);
  };

  const canProceed = () => {
    switch (currentStep) {
      case WizardStep.UPLOAD_DATA:
        return uploadedDatasets.length > 0;
      case WizardStep.ANALYZE_DATA:
        return !initializeDataMutation.isPending;
      case WizardStep.SELECT_WIDGETS:
        return selectedWidgets.length > 0;
      case WizardStep.CONFIGURE_MAPPINGS:
        return Object.keys(widgetMappings).length === selectedWidgets.length;
      case WizardStep.PREVIEW_VALIDATE:
        return Object.values(validationResults).every((result: any) => result?.is_valid);
      case WizardStep.FINALIZE:
        return true;
      default:
        return false;
    }
  };

  const getProgress = () => {
    return ((currentStep + 1) / Object.keys(WizardStep).length) * 100;
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case WizardStep.UPLOAD_DATA:
        return (
          <Card>
            <CardHeader>
              <CardTitle>Upload Clinical Data</CardTitle>
              <CardDescription>
                Upload your study data files in supported formats (CSV, SAS7BDAT, XPT, XLSX)
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <Button onClick={() => setShowUploadDialog(true)}>
                  <Upload className="mr-2 h-4 w-4" />
                  Upload Data Files
                </Button>
                {uploadedDatasets.length > 0 && (
                  <Alert>
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <AlertDescription>
                      {uploadedDatasets.length} file{uploadedDatasets.length > 1 ? 's' : ''} uploaded successfully
                    </AlertDescription>
                  </Alert>
                )}
              </div>
              <DataSourceUpload
                studyId={studyId}
                open={showUploadDialog}
                onOpenChange={setShowUploadDialog}
                onUploadComplete={() => {
                  // Fetch uploaded datasets
                  dataUploadsApi.listUploads(studyId).then((response) => {
                    const uploadIds = response.data.map((u: any) => u.id);
                    handleDataUploadComplete(uploadIds);
                  });
                }}
              />
            </CardContent>
          </Card>
        );

      case WizardStep.ANALYZE_DATA:
        return (
          <Card>
            <CardHeader>
              <CardTitle>Analyzing Data</CardTitle>
              <CardDescription>
                Examining data structure and preparing for configuration
              </CardDescription>
            </CardHeader>
            <CardContent>
              {initializeDataMutation.isPending ? (
                <div className="flex flex-col items-center justify-center py-12 space-y-4">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
                  <p className="text-sm text-gray-500">Analyzing uploaded datasets...</p>
                </div>
              ) : initializeDataMutation.isSuccess ? (
                <Alert>
                  <CheckCircle className="h-4 w-4 text-green-600" />
                  <AlertDescription>
                    Data analysis complete! Found{' '}
                    {Object.keys(initializeDataMutation.data?.dataset_schemas || {}).length}{' '}
                    datasets ready for configuration.
                  </AlertDescription>
                </Alert>
              ) : initializeDataMutation.isError ? (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    Error analyzing data. Please try again or contact support.
                  </AlertDescription>
                </Alert>
              ) : null}
            </CardContent>
          </Card>
        );

      case WizardStep.SELECT_WIDGETS:
        return (
          <Card>
            <CardHeader>
              <CardTitle>Select Dashboard Widgets</CardTitle>
              <CardDescription>
                Choose which widgets to display on your study dashboard
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {template ? (
                  <Alert>
                    <AlertDescription>
                      Using widgets from template: {template.name}
                    </AlertDescription>
                  </Alert>
                ) : null}
                
                <div className="grid grid-cols-2 gap-4">
                  {(template?.widgets || availableWidgets?.items || []).map((widget: any) => (
                    <div
                      key={widget.id}
                      className="border rounded-lg p-4 hover:bg-gray-50"
                    >
                      <div className="flex items-start space-x-3">
                        <Checkbox
                          checked={selectedWidgets.includes(widget.id)}
                          onCheckedChange={(checked) =>
                            handleWidgetSelection(widget.id, checked as boolean)
                          }
                        />
                        <div className="flex-1">
                          <h4 className="font-medium">{widget.name}</h4>
                          <p className="text-sm text-gray-500">{widget.description}</p>
                          <Badge variant="outline" className="mt-2">
                            {widget.type}
                          </Badge>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        );

      case WizardStep.CONFIGURE_MAPPINGS:
        return (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Configure Widget Data Mappings</CardTitle>
                <CardDescription>
                  Map your data fields to each widget's requirements
                </CardDescription>
              </CardHeader>
            </Card>
            
            {selectedWidgets.map((widgetId, index) => (
              <div key={widgetId} className="space-y-4">
                <div className="flex items-center gap-2">
                  <Badge>{index + 1} of {selectedWidgets.length}</Badge>
                  <span className="text-sm text-gray-500">Widget Configuration</span>
                </div>
                <FieldMappingBuilder
                  studyId={studyId}
                  widgetId={widgetId}
                  onComplete={() => {
                    handleMappingComplete(widgetId, { configured: true });
                    if (index < selectedWidgets.length - 1) {
                      // Auto-scroll to next widget
                      window.scrollTo({ top: 0, behavior: 'smooth' });
                    }
                  }}
                />
              </div>
            ))}
          </div>
        );

      case WizardStep.PREVIEW_VALIDATE:
        return (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Preview and Validate Configuration</CardTitle>
                <CardDescription>
                  Review your widget configurations and validate data mappings
                </CardDescription>
              </CardHeader>
            </Card>
            
            {selectedWidgets.map((widgetId) => (
              <MappingPreview
                key={widgetId}
                studyId={studyId}
                widgetId={widgetId}
                mappingConfig={widgetMappings[widgetId]}
                onValidation={(result) => handleValidationResult(widgetId, result)}
              />
            ))}
          </div>
        );

      case WizardStep.FINALIZE:
        return (
          <Card>
            <CardHeader>
              <CardTitle>Study Initialization Complete</CardTitle>
              <CardDescription>
                Your study is now configured and ready to use
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                <Alert>
                  <CheckCircle className="h-4 w-4 text-green-600" />
                  <AlertDescription>
                    All configurations have been validated successfully!
                  </AlertDescription>
                </Alert>

                <div className="space-y-4">
                  <h3 className="font-medium">Configuration Summary</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="border rounded-lg p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <Database className="h-4 w-4 text-gray-500" />
                        <span className="text-sm font-medium">Datasets</span>
                      </div>
                      <p className="text-2xl font-bold">{uploadedDatasets.length}</p>
                    </div>
                    <div className="border rounded-lg p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <Settings className="h-4 w-4 text-gray-500" />
                        <span className="text-sm font-medium">Widgets</span>
                      </div>
                      <p className="text-2xl font-bold">{selectedWidgets.length}</p>
                    </div>
                  </div>
                </div>

                <div className="pt-4">
                  <Button onClick={handleFinalize} className="w-full">
                    Go to Dashboard
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        );

      default:
        return null;
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Progress Bar */}
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span>{STEP_TITLES[currentStep]}</span>
          <span>Step {currentStep + 1} of {Object.keys(WizardStep).length / 2}</span>
        </div>
        <Progress value={getProgress()} />
      </div>

      {/* Step Indicators */}
      <div className="flex justify-between">
        {Object.values(WizardStep)
          .filter((v) => typeof v === 'number')
          .map((step) => (
            <div
              key={step}
              className={cn(
                'flex items-center gap-2',
                step < currentStep && 'text-green-600',
                step === currentStep && 'text-blue-600',
                step > currentStep && 'text-gray-400'
              )}
            >
              <div
                className={cn(
                  'w-8 h-8 rounded-full flex items-center justify-center border-2',
                  step < currentStep && 'bg-green-600 border-green-600 text-white',
                  step === currentStep && 'bg-blue-600 border-blue-600 text-white',
                  step > currentStep && 'bg-white border-gray-300'
                )}
              >
                {step < currentStep ? (
                  <CheckCircle className="h-5 w-5" />
                ) : (
                  <span>{(step as number) + 1}</span>
                )}
              </div>
              <span className="hidden md:block text-sm">
                {STEP_TITLES[step as WizardStep]}
              </span>
            </div>
          ))}
      </div>

      {/* Content */}
      {renderStepContent()}

      {/* Navigation */}
      <div className="flex justify-between">
        <Button
          variant="outline"
          onClick={() => setCurrentStep(Math.max(0, currentStep - 1))}
          disabled={currentStep === 0}
        >
          <ChevronLeft className="h-4 w-4 mr-1" />
          Previous
        </Button>

        {currentStep < WizardStep.FINALIZE ? (
          <Button
            onClick={() => {
              if (currentStep === WizardStep.PREVIEW_VALIDATE) {
                validateAllMutation.mutate();
              } else {
                setCurrentStep(currentStep + 1);
              }
            }}
            disabled={!canProceed()}
          >
            Next
            <ChevronRight className="h-4 w-4 ml-1" />
          </Button>
        ) : null}
      </div>
    </div>
  );
}