// ABOUTME: Widget mapping dialog for mapping uploaded data columns to widget fields
// ABOUTME: Simple dropdown-based mapping interface with automatic suggestions

import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  MapPin,
  Save,
  AlertCircle,
  CheckCircle,
  Sparkles,
  Database,
  Link2,
  Loader2
} from 'lucide-react';
import { useToast } from '@/components/ui/use-toast';

interface WidgetMappingDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  widgetId: string;
  widgetName: string;
  widgetType: string;
  studyId: string;
  onMappingComplete?: () => void;
}

interface DatasetInfo {
  upload_id: string;
  dataset_name: string;
  columns: Array<{ name: string; type: string }>;
  row_count: number;
  version: number;
  uploaded_at: string;
}

interface WidgetRequirements {
  required: string[];
  optional: string[];
}

interface MappingOptions {
  widget: {
    id: string;
    name: string;
    type: string;
    requirements: WidgetRequirements;
  };
  available_datasets: DatasetInfo[];
  current_mappings: any;
}

export function WidgetMappingDialog({
  open,
  onOpenChange,
  widgetId,
  widgetName,
  widgetType,
  studyId,
  onMappingComplete
}: WidgetMappingDialogProps) {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [mappingOptions, setMappingOptions] = useState<MappingOptions | null>(null);
  const [selectedDataset, setSelectedDataset] = useState<DatasetInfo | null>(null);
  const [fieldMappings, setFieldMappings] = useState<Record<string, string>>({});
  const [suggestions, setSuggestions] = useState<Record<string, string>>({});
  const [validationResult, setValidationResult] = useState<any>(null);
  const { toast } = useToast();

  useEffect(() => {
    if (open) {
      fetchMappingOptions();
    }
  }, [open, widgetId, studyId]);

  const fetchMappingOptions = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/v1/data/studies/${studyId}/widgets/${widgetId}/mapping-options`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setMappingOptions(data);
        
        // If there are current mappings, load them
        if (data.current_mappings) {
          setFieldMappings(data.current_mappings.field_mappings);
          // Find and select the dataset
          const dataset = data.available_datasets.find(
            (d: DatasetInfo) => d.dataset_name === data.current_mappings.dataset_name
          );
          if (dataset) {
            setSelectedDataset(dataset);
          }
        }
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to fetch mapping options',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleDatasetChange = async (datasetName: string) => {
    const dataset = mappingOptions?.available_datasets.find(d => d.dataset_name === datasetName);
    if (dataset) {
      setSelectedDataset(dataset);
      
      // Get automatic suggestions
      try {
        const response = await fetch('/api/v1/data/mappings/suggest', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            widget_type: widgetType,
            dataset_columns: dataset.columns
          })
        });

        if (response.ok) {
          const suggestedMappings = await response.json();
          setSuggestions(suggestedMappings);
          // Apply suggestions if no existing mappings
          if (Object.keys(fieldMappings).length === 0) {
            setFieldMappings(suggestedMappings);
          }
        }
      } catch (error) {
        console.error('Failed to get suggestions:', error);
      }
    }
  };

  const handleFieldMapping = (field: string, column: string) => {
    setFieldMappings(prev => ({
      ...prev,
      [field]: column
    }));
  };

  const validateMapping = async () => {
    if (!selectedDataset) return;

    try {
      const response = await fetch('/api/v1/data/mappings/validate', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          widget_type: widgetType,
          dataset_columns: selectedDataset.columns.map(c => c.name),
          field_mappings: fieldMappings
        })
      });

      if (response.ok) {
        const result = await response.json();
        setValidationResult(result);
        return result.is_valid;
      }
    } catch (error) {
      console.error('Validation failed:', error);
    }
    return false;
  };

  const handleSave = async () => {
    if (!selectedDataset) return;

    // Validate first
    const isValid = await validateMapping();
    if (!isValid) {
      toast({
        title: 'Invalid mapping',
        description: 'Please complete all required field mappings',
        variant: 'destructive',
      });
      return;
    }

    setSaving(true);

    try {
      const response = await fetch(`/api/v1/data/widgets/${widgetId}/mapping`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          widget_id: widgetId,
          upload_id: selectedDataset.upload_id,
          dataset_name: selectedDataset.dataset_name,
          field_mappings: fieldMappings
        })
      });

      if (response.ok) {
        toast({
          title: 'Mapping saved',
          description: 'Widget data mapping has been configured successfully',
        });
        
        onOpenChange(false);
        if (onMappingComplete) {
          onMappingComplete();
        }
      } else {
        throw new Error('Failed to save mapping');
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to save mapping',
        variant: 'destructive',
      });
    } finally {
      setSaving(false);
    }
  };

  const getFieldBadgeVariant = (field: string, isRequired: boolean) => {
    if (fieldMappings[field]) return 'default';
    if (isRequired) return 'destructive';
    return 'outline';
  };

  if (loading) {
    return (
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent>
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-8 w-8 animate-spin" />
          </div>
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <DialogTitle>Configure Widget Data Mapping</DialogTitle>
          <DialogDescription>
            Map data columns from your uploaded datasets to widget fields for "{widgetName}"
          </DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="mapping" className="mt-4">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="mapping">Field Mapping</TabsTrigger>
            <TabsTrigger value="validation">Validation</TabsTrigger>
          </TabsList>

          <TabsContent value="mapping" className="space-y-4">
            {/* Dataset Selection */}
            <div className="space-y-2">
              <Label htmlFor="dataset">Select Dataset</Label>
              <Select
                value={selectedDataset?.dataset_name}
                onValueChange={handleDatasetChange}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Choose a dataset to map" />
                </SelectTrigger>
                <SelectContent>
                  {mappingOptions?.available_datasets.map(dataset => (
                    <SelectItem key={dataset.dataset_name} value={dataset.dataset_name}>
                      <div className="flex items-center justify-between w-full">
                        <span>{dataset.dataset_name}</span>
                        <div className="flex gap-2 ml-2">
                          <Badge variant="secondary" className="text-xs">
                            v{dataset.version}
                          </Badge>
                          <Badge variant="outline" className="text-xs">
                            {dataset.row_count} rows
                          </Badge>
                        </div>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {selectedDataset && (
              <>
                {/* Required Fields */}
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <Label>Required Fields</Label>
                    <Badge variant="destructive" className="text-xs">Required</Badge>
                  </div>
                  <div className="space-y-2">
                    {mappingOptions?.widget.requirements.required.map(field => (
                      <div key={field} className="grid grid-cols-2 gap-4 items-center">
                        <div className="flex items-center gap-2">
                          <Badge variant={getFieldBadgeVariant(field, true)}>
                            {field}
                          </Badge>
                          {suggestions[field] && (
                            <Sparkles className="h-3 w-3 text-muted-foreground" />
                          )}
                        </div>
                        <Select
                          value={fieldMappings[field] || ''}
                          onValueChange={(value) => handleFieldMapping(field, value)}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Select column" />
                          </SelectTrigger>
                          <SelectContent>
                            {selectedDataset.columns.map(col => (
                              <SelectItem key={col.name} value={col.name}>
                                <div className="flex items-center justify-between w-full">
                                  <span>{col.name}</span>
                                  <Badge variant="outline" className="text-xs ml-2">
                                    {col.type}
                                  </Badge>
                                </div>
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Optional Fields */}
                {mappingOptions?.widget.requirements.optional && mappingOptions.widget.requirements.optional.length > 0 && (
                  <div className="space-y-3">
                    <div className="flex items-center gap-2">
                      <Label>Optional Fields</Label>
                      <Badge variant="secondary" className="text-xs">Optional</Badge>
                    </div>
                    <div className="space-y-2">
                      {mappingOptions.widget.requirements.optional.map(field => (
                        <div key={field} className="grid grid-cols-2 gap-4 items-center">
                          <div className="flex items-center gap-2">
                            <Badge variant={getFieldBadgeVariant(field, false)}>
                              {field}
                            </Badge>
                            {suggestions[field] && (
                              <Sparkles className="h-3 w-3 text-muted-foreground" />
                            )}
                          </div>
                          <Select
                            value={fieldMappings[field] || ''}
                            onValueChange={(value) => handleFieldMapping(field, value)}
                          >
                            <SelectTrigger>
                              <SelectValue placeholder="Select column (optional)" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="">None</SelectItem>
                              {selectedDataset.columns.map(col => (
                                <SelectItem key={col.name} value={col.name}>
                                  <div className="flex items-center justify-between w-full">
                                    <span>{col.name}</span>
                                    <Badge variant="outline" className="text-xs ml-2">
                                      {col.type}
                                    </Badge>
                                  </div>
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Dataset Info */}
                <Alert>
                  <Database className="h-4 w-4" />
                  <AlertDescription>
                    <strong>Dataset Info:</strong> {selectedDataset.row_count} rows, {selectedDataset.columns.length} columns
                    <br />
                    <strong>Version:</strong> {selectedDataset.version} (uploaded {new Date(selectedDataset.uploaded_at).toLocaleDateString()})
                  </AlertDescription>
                </Alert>
              </>
            )}
          </TabsContent>

          <TabsContent value="validation" className="space-y-4">
            {validationResult ? (
              <div className="space-y-4">
                {validationResult.is_valid ? (
                  <Alert>
                    <CheckCircle className="h-4 w-4" />
                    <AlertDescription>
                      All required fields are properly mapped. The configuration is valid.
                    </AlertDescription>
                  </Alert>
                ) : (
                  <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>
                      Mapping validation failed. Please check the issues below.
                    </AlertDescription>
                  </Alert>
                )}

                {validationResult.missing_required?.length > 0 && (
                  <div className="space-y-2">
                    <Label>Missing Required Fields</Label>
                    <div className="flex flex-wrap gap-2">
                      {validationResult.missing_required.map((field: string) => (
                        <Badge key={field} variant="destructive">
                          {field}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                {validationResult.warnings?.length > 0 && (
                  <div className="space-y-2">
                    <Label>Warnings</Label>
                    {validationResult.warnings.map((warning: string, idx: number) => (
                      <Alert key={idx}>
                        <AlertCircle className="h-4 w-4" />
                        <AlertDescription>{warning}</AlertDescription>
                      </Alert>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  Select a dataset and configure field mappings to validate the configuration.
                </AlertDescription>
              </Alert>
            )}
          </TabsContent>
        </Tabs>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={saving}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSave}
            disabled={!selectedDataset || Object.keys(fieldMappings).length === 0 || saving}
          >
            {saving ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="mr-2 h-4 w-4" />
                Save Mapping
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}