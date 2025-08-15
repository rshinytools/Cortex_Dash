// ABOUTME: Integration configuration dialog for setting up external data sources
// ABOUTME: Supports Medidata Rave, Veeva Vault, REDCap, and custom APIs

import React, { useState, useEffect } from 'react';
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Cloud,
  Database,
  Key,
  Link,
  Loader2,
  CheckCircle,
  XCircle,
  TestTube,
  Shield,
  Server
} from 'lucide-react';
import { useToast } from '@/components/ui/use-toast';

interface IntegrationConfigDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  studyId: string;
  integrationType?: string;
  onConfigComplete?: () => void;
}

const INTEGRATION_TYPES = {
  medidata_rave: {
    name: 'Medidata Rave',
    icon: Database,
    description: 'Connect to Medidata Rave EDC for clinical trial data',
    fields: [
      { key: 'base_url', label: 'API Base URL', type: 'url', required: true, placeholder: 'https://api.mdsol.com' },
      { key: 'client_id', label: 'Client ID', type: 'text', required: true },
      { key: 'client_secret', label: 'Client Secret', type: 'password', required: true },
      { key: 'study_oid', label: 'Study OID', type: 'text', required: false },
      { key: 'environment', label: 'Environment', type: 'select', options: ['production', 'uat', 'development'], required: true }
    ]
  },
  veeva_vault: {
    name: 'Veeva Vault',
    icon: Cloud,
    description: 'Connect to Veeva Vault CTMS for study documents and data',
    fields: [
      { key: 'vault_domain', label: 'Vault Domain', type: 'text', required: true, placeholder: 'myvault.veevavault.com' },
      { key: 'username', label: 'Username', type: 'text', required: true },
      { key: 'password', label: 'Password', type: 'password', required: true },
      { key: 'api_version', label: 'API Version', type: 'text', required: false, placeholder: 'v23.3' }
    ]
  },
  redcap: {
    name: 'REDCap',
    icon: Server,
    description: 'Connect to REDCap for research data capture',
    fields: [
      { key: 'api_url', label: 'API URL', type: 'url', required: true, placeholder: 'https://redcap.example.org/api/' },
      { key: 'api_token', label: 'API Token', type: 'password', required: true }
    ]
  }
};

