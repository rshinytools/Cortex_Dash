// ABOUTME: Field mapping builder component for mapping data columns to widget fields
// ABOUTME: Provides drag-and-drop interface with validation and suggestions

import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  AlertCircle,
  ArrowRight,
  CheckCircle,
  Database,
  FileText,
  GitBranch,
  Hash,
  Calendar,
  ToggleLeft,
  Type,
  Lightbulb,
  Sparkles,
  X,
  Layers,
  FileSpreadsheet,
} from 'lucide-react';
import { mappingApi, MappingType, DataType } from '@/lib/api/mapping';
import { widgetsApi } from '@/lib/api/widgets';
import { cn } from '@/lib/utils';

interface DatasetSchema {
  columns: Record<string, any>;
  column_count?: number;
  row_count: number;
  last_updated?: string;
  upload_id?: string;
  source_type?: 'uploaded' | 'derived';
  source_dataset?: string;
  transformation_type?: string;
  created_at?: string;
}

interface FieldMappingBuilderProps {
  studyId: string;
  widgetId: string;
  onComplete?: () => void;
}

const DATA_TYPE_ICONS = {
  string: Type,
  number: Hash,
  date: Calendar,
  datetime: Calendar,
  boolean: ToggleLeft,
  array: Database,
  object: FileText,
};

const DATA_TYPE_LABELS = {
  string: 'Text',
  number: 'Number',
  date: 'Date',
  datetime: 'Date/Time',
  boolean: 'Boolean',
  array: 'Array',
  object: 'Object',
};

