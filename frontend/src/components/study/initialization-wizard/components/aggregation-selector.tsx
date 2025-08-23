// ABOUTME: Aggregation selector component for field mappings with numeric validation
// ABOUTME: Validates that numeric aggregations (sum, avg, min, max) are only available for numeric columns

import React from 'react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircle, Calculator } from 'lucide-react';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';

export type AggregationType = 'count' | 'count_distinct' | 'sum' | 'avg' | 'min' | 'max';

interface AggregationOption {
  value: AggregationType;
  label: string;
  description: string;
  requiresNumeric: boolean;
}

const AGGREGATION_OPTIONS: AggregationOption[] = [
  {
    value: 'count',
    label: 'Count All',
    description: 'Count all records',
    requiresNumeric: false
  },
  {
    value: 'count_distinct',
    label: 'Count Unique',
    description: 'Count unique/distinct values',
    requiresNumeric: false
  },
  {
    value: 'sum',
    label: 'Sum',
    description: 'Sum of all values',
    requiresNumeric: true
  },
  {
    value: 'avg',
    label: 'Average',
    description: 'Average (mean) of values',
    requiresNumeric: true
  },
  {
    value: 'min',
    label: 'Minimum',
    description: 'Minimum value',
    requiresNumeric: true
  },
  {
    value: 'max',
    label: 'Maximum',
    description: 'Maximum value',
    requiresNumeric: true
  }
];

interface AggregationSelectorProps {
  value: AggregationType;
  onChange: (value: AggregationType) => void;
  columnType?: string;
  columnName?: string;
  disabled?: boolean;
}

export function AggregationSelector({
  value,
  onChange,
  columnType,
  columnName,
  disabled = false
}: AggregationSelectorProps) {
  // Determine if the column is numeric based on type
  const isNumericColumn = columnType ? 
    ['int', 'integer', 'float', 'double', 'decimal', 'numeric', 'number', 'int64', 'float64'].some(
      type => columnType.toLowerCase().includes(type)
    ) : false;

  // Filter available options based on column type
  const availableOptions = AGGREGATION_OPTIONS.filter(option => {
    if (option.requiresNumeric && !isNumericColumn) {
      return false;
    }
    return true;
  });

  // Check if current selection is valid
  const currentOption = AGGREGATION_OPTIONS.find(opt => opt.value === value);
  const isInvalidSelection = currentOption?.requiresNumeric && !isNumericColumn;

  // Auto-correct invalid selection
  React.useEffect(() => {
    if (isInvalidSelection) {
      onChange('count_distinct'); // Default to count_distinct
    }
  }, [isInvalidSelection, onChange]);

  return (
    <div className="space-y-2">
      <Label className="flex items-center gap-2">
        <Calculator className="h-4 w-4" />
        Aggregation Method
      </Label>
      
      <Select
        value={value}
        onValueChange={(val) => onChange(val as AggregationType)}
        disabled={disabled}
      >
        <SelectTrigger className="w-full">
          <SelectValue placeholder="Select aggregation" />
        </SelectTrigger>
        <SelectContent>
          {availableOptions.map((option) => (
            <SelectItem key={option.value} value={option.value}>
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <div className="flex items-center justify-between w-full">
                      <span>{option.label}</span>
                      {option.requiresNumeric && (
                        <span className="text-xs text-muted-foreground ml-2">(numeric)</span>
                      )}
                    </div>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>{option.description}</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {!isNumericColumn && columnName && (
        <Alert className="mt-2">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Column <strong>{columnName}</strong> appears to be non-numeric.
            Only count operations are available.
          </AlertDescription>
        </Alert>
      )}

      {columnType && (
        <p className="text-xs text-muted-foreground">
          Column type: {columnType} {isNumericColumn ? '(numeric)' : '(non-numeric)'}
        </p>
      )}
    </div>
  );
}