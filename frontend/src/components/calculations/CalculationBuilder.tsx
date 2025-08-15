// ABOUTME: Visual calculation builder component for creating complex expressions
// ABOUTME: Provides drag-and-drop interface and function palette for building calculations

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import {
  AlertCircle,
  Plus,
  Calculator,
  FunctionSquare,
  Database,
  Calendar,
  Hash,
  Type,
  Clock,
  TrendingUp,
  Activity,
  Heart,
  TestTube,
  Play,
  Code,
  HelpCircle,
  Copy,
  Trash2
} from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useToast } from '@/components/ui/use-toast';
import MonacoEditor from '@monaco-editor/react';

interface CalculationBuilderProps {
  initialExpression?: string;
  availableFields?: Field[];
  onSave?: (calculation: Calculation) => void;
  onTest?: (expression: string, testData: any) => Promise<any>;
}

interface Field {
  name: string;
  type: 'string' | 'number' | 'date' | 'boolean';
  description?: string;
}

interface Calculation {
  name: string;
  expression: string;
  description: string;
  output_type: string;
  variables: string[];
}

interface FunctionDef {
  name: string;
  category: string;
  description: string;
  syntax: string;
  example: string;
  params: Array<{
    name: string;
    type: string;
    description: string;
    required: boolean;
  }>;
}

const functionLibrary: FunctionDef[] = [
  // Math Functions
  {
    name: 'abs',
    category: 'Math',
    description: 'Returns absolute value',
    syntax: 'abs(value)',
    example: 'abs(-5) → 5',
    params: [
      { name: 'value', type: 'number', description: 'Input value', required: true }
    ]
  },
  {
    name: 'round',
    category: 'Math',
    description: 'Rounds to nearest integer or decimal places',
    syntax: 'round(value, decimals)',
    example: 'round(3.14159, 2) → 3.14',
    params: [
      { name: 'value', type: 'number', description: 'Value to round', required: true },
      { name: 'decimals', type: 'number', description: 'Decimal places', required: false }
    ]
  },
  {
    name: 'sqrt',
    category: 'Math',
    description: 'Square root',
    syntax: 'sqrt(value)',
    example: 'sqrt(16) → 4',
    params: [
      { name: 'value', type: 'number', description: 'Input value', required: true }
    ]
  },
  {
    name: 'pow',
    category: 'Math',
    description: 'Power/Exponentiation',
    syntax: 'pow(base, exponent)',
    example: 'pow(2, 3) → 8',
    params: [
      { name: 'base', type: 'number', description: 'Base value', required: true },
      { name: 'exponent', type: 'number', description: 'Exponent', required: true }
    ]
  },
  
  // Statistical Functions
  {
    name: 'mean',
    category: 'Statistics',
    description: 'Calculate average/mean',
    syntax: 'mean(values)',
    example: 'mean([1, 2, 3, 4, 5]) → 3',
    params: [
      { name: 'values', type: 'array', description: 'Array of numbers', required: true }
    ]
  },
  {
    name: 'median',
    category: 'Statistics',
    description: 'Calculate median value',
    syntax: 'median(values)',
    example: 'median([1, 2, 3, 4, 5]) → 3',
    params: [
      { name: 'values', type: 'array', description: 'Array of numbers', required: true }
    ]
  },
  {
    name: 'stdev',
    category: 'Statistics',
    description: 'Standard deviation',
    syntax: 'stdev(values)',
    example: 'stdev([1, 2, 3, 4, 5]) → 1.58',
    params: [
      { name: 'values', type: 'array', description: 'Array of numbers', required: true }
    ]
  },
  
  // Clinical Functions
  {
    name: 'calculate_bmi',
    category: 'Clinical',
    description: 'Calculate Body Mass Index',
    syntax: 'calculate_bmi(weight_kg, height_cm)',
    example: 'calculate_bmi(70, 175) → 22.9',
    params: [
      { name: 'weight_kg', type: 'number', description: 'Weight in kg', required: true },
      { name: 'height_cm', type: 'number', description: 'Height in cm', required: true }
    ]
  },
  {
    name: 'calculate_bsa',
    category: 'Clinical',
    description: 'Calculate Body Surface Area (DuBois)',
    syntax: 'calculate_bsa(weight_kg, height_cm)',
    example: 'calculate_bsa(70, 175) → 1.85',
    params: [
      { name: 'weight_kg', type: 'number', description: 'Weight in kg', required: true },
      { name: 'height_cm', type: 'number', description: 'Height in cm', required: true }
    ]
  },
  {
    name: 'calculate_egfr',
    category: 'Clinical',
    description: 'Calculate estimated GFR (CKD-EPI)',
    syntax: 'calculate_egfr(creatinine, age, sex, race)',
    example: 'calculate_egfr(1.2, 45, "M", "other") → 75.3',
    params: [
      { name: 'creatinine', type: 'number', description: 'Serum creatinine mg/dL', required: true },
      { name: 'age', type: 'number', description: 'Age in years', required: true },
      { name: 'sex', type: 'string', description: 'Sex (M/F)', required: true },
      { name: 'race', type: 'string', description: 'Race (black/other)', required: false }
    ]
  },
  
  // Logical Functions
  {
    name: 'if_else',
    category: 'Logical',
    description: 'Conditional expression',
    syntax: 'if_else(condition, true_value, false_value)',
    example: 'if_else(age >= 18, "Adult", "Minor")',
    params: [
      { name: 'condition', type: 'boolean', description: 'Condition to test', required: true },
      { name: 'true_value', type: 'any', description: 'Value if true', required: true },
      { name: 'false_value', type: 'any', description: 'Value if false', required: true }
    ]
  },
  
  // Date Functions
  {
    name: 'date_diff',
    category: 'Date',
    description: 'Difference between dates',
    syntax: 'date_diff(date1, date2, unit)',
    example: 'date_diff(visit_date, baseline_date, "days")',
    params: [
      { name: 'date1', type: 'date', description: 'First date', required: true },
      { name: 'date2', type: 'date', description: 'Second date', required: true },
      { name: 'unit', type: 'string', description: 'Unit (days/months/years)', required: false }
    ]
  },
  {
    name: 'age',
    category: 'Date',
    description: 'Calculate age from birth date',
    syntax: 'age(birth_date, reference_date)',
    example: 'age(dob, visit_date)',
    params: [
      { name: 'birth_date', type: 'date', description: 'Date of birth', required: true },
      { name: 'reference_date', type: 'date', description: 'Reference date', required: false }
    ]
  }
];

