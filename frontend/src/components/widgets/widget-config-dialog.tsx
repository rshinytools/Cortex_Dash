// ABOUTME: Widget configuration dialog for customizing widget settings
// ABOUTME: Renders dynamic form based on widget config schema with validation

'use client';

import React, { useState, useEffect, useMemo } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Slider } from '@/components/ui/slider';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { AlertCircle, Eye, Save } from 'lucide-react';
import { WidgetInstance, WidgetRegistration } from './base-widget';
import { WidgetRegistry } from './widget-registry';
import { WidgetRenderer } from './widget-renderer';

interface WidgetConfigDialogProps {
  isOpen: boolean;
  onClose: () => void;
  widgetInstance: WidgetInstance;
  onSave: (updatedWidget: WidgetInstance) => void;
  previewData?: any;
}

interface FieldSchema {
  type: 'string' | 'number' | 'boolean' | 'array' | 'object';
  enum?: string[];
  required?: boolean;
  min?: number;
  max?: number;
  description?: string;
  default?: any;
  items?: FieldSchema;
}

const renderField = (
  fieldName: string,
  schema: FieldSchema,
  value: any,
  onChange: (value: any) => void,
  errors: Record<string, string>
) => {
  const fieldId = `field-${fieldName}`;
  const error = errors[fieldName];

  switch (schema.type) {
    case 'string':
      if (schema.enum) {
        return (
          <div className="space-y-2">
            <Label htmlFor={fieldId}>
              {fieldName}
              {schema.required && <span className="text-destructive ml-1">*</span>}
            </Label>
            <Select value={value || ''} onValueChange={onChange}>
              <SelectTrigger id={fieldId} className={error ? 'border-destructive' : ''}>
                <SelectValue placeholder={`Select ${fieldName}`} />
              </SelectTrigger>
              <SelectContent>
                {schema.enum.map((option) => (
                  <SelectItem key={option} value={option}>
                    {option}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {schema.description && (
              <p className="text-sm text-muted-foreground">{schema.description}</p>
            )}
            {error && <p className="text-sm text-destructive">{error}</p>}
          </div>
        );
      }
      return (
        <div className="space-y-2">
          <Label htmlFor={fieldId}>
            {fieldName}
            {schema.required && <span className="text-destructive ml-1">*</span>}
          </Label>
          <Input
            id={fieldId}
            type="text"
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            className={error ? 'border-destructive' : ''}
          />
          {schema.description && (
            <p className="text-sm text-muted-foreground">{schema.description}</p>
          )}
          {error && <p className="text-sm text-destructive">{error}</p>}
        </div>
      );

    case 'number':
      if (schema.min !== undefined && schema.max !== undefined) {
        return (
          <div className="space-y-2">
            <Label htmlFor={fieldId}>
              {fieldName}
              {schema.required && <span className="text-destructive ml-1">*</span>}
              <span className="text-muted-foreground ml-2">({value || schema.default || 0})</span>
            </Label>
            <Slider
              id={fieldId}
              value={[value || schema.default || 0]}
              onValueChange={([val]) => onChange(val)}
              min={schema.min}
              max={schema.max}
              step={1}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>{schema.min}</span>
              <span>{schema.max}</span>
            </div>
            {schema.description && (
              <p className="text-sm text-muted-foreground">{schema.description}</p>
            )}
            {error && <p className="text-sm text-destructive">{error}</p>}
          </div>
        );
      }
      return (
        <div className="space-y-2">
          <Label htmlFor={fieldId}>
            {fieldName}
            {schema.required && <span className="text-destructive ml-1">*</span>}
          </Label>
          <Input
            id={fieldId}
            type="number"
            value={value || ''}
            onChange={(e) => onChange(e.target.value ? Number(e.target.value) : '')}
            className={error ? 'border-destructive' : ''}
          />
          {schema.description && (
            <p className="text-sm text-muted-foreground">{schema.description}</p>
          )}
          {error && <p className="text-sm text-destructive">{error}</p>}
        </div>
      );

    case 'boolean':
      return (
        <div className="flex items-center justify-between space-x-2">
          <div className="space-y-0.5">
            <Label htmlFor={fieldId}>
              {fieldName}
              {schema.required && <span className="text-destructive ml-1">*</span>}
            </Label>
            {schema.description && (
              <p className="text-sm text-muted-foreground">{schema.description}</p>
            )}
          </div>
          <Switch
            id={fieldId}
            checked={value || false}
            onCheckedChange={onChange}
          />
        </div>
      );

    case 'array':
      // Simplified array handling - would need more complex UI for real arrays
      return (
        <div className="space-y-2">
          <Label htmlFor={fieldId}>
            {fieldName}
            {schema.required && <span className="text-destructive ml-1">*</span>}
          </Label>
          <Textarea
            id={fieldId}
            value={JSON.stringify(value || [], null, 2)}
            onChange={(e) => {
              try {
                const parsed = JSON.parse(e.target.value);
                onChange(parsed);
              } catch {
                // Invalid JSON, don't update
              }
            }}
            className={`font-mono ${error ? 'border-destructive' : ''}`}
            rows={4}
          />
          {schema.description && (
            <p className="text-sm text-muted-foreground">{schema.description}</p>
          )}
          {error && <p className="text-sm text-destructive">{error}</p>}
        </div>
      );

    default:
      return null;
  }
};

export const WidgetConfigDialog: React.FC<WidgetConfigDialogProps> = ({
  isOpen,
  onClose,
  widgetInstance,
  onSave,
  previewData,
}) => {
  const [configuration, setConfiguration] = useState(widgetInstance.configuration);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [activeTab, setActiveTab] = useState('configuration');

  const registration = useMemo(() => 
    WidgetRegistry.get(widgetInstance.type),
    [widgetInstance.type]
  );

  useEffect(() => {
    setConfiguration(widgetInstance.configuration);
    setErrors({});
  }, [widgetInstance]);

  const validateConfiguration = () => {
    const newErrors: Record<string, string> = {};

    if (registration?.configSchema) {
      Object.entries(registration.configSchema).forEach(([field, schema]) => {
        const fieldSchema = schema as FieldSchema;
        const value = configuration[field];

        if (fieldSchema.required && (value === undefined || value === null || value === '')) {
          newErrors[field] = `${field} is required`;
        }

        if (fieldSchema.type === 'number' && value !== undefined) {
          if (fieldSchema.min !== undefined && value < fieldSchema.min) {
            newErrors[field] = `${field} must be at least ${fieldSchema.min}`;
          }
          if (fieldSchema.max !== undefined && value > fieldSchema.max) {
            newErrors[field] = `${field} must be at most ${fieldSchema.max}`;
          }
        }
      });
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSave = () => {
    if (validateConfiguration()) {
      onSave({
        ...widgetInstance,
        configuration,
      });
      onClose();
    }
  };

  const updateField = (field: string, value: any) => {
    setConfiguration((prev) => ({
      ...prev,
      [field]: value,
    }));
    // Clear error for this field
    setErrors((prev) => {
      const newErrors = { ...prev };
      delete newErrors[field];
      return newErrors;
    });
  };

  if (!registration) {
    return (
      <Dialog open={isOpen} onOpenChange={onClose}>
        <DialogContent>
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Widget type "{widgetInstance.type}" not found in registry
            </AlertDescription>
          </Alert>
        </DialogContent>
      </Dialog>
    );
  }

  const previewWidget: WidgetInstance = {
    ...widgetInstance,
    configuration,
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh]">
        <DialogHeader>
          <DialogTitle>Configure {registration.name}</DialogTitle>
          <DialogDescription>
            Customize the settings for this widget
          </DialogDescription>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="mt-4">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="configuration">Configuration</TabsTrigger>
            <TabsTrigger value="preview">Preview</TabsTrigger>
          </TabsList>

          <TabsContent value="configuration" className="mt-4">
            <ScrollArea className="h-[400px] pr-4">
              <div className="space-y-6">
                {/* Basic Settings */}
                <div className="space-y-4">
                  <h4 className="text-sm font-medium">Basic Settings</h4>
                  <div className="space-y-2">
                    <Label htmlFor="widget-title">
                      Title <span className="text-destructive">*</span>
                    </Label>
                    <Input
                      id="widget-title"
                      value={widgetInstance.title}
                      onChange={(e) => {
                        // Update title in parent component
                        onSave({
                          ...widgetInstance,
                          title: e.target.value,
                          configuration,
                        });
                      }}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="widget-description">Description</Label>
                    <Textarea
                      id="widget-description"
                      value={widgetInstance.description || ''}
                      onChange={(e) => {
                        // Update description in parent component
                        onSave({
                          ...widgetInstance,
                          description: e.target.value,
                          configuration,
                        });
                      }}
                      rows={2}
                    />
                  </div>
                </div>

                <Separator />

                {/* Widget-specific Configuration */}
                <div className="space-y-4">
                  <h4 className="text-sm font-medium">Widget Settings</h4>
                  {registration.configSchema &&
                    Object.entries(registration.configSchema).map(([field, schema]) => (
                      <div key={field}>
                        {renderField(
                          field,
                          schema as FieldSchema,
                          configuration[field],
                          (value) => updateField(field, value),
                          errors
                        )}
                      </div>
                    ))}
                </div>
              </div>
            </ScrollArea>
          </TabsContent>

          <TabsContent value="preview" className="mt-4">
            <div className="border rounded-lg p-4 bg-muted/50">
              <div className="mb-2 text-sm text-muted-foreground">
                Preview with {previewData ? 'sample data' : 'no data'}
              </div>
              <div className="h-[400px] overflow-auto">
                <WidgetRenderer
                  instance={previewWidget}
                  data={previewData}
                  loading={false}
                  error=""
                  viewMode={true}
                />
              </div>
            </div>
          </TabsContent>
        </Tabs>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={Object.keys(errors).length > 0}>
            <Save className="h-4 w-4 mr-2" />
            Save Configuration
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};