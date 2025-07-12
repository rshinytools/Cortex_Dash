// ABOUTME: Main component for managing data source uploads and conversions
// ABOUTME: Displays upload history, status tracking, and file management

import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Upload,
  Download,
  RefreshCw,
  Trash2,
  FileText,
  AlertCircle,
  CheckCircle,
  Clock,
  XCircle,
  Loader2,
  ChevronDown,
  ChevronRight,
  GitBranch,
  GitCompare,
  ArrowUpDown,
} from 'lucide-react';
import { format } from 'date-fns';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
import { DataSourceUpload } from './DataSourceUpload';
import { dataUploadsApi, DataSourceUpload as UploadType } from '@/lib/api/data-uploads';
import { useToast } from '@/hooks/use-toast';
import { formatBytes } from '@/lib/utils';
import { VersionSwitcher } from './VersionSwitcher';
import { VersionComparison } from './VersionComparison';

interface DataSourceManagerProps {
  studyId: string;
}

const STATUS_CONFIG = {
  pending: { label: 'Pending', color: 'default', icon: Clock },
  uploading: { label: 'Uploading', color: 'default', icon: Loader2 },
  uploaded: { label: 'Uploaded', color: 'secondary', icon: CheckCircle },
  processing: { label: 'Processing', color: 'default', icon: Loader2 },
  completed: { label: 'Completed', color: 'success', icon: CheckCircle },
  failed: { label: 'Failed', color: 'destructive', icon: XCircle },
  cancelled: { label: 'Cancelled', color: 'secondary', icon: XCircle },
};

