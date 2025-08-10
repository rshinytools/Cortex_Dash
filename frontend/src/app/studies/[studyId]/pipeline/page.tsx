// ABOUTME: Study-specific pipeline configuration page
// ABOUTME: Shows and manages data pipeline for a particular study

'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { 
  ArrowLeft, 
  Play, 
  Save, 
  Plus, 
  Trash2, 
  GripVertical,
  GitBranch,
  History,
  Settings,
  Activity
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/hooks/use-toast';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

interface PipelineStep {
  id: string;
  name: string;
  type: string;
  config: Record<string, any>;
  order: number;
}

const stepTypes = [
  { id: 'standardize', name: 'Standardize Column Names', category: 'formatting' },
  { id: 'filter', name: 'Filter Records', category: 'filtering' },
  { id: 'derive', name: 'Derive Variables', category: 'derivation' },
  { id: 'pivot', name: 'Pivot Data', category: 'transformation' },
  { id: 'aggregate', name: 'Aggregate Data', category: 'aggregation' },
  { id: 'custom', name: 'Custom Script', category: 'custom' },
];

export default function StudyPipelinePage() {
  const params = useParams();
  const router = useRouter();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const studyId = params.studyId as string;
  const [steps, setSteps] = useState<PipelineStep[]>([]);
  const [schedule, setSchedule] = useState('');

  const { data: study } = useQuery({
    queryKey: ['study', studyId],
    queryFn: async () => {
      const response = await apiClient.get(`/studies/${studyId}`);
      return response.data;
    },
  });

  const { data: pipeline, isLoading } = useQuery({
    queryKey: ['study-pipeline', studyId],
    queryFn: async () => {
      const response = await apiClient.get(`/studies/${studyId}/pipeline`);
      return response.data;
    },
  });

  useEffect(() => {
    if (pipeline) {
      setSteps(pipeline.steps || []);
      setSchedule(pipeline.schedule || '');
    }
  }, [pipeline]);

  const savePipeline = useMutation({
    mutationFn: async (data: any) => {
      const response = await apiClient.put(`/studies/${studyId}/pipeline`, data);
      return response.data;
    },
    onSuccess: () => {
      toast({
        title: 'Pipeline saved',
        description: 'Your pipeline configuration has been updated.',
      });
      queryClient.invalidateQueries({ queryKey: ['study-pipeline', studyId] });
    },
    onError: (error) => {
      toast({
        title: 'Failed to save pipeline',
        description: error instanceof Error ? error.message : 'An error occurred',
        variant: 'destructive',
      });
    },
  });

  const executePipeline = useMutation({
    mutationFn: async () => {
      const response = await apiClient.post(`/studies/${studyId}/pipeline/execute`);
      return response.data;
    },
    onSuccess: (data) => {
      toast({
        title: 'Pipeline execution started',
        description: 'The pipeline is now running. Check the execution history for progress.',
      });
      // Navigate to progress page with execution ID
      if (data?.execution_id) {
        router.push(`/studies/${studyId}/pipeline/progress?executionId=${data.execution_id}`);
      }
    },
    onError: (error) => {
      toast({
        title: 'Failed to execute pipeline',
        description: error instanceof Error ? error.message : 'An error occurred',
        variant: 'destructive',
      });
    },
  });

  const handleSave = () => {
    savePipeline.mutate({
      steps,
      schedule,
    });
  };

  const addStep = () => {
    const newStep: PipelineStep = {
      id: `step-${Date.now()}`,
      name: 'New Step',
      type: 'standardize',
      config: {},
      order: steps.length,
    };
    setSteps([...steps, newStep]);
  };

  const updateStep = (index: number, updates: Partial<PipelineStep>) => {
    const updated = [...steps];
    updated[index] = { ...updated[index], ...updates };
    setSteps(updated);
  };

  const removeStep = (index: number) => {
    setSteps(steps.filter((_, i) => i !== index));
  };

  const renderStepConfig = (step: PipelineStep, index: number) => {
    switch (step.type) {
      case 'standardize':
        return (
          <div>
            <Label>Column Mapping (JSON)</Label>
            <Textarea
              placeholder='{"SUBJID": "subject_id", "VISITNUM": "visit_number"}'
              value={step.config.mapping || ''}
              onChange={(e) => updateStep(index, {
                config: { ...step.config, mapping: e.target.value }
              })}
              className="font-mono text-sm"
              rows={3}
            />
          </div>
        );
      
      case 'filter':
        return (
          <div>
            <Label>Filter Expression</Label>
            <Input
              placeholder="e.g., status == 'ACTIVE' and age >= 18"
              value={step.config.expression || ''}
              onChange={(e) => updateStep(index, {
                config: { ...step.config, expression: e.target.value }
              })}
            />
          </div>
        );
      
      case 'custom':
        return (
          <div>
            <Label>Python Script</Label>
            <Textarea
              placeholder="# Python code to transform the dataframe"
              value={step.config.script || ''}
              onChange={(e) => updateStep(index, {
                config: { ...step.config, script: e.target.value }
              })}
              className="font-mono text-sm"
              rows={6}
            />
          </div>
        );
      
      default:
        return null;
    }
  };

  if (isLoading) {
    return <div>Loading pipeline configuration...</div>;
  }

  return (
    <div className="container mx-auto py-6">
      <div className="flex items-center mb-6">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => router.push('/studies')}
          className="mr-4"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Studies
        </Button>
        <div className="flex-1">
          <h1 className="text-3xl font-bold">Pipeline Configuration - {study?.name}</h1>
          <p className="text-muted-foreground mt-1">
            Configure data processing pipeline for this study
          </p>
        </div>
        <div className="flex space-x-2">
          <Button 
            variant="outline"
            onClick={() => router.push(`/studies/${studyId}/pipeline/progress`)}
          >
            <Activity className="mr-2 h-4 w-4" />
            Monitor Progress
          </Button>
          <Button 
            variant="outline"
            onClick={() => router.push(`/studies/${studyId}/pipeline/history`)}
          >
            <History className="mr-2 h-4 w-4" />
            History
          </Button>
          <Button
            variant="outline"
            onClick={() => executePipeline.mutate()}
            disabled={executePipeline.isPending}
          >
            <Play className="mr-2 h-4 w-4" />
            Execute Now
          </Button>
          <Button onClick={handleSave} disabled={savePipeline.isPending}>
            <Save className="mr-2 h-4 w-4" />
            Save Changes
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-12 gap-6">
        <div className="col-span-8">
          <Card>
            <CardHeader>
              <CardTitle>Pipeline Steps</CardTitle>
              <CardDescription>
                Define the sequence of operations for processing study data
              </CardDescription>
            </CardHeader>
            <CardContent>
              {steps.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  No steps configured. Add steps to process your data.
                </div>
              ) : (
                <div className="space-y-4">
                  {steps.map((step, index) => (
                    <Card key={step.id}>
                      <CardContent className="pt-6">
                        <div className="flex items-start gap-4">
                          <GripVertical className="h-5 w-5 mt-2 text-muted-foreground cursor-move" />
                          <div className="flex-1 space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                              <div>
                                <Label>Step Name</Label>
                                <Input
                                  value={step.name}
                                  onChange={(e) => updateStep(index, { name: e.target.value })}
                                />
                              </div>
                              <div>
                                <Label>Type</Label>
                                <Select
                                  value={step.type}
                                  onValueChange={(value) => updateStep(index, { type: value })}
                                >
                                  <SelectTrigger>
                                    <SelectValue />
                                  </SelectTrigger>
                                  <SelectContent>
                                    {stepTypes.map((type) => (
                                      <SelectItem key={type.id} value={type.id}>
                                        {type.name}
                                      </SelectItem>
                                    ))}
                                  </SelectContent>
                                </Select>
                              </div>
                            </div>
                            {renderStepConfig(step, index)}
                          </div>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => removeStep(index)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
              
              <Button
                variant="outline"
                className="w-full mt-4"
                onClick={addStep}
              >
                <Plus className="mr-2 h-4 w-4" />
                Add Step
              </Button>
            </CardContent>
          </Card>
        </div>

        <div className="col-span-4">
          <Card>
            <CardHeader>
              <CardTitle>Pipeline Settings</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="schedule">Execution Schedule</Label>
                <Input
                  id="schedule"
                  placeholder="0 0 * * * (daily at midnight)"
                  value={schedule}
                  onChange={(e) => setSchedule(e.target.value)}
                />
                <p className="text-sm text-muted-foreground mt-1">
                  Cron expression for automatic execution
                </p>
              </div>
              
              <div className="pt-4 border-t">
                <h4 className="text-sm font-medium mb-2">Pipeline Status</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Last Run</span>
                    <span>{pipeline?.last_run ? new Date(pipeline.last_run).toLocaleDateString() : 'Never'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Next Run</span>
                    <span>{pipeline?.next_run ? new Date(pipeline.next_run).toLocaleDateString() : 'Manual'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Status</span>
                    <Badge variant={pipeline?.is_active ? "default" : "secondary"}>
                      {pipeline?.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}