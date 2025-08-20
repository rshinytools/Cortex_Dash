// ABOUTME: Data upload step for study initialization wizard
// ABOUTME: Handles file uploads with drag-and-drop support

import React, { useState, useCallback, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useToast } from '@/hooks/use-toast';
import { 
  Upload, 
  FileSpreadsheet, 
  X, 
  ChevronRight,
  CheckCircle2,
  AlertCircle,
  Loader2,
  FlaskConical,
  Clock,
  FileText,
  Database
} from 'lucide-react';
import { studiesApi } from '@/lib/api/studies';
import { formatBytes } from '@/lib/utils';

interface UploadedFile {
  name: string;
  size: number;
  type: string;
  status: 'pending' | 'uploading' | 'completed' | 'error';
  progress?: number;
  error?: string;
  file?: File;  // Store the actual File object
}

interface DataUploadStepProps {
  studyId?: string | null;
  data?: { files?: UploadedFile[] };
  onComplete?: (data: { files: UploadedFile[] }) => void;
  isLoading?: boolean;
  mode?: 'create' | 'edit';
  onUpload?: (files: File[]) => void;
  hideNavigation?: boolean;
  uploadMode?: 'replace' | 'append';
}

const ACCEPTED_FILE_TYPES = {
  'text/csv': ['.csv'],
  'application/vnd.ms-excel': ['.xls'],
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
  'application/x-sas-data': ['.sas7bdat'],
  'application/x-sas-xport': ['.xpt'],
  'application/zip': ['.zip'],
};

