// ABOUTME: Study Info Tab - Edit basic study information
// ABOUTME: Reuses BasicInfoStep component from initialization wizard with edit mode

'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Loader2, Save, Info } from 'lucide-react';
import { BasicInfoStep } from '@/components/study/initialization-wizard/steps/basic-info';
import { useState } from 'react';
import { useToast } from '@/hooks/use-toast';
import { studiesApi } from '@/lib/api/studies';
import { getTherapeuticAreaValue, getIndicationValue } from '@/lib/clinical-data';

interface StudyInfoTabProps {
  study: any;
  onUpdate: () => void;
}

export function StudyInfoTab({ study, onUpdate }: StudyInfoTabProps) {
  const { toast } = useToast();
  const [isLoading, setIsLoading] = useState(false);
  // Convert therapeutic area and indication labels to values for the form
  const therapeuticAreaValue = study.therapeutic_area ? 
    getTherapeuticAreaValue(study.therapeutic_area) : '';
  const indicationValue = study.indication && study.therapeutic_area ? 
    getIndicationValue(study.therapeutic_area, study.indication) : '';

  const [studyData, setStudyData] = useState({
    name: study.name,
    protocol_number: study.protocol_number,
    phase: study.phase,
    therapeutic_area: therapeuticAreaValue,
    indication: indicationValue,
    sponsor: study.sponsor,
    cro: study.cro,
    start_date: study.start_date,
    end_date: study.end_date,
    description: study.description,
    target_enrollment: study.target_enrollment,
    number_of_sites: study.number_of_sites,
    number_of_countries: study.number_of_countries,
  });

  const handleSave = async () => {
    setIsLoading(true);
    try {
      await studiesApi.updateStudy(study.id, studyData);
      toast({
        title: 'Success',
        description: 'Study information updated successfully.',
      });
      onUpdate();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to update study information. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card className="bg-white dark:bg-slate-900">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Info className="h-5 w-5" />
          Study Information
        </CardTitle>
        <CardDescription>
          Update basic study details and configuration
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Reuse BasicInfoStep component in edit mode */}
        <BasicInfoStep
          mode="edit"
          initialData={studyData}
          onChange={setStudyData}
          hideNavigation={true}
        />

        {/* Save Button */}
        <div className="flex justify-end pt-4 border-t">
          <Button
            onClick={handleSave}
            disabled={isLoading}
            className="bg-blue-600 hover:bg-blue-700"
          >
            {isLoading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="h-4 w-4 mr-2" />
                Save Changes
              </>
            )}
          </Button>
        </div>

        {/* Last Modified Info */}
        <div className="text-sm text-gray-500 dark:text-slate-500">
          Last modified: {new Date(study.updated_at).toLocaleString()}
        </div>
      </CardContent>
    </Card>
  );
}