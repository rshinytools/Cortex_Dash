// ABOUTME: Main initialization wizard component
// ABOUTME: Orchestrates the step-by-step study initialization flow

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { useToast } from '@/hooks/use-toast';
import { ChevronLeft, ChevronRight, Check } from 'lucide-react';
import { studiesApi } from '@/lib/api/studies';
import { cn } from '@/lib/utils';

// Import wizard steps
import { BasicInfoStep } from './steps/basic-info';
import { TemplateSelectionStep } from './steps/template-selection';
import { DataUploadStep } from './steps/data-upload';
import { ReviewMappingsStep } from './steps/review-mappings';

export interface WizardStep {
  id: string;
  name: string;
  component: React.ComponentType<any>;
}

const wizardSteps: WizardStep[] = [
  {
    id: 'basic_info',
    name: 'Basic Information',
    component: BasicInfoStep,
  },
  {
    id: 'template_selection',
    name: 'Select Template',
    component: TemplateSelectionStep,
  },
  {
    id: 'data_upload',
    name: 'Upload Data',
    component: DataUploadStep,
  },
  {
    id: 'review_mappings',
    name: 'Review & Activate',
    component: ReviewMappingsStep,
  },
];

interface InitializationWizardProps {
  studyId?: string;
  initialStep?: number;
  initialData?: any;
  organizationId?: string;
  onComplete?: (studyId: string) => void;
  onCancel?: () => void;
}

