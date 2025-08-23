// ABOUTME: Basic information step for study initialization wizard
// ABOUTME: Collects study name, protocol number, phase, and other details with dropdowns

import React, { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Button } from '@/components/ui/button';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { ChevronRight, Building2 } from 'lucide-react';
import { 
  therapeuticAreas, 
  getIndicationsForArea, 
  DEFAULT_THERAPEUTIC_AREA, 
  DEFAULT_INDICATION,
  getTherapeuticAreaLabel,
  getIndicationLabel
} from '@/lib/clinical-data';
import { useQuery } from '@tanstack/react-query';
import { organizationsApi } from '@/lib/api/organizations';
import { useAuth } from '@/lib/auth-context';
import { UserRole } from '@/types';

const formSchema = z.object({
  name: z.string().min(1, 'Study name is required'),
  protocol_number: z.string().min(1, 'Protocol number is required'),
  description: z.string().optional(),
  phase: z.string().optional(),
  therapeutic_area: z.string().optional(),
  indication: z.string().optional(),
  org_id: z.string().min(1, 'Organization is required'),
});

interface BasicInfoStepProps {
  data?: any;
  onComplete?: (data: any) => void;
  isLoading?: boolean;
  mode?: 'create' | 'edit';
  initialData?: any;
  onChange?: (data: any) => void;
  hideNavigation?: boolean;
}

export function BasicInfoStep({ 
  data, 
  onComplete, 
  isLoading, 
  mode = 'create',
  initialData,
  onChange,
  hideNavigation = false
}: BasicInfoStepProps) {
  // Use initialData if provided (edit mode), otherwise use data (create mode)
  const formData = mode === 'edit' ? initialData : data;
  const { user } = useAuth();
  
  const [availableIndications, setAvailableIndications] = useState(
    getIndicationsForArea(formData?.therapeutic_area || DEFAULT_THERAPEUTIC_AREA)
  );

  // Fetch organizations list - ALL users should be able to select organization
  const { data: organizations, isLoading: orgsLoading } = useQuery({
    queryKey: ['organizations'],
    queryFn: organizationsApi.getOrganizations,
    enabled: true, // Enable for all users
  });

  // Use the org_id from form data if available, otherwise empty
  const defaultOrgId = formData?.org_id || '';
  
  // Debug logging
  console.log('[BasicInfoStep] Mode:', mode);
  console.log('[BasicInfoStep] FormData:', formData);
  console.log('[BasicInfoStep] DefaultOrgId:', defaultOrgId);
  console.log('[BasicInfoStep] Organizations:', organizations);

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: formData?.name || '',
      protocol_number: formData?.protocol_number || '',
      description: formData?.description || '',
      phase: formData?.phase || 'phase_3',
      therapeutic_area: formData?.therapeutic_area || DEFAULT_THERAPEUTIC_AREA,
      indication: formData?.indication || DEFAULT_INDICATION,
      org_id: defaultOrgId,
    },
  });

  // Update form when formData changes (important for edit mode)
  useEffect(() => {
    if (formData?.org_id) {
      console.log('[BasicInfoStep] Setting org_id to:', formData.org_id);
      form.setValue('org_id', formData.org_id);
    }
  }, [formData?.org_id, form]);

  // Watch therapeutic area changes to update indications
  const therapeuticArea = form.watch('therapeutic_area');
  
  useEffect(() => {
    if (therapeuticArea) {
      const indications = getIndicationsForArea(therapeuticArea);
      setAvailableIndications(indications);
      
      // Reset indication if it's not in the new list
      const currentIndication = form.getValues('indication');
      if (currentIndication && !indications.find(ind => ind.value === currentIndication)) {
        form.setValue('indication', indications[0]?.value || '');
      }
    }
  }, [therapeuticArea, form]);

  const onSubmit = (values: z.infer<typeof formSchema>) => {
    // Convert dropdown values to labels for backend
    const submissionData = {
      ...values,
      therapeutic_area: getTherapeuticAreaLabel(values.therapeutic_area || ''),
      indication: getIndicationLabel(values.therapeutic_area || '', values.indication || '')
    };
    
    // In edit mode, call onChange instead of onComplete
    if (mode === 'edit' && onChange) {
      onChange(submissionData);
    } else if (onComplete) {
      onComplete(submissionData);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium">Basic Study Information</h3>
        <p className="text-sm text-muted-foreground">
          Enter the basic information for your clinical study
        </p>
      </div>

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
          {/* Organization selector - show for all users */}
          <FormField
            control={form.control}
            name="org_id"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Organization *</FormLabel>
                <Select 
                  onValueChange={field.onChange} 
                  value={field.value}
                  disabled={orgsLoading || mode === 'edit'}
                >
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue placeholder={orgsLoading ? "Loading..." : "Select organization"} />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    {organizations?.map(org => (
                      <SelectItem key={org.id} value={org.id}>
                        <div className="flex items-center gap-2">
                          <Building2 className="h-4 w-4" />
                          {org.name}
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <FormDescription>
                  The organization this study belongs to
                </FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="name"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Study Name *</FormLabel>
                <FormControl>
                  <Input placeholder="e.g., Phase 3 NSCLC Trial" {...field} />
                </FormControl>
                <FormDescription>
                  A descriptive name for your study
                </FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="protocol_number"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Protocol Number *</FormLabel>
                <FormControl>
                  <Input placeholder="e.g., ACME-123" {...field} />
                </FormControl>
                <FormDescription>
                  Unique protocol identifier (e.g., STUDY-2025-001, TRIAL-ABC-123)
                </FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="description"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Description</FormLabel>
                <FormControl>
                  <Textarea
                    placeholder="Brief description of the study objectives and design"
                    className="min-h-[100px]"
                    {...field}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <FormField
              control={form.control}
              name="phase"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Phase</FormLabel>
                  <Select onValueChange={field.onChange} defaultValue={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Select phase" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="phase_1">Phase 1</SelectItem>
                      <SelectItem value="phase_2">Phase 2</SelectItem>
                      <SelectItem value="phase_3">Phase 3</SelectItem>
                      <SelectItem value="phase_4">Phase 4</SelectItem>
                      <SelectItem value="observational">Observational</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="therapeutic_area"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Therapeutic Area</FormLabel>
                  <Select onValueChange={field.onChange} defaultValue={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Select therapeutic area" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {therapeuticAreas.map((area) => (
                        <SelectItem key={area.value} value={area.value}>
                          {area.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="indication"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Indication</FormLabel>
                  <Select 
                    onValueChange={field.onChange} 
                    value={field.value}
                    disabled={!therapeuticArea}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Select indication" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {availableIndications.map((indication) => (
                        <SelectItem key={indication.value} value={indication.value}>
                          {indication.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormDescription>
                    {!therapeuticArea && "Select a therapeutic area first"}
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>

          {!hideNavigation && (
            <div className="flex justify-end pt-4 border-t">
              <Button type="submit" disabled={isLoading}>
                Next
                <ChevronRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          )}
        </form>
      </Form>
    </div>
  );
}