// ABOUTME: Data upload dialog component for uploading clinical data files
// ABOUTME: Supports multiple formats with automatic Parquet conversion

import React, { useState, useCallback } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Upload,
  FileUp,
  CheckCircle,
  XCircle,
  Loader2,
  FileText,
  Package,
  AlertTriangle
} from 'lucide-react';
import { useDropzone } from 'react-dropzone';
import { useToast } from '@/components/ui/use-toast';

interface DataUploadDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  studyId: string;
  onUploadComplete?: () => void;
}

const ACCEPTED_FORMATS = {
  'text/csv': ['.csv'],
  'application/vnd.ms-excel': ['.xls'],
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
  'application/x-sas-data': ['.sas7bdat'],
  'application/x-sas-xport': ['.xpt'],
  'application/zip': ['.zip'],
  'application/x-zip-compressed': ['.zip']
};

export function DataUploadDialog({
  open,
  onOpenChange,
  studyId,
  onUploadComplete
}: DataUploadDialogProps) {
  const [file, setFile] = useState<File | null>(null);
  const [uploadName, setUploadName] = useState('');
  const [description, setDescription] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'processing' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState('');
  const { toast } = useToast();

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      const uploadedFile = acceptedFiles[0];
      setFile(uploadedFile);
      
      // Auto-generate upload name from filename
      if (!uploadName) {
        const name = uploadedFile.name.replace(/\.[^/.]+$/, '');
        setUploadName(name);
      }
    }
  }, [uploadName]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED_FORMATS,
    multiple: false,
    maxSize: 500 * 1024 * 1024 // 500MB max
  });

  const handleUpload = async () => {
    if (!file || !uploadName) return;

    setUploading(true);
    setUploadStatus('uploading');
    setUploadProgress(0);
    setErrorMessage('');

    const formData = new FormData();
    formData.append('file', file);
    formData.append('upload_name', uploadName);
    if (description) {
      formData.append('description', description);
    }

    try {
      // Simulate progress updates
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 500);

      const response = await fetch(`/api/v1/data/studies/${studyId}/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: formData
      });

      clearInterval(progressInterval);

      if (response.ok) {
        setUploadProgress(100);
        setUploadStatus('success');
        
        toast({
          title: 'Upload successful',
          description: 'Your data has been uploaded and converted to Parquet format.',
        });

        setTimeout(() => {
          onOpenChange(false);
          if (onUploadComplete) {
            onUploadComplete();
          }
          // Reset form
          setFile(null);
          setUploadName('');
          setDescription('');
          setUploadStatus('idle');
          setUploadProgress(0);
        }, 2000);
      } else {
        const error = await response.json();
        throw new Error(error.detail || 'Upload failed');
      }
    } catch (error) {
      setUploadStatus('error');
      setErrorMessage(error instanceof Error ? error.message : 'Upload failed');
      
      toast({
        title: 'Upload failed',
        description: errorMessage,
        variant: 'destructive',
      });
    } finally {
      setUploading(false);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  const getFileIcon = (filename: string) => {
    const ext = filename.split('.').pop()?.toLowerCase();
    if (ext === 'zip') return <Package className="h-8 w-8" />;
    return <FileText className="h-8 w-8" />;
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Upload Data</DialogTitle>
          <DialogDescription>
            Upload clinical data files for this study. Files will be automatically converted to Parquet format for optimal performance.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* File Drop Zone */}
          <div
            {...getRootProps()}
            className={`
              border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
              transition-colors duration-200
              ${isDragActive ? 'border-primary bg-primary/5' : 'border-muted-foreground/25'}
              ${file ? 'bg-muted/50' : 'hover:border-primary/50'}
            `}
          >
            <input {...getInputProps()} />
            
            {file ? (
              <div className="space-y-2">
                <div className="flex items-center justify-center">
                  {getFileIcon(file.name)}
                </div>
                <p className="font-medium">{file.name}</p>
                <p className="text-sm text-muted-foreground">
                  {formatFileSize(file.size)}
                </p>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    setFile(null);
                  }}
                >
                  Remove file
                </Button>
              </div>
            ) : (
              <div className="space-y-2">
                <Upload className="h-10 w-10 mx-auto text-muted-foreground" />
                <p className="font-medium">
                  {isDragActive ? 'Drop the file here' : 'Drag & drop a file here'}
                </p>
                <p className="text-sm text-muted-foreground">
                  or click to browse
                </p>
                <p className="text-xs text-muted-foreground">
                  Supported formats: CSV, Excel, SAS, ZIP
                </p>
              </div>
            )}
          </div>

          {/* Upload Name */}
          <div className="space-y-2">
            <Label htmlFor="upload-name">Upload Name *</Label>
            <Input
              id="upload-name"
              value={uploadName}
              onChange={(e) => setUploadName(e.target.value)}
              placeholder="e.g., January 2024 Data Extract"
              disabled={uploading}
            />
          </div>

          {/* Description */}
          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Optional description of this data upload"
              rows={3}
              disabled={uploading}
            />
          </div>

          {/* Upload Progress */}
          {uploadStatus !== 'idle' && (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span>
                  {uploadStatus === 'uploading' && 'Uploading...'}
                  {uploadStatus === 'processing' && 'Converting to Parquet...'}
                  {uploadStatus === 'success' && 'Upload complete!'}
                  {uploadStatus === 'error' && 'Upload failed'}
                </span>
                <span>{uploadProgress}%</span>
              </div>
              <Progress value={uploadProgress} />
              
              {uploadStatus === 'success' && (
                <Alert>
                  <CheckCircle className="h-4 w-4" />
                  <AlertDescription>
                    Your data has been successfully uploaded and converted to Parquet format.
                  </AlertDescription>
                </Alert>
              )}
              
              {uploadStatus === 'error' && (
                <Alert variant="destructive">
                  <XCircle className="h-4 w-4" />
                  <AlertDescription>
                    {errorMessage}
                  </AlertDescription>
                </Alert>
              )}
            </div>
          )}

          {/* Info Alert */}
          <Alert>
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              <strong>Important:</strong> Uploaded files will be converted to Parquet format for optimal performance. 
              Original files are preserved for reference. Each upload creates a new version.
            </AlertDescription>
          </Alert>
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={uploading}
          >
            Cancel
          </Button>
          <Button
            onClick={handleUpload}
            disabled={!file || !uploadName || uploading}
          >
            {uploading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Uploading...
              </>
            ) : (
              <>
                <FileUp className="mr-2 h-4 w-4" />
                Upload
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}