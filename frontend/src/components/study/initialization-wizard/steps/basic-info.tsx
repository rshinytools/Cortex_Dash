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
import { ChevronRight } from 'lucide-react';
import { 
  therapeuticAreas, 
  getIndicationsForArea, 
  DEFAULT_THERAPEUTIC_AREA, 
  DEFAULT_INDICATION,
  getTherapeuticAreaLabel,
  getIndicationLabel
} from '@/lib/clinical-data';

const formSchema = z.object({
  name: z.string().min(1, 'Study name is required'),
  protocol_number: z.string().min(1, 'Protocol number is required'),
  description: z.string().optional(),
  phase: z.string().optional(),
  therapeutic_area: z.string().optional(),
  indication: z.string().optional(),
});

interface BasicInfoStepProps {
  data: any;
  onComplete: (data: any) => void;
  isLoading?: boolean;
}

export function BasicInfoStep({ data, onComplete, isLoading }: BasicInfoStepProps) {
  const [availableIndications, setAvailableIndications] = useState(
    getIndicationsForArea(data.therapeutic_area || DEFAULT_THERAPEUTIC_AREA)
  );

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: data.name || '',
      protocol_number: data.protocol_number || '',
      description: data.description || '',
      phase: data.phase || 'phase_3',
      therapeutic_area: data.therapeutic_area || DEFAULT_THERAPEUTIC_AREA,
      indication: data.indication || DEFAULT_INDICATION,
    },
  });

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
    onComplete(submissionData);
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

          <div className="flex justify-end pt-4 border-t">
            <Button type="submit" disabled={isLoading}>
              Next
              <ChevronRight className="ml-2 h-4 w-4" />
            </Button>
          </div>
        </form>
      </Form>
    </div>
  );
}