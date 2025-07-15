// ABOUTME: Basic information step for study initialization wizard
// ABOUTME: Collects study name, protocol number, and other basic details

import React from 'react';
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

const formSchema = z.object({
  name: z.string().min(3, 'Study name must be at least 3 characters'),
  protocol_number: z.string().min(1, 'Protocol number is required'),
  description: z.string().optional(),
  phase: z.string().optional(),
  therapeutic_area: z.string().optional(),
  indication: z.string().optional(),
});

type FormData = z.infer<typeof formSchema>;

interface BasicInfoStepProps {
  data: Partial<FormData>;
  onComplete: (data: FormData) => void;
  isLoading?: boolean;
}

export function BasicInfoStep({ data, onComplete, isLoading }: BasicInfoStepProps) {
  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: data.name || '',
      protocol_number: data.protocol_number || '',
      description: data.description || '',
      phase: data.phase || '',
      therapeutic_area: data.therapeutic_area || '',
      indication: data.indication || '',
    },
  });

  const onSubmit = (values: FormData) => {
    onComplete(values);
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
                  <Input placeholder="e.g., ACME-123 Phase II Safety Study" {...field} />
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
                  Unique protocol identifier
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
                  <FormLabel>Study Phase</FormLabel>
                  <Select onValueChange={field.onChange} defaultValue={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Select phase" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="phase_1">Phase I</SelectItem>
                      <SelectItem value="phase_2">Phase II</SelectItem>
                      <SelectItem value="phase_3">Phase III</SelectItem>
                      <SelectItem value="phase_4">Phase IV</SelectItem>
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
                  <FormControl>
                    <Input placeholder="e.g., Oncology" {...field} />
                  </FormControl>
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
                  <FormControl>
                    <Input placeholder="e.g., NSCLC" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>

          <div className="flex justify-end pt-4">
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