// ABOUTME: Component for creating and editing mapping templates
// ABOUTME: Provides visual interface for configuring widget field mappings and transformations

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Separator } from '@/components/ui/separator';
import {
  AlertCircle,
  Plus,
  Trash2,
  Save,
  Copy,
  FileJson,
  Database,
  FunctionSquare,
  Filter,
  ChevronRight,
  Code,
  Eye,
  EyeOff,
  TestTube
} from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useToast } from '@/components/ui/use-toast';
import MonacoEditor from '@monaco-editor/react';

interface MappingTemplate {
  id?: string;
  name: string;
  description: string;
  widget_type: string;
  category: string;
  tags: string[];
  configuration: {
    field_mappings: Record<string, FieldMapping>;
    transformations: Transformation[];
    filters: FilterConfig[];
    aggregations: AggregationConfig[];
    calculations: CalculationConfig[];
  };
  is_active: boolean;
}

interface FieldMapping {
  source_field: string;
  target_field?: string;
  data_type: string;
  transformation?: string;
  default_value?: any;
}

interface Transformation {
  id: string;
  name: string;
  type: string;
  input_fields: string[];
  output_field: string;
  parameters: Record<string, any>;
}

interface FilterConfig {
  field: string;
  operator: string;
  value: any;
  logic?: 'AND' | 'OR';
}

interface AggregationConfig {
  field: string;
  function: string;
  alias: string;
  group_by?: string[];
}

interface CalculationConfig {
  name: string;
  expression: string;
  output_field: string;
  data_type: string;
}

interface MappingTemplateEditorProps {
  template?: MappingTemplate;
  onSave: (template: MappingTemplate) => void;
  onCancel: () => void;
}

