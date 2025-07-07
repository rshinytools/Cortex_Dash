// ABOUTME: Export manager component for dashboard exports with format selection, progress tracking, and download handling
// ABOUTME: Supports PDF, PowerPoint, and Excel export formats with real-time status updates

'use client';

import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Progress } from '@/components/ui/progress';
import { Card, CardContent } from '@/components/ui/card';
import { AlertCircle, Download, FileText, FileSpreadsheet, FileImage, Check, Clock, X } from 'lucide-react';
import { toast } from 'sonner';
import { useSession } from 'next-auth/react';

interface ExportManagerProps {
  dashboardId: string;
  dashboardName: string;
  isOpen: boolean;
  onClose: () => void;
}

interface ExportStatus {
  export_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress?: number;
  message?: string;
  download_url?: string;
  expires_at?: string;
  file_size?: number;
}

export function ExportManager({ dashboardId, dashboardName, isOpen, onClose }: ExportManagerProps) {
  const [selectedFormat, setSelectedFormat] = useState<string>('pdf');
  const [isExporting, setIsExporting] = useState(false);
  const [exportStatus, setExportStatus] = useState<ExportStatus | null>(null);
  const [pollInterval, setPollInterval] = useState<NodeJS.Timeout | null>(null);
  const { data: session } = useSession();

  const formatOptions = [
    {
      value: 'pdf',
      label: 'PDF Document',
      description: 'Best for printing and sharing',
      icon: FileText,
    },
    {
      value: 'pptx',
      label: 'PowerPoint Presentation',
      description: 'Ideal for presentations',
      icon: FileImage,
    },
    {
      value: 'xlsx',
      label: 'Excel Workbook',
      description: 'Perfect for data analysis',
      icon: FileSpreadsheet,
    },
  ];

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollInterval) {
        clearInterval(pollInterval);
      }
    };
  }, [pollInterval]);

  const startExport = async () => {
    if (!session?.user?.accessToken) {
      toast.error('Authentication required');
      return;
    }

    setIsExporting(true);
    setExportStatus(null);

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/dashboards/${dashboardId}/export`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${session.user.accessToken}`,
          },
          body: JSON.stringify({
            format: selectedFormat,
            options: {},
          }),
        }
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Export failed');
      }

      const result = await response.json();
      setExportStatus(result);

      // If export is already completed, no need to poll
      if (result.status === 'completed') {
        toast.success('Export ready for download');
        setIsExporting(false);
      } else {
        // Start polling for status
        startStatusPolling(result.export_id);
      }
    } catch (error) {
      console.error('Export error:', error);
      toast.error(error instanceof Error ? error.message : 'Export failed');
      setIsExporting(false);
    }
  };

  const startStatusPolling = (exportId: string) => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/api/v1/dashboard-exports/${exportId}/status`,
          {
            headers: {
              Authorization: `Bearer ${session?.user?.accessToken}`,
            },
          }
        );

        if (!response.ok) {
          throw new Error('Failed to get export status');
        }

        const status = await response.json();
        setExportStatus(status);

        if (status.status === 'completed' || status.status === 'failed') {
          clearInterval(interval);
          setIsExporting(false);

          if (status.status === 'completed') {
            toast.success('Export ready for download');
          } else {
            toast.error(status.message || 'Export failed');
          }
        }
      } catch (error) {
        console.error('Status polling error:', error);
        clearInterval(interval);
        setIsExporting(false);
      }
    }, 2000); // Poll every 2 seconds

    setPollInterval(interval);
  };

  const downloadExport = async () => {
    if (!exportStatus?.download_url || !session?.user?.accessToken) return;

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}${exportStatus.download_url}`,
        {
          headers: {
            Authorization: `Bearer ${session.user.accessToken}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error('Download failed');
      }

      // Get the filename from the Content-Disposition header
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = `${dashboardName}_export.${selectedFormat}`;
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?(.+)"?/);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }

      // Convert response to blob and trigger download
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      toast.success('Download started');
    } catch (error) {
      console.error('Download error:', error);
      toast.error('Download failed');
    }
  };

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return 'Unknown size';
    const mb = bytes / (1024 * 1024);
    return mb > 1 ? `${mb.toFixed(1)} MB` : `${(bytes / 1024).toFixed(0)} KB`;
  };

  const getStatusIcon = () => {
    if (!exportStatus) return null;

    switch (exportStatus.status) {
      case 'pending':
        return <Clock className="h-4 w-4 text-yellow-500" />;
      case 'processing':
        return <Clock className="h-4 w-4 text-blue-500 animate-spin" />;
      case 'completed':
        return <Check className="h-4 w-4 text-green-500" />;
      case 'failed':
        return <X className="h-4 w-4 text-red-500" />;
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Export Dashboard</DialogTitle>
          <DialogDescription>
            Choose an export format for "{dashboardName}"
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Format selection */}
          <div className="space-y-3">
            <Label>Export Format</Label>
            <RadioGroup value={selectedFormat} onValueChange={setSelectedFormat}>
              {formatOptions.map((option) => {
                const Icon = option.icon;
                return (
                  <Card key={option.value} className="cursor-pointer">
                    <CardContent className="p-3">
                      <label
                        htmlFor={option.value}
                        className="flex items-start space-x-3 cursor-pointer"
                      >
                        <RadioGroupItem value={option.value} id={option.value} className="mt-1" />
                        <div className="flex-1">
                          <div className="flex items-center space-x-2">
                            <Icon className="h-4 w-4 text-muted-foreground" />
                            <span className="font-medium">{option.label}</span>
                          </div>
                          <p className="text-sm text-muted-foreground mt-1">
                            {option.description}
                          </p>
                        </div>
                      </label>
                    </CardContent>
                  </Card>
                );
              })}
            </RadioGroup>
          </div>

          {/* Export status */}
          {exportStatus && (
            <Card>
              <CardContent className="p-4">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      {getStatusIcon()}
                      <span className="text-sm font-medium">
                        {exportStatus.status === 'pending' && 'Preparing export...'}
                        {exportStatus.status === 'processing' && 'Generating export...'}
                        {exportStatus.status === 'completed' && 'Export ready'}
                        {exportStatus.status === 'failed' && 'Export failed'}
                      </span>
                    </div>
                    {exportStatus.file_size && (
                      <span className="text-sm text-muted-foreground">
                        {formatFileSize(exportStatus.file_size)}
                      </span>
                    )}
                  </div>

                  {exportStatus.progress !== undefined && exportStatus.status === 'processing' && (
                    <Progress value={exportStatus.progress} className="h-2" />
                  )}

                  {exportStatus.message && (
                    <p className="text-sm text-muted-foreground">{exportStatus.message}</p>
                  )}

                  {exportStatus.expires_at && exportStatus.status === 'completed' && (
                    <div className="flex items-center space-x-1 text-xs text-muted-foreground">
                      <AlertCircle className="h-3 w-3" />
                      <span>
                        Expires {new Date(exportStatus.expires_at).toLocaleDateString()}
                      </span>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={isExporting}>
            Cancel
          </Button>
          {exportStatus?.status === 'completed' ? (
            <Button onClick={downloadExport}>
              <Download className="h-4 w-4 mr-2" />
              Download
            </Button>
          ) : (
            <Button onClick={startExport} disabled={isExporting}>
              {isExporting ? 'Exporting...' : 'Export'}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}