// ABOUTME: Reusable form component for creating and editing widget definitions
// ABOUTME: Provides validation, JSON schema editing, and size constraint configuration

'use client'

import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { Button } from '@/components/ui/button'
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { AlertCircle, Code2, Layers, Save } from 'lucide-react'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { WidgetCategory, WidgetType, WidgetDefinition } from '@/types/widget'
import { CreateWidgetRequest, UpdateWidgetRequest } from '@/lib/api/widgets'

const widgetFormSchema = z.object({
  name: z.string().min(3, 'Name must be at least 3 characters').max(100),
  description: z.string().optional(),
  category: z.nativeEnum(WidgetCategory),
  type: z.nativeEnum(WidgetType),
  componentPath: z.string().min(1, 'Component path is required'),
  tags: z.string().optional(),
  size: z.object({
    minWidth: z.number().min(1).max(24),
    minHeight: z.number().min(1).max(24),
    defaultWidth: z.number().min(1).max(24),
    defaultHeight: z.number().min(1).max(24),
  }),
  dataRequirements: z.object({
    sourceType: z.enum(['dataset', 'api', 'static']),
    requiredFields: z.string().optional(),
    optionalFields: z.string().optional(),
    refreshInterval: z.number().optional(),
  }).optional(),
})

type WidgetFormValues = z.infer<typeof widgetFormSchema>

interface WidgetFormProps {
  widget?: WidgetDefinition
  onSubmit: (data: CreateWidgetRequest | UpdateWidgetRequest) => void
  isLoading?: boolean
}

