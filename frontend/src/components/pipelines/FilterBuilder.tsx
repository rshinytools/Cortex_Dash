// ABOUTME: Visual filter builder for creating data filtering conditions
// ABOUTME: Provides intuitive UI for building complex filter logic

import React from 'react';
import { Plus, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { FilterCondition } from '@/lib/api/pipelines';

interface FilterBuilderProps {
  conditions: FilterCondition[];
  onChange: (conditions: FilterCondition[]) => void;
}

const OPERATORS = [
  { value: '==', label: 'Equals' },
  { value: '!=', label: 'Not Equals' },
  { value: '>', label: 'Greater Than' },
  { value: '>=', label: 'Greater Than or Equal' },
  { value: '<', label: 'Less Than' },
  { value: '<=', label: 'Less Than or Equal' },
  { value: 'contains', label: 'Contains' },
  { value: 'in', label: 'In List' },
];

export function FilterBuilder({ conditions, onChange }: FilterBuilderProps) {
  const addCondition = () => {
    onChange([
      ...conditions,
      {
        column: '',
        operator: '==',
        value: '',
      },
    ]);
  };

  const updateCondition = (index: number, updates: Partial<FilterCondition>) => {
    const newConditions = [...conditions];
    newConditions[index] = { ...newConditions[index], ...updates };
    onChange(newConditions);
  };

  const removeCondition = (index: number) => {
    onChange(conditions.filter((_, i) => i !== index));
  };

  return (
    <div className="space-y-4">
      {conditions.length === 0 ? (
        <div className="text-center py-8 border-2 border-dashed rounded-lg">
          <p className="text-sm text-gray-500 mb-4">No filter conditions added</p>
          <Button onClick={addCondition}>
            <Plus className="mr-2 h-4 w-4" />
            Add Filter Condition
          </Button>
        </div>
      ) : (
        <>
          <div className="space-y-3">
            {conditions.map((condition, index) => (
              <div key={index} className="flex items-center gap-2">
                <Input
                  placeholder="Column name"
                  value={condition.column}
                  onChange={(e) => updateCondition(index, { column: e.target.value })}
                  className="w-48"
                />
                
                <Select
                  value={condition.operator}
                  onValueChange={(value) => updateCondition(index, { operator: value as any })}
                >
                  <SelectTrigger className="w-48">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {OPERATORS.map((op) => (
                      <SelectItem key={op.value} value={op.value}>
                        {op.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>

                {condition.operator === 'in' ? (
                  <Input
                    placeholder="Comma-separated values"
                    value={Array.isArray(condition.value) ? condition.value.join(', ') : condition.value}
                    onChange={(e) => {
                      const values = e.target.value.split(',').map(v => v.trim());
                      updateCondition(index, { value: values });
                    }}
                    className="flex-1"
                  />
                ) : (
                  <Input
                    placeholder="Value"
                    value={condition.value}
                    onChange={(e) => updateCondition(index, { value: e.target.value })}
                    className="flex-1"
                  />
                )}

                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => removeCondition(index)}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            ))}
          </div>

          <Button variant="outline" onClick={addCondition}>
            <Plus className="mr-2 h-4 w-4" />
            Add Another Condition
          </Button>

          <div className="text-sm text-gray-500">
            <p>All conditions will be combined with AND logic.</p>
            <p>For "In List" operator, separate values with commas.</p>
          </div>
        </>
      )}
    </div>
  );
}