export function IntegrationConfigDialog({
  open,
  onOpenChange,
  studyId,
  integrationType: initialType,
  onConfigComplete
}: IntegrationConfigDialogProps) {
  const [integrationType, setIntegrationType] = useState(initialType || 'medidata_rave');
  const [config, setConfig] = useState<Record<string, string>>({});
  const [testing, setTesting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);
  const { toast } = useToast();

  useEffect(() => {
    if (initialType) {
      setIntegrationType(initialType);
    }
  }, [initialType]);

  const handleConfigChange = (key: string, value: string) => {
    setConfig(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const testConnection = async () => {
    setTesting(true);
    setTestResult(null);

    try {
      const response = await fetch('/api/v1/integrations/test', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          type: integrationType,
          config: config
        })
      });

      const result = await response.json();

      if (response.ok && result.success) {
        setTestResult({
          success: true,
          message: 'Connection successful! Configuration is valid.'
        });
      } else {
        setTestResult({
          success: false,
          message: result.error || 'Connection failed. Please check your configuration.'
        });
      }
    } catch (error) {
      setTestResult({
        success: false,
        message: 'Failed to test connection. Please try again.'
      });
    } finally {
      setTesting(false);
    }
  };

  const handleSave = async () => {
    // Validate required fields
    const integration = INTEGRATION_TYPES[integrationType as keyof typeof INTEGRATION_TYPES];
    const missingFields = integration.fields
      .filter(field => field.required && !config[field.key])
      .map(field => field.label);

    if (missingFields.length > 0) {
      toast({
        title: 'Missing required fields',
        description: `Please fill in: ${missingFields.join(', ')}`,
        variant: 'destructive',
      });
      return;
    }

    setSaving(true);

    try {
      const response = await fetch('/api/v1/integrations/configure', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          study_id: studyId,
          type: integrationType,
          config: config
        })
      });

      if (response.ok) {
        toast({
          title: 'Integration configured',
          description: 'External data source has been configured successfully.',
        });

        onOpenChange(false);
        if (onConfigComplete) {
          onConfigComplete();
        }
      } else {
        throw new Error('Failed to save configuration');
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to save integration configuration.',
        variant: 'destructive',
      });
    } finally {
      setSaving(false);
    }
  };

  const renderConfigFields = () => {
    const integration = INTEGRATION_TYPES[integrationType as keyof typeof INTEGRATION_TYPES];
    if (!integration) return null;

    return integration.fields.map(field => (
      <div key={field.key} className="space-y-2">
        <Label htmlFor={field.key}>
          {field.label}
          {field.required && <span className="text-destructive ml-1">*</span>}
        </Label>
        
        {field.type === 'select' ? (
          <Select
            value={config[field.key] || ''}
            onValueChange={(value) => handleConfigChange(field.key, value)}
          >
            <SelectTrigger id={field.key}>
              <SelectValue placeholder={`Select ${field.label.toLowerCase()}`} />
            </SelectTrigger>
            <SelectContent>
              {'options' in field && field.options?.map(option => (
                <SelectItem key={option} value={option}>
                  {option}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        ) : (
          <Input
            id={field.key}
            type={field.type}
            value={config[field.key] || ''}
            onChange={(e) => handleConfigChange(field.key, e.target.value)}
            placeholder={field.placeholder}
          />
        )}
      </div>
    ));
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Configure Integration</DialogTitle>
          <DialogDescription>
            Set up connection to external clinical data systems
          </DialogDescription>
        </DialogHeader>

        <Tabs value={integrationType} onValueChange={setIntegrationType}>
          <TabsList className="grid w-full grid-cols-3">
            {Object.entries(INTEGRATION_TYPES).map(([key, integration]) => {
              const Icon = integration.icon;
              return (
                <TabsTrigger key={key} value={key} className="flex items-center gap-2">
                  <Icon className="h-4 w-4" />
                  {integration.name}
                </TabsTrigger>
              );
            })}
          </TabsList>

          {Object.entries(INTEGRATION_TYPES).map(([key, integration]) => {
            const Icon = integration.icon;
            return (
              <TabsContent key={key} value={key} className="space-y-4">
                <Alert>
                  <Icon className="h-4 w-4" />
                  <AlertDescription>
                    {integration.description}
                  </AlertDescription>
                </Alert>

                <div className="space-y-4">
                  {renderConfigFields()}
                </div>

                {/* Connection Test Section */}
                <div className="border rounded-lg p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <Label>Connection Test</Label>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={testConnection}
                      disabled={testing}
                    >
                      {testing ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Testing...
                        </>
                      ) : (
                        <>
                          <TestTube className="mr-2 h-4 w-4" />
                          Test Connection
                        </>
                      )}
                    </Button>
                  </div>

                  {testResult && (
                    <Alert variant={testResult.success ? 'default' : 'destructive'}>
                      {testResult.success ? (
                        <CheckCircle className="h-4 w-4" />
                      ) : (
                        <XCircle className="h-4 w-4" />
                      )}
                      <AlertDescription>
                        {testResult.message}
                      </AlertDescription>
                    </Alert>
                  )}
                </div>

                {/* Security Note */}
                <Alert>
                  <Shield className="h-4 w-4" />
                  <AlertDescription>
                    <strong>Security:</strong> All credentials are encrypted and stored securely. 
                    API tokens and passwords are never exposed in logs or UI.
                  </AlertDescription>
                </Alert>
              </TabsContent>
            );
          })}
        </Tabs>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={saving}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSave}
            disabled={saving || !testResult?.success}
          >
            {saving ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Link className="mr-2 h-4 w-4" />
                Save Configuration
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}