export function WidgetForm({ widget, onSubmit, isLoading }: WidgetFormProps) {
  const [jsonError, setJsonError] = useState<string>('')
  const [defaultConfig, setDefaultConfig] = useState<string>(
    widget?.defaultConfig ? JSON.stringify(widget.defaultConfig, null, 2) : '{}'
  )
  const [configSchema, setConfigSchema] = useState<string>(
    widget?.config_schema ? JSON.stringify(widget.config_schema, null, 2) : '{}'
  )

  const form = useForm<WidgetFormValues>({
    resolver: zodResolver(widgetFormSchema),
    defaultValues: {
      name: widget?.name || '',
      description: widget?.description || '',
      category: widget?.category || WidgetCategory.METRICS,
      type: widget?.type || WidgetType.METRIC,
      componentPath: widget?.componentPath || '',
      tags: widget?.tags?.join(', ') || '',
      size: widget?.size || {
        minWidth: 2,
        minHeight: 2,
        defaultWidth: 4,
        defaultHeight: 3,
      },
      dataRequirements: widget?.dataRequirements ? {
        sourceType: widget.dataRequirements.sourceType,
        requiredFields: widget.dataRequirements.requiredFields?.join(', ') || '',
        optionalFields: widget.dataRequirements.optionalFields?.join(', ') || '',
        refreshInterval: widget.dataRequirements.refreshInterval,
      } : {
        sourceType: 'dataset',
      },
    },
  })

  // Validate JSON when it changes
  const validateJSON = (value: string, field: 'defaultConfig' | 'configSchema') => {
    try {
      JSON.parse(value)
      setJsonError('')
      return true
    } catch (e) {
      setJsonError(`Invalid JSON in ${field}: ${e instanceof Error ? e.message : 'Unknown error'}`)
      return false
    }
  }

  const handleSubmit = (values: WidgetFormValues) => {
    // Validate JSON fields
    if (!validateJSON(defaultConfig, 'defaultConfig') || !validateJSON(configSchema, 'configSchema')) {
      return
    }

    const data: CreateWidgetRequest = {
      name: values.name,
      description: values.description,
      category: values.category,
      type: values.type,
      componentPath: values.componentPath,
      defaultConfig: JSON.parse(defaultConfig),
      configSchema: JSON.parse(configSchema),
      size: values.size,
      tags: values.tags ? values.tags.split(',').map(t => t.trim()).filter(Boolean) : undefined,
    }

    if (values.dataRequirements) {
      data.dataRequirements = {
        sourceType: values.dataRequirements.sourceType,
        requiredFields: values.dataRequirements.requiredFields 
          ? values.dataRequirements.requiredFields.split(',').map(f => f.trim()).filter(Boolean)
          : undefined,
        optionalFields: values.dataRequirements.optionalFields
          ? values.dataRequirements.optionalFields.split(',').map(f => f.trim()).filter(Boolean)
          : undefined,
        refreshInterval: values.dataRequirements.refreshInterval,
      }
    }

    onSubmit(data)
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Basic Information</CardTitle>
            <CardDescription>Configure the widget's basic properties</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Widget Name</FormLabel>
                    <FormControl>
                      <Input placeholder="e.g., Enrollment Metric" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="componentPath"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Component Path</FormLabel>
                    <FormControl>
                      <Input placeholder="e.g., widgets/EnrollmentMetric" {...field} />
                    </FormControl>
                    <FormDescription>Path to the React component</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <FormField
              control={form.control}
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Description</FormLabel>
                  <FormControl>
                    <Textarea 
                      placeholder="Describe what this widget displays and its purpose"
                      className="resize-none"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="category"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Category</FormLabel>
                    <Select onValueChange={field.onChange} defaultValue={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select a category" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {Object.entries(WidgetCategory).map(([key, value]) => (
                          <SelectItem key={value} value={value}>
                            {key.charAt(0) + key.slice(1).toLowerCase().replace('_', ' ')}
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
                name="type"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Type</FormLabel>
                    <Select onValueChange={field.onChange} defaultValue={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select a type" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {Object.entries(WidgetType).map(([key, value]) => (
                          <SelectItem key={value} value={value}>
                            {key.charAt(0) + key.slice(1).toLowerCase().replace('_', ' ')}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <FormField
              control={form.control}
              name="tags"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Tags</FormLabel>
                  <FormControl>
                    <Input placeholder="e.g., enrollment, safety, real-time (comma separated)" {...field} />
                  </FormControl>
                  <FormDescription>Comma-separated tags for categorization</FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Size Constraints</CardTitle>
            <CardDescription>Define the widget's size limits in grid units</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <FormField
                control={form.control}
                name="size.minWidth"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Min Width</FormLabel>
                    <FormControl>
                      <Input 
                        type="number" 
                        min={1} 
                        max={24}
                        {...field}
                        onChange={e => field.onChange(parseInt(e.target.value) || 1)}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="size.minHeight"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Min Height</FormLabel>
                    <FormControl>
                      <Input 
                        type="number" 
                        min={1} 
                        max={24}
                        {...field}
                        onChange={e => field.onChange(parseInt(e.target.value) || 1)}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="size.defaultWidth"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Default Width</FormLabel>
                    <FormControl>
                      <Input 
                        type="number" 
                        min={1} 
                        max={24}
                        {...field}
                        onChange={e => field.onChange(parseInt(e.target.value) || 1)}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="size.defaultHeight"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Default Height</FormLabel>
                    <FormControl>
                      <Input 
                        type="number" 
                        min={1} 
                        max={24}
                        {...field}
                        onChange={e => field.onChange(parseInt(e.target.value) || 1)}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Configuration Schema</CardTitle>
            <CardDescription>Define the JSON schema for widget configuration</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {jsonError && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{jsonError}</AlertDescription>
              </Alert>
            )}

            <div className="space-y-4">
              <div>
                <Label htmlFor="defaultConfig" className="flex items-center gap-2 mb-2">
                  <Code2 className="h-4 w-4" />
                  Default Configuration
                </Label>
                <Textarea
                  id="defaultConfig"
                  value={defaultConfig}
                  onChange={(e) => {
                    setDefaultConfig(e.target.value)
                    validateJSON(e.target.value, 'defaultConfig')
                  }}
                  className="font-mono text-sm min-h-[200px]"
                  placeholder='{"title": "My Widget", "refreshInterval": 30}'
                />
              </div>

              <div>
                <Label htmlFor="configSchema" className="flex items-center gap-2 mb-2">
                  <Layers className="h-4 w-4" />
                  Configuration Schema
                </Label>
                <Textarea
                  id="configSchema"
                  value={configSchema}
                  onChange={(e) => {
                    setConfigSchema(e.target.value)
                    validateJSON(e.target.value, 'configSchema')
                  }}
                  className="font-mono text-sm min-h-[200px]"
                  placeholder='{"type": "object", "properties": {"title": {"type": "string"}}}'
                />
                <p className="text-sm text-muted-foreground mt-2">
                  JSON Schema for validating widget configurations
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Data Requirements</CardTitle>
            <CardDescription>Specify the data requirements for this widget</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <FormField
              control={form.control}
              name="dataRequirements.sourceType"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Data Source Type</FormLabel>
                  <Select onValueChange={field.onChange} defaultValue={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Select source type" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="dataset">Dataset</SelectItem>
                      <SelectItem value="api">API</SelectItem>
                      <SelectItem value="static">Static</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="dataRequirements.requiredFields"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Required Fields</FormLabel>
                  <FormControl>
                    <Input 
                      placeholder="e.g., patientId, visitDate, status (comma separated)" 
                      {...field}
                    />
                  </FormControl>
                  <FormDescription>Fields that must be present in the data source</FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="dataRequirements.optionalFields"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Optional Fields</FormLabel>
                  <FormControl>
                    <Input 
                      placeholder="e.g., age, gender, site (comma separated)" 
                      {...field}
                    />
                  </FormControl>
                  <FormDescription>Fields that can enhance the widget if available</FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="dataRequirements.refreshInterval"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Refresh Interval (seconds)</FormLabel>
                  <FormControl>
                    <Input 
                      type="number" 
                      min={0}
                      placeholder="e.g., 300 (5 minutes)"
                      {...field}
                      onChange={e => field.onChange(e.target.value ? parseInt(e.target.value) : undefined)}
                    />
                  </FormControl>
                  <FormDescription>How often the widget should refresh its data (0 = no auto-refresh)</FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
          </CardContent>
        </Card>

        <div className="flex justify-end gap-4">
          <Button type="submit" disabled={isLoading || !!jsonError}>
            <Save className="mr-2 h-4 w-4" />
            {widget ? 'Update Widget' : 'Create Widget'}
          </Button>
        </div>

        {widget && (
          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            <span>Version: <Badge variant="secondary">{widget.version}</Badge></span>
            <span>Created: {widget.created_at || widget.createdAt ? 
              new Date(widget.created_at || widget.createdAt || '').toLocaleDateString() : 
              'N/A'}</span>
            <span>Updated: {widget.updated_at || widget.updatedAt ? 
              new Date(widget.updated_at || widget.updatedAt || '').toLocaleDateString() : 
              'N/A'}</span>
          </div>
        )}
      </form>
    </Form>
  )
}