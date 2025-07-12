// ABOUTME: Visual pipeline builder for creating and editing data transformations
// ABOUTME: Provides drag-and-drop interface for building transformation steps

import React, { useState, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  Plus,
  Save,
  X,
  Code,
  Filter,
  Database,
  GitBranch,
  Trash2,
  Play,
  AlertCircle,
  CheckCircle,
  Settings,
  ChevronRight,
  ChevronDown,
  RefreshCw,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Switch } from '@/components/ui/switch';
import { useToast } from '@/hooks/use-toast';
import {
  pipelinesApi,
  TransformationType,
  TransformationStep,
  CreatePipelineRequest,
} from '@/lib/api/pipelines';
import { dataUploadsApi } from '@/lib/api/data-uploads';
import { ScriptEditor } from './ScriptEditor';
import { FilterBuilder } from './FilterBuilder';

interface PipelineBuilderProps {
  studyId: string;
  pipelineId?: string | null;
  onClose: () => void;
  onSave: () => void;
}

const TRANSFORMATION_TYPES = [
  {
    type: TransformationType.FILTER,
    label: 'Filter Data',
    icon: Filter,
    description: 'Filter rows based on conditions',
  },
  {
    type: TransformationType.PYTHON_SCRIPT,
    label: 'Python Script',
    icon: Code,
    description: 'Custom transformation using Python',
  },
  {
    type: TransformationType.AGGREGATION,
    label: 'Aggregate',
    icon: Database,
    description: 'Group and aggregate data',
  },
  {
    type: TransformationType.PIVOT,
    label: 'Pivot',
    icon: GitBranch,
    description: 'Pivot data from long to wide format',
  },
  {
    type: TransformationType.MAPPING,
    label: 'Map Values',
    icon: GitBranch,
    description: 'Map column values to new values',
  },
];