export function MappingTemplateEditor({ template, onSave, onCancel }: MappingTemplateEditorProps) {
  const [formData, setFormData] = useState<MappingTemplate>({
    name: '',
    description: '',
    widget_type: 'kpi_metric',
    category: 'clinical',
    tags: [],
    configuration: {
      field_mappings: {},
      transformations: [],
      filters: [],
      aggregations: [],
      calculations: []
    },
    is_active: true,
    ...template
  });

  const [tagInput, setTagInput] = useState('');
  const [showPreview, setShowPreview] = useState(false);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const { toast } = useToast();

  const widgetTypes = [
    { value: 'kpi_metric', label: 'KPI Metric Card' },
    { value: 'time_series', label: 'Time Series Chart' },
    { value: 'distribution', label: 'Distribution Chart' },
    { value: 'data_table', label: 'Data Table' },
    { value: 'subject_timeline', label: 'Subject Timeline' }
  ];

  const transformationTypes = [
    { value: 'rename', label: 'Rename Field' },
    { value: 'type_cast', label: 'Type Cast' },
    { value: 'date_format', label: 'Date Format' },
    { value: 'calculation', label: 'Calculation' },
    { value: 'aggregation', label: 'Aggregation' },
    { value: 'pivot', label: 'Pivot' },
    { value: 'unpivot', label: 'Unpivot' },
    { value: 'join', label: 'Join' },
    { value: 'filter', label: 'Filter' },
    { value: 'sort', label: 'Sort' },
    { value: 'custom', label: 'Custom Script' }
  ];

  const addFieldMapping = () => {
    const newId = `field_${Date.now()}`;
    setFormData({
      ...formData,
      configuration: {
        ...formData.configuration,
        field_mappings: {
          ...formData.configuration.field_mappings,
          [newId]: {
            source_field: '',
            target_field: '',
            data_type: 'string',
            transformation: undefined,
            default_value: undefined
          }
        }
      }
    });
  };

  const updateFieldMapping = (id: string, field: Partial<FieldMapping>) => {
    setFormData({
      ...formData,
      configuration: {
        ...formData.configuration,
        field_mappings: {
          ...formData.configuration.field_mappings,
          [id]: {
            ...formData.configuration.field_mappings[id],
            ...field
          }
        }
      }
    });
  };

  const removeFieldMapping = (id: string) => {
    const newMappings = { ...formData.configuration.field_mappings };
    delete newMappings[id];
    setFormData({
      ...formData,
      configuration: {
        ...formData.configuration,
        field_mappings: newMappings
      }
    });
  };

  const addTransformation = () => {
    const newTransformation: Transformation = {
      id: `transform_${Date.now()}`,
      name: '',
      type: 'rename',
      input_fields: [],
      output_field: '',
      parameters: {}
    };
    
    setFormData({
      ...formData,
      configuration: {
        ...formData.configuration,
        transformations: [...formData.configuration.transformations, newTransformation]
      }
    });
  };

  const updateTransformation = (index: number, transformation: Partial<Transformation>) => {
    const newTransformations = [...formData.configuration.transformations];
    newTransformations[index] = { ...newTransformations[index], ...transformation };
    
    setFormData({
      ...formData,
      configuration: {
        ...formData.configuration,
        transformations: newTransformations
      }
    });
  };

  const removeTransformation = (index: number) => {
    setFormData({
      ...formData,
      configuration: {
        ...formData.configuration,
        transformations: formData.configuration.transformations.filter((_, i) => i !== index)
      }
    });
  };

  const addCalculation = () => {
    const newCalculation: CalculationConfig = {
      name: '',
      expression: '',
      output_field: '',
      data_type: 'float'
    };
    
    setFormData({
      ...formData,
      configuration: {
        ...formData.configuration,
        calculations: [...formData.configuration.calculations, newCalculation]
      }
    });
  };

  const updateCalculation = (index: number, calculation: Partial<CalculationConfig>) => {
    const newCalculations = [...formData.configuration.calculations];
    newCalculations[index] = { ...newCalculations[index], ...calculation };
    
    setFormData({
      ...formData,
      configuration: {
        ...formData.configuration,
        calculations: newCalculations
      }
    });
  };

  const removeCalculation = (index: number) => {
    setFormData({
      ...formData,
      configuration: {
        ...formData.configuration,
        calculations: formData.configuration.calculations.filter((_, i) => i !== index)
      }
    });
  };

  const addTag = () => {
    if (tagInput && !formData.tags.includes(tagInput)) {
      setFormData({
        ...formData,
        tags: [...formData.tags, tagInput]
      });
      setTagInput('');
    }
  };

  const removeTag = (tag: string) => {
    setFormData({
      ...formData,
      tags: formData.tags.filter(t => t !== tag)
    });
  };

  const validateTemplate = (): boolean => {
    const errors: string[] = [];
    
    if (!formData.name) {
      errors.push('Template name is required');
    }
    
    if (!formData.description) {
      errors.push('Template description is required');
    }
    
    if (Object.keys(formData.configuration.field_mappings).length === 0) {
      errors.push('At least one field mapping is required');
    }
    
    // Validate field mappings
    Object.entries(formData.configuration.field_mappings).forEach(([id, mapping]) => {
      if (!mapping.source_field) {
        errors.push(`Source field is required for mapping ${id}`);
      }
    });
    
    setValidationErrors(errors);
    return errors.length === 0;
  };

  const handleSave = () => {
    if (validateTemplate()) {
      onSave(formData);
      toast({
        title: 'Success',
        description: 'Template saved successfully',
      });
    } else {
      toast({
        title: 'Validation Error',
        description: 'Please fix the errors before saving',
        variant: 'destructive',
      });
    }
  };

  const testTemplate = async () => {
    try {
      const response = await fetch('/api/v1/mapping-templates/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData.configuration)
      });
      
      if (response.ok) {
        const result = await response.json();
        toast({
          title: 'Test Successful',
          description: 'Template configuration is valid',
        });
      } else {
        const error = await response.json();
        toast({
          title: 'Test Failed',
          description: error.detail || 'Template configuration has errors',
          variant: 'destructive',
        });
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to test template',
        variant: 'destructive',
      });
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">
            {template ? 'Edit Template' : 'Create Template'}
          </h2>
          <p className="text-muted-foreground">
            Configure reusable widget mapping template
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={testTemplate}>
            <TestTube className="mr-2 h-4 w-4" />
            Test
          </Button>
          <Button variant="outline" onClick={() => setShowPreview(!showPreview)}>
            {showPreview ? (
              <>
                <EyeOff className="mr-2 h-4 w-4" />
                Hide Preview
              </>
            ) : (
              <>
                <Eye className="mr-2 h-4 w-4" />
                Show Preview
              </>
            )}
          </Button>
          <Button variant="outline" onClick={onCancel}>
            Cancel
          </Button>
          <Button onClick={handleSave}>
            <Save className="mr-2 h-4 w-4" />
            Save Template
          </Button>
        </div>
      </div>

      {/* Validation Errors */}
      {validationErrors.length > 0 && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            <ul className="list-disc list-inside">
              {validationErrors.map((error, index) => (
                <li key={index}>{error}</li>
              ))}
            </ul>
          </AlertDescription>
        </Alert>
      )}

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Configuration Form */}
        <div className="space-y-6">
          {/* Basic Information */}
          <Card>
            <CardHeader>
              <CardTitle>Basic Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="name">Template Name</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Enter template name"
                />
              </div>
              
              <div>
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Describe what this template does"
                  rows={3}
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="widget_type">Widget Type</Label>
                  <Select
                    value={formData.widget_type}
                    onValueChange={(value) => setFormData({ ...formData, widget_type: value })}
                  >
                    <SelectTrigger id="widget_type">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {widgetTypes.map(type => (
                        <SelectItem key={type.value} value={type.value}>
                          {type.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                
                <div>
                  <Label htmlFor="category">Category</Label>
                  <Select
                    value={formData.category}
                    onValueChange={(value) => setFormData({ ...formData, category: value })}
                  >
                    <SelectTrigger id="category">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="clinical">Clinical</SelectItem>
                      <SelectItem value="operational">Operational</SelectItem>
                      <SelectItem value="safety">Safety</SelectItem>
                      <SelectItem value="quality">Quality</SelectItem>
                      <SelectItem value="custom">Custom</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              
              <div>
                <Label htmlFor="tags">Tags</Label>
                <div className="flex gap-2">
                  <Input
                    id="tags"
                    value={tagInput}
                    onChange={(e) => setTagInput(e.target.value)}
                    placeholder="Add tag"
                    onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addTag())}
                  />
                  <Button onClick={addTag} size="sm">Add</Button>
                </div>
                <div className="flex gap-2 flex-wrap mt-2">
                  {formData.tags.map(tag => (
                    <Badge key={tag} variant="secondary">
                      {tag}
                      <button
                        onClick={() => removeTag(tag)}
                        className="ml-1 hover:text-destructive"
                      >
                        ×
                      </button>
                    </Badge>
                  ))}
                </div>
              </div>
              
              <div className="flex items-center space-x-2">
                <Switch
                  id="active"
                  checked={formData.is_active}
                  onCheckedChange={(checked) => setFormData({ ...formData, is_active: checked })}
                />
                <Label htmlFor="active">Active</Label>
              </div>
            </CardContent>
          </Card>

          {/* Configuration Tabs */}
          <Card>
            <CardHeader>
              <CardTitle>Template Configuration</CardTitle>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="mappings">
                <TabsList className="grid w-full grid-cols-3">
                  <TabsTrigger value="mappings">Field Mappings</TabsTrigger>
                  <TabsTrigger value="transformations">Transformations</TabsTrigger>
                  <TabsTrigger value="calculations">Calculations</TabsTrigger>
                </TabsList>
                
                <TabsContent value="mappings" className="space-y-4">
                  <div className="flex justify-between items-center">
                    <p className="text-sm text-muted-foreground">
                      Map source fields to widget requirements
                    </p>
                    <Button onClick={addFieldMapping} size="sm">
                      <Plus className="mr-2 h-4 w-4" />
                      Add Mapping
                    </Button>
                  </div>
                  
                  {Object.entries(formData.configuration.field_mappings).map(([id, mapping]) => (
                    <div key={id} className="border rounded-lg p-4 space-y-3">
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <Label>Source Field</Label>
                          <Input
                            value={mapping.source_field}
                            onChange={(e) => updateFieldMapping(id, { source_field: e.target.value })}
                            placeholder="e.g., SUBJID"
                          />
                        </div>
                        <div>
                          <Label>Target Field</Label>
                          <Input
                            value={mapping.target_field || ''}
                            onChange={(e) => updateFieldMapping(id, { target_field: e.target.value })}
                            placeholder="e.g., subject_id"
                          />
                        </div>
                      </div>
                      
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <Label>Data Type</Label>
                          <Select
                            value={mapping.data_type}
                            onValueChange={(value) => updateFieldMapping(id, { data_type: value })}
                          >
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="string">String</SelectItem>
                              <SelectItem value="number">Number</SelectItem>
                              <SelectItem value="date">Date</SelectItem>
                              <SelectItem value="boolean">Boolean</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        <div>
                          <Label>Default Value</Label>
                          <Input
                            value={mapping.default_value || ''}
                            onChange={(e) => updateFieldMapping(id, { default_value: e.target.value })}
                            placeholder="Optional"
                          />
                        </div>
                      </div>
                      
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => removeFieldMapping(id)}
                        className="text-destructive"
                      >
                        <Trash2 className="mr-2 h-4 w-4" />
                        Remove
                      </Button>
                    </div>
                  ))}
                </TabsContent>
                
                <TabsContent value="transformations" className="space-y-4">
                  <div className="flex justify-between items-center">
                    <p className="text-sm text-muted-foreground">
                      Define data transformations
                    </p>
                    <Button onClick={addTransformation} size="sm">
                      <Plus className="mr-2 h-4 w-4" />
                      Add Transformation
                    </Button>
                  </div>
                  
                  {formData.configuration.transformations.map((transform, index) => (
                    <div key={transform.id} className="border rounded-lg p-4 space-y-3">
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <Label>Name</Label>
                          <Input
                            value={transform.name}
                            onChange={(e) => updateTransformation(index, { name: e.target.value })}
                            placeholder="Transformation name"
                          />
                        </div>
                        <div>
                          <Label>Type</Label>
                          <Select
                            value={transform.type}
                            onValueChange={(value) => updateTransformation(index, { type: value })}
                          >
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              {transformationTypes.map(type => (
                                <SelectItem key={type.value} value={type.value}>
                                  {type.label}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                      </div>
                      
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => removeTransformation(index)}
                        className="text-destructive"
                      >
                        <Trash2 className="mr-2 h-4 w-4" />
                        Remove
                      </Button>
                    </div>
                  ))}
                </TabsContent>
                
                <TabsContent value="calculations" className="space-y-4">
                  <div className="flex justify-between items-center">
                    <p className="text-sm text-muted-foreground">
                      Define calculated fields
                    </p>
                    <Button onClick={addCalculation} size="sm">
                      <Plus className="mr-2 h-4 w-4" />
                      Add Calculation
                    </Button>
                  </div>
                  
                  {formData.configuration.calculations.map((calc, index) => (
                    <div key={index} className="border rounded-lg p-4 space-y-3">
                      <div>
                        <Label>Name</Label>
                        <Input
                          value={calc.name}
                          onChange={(e) => updateCalculation(index, { name: e.target.value })}
                          placeholder="Calculation name"
                        />
                      </div>
                      
                      <div>
                        <Label>Expression</Label>
                        <Textarea
                          value={calc.expression}
                          onChange={(e) => updateCalculation(index, { expression: e.target.value })}
                          placeholder="e.g., field1 + field2"
                          rows={2}
                        />
                      </div>
                      
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <Label>Output Field</Label>
                          <Input
                            value={calc.output_field}
                            onChange={(e) => updateCalculation(index, { output_field: e.target.value })}
                            placeholder="Result field name"
                          />
                        </div>
                        <div>
                          <Label>Data Type</Label>
                          <Select
                            value={calc.data_type}
                            onValueChange={(value) => updateCalculation(index, { data_type: value })}
                          >
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="float">Float</SelectItem>
                              <SelectItem value="integer">Integer</SelectItem>
                              <SelectItem value="string">String</SelectItem>
                              <SelectItem value="boolean">Boolean</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      </div>
                      
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => removeCalculation(index)}
                        className="text-destructive"
                      >
                        <Trash2 className="mr-2 h-4 w-4" />
                        Remove
                      </Button>
                    </div>
                  ))}
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        </div>

        {/* Preview Panel */}
        {showPreview && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Configuration Preview</CardTitle>
                <CardDescription>
                  JSON representation of the template configuration
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-[600px] border rounded-lg overflow-hidden">
                  <MonacoEditor
                    height="100%"
                    language="json"
                    theme="vs-light"
                    value={JSON.stringify(formData.configuration, null, 2)}
                    options={{
                      readOnly: true,
                      minimap: { enabled: false },
                      scrollBeyondLastLine: false,
                      fontSize: 12
                    }}
                  />
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader>
                <CardTitle>Template Summary</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Field Mappings:</span>
                  <span>{Object.keys(formData.configuration.field_mappings).length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Transformations:</span>
                  <span>{formData.configuration.transformations.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Calculations:</span>
                  <span>{formData.configuration.calculations.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Filters:</span>
                  <span>{formData.configuration.filters.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Aggregations:</span>
                  <span>{formData.configuration.aggregations.length}</span>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}