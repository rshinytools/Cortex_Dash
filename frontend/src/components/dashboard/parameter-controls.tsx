// ABOUTME: Parameter controls UI component for managing dashboard parameters
// ABOUTME: Provides forms and controls for editing parameter values and settings

'use client';

import React, { useState, useCallback, useMemo } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import { Calendar } from '@/components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { 
  Settings, 
  Plus, 
  Edit3, 
  Trash2, 
  Save, 
  RotateCcw,
  Calendar as CalendarIcon,
  AlertCircle,
  Check,
  X,
  Copy,
  Link
} from 'lucide-react';
import { format } from 'date-fns';
import { cn } from '@/lib/utils';
import { useParameterManager, ParameterDefinition } from './dashboard-parameters';
import { toast } from 'sonner';

interface ParameterControlsProps {
  className?: string;
  variant?: 'sheet' | 'inline' | 'dialog';
  showValidationErrors?: boolean;
  children?: React.ReactNode;
}

export function ParameterControls({
  className,
  variant = 'sheet',
  showValidationErrors = true,
  children,
}: ParameterControlsProps) {
  const {
    state,
    setParameterValue,
    validateParameters,
    saveParameters,
    resetToDefaults,
    addParameter,
    updateParameter,
    removeParameter,
  } = useParameterManager();

  const [isOpen, setIsOpen] = useState(false);
  const [editingParameter, setEditingParameter] = useState<string | null>(null);
  const [newParameter, setNewParameter] = useState<Partial<ParameterDefinition>>({
    name: '',
    label: '',
    type: 'string',
    scope: 'dashboard',
    widget_bindings: [],
    required: false,
  });

  // Get parameters grouped by scope
  const parametersByScope = useMemo(() => {
    const groups: Record<string, ParameterDefinition[]> = {
      global: [],
      dashboard: [],
      study: [],
    };

    Object.values(state.parameters).forEach(param => {
      groups[param.scope].push(param);
    });

    return groups;
  }, [state.parameters]);

  // Handle parameter value change
  const handleParameterChange = useCallback((parameterId: string, value: any) => {
    setParameterValue(parameterId, value);
  }, [setParameterValue]);

  // Handle save
  const handleSave = useCallback(async () => {
    try {
      await saveParameters();
      setIsOpen(false);
    } catch (error) {
      console.error('Failed to save parameters:', error);
    }
  }, [saveParameters]);

  // Handle reset
  const handleReset = useCallback(() => {
    resetToDefaults();
  }, [resetToDefaults]);

  // Handle create parameter
  const handleCreateParameter = useCallback(() => {
    if (!newParameter.name || !newParameter.label) {
      toast.error('Name and label are required');
      return;
    }

    addParameter({
      name: newParameter.name!,
      label: newParameter.label!,
      type: newParameter.type || 'string',
      description: newParameter.description,
      default_value: newParameter.default_value,
      required: newParameter.required || false,
      validation: newParameter.validation,
      scope: newParameter.scope || 'dashboard',
      widget_bindings: newParameter.widget_bindings || [],
    });

    // Reset form
    setNewParameter({
      name: '',
      label: '',
      type: 'string',
      scope: 'dashboard',
      widget_bindings: [],
      required: false,
    });

    toast.success('Parameter created successfully');
  }, [newParameter, addParameter]);

  // Handle edit parameter
  const handleEditParameter = useCallback((parameterId: string) => {
    setEditingParameter(parameterId);
  }, []);

  // Handle update parameter
  const handleUpdateParameter = useCallback((parameterId: string, updates: Partial<ParameterDefinition>) => {
    updateParameter(parameterId, updates);
    setEditingParameter(null);
    toast.success('Parameter updated successfully');
  }, [updateParameter]);

  // Handle delete parameter
  const handleDeleteParameter = useCallback((parameterId: string) => {
    removeParameter(parameterId);
  }, [removeParameter]);

  // Handle copy parameter link
  const handleCopyParameterLink = useCallback((parameter: ParameterDefinition) => {
    const link = `{{${parameter.name}}}`;
    navigator.clipboard.writeText(link);
    toast.success(`Parameter link copied: ${link}`);
  }, []);

  // Render parameter input based on type
  const renderParameterInput = (parameter: ParameterDefinition) => {
    const value = state.parameter_values[parameter.id];
    const error = state.validation_errors[parameter.id];

    switch (parameter.type) {
      case 'string':
        return (
          <div className="space-y-1">
            <Input
              value={value || ''}
              onChange={(e) => handleParameterChange(parameter.id, e.target.value)}
              placeholder={`Enter ${parameter.label.toLowerCase()}...`}
              className={error ? 'border-destructive' : ''}
            />
            {error && showValidationErrors && (
              <p className="text-sm text-destructive flex items-center gap-1">
                <AlertCircle className="h-3 w-3" />
                {error}
              </p>
            )}
          </div>
        );

      case 'number':
        return (
          <div className="space-y-1">
            <Input
              type="number"
              value={value || ''}
              onChange={(e) => handleParameterChange(parameter.id, e.target.value ? Number(e.target.value) : '')}
              placeholder={`Enter ${parameter.label.toLowerCase()}...`}
              min={parameter.validation?.min}
              max={parameter.validation?.max}
              className={error ? 'border-destructive' : ''}
            />
            {error && showValidationErrors && (
              <p className="text-sm text-destructive flex items-center gap-1">
                <AlertCircle className="h-3 w-3" />
                {error}
              </p>
            )}
          </div>
        );

      case 'boolean':
        return (
          <div className="flex items-center space-x-2">
            <Checkbox
              id={parameter.id}
              checked={value || false}
              onCheckedChange={(checked) => handleParameterChange(parameter.id, checked)}
            />
            <Label htmlFor={parameter.id}>Enable {parameter.label}</Label>
          </div>
        );

      case 'select':
        return (
          <div className="space-y-1">
            <Select value={value || ''} onValueChange={(newValue) => handleParameterChange(parameter.id, newValue)}>
              <SelectTrigger className={error ? 'border-destructive' : ''}>
                <SelectValue placeholder={`Select ${parameter.label.toLowerCase()}...`} />
              </SelectTrigger>
              <SelectContent>
                {parameter.validation?.options?.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {error && showValidationErrors && (
              <p className="text-sm text-destructive flex items-center gap-1">
                <AlertCircle className="h-3 w-3" />
                {error}
              </p>
            )}
          </div>
        );

      case 'multi_select':
        const selectedValues = Array.isArray(value) ? value : [];
        return (
          <div className="space-y-2">
            <div className="flex flex-wrap gap-2">
              {selectedValues.map((val) => {
                const option = parameter.validation?.options?.find(opt => opt.value === val);
                return (
                  <Badge key={val} variant="secondary" className="text-xs">
                    {option?.label || val}
                    <X
                      className="ml-1 h-3 w-3 cursor-pointer"
                      onClick={() => {
                        const newValues = selectedValues.filter(v => v !== val);
                        handleParameterChange(parameter.id, newValues);
                      }}
                    />
                  </Badge>
                );
              })}
            </div>
            <Select
              onValueChange={(newValue) => {
                if (!selectedValues.includes(newValue)) {
                  handleParameterChange(parameter.id, [...selectedValues, newValue]);
                }
              }}
            >
              <SelectTrigger className={error ? 'border-destructive' : ''}>
                <SelectValue placeholder={`Add ${parameter.label.toLowerCase()}...`} />
              </SelectTrigger>
              <SelectContent>
                {parameter.validation?.options?.filter(option => !selectedValues.includes(option.value)).map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {error && showValidationErrors && (
              <p className="text-sm text-destructive flex items-center gap-1">
                <AlertCircle className="h-3 w-3" />
                {error}
              </p>
            )}
          </div>
        );

      case 'date':
        return (
          <div className="space-y-1">
            <Popover>
              <PopoverTrigger asChild>
                <Button
                  variant="outline"
                  className={cn(
                    "w-full justify-start text-left font-normal",
                    !value && "text-muted-foreground",
                    error && "border-destructive"
                  )}
                >
                  <CalendarIcon className="mr-2 h-4 w-4" />
                  {value ? format(new Date(value), 'PPP') : `Select ${parameter.label.toLowerCase()}`}
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-auto p-0">
                <Calendar
                  mode="single"
                  selected={value ? new Date(value) : undefined}
                  onSelect={(date) => handleParameterChange(parameter.id, date ? format(date, 'yyyy-MM-dd') : '')}
                />
              </PopoverContent>
            </Popover>
            {error && showValidationErrors && (
              <p className="text-sm text-destructive flex items-center gap-1">
                <AlertCircle className="h-3 w-3" />
                {error}
              </p>
            )}
          </div>
        );

      case 'date_range':
        const [startDate, endDate] = Array.isArray(value) && value.length === 2 ? value : [null, null];
        return (
          <div className="space-y-2">
            <div className="grid grid-cols-2 gap-2">
              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    variant="outline"
                    className={cn(
                      "justify-start text-left font-normal",
                      !startDate && "text-muted-foreground",
                      error && "border-destructive"
                    )}
                  >
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {startDate ? format(new Date(startDate), 'MMM dd') : 'Start date'}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0">
                  <Calendar
                    mode="single"
                    selected={startDate ? new Date(startDate) : undefined}
                    onSelect={(date) => {
                      const newStart = date ? format(date, 'yyyy-MM-dd') : null;
                      handleParameterChange(parameter.id, [newStart, endDate]);
                    }}
                  />
                </PopoverContent>
              </Popover>
              
              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    variant="outline"
                    className={cn(
                      "justify-start text-left font-normal",
                      !endDate && "text-muted-foreground",
                      error && "border-destructive"
                    )}
                  >
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {endDate ? format(new Date(endDate), 'MMM dd') : 'End date'}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0">
                  <Calendar
                    mode="single"
                    selected={endDate ? new Date(endDate) : undefined}
                    onSelect={(date) => {
                      const newEnd = date ? format(date, 'yyyy-MM-dd') : null;
                      handleParameterChange(parameter.id, [startDate, newEnd]);
                    }}
                  />
                </PopoverContent>
              </Popover>
            </div>
            {error && showValidationErrors && (
              <p className="text-sm text-destructive flex items-center gap-1">
                <AlertCircle className="h-3 w-3" />
                {error}
              </p>
            )}
          </div>
        );

      default:
        return (
          <Input
            value={value || ''}
            onChange={(e) => handleParameterChange(parameter.id, e.target.value)}
            placeholder={`Enter ${parameter.label.toLowerCase()}...`}
          />
        );
    }
  };

  // Render parameter list section
  const renderParameterSection = (title: string, parameters: ParameterDefinition[]) => {
    if (parameters.length === 0) return null;

    return (
      <div className="space-y-3">
        <h4 className="font-medium text-sm text-muted-foreground uppercase tracking-wide">
          {title}
        </h4>
        <div className="space-y-4">
          {parameters.map((parameter) => (
            <div key={parameter.id} className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Label htmlFor={parameter.id} className="font-medium">
                    {parameter.label}
                    {parameter.required && <span className="text-destructive ml-1">*</span>}
                  </Label>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-5 w-5"
                    onClick={() => handleCopyParameterLink(parameter)}
                    title="Copy parameter link"
                  >
                    <Copy className="h-3 w-3" />
                  </Button>
                </div>
                <div className="flex items-center gap-1">
                  <Badge variant="outline" className="text-xs">
                    {parameter.type}
                  </Badge>
                  {parameter.widget_bindings.length > 0 && (
                    <Badge variant="secondary" className="text-xs">
                      <Link className="mr-1 h-3 w-3" />
                      {parameter.widget_bindings.length}
                    </Badge>
                  )}
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-5 w-5"
                    onClick={() => handleEditParameter(parameter.id)}
                  >
                    <Edit3 className="h-3 w-3" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-5 w-5"
                    onClick={() => handleDeleteParameter(parameter.id)}
                  >
                    <Trash2 className="h-3 w-3" />
                  </Button>
                </div>
              </div>
              
              {parameter.description && (
                <p className="text-sm text-muted-foreground">{parameter.description}</p>
              )}
              
              {renderParameterInput(parameter)}
            </div>
          ))}
        </div>
      </div>
    );
  };

  // Render content
  const content = (
    <div className="space-y-6">
      {/* Parameter sections */}
      {renderParameterSection('Global Parameters', parametersByScope.global)}
      {renderParameterSection('Dashboard Parameters', parametersByScope.dashboard)}
      {renderParameterSection('Study Parameters', parametersByScope.study)}

      {/* Add parameter button */}
      <div className="border-t pt-4">
        <Dialog>
          <DialogTrigger asChild>
            <Button variant="outline" className="w-full">
              <Plus className="mr-2 h-4 w-4" />
              Add Parameter
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>Create Parameter</DialogTitle>
            </DialogHeader>
            
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>Name</Label>
                <Input
                  value={newParameter.name || ''}
                  onChange={(e) => setNewParameter(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="parameter_name"
                />
              </div>
              
              <div className="space-y-2">
                <Label>Label</Label>
                <Input
                  value={newParameter.label || ''}
                  onChange={(e) => setNewParameter(prev => ({ ...prev, label: e.target.value }))}
                  placeholder="Display Label"
                />
              </div>
              
              <div className="space-y-2">
                <Label>Type</Label>
                <Select
                  value={newParameter.type || 'string'}
                  onValueChange={(value: any) => setNewParameter(prev => ({ ...prev, type: value }))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="string">Text</SelectItem>
                    <SelectItem value="number">Number</SelectItem>
                    <SelectItem value="boolean">Boolean</SelectItem>
                    <SelectItem value="date">Date</SelectItem>
                    <SelectItem value="date_range">Date Range</SelectItem>
                    <SelectItem value="select">Select</SelectItem>
                    <SelectItem value="multi_select">Multi Select</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div className="space-y-2">
                <Label>Description</Label>
                <Textarea
                  value={newParameter.description || ''}
                  onChange={(e) => setNewParameter(prev => ({ ...prev, description: e.target.value }))}
                  placeholder="Optional description..."
                  rows={2}
                />
              </div>
              
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="required"
                  checked={newParameter.required || false}
                  onCheckedChange={(checked) => setNewParameter(prev => ({ ...prev, required: checked as boolean }))}
                />
                <Label htmlFor="required">Required</Label>
              </div>
              
              <div className="flex justify-end gap-2 pt-4">
                <Button variant="outline" onClick={() => setNewParameter({})}>
                  Cancel
                </Button>
                <Button onClick={handleCreateParameter}>
                  Create Parameter
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Actions */}
      <div className="flex gap-2 pt-4 border-t">
        <Button onClick={handleSave} disabled={!state.has_unsaved_changes}>
          <Save className="mr-2 h-4 w-4" />
          Save Changes
        </Button>
        <Button variant="outline" onClick={handleReset}>
          <RotateCcw className="mr-2 h-4 w-4" />
          Reset to Defaults
        </Button>
      </div>

      {/* Status info */}
      {state.has_unsaved_changes && (
        <div className="text-sm text-muted-foreground">
          You have unsaved changes
        </div>
      )}
    </div>
  );

  // Render based on variant
  if (variant === 'inline') {
    return <div className={className}>{content}</div>;
  }

  if (variant === 'dialog') {
    return (
      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogTrigger asChild>
          {children || (
            <Button variant="outline" size="sm">
              <Settings className="mr-2 h-4 w-4" />
              Parameters
            </Button>
          )}
        </DialogTrigger>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Dashboard Parameters</DialogTitle>
          </DialogHeader>
          {content}
        </DialogContent>
      </Dialog>
    );
  }

  // Default to sheet
  return (
    <Sheet open={isOpen} onOpenChange={setIsOpen}>
      <SheetTrigger asChild>
        {children || (
          <Button variant="outline" size="sm">
            <Settings className="mr-2 h-4 w-4" />
            Parameters
          </Button>
        )}
      </SheetTrigger>
      <SheetContent className="w-96 overflow-y-auto">
        <SheetHeader>
          <SheetTitle>Dashboard Parameters</SheetTitle>
        </SheetHeader>
        <div className="mt-6">
          {content}
        </div>
      </SheetContent>
    </Sheet>
  );
}