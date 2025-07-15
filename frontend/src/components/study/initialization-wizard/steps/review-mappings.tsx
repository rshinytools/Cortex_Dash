// ABOUTME: Review and mapping step for study initialization wizard
// ABOUTME: Shows auto-detected field mappings and allows customization

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useToast } from '@/hooks/use-toast';
import { studiesApi } from '@/lib/api/studies';
import { 
  CheckCircle2, 
  AlertCircle, 
  ArrowRight,
  Sparkles,
  Database,
  FileSpreadsheet,
  Rocket,
  Link2,
  ArrowDown
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface FieldMapping {
  widget_field: string;
  dataset: string;
  field: string;
  confidence: number;
  patterns: string[];
}

interface MappingSummary {
  total_widgets: number;
  mapped_widgets: number;
  unmapped_widgets: number;
  average_confidence: number;
  mappings: Record<string, FieldMapping[]>;
}

interface MappingData {
  dataset_schemas: Record<string, any>;
  template_requirements: any[];
  mapping_suggestions: Record<string, any[]>;
  total_datasets: number;
  total_columns: number;
  total_widgets: number;
}

interface ReviewMappingsStepProps {
  studyId: string | null;
  data: {
    acceptAutoMappings?: boolean;
    customMappings?: any;
  };
  onComplete: (data: {
    acceptAutoMappings: boolean;
    customMappings?: any;
  }) => void;
  isLoading?: boolean;
}

export function ReviewMappingsStep({
  studyId,
  data,
  onComplete,
  isLoading
}: ReviewMappingsStepProps) {
  const { toast } = useToast();
  const [acceptAutoMappings, setAcceptAutoMappings] = useState(
    data.acceptAutoMappings ?? true
  );
  const [mappingData, setMappingData] = useState<MappingData | null>(null);
  const [customMappings, setCustomMappings] = useState<Record<string, any>>({});
  const [isLoadingMappings, setIsLoadingMappings] = useState(true);

  useEffect(() => {
    // Fetch real mapping data from backend
    const loadMappings = async () => {
      if (!studyId) {
        setIsLoadingMappings(false);
        return;
      }
      
      try {
        const response = await studiesApi.getMappingData(studyId);
        setMappingData(response);
        
        // Initialize custom mappings from suggestions
        const initialMappings: Record<string, any> = {};
        Object.entries(response.mapping_suggestions).forEach(([widgetId, suggestions]) => {
          initialMappings[widgetId] = {};
          (suggestions as any[]).forEach((suggestion: any) => {
            if (suggestion.suggested_column && suggestion.confidence > 0.7) {
              initialMappings[widgetId][suggestion.field_name] = {
                dataset: suggestion.suggested_dataset,
                column: suggestion.suggested_column
              };
            }
          });
        });
        setCustomMappings(initialMappings);
      } catch (error) {
        console.error('Error loading mappings:', error);
        toast({
          title: 'Error',
          description: 'Failed to load mapping data',
          variant: 'destructive',
        });
      } finally {
        setIsLoadingMappings(false);
      }
    };
    
    loadMappings();
  }, [studyId, toast]);

  const handleComplete = () => {
    onComplete({
      acceptAutoMappings,
      customMappings: customMappings
    });
  };

  const getConfidenceBadge = (confidence: number) => {
    if (confidence >= 0.9) {
      return <Badge className="bg-green-500 text-white">High</Badge>;
    } else if (confidence >= 0.7) {
      return <Badge className="bg-yellow-500 text-white">Medium</Badge>;
    } else {
      return <Badge className="bg-red-500 text-white">Low</Badge>;
    }
  };

  if (isLoadingMappings) {
    return (
      <div className="space-y-6">
        <div>
          <h3 className="text-lg font-medium">Review Field Mappings</h3>
          <p className="text-sm text-muted-foreground">
            Analyzing your data structure...
          </p>
        </div>
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-24 w-full" />
          ))}
        </div>
      </div>
    );
  }

  // Show message if no mapping data
  if (!mappingData || mappingData.total_widgets === 0) {
    return (
      <div className="space-y-6">
        <div>
          <h3 className="text-lg font-medium">Review & Activate</h3>
          <p className="text-sm text-muted-foreground">
            Complete the study initialization
          </p>
        </div>
        
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            No data requirements found in the selected template. You can proceed with activation.
          </AlertDescription>
        </Alert>
        
        <div className="flex justify-end gap-2">
          <Button onClick={handleComplete}>
            Complete Setup
            <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium">Review & Activate</h3>
        <p className="text-sm text-muted-foreground">
          Review the auto-detected field mappings and activate your study
        </p>
      </div>

      {/* Data Summary */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-yellow-500" />
            Data Schema Summary
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-2xl font-bold">{mappingData.total_datasets}</p>
              <p className="text-xs text-muted-foreground">Datasets Found</p>
            </div>
            <div>
              <p className="text-2xl font-bold">{mappingData.total_columns}</p>
              <p className="text-xs text-muted-foreground">Total Columns</p>
            </div>
            <div>
              <p className="text-2xl font-bold">{mappingData.total_widgets}</p>
              <p className="text-xs text-muted-foreground">Widgets to Map</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-green-600">
                {Object.values(customMappings).filter(m => Object.keys(m).length > 0).length}
              </p>
              <p className="text-xs text-muted-foreground">Mapped</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Field Mappings */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-medium">Field Mappings</h4>
          <Badge variant="outline">
            {acceptAutoMappings ? 'Auto-mapping enabled' : 'Manual mapping'}
          </Badge>
        </div>
        <ScrollArea className="h-[400px]">
          <div className="space-y-4">
            {mappingData.template_requirements.map((requirement) => {
              const widgetMappings = mappingData.mapping_suggestions[requirement.widget_id] || [];
              const widgetCustomMappings = customMappings[requirement.widget_id] || {};
              
              return (
                <Card key={requirement.widget_id} className="p-4">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <h5 className="font-medium">{requirement.widget_title}</h5>
                      <Badge variant="secondary">{requirement.widget_type}</Badge>
                    </div>
                    
                    <div className="space-y-2">
                      {widgetMappings.map((suggestion) => {
                        const mapping = widgetCustomMappings[suggestion.field_name];
                        const hasMapping = mapping && mapping.column;
                        
                        return (
                          <div key={suggestion.field_name} className="border rounded-lg p-3">
                            <div className="flex items-center justify-between mb-2">
                              <div className="flex items-center gap-2">
                                <span className="font-medium text-sm">
                                  {suggestion.field_name}
                                </span>
                                {suggestion.confidence > 0 && getConfidenceBadge(suggestion.confidence)}
                              </div>
                              {hasMapping && (
                                <CheckCircle2 className="h-4 w-4 text-green-500" />
                              )}
                            </div>
                            
                            <div className="flex items-center gap-2 text-sm">
                              <Database className="h-4 w-4 text-muted-foreground" />
                              {hasMapping ? (
                                <>
                                  <span className="text-muted-foreground">Mapped to:</span>
                                  <code className="px-2 py-1 bg-muted rounded">
                                    {mapping.dataset}.{mapping.column}
                                  </code>
                                </>
                              ) : suggestion.suggested_column ? (
                                <>
                                  <span className="text-muted-foreground">Suggested:</span>
                                  <code className="px-2 py-1 bg-muted rounded">
                                    {suggestion.suggested_dataset}.{suggestion.suggested_column}
                                  </code>
                                  <span className="text-xs text-muted-foreground">
                                    ({suggestion.reason})
                                  </span>
                                </>
                              ) : (
                                <span className="text-muted-foreground italic">
                                  No matching column found
                                </span>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </Card>
              );
            })}
          </div>
        </ScrollArea>
      </div>
      
      {/* Available Datasets */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Available Datasets</CardTitle>
          <CardDescription>
            Columns extracted from your uploaded files
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {Object.entries(mappingData.dataset_schemas).map(([datasetName, schema]: [string, any]) => (
              <div key={datasetName} className="flex items-center justify-between p-2 border rounded">
                <div className="flex items-center gap-2">
                  <FileSpreadsheet className="h-4 w-4 text-muted-foreground" />
                  <span className="font-medium">{datasetName}</span>
                  <Badge variant="outline">{schema.column_count} columns</Badge>
                </div>
                <span className="text-sm text-muted-foreground">
                  {schema.row_count} rows
                </span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Auto Mapping Toggle */}
      <Card>
        <CardContent className="flex items-center justify-between p-4">
          <div className="space-y-0.5">
            <Label htmlFor="auto-mappings" className="text-base">
              Accept Auto-Detected Mappings
            </Label>
            <p className="text-sm text-muted-foreground">
              Use the smart field mappings detected by the system
            </p>
          </div>
          <Switch
            id="auto-mappings"
            checked={acceptAutoMappings}
            onCheckedChange={setAcceptAutoMappings}
          />
        </CardContent>
      </Card>

      {/* Info Alert */}
      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          You can customize field mappings after initialization if needed. The system will continuously improve mapping accuracy as you use it.
        </AlertDescription>
      </Alert>

      {/* Ready to Launch */}
      <Card className="border-green-200 bg-green-50">
        <CardContent className="flex items-center gap-4 p-6">
          <CheckCircle2 className="h-8 w-8 text-green-600" />
          <div className="flex-1">
            <h4 className="font-medium">Ready to Initialize!</h4>
            <p className="text-sm text-muted-foreground">
              Your study will be initialized with the selected template and data mappings
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Complete Button */}
      <div className="flex justify-end pt-4 border-t">
        <Button 
          onClick={handleComplete}
          disabled={isLoading}
          size="lg"
          className="gap-2"
        >
          <Rocket className="h-4 w-4" />
          Initialize Study
        </Button>
      </div>
    </div>
  );
}