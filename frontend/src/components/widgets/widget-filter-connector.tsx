// ABOUTME: Widget filter connector component that integrates filtering capabilities into widgets
// ABOUTME: Handles filter creation, application, and real-time updates for widget data

'use client';

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { Calendar } from '@/components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { 
  Filter, 
  FilterX, 
  Plus, 
  Trash2, 
  Calendar as CalendarIcon,
  Check,
  X
} from 'lucide-react';
import { format } from 'date-fns';
import { cn } from '@/lib/utils';
import { useFilterManager, FilterDefinition, FilterValue } from './filter-manager';

interface FilterableField {
  field: string;
  label: string;
  type: 'string' | 'number' | 'date' | 'boolean' | 'select';
  options?: { value: any; label: string }[];
  dataset?: string;
}

interface WidgetFilterConnectorProps {
  widgetId: string;
  widgetType: string;
  availableFields: FilterableField[];
  onFilterCreate?: (filter: FilterDefinition) => void;
  onDataRefresh?: () => void;
  className?: string;
  children?: React.ReactNode;
}

export function WidgetFilterConnector({
  widgetId,
  widgetType,
  availableFields,
  onFilterCreate,
  onDataRefresh,
  className,
  children,
}: WidgetFilterConnectorProps) {
  const {
    addFilter,
    removeFilter,
    toggleFilter,
    clearWidgetFilters,
    getWidgetFilters,
    getActiveFilters,
    state,
  } = useFilterManager();

  const [isCreatingFilter, setIsCreatingFilter] = useState(false);
  const [newFilter, setNewFilter] = useState<{
    field: string;
    label: string;
    type: string;
    values: FilterValue[];
    scope: 'dashboard' | 'widget';
  }>({
    field: '',
    label: '',
    type: 'string',
    values: [],
    scope: 'dashboard',
  });

  // Get filters created by or affecting this widget
  const widgetFilters = useMemo(() => getWidgetFilters(widgetId), [widgetId, getWidgetFilters]);
  const activeFilters = useMemo(() => getActiveFilters(), [getActiveFilters]);

  // Check if widget is affected by any filters
  const isFiltered = useMemo(() => {
    return activeFilters.some(filter => 
      filter.widget_id !== widgetId && filter.source_widget_id !== widgetId
    );
  }, [activeFilters, widgetId]);

  // Handle creating a new filter
  const handleCreateFilter = useCallback(() => {
    if (!newFilter.field || newFilter.values.length === 0) return;

    const selectedField = availableFields.find(f => f.field === newFilter.field);
    if (!selectedField) return;

    const filterId = addFilter({
      field: newFilter.field,
      label: newFilter.label || selectedField.label,
      type: selectedField.type,
      widget_id: widgetId,
      scope: newFilter.scope,
      values: newFilter.values,
      active: true,
    });

    // Reset form
    setNewFilter({
      field: '',
      label: '',
      type: 'string',
      values: [],
      scope: 'dashboard',
    });
    setIsCreatingFilter(false);

    // Notify parent component
    if (onFilterCreate) {
      const createdFilter = state.filters[filterId];
      if (createdFilter) {
        onFilterCreate(createdFilter);
      }
    }

    // Trigger data refresh
    if (onDataRefresh) {
      onDataRefresh();
    }
  }, [newFilter, availableFields, addFilter, widgetId, onFilterCreate, onDataRefresh, state.filters]);

  // Handle field selection for new filter
  const handleFieldSelect = useCallback((fieldName: string) => {
    const field = availableFields.find(f => f.field === fieldName);
    if (field) {
      setNewFilter(prev => ({
        ...prev,
        field: fieldName,
        label: field.label,
        type: field.type,
        values: [],
      }));
    }
  }, [availableFields]);

  // Handle adding a value to the new filter
  const handleAddFilterValue = useCallback((value: any, operator = 'eq') => {
    if (!value) return;

    const filterValue: FilterValue = {
      value,
      operator: operator as FilterValue['operator'],
      label: typeof value === 'string' ? value : String(value),
    };

    setNewFilter(prev => ({
      ...prev,
      values: [...prev.values, filterValue],
    }));
  }, []);

  // Handle removing a value from the new filter
  const handleRemoveFilterValue = useCallback((index: number) => {
    setNewFilter(prev => ({
      ...prev,
      values: prev.values.filter((_, i) => i !== index),
    }));
  }, []);

  // Handle clearing all filters for this widget
  const handleClearWidgetFilters = useCallback(() => {
    clearWidgetFilters(widgetId);
    if (onDataRefresh) {
      onDataRefresh();
    }
  }, [clearWidgetFilters, widgetId, onDataRefresh]);

  // Handle removing a specific filter
  const handleRemoveFilter = useCallback((filterId: string) => {
    removeFilter(filterId);
    if (onDataRefresh) {
      onDataRefresh();
    }
  }, [removeFilter, onDataRefresh]);

  // Handle toggling a filter
  const handleToggleFilter = useCallback((filterId: string) => {
    toggleFilter(filterId);
    if (onDataRefresh) {
      onDataRefresh();
    }
  }, [toggleFilter, onDataRefresh]);

  // Trigger data refresh when filters change
  useEffect(() => {
    if (onDataRefresh && state.last_updated) {
      onDataRefresh();
    }
  }, [state.last_updated, onDataRefresh]);

  // Render filter value input based on field type
  const renderFilterValueInput = () => {
    const selectedField = availableFields.find(f => f.field === newFilter.field);
    if (!selectedField) return null;

    switch (selectedField.type) {
      case 'string':
        return (
          <div className="space-y-2">
            <Label>Filter Value</Label>
            <div className="flex gap-2">
              <Select defaultValue="contains">
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="eq">Equals</SelectItem>
                  <SelectItem value="contains">Contains</SelectItem>
                  <SelectItem value="starts_with">Starts with</SelectItem>
                  <SelectItem value="ends_with">Ends with</SelectItem>
                </SelectContent>
              </Select>
              <Input
                placeholder="Enter value..."
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    const operator = (e.currentTarget.previousElementSibling as any)?.value || 'contains';
                    handleAddFilterValue(e.currentTarget.value, operator);
                    e.currentTarget.value = '';
                  }
                }}
              />
              <Button
                type="button"
                variant="outline"
                size="icon"
                onClick={(e) => {
                  const input = (e.currentTarget.previousElementSibling as HTMLInputElement);
                  const select = input?.previousElementSibling as any;
                  const operator = select?.value || 'contains';
                  if (input?.value) {
                    handleAddFilterValue(input.value, operator);
                    input.value = '';
                  }
                }}
              >
                <Plus className="h-4 w-4" />
              </Button>
            </div>
          </div>
        );

      case 'number':
        return (
          <div className="space-y-2">
            <Label>Filter Value</Label>
            <div className="flex gap-2">
              <Select defaultValue="eq">
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="eq">Equals</SelectItem>
                  <SelectItem value="gt">Greater than</SelectItem>
                  <SelectItem value="gte">Greater or equal</SelectItem>
                  <SelectItem value="lt">Less than</SelectItem>
                  <SelectItem value="lte">Less or equal</SelectItem>
                </SelectContent>
              </Select>
              <Input
                type="number"
                placeholder="Enter number..."
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    const operator = (e.currentTarget.previousElementSibling as any)?.value || 'eq';
                    const value = parseFloat(e.currentTarget.value);
                    if (!isNaN(value)) {
                      handleAddFilterValue(value, operator);
                      e.currentTarget.value = '';
                    }
                  }
                }}
              />
              <Button
                type="button"
                variant="outline"
                size="icon"
                onClick={(e) => {
                  const input = (e.currentTarget.previousElementSibling as HTMLInputElement);
                  const select = input?.previousElementSibling as any;
                  const operator = select?.value || 'eq';
                  const value = parseFloat(input?.value || '');
                  if (!isNaN(value)) {
                    handleAddFilterValue(value, operator);
                    input.value = '';
                  }
                }}
              >
                <Plus className="h-4 w-4" />
              </Button>
            </div>
          </div>
        );

      case 'date':
        return (
          <div className="space-y-2">
            <Label>Filter Date</Label>
            <div className="flex gap-2">
              <Select defaultValue="eq">
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="eq">On</SelectItem>
                  <SelectItem value="gt">After</SelectItem>
                  <SelectItem value="gte">On or after</SelectItem>
                  <SelectItem value="lt">Before</SelectItem>
                  <SelectItem value="lte">On or before</SelectItem>
                </SelectContent>
              </Select>
              <Popover>
                <PopoverTrigger asChild>
                  <Button variant="outline" className="flex-1">
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    Select date
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0">
                  <Calendar
                    mode="single"
                    onSelect={(date) => {
                      if (date) {
                        // Get operator from select
                        const operator = 'eq'; // Default for now
                        handleAddFilterValue(format(date, 'yyyy-MM-dd'), operator);
                      }
                    }}
                  />
                </PopoverContent>
              </Popover>
            </div>
          </div>
        );

      case 'select':
        return (
          <div className="space-y-2">
            <Label>Filter Options</Label>
            <Select
              onValueChange={(value) => {
                const option = selectedField.options?.find(opt => opt.value === value);
                if (option) {
                  handleAddFilterValue(option.value, 'eq');
                }
              }}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select option..." />
              </SelectTrigger>
              <SelectContent>
                {selectedField.options?.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        );

      case 'boolean':
        return (
          <div className="space-y-2">
            <Label>Filter Value</Label>
            <div className="flex gap-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => handleAddFilterValue(true, 'eq')}
              >
                True
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => handleAddFilterValue(false, 'eq')}
              >
                False
              </Button>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className={cn("relative", className)}>
      {children}
      
      {/* Filter indicator and controls */}
      <div className="absolute top-2 left-2 z-10 flex items-center gap-2">
        {/* Active filters indicator */}
        {isFiltered && (
          <Badge variant="secondary" className="bg-blue-100 text-blue-800">
            <Filter className="mr-1 h-3 w-3" />
            Filtered
          </Badge>
        )}

        {/* Widget-specific filters */}
        {widgetFilters.length > 0 && (
          <div className="flex items-center gap-1">
            {widgetFilters.slice(0, 2).map((filter) => (
              <Badge
                key={filter.id}
                variant={filter.active ? "default" : "secondary"}
                className="text-xs cursor-pointer"
                onClick={() => handleToggleFilter(filter.id)}
              >
                {filter.label}
                {filter.active && (
                  <X
                    className="ml-1 h-3 w-3"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleRemoveFilter(filter.id);
                    }}
                  />
                )}
              </Badge>
            ))}
            {widgetFilters.length > 2 && (
              <Badge variant="outline" className="text-xs">
                +{widgetFilters.length - 2} more
              </Badge>
            )}
          </div>
        )}

        {/* Filter controls */}
        <div className="flex items-center gap-1">
          {/* Create filter button */}
          <Sheet open={isCreatingFilter} onOpenChange={setIsCreatingFilter}>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon" className="h-6 w-6">
                <Plus className="h-3 w-3" />
              </Button>
            </SheetTrigger>
            <SheetContent>
              <SheetHeader>
                <SheetTitle>Create Filter</SheetTitle>
              </SheetHeader>
              
              <div className="space-y-4 mt-6">
                {/* Field selection */}
                <div className="space-y-2">
                  <Label>Field</Label>
                  <Select value={newFilter.field} onValueChange={handleFieldSelect}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select field to filter..." />
                    </SelectTrigger>
                    <SelectContent>
                      {availableFields.map((field) => (
                        <SelectItem key={field.field} value={field.field}>
                          {field.label} ({field.type})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Filter scope */}
                <div className="space-y-2">
                  <Label>Scope</Label>
                  <Select value={newFilter.scope} onValueChange={(value: 'dashboard' | 'widget') => 
                    setNewFilter(prev => ({ ...prev, scope: value }))
                  }>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="widget">This widget only</SelectItem>
                      <SelectItem value="dashboard">All widgets on dashboard</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Filter label */}
                <div className="space-y-2">
                  <Label>Label (optional)</Label>
                  <Input
                    value={newFilter.label}
                    onChange={(e) => setNewFilter(prev => ({ ...prev, label: e.target.value }))}
                    placeholder="Custom filter label..."
                  />
                </div>

                {/* Filter values input */}
                {newFilter.field && renderFilterValueInput()}

                {/* Current filter values */}
                {newFilter.values.length > 0 && (
                  <div className="space-y-2">
                    <Label>Selected Values</Label>
                    <div className="flex flex-wrap gap-2">
                      {newFilter.values.map((value, index) => (
                        <Badge key={index} variant="outline" className="text-xs">
                          {value.operator !== 'eq' && `${value.operator} `}
                          {value.label || String(value.value)}
                          <X
                            className="ml-1 h-3 w-3 cursor-pointer"
                            onClick={() => handleRemoveFilterValue(index)}
                          />
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                {/* Actions */}
                <div className="flex justify-end gap-2 pt-4">
                  <Button
                    variant="outline"
                    onClick={() => setIsCreatingFilter(false)}
                  >
                    Cancel
                  </Button>
                  <Button
                    onClick={handleCreateFilter}
                    disabled={!newFilter.field || newFilter.values.length === 0}
                  >
                    Create Filter
                  </Button>
                </div>
              </div>
            </SheetContent>
          </Sheet>

          {/* Clear filters button */}
          {widgetFilters.length > 0 && (
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6"
              onClick={handleClearWidgetFilters}
              title="Clear widget filters"
            >
              <FilterX className="h-3 w-3" />
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}

// Hook for widgets to create filters from user interactions
export function useWidgetFilterCreator(widgetId: string) {
  const { addFilter } = useFilterManager();

  const createFilterFromSelection = useCallback((
    field: string,
    label: string,
    values: any[],
    fieldType: FilterableField['type'] = 'string',
    scope: 'dashboard' | 'widget' = 'dashboard'
  ) => {
    const filterValues: FilterValue[] = values.map(value => ({
      value,
      label: String(value),
      operator: 'eq' as const,
    }));

    return addFilter({
      field,
      label,
      type: fieldType,
      widget_id: widgetId,
      source_widget_id: widgetId,
      scope,
      values: filterValues,
      active: true,
    });
  }, [addFilter, widgetId]);

  const createDrillDownFilter = useCallback((
    field: string,
    label: string,
    value: any,
    fieldType: FilterableField['type'] = 'string'
  ) => {
    const filterValue: FilterValue = {
      value,
      label: String(value),
      operator: 'eq',
    };

    return addFilter({
      field,
      label: `Drill-down: ${label}`,
      type: fieldType,
      widget_id: widgetId,
      source_widget_id: widgetId,
      scope: 'dashboard',
      values: [filterValue],
      active: true,
      temporary: true,
    });
  }, [addFilter, widgetId]);

  return {
    createFilterFromSelection,
    createDrillDownFilter,
  };
}