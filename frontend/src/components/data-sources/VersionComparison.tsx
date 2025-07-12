// ABOUTME: Component for comparing two data upload versions side by side
// ABOUTME: Shows file changes, row counts, column differences, and impact analysis

import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  ChevronRight,
  ChevronDown,
  FileText,
  Plus,
  Minus,
  AlertTriangle,
  Download,
  CheckCircle,
  XCircle,
  RefreshCw,
  ArrowRight,
} from 'lucide-react';
import { format } from 'date-fns';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
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
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { dataUploadsApi, VersionComparisonResult } from '@/lib/api/data-uploads';
import { cn } from '@/lib/utils';

interface VersionComparisonProps {
  studyId: string;
  version1Id: string;
  version2Id: string;
  onVersionSwitch?: (versionId: string) => void;
  onClose?: () => void;
}

type FilterType = 'all' | 'new' | 'removed' | 'modified' | 'unchanged';

export function VersionComparison({
  studyId,
  version1Id,
  version2Id,
  onVersionSwitch,
  onClose,
}: VersionComparisonProps) {
  const [expandedDatasets, setExpandedDatasets] = useState<Set<string>>(new Set());
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<FilterType>('all');

  // Fetch comparison data
  const { data: comparison, isLoading, error } = useQuery({
    queryKey: ['versionComparison', studyId, version1Id, version2Id],
    queryFn: () => dataUploadsApi.compareVersions(studyId, version1Id, version2Id),
  });

  const toggleDatasetExpansion = (datasetName: string) => {
    const newExpanded = new Set(expandedDatasets);
    if (newExpanded.has(datasetName)) {
      newExpanded.delete(datasetName);
    } else {
      newExpanded.add(datasetName);
    }
    setExpandedDatasets(newExpanded);
  };

  const formatNumber = (num: number) => {
    return num.toLocaleString();
  };

  const formatChange = (change: number) => {
    if (change === 0) return '0';
    const formatted = formatNumber(Math.abs(change));
    return change > 0 ? `+${formatted}` : `-${formatted}`;
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'new':
        return <Plus className="h-4 w-4 text-green-600" />;
      case 'removed':
        return <XCircle className="h-4 w-4 text-red-600" />;
      case 'modified':
        return <RefreshCw className="h-4 w-4 text-yellow-600" />;
      case 'unchanged':
        return <CheckCircle className="h-4 w-4 text-gray-400" />;
      default:
        return null;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'new':
        return <Badge className="bg-green-100 text-green-800">New</Badge>;
      case 'removed':
        return <Badge variant="destructive">Removed</Badge>;
      case 'modified':
        return <Badge className="bg-yellow-100 text-yellow-800">Modified</Badge>;
      case 'unchanged':
        return <Badge variant="secondary">Unchanged</Badge>;
      default:
        return null;
    }
  };

  // Filter datasets based on search and filter type
  const filteredDatasets = comparison?.dataset_comparison.filter((dataset) => {
    // Search filter
    if (searchTerm && !dataset.dataset_name.toLowerCase().includes(searchTerm.toLowerCase())) {
      return false;
    }
    // Status filter
    if (filterType !== 'all' && dataset.status !== filterType) {
      return false;
    }
    return true;
  });

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (error || !comparison) {
    return (
      <Alert variant="destructive">
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>
          Failed to load version comparison. Please try again.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      {/* High-Level Summary */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg">
              Version {comparison.version1.version_number}
            </CardTitle>
            <CardDescription>
              {format(new Date(comparison.version1.upload_timestamp), 'MMM d, yyyy h:mm a')}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Files:</span>
                <span className="font-medium">{comparison.version1.file_count}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Total Rows:</span>
                <span className="font-medium">{formatNumber(comparison.version1.total_rows)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Total Size:</span>
                <span className="font-medium">{comparison.version1.total_size_mb.toFixed(1)} MB</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg">
                Version {comparison.version2.version_number}
              </CardTitle>
              <Badge variant="outline" className="text-xs">Latest</Badge>
            </div>
            <CardDescription>
              {format(new Date(comparison.version2.upload_timestamp), 'MMM d, yyyy h:mm a')}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Files:</span>
                <span className="font-medium">
                  {comparison.version2.file_count}
                  {comparison.differences.file_count_change !== 0 && (
                    <span className={cn(
                      "ml-2",
                      comparison.differences.file_count_change > 0 ? "text-green-600" : "text-red-600"
                    )}>
                      ({formatChange(comparison.differences.file_count_change)})
                    </span>
                  )}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Total Rows:</span>
                <span className="font-medium">
                  {formatNumber(comparison.version2.total_rows)}
                  {comparison.differences.row_count_change !== 0 && (
                    <span className={cn(
                      "ml-2",
                      comparison.differences.row_count_change > 0 ? "text-green-600" : "text-red-600"
                    )}>
                      ({formatChange(comparison.differences.row_count_change)})
                    </span>
                  )}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Total Size:</span>
                <span className="font-medium">
                  {comparison.version2.total_size_mb.toFixed(1)} MB
                  {comparison.differences.size_change_mb !== 0 && (
                    <span className={cn(
                      "ml-2",
                      comparison.differences.size_change_mb > 0 ? "text-green-600" : "text-red-600"
                    )}>
                      ({formatChange(comparison.differences.size_change_mb)} MB)
                    </span>
                  )}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Dataset Comparison */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Dataset Comparison</CardTitle>
              <CardDescription>
                Changes between versions at the dataset level
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Input
                placeholder="Search datasets..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-64"
              />
              <Select value={filterType} onValueChange={(value) => setFilterType(value as FilterType)}>
                <SelectTrigger className="w-40">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Changes</SelectItem>
                  <SelectItem value="new">New Only</SelectItem>
                  <SelectItem value="removed">Removed Only</SelectItem>
                  <SelectItem value="modified">Modified Only</SelectItem>
                  <SelectItem value="unchanged">Unchanged Only</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[30px]"></TableHead>
                <TableHead>Dataset Name</TableHead>
                <TableHead className="text-center">V1 Rows</TableHead>
                <TableHead className="text-center">V2 Rows</TableHead>
                <TableHead className="text-center">Change</TableHead>
                <TableHead className="text-center">Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredDatasets?.map((dataset) => (
                <React.Fragment key={dataset.dataset_name}>
                  <TableRow
                    className={cn(
                      "cursor-pointer hover:bg-muted/50",
                      dataset.column_changes.length > 0 && "font-medium"
                    )}
                    onClick={() => dataset.column_changes.length > 0 && toggleDatasetExpansion(dataset.dataset_name)}
                  >
                    <TableCell>
                      {dataset.column_changes.length > 0 && (
                        <Button variant="ghost" size="icon" className="h-6 w-6">
                          {expandedDatasets.has(dataset.dataset_name) ? (
                            <ChevronDown className="h-4 w-4" />
                          ) : (
                            <ChevronRight className="h-4 w-4" />
                          )}
                        </Button>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <FileText className="h-4 w-4 text-muted-foreground" />
                        {dataset.dataset_name}
                      </div>
                    </TableCell>
                    <TableCell className="text-center">
                      {dataset.v1_rows !== null ? formatNumber(dataset.v1_rows) : '-'}
                    </TableCell>
                    <TableCell className="text-center">
                      {dataset.v2_rows !== null ? formatNumber(dataset.v2_rows) : '-'}
                    </TableCell>
                    <TableCell className="text-center">
                      {dataset.row_change !== 0 && (
                        <span className={cn(
                          dataset.row_change > 0 ? "text-green-600" : "text-red-600"
                        )}>
                          {formatChange(dataset.row_change)}
                        </span>
                      )}
                      {dataset.row_change === 0 && dataset.status === 'unchanged' && (
                        <span className="text-muted-foreground">-</span>
                      )}
                    </TableCell>
                    <TableCell className="text-center">
                      {getStatusBadge(dataset.status)}
                    </TableCell>
                  </TableRow>
                  {expandedDatasets.has(dataset.dataset_name) && dataset.column_changes.length > 0 && (
                    <TableRow>
                      <TableCell colSpan={6} className="p-0 bg-muted/20">
                        <div className="p-4">
                          <h4 className="text-sm font-medium mb-3">Column Changes</h4>
                          <Table>
                            <TableHeader>
                              <TableRow>
                                <TableHead>Column Name</TableHead>
                                <TableHead>V1 Type</TableHead>
                                <TableHead>V2 Type</TableHead>
                                <TableHead>Change</TableHead>
                              </TableRow>
                            </TableHeader>
                            <TableBody>
                              {dataset.column_changes.map((col) => (
                                <TableRow key={col.column_name}>
                                  <TableCell className="font-mono text-sm">
                                    {col.column_name}
                                  </TableCell>
                                  <TableCell>{col.v1_type || '-'}</TableCell>
                                  <TableCell>{col.v2_type || '-'}</TableCell>
                                  <TableCell>
                                    {col.change_type === 'added' && (
                                      <Badge className="bg-green-100 text-green-800 text-xs">
                                        New Column
                                      </Badge>
                                    )}
                                    {col.change_type === 'removed' && (
                                      <Badge variant="destructive" className="text-xs">
                                        Removed
                                      </Badge>
                                    )}
                                    {col.change_type === 'type_changed' && (
                                      <Badge className="bg-yellow-100 text-yellow-800 text-xs">
                                        Type Changed
                                      </Badge>
                                    )}
                                  </TableCell>
                                </TableRow>
                              ))}
                            </TableBody>
                          </Table>
                        </div>
                      </TableCell>
                    </TableRow>
                  )}
                </React.Fragment>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Impact Analysis */}
      <Alert>
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>
          <div className="space-y-2">
            <p className="font-medium">Switching to Version {comparison.version2.version_number} will affect:</p>
            <ul className="list-disc list-inside space-y-1 text-sm">
              {comparison.differences.file_count_change > 0 && (
                <li>{comparison.differences.file_count_change} new dataset{comparison.differences.file_count_change > 1 ? 's' : ''} added</li>
              )}
              {comparison.differences.file_count_change < 0 && (
                <li>{Math.abs(comparison.differences.file_count_change)} dataset{Math.abs(comparison.differences.file_count_change) > 1 ? 's' : ''} removed</li>
              )}
              {comparison.dataset_comparison.filter(d => d.status === 'modified').length > 0 && (
                <li>{comparison.dataset_comparison.filter(d => d.status === 'modified').length} dataset{comparison.dataset_comparison.filter(d => d.status === 'modified').length > 1 ? 's' : ''} modified</li>
              )}
              {comparison.dataset_comparison.some(d => d.column_changes.length > 0) && (
                <li>Column structure changes detected - review widget configurations</li>
              )}
            </ul>
            <p className="text-sm text-muted-foreground mt-2">
              Recommendation: Review all dashboard widgets after switching versions
            </p>
          </div>
        </AlertDescription>
      </Alert>

      {/* Actions */}
      <div className="flex items-center justify-between">
        <div className="flex gap-2">
          <Button variant="outline">
            <Download className="mr-2 h-4 w-4" />
            Export Comparison
          </Button>
        </div>
        <div className="flex gap-2">
          {onClose && (
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
          )}
          {onVersionSwitch && (
            <Button 
              onClick={() => onVersionSwitch(version2Id)}
              className="gap-2"
            >
              Switch to Version {comparison.version2.version_number}
              <ArrowRight className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}