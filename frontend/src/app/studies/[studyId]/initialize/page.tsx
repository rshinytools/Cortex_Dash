// ABOUTME: Study initialization wizard - simplified template-based configuration
// ABOUTME: Guides admin through template selection and data field mapping

'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { 
  ArrowLeft, 
  ArrowRight, 
  Check, 
  Layout, 
  Map,
  Eye,
  Database
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { useToast } from '@/hooks/use-toast';
import { useQuery, useMutation } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';
import { cn } from '@/lib/utils';

// Import step components
import { TemplateSelectionStep } from './steps/template-selection-step';
import { DataSourceStep } from './steps/data-source-step';
import { DataMappingStep } from './steps/data-mapping-step';
import { ReviewStep } from './steps/review-step';

interface WizardStep {
  id: string;
  title: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  component: React.ComponentType<any>;
}

const steps: WizardStep[] = [
  {
    id: 'template',
    title: 'Select Template',
    description: 'Choose a dashboard template for your study',
    icon: Layout,
    component: TemplateSelectionStep,
  },
  {
    id: 'datasource',
    title: 'Configure Data Source',
    description: 'Set up how data will be imported into your study',
    icon: Database,
    component: DataSourceStep,
  },
  {
    id: 'mapping',
    title: 'Map Data Fields',
    description: 'Map your study data fields to template requirements',
    icon: Map,
    component: DataMappingStep,
  },
  {
    id: 'review',
    title: 'Review & Activate',
    description: 'Review configuration and activate the study',
    icon: Eye,
    component: ReviewStep,
  },
];

export default function StudyInitializePage() {
  const params = useParams();
  const router = useRouter();
  const { toast } = useToast();
  const studyId = params.studyId as string;
  const [currentStep, setCurrentStep] = useState(0);
  const [wizardData, setWizardData] = useState<Record<string, any>>({});

  const { data: study, isLoading } = useQuery({
    queryKey: ['study', studyId],
    queryFn: async () => {
      const response = await apiClient.get(`/studies/${studyId}`);
      return response.data;
    },
  });

  const saveConfiguration = useMutation({
    mutationFn: async (data: any) => {
      const response = await apiClient.post(`/studies/${studyId}/apply-template`, data);
      return response.data;
    },
    onSuccess: () => {
      toast({
        title: 'Study configuration saved',
        description: 'The dashboard template has been applied successfully.',
      });
      router.push(`/studies/${studyId}/dashboard`);
    },
    onError: (error) => {
      toast({
        title: 'Failed to apply template',
        description: error instanceof Error ? error.message : 'An error occurred',
        variant: 'destructive',
      });
    },
  });

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleStepData = (stepId: string, data: any) => {
    setWizardData({ ...wizardData, [stepId]: data });
  };

  const handleFinish = () => {
    // Validate that template and mappings are configured
    const templateId = wizardData['template']?.templateId;
    const fieldMappings = wizardData['mapping']?.fieldMappings || {};
    
    if (!templateId) {
      toast({
        title: 'Template required',
        description: 'Please select a dashboard template before completing setup.',
        variant: 'destructive',
      });
      setCurrentStep(0);
      return;
    }
    
    if (Object.keys(fieldMappings).length === 0) {
      toast({
        title: 'Field mappings required',
        description: 'Please map at least the required fields before completing setup.',
        variant: 'destructive',
      });
      setCurrentStep(1);
      return;
    }

    // Apply template with field mappings
    const configuration = {
      dashboard_template_id: templateId,
      field_mappings: fieldMappings,
      config: {
        study_id: studyId,
        status: 'active',
      },
    };
    
    saveConfiguration.mutate(configuration);
  };

  if (isLoading) {
    return <div>Loading study information...</div>;
  }

  const CurrentStepComponent = steps[currentStep].component;
  const progress = ((currentStep + 1) / steps.length) * 100;

  return (
    <div className="container mx-auto py-6">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => router.push('/studies')}
            className="mb-4"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Studies
          </Button>
          <h1 className="text-3xl font-bold">Initialize Study: {study?.name}</h1>
          <p className="text-muted-foreground mt-2">
            Configure your study step by step to get started with data collection and analysis
          </p>
        </div>

        {/* Progress Bar */}
        <div className="mb-8">
          <Progress value={progress} className="h-2" />
          <div className="flex justify-between mt-4">
            {steps.map((step, index) => {
              const Icon = step.icon;
              const isActive = index === currentStep;
              const isCompleted = index < currentStep;
              
              return (
                <div
                  key={step.id}
                  className={cn(
                    'flex flex-col items-center cursor-pointer',
                    isActive && 'text-primary',
                    isCompleted && 'text-green-600',
                    !isActive && !isCompleted && 'text-muted-foreground'
                  )}
                  onClick={() => isCompleted && setCurrentStep(index)}
                >
                  <div
                    className={cn(
                      'w-10 h-10 rounded-full flex items-center justify-center mb-2',
                      isActive && 'bg-primary text-primary-foreground',
                      isCompleted && 'bg-green-600 text-white',
                      !isActive && !isCompleted && 'bg-muted'
                    )}
                  >
                    {isCompleted ? (
                      <Check className="h-5 w-5" />
                    ) : (
                      <Icon className="h-5 w-5" />
                    )}
                  </div>
                  <span className="text-sm font-medium">{step.title}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Step Content */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>{steps[currentStep].title}</CardTitle>
            <CardDescription>{steps[currentStep].description}</CardDescription>
          </CardHeader>
          <CardContent>
            <CurrentStepComponent
              studyId={studyId}
              data={{
                ...(wizardData[steps[currentStep].id] || {}),
                // Pass template data to mapping step
                ...(steps[currentStep].id === 'mapping' && wizardData['template'] ? {
                  templateId: wizardData['template'].templateId,
                  templateDetails: wizardData['template'].templateDetails,
                } : {}),
                // Pass datasource data to mapping step
                ...(steps[currentStep].id === 'mapping' && wizardData['datasource'] ? {
                  dataSources: wizardData['datasource'].dataSources,
                } : {}),
              }}
              onDataChange={(data: any) => handleStepData(steps[currentStep].id, data)}
            />
          </CardContent>
        </Card>

        {/* Navigation Buttons */}
        <div className="flex justify-between">
          <Button
            variant="outline"
            onClick={handlePrevious}
            disabled={currentStep === 0}
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Previous
          </Button>
          
          {currentStep === steps.length - 1 ? (
            <Button onClick={handleFinish} disabled={saveConfiguration.isPending}>
              {saveConfiguration.isPending ? 'Saving...' : 'Complete Setup'}
              <Check className="ml-2 h-4 w-4" />
            </Button>
          ) : (
            <Button onClick={handleNext}>
              Next
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}