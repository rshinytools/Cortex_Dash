// ABOUTME: Code editor component for Python transformation scripts
// ABOUTME: Includes syntax validation and allowed imports configuration

import React, { useState } from 'react';
import { Check, AlertCircle, Info } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import { Checkbox } from '@/components/ui/checkbox';
import { useMutation } from '@tanstack/react-query';
import { pipelinesApi, TransformationType } from '@/lib/api/pipelines';
import PythonEditor from '@/components/code-editor/PythonEditor';

interface ScriptEditorProps {
  script: string;
  onChange: (script: string) => void;
  allowedImports: string[];
  onImportsChange: (imports: string[]) => void;
}

const AVAILABLE_IMPORTS = [
  { name: 'pandas', description: 'Data manipulation and analysis' },
  { name: 'numpy', description: 'Numerical computing' },
  { name: 'datetime', description: 'Date and time operations' },
  { name: 're', description: 'Regular expressions' },
  { name: 'json', description: 'JSON data handling' },
  { name: 'math', description: 'Mathematical functions' },
];

const EXAMPLE_SCRIPTS = {
  'Standardize Columns': `# Standardize column names
df.columns = [col.lower().replace(' ', '_') for col in df.columns]

# Convert data types
if 'age' in df.columns:
    df['age'] = pd.to_numeric(df['age'], errors='coerce')

# Output the transformed dataframe
output = df`,

  'Filter by Date': `# Filter data by date range
from datetime import datetime

# Convert date column to datetime
df['visit_date'] = pandas.to_datetime(df['visit_date'])

# Filter last 30 days
cutoff_date = datetime.now() - pandas.Timedelta(days=30)
output = df[df['visit_date'] >= cutoff_date]`,

  'Derive BMI': `# Calculate BMI from height and weight
df['bmi'] = df['weight'] / (df['height'] / 100) ** 2

# Categorize BMI
df['bmi_category'] = pandas.cut(
    df['bmi'],
    bins=[0, 18.5, 25, 30, 100],
    labels=['Underweight', 'Normal', 'Overweight', 'Obese']
)

output = df`,

  'Aggregate by Group': `# Aggregate data by treatment arm
aggregated = df.groupby('treatment_arm').agg({
    'age': ['mean', 'std'],
    'subject_id': 'count',
    'adverse_event': 'sum'
}).reset_index()

# Rename columns
aggregated.columns = ['_'.join(col).strip() for col in aggregated.columns.values]
output = aggregated`,
};

export function ScriptEditor({
  script,
  onChange,
  allowedImports,
  onImportsChange,
}: ScriptEditorProps) {
  const [validationResult, setValidationResult] = useState<{
    is_valid: boolean;
    errors: string[];
  } | null>(null);

  // Validate script mutation
  const validateMutation = useMutation({
    mutationFn: () =>
      pipelinesApi.validateScript(script, TransformationType.PYTHON_SCRIPT, allowedImports),
    onSuccess: (data) => {
      setValidationResult(data);
    },
  });

  const handleImportToggle = (importName: string) => {
    if (allowedImports.includes(importName)) {
      onImportsChange(allowedImports.filter((i) => i !== importName));
    } else {
      onImportsChange([...allowedImports, importName]);
    }
  };

  const insertExample = (exampleScript: string) => {
    onChange(script + '\n\n' + exampleScript);
  };

  return (
    <div className="space-y-4">
      <div>
        <Label htmlFor="script">Transformation Script</Label>
        <div className="mt-2 space-y-2">
          <Alert>
            <Info className="h-4 w-4" />
            <AlertDescription>
              <div className="space-y-2">
                <p>Write Python code to transform your data. The input dataframe is available as `df`.</p>
                <p>Set the transformed dataframe to `output` variable.</p>
                <p className="font-mono text-sm bg-gray-100 p-2 rounded">
                  {'# Example:\n'}
                  {'df["new_column"] = df["old_column"] * 2\n'}
                  {'output = df'}
                </p>
              </div>
            </AlertDescription>
          </Alert>

          <PythonEditor
            value={script}
            onChange={onChange}
            height="400px"
            placeholder="# Write your transformation script here..."
          />
        </div>
      </div>

      <Accordion type="single" collapsible className="w-full">
        <AccordionItem value="imports">
          <AccordionTrigger>Allowed Imports</AccordionTrigger>
          <AccordionContent>
            <div className="space-y-3">
              {AVAILABLE_IMPORTS.map((imp) => (
                <div key={imp.name} className="flex items-center space-x-2">
                  <Checkbox
                    id={imp.name}
                    checked={allowedImports.includes(imp.name)}
                    onCheckedChange={() => handleImportToggle(imp.name)}
                  />
                  <Label
                    htmlFor={imp.name}
                    className="text-sm font-normal cursor-pointer flex-1"
                  >
                    <span className="font-mono">{imp.name}</span>
                    <span className="text-gray-500 ml-2">- {imp.description}</span>
                  </Label>
                </div>
              ))}
            </div>
          </AccordionContent>
        </AccordionItem>

        <AccordionItem value="examples">
          <AccordionTrigger>Example Scripts</AccordionTrigger>
          <AccordionContent>
            <div className="space-y-3">
              {Object.entries(EXAMPLE_SCRIPTS).map(([name, exampleScript]) => (
                <div key={name} className="border rounded-lg p-3">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="text-sm font-medium">{name}</h4>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => insertExample(exampleScript)}
                    >
                      Insert
                    </Button>
                  </div>
                  <pre className="text-xs bg-gray-50 p-2 rounded overflow-x-auto">
                    <code>{exampleScript}</code>
                  </pre>
                </div>
              ))}
            </div>
          </AccordionContent>
        </AccordionItem>
      </Accordion>

      <div className="flex items-center justify-between">
        <Button
          variant="outline"
          onClick={() => validateMutation.mutate()}
          disabled={validateMutation.isPending}
        >
          {validateMutation.isPending ? 'Validating...' : 'Validate Script'}
        </Button>

        {validationResult && (
          <div className="flex items-center gap-2">
            {validationResult.is_valid ? (
              <Badge variant="outline" className="text-green-600">
                <Check className="mr-1 h-3 w-3" />
                Valid
              </Badge>
            ) : (
              <Badge variant="outline" className="text-red-600">
                <AlertCircle className="mr-1 h-3 w-3" />
                Invalid
              </Badge>
            )}
          </div>
        )}
      </div>

      {validationResult && !validationResult.is_valid && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            <div className="space-y-1">
              <p className="font-medium">Validation Errors:</p>
              <ul className="list-disc list-inside text-sm">
                {validationResult.errors.map((error, idx) => (
                  <li key={idx}>{error}</li>
                ))}
              </ul>
            </div>
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
}