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
  code: z.string().min(1, 'Code is required').regex(/^[a-z_]+$/, 'Code must be lowercase with underscores'),
  name: z.string().min(3, 'Name must be at least 3 characters').max(100),
  description: z.string().optional(),
  category: z.nativeEnum(WidgetCategory),
  size_constraints: z.object({
    minWidth: z.number().min(1).max(24),
    minHeight: z.number().min(1).max(24),
    maxWidth: z.number().min(1).max(24).optional(),
    maxHeight: z.number().min(1).max(24).optional(),
    defaultWidth: z.number().min(1).max(24),
    defaultHeight: z.number().min(1).max(24),
  }),
  is_active: z.boolean().optional(),
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
    widget?.config_schema ? JSON.stringify(widget.config_schema, null, 2) : '{\n  "type": "object",\n  "properties": {}\n}'
  )

  const form = useForm<WidgetFormValues>({
    resolver: zodResolver(widgetFormSchema),
    defaultValues: {
      code: widget?.code || '',
      name: widget?.name || '',
      description: widget?.description || '',
      category: widget?.category || WidgetCategory.METRICS,
      size_constraints: widget?.size_constraints || {
        minWidth: 2,
        minHeight: 2,
        defaultWidth: 4,
        defaultHeight: 3,
      },
      is_active: widget?.is_active !== undefined ? widget.is_active : true,
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
      code: values.code,
      name: values.name,
      description: values.description,
      category: values.category,
      config_schema: JSON.parse(configSchema),
      default_config: JSON.parse(defaultConfig),
      size_constraints: values.size_constraints,
      data_requirements: {},  // Can be expanded based on needs
      is_active: values.is_active,
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
                name="code"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Widget Code</FormLabel>
                    <FormControl>
                      <Input placeholder="e.g., metric_card" {...field} disabled={!!widget} />
                    </FormControl>
                    <FormDescription>Unique identifier (lowercase with underscores)</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Display Name</FormLabel>
                    <FormControl>
                      <Input placeholder="e.g., Metric Card" {...field} />
                    </FormControl>
                    <FormDescription>Human-readable name</FormDescription>
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
              name="is_active"
              render={({ field }) => (
                <FormItem className="flex items-center space-x-2">
                  <FormControl>
                    <input
                      type="checkbox"
                      checked={field.value}
                      onChange={(e) => field.onChange(e.target.checked)}
                      className="h-4 w-4"
                    />
                  </FormControl>
                  <FormLabel className="!mt-0">Active</FormLabel>
                  <FormDescription className="!mt-0 ml-2">Widget is available for use</FormDescription>
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
                name="size_constraints.minWidth"
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
                name="size_constraints.minHeight"
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
                name="size_constraints.defaultWidth"
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
                name="size_constraints.defaultHeight"
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
                  placeholder='{"type": "object", "properties": {"title": {"type": "string"}}, "required": ["title"]}'
                />
                <p className="text-sm text-muted-foreground mt-2">
                  JSON Schema for validating widget configurations
                </p>
              </div>
            </div>
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