export function DataSourceManager({ studyId }: DataSourceManagerProps) {
  const [showUploadDialog, setShowUploadDialog] = useState(false);
  const [deleteUploadId, setDeleteUploadId] = useState<string | null>(null);
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());
  const [showVersionSwitcher, setShowVersionSwitcher] = useState(false);
  const [showVersionComparison, setShowVersionComparison] = useState(false);
  const [compareVersions, setCompareVersions] = useState<[string, string] | null>(null);
  const { toast } = useToast();
  const queryClient = useQueryClient();

  // Fetch uploads
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['dataUploads', studyId],
    queryFn: () => dataUploadsApi.listUploads(studyId, { active_only: false }),
    refetchInterval: (query) => {
      // Refetch every 5 seconds if any upload is processing
      const uploads = query.state.data?.data;
      if (!uploads) return false;
      
      const hasProcessing = uploads.some(
        (upload: UploadType) => upload.status === 'processing' || upload.status === 'uploading'
      );
      return hasProcessing ? 5000 : false;
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: dataUploadsApi.deleteUpload,
    onSuccess: () => {
      toast({
        title: 'Upload deleted',
        description: 'The upload has been deleted successfully.',
      });
      queryClient.invalidateQueries({ queryKey: ['dataUploads', studyId] });
    },
    onError: (err: any) => {
      toast({
        title: 'Delete failed',
        description: err.response?.data?.detail || 'Failed to delete upload',
        variant: 'destructive',
      });
    },
  });

  // Reprocess mutation
  const reprocessMutation = useMutation({
    mutationFn: dataUploadsApi.reprocessUpload,
    onSuccess: () => {
      toast({
        title: 'Reprocessing started',
        description: 'The upload is being reprocessed.',
      });
      queryClient.invalidateQueries({ queryKey: ['dataUploads', studyId] });
    },
    onError: (err: any) => {
      toast({
        title: 'Reprocess failed',
        description: err.response?.data?.detail || 'Failed to reprocess upload',
        variant: 'destructive',
      });
    },
  });

  const toggleRowExpansion = (uploadId: string) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(uploadId)) {
      newExpanded.delete(uploadId);
    } else {
      newExpanded.add(uploadId);
    }
    setExpandedRows(newExpanded);
  };

  const renderStatus = (status: UploadType['status']) => {
    const config = STATUS_CONFIG[status];
    const Icon = config.icon;
    
    return (
      <Badge variant={config.color as any} className="gap-1">
        {status === 'processing' || status === 'uploading' ? (
          <Icon className="h-3 w-3 animate-spin" />
        ) : (
          <Icon className="h-3 w-3" />
        )}
        {config.label}
      </Badge>
    );
  };

  const renderFileExtractedInfo = (upload: UploadType) => {
    if (!upload.files_extracted || upload.files_extracted.length === 0) {
      return null;
    }

    return (
      <div className="p-4 bg-gray-50 border-t">
        <h4 className="text-sm font-medium mb-3">Extracted Files</h4>
        <div className="space-y-2">
          {upload.files_extracted.map((file, idx) => (
            <div key={idx} className="bg-white p-3 rounded border text-sm">
              <div className="flex justify-between items-start mb-2">
                <div>
                  <span className="font-medium">{file.dataset_name}</span>
                  <span className="text-gray-500 ml-2">({file.name})</span>
                </div>
                <Badge variant="outline">{file.format.toUpperCase()}</Badge>
              </div>
              <div className="grid grid-cols-4 gap-4 text-xs text-gray-600">
                <div>
                  <span className="font-medium">Rows:</span> {file.rows.toLocaleString()}
                </div>
                <div>
                  <span className="font-medium">Columns:</span> {file.columns}
                </div>
                <div>
                  <span className="font-medium">Size:</span> {formatBytes(file.size_mb * 1024 * 1024)}
                </div>
                <div>
                  <span className="font-medium">Format:</span> Parquet
                </div>
              </div>
              {file.column_info && file.column_info.length > 0 && (
                <details className="mt-2">
                  <summary className="cursor-pointer text-xs text-blue-600 hover:text-blue-800">
                    View columns ({file.column_info.length})
                  </summary>
                  <div className="mt-2 grid grid-cols-3 gap-1 text-xs">
                    {file.column_info.slice(0, 12).map((col, colIdx) => (
                      <div key={colIdx} className="truncate">
                        <span className="font-medium">{col.name}</span>
                        <span className="text-gray-500 ml-1">({col.type})</span>
                      </div>
                    ))}
                    {file.column_info.length > 12 && (
                      <div className="text-gray-500">
                        ... and {file.column_info.length - 12} more
                      </div>
                    )}
                  </div>
                </details>
              )}
            </div>
          ))}
        </div>
      </div>
    );
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Data Sources</CardTitle>
          <CardDescription>Loading data source uploads...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Data Sources</CardTitle>
        </CardHeader>
        <CardContent>
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Failed to load data sources. Please try again.
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  const uploads = data?.data || [];

  return (
    <>
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Data Sources</CardTitle>
              <CardDescription>
                Manage clinical data uploads and view processing status
              </CardDescription>
            </div>
            <div className="flex gap-2">
              {uploads.length > 1 && (
                <>
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={() => setShowVersionSwitcher(true)}
                  >
                    <GitBranch className="mr-2 h-4 w-4" />
                    Switch Version
                  </Button>
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={() => {
                      const activeVersion = uploads.find(u => u.is_active_version);
                      const latestVersion = uploads[0]; // Assuming sorted by version desc
                      if (activeVersion && latestVersion && activeVersion.id !== latestVersion.id) {
                        setCompareVersions([activeVersion.id, latestVersion.id]);
                        setShowVersionComparison(true);
                      }
                    }}
                  >
                    <GitCompare className="mr-2 h-4 w-4" />
                    Compare
                  </Button>
                </>
              )}
              <Button onClick={() => setShowUploadDialog(true)}>
                <Upload className="mr-2 h-4 w-4" />
                Upload Data
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {uploads.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="mx-auto h-12 w-12 text-gray-400 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                No data sources uploaded
              </h3>
              <p className="text-sm text-gray-500 mb-4">
                Upload clinical data files to get started
              </p>
              <Button onClick={() => setShowUploadDialog(true)}>
                <Upload className="mr-2 h-4 w-4" />
                Upload First Data Source
              </Button>
            </div>
          ) : (
            <div className="overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[30px]"></TableHead>
                    <TableHead>Upload Name</TableHead>
                    <TableHead>File</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Version</TableHead>
                    <TableHead>Uploaded</TableHead>
                    <TableHead>Size</TableHead>
                    <TableHead>Data Summary</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {uploads.map((upload) => (
                    <React.Fragment key={upload.id}>
                      <TableRow>
                        <TableCell>
                          {upload.files_extracted && upload.files_extracted.length > 0 && (
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-6 w-6"
                              onClick={() => toggleRowExpansion(upload.id)}
                            >
                              {expandedRows.has(upload.id) ? (
                                <ChevronDown className="h-4 w-4" />
                              ) : (
                                <ChevronRight className="h-4 w-4" />
                              )}
                            </Button>
                          )}
                        </TableCell>
                        <TableCell className="font-medium">
                          {upload.upload_name}
                          {upload.description && (
                            <p className="text-xs text-gray-500 mt-1">
                              {upload.description}
                            </p>
                          )}
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <FileText className="h-4 w-4 text-gray-400" />
                            <span className="text-sm">{upload.original_filename}</span>
                          </div>
                        </TableCell>
                        <TableCell>{renderStatus(upload.status)}</TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <span>v{upload.version_number}</span>
                            {upload.is_active_version && (
                              <Badge variant="outline" className="text-xs">
                                Active
                              </Badge>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>
                          {format(new Date(upload.upload_timestamp), 'MMM d, yyyy HH:mm')}
                        </TableCell>
                        <TableCell>{formatBytes(upload.file_size_mb * 1024 * 1024)}</TableCell>
                        <TableCell>
                          {upload.status === 'completed' && upload.total_rows ? (
                            <div className="text-sm">
                              <div>{upload.total_rows.toLocaleString()} rows</div>
                              {upload.files_extracted && (
                                <div className="text-xs text-gray-500">
                                  {upload.files_extracted.length} files
                                </div>
                              )}
                            </div>
                          ) : upload.status === 'processing' ? (
                            <span className="text-sm text-gray-500">Processing...</span>
                          ) : upload.status === 'failed' ? (
                            <span className="text-sm text-red-600">Failed</span>
                          ) : (
                            <span className="text-sm text-gray-500">-</span>
                          )}
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end gap-2">
                            {upload.status === 'failed' && (
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => reprocessMutation.mutate(upload.id)}
                                disabled={reprocessMutation.isPending}
                              >
                                <RefreshCw className="h-4 w-4" />
                              </Button>
                            )}
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => setDeleteUploadId(upload.id)}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                      {expandedRows.has(upload.id) && (
                        <TableRow>
                          <TableCell colSpan={9} className="p-0">
                            {renderFileExtractedInfo(upload)}
                          </TableCell>
                        </TableRow>
                      )}
                      {upload.error_message && (
                        <TableRow>
                          <TableCell colSpan={9}>
                            <Alert variant="destructive" className="mb-0">
                              <AlertCircle className="h-4 w-4" />
                              <AlertDescription>{upload.error_message}</AlertDescription>
                            </Alert>
                          </TableCell>
                        </TableRow>
                      )}
                      {upload.warnings && upload.warnings.length > 0 && (
                        <TableRow>
                          <TableCell colSpan={9}>
                            <Alert className="mb-0">
                              <AlertCircle className="h-4 w-4" />
                              <AlertDescription>
                                <div className="space-y-1">
                                  {upload.warnings.map((warning, idx) => (
                                    <div key={idx}>{warning}</div>
                                  ))}
                                </div>
                              </AlertDescription>
                            </Alert>
                          </TableCell>
                        </TableRow>
                      )}
                    </React.Fragment>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Upload Dialog */}
      <DataSourceUpload
        studyId={studyId}
        open={showUploadDialog}
        onOpenChange={setShowUploadDialog}
        onUploadComplete={() => refetch()}
      />

      {/* Delete Confirmation */}
      <AlertDialog open={!!deleteUploadId} onOpenChange={() => setDeleteUploadId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Upload</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete this upload? This will also delete all
              associated files and cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                if (deleteUploadId) {
                  deleteMutation.mutate(deleteUploadId);
                  setDeleteUploadId(null);
                }
              }}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Version Switcher Dialog */}
      <Dialog open={showVersionSwitcher} onOpenChange={setShowVersionSwitcher}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>Switch Data Version</DialogTitle>
            <DialogDescription>
              Select which version of uploaded data to use for this study
            </DialogDescription>
          </DialogHeader>
          <VersionSwitcher
            studyId={studyId}
            currentVersionId={uploads.find(u => u.is_active_version)?.id || ''}
            availableVersions={uploads}
            onClose={() => setShowVersionSwitcher(false)}
          />
        </DialogContent>
      </Dialog>

      {/* Version Comparison Dialog */}
      {showVersionComparison && compareVersions && (
        <Dialog open={showVersionComparison} onOpenChange={setShowVersionComparison}>
          <DialogContent className="max-w-6xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Version Comparison</DialogTitle>
              <DialogDescription>
                Compare changes between data versions
              </DialogDescription>
            </DialogHeader>
            <VersionComparison
              studyId={studyId}
              version1Id={compareVersions[0]}
              version2Id={compareVersions[1]}
              onVersionSwitch={(versionId) => {
                dataUploadsApi.activateVersion(studyId, versionId).then(() => {
                  toast({
                    title: 'Version switched',
                    description: 'The selected version is now active.',
                  });
                  refetch();
                  setShowVersionComparison(false);
                });
              }}
              onClose={() => setShowVersionComparison(false)}
            />
          </DialogContent>
        </Dialog>
      )}
    </>
  );
}