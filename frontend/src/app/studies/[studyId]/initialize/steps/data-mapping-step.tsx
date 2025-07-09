// ABOUTME: Data mapping step for study initialization wizard
// ABOUTME: Allows users to map study data fields to template requirements

'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { useQuery, useMutation } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';
import { Loader2, AlertCircle, Database } from 'lucide-react';
import { DataMappingWizard } from '@/components/studies/data-mapping-wizard';
import { useToast } from '@/hooks/use-toast';

interface DataMappingStepProps {
  studyId: string;
  data: {
    fieldMappings?: Record<string, string>;
    templateId?: string;
    templateDetails?: any;
  };
  onDataChange: (data: any) => void;
}

export function DataMappingStep({ studyId, data, onDataChange }: DataMappingStepProps) {
  const { toast } = useToast();
  const [fieldMappings, setFieldMappings] = useState<Record<string, string>>(
    data.fieldMappings || {}
  );

  // Fetch template data requirements
  const { data: requirementsData, isLoading: isLoadingRequirements } = useQuery({
    queryKey: ['template-requirements', data.templateId],
    queryFn: async () => {
      if (!data.templateId) throw new Error('No template selected');
      const response = await apiClient.get(`/dashboard-templates/${data.templateId}/data-requirements`);
      return response.data;
    },
    enabled: !!data.templateId,
  });

  // Fetch available study fields (mock for now)
  const { data: studyFieldsData, isLoading: isLoadingFields } = useQuery({
    queryKey: ['study-fields', studyId],
    queryFn: async () => {
      // In a real implementation, this would fetch actual study data schemas
      // For now, return mock data based on common clinical trial fields
      return {
        fields: [
          // ADSL (Subject Level Analysis Dataset)
          'subject_id', 'patient_id', 'usubjid',
          'age', 'ageu', 'sex', 'gender', 'race', 'ethnic',
          'country', 'site_id', 'siteid',
          'arm', 'treatment_group', 'actarm',
          'trt01p', 'trt01a',
          'rfstdtc', 'rfendtc',
          
          // ADAE (Adverse Events Analysis Dataset)
          'aeterm', 'aedecod', 'aebodsys',
          'aesev', 'severity', 'aeser',
          'aerel', 'aeacn', 'aeout',
          'aestdtc', 'aeendtc',
          
          // Visit data
          'visit', 'visitnum', 'visitdy',
          'visit_date', 'visitdt',
          
          // Lab data
          'lbtestcd', 'lbtest', 'lborres', 'lborresu',
          'lbstresn', 'lbstresu', 'lbnrind',
          
          // Vital signs
          'vstestcd', 'vstest', 'vsorres', 'vsorresu',
          'vsstresc', 'vsstresn', 'vsstresu',
          
          // Efficacy
          'paramcd', 'param', 'aval', 'base', 'chg',
          'pchg', 'avalc', 'avalu'
        ].sort()
      };
    },
  });

  // Validate field mappings
  const validateMappingsMutation = useMutation({
    mutationFn: async (mappings: Record<string, string>) => {
      const response = await apiClient.post(`/studies/${studyId}/validate-field-mappings`, {
        template_id: data.templateId,
        field_mappings: mappings,
      });
      return response.data;
    },
  });

  // Handle mappings change
  const handleMappingsChange = (mappings: Record<string, string>) => {
    setFieldMappings(mappings);
    onDataChange({
      ...data,
      fieldMappings: mappings,
    });
  };

  // Convert requirements data to the format expected by DataMappingWizard
  const dataRequirements: any[] = [];
  if (requirementsData?.field_mappings) {
    Object.entries(requirementsData.field_mappings).forEach(([dataset, fields]) => {
      (fields as string[]).forEach(field => {
        dataRequirements.push({
          dataset,
          field,
          description: `${field} field from ${dataset} dataset`,
          required: true,
          example: getFieldExample(dataset, field),
        });
      });
    });
  }

  if (isLoadingRequirements || isLoadingFields) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!data.templateId) {
    return (
      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          Please select a dashboard template in the previous step.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      {/* Template info */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            Data Requirements for {data.templateDetails?.name || 'Selected Template'}
          </CardTitle>
          <CardDescription>
            Map your study's data fields to the template requirements below
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 text-sm">
            <p><strong>Required Datasets:</strong> {requirementsData?.required_datasets?.join(', ') || 'None'}</p>
            <p><strong>Total Fields to Map:</strong> {dataRequirements.length}</p>
          </div>
        </CardContent>
      </Card>

      {/* Data mapping wizard */}
      <DataMappingWizard
        templateId={data.templateId}
        templateName={data.templateDetails?.name || 'Template'}
        dataRequirements={dataRequirements}
        availableStudyFields={studyFieldsData?.fields || []}
        initialMappings={fieldMappings}
        onMappingsChange={handleMappingsChange}
        onValidate={async (mappings) => {
          const result = await validateMappingsMutation.mutateAsync(mappings);
          return {
            isValid: result.is_valid,
            missingMappings: result.missing_mappings,
            suggestedMappings: result.suggested_mappings,
            warnings: result.warnings,
          };
        }}
      />

      {/* Instructions */}
      <Alert>
        <AlertDescription>
          <strong>Tips for mapping fields:</strong>
          <ul className="list-disc list-inside mt-2 space-y-1">
            <li>Required fields must be mapped before proceeding</li>
            <li>Use the auto-mapping feature to quickly map common fields</li>
            <li>Field names are matched case-insensitively</li>
            <li>You can customize mappings after the initial setup</li>
          </ul>
        </AlertDescription>
      </Alert>
    </div>
  );
}

// Helper function to provide examples for common SDTM fields
function getFieldExample(dataset: string, field: string): string | undefined {
  const examples: Record<string, Record<string, string>> = {
    ADSL: {
      USUBJID: 'STUDY001-SITE01-0001',
      AGE: '45',
      SEX: 'M/F',
      RACE: 'WHITE',
      ARM: 'TREATMENT A',
    },
    ADAE: {
      AETERM: 'HEADACHE',
      AESEV: 'MILD/MODERATE/SEVERE',
      AESER: 'Y/N',
      AEREL: 'RELATED/NOT RELATED',
    },
  };
  
  return examples[dataset]?.[field];
}