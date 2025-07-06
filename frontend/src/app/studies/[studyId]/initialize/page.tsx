// ABOUTME: Study initialization wizard - multi-step configuration process
// ABOUTME: Guides admin through data sources, pipelines, and dashboard setup

'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { 
  ArrowLeft, 
  ArrowRight, 
  Check, 
  Database, 
  GitBranch, 
  Layout, 
  BarChart3,
  Save
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { useToast } from '@/hooks/use-toast';
import { useQuery, useMutation } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';
import { cn } from '@/lib/utils';

// Import step components
import { DataSourceStep } from './steps/data-source-step';
import { PipelineStep } from './steps/pipeline-step';
import { DashboardStep } from './steps/dashboard-step';
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
    id: 'data-source',
    title: 'Data Sources',
    description: 'Configure how data will be imported into the study',
    icon: Database,
    component: DataSourceStep,
  },
  {
    id: 'pipeline',
    title: 'Data Pipeline',
    description: 'Set up data processing and transformation rules',
    icon: GitBranch,
    component: PipelineStep,
  },
  {
    id: 'dashboard',
    title: 'Dashboard Configuration',
    description: 'Design the study dashboard layout and widgets',
    icon: Layout,
    component: DashboardStep,
  },
  {
    id: 'review',
    title: 'Review & Activate',
    description: 'Review configuration and activate the study',
    icon: Check,
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
      const response = await apiClient.put(`/studies/${studyId}/configuration`, data);
      return response.data;
    },
    onSuccess: () => {
      toast({
        title: 'Study configuration saved',
        description: 'The study has been successfully configured and activated.',
      });
      router.push(`/studies/${studyId}/dashboard`);
    },
    onError: (error) => {
      toast({
        title: 'Failed to save configuration',
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
    // Validate that at least one data source is configured
    const dataSources = wizardData['data-source']?.dataSources || [];
    if (dataSources.length === 0) {
      toast({
        title: 'Data source required',
        description: 'Please configure at least one data source before completing setup.',
        variant: 'destructive',
      });
      setCurrentStep(0); // Go back to data source step
      return;
    }

    // Combine all wizard data and save
    const configuration = {
      config: {
        data_sources: dataSources,
        study_id: studyId,
        status: 'active',
      },
      pipeline_config: wizardData['pipeline'] || {},
      dashboard_config: wizardData['dashboard'] || {},
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
              data={wizardData[steps[currentStep].id] || {}}
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