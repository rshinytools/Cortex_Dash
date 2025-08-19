// ABOUTME: Data Source Tab - Manage study data sources and versions
// ABOUTME: Handles manual uploads, API integrations, and data versioning

'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { 
  Database, 
  Upload, 
  Clock, 
  HardDrive,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  FileText,
  Calendar,
  ChevronRight
} from 'lucide-react';
import { useState } from 'react';
import { useToast } from '@/hooks/use-toast';
import { DataUploadStep } from '@/components/study/initialization-wizard/steps/data-upload';

interface DataSourceTabProps {
  study: any;
  onUpdate: () => void;
}

export function DataSourceTab({ study, onUpdate }: DataSourceTabProps) {
  const { toast } = useToast();
  const [isUploading, setIsUploading] = useState(false);

  // Mock data versions for demonstration
  const dataVersions = [
    {
      version: '2024-03-10_09-15-00',
      date: '2024-03-10 09:15:00',
      records: 5420,
      status: 'current',
      uploadedBy: 'Admin User',
    },
    {
      version: '2024-02-20_14-45-00',
      date: '2024-02-20 14:45:00',
      records: 4850,
      status: 'archived',
      uploadedBy: 'Admin User',
    },
    {
      version: '2024-01-15_10-30-00',
      date: '2024-01-15 10:30:00',
      records: 3200,
      status: 'archived',
      uploadedBy: 'Admin User',
    },
  ];

  const handleDataUpload = async (files: File[]) => {
    setIsUploading(true);
    try {
      toast({
        title: 'Upload Started',
        description: 'Creating new data version...',
      });
      
      // Simulate upload - In real implementation, this would upload to backend
      // and create a new timestamped folder like /data/studies/{id}/source_data/2024-03-15_10-30-00/
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      toast({
        title: 'Success',
        description: 'New data version created successfully.',
      });
      onUpdate();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to upload data. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setIsUploading(false);
    }
  };

  const handleRollback = (version: string) => {
    toast({
      title: 'Version Restored',
      description: `Data rolled back to version ${version}`,
    });
    onUpdate();
  };

  return (
    <div className="space-y-6">
      {/* Current Data Source */}
      <Card className="bg-white dark:bg-slate-900">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            Current Data Source
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <p className="text-sm text-gray-500 dark:text-slate-500">Type</p>
              <p className="font-medium flex items-center gap-2">
                <Upload className="h-4 w-4" />
                Manual Upload
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500 dark:text-slate-500">Current Version</p>
              <p className="font-medium">2024-03-10_09-15-00</p>
            </div>
            <div>
              <p className="text-sm text-gray-500 dark:text-slate-500">Records</p>
              <p className="font-medium">5,420 rows</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Version History */}
      <Card className="bg-white dark:bg-slate-900">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Data Version History
          </CardTitle>
          <CardDescription>
            View and manage data versions
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {dataVersions.map((version) => (
              <div
                key={version.version}
                className="flex items-center justify-between p-3 rounded-lg border border-gray-200 dark:border-slate-800"
              >
                <div className="flex items-center gap-4">
                  <FileText className="h-5 w-5 text-gray-400" />
                  <div>
                    <div className="flex items-center gap-2">
                      <p className="font-medium">{version.version}</p>
                      {version.status === 'current' && (
                        <Badge variant="success" className="text-xs">
                          Current
                        </Badge>
                      )}
                    </div>
                    <p className="text-sm text-gray-500 dark:text-slate-500">
                      {version.records.toLocaleString()} records • {version.date}
                    </p>
                  </div>
                </div>
                {version.status !== 'current' && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleRollback(version.version)}
                  >
                    Restore
                  </Button>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Upload New Data */}
      <Card className="bg-white dark:bg-slate-900">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Upload className="h-5 w-5" />
            Upload New Data
          </CardTitle>
          <CardDescription>
            Upload new data files to create a new version. Each upload creates a timestamped version that can be rolled back if needed.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {/* Upload Component */}
          <DataUploadStep
            mode="edit"
            onUpload={handleDataUpload}
            hideNavigation={true}
          />
        </CardContent>
      </Card>

      {/* API Integration (Future) */}
      <Card className="bg-white dark:bg-slate-900 opacity-60">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <RefreshCw className="h-5 w-5" />
            API Integration
          </CardTitle>
          <CardDescription>
            Connect to external data sources for automatic updates
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              API integration coming soon. You'll be able to connect to Medidata Rave, Veeva Vault, and other EDC systems.
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    </div>
  );
}