export function DataUploadStep({ 
  studyId, 
  data, 
  onComplete, 
  isLoading,
  mode = 'create',
  onUpload,
  hideNavigation = false,
  uploadMode = 'replace'
}: DataUploadStepProps) {
  const { toast } = useToast();
  const [files, setFiles] = useState<UploadedFile[]>(data?.files || []);
  const [isUploading, setIsUploading] = useState(false);
  const [dataVersions, setDataVersions] = useState<any[]>([]);
  const [isLoadingVersions, setIsLoadingVersions] = useState(false);

  // Fetch data versions in edit mode
  useEffect(() => {
    if (mode === 'edit' && studyId) {
      const fetchDataVersions = async () => {
        try {
          setIsLoadingVersions(true);
          const response = await studiesApi.getDataVersions(studyId);
          setDataVersions(response.versions || []);
        } catch (error) {
          console.error('Failed to fetch data versions:', error);
        } finally {
          setIsLoadingVersions(false);
        }
      };
      fetchDataVersions();
    }
  }, [mode, studyId]);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles: UploadedFile[] = acceptedFiles.map(file => ({
      name: file.name,
      size: file.size,
      type: file.type || 'unknown',
      status: 'pending' as const,
      file: file,  // Store the actual File object
    }));
    
    setFiles(prev => [...prev, ...newFiles]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED_FILE_TYPES,
    disabled: isUploading,
  });

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const uploadFiles = async () => {
    if (!studyId || files.length === 0) return;
    
    setIsUploading(true);
    
    try {
      // Create FormData with all pending files
      const formData = new FormData();
      
      // Add all files that have a File object and are pending
      const filesToUpload = files.filter(f => f.file && f.status === 'pending');
      
      if (filesToUpload.length === 0) {
        toast({
          title: 'No files to upload',
          description: 'Please add files before uploading',
          variant: 'destructive',
        });
        setIsUploading(false);
        return;
      }
      
      filesToUpload.forEach(f => {
        if (f.file) {
          formData.append('files', f.file);
        }
      });
      
      console.log('Uploading files to studyId:', studyId);
      console.log('FormData has files:', formData.getAll('files').length);
      
      // Update file statuses to uploading
      setFiles(prev => prev.map(f => ({ ...f, status: 'uploading' as const, progress: 0 })));
      
      // Upload files
      const response = await studiesApi.uploadStudyData(studyId, formData);
      console.log('Upload response:', response);
      
      // Update file statuses to completed
      setFiles(prev => prev.map(f => ({ 
        ...f, 
        status: 'completed' as const, 
        progress: 100 
      })));
      
      toast({
        title: 'Upload Complete',
        description: `Successfully uploaded ${response.total_files} files`,
      });
      
    } catch (error: any) {
      // Update file statuses to error
      setFiles(prev => prev.map(f => ({ 
        ...f, 
        status: 'error' as const,
        error: error.message 
      })));
      
      toast({
        title: 'Upload Failed',
        description: error.message || 'Failed to upload files',
        variant: 'destructive',
      });
    } finally {
      setIsUploading(false);
    }
  };

  const handleSubmit = async () => {
    console.log('handleSubmit called, files:', files);
    
    // In edit mode, call onUpload with the actual File objects
    if (mode === 'edit' && onUpload) {
      const fileObjects = files
        .filter(f => f.file)
        .map(f => f.file as File);
      
      if (fileObjects.length === 0) {
        toast({
          title: 'Error',
          description: 'Please select files to upload',
          variant: 'destructive',
        });
        return;
      }
      
      onUpload(fileObjects);
      return;
    }
    
    // Original create mode logic
    // Upload any pending files first
    const hasPendingFiles = files.some(f => f.status === 'pending');
    if (hasPendingFiles) {
      console.log('Found pending files, uploading...');
      await uploadFiles();
    }
    
    // Check if all files uploaded successfully
    const hasErrors = files.some(f => f.status === 'error');
    if (hasErrors) {
      toast({
        title: 'Error',
        description: 'Please fix upload errors before continuing',
        variant: 'destructive',
      });
      return;
    }
    
    if (files.length === 0) {
      toast({
        title: 'Error',
        description: 'Please upload at least one data file',
        variant: 'destructive',
      });
      return;
    }
    
    console.log('Calling onComplete with files:', files);
    if (onComplete) {
      onComplete({ 
        files
      });
    }
  };

  const getFileIcon = (file: UploadedFile) => {
    switch (file.status) {
      case 'completed':
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      case 'uploading':
        return <Loader2 className="h-4 w-4 animate-spin text-blue-500" />;
      default:
        return <FileSpreadsheet className="h-4 w-4 text-gray-400" />;
    }
  };

  const hasCompletedFiles = files.some(f => f.status === 'completed');

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium">Upload Study Data</h3>
        <p className="text-sm text-muted-foreground">
          Upload your clinical data files for processing
        </p>
      </div>

      {/* Data Version History - Only show in edit mode */}
      {mode === 'edit' && (
        <Card className="bg-slate-950 border-slate-800">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Clock className="h-4 w-4" />
              Data Version History
            </CardTitle>
            <CardDescription>
              Previous data uploads for this study
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isLoadingVersions ? (
              <div className="flex items-center justify-center py-4">
                <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
              </div>
            ) : dataVersions.length > 0 ? (
              <div className="space-y-2">
                {dataVersions.slice(0, 3).map((version) => (
                  <div
                    key={version.version}
                    className="flex items-center justify-between p-3 rounded-lg border border-slate-800 bg-slate-900"
                  >
                    <div className="flex items-center gap-3">
                      <FileText className="h-4 w-4 text-gray-400" />
                      <div>
                        <div className="flex items-center gap-2">
                          <p className="text-sm font-medium">{version.version}</p>
                          {version.status === 'current' && (
                            <Badge variant="success" className="text-xs">
                              Current
                            </Badge>
                          )}
                        </div>
                        <p className="text-xs text-gray-500">
                          {version.file_count} files • {version.size_readable} • {version.date}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <Alert className="bg-slate-900 border-slate-800">
                <Database className="h-4 w-4" />
                <AlertDescription>
                  No previous data versions found. Upload new data files below.
                </AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>
      )}

      {/* Dropzone */}
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
          transition-colors
          ${isDragActive ? 'border-primary bg-primary/5' : 'border-gray-300 hover:border-gray-400'}
          ${isUploading ? 'opacity-50 cursor-not-allowed' : ''}
        `}
      >
        <input {...getInputProps()} />
        <Upload className="h-12 w-12 mx-auto mb-4 text-gray-400" />
        {isDragActive ? (
          <p className="text-lg font-medium">Drop files here...</p>
        ) : (
          <>
            <p className="text-lg font-medium mb-1">
              Drag & drop files here, or click to select
            </p>
            <p className="text-sm text-muted-foreground">
              Supports CSV, Excel, SAS (.sas7bdat, .xpt), and ZIP files
            </p>
          </>
        )}
      </div>

      {/* File List */}
      {files.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium">Uploaded Files</h4>
          {files.map((file, index) => (
            <Card key={index}>
              <CardContent className="flex items-center justify-between p-4">
                <div className="flex items-center gap-3 flex-1">
                  {getFileIcon(file)}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{file.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {formatBytes(file.size)}
                    </p>
                  </div>
                  {file.status === 'uploading' && file.progress !== undefined && (
                    <div className="w-32">
                      <Progress value={file.progress} className="h-1" />
                    </div>
                  )}
                  {file.error && (
                    <Badge variant="destructive" className="text-xs">
                      {file.error}
                    </Badge>
                  )}
                </div>
                {file.status === 'pending' && !isUploading && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeFile(index)}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Info Alert */}
      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          <div className="space-y-2">
            <p>Your data will be automatically converted to optimized format and field mappings will be detected based on your selected template.</p>
            {isUploading && (
              <p className="font-medium text-blue-600">
                Please wait while files are being uploaded. Do not navigate away from this page.
              </p>
            )}
          </div>
        </AlertDescription>
      </Alert>

      {/* Actions */}
      {!hideNavigation && (
        <div className="flex justify-between pt-4 border-t">
          <div>
            {files.length > 0 && !hasCompletedFiles && (
              <Button
                variant="outline"
                onClick={uploadFiles}
                disabled={isUploading}
              >
                {isUploading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Uploading...
                  </>
                ) : (
                  <>
                    <Upload className="mr-2 h-4 w-4" />
                    Upload Files
                  </>
                )}
              </Button>
            )}
          </div>
          <Button 
            onClick={handleSubmit} 
            disabled={files.length === 0 || isUploading || isLoading || files.some(f => f.status === 'uploading')}
          >
            {isUploading ? 'Uploading...' : 'Next'}
            <ChevronRight className="ml-2 h-4 w-4" />
          </Button>
        </div>
      )}
      
      {/* Edit Mode Actions */}
      {hideNavigation && mode === 'edit' && files.length > 0 && (
        <div className="flex justify-end pt-4">
          <Button 
            onClick={handleSubmit} 
            disabled={files.length === 0 || isUploading}
            className="bg-blue-600 hover:bg-blue-700"
          >
            {isUploading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Uploading...
              </>
            ) : (
              <>
                <Upload className="mr-2 h-4 w-4" />
                Upload New Version
              </>
            )}
          </Button>
        </div>
      )}
    </div>
  );
}