// ABOUTME: SQL filter builder component for widget filtering
// ABOUTME: Provides UI for creating and validating SQL WHERE clause expressions

import React, { useState, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Textarea } from '@/components/ui/textarea';
import { api } from '@/lib/api-config';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Info,
  AlertCircle,
  CheckCircle,
  Filter,
  Code,
  Eye,
  Play,
  Loader2,
  X,
  Plus,
  Database,
  Columns,
  HelpCircle,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface FilterBuilderProps {
  studyId: string;
  widgetId: string;
  datasetName: string;
  columns?: string[];
  currentFilter?: string;
  onSave: (filter: string) => void;
  onCancel?: () => void;
  className?: string;
}

interface ValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
  validatedColumns: Array<{
    name: string;
    type: string;
  }>;
  complexity?: number;
}

interface TestResult {
  success: boolean;
  rowCount: number;
  originalCount: number;
  executionTimeMs: number;
  sampleData?: any[];
  error?: string;
}

const OPERATORS = [
  { value: '=', label: 'Equals (=)', description: 'Exact match' },
  { value: '!=', label: 'Not Equals (!=)', description: 'Not matching' },
  { value: '>', label: 'Greater Than (>)', description: 'Value is greater' },
  { value: '>=', label: 'Greater or Equal (>=)', description: 'Value is greater or equal' },
  { value: '<', label: 'Less Than (<)', description: 'Value is less' },
  { value: '<=', label: 'Less or Equal (<=)', description: 'Value is less or equal' },
  { value: 'LIKE', label: 'Like (LIKE)', description: 'Pattern matching with %' },
  { value: 'NOT LIKE', label: 'Not Like (NOT LIKE)', description: 'Pattern not matching' },
  { value: 'IN', label: 'In List (IN)', description: 'Value in list' },
  { value: 'NOT IN', label: 'Not In List (NOT IN)', description: 'Value not in list' },
  { value: 'IS NULL', label: 'Is Null', description: 'Value is null' },
  { value: 'IS NOT NULL', label: 'Is Not Null', description: 'Value is not null' },
  { value: 'BETWEEN', label: 'Between', description: 'Value in range' },
];

const SAMPLE_FILTERS = [
  { label: 'Serious AEs only', value: "AESER = 'Y'" },
  { label: 'Non-serious AEs', value: "AESER = 'N'" },
  { label: 'Active subjects', value: "STATUS = 'ACTIVE'" },
  { label: 'Age 18 or older', value: 'AGE >= 18' },
  { label: 'Age 65 or older', value: 'AGE >= 65' },
  { label: 'USA or Canada', value: "COUNTRY IN ('USA', 'CANADA')" },
  { label: 'High severity', value: "AESEV IN ('SEVERE', 'LIFE THREATENING')" },
  { label: 'Completed visits', value: "VISITSTAT = 'COMPLETED'" },
  { label: 'Discontinued subjects', value: "DCSREAS IS NOT NULL" },
];

