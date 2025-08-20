// ABOUTME: Field mapping step for study initialization wizard
// ABOUTME: Maps uploaded data fields to template widget requirements with dropdowns

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Skeleton } from '@/components/ui/skeleton';
import { Checkbox } from '@/components/ui/checkbox';
import { Separator } from '@/components/ui/separator';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { useToast } from '@/hooks/use-toast';
import { studiesApi } from '@/lib/api/studies';
import {
  ChevronRight,
  Database,
  Link2,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Info,
  Sparkles,
  ArrowRight,
  FileSpreadsheet,
  Columns,
  Filter,
  Plus
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { FilterBuilder } from '@/components/filters/FilterBuilder';

interface FieldMappingStepProps {
  studyId: string | null;
  data: {
    templateId?: string;
    uploadedFiles?: any[];
  };
  onComplete: (data: {
    mappings: Record<string, any>;
    filters?: Record<string, any>;
    acceptAutoMappings: boolean;
  }) => void;
  isLoading?: boolean;
  mode?: 'create' | 'edit';
  existingStudy?: any;
}

interface TemplateRequirement {
  widget_id: string;
  widget_title: string;
  widget_type: string;
  required_fields: string[];
  data_requirements: any;
}

interface DatasetSchema {
  dataset_name: string;
  columns: string[];
  row_count: number;
  column_count: number;
}

interface FieldMapping {
  dataset: string;
  column: string;
  confidence?: number;
  filter?: {
    expression: string;
    isValid: boolean;
    validationMessage?: string;
  };
}

export function FieldMappingStep({
  studyId,
  data,
  onComplete,
  isLoading,
  mode = 'create',
  existingStudy
}: FieldMappingStepProps) {
  const { toast } = useToast();
  const [isLoadingData, setIsLoadingData] = useState(true);
  const [templateRequirements, setTemplateRequirements] = useState<TemplateRequirement[]>([]);
  const [datasetSchemas, setDatasetSchemas] = useState<DatasetSchema[]>([]);
  const [mappings, setMappings] = useState<Record<string, Record<string, FieldMapping>>>({});
  const [autoMappingSuggestions, setAutoMappingSuggestions] = useState<Record<string, any>>({});
  const [acceptAutoMappings, setAcceptAutoMappings] = useState(true);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [filterDialogOpen, setFilterDialogOpen] = useState(false);
  const [activeFilterWidget, setActiveFilterWidget] = useState<{ widgetId: string; field: string } | null>(null);
  const [widgetFilters, setWidgetFilters] = useState<Record<string, string>>({});

  useEffect(() => {
    loadMappingData();
  }, [studyId, mode, existingStudy]);

  const loadMappingData = async () => {
    if (!studyId) {
      setIsLoadingData(false);
      return;
    }

    try {
      setIsLoadingData(true);
      
      console.log('[FieldMapping] Loading data for study:', studyId, 'mode:', mode);
      console.log('[FieldMapping] Existing study data:', existingStudy);
      
      // Get mapping data from the proper endpoint
      const mappingData = await studiesApi.getMappingData(studyId);
      console.log('[FieldMapping] Mapping data received:', mappingData);
      
      // Extract dataset schemas
      if (mappingData?.dataset_schemas) {
        const schemas: DatasetSchema[] = Object.entries(mappingData.dataset_schemas).map(([name, schema]: [string, any]) => ({
          dataset_name: name,
          columns: Object.keys(schema.columns || {}),
          row_count: schema.row_count || 0,
          column_count: schema.column_count || Object.keys(schema.columns || {}).length
        }));
        console.log('[FieldMapping] Dataset schemas extracted:', schemas);
        setDatasetSchemas(schemas);
      } else {
        console.log('[FieldMapping] No dataset schemas in response');
      }
      
      // Set template requirements with proper structure
      if (mappingData?.template_requirements) {
        const formattedRequirements = mappingData.template_requirements.map((req: any) => ({
          ...req,
          required_fields: req.required_fields || [],
          optional_fields: req.optional_fields || []
        }));
        setTemplateRequirements(formattedRequirements);
        console.log('Template requirements loaded:', formattedRequirements);
      }
      
      // Load existing widget filters
      if (studyId) {
        try {
          const filtersResponse = await studiesApi.getAllWidgetFilters(studyId);
          if (Array.isArray(filtersResponse)) {
            const loadedFilters: Record<string, string> = {};
            filtersResponse.forEach((filterConfig: any) => {
              if (filterConfig?.widget_id && filterConfig?.expression) {
                // Store filter for all possible field keys that might be used
                // The field could be 'value', 'value_field', etc.
                loadedFilters[`${filterConfig.widget_id}_value`] = filterConfig.expression;
                loadedFilters[`${filterConfig.widget_id}_value_field`] = filterConfig.expression;
                // Also store without field suffix for widgets that save without field
                loadedFilters[filterConfig.widget_id] = filterConfig.expression;
              }
            });
            setWidgetFilters(loadedFilters);
            console.log('Loaded widget filters:', loadedFilters);
          }
        } catch (error) {
          console.error('Failed to load widget filters:', error);
        }
      }
      
      // Set auto-mapping suggestions
      if (mappingData?.mapping_suggestions) {
        setAutoMappingSuggestions(mappingData.mapping_suggestions);
        
        // Only initialize mappings with auto-suggestions if we're in create mode and accepted
        // In edit mode, we'll load existing mappings below
        if (acceptAutoMappings && mode !== 'edit') {
          const initialMappings: Record<string, Record<string, FieldMapping>> = {};
          
          Object.entries(mappingData.mapping_suggestions).forEach(([widgetId, suggestions]: [string, any]) => {
            initialMappings[widgetId] = {};
            
            // Handle both list and object formats
            if (Array.isArray(suggestions)) {
              // List format from backend
              suggestions.forEach((suggestion: any) => {
                if (suggestion.field_name && suggestion.suggested_column) {
                  initialMappings[widgetId][suggestion.field_name] = {
                    dataset: suggestion.suggested_dataset || '',
                    column: suggestion.suggested_column || '',
                    confidence: suggestion.confidence
                  };
                }
              });
            } else if (typeof suggestions === 'object') {
              // Object format
              Object.entries(suggestions).forEach(([field, mapping]: [string, any]) => {
                initialMappings[widgetId][field] = {
                  dataset: mapping.dataset || mapping.suggested_dataset || '',
                  column: mapping.column || mapping.suggested_column || '',
                  confidence: mapping.confidence
                };
              });
            }
          });
          
          setMappings(initialMappings);
        }
      }
      
      // In edit mode, also load existing field mappings
      if (mode === 'edit' && existingStudy?.field_mappings) {
        console.log('[FieldMapping] Loading existing mappings:', existingStudy.field_mappings);
        console.log('[FieldMapping] Template requirements:', mappingData.template_requirements);
        
        // Convert from flattened format to nested format if needed
        const existingMappings: Record<string, Record<string, FieldMapping>> = {};
        
        // For each template requirement, find its mapping
        if (mappingData?.template_requirements) {
          mappingData.template_requirements.forEach((req: any) => {
            const widgetId = req.widget_id;
            
            // Look for direct widget ID mapping
            if (existingStudy.field_mappings[widgetId]) {
              const mapping = existingStudy.field_mappings[widgetId];
              if (typeof mapping === 'string' && mapping.includes('.')) {
                const [dataset, column] = mapping.split('.');
                if (!existingMappings[widgetId]) {
                  existingMappings[widgetId] = {};
                }
                // Map to the first required field (usually 'value_field')
                const fieldName = req.required_fields?.[0] || 'value_field';
                existingMappings[widgetId][fieldName] = {
                  dataset,
                  column,
                  confidence: undefined
                };
                console.log(`[FieldMapping] Mapped widget ${widgetId} field ${fieldName} to ${dataset}.${column}`);
              }
            }
            
            // Also check for underscore-based mappings
            req.required_fields?.forEach((field: string) => {
              const mappingKey = `${widgetId}_${field}`;
              if (existingStudy.field_mappings[mappingKey]) {
                const mapping = existingStudy.field_mappings[mappingKey];
                if (typeof mapping === 'string' && mapping.includes('.')) {
                  const [dataset, column] = mapping.split('.');
                  if (!existingMappings[widgetId]) {
                    existingMappings[widgetId] = {};
                  }
                  existingMappings[widgetId][field] = {
                    dataset,
                    column,
                    confidence: undefined
                  };
                  console.log(`[FieldMapping] Mapped widget ${widgetId} field ${field} to ${dataset}.${column} (from underscore key)`);
                }
              }
            });
          });
        }
        
        if (Object.keys(existingMappings).length > 0) {
          console.log('[FieldMapping] Setting existing mappings:', existingMappings);
          setMappings(existingMappings);
        } else {
          console.log('[FieldMapping] No mappings found to set');
        }
      }
    } catch (error) {
      console.error('Failed to load mapping data:', error);
      toast({
        title: 'Error',
        description: 'Failed to load mapping information',
        variant: 'destructive'
      });
    } finally {
      setIsLoadingData(false);
    }
  };

  const handleFieldMapping = (widgetId: string, field: string, dataset: string, column: string) => {
    setMappings(prev => ({
      ...prev,
      [widgetId]: {
        ...prev[widgetId],
        [field]: {
          dataset,
          column,
          confidence: undefined // Clear confidence when manually mapped
        }
      }
    }));
    
    // Clear validation errors when user makes changes
    setValidationErrors([]);
  };

  const getConfidenceBadge = (confidence?: number) => {
    if (!confidence) return null;
    
    if (confidence >= 90) {
      return <Badge variant="default" className="bg-green-500">High Match</Badge>;
    } else if (confidence >= 70) {
      return <Badge variant="default" className="bg-yellow-500">Good Match</Badge>;
    } else {
      return <Badge variant="default" className="bg-orange-500">Possible Match</Badge>;
    }
  };

  const validateMappings = (): boolean => {
    const errors: string[] = [];
    
    templateRequirements.forEach(req => {
      (req.required_fields || []).forEach(field => {
        const mapping = mappings[req.widget_id]?.[field];
        if (!mapping?.dataset || !mapping?.column) {
          errors.push(`${req.widget_title}: ${field} is not mapped`);
        }
      });
    });
    
    setValidationErrors(errors);
    return errors.length === 0;
  };

  const handleComplete = () => {
    if (!acceptAutoMappings && !validateMappings()) {
      toast({
        title: 'Incomplete Mappings',
        description: 'Please map all required fields before continuing',
        variant: 'destructive'
      });
      return;
    }

    console.log('Field mapping complete. Mappings:', mappings);
    console.log('Accept auto mappings:', acceptAutoMappings);

    // Prepare filters for backend
    const filters: Record<string, any> = {};
    Object.entries(widgetFilters).forEach(([key, expression]) => {
      const [widgetId] = key.split('_');
      if (expression) {
        filters[widgetId] = {
          expression,
          enabled: true
        };
      }
    });

    // Return both nested (for Review display) and flat (for backend) structures
    onComplete({
      mappings: mappings,  // Keep nested structure for display
      filters: filters,  // Include filters
      flatMappings: (() => {
        // Create flat structure for backend
        const flat: Record<string, any> = {};
        Object.entries(mappings).forEach(([widgetId, widgetMappings]) => {
          Object.entries(widgetMappings).forEach(([field, mapping]) => {
            flat[`${widgetId}_${field}`] = mapping;
          });
        });
        return flat;
      })(),
      acceptAutoMappings
    });
  };

  if (isLoadingData) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-1/3" />
        <Skeleton className="h-64 w-full" />
        <Skeleton className="h-32 w-full" />
      </div>
    );
  }

  // Check if we have data to map
  const hasDatasets = datasetSchemas.length > 0;
  const hasRequirements = templateRequirements.length > 0;

  if (!hasDatasets) {
    return (
      <div className="space-y-6">
        <Alert className="border-orange-200 bg-orange-50 dark:border-orange-800 dark:bg-orange-900/20">
          <AlertCircle className="h-4 w-4 text-orange-600 dark:text-orange-400" />
          <AlertDescription>
            <div className="space-y-2">
              <p className="font-medium text-orange-900 dark:text-orange-100">
                No Data Available for Mapping
              </p>
              <p className="text-sm text-orange-800 dark:text-orange-200">
                Please go back to the Upload Data step and upload your clinical data files.
                The system needs to process your files to extract the data structure before mapping can be configured.
              </p>
            </div>
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium">Map Data Fields</h3>
        <p className="text-sm text-muted-foreground">
          Connect your uploaded data fields to the dashboard widget requirements
        </p>
      </div>

      {/* Debug info - remove after testing */}
      {mode === 'edit' && existingStudy?.field_mappings && (
        <div className="p-4 bg-gray-100 dark:bg-gray-800 rounded text-xs">
          <p className="font-bold mb-2">Debug: Existing Field Mappings</p>
          <pre>{JSON.stringify(existingStudy.field_mappings, null, 2)}</pre>
          <p className="font-bold mt-4 mb-2">Debug: Current Mappings State</p>
          <pre>{JSON.stringify(mappings, null, 2)}</pre>
        </div>
      )}

      {/* Dataset Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Database className="h-5 w-5" />
            Available Datasets
          </CardTitle>
          <CardDescription>
            Data extracted from your uploaded files
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3">
            {datasetSchemas.map((schema) => (
              <div key={schema.dataset_name} className="flex items-center justify-between p-3 border rounded-lg">
                <div className="flex items-center gap-3">
                  <FileSpreadsheet className="h-5 w-5 text-muted-foreground" />
                  <div>
                    <p className="font-medium">{schema.dataset_name}</p>
                    <p className="text-sm text-muted-foreground">
                      {schema.column_count} columns • {schema.row_count.toLocaleString()} rows
                    </p>
                  </div>
                </div>
                <Badge variant="secondary">
                  {schema.columns.length} fields
                </Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Auto-Mapping Toggle */}
      <Alert className="border-blue-200 bg-blue-50 dark:border-blue-800 dark:bg-blue-900/20">
        <Sparkles className="h-4 w-4 text-blue-600 dark:text-blue-400" />
        <AlertDescription>
          <div className="space-y-3">
            <p className="font-medium text-blue-900 dark:text-blue-100">
              Smart Mapping Assistant
            </p>
            <p className="text-sm text-blue-800 dark:text-blue-200">
              We've analyzed your data and suggested mappings based on common clinical data patterns.
              You can accept these suggestions or manually configure each mapping.
            </p>
            <div className="flex items-center gap-2">
              <Checkbox
                id="auto-mapping"
                checked={acceptAutoMappings}
                onCheckedChange={(checked) => setAcceptAutoMappings(checked as boolean)}
              />
              <Label 
                htmlFor="auto-mapping" 
                className="text-sm cursor-pointer text-blue-800 dark:text-blue-200"
              >
                Use smart mapping suggestions
              </Label>
            </div>
          </div>
        </AlertDescription>
      </Alert>

      {/* Field Mappings */}
      {hasRequirements ? (
        <div className="space-y-4">
          <h4 className="text-sm font-medium flex items-center gap-2">
            <Link2 className="h-4 w-4" />
            Widget Field Mappings
          </h4>
          
          {templateRequirements.map((requirement) => (
            <Card key={requirement.widget_id}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-base">{requirement.widget_title}</CardTitle>
                    <CardDescription className="text-xs mt-1">
                      Widget Type: {requirement.widget_type}
                    </CardDescription>
                  </div>
                  <Badge variant="outline">{(requirement.required_fields || []).length} fields</Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* Show required fields */}
                  {(requirement.required_fields || []).length > 0 ? (
                    (requirement.required_fields || []).map((field) => {
                      const currentMapping = mappings[requirement.widget_id]?.[field];
                      
                      // Find suggestion from list or object format
                      let suggestion = null;
                      const widgetSuggestions = autoMappingSuggestions[requirement.widget_id];
                      if (Array.isArray(widgetSuggestions)) {
                        suggestion = widgetSuggestions.find(s => s.field_name === field);
                      } else if (widgetSuggestions) {
                        suggestion = widgetSuggestions[field];
                      }
                      
                      return (
                        <div key={field} className="space-y-2">
                          <div className="flex items-center justify-between">
                            <Label className="text-sm font-medium flex items-center gap-2">
                              <Columns className="h-3 w-3" />
                              {field}
                              <Badge variant="destructive" className="text-xs">Required</Badge>
                            </Label>
                            {currentMapping?.confidence && getConfidenceBadge(currentMapping.confidence)}
                          </div>
                          
                          <div className="grid grid-cols-2 gap-2">
                            {/* Dataset Selection */}
                            <div>
                              <Label className="text-xs text-muted-foreground mb-1 block">
                                Dataset
                              </Label>
                              <Select
                                value={currentMapping?.dataset || ''}
                                onValueChange={(value) => {
                                  const firstColumn = datasetSchemas.find(d => d.dataset_name === value)?.columns[0] || '';
                                  handleFieldMapping(requirement.widget_id, field, value, firstColumn);
                                }}
                              >
                                <SelectTrigger className="w-full">
                                  <SelectValue placeholder="Select dataset" />
                                </SelectTrigger>
                                <SelectContent>
                                  {datasetSchemas.map((schema) => (
                                    <SelectItem key={schema.dataset_name} value={schema.dataset_name}>
                                      {schema.dataset_name}
                                    </SelectItem>
                                  ))}
                                </SelectContent>
                              </Select>
                            </div>
                            
                            {/* Column Selection */}
                            <div>
                              <Label className="text-xs text-muted-foreground mb-1 block">
                                Column
                              </Label>
                              <Select
                                value={currentMapping?.column || ''}
                                onValueChange={(value) => {
                                  handleFieldMapping(requirement.widget_id, field, currentMapping?.dataset || '', value);
                                }}
                                disabled={!currentMapping?.dataset}
                              >
                                <SelectTrigger className="w-full">
                                  <SelectValue placeholder="Select column" />
                              </SelectTrigger>
                              <SelectContent>
                                {datasetSchemas
                                  .find(s => s.dataset_name === currentMapping?.dataset)
                                  ?.columns.map((col) => (
                                    <SelectItem key={col} value={col}>
                                      {col}
                                    </SelectItem>
                                  ))}
                              </SelectContent>
                            </Select>
                          </div>
                          
                          {/* Filter Button */}
                          <div className="flex items-end">
                            <TooltipProvider>
                              <Tooltip>
                                <TooltipTrigger asChild>
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => {
                                      setActiveFilterWidget({ widgetId: requirement.widget_id, field });
                                      setFilterDialogOpen(true);
                                    }}
                                    disabled={!currentMapping?.dataset || !currentMapping?.column}
                                    className="h-9"
                                  >
                                    <Filter className="h-4 w-4" />
                                    {widgetFilters[`${requirement.widget_id}_${field}`] ? (
                                      <Badge variant="secondary" className="ml-1">Active</Badge>
                                    ) : null}
                                  </Button>
                                </TooltipTrigger>
                                <TooltipContent>
                                  <p>Add filter condition (optional)</p>
                                </TooltipContent>
                              </Tooltip>
                            </TooltipProvider>
                          </div>
                        </div>
                        
                        {/* Show filter if exists */}
                        {widgetFilters[`${requirement.widget_id}_${field}`] && (
                          <div className="mt-2 p-2 bg-muted rounded-md">
                            <p className="text-xs font-mono">
                              Filter: {widgetFilters[`${requirement.widget_id}_${field}`]}
                            </p>
                          </div>
                        )}
                        
                        {/* Show suggestion if available */}
                        {suggestion && acceptAutoMappings && (
                          <p className="text-xs text-muted-foreground flex items-center gap-1">
                            <Sparkles className="h-3 w-3" />
                            Auto-mapped to: {suggestion.suggested_dataset || suggestion.dataset}.{suggestion.suggested_column || suggestion.column}
                            {suggestion.candidates?.length > 1 && (
                              <span className="ml-1">(alternatives: {suggestion.candidates.slice(1).join(', ')})</span>
                            )}
                          </p>
                        )}
                      </div>
                    );
                  })
                  ) : (
                    <p className="text-sm text-muted-foreground">
                      No fields to map for this widget
                    </p>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Alert>
          <Info className="h-4 w-4" />
          <AlertDescription>
            No widget requirements found for the selected template.
            You can proceed without field mappings.
          </AlertDescription>
        </Alert>
      )}

      {/* Validation Errors */}
      {validationErrors.length > 0 && (
        <Alert className="border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/20">
          <AlertCircle className="h-4 w-4 text-red-600 dark:text-red-400" />
          <AlertDescription>
            <div className="space-y-1">
              <p className="font-medium text-red-900 dark:text-red-100">
                Missing Required Mappings:
              </p>
              <ul className="list-disc list-inside text-sm text-red-800 dark:text-red-200">
                {validationErrors.map((error, idx) => (
                  <li key={idx}>{error}</li>
                ))}
              </ul>
            </div>
          </AlertDescription>
        </Alert>
      )}

      {/* Actions */}
      <div className="flex justify-end pt-4 border-t">
        <Button 
          onClick={handleComplete}
          disabled={isLoading}
        >
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Processing...
            </>
          ) : (
            <>
              Next
              <ChevronRight className="ml-2 h-4 w-4" />
            </>
          )}
        </Button>
      </div>

      {/* Filter Dialog */}
      <Dialog open={filterDialogOpen} onOpenChange={setFilterDialogOpen}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Configure Widget Filter</DialogTitle>
            <DialogDescription>
              Add an optional SQL WHERE clause to filter the data for this widget
            </DialogDescription>
          </DialogHeader>
          
          {activeFilterWidget && studyId && (
            <FilterBuilder
              studyId={studyId}
              widgetId={activeFilterWidget.widgetId}
              datasetName={mappings[activeFilterWidget.widgetId]?.[activeFilterWidget.field]?.dataset || ''}
              columns={
                datasetSchemas.find(
                  s => s.dataset_name === mappings[activeFilterWidget.widgetId]?.[activeFilterWidget.field]?.dataset
                )?.columns || []
              }
              currentFilter={widgetFilters[`${activeFilterWidget.widgetId}_${activeFilterWidget.field}`] || ''}
              onSave={async (filter) => {
                setWidgetFilters(prev => ({
                  ...prev,
                  [`${activeFilterWidget.widgetId}_${activeFilterWidget.field}`]: filter
                }));
                
                // Update the mapping with filter info
                if (mappings[activeFilterWidget.widgetId]?.[activeFilterWidget.field]) {
                  const updatedMappings = { ...mappings };
                  updatedMappings[activeFilterWidget.widgetId][activeFilterWidget.field] = {
                    ...updatedMappings[activeFilterWidget.widgetId][activeFilterWidget.field],
                    filter: {
                      expression: filter,
                      isValid: true,
                      validationMessage: undefined
                    }
                  };
                  setMappings(updatedMappings);
                }
                
                // Save filter to backend
                if (studyId) {
                  try {
                    await studiesApi.saveWidgetFilter(studyId, activeFilterWidget.widgetId, {
                      expression: filter,
                      enabled: true
                    });
                  } catch (error) {
                    console.error('Failed to save filter to backend:', error);
                  }
                }
                
                setFilterDialogOpen(false);
                toast({
                  title: "Filter Applied",
                  description: "The filter has been applied and saved",
                });
              }}
              onCancel={() => setFilterDialogOpen(false)}
            />
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}