export function CalculationBuilder({ 
  initialExpression = '', 
  availableFields = [], 
  onSave, 
  onTest 
}: CalculationBuilderProps) {
  const [calculation, setCalculation] = useState<Calculation>({
    name: '',
    expression: initialExpression,
    description: '',
    output_type: 'number',
    variables: []
  });
  
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [testData, setTestData] = useState<Record<string, any>>({});
  const [testResult, setTestResult] = useState<any>(null);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [showHelp, setShowHelp] = useState(false);
  const { toast } = useToast();

  // Extract variables from expression
  useEffect(() => {
    const variablePattern = /\b[a-zA-Z_][a-zA-Z0-9_]*\b/g;
    const matches = calculation.expression.match(variablePattern) || [];
    const uniqueVars = [...new Set(matches)].filter(v => 
      !functionLibrary.some(f => f.name === v) &&
      !['true', 'false', 'null', 'undefined'].includes(v)
    );
    setCalculation(prev => ({ ...prev, variables: uniqueVars }));
  }, [calculation.expression]);

  const categories = ['all', ...new Set(functionLibrary.map(f => f.category))];

  const filteredFunctions = functionLibrary.filter(func => {
    const matchesCategory = selectedCategory === 'all' || func.category === selectedCategory;
    const matchesSearch = func.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          func.description.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  const insertFunction = (func: FunctionDef) => {
    const insertion = func.syntax;
    setCalculation(prev => ({
      ...prev,
      expression: prev.expression + (prev.expression ? ' ' : '') + insertion
    }));
  };

  const insertField = (field: Field) => {
    setCalculation(prev => ({
      ...prev,
      expression: prev.expression + (prev.expression ? ' ' : '') + field.name
    }));
  };

  const insertOperator = (operator: string) => {
    setCalculation(prev => ({
      ...prev,
      expression: prev.expression + ' ' + operator + ' '
    }));
  };

  const validateExpression = async () => {
    try {
      const response = await fetch('/api/v1/calculations/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ expression: calculation.expression })
      });
      
      if (response.ok) {
        const result = await response.json();
        if (result.valid) {
          setValidationError(null);
          toast({
            title: 'Valid Expression',
            description: 'The calculation expression is syntactically correct',
          });
        } else {
          setValidationError(result.error);
        }
      }
    } catch (error) {
      toast({
        title: 'Validation Error',
        description: 'Failed to validate expression',
        variant: 'destructive',
      });
    }
  };

  const testExpression = async () => {
    if (!onTest) {
      toast({
        title: 'Test Not Available',
        description: 'Test function not provided',
        variant: 'destructive',
      });
      return;
    }

    try {
      const result = await onTest(calculation.expression, testData);
      setTestResult(result);
      toast({
        title: 'Test Successful',
        description: `Result: ${JSON.stringify(result)}`,
      });
    } catch (error) {
      toast({
        title: 'Test Failed',
        description: error instanceof Error ? error.message : 'Unknown error',
        variant: 'destructive',
      });
    }
  };

  const handleSave = () => {
    if (!calculation.name) {
      toast({
        title: 'Validation Error',
        description: 'Please provide a name for the calculation',
        variant: 'destructive',
      });
      return;
    }

    if (!calculation.expression) {
      toast({
        title: 'Validation Error',
        description: 'Please provide an expression',
        variant: 'destructive',
      });
      return;
    }

    if (onSave) {
      onSave(calculation);
      toast({
        title: 'Success',
        description: 'Calculation saved successfully',
      });
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Calculation Builder</h2>
          <p className="text-muted-foreground">
            Build complex calculations using functions and fields
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setShowHelp(!showHelp)}>
            <HelpCircle className="mr-2 h-4 w-4" />
            Help
          </Button>
          <Button variant="outline" onClick={validateExpression}>
            <TestTube className="mr-2 h-4 w-4" />
            Validate
          </Button>
          <Button onClick={handleSave}>
            Save Calculation
          </Button>
        </div>
      </div>

      {/* Help Section */}
      {showHelp && (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            <div className="space-y-2 mt-2">
              <p><strong>Building Calculations:</strong></p>
              <ul className="list-disc list-inside space-y-1">
                <li>Click on functions from the palette to insert them</li>
                <li>Click on available fields to add them to your expression</li>
                <li>Use operators (+, -, *, /, etc.) to combine values</li>
                <li>Variables in the expression will be automatically detected</li>
                <li>Test your expression with sample data before saving</li>
              </ul>
            </div>
          </AlertDescription>
        </Alert>
      )}

      {/* Validation Error */}
      {validationError && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{validationError}</AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Panel - Function Palette */}
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Function Palette</CardTitle>
              <CardDescription>
                Click to insert functions into your expression
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Search and Filter */}
              <Input
                placeholder="Search functions..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
              
              <Select value={selectedCategory} onValueChange={setSelectedCategory}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {categories.map(cat => (
                    <SelectItem key={cat} value={cat}>
                      {cat.charAt(0).toUpperCase() + cat.slice(1)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              {/* Function List */}
              <div className="space-y-2 max-h-[400px] overflow-y-auto">
                {filteredFunctions.map(func => (
                  <TooltipProvider key={func.name}>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button
                          variant="outline"
                          size="sm"
                          className="w-full justify-start"
                          onClick={() => insertFunction(func)}
                        >
                          <FunctionSquare className="mr-2 h-4 w-4" />
                          {func.name}
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent side="right" className="max-w-xs">
                        <div className="space-y-2">
                          <p className="font-semibold">{func.name}</p>
                          <p className="text-sm">{func.description}</p>
                          <p className="text-sm font-mono">{func.syntax}</p>
                          <p className="text-sm text-muted-foreground">
                            Example: {func.example}
                          </p>
                        </div>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Available Fields */}
          {availableFields.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Available Fields</CardTitle>
                <CardDescription>
                  Click to insert fields
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 max-h-[200px] overflow-y-auto">
                  {availableFields.map(field => (
                    <Button
                      key={field.name}
                      variant="outline"
                      size="sm"
                      className="w-full justify-start"
                      onClick={() => insertField(field)}
                    >
                      <Database className="mr-2 h-4 w-4" />
                      {field.name}
                      <Badge variant="secondary" className="ml-auto">
                        {field.type}
                      </Badge>
                    </Button>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Operators */}
          <Card>
            <CardHeader>
              <CardTitle>Operators</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-4 gap-2">
                {['+', '-', '*', '/', '(', ')', '==', '!=', '>', '<', '>=', '<=', '&&', '||', '!', '%'].map(op => (
                  <Button
                    key={op}
                    variant="outline"
                    size="sm"
                    onClick={() => insertOperator(op)}
                  >
                    {op}
                  </Button>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Middle Panel - Expression Editor */}
        <div className="lg:col-span-2 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Calculation Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="name">Name</Label>
                <Input
                  id="name"
                  value={calculation.name}
                  onChange={(e) => setCalculation({ ...calculation, name: e.target.value })}
                  placeholder="Enter calculation name"
                />
              </div>

              <div>
                <Label htmlFor="description">Description</Label>
                <Input
                  id="description"
                  value={calculation.description}
                  onChange={(e) => setCalculation({ ...calculation, description: e.target.value })}
                  placeholder="Describe what this calculation does"
                />
              </div>

              <div>
                <Label htmlFor="output_type">Output Type</Label>
                <Select
                  value={calculation.output_type}
                  onValueChange={(value) => setCalculation({ ...calculation, output_type: value })}
                >
                  <SelectTrigger id="output_type">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="number">Number</SelectItem>
                    <SelectItem value="string">String</SelectItem>
                    <SelectItem value="boolean">Boolean</SelectItem>
                    <SelectItem value="date">Date</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Expression</CardTitle>
              <CardDescription>
                Build your calculation expression
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[200px] border rounded-lg overflow-hidden">
                <MonacoEditor
                  height="100%"
                  language="javascript"
                  theme="vs-light"
                  value={calculation.expression}
                  onChange={(value) => setCalculation({ ...calculation, expression: value || '' })}
                  options={{
                    minimap: { enabled: false },
                    scrollBeyondLastLine: false,
                    fontSize: 14,
                    lineNumbers: 'off',
                    wordWrap: 'on'
                  }}
                />
              </div>

              {/* Detected Variables */}
              {calculation.variables.length > 0 && (
                <div className="mt-4">
                  <Label>Detected Variables</Label>
                  <div className="flex gap-2 flex-wrap mt-2">
                    {calculation.variables.map(variable => (
                      <Badge key={variable} variant="secondary">
                        {variable}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Test Panel */}
          <Card>
            <CardHeader>
              <CardTitle>Test Expression</CardTitle>
              <CardDescription>
                Provide test values for variables
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {calculation.variables.map(variable => (
                <div key={variable} className="grid grid-cols-3 gap-4 items-center">
                  <Label>{variable}</Label>
                  <Input
                    type="text"
                    placeholder="Enter test value"
                    onChange={(e) => setTestData({ ...testData, [variable]: e.target.value })}
                  />
                  <Select
                    onValueChange={(value) => {
                      const typedValue = value === 'number' ? parseFloat(testData[variable] || 0) :
                                       value === 'boolean' ? testData[variable] === 'true' :
                                       testData[variable];
                      setTestData({ ...testData, [variable]: typedValue });
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="string">String</SelectItem>
                      <SelectItem value="number">Number</SelectItem>
                      <SelectItem value="boolean">Boolean</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              ))}

              <div className="flex gap-2">
                <Button onClick={testExpression} className="flex-1">
                  <Play className="mr-2 h-4 w-4" />
                  Run Test
                </Button>
              </div>

              {testResult !== null && (
                <Alert>
                  <AlertDescription>
                    <strong>Result:</strong> {JSON.stringify(testResult)}
                  </AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}