export function PipelineBuilder({
  studyId,
  pipelineId,
  onClose,
  onSave,
}: PipelineBuilderProps) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [sourceDataset, setSourceDataset] = useState('');
  const [outputFormat, setOutputFormat] = useState('parquet');
  const [outputName, setOutputName] = useState('');
  const [transformationSteps, setTransformationSteps] = useState<TransformationStep[]>([]);
  const [scheduleCron, setScheduleCron] = useState('');
  const [enableSchedule, setEnableSchedule] = useState(false);
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});
  const { toast } = useToast();

  // Fetch available datasets
  const { data: uploads } = useQuery({
    queryKey: ['dataUploads', studyId],
    queryFn: () => dataUploadsApi.listUploads(studyId, { active_only: true }),
  });

  // Fetch existing pipeline if editing
  const { data: existingPipeline } = useQuery({
    queryKey: ['pipeline', pipelineId],
    queryFn: () => (pipelineId ? pipelinesApi.getPipeline(pipelineId) : null),
    enabled: !!pipelineId,
  });

  // Initialize form with existing data
  useEffect(() => {
    if (existingPipeline) {
      setName(existingPipeline.name);
      setDescription(existingPipeline.description || '');
      setSourceDataset(existingPipeline.source_config.dataset_name || '');
      setOutputFormat(existingPipeline.output_config.format || 'parquet');
      setOutputName(existingPipeline.output_config.name || '');
      setTransformationSteps(existingPipeline.transformation_steps || []);
      setScheduleCron(existingPipeline.schedule_cron || '');
      setEnableSchedule(!!existingPipeline.schedule_cron);
    }
  }, [existingPipeline]);

  // Save pipeline mutation
  const saveMutation = useMutation({
    mutationFn: async (data: CreatePipelineRequest) => {
      if (pipelineId) {
        return pipelinesApi.updatePipeline(pipelineId, data);
      } else {
        return pipelinesApi.createPipeline(studyId, data);
      }
    },
    onSuccess: () => {
      toast({
        title: 'Pipeline saved',
        description: pipelineId ? 'Pipeline updated successfully' : 'Pipeline created successfully',
      });
      onSave();
    },
    onError: (err: any) => {
      toast({
        title: 'Save failed',
        description: err.response?.data?.detail || 'Failed to save pipeline',
        variant: 'destructive',
      });
    },
  });

  const addTransformationStep = (type: TransformationType) => {
    const newStep: TransformationStep = {
      name: `${type} Step ${transformationSteps.length + 1}`,
      type,
    };

    if (type === TransformationType.FILTER) {
      newStep.conditions = [];
    } else if (type === TransformationType.PYTHON_SCRIPT) {
      newStep.script_content = '# Transform the dataframe\n# Input: df\n# Output: df\n\n';
      newStep.allowed_imports = ['pandas', 'numpy', 'datetime', 're', 'json'];
      newStep.resource_limits = {
        max_memory_mb: 1024,
        max_execution_time_seconds: 300,
        max_cpu_percent: 80,
      };
    }

    setTransformationSteps([...transformationSteps, newStep]);
  };

  const updateStep = (index: number, updates: Partial<TransformationStep>) => {
    const newSteps = [...transformationSteps];
    newSteps[index] = { ...newSteps[index], ...updates };
    setTransformationSteps(newSteps);
  };

  const removeStep = (index: number) => {
    setTransformationSteps(transformationSteps.filter((_, i) => i !== index));
  };

  const validateForm = () => {
    const errors: Record<string, string> = {};

    if (!name.trim()) errors.name = 'Pipeline name is required';
    if (!sourceDataset) errors.sourceDataset = 'Source dataset is required';
    if (!outputName.trim()) errors.outputName = 'Output name is required';
    if (transformationSteps.length === 0) errors.steps = 'At least one transformation step is required';

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSave = () => {
    if (!validateForm()) {
      toast({
        title: 'Validation failed',
        description: 'Please fix the errors before saving',
        variant: 'destructive',
      });
      return;
    }

    const pipelineData: CreatePipelineRequest = {
      name,
      description: description || undefined,
      schedule_cron: enableSchedule ? scheduleCron : undefined,
      source_config: {
        type: 'data_upload',
        dataset_name: sourceDataset,
      },
      transformation_steps: transformationSteps,
      output_config: {
        format: outputFormat,
        name: outputName,
      },
    };

    saveMutation.mutate(pipelineData);
  };

  const availableDatasets = uploads?.data?.flatMap((upload: any) =>
    upload.files_extracted?.map((file: any) => ({
      value: file.dataset_name,
      label: file.dataset_name,
      rows: file.rows,
      columns: file.columns,
    })) || []
  ) || [];

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>{pipelineId ? 'Edit Pipeline' : 'Create Pipeline'}</CardTitle>
              <CardDescription>
                Configure data transformations to process your clinical data
              </CardDescription>
            </div>
            <Button variant="ghost" size="icon" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="config" className="space-y-4">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="config">Configuration</TabsTrigger>
              <TabsTrigger value="transformations">Transformations</TabsTrigger>
              <TabsTrigger value="output">Output</TabsTrigger>
            </TabsList>

            <TabsContent value="config" className="space-y-4">
              <div className="grid gap-4">
                <div className="grid gap-2">
                  <Label htmlFor="name">Pipeline Name</Label>
                  <Input
                    id="name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="e.g., Demographics Processing"
                    className={validationErrors.name ? 'border-red-500' : ''}
                  />
                  {validationErrors.name && (
                    <p className="text-sm text-red-500">{validationErrors.name}</p>
                  )}
                </div>

                <div className="grid gap-2">
                  <Label htmlFor="description">Description</Label>
                  <Textarea
                    id="description"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="Describe what this pipeline does..."
                    rows={3}
                  />
                </div>

                <div className="grid gap-2">
                  <Label htmlFor="source">Source Dataset</Label>
                  <Select value={sourceDataset} onValueChange={setSourceDataset}>
                    <SelectTrigger className={validationErrors.sourceDataset ? 'border-red-500' : ''}>
                      <SelectValue placeholder="Select a dataset" />
                    </SelectTrigger>
                    <SelectContent>
                      {availableDatasets.map((dataset: any) => (
                        <SelectItem key={dataset.value} value={dataset.value}>
                          <div className="flex items-center justify-between w-full">
                            <span>{dataset.label}</span>
                            <span className="text-xs text-gray-500 ml-2">
                              {dataset.rows} rows, {dataset.columns} cols
                            </span>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {validationErrors.sourceDataset && (
                    <p className="text-sm text-red-500">{validationErrors.sourceDataset}</p>
                  )}
                </div>

                <div className="flex items-center space-x-2">
                  <Switch
                    id="schedule"
                    checked={enableSchedule}
                    onCheckedChange={setEnableSchedule}
                  />
                  <Label htmlFor="schedule">Enable Scheduled Execution</Label>
                </div>

                {enableSchedule && (
                  <div className="grid gap-2">
                    <Label htmlFor="cron">Schedule (Cron Expression)</Label>
                    <Input
                      id="cron"
                      value={scheduleCron}
                      onChange={(e) => setScheduleCron(e.target.value)}
                      placeholder="0 0 * * * (daily at midnight)"
                    />
                    <p className="text-xs text-gray-500">
                      Use cron syntax for scheduling. Examples: "0 0 * * *" (daily), "0 */6 * * *" (every 6 hours)
                    </p>
                  </div>
                )}
              </div>
            </TabsContent>

            <TabsContent value="transformations" className="space-y-4">
              {validationErrors.steps && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{validationErrors.steps}</AlertDescription>
                </Alert>
              )}

              <div className="space-y-4">
                {transformationSteps.map((step, index) => (
                  <Card key={index}>
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          {React.createElement(
                            TRANSFORMATION_TYPES.find((t) => t.type === step.type)?.icon || Code,
                            { className: 'h-4 w-4' }
                          )}
                          <Input
                            value={step.name}
                            onChange={(e) => updateStep(index, { name: e.target.value })}
                            className="w-64"
                          />
                        </div>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => removeStep(index)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </CardHeader>
                    <CardContent>
                      {step.type === TransformationType.FILTER && (
                        <FilterBuilder
                          conditions={step.conditions || []}
                          onChange={(conditions) => updateStep(index, { conditions })}
                        />
                      )}
                      {step.type === TransformationType.PYTHON_SCRIPT && (
                        <ScriptEditor
                          script={step.script_content || ''}
                          onChange={(script_content) => updateStep(index, { script_content })}
                          allowedImports={step.allowed_imports || []}
                          onImportsChange={(allowed_imports) => updateStep(index, { allowed_imports })}
                        />
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>

              <div className="border-2 border-dashed rounded-lg p-6">
                <h3 className="text-sm font-medium text-center mb-4">
                  Add Transformation Step
                </h3>
                <div className="grid grid-cols-2 gap-3">
                  {TRANSFORMATION_TYPES.map((type) => (
                    <Button
                      key={type.type}
                      variant="outline"
                      className="h-auto p-4 justify-start"
                      onClick={() => addTransformationStep(type.type)}
                    >
                      <type.icon className="mr-3 h-5 w-5" />
                      <div className="text-left">
                        <div className="font-medium">{type.label}</div>
                        <div className="text-xs text-gray-500">{type.description}</div>
                      </div>
                    </Button>
                  ))}
                </div>
              </div>
            </TabsContent>

            <TabsContent value="output" className="space-y-4">
              <div className="grid gap-4">
                <div className="grid gap-2">
                  <Label htmlFor="outputName">Output Name</Label>
                  <Input
                    id="outputName"
                    value={outputName}
                    onChange={(e) => setOutputName(e.target.value)}
                    placeholder="e.g., processed_demographics"
                    className={validationErrors.outputName ? 'border-red-500' : ''}
                  />
                  {validationErrors.outputName && (
                    <p className="text-sm text-red-500">{validationErrors.outputName}</p>
                  )}
                </div>

                <div className="grid gap-2">
                  <Label htmlFor="format">Output Format</Label>
                  <Select value={outputFormat} onValueChange={setOutputFormat}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="parquet">Parquet (Recommended)</SelectItem>
                      <SelectItem value="csv">CSV</SelectItem>
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-gray-500">
                    Parquet format is recommended for better performance and compression
                  </p>
                </div>
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      <div className="flex justify-end gap-2">
        <Button variant="outline" onClick={onClose}>
          Cancel
        </Button>
        <Button onClick={handleSave} disabled={saveMutation.isPending}>
          {saveMutation.isPending ? (
            <>
              <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
              Saving...
            </>
          ) : (
            <>
              <Save className="mr-2 h-4 w-4" />
              Save Pipeline
            </>
          )}
        </Button>
      </div>
    </div>
  );
}