// ABOUTME: Component for previewing mapped data before saving configuration
// ABOUTME: Shows sample data with transformations applied

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  AlertCircle,
  CheckCircle,
  RefreshCw,
  Database,
  Eye,
  Download,
  Filter,
} from 'lucide-react';
import { mappingApi } from '@/lib/api/mapping';
import { widgetsApi } from '@/lib/api/widgets';
import { cn } from '@/lib/utils';
import { WidgetType } from '@/types/widget';

interface MappingPreviewProps {
  studyId: string;
  widgetId: string;
  mappingConfig?: any;
  onValidation?: (result: any) => void;
}

export function MappingPreview({
  studyId,
  widgetId,
  mappingConfig,
  onValidation,
}: MappingPreviewProps) {
  const [previewLimit, setPreviewLimit] = useState(10);
  const [showRawData, setShowRawData] = useState(false);

  // Fetch widget details
  const { data: widget } = useQuery({
    queryKey: ['widget', widgetId],
    queryFn: () => widgetsApi.getWidget(widgetId),
  });

  // Fetch preview data
  const {
    data: previewData,
    isLoading: isLoadingPreview,
    refetch: refetchPreview,
  } = useQuery({
    queryKey: ['mapping-preview', studyId, widgetId, previewLimit],
    queryFn: () => mappingApi.previewMappingData(studyId, widgetId, previewLimit),
    enabled: !!mappingConfig,
  });

  // Validate mapping
  const {
    data: validationResult,
    isLoading: isValidating,
    refetch: refetchValidation,
  } = useQuery({
    queryKey: ['mapping-validation', studyId, widgetId, mappingConfig],
    queryFn: async () => {
      if (!mappingConfig) return null;
      const result = await mappingApi.validateMapping({
        study_id: studyId,
        widget_id: widgetId,
        ...mappingConfig,
      });
      onValidation?.(result);
      return result;
    },
    enabled: !!mappingConfig,
  });

  const getFieldValue = (row: any, fieldName: string) => {
    const value = row[fieldName];
    if (value === null || value === undefined) {
      return <span className="text-gray-400">null</span>;
    }
    if (typeof value === 'boolean') {
      return value ? (
        <Badge variant="outline" className="bg-green-50">
          true
        </Badge>
      ) : (
        <Badge variant="outline" className="bg-red-50">
          false
        </Badge>
      );
    }
    if (typeof value === 'number') {
      return <span className="font-mono">{value.toLocaleString()}</span>;
    }
    if (value instanceof Date || /^\d{4}-\d{2}-\d{2}/.test(value)) {
      return <span className="font-mono">{new Date(value).toLocaleDateString()}</span>;
    }
    return String(value);
  };

  const handleExportSample = () => {
    if (!previewData?.data) return;

    const csv = [
      Object.keys(previewData.data[0]).join(','),
      ...previewData.data.map((row) =>
        Object.values(row)
          .map((v) => `"${String(v).replace(/"/g, '""')}"`)
          .join(',')
      ),
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${widget?.name}_preview_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (!mappingConfig) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center h-64">
          <div className="text-center text-gray-500">
            <Database className="h-12 w-12 mx-auto mb-4" />
            <p>Configure field mappings to preview data</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Validation Summary */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Data Validation</CardTitle>
              <CardDescription>
                Validation results for your mapping configuration
              </CardDescription>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => refetchValidation()}
              disabled={isValidating}
            >
              <RefreshCw className={cn("h-4 w-4 mr-1", isValidating && "animate-spin")} />
              Revalidate
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {isValidating ? (
            <div className="space-y-3">
              <Skeleton className="h-16 w-full" />
              <Skeleton className="h-16 w-full" />
            </div>
          ) : validationResult ? (
            <div className="space-y-4">
              {/* Overall Status */}
              <div className="flex items-center gap-4">
                {validationResult.is_valid ? (
                  <>
                    <CheckCircle className="h-5 w-5 text-green-600" />
                    <span className="font-medium text-green-600">
                      All validations passed
                    </span>
                  </>
                ) : (
                  <>
                    <AlertCircle className="h-5 w-5 text-red-600" />
                    <span className="font-medium text-red-600">
                      Validation failed
                    </span>
                  </>
                )}
              </div>

              {/* Errors */}
              {validationResult.errors.length > 0 && (
                <div className="space-y-2">
                  <h4 className="font-medium text-red-600">Errors</h4>
                  {validationResult.errors.map((error, idx) => (
                    <Alert key={idx} variant="destructive">
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription>{error}</AlertDescription>
                    </Alert>
                  ))}
                </div>
              )}

              {/* Warnings */}
              {validationResult.warnings.length > 0 && (
                <div className="space-y-2">
                  <h4 className="font-medium text-yellow-600">Warnings</h4>
                  {validationResult.warnings.map((warning, idx) => (
                    <Alert key={idx}>
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription>{warning}</AlertDescription>
                    </Alert>
                  ))}
                </div>
              )}

              {/* Coverage */}
              {Object.keys(validationResult.coverage).length > 0 && (
                <div>
                  <h4 className="font-medium mb-2">Field Coverage</h4>
                  <div className="grid grid-cols-2 gap-2">
                    {Object.entries(validationResult.coverage).map(([field, coverage]) => (
                      <div key={field} className="flex items-center justify-between p-2 border rounded">
                        <span className="text-sm">{field}</span>
                        <Badge variant={coverage > 0.8 ? 'default' : coverage > 0.5 ? 'secondary' : 'destructive'}>
                          {(coverage * 100).toFixed(0)}%
                        </Badge>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : null}
        </CardContent>
      </Card>

      {/* Data Preview */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Data Preview</CardTitle>
              <CardDescription>
                Sample data with your mapping configuration applied
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Select
                value={previewLimit.toString()}
                onValueChange={(value) => setPreviewLimit(parseInt(value))}
              >
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="10">10 rows</SelectItem>
                  <SelectItem value="25">25 rows</SelectItem>
                  <SelectItem value="50">50 rows</SelectItem>
                  <SelectItem value="100">100 rows</SelectItem>
                </SelectContent>
              </Select>
              <Button
                variant="outline"
                size="sm"
                onClick={() => refetchPreview()}
                disabled={isLoadingPreview}
              >
                <RefreshCw className={cn("h-4 w-4 mr-1", isLoadingPreview && "animate-spin")} />
                Refresh
              </Button>
              {previewData?.data && previewData.data.length > 0 && (
                <Button variant="outline" size="sm" onClick={handleExportSample}>
                  <Download className="h-4 w-4 mr-1" />
                  Export
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="mapped" className="space-y-4">
            <TabsList>
              <TabsTrigger value="mapped">Mapped Data</TabsTrigger>
              <TabsTrigger value="widget">Widget Preview</TabsTrigger>
            </TabsList>

            <TabsContent value="mapped">
              {isLoadingPreview ? (
                <div className="space-y-3">
                  <Skeleton className="h-10 w-full" />
                  <Skeleton className="h-32 w-full" />
                </div>
              ) : previewData?.data && previewData.data.length > 0 ? (
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        {Object.keys(previewData.data[0]).map((field) => (
                          <TableHead key={field} className="font-mono text-xs">
                            {field}
                          </TableHead>
                        ))}
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {previewData.data.map((row, idx) => (
                        <TableRow key={idx}>
                          {Object.keys(row).map((field) => (
                            <TableCell key={field} className="text-sm">
                              {getFieldValue(row, field)}
                            </TableCell>
                          ))}
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  No preview data available
                </div>
              )}
            </TabsContent>

            <TabsContent value="widget">
              <div className="bg-gray-50 p-6 rounded-lg">
                <p className="text-sm text-gray-600 mb-4">
                  This is how your data will appear in the {widget?.name} widget:
                </p>
                {widget?.type === WidgetType.METRIC && previewData?.data?.[0] && (
                  <div className="bg-white rounded-lg shadow-sm p-6 max-w-sm">
                    <div className="space-y-2">
                      <p className="text-sm text-gray-500">
                        {previewData.data[0].label || widget.name}
                      </p>
                      <p className="text-3xl font-bold">
                        {previewData.data[0].value || '0'}
                      </p>
                      {previewData.data[0].change !== undefined && (
                        <div className="flex items-center gap-2">
                          <Badge
                            variant={previewData.data[0].change >= 0 ? 'default' : 'destructive'}
                          >
                            {previewData.data[0].change >= 0 ? '+' : ''}
                            {previewData.data[0].change}%
                          </Badge>
                          <span className="text-sm text-gray-500">vs previous period</span>
                        </div>
                      )}
                    </div>
                  </div>
                )}
                {/* Add more widget type previews here */}
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}