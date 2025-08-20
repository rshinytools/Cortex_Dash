// ABOUTME: Filter management page for study widgets
// ABOUTME: Allows viewing, editing, and testing all widget filters

'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/hooks/use-toast';
import {
  Filter,
  Edit,
  Trash2,
  Play,
  CheckCircle,
  XCircle,
  AlertCircle,
  Loader2,
  Search,
  Plus,
  Eye,
  TrendingUp,
  Clock,
  Database,
  ArrowLeft
} from 'lucide-react';
import { FilterBuilder } from '@/components/filters/FilterBuilder';
import { format } from 'date-fns';
import Link from 'next/link';

interface WidgetFilter {
  widget_id: string;
  expression: string | null;
  enabled: boolean;
  last_validated: string | null;
  validation_status: string | null;
}

interface FilterMetric {
  widget_id: string;
  filter_expression: string;
  execution_time_ms: number;
  rows_before: number;
  rows_after: number;
  reduction_percentage: number;
  executed_at: string;
}

export default function StudyFiltersPage() {
  const params = useParams();
  const router = useRouter();
  const { toast } = useToast();
  const studyId = params.studyId as string;

  const [filters, setFilters] = useState<WidgetFilter[]>([]);
  const [metrics, setMetrics] = useState<FilterMetric[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedFilter, setSelectedFilter] = useState<WidgetFilter | null>(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [activeTab, setActiveTab] = useState('filters');

  useEffect(() => {
    loadFilters();
    loadMetrics();
  }, [studyId]);

  const loadFilters = async () => {
    try {
      const response = await fetch(`/api/v1/studies/${studyId}/filters`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setFilters(data);
      } else {
        toast({
          title: 'Error',
          description: 'Failed to load filters',
          variant: 'destructive',
        });
      }
    } catch (error) {
      console.error('Error loading filters:', error);
      toast({
        title: 'Error',
        description: 'Failed to load filters',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const loadMetrics = async () => {
    try {
      const response = await fetch(`/api/v1/studies/${studyId}/filters/metrics`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setMetrics(data.metrics || []);
      }
    } catch (error) {
      console.error('Error loading metrics:', error);
    }
  };

  const deleteFilter = async (widgetId: string) => {
    try {
      const response = await fetch(
        `/api/v1/studies/${studyId}/widgets/${widgetId}/filter`,
        {
          method: 'DELETE',
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`,
          },
        }
      );

      if (response.ok) {
        toast({
          title: 'Success',
          description: 'Filter deleted successfully',
        });
        loadFilters();
        setDeleteDialogOpen(false);
      } else {
        toast({
          title: 'Error',
          description: 'Failed to delete filter',
          variant: 'destructive',
        });
      }
    } catch (error) {
      console.error('Error deleting filter:', error);
      toast({
        title: 'Error',
        description: 'Failed to delete filter',
        variant: 'destructive',
      });
    }
  };

  const toggleFilter = async (widgetId: string, enabled: boolean) => {
    const filter = filters.find(f => f.widget_id === widgetId);
    if (!filter) return;

    try {
      const response = await fetch(
        `/api/v1/studies/${studyId}/widgets/${widgetId}/filter`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${localStorage.getItem('token')}`,
          },
          body: JSON.stringify({
            widget_id: widgetId,
            expression: filter.expression,
            enabled,
          }),
        }
      );

      if (response.ok) {
        toast({
          title: 'Success',
          description: `Filter ${enabled ? 'enabled' : 'disabled'} successfully`,
        });
        loadFilters();
      } else {
        toast({
          title: 'Error',
          description: 'Failed to update filter',
          variant: 'destructive',
        });
      }
    } catch (error) {
      console.error('Error updating filter:', error);
      toast({
        title: 'Error',
        description: 'Failed to update filter',
        variant: 'destructive',
      });
    }
  };

  const filteredFilters = filters.filter(
    f => !searchTerm || 
         f.widget_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
         f.expression?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const calculateAverageReduction = () => {
    if (metrics.length === 0) return 0;
    const sum = metrics.reduce((acc, m) => acc + m.reduction_percentage, 0);
    return Math.round(sum / metrics.length);
  };

  const calculateAverageExecutionTime = () => {
    if (metrics.length === 0) return 0;
    const sum = metrics.reduce((acc, m) => acc + m.execution_time_ms, 0);
    return Math.round(sum / metrics.length);
  };

  return (
    <div className="container mx-auto py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <Link href={`/studies/${studyId}/dashboard`}>
            <Button variant="ghost" size="sm">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Dashboard
            </Button>
          </Link>
          <div>
            <h1 className="text-3xl font-bold">Widget Filters</h1>
            <p className="text-muted-foreground">
              Manage filters for dashboard widgets
            </p>
          </div>
        </div>
        
        <Button 
          onClick={() => {
            setSelectedFilter(null);
            setEditDialogOpen(true);
          }}
        >
          <Plus className="h-4 w-4 mr-2" />
          Add Filter
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Filters</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{filters.length}</div>
            <p className="text-xs text-muted-foreground">
              {filters.filter(f => f.enabled).length} active
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Valid Filters</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {filters.filter(f => f.validation_status === 'valid').length}
            </div>
            <p className="text-xs text-muted-foreground">
              {filters.filter(f => f.validation_status === 'invalid').length} invalid
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Avg. Reduction</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{calculateAverageReduction()}%</div>
            <p className="text-xs text-muted-foreground">
              Data filtered out
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Avg. Execution</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{calculateAverageExecutionTime()}ms</div>
            <p className="text-xs text-muted-foreground">
              Per filter
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Filter Management</CardTitle>
            <div className="flex items-center gap-2">
              <div className="relative">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search filters..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-8 w-[250px]"
                />
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="filters">Filters</TabsTrigger>
              <TabsTrigger value="metrics">Performance Metrics</TabsTrigger>
            </TabsList>

            <TabsContent value="filters" className="space-y-4">
              {isLoading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-8 w-8 animate-spin" />
                </div>
              ) : filteredFilters.length === 0 ? (
                <Alert>
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    No filters found. Add filters to control widget data.
                  </AlertDescription>
                </Alert>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Widget ID</TableHead>
                      <TableHead>Filter Expression</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Validation</TableHead>
                      <TableHead>Last Validated</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredFilters.map((filter) => (
                      <TableRow key={filter.widget_id}>
                        <TableCell className="font-medium">
                          {filter.widget_id}
                        </TableCell>
                        <TableCell>
                          <code className="text-sm bg-muted px-2 py-1 rounded">
                            {filter.expression || '-'}
                          </code>
                        </TableCell>
                        <TableCell>
                          <Badge variant={filter.enabled ? 'default' : 'secondary'}>
                            {filter.enabled ? 'Active' : 'Disabled'}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {filter.validation_status === 'valid' ? (
                            <Badge variant="outline" className="text-green-600">
                              <CheckCircle className="h-3 w-3 mr-1" />
                              Valid
                            </Badge>
                          ) : filter.validation_status === 'invalid' ? (
                            <Badge variant="outline" className="text-red-600">
                              <XCircle className="h-3 w-3 mr-1" />
                              Invalid
                            </Badge>
                          ) : (
                            <Badge variant="outline">
                              Unknown
                            </Badge>
                          )}
                        </TableCell>
                        <TableCell>
                          {filter.last_validated ? (
                            format(new Date(filter.last_validated), 'MMM dd, yyyy HH:mm')
                          ) : (
                            '-'
                          )}
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex items-center justify-end gap-2">
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => toggleFilter(filter.widget_id, !filter.enabled)}
                            >
                              {filter.enabled ? (
                                <Eye className="h-4 w-4" />
                              ) : (
                                <Eye className="h-4 w-4 opacity-50" />
                              )}
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => {
                                setSelectedFilter(filter);
                                setEditDialogOpen(true);
                              }}
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => {
                                setSelectedFilter(filter);
                                setDeleteDialogOpen(true);
                              }}
                            >
                              <Trash2 className="h-4 w-4 text-red-500" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </TabsContent>

            <TabsContent value="metrics" className="space-y-4">
              {metrics.length === 0 ? (
                <Alert>
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    No performance metrics available yet. Metrics are collected when filters are executed.
                  </AlertDescription>
                </Alert>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Widget ID</TableHead>
                      <TableHead>Filter Expression</TableHead>
                      <TableHead>Rows Before</TableHead>
                      <TableHead>Rows After</TableHead>
                      <TableHead>Reduction</TableHead>
                      <TableHead>Execution Time</TableHead>
                      <TableHead>Executed At</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {metrics.map((metric, idx) => (
                      <TableRow key={idx}>
                        <TableCell className="font-medium">
                          {metric.widget_id}
                        </TableCell>
                        <TableCell>
                          <code className="text-sm bg-muted px-2 py-1 rounded">
                            {metric.filter_expression}
                          </code>
                        </TableCell>
                        <TableCell>{metric.rows_before.toLocaleString()}</TableCell>
                        <TableCell>{metric.rows_after.toLocaleString()}</TableCell>
                        <TableCell>
                          <Badge variant="outline">
                            {metric.reduction_percentage}%
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge variant="secondary">
                            {metric.execution_time_ms}ms
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {format(new Date(metric.executed_at), 'MMM dd, HH:mm:ss')}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {/* Edit Dialog */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {selectedFilter ? 'Edit Filter' : 'Add New Filter'}
            </DialogTitle>
            <DialogDescription>
              Configure filter for widget data
            </DialogDescription>
          </DialogHeader>
          
          {/* Filter builder would go here - simplified for now */}
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Filter editing interface would be displayed here
            </AlertDescription>
          </Alert>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Filter</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this filter? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <div className="flex justify-end gap-2 mt-4">
            <Button variant="outline" onClick={() => setDeleteDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={() => {
                if (selectedFilter) {
                  deleteFilter(selectedFilter.widget_id);
                }
              }}
            >
              Delete Filter
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}