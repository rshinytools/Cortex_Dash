// ABOUTME: Data source configuration step in study initialization wizard
// ABOUTME: Allows configuring data sources specific to the study

'use client';

import { useState, useEffect, useRef } from 'react';
import { Plus, Trash2, TestTube, Upload, Lock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';
import { dataSourcesApi, DataSourceType } from '@/lib/api/data-sources';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';

interface DataSourceStepProps {
  studyId: string;
  data: any;
  onDataChange: (data: any) => void;
}

export function DataSourceStep({ studyId, data, onDataChange }: DataSourceStepProps) {
  const { toast } = useToast();
  const [dataSources, setDataSources] = useState(data.dataSources || []);
  const [isAddingNew, setIsAddingNew] = useState(false);

  useEffect(() => {
    onDataChange({ dataSources });
  }, [dataSources]);

  const addDataSource = () => {
    const newSource = {
      id: `temp-${Date.now()}`,
      name: '',
      type: DataSourceType.MEDIDATA_API,
      config: {},
      isNew: true,
    };
    setDataSources([...dataSources, newSource]);
    setIsAddingNew(true);
  };

  const updateDataSource = (index: number, updates: any) => {
    const updated = [...dataSources];
    updated[index] = { ...updated[index], ...updates };
    setDataSources(updated);
  };

  const removeDataSource = (index: number) => {
    setDataSources(dataSources.filter((_: any, i: number) => i !== index));
  };

  const testConnection = async (index: number) => {
    const source = dataSources[index];
    try {
      const result = await dataSourcesApi.testConnection(source.config, source.type);
      toast({
        title: result.success ? 'Connection successful' : 'Connection failed',
        description: result.message,
        variant: result.success ? 'default' : 'destructive',
      });
    } catch (error) {
      toast({
        title: 'Test failed',
        description: 'Failed to test connection',
        variant: 'destructive',
      });
    }
  };

  const renderConfigFields = (source: any, index: number) => {
    switch (source.type) {
      case DataSourceType.MEDIDATA_API:
        return (
          <>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>API Base URL</Label>
                <Input
                  placeholder="https://api.mdsol.com"
                  value={source.config.base_url || ''}
                  onChange={(e) => updateDataSource(index, {
                    config: { ...source.config, base_url: e.target.value }
                  })}
                />
              </div>
              <div>
                <Label>Study OID</Label>
                <Input
                  placeholder="STUDY001"
                  value={source.config.study_oid || ''}
                  onChange={(e) => updateDataSource(index, {
                    config: { ...source.config, study_oid: e.target.value }
                  })}
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Username</Label>
                <Input
                  placeholder="api_user"
                  value={source.config.username || ''}
                  onChange={(e) => updateDataSource(index, {
                    config: { ...source.config, username: e.target.value }
                  })}
                />
              </div>
              <div>
                <Label>Password</Label>
                <Input
                  type="password"
                  value={source.config.password || ''}
                  onChange={(e) => updateDataSource(index, {
                    config: { ...source.config, password: e.target.value }
                  })}
                />
              </div>
            </div>
          </>
        );
      
      case DataSourceType.ZIP_UPLOAD:
        return (
          <div className="space-y-4">
            <div>
              <Label htmlFor={`extract-date-${index}`}>EDC Extract Date *</Label>
              <Input
                id={`extract-date-${index}`}
                placeholder="DDMMMYYYY (e.g., 05JUL2025)"
                value={source.config.extractDate || ''}
                onChange={(e) => {
                  const value = e.target.value.toUpperCase();
                  // Basic validation for DDMMMYYYY format
                  if (value.length <= 9) {
                    updateDataSource(index, {
                      config: { ...source.config, extractDate: value }
                    });
                  }
                }}
                pattern="[0-9]{2}[A-Z]{3}[0-9]{4}"
                required
              />
              <p className="text-xs text-muted-foreground mt-1">
                Date when data was extracted from EDC system (format: DDMMMYYYY)
              </p>
            </div>
            
            <div>
              <Label htmlFor={`file-${index}`}>Upload Data File</Label>
              <div className="mt-2">
                <Input
                  id={`file-${index}`}
                  type="file"
                  accept=".zip"
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) {
                      updateDataSource(index, {
                        config: { ...source.config, file, fileName: file.name }
                      });
                    }
                  }}
                  className="cursor-pointer"
                />
                {source.config.fileName && (
                  <p className="text-sm text-muted-foreground mt-2">
                    Selected file: {source.config.fileName}
                  </p>
                )}
                <p className="text-xs text-muted-foreground mt-1">
                  Only ZIP files are accepted. Maximum file size: 500MB
                </p>
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              <Switch
                id={`password-${index}`}
                checked={source.config.hasPassword || false}
                onCheckedChange={(checked) => {
                  updateDataSource(index, {
                    config: { ...source.config, hasPassword: checked, password: checked ? source.config.password : '' }
                  });
                }}
              />
              <Label htmlFor={`password-${index}`} className="cursor-pointer">
                ZIP file has password protection
              </Label>
            </div>
            
            {source.config.hasPassword && (
              <div>
                <Label>ZIP Password</Label>
                <Input
                  type="password"
                  placeholder="Enter ZIP password"
                  value={source.config.password || ''}
                  onChange={(e) => updateDataSource(index, {
                    config: { ...source.config, password: e.target.value }
                  })}
                />
              </div>
            )}
            
            <div className="p-4 bg-muted rounded-lg">
              <p className="text-sm text-muted-foreground">
                <strong>Note:</strong> Manual upload does not support automatic synchronization. 
                Files must be uploaded manually through the interface when new data is available.
              </p>
            </div>
          </div>
        );
      
      default:
        return (
          <p className="text-sm text-muted-foreground">
            Configuration for this data source type coming soon.
          </p>
        );
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center mb-4">
        <div>
          <p className="text-sm text-muted-foreground">
            Configure how data will be imported into this study.
          </p>
          <p className="text-sm text-yellow-600 mt-1">
            <strong>Note:</strong> Once configured, the data source type cannot be changed.
          </p>
        </div>
        {dataSources.length === 0 && (
          <Button onClick={addDataSource} size="sm">
            <Plus className="mr-2 h-4 w-4" />
            Add Data Source
          </Button>
        )}
      </div>

      {dataSources.length === 0 ? (
        <Card>
          <CardContent className="py-8 text-center">
            <p className="text-muted-foreground mb-4">
              No data sources configured yet. Add your first data source to get started.
            </p>
            <Button onClick={addDataSource}>
              <Plus className="mr-2 h-4 w-4" />
              Add First Data Source
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {dataSources.map((source: any, index: number) => (
            <Card key={source.id}>
              <CardContent className="pt-6">
                <div className="flex justify-between items-start mb-4">
                  <div className="flex-1 grid grid-cols-2 gap-4">
                    <div>
                      <Label>Data Source Name</Label>
                      <Input
                        placeholder="e.g., Primary EDC System"
                        value={source.name}
                        onChange={(e) => updateDataSource(index, { name: e.target.value })}
                      />
                    </div>
                    <div>
                      <Label>Type</Label>
                      <Select
                        value={source.type}
                        onValueChange={(value) => updateDataSource(index, { type: value })}
                        disabled={!source.isNew}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value={DataSourceType.MEDIDATA_API}>Medidata Rave API</SelectItem>
                          <SelectItem value={DataSourceType.ZIP_UPLOAD}>Manual ZIP Upload</SelectItem>
                          <SelectItem value={DataSourceType.SFTP}>SFTP Server</SelectItem>
                        </SelectContent>
                      </Select>
                      {!source.isNew && (
                        <p className="text-xs text-muted-foreground mt-1">
                          Data source type cannot be changed after creation
                        </p>
                      )}
                    </div>
                  </div>
                  <div className="flex gap-2 ml-4">
                    {source.type !== DataSourceType.ZIP_UPLOAD && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => testConnection(index)}
                        title="Test Connection"
                      >
                        <TestTube className="h-4 w-4" />
                      </Button>
                    )}
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => removeDataSource(index)}
                      title="Remove Data Source"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
                
                <div className="space-y-4">
                  {renderConfigFields(source, index)}
                </div>
                
                {source.type !== DataSourceType.ZIP_UPLOAD && (
                  <div className="mt-4">
                    <Label>Sync Schedule (optional)</Label>
                    <Input
                      placeholder="0 0 * * * (daily at midnight)"
                      value={source.config.sync_schedule || ''}
                      onChange={(e) => updateDataSource(index, {
                        config: { ...source.config, sync_schedule: e.target.value }
                      })}
                    />
                    <p className="text-xs text-muted-foreground mt-1">
                      Cron expression for automatic sync. Leave empty for manual sync only.
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}