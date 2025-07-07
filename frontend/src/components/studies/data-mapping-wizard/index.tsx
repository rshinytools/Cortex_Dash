// ABOUTME: Data mapping wizard component for mapping study fields to template requirements
// ABOUTME: Provides auto-mapping suggestions and validation for field mappings

'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Info, AlertCircle, CheckCircle, ArrowRight, Sparkles } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface DataFieldRequirement {
  dataset: string;
  field: string;
  description: string;
  required: boolean;
  example?: string;
}

export interface FieldMapping {
  templateField: string;
  studyField: string;
}

export interface DataMappingWizardProps {
  templateId: string;
  templateName: string;
  dataRequirements: DataFieldRequirement[];
  availableStudyFields: string[];
  initialMappings?: Record<string, string>;
  onMappingsChange: (mappings: Record<string, string>) => void;
  onValidate?: (mappings: Record<string, string>) => Promise<{
    isValid: boolean;
    missingMappings: string[];
    suggestedMappings: Record<string, string>;
    warnings: string[];
  }>;
}

export function DataMappingWizard({
  templateId,
  templateName,
  dataRequirements,
  availableStudyFields,
  initialMappings = {},
  onMappingsChange,
  onValidate
}: DataMappingWizardProps) {
  const [mappings, setMappings] = useState<Record<string, string>>(initialMappings);
  const [suggestedMappings, setSuggestedMappings] = useState<Record<string, string>>({});
  const [validationResult, setValidationResult] = useState<{
    isValid: boolean;
    warnings: string[];
  } | null>(null);
  const [isValidating, setIsValidating] = useState(false);
  const [autoMappingApplied, setAutoMappingApplied] = useState(false);

  // Group requirements by dataset
  const groupedRequirements = dataRequirements.reduce((acc, req) => {
    const key = req.dataset;
    if (!acc[key]) {
      acc[key] = [];
    }
    acc[key].push(req);
    return acc;
  }, {} as Record<string, DataFieldRequirement[]>);

  // Auto-suggest mappings based on field names
  const generateAutoMappings = () => {
    const suggestions: Record<string, string> = {};
    
    dataRequirements.forEach(req => {
      const templateField = `${req.dataset}.${req.field}`;
      const fieldUpper = req.field.toUpperCase();
      
      // Look for exact matches first (case-insensitive)
      const exactMatch = availableStudyFields.find(f => 
        f.toUpperCase() === fieldUpper
      );
      
      if (exactMatch) {
        suggestions[templateField] = exactMatch;
        return;
      }
      
      // Common SDTM field mappings
      const commonMappings: Record<string, string[]> = {
        'USUBJID': ['subject_id', 'patient_id', 'subj_id'],
        'VISITNUM': ['visit_number', 'visit_num', 'visit'],
        'VISITDAT': ['visit_date', 'visitdt', 'date'],
        'AGE': ['age', 'patient_age'],
        'SEX': ['sex', 'gender'],
        'RACE': ['race', 'ethnicity'],
        'AETERM': ['adverse_event', 'ae_term', 'event'],
        'AESEV': ['severity', 'ae_severity', 'sev']
      };
      
      // Check common mappings
      if (commonMappings[fieldUpper]) {
        const studyField = availableStudyFields.find(f => 
          commonMappings[fieldUpper].some(m => 
            f.toLowerCase().includes(m)
          )
        );
        if (studyField) {
          suggestions[templateField] = studyField;
        }
      }
    });
    
    setSuggestedMappings(suggestions);
    return suggestions;
  };

  // Apply auto-mapped suggestions
  const applyAutoMappings = () => {
    const newMappings = { ...mappings, ...suggestedMappings };
    setMappings(newMappings);
    onMappingsChange(newMappings);
    setAutoMappingApplied(true);
  };

  // Handle field mapping change
  const handleMappingChange = (templateField: string, studyField: string) => {
    const newMappings = {
      ...mappings,
      [templateField]: studyField
    };
    
    if (!studyField) {
      delete newMappings[templateField];
    }
    
    setMappings(newMappings);
    onMappingsChange(newMappings);
  };

  // Validate mappings
  const validateMappings = async () => {
    if (!onValidate) return;
    
    setIsValidating(true);
    try {
      const result = await onValidate(mappings);
      setValidationResult({
        isValid: result.isValid,
        warnings: result.warnings
      });
      
      // Update suggested mappings with validation results
      if (result.suggestedMappings) {
        setSuggestedMappings(prev => ({
          ...prev,
          ...result.suggestedMappings
        }));
      }
    } catch (error) {
      console.error('Validation error:', error);
    } finally {
      setIsValidating(false);
    }
  };

  // Generate suggestions on mount
  useEffect(() => {
    if (!autoMappingApplied && Object.keys(mappings).length === 0) {
      generateAutoMappings();
    }
  }, [dataRequirements, availableStudyFields]);

  // Count mapped fields
  const requiredFields = dataRequirements.filter(r => r.required);
  const mappedRequiredCount = requiredFields.filter(r => {
    const key = `${r.dataset}.${r.field}`;
    return mappings[key];
  }).length;
  const completionPercentage = Math.round((mappedRequiredCount / requiredFields.length) * 100);

  return (
    <div className="space-y-6">
      {/* Progress indicator */}
      <Card>
        <CardContent className="pt-6">
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>Mapping Progress</span>
              <span className="font-medium">{completionPercentage}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-primary h-2 rounded-full transition-all"
                style={{ width: `${completionPercentage}%` }}
              />
            </div>
            <p className="text-sm text-muted-foreground">
              {mappedRequiredCount} of {requiredFields.length} required fields mapped
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Auto-mapping suggestions */}
      {Object.keys(suggestedMappings).length > 0 && !autoMappingApplied && (
        <Alert>
          <Sparkles className="h-4 w-4" />
          <AlertDescription className="space-y-2">
            <p>We found {Object.keys(suggestedMappings).length} potential auto-mappings based on field names.</p>
            <Button 
              size="sm" 
              onClick={applyAutoMappings}
              className="mt-2"
            >
              Apply Auto-mappings
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Validation result */}
      {validationResult && (
        <Alert className={validationResult.isValid ? 'border-green-500' : 'border-yellow-500'}>
          {validationResult.isValid ? (
            <CheckCircle className="h-4 w-4 text-green-500" />
          ) : (
            <AlertCircle className="h-4 w-4 text-yellow-500" />
          )}
          <AlertDescription>
            {validationResult.isValid ? (
              'All required fields are mapped correctly.'
            ) : (
              <ul className="list-disc list-inside space-y-1">
                {validationResult.warnings.map((warning, i) => (
                  <li key={i}>{warning}</li>
                ))}
              </ul>
            )}
          </AlertDescription>
        </Alert>
      )}

      {/* Field mappings by dataset */}
      {Object.entries(groupedRequirements).map(([dataset, requirements]) => (
        <Card key={dataset}>
          <CardHeader>
            <CardTitle className="text-lg">{dataset} Dataset</CardTitle>
            <CardDescription>
              Map template fields to your study's data fields
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {requirements.map(req => {
              const templateField = `${req.dataset}.${req.field}`;
              const isMapped = !!mappings[templateField];
              const hasSuggestion = !!suggestedMappings[templateField] && !mappings[templateField];
              
              return (
                <div key={templateField} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label className="flex items-center gap-2">
                      <span className={cn(
                        "font-medium",
                        req.required && !isMapped && "text-destructive"
                      )}>
                        {req.field}
                      </span>
                      {req.required && (
                        <Badge variant="secondary" className="text-xs">Required</Badge>
                      )}
                      {isMapped && (
                        <CheckCircle className="h-4 w-4 text-green-500" />
                      )}
                    </Label>
                    {hasSuggestion && (
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleMappingChange(templateField, suggestedMappings[templateField])}
                      >
                        <Sparkles className="h-3 w-3 mr-1" />
                        Use suggestion
                      </Button>
                    )}
                  </div>
                  
                  <Select
                    value={mappings[templateField] || ''}
                    onValueChange={(value) => handleMappingChange(templateField, value)}
                  >
                    <SelectTrigger className={cn(
                      "w-full",
                      req.required && !isMapped && "border-destructive"
                    )}>
                      <SelectValue placeholder="Select a study field..." />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="">None</SelectItem>
                      {availableStudyFields.map(field => (
                        <SelectItem key={field} value={field}>
                          {field}
                          {suggestedMappings[templateField] === field && (
                            <span className="ml-2 text-xs text-muted-foreground">(suggested)</span>
                          )}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  
                  {req.description && (
                    <p className="text-sm text-muted-foreground">{req.description}</p>
                  )}
                  {req.example && (
                    <p className="text-xs text-muted-foreground">
                      Example: {req.example}
                    </p>
                  )}
                </div>
              );
            })}
          </CardContent>
        </Card>
      ))}

      {/* Validate button */}
      {onValidate && (
        <div className="flex justify-end">
          <Button
            onClick={validateMappings}
            disabled={isValidating || mappedRequiredCount === 0}
          >
            {isValidating ? 'Validating...' : 'Validate Mappings'}
          </Button>
        </div>
      )}
    </div>
  );
}