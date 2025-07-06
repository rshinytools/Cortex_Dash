// ABOUTME: Pipeline configuration step in study initialization wizard
// ABOUTME: Allows setting up data processing rules for the study

'use client';

import { useState, useEffect } from 'react';
import { Plus, Trash2, GripVertical, Upload, FileText } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

interface PipelineStepProps {
  studyId: string;
  data: any;
  onDataChange: (data: any) => void;
}

const transformationTypes = [
  { id: 'standardize', name: 'Standardize Column Names', category: 'formatting' },
  { id: 'filter', name: 'Filter Records', category: 'filtering' },
  { id: 'derive', name: 'Derive Variables', category: 'derivation' },
  { id: 'pivot', name: 'Pivot Data', category: 'transformation' },
  { id: 'aggregate', name: 'Aggregate Data', category: 'aggregation' },
  { id: 'custom', name: 'Custom Script', category: 'custom' },
];

export function PipelineStep({ studyId, data, onDataChange }: PipelineStepProps) {
  const [pipelineSteps, setPipelineSteps] = useState(data.steps || []);
  const [schedule, setSchedule] = useState(data.schedule || '');

  useEffect(() => {
    onDataChange({ steps: pipelineSteps, schedule });
  }, [pipelineSteps, schedule]);

  const addStep = () => {
    const newStep = {
      id: `step-${Date.now()}`,
      name: '',
      type: 'standardize',
      config: {},
      order: pipelineSteps.length,
    };
    setPipelineSteps([...pipelineSteps, newStep]);
  };

  const updateStep = (index: number, updates: any) => {
    const updated = [...pipelineSteps];
    updated[index] = { ...updated[index], ...updates };
    setPipelineSteps(updated);
  };

  const removeStep = (index: number) => {
    setPipelineSteps(pipelineSteps.filter((_: any, i: number) => i !== index));
  };

  const renderStepConfig = (step: any, index: number) => {
    switch (step.type) {
      case 'standardize':
        return (
          <div>
            <Label>Column Mapping</Label>
            <Textarea
              placeholder='{"SUBJID": "subject_id", "VISITNUM": "visit_number"}'
              value={step.config.mapping || ''}
              onChange={(e) => updateStep(index, {
                config: { ...step.config, mapping: e.target.value }
              })}
              className="font-mono text-sm"
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
            <Tabs defaultValue="inline" className="mt-2">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="inline">Write Inline</TabsTrigger>
                <TabsTrigger value="upload">Upload File</TabsTrigger>
              </TabsList>
              <TabsContent value="inline" className="mt-4">
                <Textarea
                  placeholder="# Python code to transform the dataframe&#10;# Input: df (pandas DataFrame)&#10;# Output: transformed df&#10;&#10;def transform(df):&#10;    # Your transformation logic here&#10;    return df"
                  value={step.config.script || ''}
                  onChange={(e) => updateStep(index, {
                    config: { ...step.config, script: e.target.value, scriptType: 'inline' }
                  })}
                  className="font-mono text-sm"
                  rows={10}
                />
              </TabsContent>
              <TabsContent value="upload" className="mt-4">
                <div className="space-y-4">
                  <div>
                    <Input
                      id={`script-${index}`}
                      type="file"
                      accept=".py"
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) {
                          updateStep(index, {
                            config: { 
                              ...step.config, 
                              scriptFile: file, 
                              scriptFileName: file.name,
                              scriptType: 'upload'
                            }
                          });
                        }
                      }}
                      className="cursor-pointer"
                    />
                    {step.config.scriptFileName && (
                      <div className="flex items-center gap-2 mt-2 text-sm text-muted-foreground">
                        <FileText className="h-4 w-4" />
                        <span>{step.config.scriptFileName}</span>
                      </div>
                    )}
                    <p className="text-xs text-muted-foreground mt-1">
                      Upload a Python script file (.py). The script should define a transform(df) function.
                    </p>
                  </div>
                </div>
              </TabsContent>
            </Tabs>
          </div>
        );
      
      default:
        return (
          <p className="text-sm text-muted-foreground">
            Configuration for this transformation type coming soon.
          </p>
        );
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium mb-2">Processing Steps</h3>
        <p className="text-sm text-muted-foreground mb-4">
          Define how data should be processed after import. Steps are executed in order.
        </p>
        
        {pipelineSteps.length === 0 ? (
          <Card>
            <CardContent className="py-8 text-center">
              <p className="text-muted-foreground mb-4">
                No processing steps configured. Add steps to transform your data.
              </p>
              <Button onClick={addStep}>
                <Plus className="mr-2 h-4 w-4" />
                Add First Step
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4">
            {pipelineSteps.map((step: any, index: number) => (
              <Card key={step.id}>
                <CardContent className="pt-6">
                  <div className="flex items-start gap-4">
                    <div className="mt-2">
                      <GripVertical className="h-5 w-5 text-muted-foreground" />
                    </div>
                    <div className="flex-1 space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <Label>Step Name</Label>
                          <Input
                            placeholder="e.g., Standardize column names"
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
                              {transformationTypes.map((type) => (
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
                      variant="outline"
                      onClick={() => removeStep(index)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
            <Button onClick={addStep} variant="outline" className="w-full">
              <Plus className="mr-2 h-4 w-4" />
              Add Step
            </Button>
          </div>
        )}
      </div>

      <div>
        <h3 className="text-lg font-medium mb-2">Pipeline Schedule</h3>
        <Label>Automatic Execution Schedule</Label>
        <Input
          placeholder="0 0 * * * (daily at midnight)"
          value={schedule}
          onChange={(e) => setSchedule(e.target.value)}
        />
        <p className="text-xs text-muted-foreground mt-1">
          Cron expression for automatic pipeline execution. Leave empty for manual execution only.
        </p>
        <div className="mt-4 p-4 bg-muted rounded-lg">
          <p className="text-sm">
            <strong>Note:</strong> Even with manual data uploads, you can schedule automatic 
            pipeline execution to process any newly uploaded data. The pipeline will run at 
            the specified schedule and process all available data.
          </p>
        </div>
      </div>
    </div>
  );
}