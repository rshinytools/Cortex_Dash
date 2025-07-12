// ABOUTME: Component for uploading data source files with drag and drop support
// ABOUTME: Handles file validation, upload progress, and error handling

import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File, X, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { dataUploadsApi } from '@/lib/api/data-uploads';
import { useToast } from '@/hooks/use-toast';
import { formatBytes } from '@/lib/utils';

interface DataSourceUploadProps {
  studyId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onUploadComplete?: () => void;
}

const ACCEPTED_FILE_TYPES = {
  'text/csv': ['.csv'],
  'application/zip': ['.zip'],
  'application/vnd.ms-excel': ['.xls'],
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
  'application/octet-stream': ['.sas7bdat', '.xpt'],
  'application/x-sas-xport': ['.xpt'],
};

const MAX_FILE_SIZE = 500 * 1024 * 1024; // 500MB

export function DataSourceUpload({
  studyId,
  open,
  onOpenChange,
  onUploadComplete,
}: DataSourceUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [uploadName, setUploadName] = useState('');
  const [description, setDescription] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const { toast } = useToast();

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      const droppedFile = acceptedFiles[0];
      setFile(droppedFile);
      setError(null);
      
      // Auto-fill upload name from filename if empty
      if (!uploadName) {
        const nameWithoutExt = droppedFile.name.replace(/\.[^/.]+$/, '');
        setUploadName(nameWithoutExt);
      }
    }
  }, [uploadName]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED_FILE_TYPES,
    maxSize: MAX_FILE_SIZE,
    multiple: false,
    onDropRejected: (rejectedFiles: any[]) => {
      const rejection = rejectedFiles[0];
      if (rejection.errors[0]?.code === 'file-too-large') {
        setError(`File is too large. Maximum size is ${formatBytes(MAX_FILE_SIZE)}`);
      } else if (rejection.errors[0]?.code === 'file-invalid-type') {
        setError('Invalid file type. Supported: CSV, ZIP, XLS, XLSX, SAS7BDAT, XPT');
      } else {
        setError('Failed to process file');
      }
    },
  });

  const handleUpload = async () => {
    if (!file || !uploadName) return;

    setIsUploading(true);
    setUploadProgress(0);
    setError(null);

    try {
      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => Math.min(prev + 10, 90));
      }, 200);

      await dataUploadsApi.uploadFile(studyId, file, uploadName, description);

      clearInterval(progressInterval);
      setUploadProgress(100);

      toast({
        title: 'Upload successful',
        description: `${file.name} has been uploaded and is being processed.`,
      });

      // Reset form
      setFile(null);
      setUploadName('');
      setDescription('');
      onOpenChange(false);
      onUploadComplete?.();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload file');
      toast({
        title: 'Upload failed',
        description: err.response?.data?.detail || 'Failed to upload file',
        variant: 'destructive',
      });
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
    }
  };

  const handleRemoveFile = () => {
    setFile(null);
    setError(null);
  };

  const handleClose = () => {
    if (!isUploading) {
      setFile(null);
      setUploadName('');
      setDescription('');
      setError(null);
      onOpenChange(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>Upload Data Source</DialogTitle>
          <DialogDescription>
            Upload clinical data files for processing. Supported formats: CSV, ZIP, Excel, SAS files.
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-6 py-4">
          {/* Upload Name */}
          <div className="grid gap-2">
            <Label htmlFor="upload-name">Upload Name</Label>
            <Input
              id="upload-name"
              value={uploadName}
              onChange={(e) => setUploadName(e.target.value)}
              placeholder="e.g., January 2024 Data Extract"
              disabled={isUploading}
            />
          </div>

          {/* File Upload Area */}
          <div className="grid gap-2">
            <Label>File</Label>
            {!file ? (
              <div
                {...getRootProps()}
                className={`
                  border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
                  transition-colors duration-200
                  ${isDragActive 
                    ? 'border-primary bg-primary/5' 
                    : 'border-gray-300 hover:border-gray-400'
                  }
                  ${error ? 'border-destructive' : ''}
                `}
              >
                <input {...getInputProps()} />
                <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                <p className="text-sm text-gray-600">
                  {isDragActive
                    ? 'Drop the file here...'
                    : 'Drag and drop a file here, or click to select'
                  }
                </p>
                <p className="text-xs text-gray-500 mt-2">
                  Supported: CSV, ZIP, XLS, XLSX, SAS7BDAT, XPT (Max {formatBytes(MAX_FILE_SIZE)})
                </p>
              </div>
            ) : (
              <div className="border rounded-lg p-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <File className="h-8 w-8 text-gray-400" />
                  <div>
                    <p className="text-sm font-medium">{file.name}</p>
                    <p className="text-xs text-gray-500">{formatBytes(file.size)}</p>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={handleRemoveFile}
                  disabled={isUploading}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            )}
          </div>

          {/* Description */}
          <div className="grid gap-2">
            <Label htmlFor="description">Description (Optional)</Label>
            <Textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Add any notes about this data upload..."
              rows={3}
              disabled={isUploading}
            />
          </div>

          {/* Error Alert */}
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Upload Progress */}
          {isUploading && (
            <div className="grid gap-2">
              <div className="flex justify-between text-sm">
                <span>Uploading...</span>
                <span>{uploadProgress}%</span>
              </div>
              <Progress value={uploadProgress} />
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleClose} disabled={isUploading}>
            Cancel
          </Button>
          <Button 
            onClick={handleUpload} 
            disabled={!file || !uploadName || isUploading}
          >
            {isUploading ? 'Uploading...' : 'Upload'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}