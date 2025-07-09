// ABOUTME: Study-specific data sources management page
// ABOUTME: Shows and manages data sources for a particular study

'use client';

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, Plus, Database, RefreshCw, Settings, Trash2, Upload } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/hooks/use-toast';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';
import { dataSourcesApi, DataSourceType } from '@/lib/api/data-sources';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { MoreHorizontal } from 'lucide-react';

const dataSourceIcons = {
  [DataSourceType.MEDIDATA_API]: Database,
  [DataSourceType.ZIP_UPLOAD]: Database,
  [DataSourceType.SFTP]: Database,
  [DataSourceType.FOLDER_SYNC]: Database,
  [DataSourceType.EDC_API]: Database,
  [DataSourceType.AWS_S3]: Database,
  [DataSourceType.AZURE_BLOB]: Database,
};

export default function StudyDataSourcesPage() {
  const params = useParams();
  const router = useRouter();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const studyId = params.studyId as string;

  const { data: study } = useQuery({
    queryKey: ['study', studyId],
    queryFn: async () => {
      const response = await apiClient.get(`/studies/${studyId}`);
      return response.data;
    },
  });

  const { data: dataSources, isLoading } = useQuery({
    queryKey: ['study-data-sources', studyId],
    queryFn: async () => {
      const response = await apiClient.get(`/studies/${studyId}/data-sources`);
      return response.data;
    },
  });

  const syncDataSource = useMutation({
    mutationFn: (dataSourceId: string) => dataSourcesApi.syncDataSource(dataSourceId),
    onSuccess: () => {
      toast({
        title: 'Sync started',
        description: 'Data source synchronization has been initiated.',
      });
      queryClient.invalidateQueries({ queryKey: ['study-data-sources', studyId] });
    },
    onError: (error) => {
      toast({
        title: 'Sync failed',
        description: error instanceof Error ? error.message : 'An error occurred',
        variant: 'destructive',
      });
    },
  });

  const deleteDataSource = useMutation({
    mutationFn: (dataSourceId: string) => dataSourcesApi.deleteDataSource(dataSourceId),
    onSuccess: () => {
      toast({
        title: 'Data source deleted',
        description: 'The data source has been removed.',
      });
      queryClient.invalidateQueries({ queryKey: ['study-data-sources', studyId] });
    },
    onError: (error) => {
      toast({
        title: 'Delete failed',
        description: error instanceof Error ? error.message : 'An error occurred',
        variant: 'destructive',
      });
    },
  });

  const formatDate = (dateString: string | undefined) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleString();
  };

  // Check if there are any manual upload data sources
  const hasManualUploadSources = dataSources?.some(
    (source: any) => source.type === DataSourceType.ZIP_UPLOAD && source.is_active
  );

  return (
    <div className="container mx-auto py-6">
      <div className="flex items-center mb-6">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => router.push('/studies')}
          className="mr-4"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Studies
        </Button>
        <div className="flex-1">
          <h1 className="text-3xl font-bold">Data Sources - {study?.name}</h1>
          <p className="text-muted-foreground mt-1">
            Manage data connections for this study
          </p>
        </div>
        <div className="flex gap-2">
          {hasManualUploadSources && (
            <Button variant="outline" onClick={() => router.push(`/studies/${studyId}/data-sources/upload`)}>
              <Upload className="mr-2 h-4 w-4" />
              Upload Data
            </Button>
          )}
          <Button onClick={() => router.push(`/studies/${studyId}/data-sources/new`)}>
            <Plus className="mr-2 h-4 w-4" />
            Add Data Source
          </Button>
        </div>
      </div>

      {isLoading ? (
        <Card>
          <CardContent className="py-8">
            <p className="text-center text-muted-foreground">Loading data sources...</p>
          </CardContent>
        </Card>
      ) : !dataSources || dataSources.length === 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>No data sources configured</CardTitle>
            <CardDescription>
              Add data sources to start importing clinical data for this study
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={() => router.push(`/studies/${studyId}/data-sources/new`)}>
              <Plus className="mr-2 h-4 w-4" />
              Configure First Data Source
            </Button>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Configured Data Sources</CardTitle>
            <CardDescription>
              Data sources configured for {study?.name}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Last Sync</TableHead>
                  <TableHead>Next Sync</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {dataSources.map((source: any) => {
                  const Icon = dataSourceIcons[source.type as keyof typeof dataSourceIcons] || Database;
                  return (
                    <TableRow key={source.id}>
                      <TableCell className="font-medium">
                        <div className="flex items-center space-x-2">
                          <Icon className="h-4 w-4 text-muted-foreground" />
                          <span>{source.name}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <span className="text-sm">{source.type.replace('_', ' ').toUpperCase()}</span>
                      </TableCell>
                      <TableCell>
                        <Badge variant={source.is_active ? "default" : "secondary"}>
                          {source.is_active ? 'Active' : 'Inactive'}
                        </Badge>
                      </TableCell>
                      <TableCell>{formatDate(source.last_sync)}</TableCell>
                      <TableCell>
                        {source.config?.sync_schedule ? formatDate(source.next_sync) : 'Manual'}
                      </TableCell>
                      <TableCell className="text-right">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem 
                              onClick={() => router.push(`/studies/${studyId}/data-sources/${source.id}/edit`)}
                            >
                              <Settings className="mr-2 h-4 w-4" />
                              Configure
                            </DropdownMenuItem>
                            {source.type === DataSourceType.ZIP_UPLOAD && (
                              <DropdownMenuItem 
                                onClick={() => router.push(`/studies/${studyId}/data-sources/upload`)}
                              >
                                <Upload className="mr-2 h-4 w-4" />
                                Upload Data
                              </DropdownMenuItem>
                            )}
                            {source.type !== DataSourceType.ZIP_UPLOAD && (
                              <DropdownMenuItem 
                                onClick={() => syncDataSource.mutate(source.id)}
                              >
                                <RefreshCw className="mr-2 h-4 w-4" />
                                Sync Now
                              </DropdownMenuItem>
                            )}
                            <DropdownMenuItem 
                              className="text-destructive"
                              onClick={() => {
                                if (confirm('Are you sure you want to delete this data source?')) {
                                  deleteDataSource.mutate(source.id);
                                }
                              }}
                            >
                              <Trash2 className="mr-2 h-4 w-4" />
                              Delete
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}