export function InitializationWizard({
  studyId: existingStudyId,
  initialStep = 0,
  initialData,
  organizationId,
  onComplete,
  onCancel,
}: InitializationWizardProps) {
  const router = useRouter();
  const { toast } = useToast();
  const [currentStep, setCurrentStep] = useState(initialStep);
  const [studyId, setStudyId] = useState<string | null>(existingStudyId || null);
  const [wizardData, setWizardData] = useState<any>(initialData || {});
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingStudy, setIsLoadingStudy] = useState(!!existingStudyId);
  const [completedSteps, setCompletedSteps] = useState<Set<string>>(() => {
    // Mark previous steps as completed if resuming
    const completed = new Set<string>();
    if (initialStep > 0) {
      for (let i = 0; i < initialStep; i++) {
        completed.add(wizardSteps[i].id);
      }
    }
    return completed;
  });

  // Load study data if resuming
  useEffect(() => {
    if (existingStudyId && !initialData) {
      const loadStudyData = async () => {
        try {
          const study = await studiesApi.getStudy(existingStudyId);
          const wizardState = await studiesApi.getWizardState(existingStudyId);
          
          // Populate wizard data from study
          setWizardData({
            basic_info: {
              name: study.name,
              protocol_number: study.protocol_number,
              description: study.description,
              phase: study.phase,
              therapeutic_area: study.therapeutic_area,
              indication: study.indication,
            },
            template_selection: {
              templateId: study.dashboard_template_id,
            },
            // Add other step data as needed
          });
          
          // Update current step from wizard state
          if (wizardState.current_step) {
            setCurrentStep(wizardState.current_step - 1);
          }
        } catch (error) {
          console.error('Failed to load study data:', error);
          toast({
            title: 'Error',
            description: 'Failed to load draft study data',
            variant: 'destructive',
          });
        } finally {
          setIsLoadingStudy(false);
        }
      };
      
      loadStudyData();
    } else {
      setIsLoadingStudy(false);
    }
  }, [existingStudyId, initialData, toast]);

  // Get current step component
  const CurrentStepComponent = wizardSteps[currentStep].component;
  const isFirstStep = currentStep === 0;
  const isLastStep = currentStep === wizardSteps.length - 1;

  // Handle step navigation
  const goToStep = (stepIndex: number) => {
    if (stepIndex >= 0 && stepIndex < wizardSteps.length) {
      setCurrentStep(stepIndex);
    }
  };

  const goToPreviousStep = () => {
    if (!isFirstStep) {
      goToStep(currentStep - 1);
    }
  };

  const goToNextStep = () => {
    if (!isLastStep) {
      goToStep(currentStep + 1);
    }
  };

  // Handle step completion
  const handleStepComplete = async (stepData: any) => {
    try {
      setIsLoading(true);
      const stepId = wizardSteps[currentStep].id;
      
      // Update wizard data
      const updatedData = { ...wizardData, [stepId]: stepData };
      setWizardData(updatedData);
      
      // Store in window for cross-component access (temporary solution)
      (window as any).__wizardData = updatedData;

      // Handle specific step logic
      switch (stepId) {
        case 'basic_info':
          // Create study only if we don't have one already
          if (!studyId) {
            const createResponse = await studiesApi.startInitializationWizard({
              name: stepData.name,
              protocol_number: stepData.protocol_number,
              description: stepData.description,
              phase: stepData.phase,
              therapeutic_area: stepData.therapeutic_area,
              indication: stepData.indication,
            });
            setStudyId(createResponse.study_id);
          }
          break;

        case 'template_selection':
          // Select template
          if (studyId) {
            await studiesApi.selectTemplate(studyId, {
              template_id: stepData.templateId,
            });
          }
          break;

        case 'data_upload':
          // Mark upload complete and trigger processing
          if (studyId) {
            // Show processing state
            toast({
              title: 'Processing Files',
              description: 'Extracting schema information from your uploaded files...',
            });
            
            try {
              await studiesApi.completeUploadStep(studyId);
              
              // File processing happens on backend during completeUploadStep
              toast({
                title: 'Processing Complete',
                description: 'File schema extracted successfully',
              });
            } catch (error) {
              toast({
                title: 'Processing Error',
                description: 'Failed to process files. Please try again.',
                variant: 'destructive',
              });
              throw error;
            }
          }
          break;

        case 'review_mappings':
          // Complete wizard
          if (studyId) {
            const result = await studiesApi.completeWizard(studyId, {
              accept_auto_mappings: stepData.acceptAutoMappings,
              custom_mappings: stepData.customMappings,
            });
            
            // Start actual initialization
            await studiesApi.initializeStudyWithProgress(studyId, {
              template_id: wizardData.template_selection.templateId,
              skip_data_upload: false,
            });
            
            toast({
              title: 'Initialization Started',
              description: 'Study initialization is in progress',
            });
            
            onComplete?.(studyId);
            return;
          }
          break;
      }

      // Mark step as completed
      setCompletedSteps(prev => new Set(prev).add(stepId));
      
      // Move to next step
      if (!isLastStep) {
        goToNextStep();
      }
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to complete step',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Handle wizard cancellation
  const handleCancel = async () => {
    if (studyId) {
      try {
        await studiesApi.cancelWizard(studyId);
      } catch (error) {
        console.error('Failed to cancel wizard:', error);
      }
    }
    onCancel?.();
  };

  // Calculate progress
  const progress = ((currentStep + 1) / wizardSteps.length) * 100;

  if (isLoadingStudy) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Progress Bar */}
      <div className="space-y-2">
        <div className="flex justify-between text-sm text-muted-foreground">
          <span>Step {currentStep + 1} of {wizardSteps.length}</span>
          <span>{Math.round(progress)}% Complete</span>
        </div>
        <Progress value={progress} className="h-2" />
      </div>

      {/* Step Indicators */}
      <div className="flex justify-between">
        {wizardSteps.map((step, index) => {
          const isActive = index === currentStep;
          const isCompleted = completedSteps.has(step.id);
          const isPending = index > currentStep;
          
          return (
            <div
              key={step.id}
              className={cn(
                'flex items-center',
                index < wizardSteps.length - 1 && 'flex-1'
              )}
            >
              <button
                onClick={() => !isPending && goToStep(index)}
                disabled={isPending}
                className={cn(
                  'flex items-center justify-center w-10 h-10 rounded-full border-2 transition-colors',
                  isActive && 'border-primary bg-primary text-primary-foreground',
                  isCompleted && !isActive && 'border-green-500 bg-green-500 text-white',
                  isPending && 'border-gray-300 bg-white text-gray-400',
                  !isActive && !isCompleted && !isPending && 'border-gray-300 bg-white text-gray-600 hover:border-gray-400'
                )}
              >
                {isCompleted ? (
                  <Check className="h-5 w-5" />
                ) : (
                  <span className="text-sm font-medium">{index + 1}</span>
                )}
              </button>
              <div className="ml-3 hidden sm:block">
                <p className={cn(
                  'text-sm font-medium',
                  isActive && 'text-primary',
                  isCompleted && 'text-green-600',
                  isPending && 'text-gray-400'
                )}>
                  {step.name}
                </p>
              </div>
              {index < wizardSteps.length - 1 && (
                <div className={cn(
                  'flex-1 h-0.5 mx-4',
                  isCompleted ? 'bg-green-500' : 'bg-gray-300'
                )} />
              )}
            </div>
          );
        })}
      </div>

      {/* Step Content */}
      <Card className="p-6">
        <CurrentStepComponent
          studyId={studyId}
          data={wizardData[wizardSteps[currentStep].id] || {}}
          onComplete={handleStepComplete}
          isLoading={isLoading}
        />
      </Card>

      {/* Navigation Buttons */}
      <div className="flex justify-between">
        <Button
          variant="outline"
          onClick={handleCancel}
        >
          Cancel
        </Button>
        <div className="flex gap-2">
          {!isFirstStep && (
            <Button
              variant="outline"
              onClick={goToPreviousStep}
              disabled={isLoading}
            >
              <ChevronLeft className="h-4 w-4 mr-2" />
              Previous
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}