// ABOUTME: Email templates management page for creating and editing email templates
// ABOUTME: Provides template editor with live preview and variable support

'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Textarea } from '@/components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { useToast } from '@/components/ui/use-toast';
import { 
  Loader2, FileText, Plus, Edit2, Trash2, Eye, Save, X, 
  AlertCircle, Code, FileCode, Check, Copy, ChevronLeft,
  Mail, Clock, History, Settings
} from 'lucide-react';
import { AuthGuard } from '@/components/auth-guard';
import { EmailNav } from '@/components/email/email-nav';
import { emailApi, type EmailTemplate } from '@/lib/api/email';

export default function EmailTemplatesPage() {
  const router = useRouter();
  const [templates, setTemplates] = useState<EmailTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTemplate, setSelectedTemplate] = useState<EmailTemplate | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [previewing, setPreviewing] = useState(false);
  const [previewContent, setPreviewContent] = useState<{ html: string; plain: string; subject: string } | null>(null);
  const { toast } = useToast();

  // Form state
  const [formData, setFormData] = useState({
    key: '',
    name: '',
    subject: '',
    html_body: '',
    plain_body: '',
    variables: {} as Record<string, any>,
    is_active: true,
  });

  // Sample variables for preview
  const [previewVariables, setPreviewVariables] = useState<Record<string, any>>({});

  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    try {
      setLoading(true);
      const data = await emailApi.templates.listTemplates();
      setTemplates(data);
    } catch (error) {
      console.error('Failed to load templates:', error);
      toast({
        title: 'Error',
        description: 'Failed to load email templates',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSelectTemplate = (template: EmailTemplate) => {
    setSelectedTemplate(template);
    setFormData({
      key: template.key,
      name: template.name,
      subject: template.subject,
      html_body: template.html_body,
      plain_body: template.plain_body || '',
      variables: template.variables || {},
      is_active: template.is_active,
    });
    setPreviewVariables(template.variables || {});
    setIsEditing(false);
    setIsCreating(false);
  };

  const handleCreateNew = () => {
    setSelectedTemplate(null);
    setFormData({
      key: '',
      name: '',
      subject: '',
      html_body: '',
      plain_body: '',
      variables: {},
      is_active: true,
    });
    setPreviewVariables({});
    setIsCreating(true);
    setIsEditing(true);
  };

  const handleSave = async () => {
    try {
      setSaving(true);

      // Validate required fields
      if (!formData.key || !formData.name || !formData.subject || !formData.html_body) {
        toast({
          title: 'Validation Error',
          description: 'Please fill in all required fields',
          variant: 'destructive',
        });
        return;
      }

      if (isCreating) {
        // Create new template
        const newTemplate = await emailApi.templates.createTemplate(formData);
        toast({
          title: 'Success',
          description: 'Template created successfully',
        });
        await loadTemplates();
        handleSelectTemplate(newTemplate);
      } else if (selectedTemplate) {
        // Update existing template
        const updatedTemplate = await emailApi.templates.updateTemplate(
          selectedTemplate.id,
          formData
        );
        toast({
          title: 'Success',
          description: 'Template updated successfully',
        });
        await loadTemplates();
        handleSelectTemplate(updatedTemplate);
      }
    } catch (error: any) {
      console.error('Failed to save template:', error);
      toast({
        title: 'Error',
        description: error.message || 'Failed to save template',
        variant: 'destructive',
      });
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!selectedTemplate) return;

    try {
      setDeleting(true);
      await emailApi.templates.deleteTemplate(selectedTemplate.id);
      toast({
        title: 'Success',
        description: 'Template deleted successfully',
      });
      setSelectedTemplate(null);
      await loadTemplates();
    } catch (error) {
      console.error('Failed to delete template:', error);
      toast({
        title: 'Error',
        description: 'Failed to delete template',
        variant: 'destructive',
      });
    } finally {
      setDeleting(false);
    }
  };

  const handlePreview = async () => {
    if (!selectedTemplate) return;

    try {
      setPreviewing(true);
      const preview = await emailApi.templates.previewTemplate(
        selectedTemplate.id,
        previewVariables
      );
      setPreviewContent(preview);
    } catch (error) {
      console.error('Failed to preview template:', error);
      toast({
        title: 'Error',
        description: 'Failed to preview template',
        variant: 'destructive',
      });
    } finally {
      setPreviewing(false);
    }
  };

  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleVariableChange = (key: string, value: string) => {
    setPreviewVariables(prev => ({
      ...prev,
      [key]: value,
    }));
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast({
      title: 'Copied',
      description: 'Variable copied to clipboard',
    });
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
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
              <Mail className="h-8 w-8" />
              Email Management
            </h1>
            <p className="text-muted-foreground">
              Configure email settings, templates, and monitor delivery
            </p>
          </div>
          
          <Button onClick={handleCreateNew} size="sm">
            <Plus className="h-4 w-4 mr-2" />
            New Template
          </Button>
        </div>

        {/* Tab Navigation */}
        <EmailNav />

        <div className="grid grid-cols-12 gap-6">
          {/* Templates List */}
          <div className="col-span-4">
            <Card>
              <CardHeader>
                <CardTitle>Templates</CardTitle>
                <CardDescription>
                  Select a template to view or edit
                </CardDescription>
              </CardHeader>
              <CardContent className="p-0">
                <div className="divide-y">
                  {templates.length === 0 ? (
                    <div className="p-6 text-center text-muted-foreground">
                      No templates found
                    </div>
                  ) : (
                    templates.map((template) => (
                      <div
                        key={template.id}
                        className={`p-4 cursor-pointer hover:bg-muted/50 transition-colors ${
                          selectedTemplate?.id === template.id ? 'bg-muted' : ''
                        }`}
                        onClick={() => handleSelectTemplate(template)}
                      >
                        <div className="flex justify-between items-start">
                          <div className="space-y-1">
                            <p className="font-medium">{template.name}</p>
                            <p className="text-sm text-muted-foreground">
                              {template.key}
                            </p>
                          </div>
                          <div className="flex items-center gap-2">
                            {template.is_active ? (
                              <Check className="h-4 w-4 text-green-500" />
                            ) : (
                              <X className="h-4 w-4 text-red-500" />
                            )}
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Template Editor */}
          <div className="col-span-8">
            {selectedTemplate || isCreating ? (
              <Card>
                <CardHeader>
                  <div className="flex justify-between items-center">
                    <CardTitle>
                      {isCreating ? 'New Template' : selectedTemplate?.name}
                    </CardTitle>
                    <div className="flex gap-2">
                      {!isCreating && !isEditing && (
                        <>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setIsEditing(true)}
                          >
                            <Edit2 className="h-4 w-4 mr-2" />
                            Edit
                          </Button>
                          <Dialog>
                            <DialogTrigger asChild>
                              <Button
                                variant="outline"
                                size="sm"
                                className="text-red-600 hover:text-red-700"
                              >
                                <Trash2 className="h-4 w-4 mr-2" />
                                Delete
                              </Button>
                            </DialogTrigger>
                            <DialogContent>
                              <DialogHeader>
                                <DialogTitle>Delete Template</DialogTitle>
                                <DialogDescription>
                                  Are you sure you want to delete this template? This action cannot be undone.
                                </DialogDescription>
                              </DialogHeader>
                              <DialogFooter>
                                <Button variant="outline" onClick={() => {}}>
                                  Cancel
                                </Button>
                                <Button
                                  variant="destructive"
                                  onClick={handleDelete}
                                  disabled={deleting}
                                >
                                  {deleting ? (
                                    <>
                                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                      Deleting...
                                    </>
                                  ) : (
                                    'Delete'
                                  )}
                                </Button>
                              </DialogFooter>
                            </DialogContent>
                          </Dialog>
                        </>
                      )}
                      {isEditing && (
                        <>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              setIsEditing(false);
                              setIsCreating(false);
                              if (selectedTemplate) {
                                handleSelectTemplate(selectedTemplate);
                              }
                            }}
                          >
                            <X className="h-4 w-4 mr-2" />
                            Cancel
                          </Button>
                          <Button
                            size="sm"
                            onClick={handleSave}
                            disabled={saving}
                          >
                            {saving ? (
                              <>
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                Saving...
                              </>
                            ) : (
                              <>
                                <Save className="h-4 w-4 mr-2" />
                                Save
                              </>
                            )}
                          </Button>
                        </>
                      )}
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <Tabs defaultValue="editor" className="space-y-4">
                    <TabsList className="grid w-full grid-cols-3">
                      <TabsTrigger value="editor">Editor</TabsTrigger>
                      <TabsTrigger value="variables">Variables</TabsTrigger>
                      <TabsTrigger value="preview" disabled={isCreating}>
                        Preview
                      </TabsTrigger>
                    </TabsList>

                    <TabsContent value="editor" className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label htmlFor="key">Template Key *</Label>
                          <Input
                            id="key"
                            value={formData.key}
                            onChange={(e) => handleInputChange('key', e.target.value)}
                            disabled={!isEditing}
                            placeholder="user_created"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="name">Template Name *</Label>
                          <Input
                            id="name"
                            value={formData.name}
                            onChange={(e) => handleInputChange('name', e.target.value)}
                            disabled={!isEditing}
                            placeholder="User Created"
                          />
                        </div>
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="subject">Email Subject *</Label>
                        <Input
                          id="subject"
                          value={formData.subject}
                          onChange={(e) => handleInputChange('subject', e.target.value)}
                          disabled={!isEditing}
                          placeholder="Welcome to {{ app_name }}!"
                        />
                        <p className="text-xs text-muted-foreground">
                          Use {'{{ variable_name }}'} for dynamic content
                        </p>
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="html_body">HTML Template *</Label>
                        <Textarea
                          id="html_body"
                          value={formData.html_body}
                          onChange={(e) => handleInputChange('html_body', e.target.value)}
                          disabled={!isEditing}
                          rows={10}
                          className="font-mono text-sm"
                          placeholder={`<!DOCTYPE html>
<html>
<body>
  <h1>Welcome {{ user_name }}!</h1>
  <p>Your account has been created.</p>
</body>
</html>`}
                        />
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="plain_body">Plain Text Template</Label>
                        <Textarea
                          id="plain_body"
                          value={formData.plain_body}
                          onChange={(e) => handleInputChange('plain_body', e.target.value)}
                          disabled={!isEditing}
                          rows={6}
                          className="font-mono text-sm"
                          placeholder={`Welcome {{ user_name }}!

Your account has been created.`}
                        />
                      </div>

                      <div className="flex items-center justify-between">
                        <div>
                          <Label htmlFor="is_active">Active</Label>
                          <p className="text-sm text-muted-foreground">
                            Enable or disable this template
                          </p>
                        </div>
                        <Switch
                          id="is_active"
                          checked={formData.is_active}
                          onCheckedChange={(checked) => handleInputChange('is_active', checked)}
                          disabled={!isEditing}
                        />
                      </div>
                    </TabsContent>

                    <TabsContent value="variables" className="space-y-4">
                      <Alert>
                        <Code className="h-4 w-4" />
                        <AlertDescription>
                          Variables can be used in templates with {'{{ variable_name }}'} syntax.
                          Click on a variable to copy it to clipboard.
                        </AlertDescription>
                      </Alert>

                      <div className="space-y-2">
                        <Label>Common Variables</Label>
                        <div className="grid grid-cols-2 gap-2">
                          {[
                            'user_name',
                            'user_email',
                            'app_name',
                            'app_url',
                            'current_date',
                            'current_time',
                          ].map((variable) => (
                            <Button
                              key={variable}
                              variant="outline"
                              size="sm"
                              className="justify-start"
                              onClick={() => copyToClipboard(`{{ ${variable} }}`)}
                            >
                              <Copy className="h-3 w-3 mr-2" />
                              {`{{ ${variable} }}`}
                            </Button>
                          ))}
                        </div>
                      </div>

                      {selectedTemplate && Object.keys(formData.variables).length > 0 && (
                        <div className="space-y-2">
                          <Label>Template Variables</Label>
                          <div className="grid grid-cols-2 gap-2">
                            {Object.keys(formData.variables).map((variable) => (
                              <Button
                                key={variable}
                                variant="outline"
                                size="sm"
                                className="justify-start"
                                onClick={() => copyToClipboard(`{{ ${variable} }}`)}
                              >
                                <Copy className="h-3 w-3 mr-2" />
                                {`{{ ${variable} }}`}
                              </Button>
                            ))}
                          </div>
                        </div>
                      )}
                    </TabsContent>

                    <TabsContent value="preview" className="space-y-4">
                      {selectedTemplate && (
                        <>
                          <div className="space-y-4">
                            <Label>Preview Variables</Label>
                            {Object.keys(formData.variables).length > 0 ? (
                              <div className="grid grid-cols-2 gap-4">
                                {Object.keys(formData.variables).map((key) => (
                                  <div key={key} className="space-y-2">
                                    <Label htmlFor={`var-${key}`}>{key}</Label>
                                    <Input
                                      id={`var-${key}`}
                                      value={previewVariables[key] || ''}
                                      onChange={(e) => handleVariableChange(key, e.target.value)}
                                      placeholder={`Enter ${key}`}
                                    />
                                  </div>
                                ))}
                              </div>
                            ) : (
                              <p className="text-sm text-muted-foreground">
                                No variables defined for this template
                              </p>
                            )}

                            <Button
                              onClick={handlePreview}
                              disabled={previewing}
                              className="w-full"
                            >
                              {previewing ? (
                                <>
                                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                  Generating Preview...
                                </>
                              ) : (
                                <>
                                  <Eye className="mr-2 h-4 w-4" />
                                  Generate Preview
                                </>
                              )}
                            </Button>
                          </div>

                          {previewContent && (
                            <div className="space-y-4">
                              <div className="space-y-2">
                                <Label>Subject</Label>
                                <div className="p-3 border rounded-md bg-muted/50">
                                  {previewContent.subject}
                                </div>
                              </div>

                              <Tabs defaultValue="html" className="w-full">
                                <TabsList className="grid w-full grid-cols-2">
                                  <TabsTrigger value="html">HTML</TabsTrigger>
                                  <TabsTrigger value="plain">Plain Text</TabsTrigger>
                                </TabsList>
                                <TabsContent value="html">
                                  <div className="border rounded-md p-4 bg-white h-96 overflow-auto">
                                    <div dangerouslySetInnerHTML={{ __html: previewContent.html }} />
                                  </div>
                                </TabsContent>
                                <TabsContent value="plain">
                                  <div className="border rounded-md p-4 bg-muted/50 h-96 overflow-auto">
                                    <pre className="whitespace-pre-wrap text-sm">
                                      {previewContent.plain}
                                    </pre>
                                  </div>
                                </TabsContent>
                              </Tabs>
                            </div>
                          )}
                        </>
                      )}
                    </TabsContent>
                  </Tabs>
                </CardContent>
              </Card>
            ) : (
              <Card>
                <CardContent className="flex flex-col items-center justify-center h-96 text-center">
                  <FileCode className="h-12 w-12 text-muted-foreground mb-4" />
                  <p className="text-lg font-medium">Select a template</p>
                  <p className="text-sm text-muted-foreground">
                    Choose a template from the list to view or edit
                  </p>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </AuthGuard>
  );
}