export function FieldMappingBuilder({
  studyId,
  widgetId,
  onComplete,
}: FieldMappingBuilderProps) {
  const queryClient = useQueryClient();
  const [mappings, setMappings] = useState<Record<string, any>>({});
  const [selectedDataset, setSelectedDataset] = useState<string>('');
  const [activeField, setActiveField] = useState<string>('');
  const [showSuggestions, setShowSuggestions] = useState(true);

  // Fetch widget details
  const { data: widget, isLoading: isLoadingWidget } = useQuery({
    queryKey: ['widget', widgetId],
    queryFn: () => widgetsApi.getWidget(widgetId),
  });

  // Fetch study data configuration
  const { data: dataConfig, isLoading: isLoadingConfig } = useQuery({
    queryKey: ['study-data-config', studyId],
    queryFn: () => mappingApi.getStudyDataConfig(studyId),
  });

  // Fetch mapping suggestions
  const { data: suggestions } = useQuery({
    queryKey: ['mapping-suggestions', studyId, widgetId],
    queryFn: () => mappingApi.getSuggestions(studyId, widgetId),
    enabled: showSuggestions && !!widget && !!dataConfig,
  });

  // Validate mapping mutation
  const validateMappingMutation = useMutation({
    mutationFn: (mapping: any) => mappingApi.validateMapping(mapping),
  });

  // Save mapping mutation
  const saveMappingMutation = useMutation({
    mutationFn: (mapping: any) => mappingApi.createMapping(mapping),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['widget-mappings', studyId] });
      onComplete?.();
    },
  });

  // Initialize mappings from suggestions
  useEffect(() => {
    if (suggestions && suggestions.length > 0) {
      const initialMappings: Record<string, any> = {};
      suggestions.forEach((suggestion) => {
        if (suggestion.confidence > 0.7) {
          const [dataset, field] = suggestion.suggested_source_field.split('.');
          initialMappings[suggestion.field_name] = {
            type: MappingType.DIRECT,
            source_field: field,
            data_type: suggestion.data_type_match ? getFieldDataType(field) : DataType.STRING,
          };
          if (!selectedDataset) {
            setSelectedDataset(dataset);
          }
        }
      });
      setMappings(initialMappings);
    }
  }, [suggestions]);

  const getFieldDataType = (fieldName: string): DataType => {
    if (!dataConfig || !selectedDataset) return DataType.STRING;
    const schema = dataConfig.dataset_schemas[selectedDataset];
    if (!schema) return DataType.STRING;
    const type = schema.columns[fieldName]?.type;
    // Ensure the type is a valid DataType
    if (type && Object.values(DataType).includes(type as DataType)) {
      return type as DataType;
    }
    return DataType.STRING;
  };

  const getRequiredFields = (): Record<string, any> => {
    if (!widget?.dataContract?.requiredFields) return {};
    // Convert array of fields to object keyed by field name
    const fieldsObj: Record<string, any> = {};
    widget.dataContract.requiredFields.forEach((field) => {
      fieldsObj[field.name] = field;
    });
    return fieldsObj;
  };

  const getAvailableColumns = () => {
    if (!dataConfig || !selectedDataset) return [];
    const schema = dataConfig.dataset_schemas[selectedDataset];
    if (!schema) return [];
    return Object.entries(schema.columns).map(([name, info]: [string, any]) => ({
      name,
      type: info.type,
      nullable: info.nullable,
      unique_count: info.unique_count,
      sample_values: info.sample_values || [],
    }));
  };

  const handleFieldMapping = (fieldName: string, mapping: any) => {
    setMappings((prev) => ({
      ...prev,
      [fieldName]: mapping,
    }));
  };

  const getMappingCompleteness = () => {
    const requiredFields = Object.keys(getRequiredFields());
    const mappedFields = Object.keys(mappings).filter(
      (field) => mappings[field]?.source_field || mappings[field]?.constant_value
    );
    return requiredFields.length > 0
      ? (mappedFields.length / requiredFields.length) * 100
      : 0;
  };

  const handleValidate = async () => {
    const mappingData = {
      study_id: studyId,
      widget_id: widgetId,
      field_mappings: mappings,
      data_source_config: {
        dataset_name: selectedDataset,
      },
    };
    await validateMappingMutation.mutateAsync(mappingData);
  };

  const handleSave = async () => {
    const mappingData = {
      study_id: studyId,
      widget_id: widgetId,
      field_mappings: mappings,
      data_source_config: {
        dataset_name: selectedDataset,
      },
    };
    await saveMappingMutation.mutateAsync(mappingData);
  };

  if (isLoadingWidget || isLoadingConfig) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto"></div>
            <p className="mt-2 text-sm text-gray-500">Loading configuration...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const requiredFields = getRequiredFields();
  const availableColumns = getAvailableColumns();
  const completeness = getMappingCompleteness();

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Field Mapping Configuration</CardTitle>
              <CardDescription>
                Map data source columns to {widget?.name} widget fields
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="outline">
                {Object.keys(mappings).length} / {Object.keys(requiredFields).length} mapped
              </Badge>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowSuggestions(!showSuggestions)}
              >
                <Lightbulb className={cn("h-4 w-4 mr-1", showSuggestions && "text-yellow-500")} />
                Suggestions
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <Label>Data Source</Label>
              <Select value={selectedDataset} onValueChange={setSelectedDataset}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a dataset" />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(dataConfig?.dataset_schemas || {}).map(([name, schema]: [string, DatasetSchema]) => (
                    <SelectItem key={name} value={name}>
                      <div className="flex items-center justify-between w-full">
                        <div className="flex items-center gap-2">
                          <FileSpreadsheet className="h-4 w-4 text-muted-foreground" />
                          <span>{name}</span>
                        </div>
                        <Badge variant="outline" className="ml-2">
                          {Object.keys(schema.columns || {}).length} cols
                        </Badge>
                      </div>
                    </SelectItem>
                  ))}
                  
                  {Object.keys(dataConfig?.dataset_schemas || {}).length === 0 && (
                    <div className="p-4 text-center text-muted-foreground">
                      No datasets available
                    </div>
                  )}
                </SelectContent>
              </Select>
            </div>

            {/* Dataset Info */}
            {selectedDataset && dataConfig?.dataset_schemas[selectedDataset] && (
              <div className="p-3 bg-muted rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <FileSpreadsheet className="h-4 w-4 text-blue-500" />
                  <span className="text-sm font-medium">Dataset: {selectedDataset}</span>
                </div>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <span className="text-muted-foreground">Rows:</span>{' '}
                    <span className="font-medium">{dataConfig.dataset_schemas[selectedDataset]?.row_count || 0}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Columns:</span>{' '}
                    <span className="font-medium">{Object.keys(dataConfig.dataset_schemas[selectedDataset]?.columns || {}).length}</span>
                  </div>
                  {dataConfig.dataset_schemas[selectedDataset]?.last_updated && (
                    <div className="col-span-2">
                      <span className="text-muted-foreground">Last Updated:</span>{' '}
                      <span className="font-medium">
                        {new Date(dataConfig.dataset_schemas[selectedDataset].last_updated).toLocaleString()}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            )}

            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Mapping Progress</span>
                <span>{Math.round(completeness)}%</span>
              </div>
              <Progress value={completeness} />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Mapping Interface */}
      <div className="grid grid-cols-12 gap-6">
        {/* Required Fields */}
        <div className="col-span-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Widget Fields</CardTitle>
              <CardDescription>Required fields for {widget?.name}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {Object.entries(requiredFields).map(([fieldName, fieldConfig]: [string, any]) => {
                  const mapping = mappings[fieldName];
                  const isMapped = mapping?.source_field || mapping?.constant_value;
                  const Icon = DATA_TYPE_ICONS[fieldConfig.data_type as keyof typeof DATA_TYPE_ICONS] || FileText;

                  return (
                    <div
                      key={fieldName}
                      className={cn(
                        "p-3 border rounded-lg cursor-pointer transition-colors",
                        activeField === fieldName && "border-blue-500 bg-blue-50",
                        isMapped && "bg-green-50 border-green-300"
                      )}
                      onClick={() => setActiveField(fieldName)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Icon className="h-4 w-4 text-gray-500" />
                          <div>
                            <p className="font-medium">{fieldName}</p>
                            <p className="text-xs text-gray-500">
                              {DATA_TYPE_LABELS[fieldConfig.data_type as keyof typeof DATA_TYPE_LABELS] || 'Unknown'}
                              {fieldConfig.required && (
                                <span className="text-red-500 ml-1">*</span>
                              )}
                            </p>
                          </div>
                        </div>
                        {isMapped && <CheckCircle className="h-4 w-4 text-green-600" />}
                      </div>
                      {fieldConfig.description && (
                        <p className="mt-1 text-xs text-gray-600">{fieldConfig.description}</p>
                      )}
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Mapping Configuration */}
        <div className="col-span-8">
          {activeField ? (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">
                  Configure Mapping for "{activeField}"
                </CardTitle>
                <CardDescription>
                  {requiredFields[activeField]?.description || 'Select how to populate this field'}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Tabs defaultValue={mappings[activeField]?.type || MappingType.DIRECT}>
                  <TabsList className="grid w-full grid-cols-4">
                    <TabsTrigger value={MappingType.DIRECT}>Direct</TabsTrigger>
                    <TabsTrigger value={MappingType.CALCULATED}>Calculated</TabsTrigger>
                    <TabsTrigger value={MappingType.CONSTANT}>Constant</TabsTrigger>
                    <TabsTrigger value={MappingType.TRANSFORMATION}>Transform</TabsTrigger>
                  </TabsList>

                  <TabsContent value={MappingType.DIRECT} className="space-y-4">
                    <div>
                      <Label>Source Column</Label>
                      <Select
                        value={mappings[activeField]?.source_field || ''}
                        onValueChange={(value) =>
                          handleFieldMapping(activeField, {
                            type: MappingType.DIRECT,
                            source_field: value,
                            data_type: getFieldDataType(value),
                          })
                        }
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select a column" />
                        </SelectTrigger>
                        <SelectContent>
                          {availableColumns.map((col) => (
                            <SelectItem key={col.name} value={col.name}>
                              <div className="flex items-center justify-between w-full">
                                <div className="flex items-center gap-2">
                                  {React.createElement(DATA_TYPE_ICONS[col.type as keyof typeof DATA_TYPE_ICONS] || FileText, {
                                    className: "h-4 w-4",
                                  })}
                                  <span>{col.name}</span>
                                </div>
                                <Badge variant="outline" className="ml-2">
                                  {DATA_TYPE_LABELS[col.type as keyof typeof DATA_TYPE_LABELS] || 'Unknown'}
                                </Badge>
                              </div>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    {/* Show sample values */}
                    {mappings[activeField]?.source_field && (
                      <div>
                        <Label>Sample Values</Label>
                        <div className="flex flex-wrap gap-2 mt-2">
                          {availableColumns
                            .find((col) => col.name === mappings[activeField].source_field)
                            ?.sample_values.slice(0, 5)
                            .map((value: any, idx: number) => (
                              <Badge key={idx} variant="secondary">
                                {String(value)}
                              </Badge>
                            ))}
                        </div>
                      </div>
                    )}
                  </TabsContent>

                  <TabsContent value={MappingType.CALCULATED} className="space-y-4">
                    <Alert>
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription>
                        Define an expression using column names wrapped in curly braces.
                        Example: {'{first_name} + " " + {last_name}'}
                      </AlertDescription>
                    </Alert>
                    <div>
                      <Label>Expression</Label>
                      <Input
                        placeholder="Enter expression..."
                        value={mappings[activeField]?.expression || ''}
                        onChange={(e) =>
                          handleFieldMapping(activeField, {
                            type: MappingType.CALCULATED,
                            expression: e.target.value,
                            data_type: requiredFields[activeField].data_type,
                          })
                        }
                      />
                    </div>
                  </TabsContent>

                  <TabsContent value={MappingType.CONSTANT} className="space-y-4">
                    <div>
                      <Label>Constant Value</Label>
                      <Input
                        placeholder="Enter constant value..."
                        value={mappings[activeField]?.constant_value || ''}
                        onChange={(e) =>
                          handleFieldMapping(activeField, {
                            type: MappingType.CONSTANT,
                            constant_value: e.target.value,
                            data_type: requiredFields[activeField].data_type,
                          })
                        }
                      />
                    </div>
                  </TabsContent>

                  <TabsContent value={MappingType.TRANSFORMATION} className="space-y-4">
                    <Alert>
                      <GitBranch className="h-4 w-4" />
                      <AlertDescription>
                        This field will be populated by a transformation pipeline.
                        Configure the pipeline separately.
                      </AlertDescription>
                    </Alert>
                  </TabsContent>
                </Tabs>

                {/* Suggestions */}
                {showSuggestions && suggestions && (
                  <div className="mt-6">
                    <Label className="flex items-center gap-2">
                      <Sparkles className="h-4 w-4 text-yellow-500" />
                      AI Suggestions
                    </Label>
                    <div className="mt-2 space-y-2">
                      {suggestions
                        .filter((s) => s.field_name === activeField)
                        .map((suggestion, idx) => (
                          <div
                            key={idx}
                            className="p-3 border rounded-lg cursor-pointer hover:bg-gray-50"
                            onClick={() => {
                              const [dataset, field] = suggestion.suggested_source_field.split('.');
                              if (dataset !== selectedDataset) {
                                setSelectedDataset(dataset);
                              }
                              handleFieldMapping(activeField, {
                                type: MappingType.DIRECT,
                                source_field: field,
                                data_type: getFieldDataType(field),
                              });
                            }}
                          >
                            <div className="flex items-center justify-between">
                              <div>
                                <p className="font-medium">{suggestion.suggested_source_field}</p>
                                <p className="text-xs text-gray-500">{suggestion.reason}</p>
                              </div>
                              <Badge
                                variant={suggestion.confidence > 0.8 ? 'default' : 'secondary'}
                              >
                                {Math.round(suggestion.confidence * 100)}% match
                              </Badge>
                            </div>
                          </div>
                        ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="flex items-center justify-center h-64">
                <div className="text-center text-gray-500">
                  <Database className="h-12 w-12 mx-auto mb-4" />
                  <p>Select a field from the left to configure its mapping</p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Validation Results */}
      {validateMappingMutation.data && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Validation Results</CardTitle>
          </CardHeader>
          <CardContent>
            {validateMappingMutation.data.is_valid ? (
              <Alert>
                <CheckCircle className="h-4 w-4 text-green-600" />
                <AlertDescription>
                  All mappings are valid. You can proceed to save the configuration.
                </AlertDescription>
              </Alert>
            ) : (
              <div className="space-y-2">
                {validateMappingMutation.data.errors.map((error, idx) => (
                  <Alert key={idx} variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                ))}
                {validateMappingMutation.data.warnings.map((warning, idx) => (
                  <Alert key={idx}>
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>{warning}</AlertDescription>
                  </Alert>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Actions */}
      <div className="flex justify-between">
        <Button variant="outline" onClick={handleValidate}>
          Validate Mappings
        </Button>
        <Button
          onClick={handleSave}
          disabled={completeness < 100 || saveMappingMutation.isPending}
        >
          {saveMappingMutation.isPending ? 'Saving...' : 'Save Configuration'}
        </Button>
      </div>
    </div>
  );
}