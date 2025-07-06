// ABOUTME: Data upload page for manual data sources
// ABOUTME: Allows users to upload new data extracts for existing studies

'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useSession } from 'next-auth/react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useToast } from '@/hooks/use-toast';
import { ArrowLeft, Upload, AlertCircle, FileZip, Lock } from 'lucide-react';
import { Switch } from '@/components/ui/switch';
import { studiesApi } from '@/lib/api/studies';
import { dataSourcesApi, DataSourceType } from '@/lib/api/data-sources';
import { UserMenu } from '@/components/user-menu';

export default function DataUploadPage() {
  const router = useRouter();
  const params = useParams();
  const studyId = params.studyId as string;
  const { data: session } = useSession();
  const { toast } = useToast();
  
  const [selectedDataSource, setSelectedDataSource] = useState<string>('');
  const [extractDate, setExtractDate] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [hasPassword, setHasPassword] = useState(false);
  const [password, setPassword] = useState('');
  const [isUploading, setIsUploading] = useState(false);

  // Fetch study details
  const { data: study } = useQuery({
    queryKey: ['study', studyId],
    queryFn: () => studiesApi.getStudy(studyId),
  });

  // Fetch data sources for the study
  const { data: dataSources = [] } = useQuery({
    queryKey: ['data-sources', studyId],
    queryFn: () => dataSourcesApi.getDataSources(studyId),
  });

  // Filter to only show manual upload data sources
  const manualDataSources = dataSources.filter(ds => ds.type === DataSourceType.ZIP_UPLOAD);

  // Set default data source
  useEffect(() => {
    if (manualDataSources.length > 0 && !selectedDataSource) {
      setSelectedDataSource(manualDataSources[0].id);
    }
  }, [manualDataSources, selectedDataSource]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      if (!selectedFile.name.endsWith('.zip')) {
        toast({
          title: 'Invalid file type',
          description: 'Only ZIP files are accepted',
          variant: 'destructive',
        });
        return;
      }
      
      if (selectedFile.size > 500 * 1024 * 1024) {
        toast({
          title: 'File too large',
          description: 'File size must be less than 500MB',
          variant: 'destructive',
        });
        return;
      }
      
      setFile(selectedFile);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      toast({
        title: 'No file selected',
        description: 'Please select a ZIP file to upload',
        variant: 'destructive',
      });
      return;
    }

    if (!extractDate) {
      toast({
        title: 'Extract date required',
        description: 'Please enter the EDC extract date',
        variant: 'destructive',
      });
      return;
    }

    // Validate extract date format
    const datePattern = /^[0-9]{2}[A-Z]{3}[0-9]{4}$/;
    if (!datePattern.test(extractDate)) {
      toast({
        title: 'Invalid date format',
        description: 'Date must be in DDMMMYYYY format (e.g., 05JUL2025)',
        variant: 'destructive',
      });
      return;
    }

    if (!selectedDataSource) {
      toast({
        title: 'No data source selected',
        description: 'Please select a data source',
        variant: 'destructive',
      });
      return;
    }

    setIsUploading(true);
    try {
      await dataSourcesApi.uploadDataFile(
        studyId,
        selectedDataSource,
        file,
        extractDate,
        hasPassword ? password : undefined
      );

      toast({
        title: 'Upload successful',
        description: `Data uploaded for extract date ${extractDate}`,
      });

      // Navigate back to data sources page
      router.push(`/studies/${studyId}/data-sources`);
    } catch (error: any) {
      toast({
        title: 'Upload failed',
        description: error.response?.data?.detail || 'Failed to upload file',
        variant: 'destructive',
      });
    } finally {
      setIsUploading(false);
    }
  };

  if (manualDataSources.length === 0) {
    return (
      <div className="container mx-auto py-6">
        <div className="flex items-center mb-6">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => router.push(`/studies/${studyId}/data-sources`)}
            className="mr-4"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Data Sources
          </Button>
          <div className="flex-1">
            <h1 className="text-3xl font-bold">Upload Data</h1>
            <p className="text-muted-foreground mt-1">
              {study?.name} - {study?.protocol_number}
            </p>
          </div>
          <UserMenu />
        </div>

        <Card>
          <CardContent className="py-8">
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                No manual upload data sources configured for this study. 
                Please configure a manual upload data source first.
              </AlertDescription>
            </Alert>
            <div className="mt-4">
              <Button onClick={() => router.push(`/studies/${studyId}/data-sources`)}>
                Configure Data Sources
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-6">
      <div className="flex items-center mb-6">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => router.push(`/studies/${studyId}/data-sources`)}
          className="mr-4"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Data Sources
        </Button>
        <div className="flex-1">
          <h1 className="text-3xl font-bold">Upload Data</h1>
          <p className="text-muted-foreground mt-1">
            {study?.name} - {study?.protocol_number}
          </p>
        </div>
        <UserMenu />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Upload New Data Extract</CardTitle>
          <CardDescription>
            Upload a new ZIP file containing clinical data for this study
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {manualDataSources.length > 1 && (
            <div>
              <Label htmlFor="data-source">Data Source</Label>
              <select
                id="data-source"
                className="w-full mt-2 px-3 py-2 border rounded-md"
                value={selectedDataSource}
                onChange={(e) => setSelectedDataSource(e.target.value)}
              >
                {manualDataSources.map(ds => (
                  <option key={ds.id} value={ds.id}>
                    {ds.name}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div>
            <Label htmlFor="extract-date">EDC Extract Date *</Label>
            <Input
              id="extract-date"
              placeholder="DDMMMYYYY (e.g., 05JUL2025)"
              value={extractDate}
              onChange={(e) => {
                const value = e.target.value.toUpperCase();
                if (value.length <= 9) {
                  setExtractDate(value);
                }
              }}
              pattern="[0-9]{2}[A-Z]{3}[0-9]{4}"
              required
              className="mt-2"
            />
            <p className="text-xs text-muted-foreground mt-1">
              Date when data was extracted from EDC system (format: DDMMMYYYY)
            </p>
          </div>

          <div>
            <Label htmlFor="file">Upload Data File</Label>
            <div className="mt-2">
              <Input
                id="file"
                type="file"
                accept=".zip"
                onChange={handleFileChange}
                className="cursor-pointer"
              />
              {file && (
                <div className="flex items-center gap-2 mt-2 text-sm text-muted-foreground">
                  <FileZip className="h-4 w-4" />
                  {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
                </div>
              )}
              <p className="text-xs text-muted-foreground mt-1">
                Only ZIP files are accepted. Maximum file size: 500MB
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <Switch
              id="password"
              checked={hasPassword}
              onCheckedChange={setHasPassword}
            />
            <Label htmlFor="password" className="cursor-pointer">
              ZIP file has password protection
            </Label>
          </div>

          {hasPassword && (
            <div>
              <Label>ZIP Password</Label>
              <div className="relative mt-2">
                <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  type="password"
                  placeholder="Enter ZIP password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
          )}

          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              <strong>Important:</strong> Each upload creates a new folder based on the extract date. 
              Multiple files can be uploaded for the same date if needed.
            </AlertDescription>
          </Alert>

          <div className="flex justify-end gap-4">
            <Button
              variant="outline"
              onClick={() => router.push(`/studies/${studyId}/data-sources`)}
            >
              Cancel
            </Button>
            <Button
              onClick={handleUpload}
              disabled={!file || !extractDate || isUploading}
            >
              {isUploading ? (
                <>Uploading...</>
              ) : (
                <>
                  <Upload className="mr-2 h-4 w-4" />
                  Upload File
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}