// ABOUTME: Email settings management page for configuring SMTP and testing connections
// ABOUTME: Provides UI for database-driven email configuration with encryption support

'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { useToast } from '@/components/ui/use-toast';
import { 
  Loader2, Mail, Settings, Send, CheckCircle2, XCircle, 
  AlertCircle, Save, TestTube2, ChevronLeft, FileText, 
  Clock, History 
} from 'lucide-react';
import { AuthGuard } from '@/components/auth-guard';
import { EmailNav } from '@/components/email/email-nav';
import { emailApi, type EmailSettings } from '@/lib/api/email';

export default function EmailSettingsPage() {
  const router = useRouter();
  const [settings, setSettings] = useState<EmailSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testEmail, setTestEmail] = useState('');
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);
  const { toast } = useToast();

  // Form state
  const [formData, setFormData] = useState({
    smtp_host: '',
    smtp_port: 587,
    smtp_username: '',
    smtp_password: '',
    smtp_from_email: '',
    smtp_from_name: '',
    smtp_use_tls: true,
    smtp_use_ssl: false,
    smtp_timeout: 30,
    is_active: true,
    test_recipient_email: '',
    max_retries: 3,
    retry_delay: 300,
  });

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      const data = await emailApi.settings.getSettings();
      if (data) {
        setSettings(data);
        setFormData({
          smtp_host: data.smtp_host || '',
          smtp_port: data.smtp_port || 587,
          smtp_username: data.smtp_username || '',
          smtp_password: '', // Don't populate password
          smtp_from_email: data.smtp_from_email || '',
          smtp_from_name: data.smtp_from_name || '',
          smtp_use_tls: data.smtp_use_tls ?? true,
          smtp_use_ssl: data.smtp_use_ssl ?? false,
          smtp_timeout: data.smtp_timeout || 30,
          is_active: data.is_active ?? true,
          test_recipient_email: data.test_recipient_email || '',
          max_retries: data.max_retries || 3,
          retry_delay: data.retry_delay || 300,
        });
      }
    } catch (error) {
      console.error('Failed to load email settings:', error);
      toast({
        title: 'Error',
        description: 'Failed to load email settings',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      
      // Validate required fields
      if (!formData.smtp_host || !formData.smtp_from_email) {
        toast({
          title: 'Validation Error',
          description: 'SMTP host and from email are required',
          variant: 'destructive',
        });
        return;
      }

      const dataToSave: any = {
        ...formData,
      };
      
      // Only exclude password if it's explicitly empty (not changed)
      if (!formData.smtp_password && settings) {
        delete dataToSave.smtp_password;
      }

      if (settings) {
        // Update existing settings
        await emailApi.settings.updateSettings(settings.id, dataToSave);
        toast({
          title: 'Success',
          description: 'Email settings updated successfully',
        });
      } else {
        // Create new settings
        const newSettings = await emailApi.settings.createSettings(dataToSave);
        setSettings(newSettings);
        toast({
          title: 'Success',
          description: 'Email settings created successfully',
        });
      }

      await loadSettings();
    } catch (error) {
      console.error('Failed to save email settings:', error);
      toast({
        title: 'Error',
        description: 'Failed to save email settings',
        variant: 'destructive',
      });
    } finally {
      setSaving(false);
    }
  };

  const handleTestConnection = async () => {
    if (!testEmail) {
      toast({
        title: 'Validation Error',
        description: 'Please enter a test email address',
        variant: 'destructive',
      });
      return;
    }

    try {
      setTesting(true);
      setTestResult(null);
      
      const result = await emailApi.settings.testConnection({
        to_email: testEmail,
        test_connection: true,
      });

      setTestResult({
        success: result.success,
        message: result.message || result.error || 'Test completed',
      });

      if (result.success) {
        toast({
          title: 'Success',
          description: 'Email test successful! Check your inbox.',
        });
      } else {
        toast({
          title: 'Test Failed',
          description: result.error || 'Failed to send test email',
          variant: 'destructive',
        });
      }
    } catch (error: any) {
      console.error('Failed to test email:', error);
      setTestResult({
        success: false,
        message: error.message || 'Failed to test email connection',
      });
      toast({
        title: 'Error',
        description: 'Failed to test email connection',
        variant: 'destructive',
      });
    } finally {
      setTesting(false);
    }
  };

  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));
  };

  if (loading) {
    return (
      <AuthGuard>
        <div className="flex items-center justify-center h-96">
          <Loader2 className="h-8 w-8 animate-spin" />
        </div>
      </AuthGuard>
    );
  }

  return (
    <AuthGuard>
      <div className="container mx-auto py-6 space-y-6">
        {/* Navigation */}
        <div>
          <Button
            variant="ghost"
            onClick={() => router.push('/admin')}
            className="mb-4"
          >
            <ChevronLeft className="mr-2 h-4 w-4" />
            Back to Admin Dashboard
          </Button>
        </div>

        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <Mail className="h-8 w-8" />
            Email Management
          </h1>
          <p className="text-muted-foreground">
            Configure email settings, templates, and monitor delivery
          </p>
        </div>

        {/* Tab Navigation */}
        <EmailNav />

        <Tabs defaultValue="configuration" className="space-y-4">
          <TabsList>
            <TabsTrigger value="configuration">
              <Settings className="h-4 w-4 mr-2" />
              Configuration
            </TabsTrigger>
            <TabsTrigger value="testing">
              <TestTube2 className="h-4 w-4 mr-2" />
              Testing
            </TabsTrigger>
          </TabsList>

          <TabsContent value="configuration" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>SMTP Configuration</CardTitle>
                <CardDescription>
                  Configure your SMTP server settings for sending emails
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="smtp_host">SMTP Host *</Label>
                    <Input
                      id="smtp_host"
                      value={formData.smtp_host}
                      onChange={(e) => handleInputChange('smtp_host', e.target.value)}
                      placeholder="smtp.example.com"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="smtp_port">SMTP Port *</Label>
                    <Input
                      id="smtp_port"
                      type="number"
                      value={formData.smtp_port}
                      onChange={(e) => handleInputChange('smtp_port', parseInt(e.target.value))}
                      placeholder="587"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="smtp_username">Username</Label>
                    <Input
                      id="smtp_username"
                      value={formData.smtp_username}
                      onChange={(e) => handleInputChange('smtp_username', e.target.value)}
                      placeholder="Optional"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="smtp_password">Password</Label>
                    <Input
                      id="smtp_password"
                      type="password"
                      value={formData.smtp_password}
                      onChange={(e) => handleInputChange('smtp_password', e.target.value)}
                      placeholder={settings ? '••••••••' : 'Optional'}
                    />
                    {settings && (
                      <p className="text-xs text-muted-foreground">
                        Leave blank to keep existing password
                      </p>
                    )}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="smtp_from_email">From Email *</Label>
                    <Input
                      id="smtp_from_email"
                      type="email"
                      value={formData.smtp_from_email}
                      onChange={(e) => handleInputChange('smtp_from_email', e.target.value)}
                      placeholder="noreply@example.com"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="smtp_from_name">From Name</Label>
                    <Input
                      id="smtp_from_name"
                      value={formData.smtp_from_name}
                      onChange={(e) => handleInputChange('smtp_from_name', e.target.value)}
                      placeholder="Clinical Dashboard"
                    />
                  </div>
                </div>

                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <Label htmlFor="smtp_use_tls">Use TLS</Label>
                      <p className="text-sm text-muted-foreground">
                        Enable TLS encryption (recommended for port 587)
                      </p>
                    </div>
                    <Switch
                      id="smtp_use_tls"
                      checked={formData.smtp_use_tls}
                      onCheckedChange={(checked) => handleInputChange('smtp_use_tls', checked)}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <Label htmlFor="smtp_use_ssl">Use SSL</Label>
                      <p className="text-sm text-muted-foreground">
                        Enable SSL encryption (typically for port 465)
                      </p>
                    </div>
                    <Switch
                      id="smtp_use_ssl"
                      checked={formData.smtp_use_ssl}
                      onCheckedChange={(checked) => handleInputChange('smtp_use_ssl', checked)}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <Label htmlFor="is_active">Active</Label>
                      <p className="text-sm text-muted-foreground">
                        Enable or disable email sending
                      </p>
                    </div>
                    <Switch
                      id="is_active"
                      checked={formData.is_active}
                      onCheckedChange={(checked) => handleInputChange('is_active', checked)}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="smtp_timeout">Timeout (seconds)</Label>
                    <Input
                      id="smtp_timeout"
                      type="number"
                      value={formData.smtp_timeout}
                      onChange={(e) => handleInputChange('smtp_timeout', parseInt(e.target.value))}
                      placeholder="30"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="max_retries">Max Retries</Label>
                    <Input
                      id="max_retries"
                      type="number"
                      value={formData.max_retries}
                      onChange={(e) => handleInputChange('max_retries', parseInt(e.target.value))}
                      placeholder="3"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="retry_delay">Retry Delay (seconds)</Label>
                    <Input
                      id="retry_delay"
                      type="number"
                      value={formData.retry_delay}
                      onChange={(e) => handleInputChange('retry_delay', parseInt(e.target.value))}
                      placeholder="300"
                    />
                  </div>
                </div>

                <div className="flex justify-end">
                  <Button onClick={handleSave} disabled={saving}>
                    {saving ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Saving...
                      </>
                    ) : (
                      <>
                        <Save className="mr-2 h-4 w-4" />
                        Save Settings
                      </>
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="testing" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Test Email Connection</CardTitle>
                <CardDescription>
                  Send a test email to verify your SMTP configuration
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {!settings ? (
                  <Alert>
                    <AlertCircle className="h-4 w-4" />
                    <AlertTitle>No Configuration</AlertTitle>
                    <AlertDescription>
                      Please configure and save your SMTP settings first
                    </AlertDescription>
                  </Alert>
                ) : !formData.is_active ? (
                  <Alert>
                    <AlertCircle className="h-4 w-4" />
                    <AlertTitle>Email Disabled</AlertTitle>
                    <AlertDescription>
                      Email sending is currently disabled. Enable it in the configuration tab.
                    </AlertDescription>
                  </Alert>
                ) : (
                  <>
                    <div className="space-y-2">
                      <Label htmlFor="test_email">Test Email Address</Label>
                      <Input
                        id="test_email"
                        type="email"
                        value={testEmail}
                        onChange={(e) => setTestEmail(e.target.value)}
                        placeholder="test@example.com"
                      />
                      <p className="text-sm text-muted-foreground">
                        Enter an email address to send a test message
                      </p>
                    </div>

                    <Button 
                      onClick={handleTestConnection} 
                      disabled={testing || !testEmail}
                      className="w-full"
                    >
                      {testing ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Sending Test Email...
                        </>
                      ) : (
                        <>
                          <Send className="mr-2 h-4 w-4" />
                          Send Test Email
                        </>
                      )}
                    </Button>

                    {testResult && (
                      <Alert className={testResult.success ? 'border-green-500' : 'border-red-500'}>
                        {testResult.success ? (
                          <CheckCircle2 className="h-4 w-4 text-green-500" />
                        ) : (
                          <XCircle className="h-4 w-4 text-red-500" />
                        )}
                        <AlertTitle>
                          {testResult.success ? 'Test Successful' : 'Test Failed'}
                        </AlertTitle>
                        <AlertDescription>{testResult.message}</AlertDescription>
                      </Alert>
                    )}
                  </>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Current Configuration</CardTitle>
                <CardDescription>
                  Active SMTP settings overview
                </CardDescription>
              </CardHeader>
              <CardContent>
                {settings ? (
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="font-medium">Host:</span>
                      <span>{settings.smtp_host}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="font-medium">Port:</span>
                      <span>{settings.smtp_port}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="font-medium">From:</span>
                      <span>{settings.smtp_from_email}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="font-medium">Encryption:</span>
                      <span>
                        {settings.smtp_use_tls ? 'TLS' : settings.smtp_use_ssl ? 'SSL' : 'None'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="font-medium">Authentication:</span>
                      <span>{settings.smtp_username ? 'Yes' : 'No'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="font-medium">Status:</span>
                      <span className={settings.is_active ? 'text-green-600' : 'text-red-600'}>
                        {settings.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </div>
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">No configuration found</p>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </AuthGuard>
  );
}