export function FilterBuilder({
  studyId,
  widgetId,
  datasetName,
  columns = [],
  currentFilter = '',
  onSave,
  onCancel,
  className,
}: FilterBuilderProps) {
  const [expression, setExpression] = useState(currentFilter);
  const [isValidating, setIsValidating] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
  const [testResult, setTestResult] = useState<TestResult | null>(null);
  const [showHelp, setShowHelp] = useState(false);
  const [activeTab, setActiveTab] = useState('builder');
  const [showSampleData, setShowSampleData] = useState(false);

  // Validate filter expression
  const validateFilter = useCallback(async () => {
    if (!expression.trim()) {
      setValidationResult(null);
      return;
    }

    setIsValidating(true);
    try {
      const response = await api.post(
        `/studies/${studyId}/widgets/${widgetId}/filter/validate`,
        {
          widget_id: widgetId,
          expression: expression.trim(), // Trim whitespace
          dataset_name: datasetName,
        }
      );

      if (response.ok) {
        const result = await response.json();
        setValidationResult({
          isValid: result.is_valid || false,
          errors: result.errors || [],
          warnings: result.warnings || [],
          validatedColumns: result.validated_columns || [],
          complexity: result.complexity
        });
      } else {
        const errorData = await response.json().catch(() => null);
        const errorMessage = errorData?.detail || `Validation failed (${response.status})`;
        
        console.error('Validation response error:', errorData);
        
        setValidationResult({
          isValid: false,
          errors: [errorMessage],
          warnings: [],
          validatedColumns: [],
        });
      }
    } catch (error) {
      console.error('Validation error:', error);
      setValidationResult({
        isValid: false,
        errors: [`Network error: ${error instanceof Error ? error.message : 'Unable to validate filter'}`],
        warnings: [],
        validatedColumns: [],
      });
    } finally {
      setIsValidating(false);
    }
  }, [expression, studyId, widgetId, datasetName]);

  // Test filter on actual data
  const testFilter = useCallback(async () => {
    if (!expression.trim() || !validationResult?.isValid) {
      return;
    }

    setIsTesting(true);
    try {
      const response = await api.post(
        `/studies/${studyId}/widgets/${widgetId}/filter/test`,
        {
          widget_id: widgetId,
          expression,
          dataset_name: datasetName,
          limit: 10,
        }
      );

      if (response.ok) {
        const result = await response.json();
        // Convert snake_case from backend to camelCase for frontend
        setTestResult({
          success: result.success,
          rowCount: result.row_count || 0,
          originalCount: result.original_count || 0,
          executionTimeMs: result.execution_time_ms || 0,
          sampleData: result.sample_data,
          error: result.error
        });
      } else {
        setTestResult({
          success: false,
          rowCount: 0,
          originalCount: 0,
          executionTimeMs: 0,
          error: 'Failed to test filter',
        });
      }
    } catch (error) {
      console.error('Test error:', error);
      setTestResult({
        success: false,
        rowCount: 0,
        originalCount: 0,
        executionTimeMs: 0,
        error: 'Network error during test',
      });
    } finally {
      setIsTesting(false);
    }
  }, [expression, validationResult, studyId, widgetId, datasetName]);

  // Debounced validation
  useEffect(() => {
    const timer = setTimeout(() => {
      if (expression) {
        // Only validate if expression looks complete
        const trimmed = expression.trim();
        
        // Check if it's a complete expression with value
        const looksComplete = 
          // Has comparison with value
          (trimmed.includes('=') && trimmed.split('=')[1]?.trim().length > 0) ||
          (trimmed.includes('!=') && trimmed.split('!=')[1]?.trim().length > 0) ||
          (trimmed.includes('>') && !trimmed.includes('>=') && trimmed.split('>')[1]?.trim().length > 0) ||
          (trimmed.includes('>=') && trimmed.split('>=')[1]?.trim().length > 0) ||
          (trimmed.includes('<') && !trimmed.includes('<=') && trimmed.split('<')[1]?.trim().length > 0) ||
          (trimmed.includes('<=') && trimmed.split('<=')[1]?.trim().length > 0) ||
          // Has LIKE with pattern
          (trimmed.includes('LIKE') && trimmed.split('LIKE')[1]?.trim().length > 0) ||
          // Has IN with values
          (trimmed.includes(' IN ') && trimmed.includes('(') && trimmed.includes(')')) ||
          // Has NULL checks (these are complete by themselves)
          trimmed.includes('IS NULL') || trimmed.includes('IS NOT NULL') ||
          // Has BETWEEN with values
          (trimmed.includes('BETWEEN') && trimmed.includes('AND'));
        
        if (looksComplete) {
          validateFilter();
        } else {
          // Clear validation for incomplete expressions
          setValidationResult(null);
        }
      } else {
        setValidationResult(null);
      }
    }, 1000); // Give user time to type

    return () => clearTimeout(timer);
  }, [expression, validateFilter]);

  const handleSave = () => {
    if (validationResult?.isValid) {
      onSave(expression);
    }
  };

  const insertOperator = (operator: string) => {
    // For NULL operators, don't add if already ends with them
    if (operator === 'IS NULL' || operator === 'IS NOT NULL') {
      // Check if expression already ends with IS NULL or IS NOT NULL
      const trimmed = expression.trim();
      if (trimmed.endsWith('IS NULL') || trimmed.endsWith('IS NOT NULL')) {
        return; // Don't add duplicate
      }
      // Add the operator without expecting a value after
      const newExpression = expression ? `${expression.trim()} ${operator}` : operator;
      setExpression(newExpression);
    } else if (operator === 'BETWEEN') {
      // BETWEEN needs special handling
      const newExpression = expression ? `${expression.trim()} ${operator} ` : `${operator} `;
      setExpression(newExpression);
    } else {
      // For other operators, check we're not adding duplicate operators
      const trimmed = expression.trim();
      const lastChar = trimmed[trimmed.length - 1];
      const isOperatorChar = ['=', '!', '>', '<'].includes(lastChar);
      const endsWithOperator = trimmed.endsWith(' IN') || trimmed.endsWith(' LIKE') || 
                               trimmed.endsWith('NOT IN') || trimmed.endsWith('NOT LIKE');
      
      if (isOperatorChar || endsWithOperator) {
        return; // Don't add another operator
      }
      
      const newExpression = expression ? `${expression.trim()} ${operator} ` : `${operator} `;
      setExpression(newExpression);
    }
  };

  const insertColumn = (column: string) => {
    // Smart insertion: if expression ends with operator, just append
    // If it's empty or complete, start new condition
    const trimmed = expression.trim();
    
    if (!trimmed) {
      // Empty expression, just add column
      setExpression(column);
    } else if (trimmed.endsWith('=') || trimmed.endsWith('!=') || 
               trimmed.endsWith('>') || trimmed.endsWith('>=') ||
               trimmed.endsWith('<') || trimmed.endsWith('<=') ||
               trimmed.endsWith(' IN') || trimmed.endsWith(' LIKE') ||
               trimmed.endsWith('NOT IN') || trimmed.endsWith('NOT LIKE')) {
      // Ends with operator, add space and column
      setExpression(`${trimmed} ${column}`);
    } else if (trimmed.endsWith('AND') || trimmed.endsWith('OR')) {
      // Ends with logical operator, add space and column
      setExpression(`${trimmed} ${column}`);
    } else {
      // Complete expression, add AND and column
      setExpression(`${trimmed} AND ${column}`);
    }
  };

  const insertSampleFilter = (filter: string) => {
    setExpression(filter);
  };

  return (
    <>
      <Card className={cn('w-full', className)}>
        <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            <CardTitle>Widget Filter</CardTitle>
          </div>
          <div className="flex items-center gap-2">
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => setShowHelp(!showHelp)}
                  >
                    <HelpCircle className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Show filter syntax help</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
        </div>
        <CardDescription>
          Apply SQL WHERE clause filters to limit widget data
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-4">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="builder">Build Filter</TabsTrigger>
            <TabsTrigger value="preview">Test & Preview</TabsTrigger>
          </TabsList>

          <TabsContent value="builder" className="space-y-4">
            {/* Expression Input */}
            <div className="space-y-2">
              <Label htmlFor="filter-expression" className="text-sm font-medium">
                Filter Expression
              </Label>
              <div className="flex gap-2">
                <Textarea
                  id="filter-expression"
                  value={expression}
                  onChange={(e) => setExpression(e.target.value)}
                  placeholder="Enter SQL WHERE clause (e.g., AESER = 'Y' AND AGE >= 18)"
                  className="flex-1 font-mono text-sm min-h-[80px]"
                />
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => {
                    setExpression('');
                    setValidationResult(null);
                    setTestResult(null);
                  }}
                  disabled={!expression}
                  title="Clear expression"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </div>

            {/* Quick Insert Sections */}
            <div className="space-y-4">
              {/* Columns */}
              <div>
                <Label className="text-sm font-medium mb-2">Available Columns</Label>
                {columns.length > 0 ? (
                  <div className="flex flex-wrap gap-2 mt-2">
                    {columns.map((column) => (
                      <Button
                        key={column}
                        variant="outline"
                        size="sm"
                        onClick={() => insertColumn(column)}
                        className="h-7"
                      >
                        <Columns className="h-3 w-3 mr-1" />
                        {column}
                      </Button>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground mt-2">
                    No columns available. Please ensure dataset is selected.
                  </p>
                )}
              </div>

              {/* Operators */}
              <div>
                <Label className="text-sm font-medium mb-2">Operators</Label>
                <div className="grid grid-cols-4 gap-2 mt-2">
                  {OPERATORS.map((op) => (
                    <TooltipProvider key={op.value}>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => insertOperator(op.value)}
                            className="h-8 text-xs"
                          >
                            {op.label}
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>{op.description}</p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  ))}
                </div>
              </div>

              {/* Common Values */}
              <div>
                <Label className="text-sm font-medium mb-2">Common Values</Label>
                <div className="flex flex-wrap gap-2 mt-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setExpression(`${expression}'Y'`)}
                    className="h-7"
                  >
                    'Y'
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setExpression(`${expression}'N'`)}
                    className="h-7"
                  >
                    'N'
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setExpression(`${expression}'ACTIVE'`)}
                    className="h-7"
                  >
                    'ACTIVE'
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setExpression(`${expression}'COMPLETED'`)}
                    className="h-7"
                  >
                    'COMPLETED'
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setExpression(`${expression}1`)}
                    className="h-7"
                  >
                    1
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setExpression(`${expression}0`)}
                    className="h-7"
                  >
                    0
                  </Button>
                </div>
              </div>

              {/* Logical Operators */}
              <div>
                <Label className="text-sm font-medium mb-2">Logical Operators</Label>
                <div className="flex gap-2 mt-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      const trimmed = expression.trim();
                      if (trimmed && !trimmed.endsWith('AND') && !trimmed.endsWith('OR')) {
                        setExpression(`${trimmed} AND `);
                      }
                    }}
                    disabled={!expression || expression.trim().endsWith('AND') || expression.trim().endsWith('OR')}
                  >
                    AND
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      const trimmed = expression.trim();
                      if (trimmed && !trimmed.endsWith('AND') && !trimmed.endsWith('OR')) {
                        setExpression(`${trimmed} OR `);
                      }
                    }}
                    disabled={!expression || expression.trim().endsWith('AND') || expression.trim().endsWith('OR')}
                  >
                    OR
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setExpression(`${expression}(`)}
                  >
                    ( )
                  </Button>
                </div>
              </div>

              {/* Sample Filters */}
              <div>
                <Label className="text-sm font-medium mb-2">Sample Filters</Label>
                <Select onValueChange={insertSampleFilter}>
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Choose a sample filter..." />
                  </SelectTrigger>
                  <SelectContent>
                    {SAMPLE_FILTERS.map((filter) => (
                      <SelectItem key={filter.value} value={filter.value}>
                        {filter.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="preview" className="space-y-4">
            {testResult && (
              <div className="space-y-4">
                <div className="grid grid-cols-3 gap-4">
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm">Original Rows</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-2xl font-bold">{testResult.originalCount}</p>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm">Filtered Rows</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-2xl font-bold">{testResult.rowCount}</p>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm">Reduction</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-2xl font-bold">
                        {Math.round(((testResult.originalCount - testResult.rowCount) / testResult.originalCount) * 100)}%
                      </p>
                    </CardContent>
                  </Card>
                </div>

                {testResult.sampleData && testResult.sampleData.length > 0 && (
                  <div className="flex justify-center">
                    <Button
                      variant="outline"
                      onClick={() => setShowSampleData(true)}
                      className="w-full max-w-sm"
                    >
                      <Eye className="h-4 w-4 mr-2" />
                      Show Sample Data ({testResult.sampleData.length} rows)
                    </Button>
                  </div>
                )}
              </div>
            )}

            {!testResult && (
              <Alert>
                <Info className="h-4 w-4" />
                <AlertDescription>
                  Click "Test Filter" to preview how the filter affects your data
                </AlertDescription>
              </Alert>
            )}
          </TabsContent>
        </Tabs>

        {/* Validation Results */}
        {isValidating && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-3 w-3 animate-spin" />
            Validating...
          </div>
        )}
        
        {validationResult && (
          <div className="space-y-2">
            {validationResult.isValid ? (
              <Alert className="border-green-200 bg-green-50">
                <CheckCircle className="h-4 w-4 text-green-600" />
                <AlertDescription className="text-green-800">
                  Filter is valid and ready to use
                  {validationResult.validatedColumns.length > 0 && (
                    <div className="mt-2">
                      <span className="font-medium">Columns used: </span>
                      {validationResult.validatedColumns.map((col) => (
                        <Badge key={col.name} variant="secondary" className="ml-1">
                          {col.name} ({col.type})
                        </Badge>
                      ))}
                    </div>
                  )}
                </AlertDescription>
              </Alert>
            ) : (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  {validationResult.errors.map((error, idx) => (
                    <div key={idx}>{error}</div>
                  ))}
                </AlertDescription>
              </Alert>
            )}

            {validationResult.warnings.length > 0 && (
              <Alert className="border-yellow-200 bg-yellow-50">
                <AlertCircle className="h-4 w-4 text-yellow-600" />
                <AlertDescription className="text-yellow-800">
                  {validationResult.warnings.map((warning, idx) => (
                    <div key={idx}>{warning}</div>
                  ))}
                </AlertDescription>
              </Alert>
            )}
          </div>
        )}

        {/* Help Section */}
        {showHelp && (
          <Alert>
            <Info className="h-4 w-4" />
            <AlertDescription>
              <div className="space-y-2 text-sm">
                <p className="font-medium">Filter Syntax Examples:</p>
                <ul className="list-disc list-inside space-y-1">
                  <li>Simple comparison: <code>AGE >= 18</code></li>
                  <li>Multiple conditions: <code>AGE >= 18 AND AESER = 'Y'</code></li>
                  <li>List matching: <code>COUNTRY IN ('USA', 'UK')</code></li>
                  <li>Pattern matching: <code>AETERM LIKE '%headache%'</code></li>
                  <li>Null checking: <code>DISCONTINUED IS NULL</code></li>
                  <li>Range: <code>AGE BETWEEN 18 AND 65</code></li>
                  <li>Complex: <code>(AESER = 'Y' AND AGE >= 65) OR AESEV = 'SEVERE'</code></li>
                </ul>
              </div>
            </AlertDescription>
          </Alert>
        )}

        {/* Action Buttons */}
        <div className="flex justify-between gap-2">
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={testFilter}
              disabled={!expression || !validationResult?.isValid || isTesting}
            >
              {isTesting ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Testing...
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 mr-2" />
                  Test Filter
                </>
              )}
            </Button>
          </div>

          <div className="flex gap-2">
            {onCancel && (
              <Button variant="outline" onClick={onCancel}>
                Cancel
              </Button>
            )}
            <Button
              onClick={handleSave}
              disabled={!expression || !validationResult?.isValid}
            >
              <CheckCircle className="h-4 w-4 mr-2" />
              Apply Filter
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>

    {/* Sample Data Dialog */}
    <Dialog open={showSampleData} onOpenChange={setShowSampleData}>
      <DialogContent className="max-w-5xl max-h-[80vh]">
        <DialogHeader>
          <DialogTitle>Sample Data Preview</DialogTitle>
          <DialogDescription>
            Showing first {testResult?.sampleData?.length || 0} rows after applying the filter
          </DialogDescription>
        </DialogHeader>
        
        <div className="overflow-auto max-h-[60vh]">
          {testResult?.sampleData && testResult.sampleData.length > 0 && (
            <div className="border rounded-lg">
              <table className="w-full text-sm">
                <thead className="bg-muted sticky top-0 z-10">
                  <tr>
                    {Object.keys(testResult.sampleData[0]).map((key) => (
                      <th key={key} className="px-3 py-2 text-left font-medium border-b">
                        {key}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {testResult.sampleData.map((row, idx) => (
                    <tr key={idx} className="border-b hover:bg-muted/50">
                      {Object.values(row).map((value: any, vidx) => (
                        <td key={vidx} className="px-3 py-2 text-xs">
                          {value?.toString() || '-'}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button onClick={() => setShowSampleData(false)}>
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
    </>
  );
}