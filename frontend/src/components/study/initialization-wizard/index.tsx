// ABOUTME: Main initialization wizard component
// ABOUTME: Orchestrates the step-by-step study initialization flow

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { useToast } from '@/hooks/use-toast';
import { ChevronLeft, ChevronRight, Check, AlertCircle } from 'lucide-react';
import { studiesApi } from '@/lib/api/studies';
import { cn } from '@/lib/utils';

// Import wizard steps
import { BasicInfoStep } from './steps/basic-info';
import { TemplateSelectionStep } from './steps/template-selection';
import { DataUploadStep } from './steps/data-upload';
import { FieldMappingStep } from './steps/field-mapping';
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
    id: 'field_mapping',
    name: 'Map Fields',
    component: FieldMappingStep,
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
  existingStudy?: any;
  mode?: 'create' | 'edit';
  onComplete?: (studyId: string) => void;
  onCancel?: () => void;
}

export function InitializationWizard({
  studyId: existingStudyId,
  initialStep = 0,
  initialData,
  organizationId,
  existingStudy,
  mode = 'create',
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
  const [errorSteps, setErrorSteps] = useState<Set<string>>(new Set());

  // Load study data if resuming or editing
  useEffect(() => {
    const loadData = async () => {
      console.log('[InitializationWizard] mode:', mode, 'existingStudy:', existingStudy);
      
      if (mode === 'edit' && existingStudy) {
        // Import helper functions to convert labels back to values
        const clinicalData = await import('@/lib/clinical-data');
        const { getTherapeuticAreaValue, getIndicationValue } = clinicalData;
        
        // Edit mode: pre-populate from existing study
        const baseData = {
          basic_info: {
            name: existingStudy.name,
            protocol_number: existingStudy.protocol_number,
            description: existingStudy.description,
            phase: existingStudy.phase,
            // Convert labels back to values for dropdowns
            therapeutic_area: getTherapeuticAreaValue(existingStudy.therapeutic_area),
            indication: getIndicationValue(existingStudy.therapeutic_area, existingStudy.indication),
          },
          template_selection: {
            templateId: existingStudy.dashboard_template_id,
          },
          field_mapping: {
            mappings: existingStudy.field_mappings || {},
          },
        };
        
        console.log('[InitializationWizard] Setting wizard data for edit mode:', baseData);
        setWizardData(baseData);
        // In edit mode, mark all steps as accessible
        if (existingStudy.dashboard_template_id) {
          const completed = new Set<string>();
          completed.add('basic_info');
          completed.add('template_selection');
          if (existingStudy.data_uploaded_at) {
            completed.add('data_upload');
          }
          if (existingStudy.field_mappings) {
            completed.add('field_mapping');
          }
          setCompletedSteps(completed);
        }
        setIsLoadingStudy(false);
      } else if (existingStudyId && !initialData) {
        // Resume mode: load from wizard state
        try {
          const study = await studiesApi.getStudy(existingStudyId);
          const wizardState = await studiesApi.getWizardState(existingStudyId);
          
          // Populate wizard data from study and wizard state
          const baseData = {
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
          };
          
          // Merge with any saved wizard data
          if (wizardState.data) {
            setWizardData({ ...baseData, ...wizardState.data });
          } else {
            setWizardData(baseData);
          }
          
          // Mark completed steps based on wizard state
          if (wizardState.completed_steps) {
            const completed = new Set<string>();
            wizardState.completed_steps.forEach((step: string) => {
              completed.add(step);
            });
            setCompletedSteps(completed);
          }
          
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
      } else {
        setIsLoadingStudy(false);
      }
    };
    
    loadData();
  }, [existingStudyId, initialData, existingStudy, mode, toast]);

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
      
      console.log(`[Wizard] Step ${stepId} completed with data:`, stepData);
      
      // Update wizard data
      const updatedData = { ...wizardData, [stepId]: stepData };
      setWizardData(updatedData);
      
      console.log('[Wizard] Updated wizard data:', updatedData);
      
      // Store in window for cross-component access (temporary solution)
      (window as any).__wizardData = updatedData;

      // Handle specific step logic
      switch (stepId) {
        case 'basic_info':
          if (mode === 'edit' && studyId) {
            // Update existing study
            try {
              await studiesApi.updateStudy(studyId, {
                name: stepData.name,
                protocol_number: stepData.protocol_number,
                description: stepData.description,
                phase: stepData.phase,
                therapeutic_area: stepData.therapeutic_area,
                indication: stepData.indication,
              });
              toast({
                title: 'Study Updated',
                description: 'Study information has been updated successfully',
              });
            } catch (error: any) {
              console.error('Study update error:', error);
              const errorMessage = error.response?.data?.detail || error.message || 'Failed to update study';
              toast({
                title: 'Update Failed',
                description: errorMessage,
                variant: 'destructive',
              });
              error.toastShown = true;
              throw error;
            }
          } else if (!studyId) {
            // Create new study
            try {
              const createResponse = await studiesApi.startInitializationWizard({
                name: stepData.name,
                protocol_number: stepData.protocol_number,
                description: stepData.description,
                phase: stepData.phase,
                therapeutic_area: stepData.therapeutic_area,
                indication: stepData.indication,
              });
              setStudyId(createResponse.study_id);
            } catch (error: any) {
              console.error('Study creation error:', error);
              
              // Extract error message from response
              const errorMessage = error.response?.data?.detail || error.message || 'Failed to create study';
              
              console.log('Showing toast with message:', errorMessage);
              
              // Show specific error message to user
              toast({
                title: 'Study Creation Failed',
                description: errorMessage,
                variant: 'destructive',
              });
              
              // Mark that we've shown a toast to prevent duplicate
              error.toastShown = true;
              
              // Re-throw to prevent continuing to next step
              throw error;
            }
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

        case 'field_mapping':
          // Save field mappings
          if (studyId) {
            try {
              // Use flatMappings for backend, keep nested mappings for display
              await studiesApi.saveFieldMappings(studyId, {
                mappings: stepData.flatMappings || stepData.mappings,
                accept_auto_mappings: stepData.acceptAutoMappings,
              });
              
              console.log('Field mappings saved:', stepData);
              
              toast({
                title: 'Mappings Saved',
                description: 'Field mappings have been configured successfully',
              });
            } catch (error) {
              console.error('Failed to save field mappings:', error);
              toast({
                title: 'Error',
                description: 'Failed to save field mappings. You can continue anyway.',
                variant: 'destructive',
              });
              // Don't throw error to allow continuing
            }
          }
          break;

        case 'review_mappings':
          // Complete wizard
          if (studyId) {
            if (mode === 'edit') {
              // In edit mode, save changes and re-initialize if new data was uploaded
              const result = await studiesApi.completeWizard(studyId, {
                accept_auto_mappings: stepData.acceptAutoMappings,
                custom_mappings: stepData.customMappings,
              });
              
              // Check if new data was uploaded (data_upload step exists in wizardData)
              if (wizardData.data_upload && wizardData.data_upload.files && wizardData.data_upload.files.length > 0) {
                // Re-initialize with new data
                await studiesApi.initializeStudyWithProgress(studyId, {
                  template_id: existingStudy?.dashboard_template_id || wizardData.template_selection?.templateId,
                  skip_data_upload: false,
                });
                
                toast({
                  title: 'Re-initialization Started',
                  description: 'Study is being updated with new data',
                });
                
                // Redirect to initialization progress page
                router.push(`/initialization/${studyId}`);
              } else {
                toast({
                  title: 'Changes Saved',
                  description: 'Study configuration has been updated successfully',
                });
              }
              
              onComplete?.(studyId);
              return;
            } else {
              // In create mode, start initialization
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
              
              // Redirect to initialization progress page (outside study layout to avoid sidebar)
              router.push(`/initialization/${studyId}`);
              onComplete?.(studyId);
              return;
            }
          }
          break;
      }

      // Mark step as completed and remove from error steps
      setCompletedSteps(prev => new Set(prev).add(stepId));
      setErrorSteps(prev => {
        const newErrors = new Set(prev);
        newErrors.delete(stepId);
        return newErrors;
      });
      
      // Save wizard state to backend
      if (studyId) {
        try {
          await studiesApi.updateWizardState(studyId, {
            current_step: currentStep + 2, // Backend expects 1-based index
            data: wizardData,
            completed_steps: Array.from(completedSteps).concat(stepId),
          });
        } catch (error) {
          console.error('Failed to save wizard state:', error);
          // Continue anyway - state saving is not critical
        }
      }
      
      // Move to next step
      if (!isLastStep) {
        goToNextStep();
      }
    } catch (error: any) {
      // Mark step as having an error
      const stepId = wizardSteps[currentStep].id;
      setErrorSteps(prev => new Set(prev).add(stepId));
      
      // Only show toast if we haven't already shown a specific one
      // (check if error has already been handled with a toast)
      if (!error.toastShown) {
        const errorMessage = error.response?.data?.detail || error.message || 'Failed to complete step';
        toast({
          title: 'Error',
          description: errorMessage,
          variant: 'destructive',
        });
      }
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
          const hasError = errorSteps.has(step.id);
          const isPending = index > currentStep && !isCompleted;
          
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
                  isActive && !hasError && 'border-primary bg-primary text-primary-foreground',
                  isActive && hasError && 'border-red-500 bg-red-500 text-white',
                  isCompleted && !isActive && !hasError && 'border-green-500 bg-green-500 text-white',
                  hasError && !isActive && 'border-red-500 bg-red-500 text-white',
                  isPending && 'border-gray-300 bg-white text-gray-400',
                  !isActive && !isCompleted && !isPending && !hasError && 'border-gray-300 bg-white text-gray-600 hover:border-gray-400'
                )}
              >
                {isCompleted && !hasError ? (
                  <Check className="h-5 w-5" />
                ) : hasError ? (
                  <AlertCircle className="h-5 w-5" />
                ) : (
                  <span className="text-sm font-medium">{index + 1}</span>
                )}
              </button>
              <div className="ml-3 hidden sm:block">
                <p className={cn(
                  'text-sm font-medium',
                  isActive && 'text-primary',
                  isCompleted && !hasError && 'text-green-600',
                  hasError && 'text-red-600',
                  isPending && 'text-gray-400'
                )}>
                  {step.id === 'review_mappings' && mode === 'edit' ? 'Review & Save' : step.name}
                </p>
              </div>
              {index < wizardSteps.length - 1 && (
                <div className={cn(
                  'flex-1 h-0.5 mx-4',
                  isCompleted && !hasError ? 'bg-green-500' : hasError ? 'bg-red-500' : 'bg-gray-300'
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
          mode={mode}
          existingStudy={existingStudy}
          data={(() => {
            const currentStepData = wizardData[wizardSteps[currentStep].id] || {};
            const dataToPass = {
              ...currentStepData,
              // Pass relevant data from previous steps
              templateId: wizardData.template_selection?.templateId,
              uploadedFiles: wizardData.data_upload?.files,
              fieldMappings: wizardData.field_mapping,
            };
            console.log(`[Wizard] Passing data to step ${wizardSteps[currentStep].id}:`, dataToPass);
            return dataToPass;
          })()}
          initialData={mode === 'edit' ? wizardData[wizardSteps[currentStep].id] : undefined}
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