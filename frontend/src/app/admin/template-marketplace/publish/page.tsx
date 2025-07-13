// ABOUTME: Template publishing page for uploading and publishing templates to the marketplace
// ABOUTME: Currently disabled - redirects to disabled page

'use client';

import MarketplaceDisabled from '../disabled';

export default function PublishTemplatePage() {
  return <MarketplaceDisabled />;
}

/* Original implementation preserved below for future use
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Upload, X, Plus, AlertCircle, CheckCircle, FileText, Image, Tag, Globe } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { useToast } from '@/hooks/use-toast';

interface TemplateMetadata {
  name: string;
  description: string;
  category: string;
  tags: string[];
  license: string;
  documentation_url: string;
  source_url: string;
  compatibility: string[];
  requirements: string[];
  is_public: boolean;
}

interface ValidationError {
  field: string;
  message: string;
}

const CATEGORIES = [
  { value: 'overview', label: 'Overview' },
  { value: 'safety', label: 'Safety' },
  { value: 'efficacy', label: 'Efficacy' },
  { value: 'operational', label: 'Operational' },
  { value: 'quality', label: 'Quality' },
  { value: 'custom', label: 'Custom' },
];

const LICENSES = [
  { value: 'MIT', label: 'MIT License' },
  { value: 'Apache-2.0', label: 'Apache 2.0' },
  { value: 'GPL-3.0', label: 'GPL 3.0' },
  { value: 'BSD-3-Clause', label: 'BSD 3-Clause' },
  { value: 'Proprietary', label: 'Proprietary' },
];

const COMPATIBILITY_OPTIONS = [
  'CDISC SDTM',
  'CDISC ADaM',
  'Custom Data',
  'CSV Files',
  'SAS Datasets',
  'Parquet Files',
];

export default function PublishTemplatePage() {
  const router = useRouter();
  const { toast } = useToast();
  
  const [currentStep, setCurrentStep] = useState(0);
  const [templateFile, setTemplateFile] = useState<File | null>(null);
  const [screenshots, setScreenshots] = useState<File[]>([]);
  const [screenshotPreviews, setScreenshotPreviews] = useState<string[]>([]);
  const [metadata, setMetadata] = useState<TemplateMetadata>({
    name: '',
    description: '',
    category: '',
    tags: [],
    license: 'MIT',
    documentation_url: '',
    source_url: '',
    compatibility: [],
    requirements: [],
    is_public: true,
  });
  const [newTag, setNewTag] = useState('');
  const [newCompatibility, setNewCompatibility] = useState('');
  const [newRequirement, setNewRequirement] = useState('');
  const [validationErrors, setValidationErrors] = useState<ValidationError[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  const steps = [
    { id: 0, title: 'Upload Template', description: 'Upload your template file' },
    { id: 1, title: 'Template Metadata', description: 'Provide template information' },
    { id: 2, title: 'Screenshots', description: 'Add preview images' },
    { id: 3, title: 'Review & Publish', description: 'Review and publish template' },
  ];

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      if (file.type === 'application/json' || file.name.endsWith('.json')) {
        setTemplateFile(file);
        // Parse and validate template structure
        const reader = new FileReader();
        reader.onload = (e) => {
          try {
            const content = JSON.parse(e.target?.result as string);
            // Extract metadata from template if available
            if (content.metadata) {
              setMetadata(prev => ({
                ...prev,
                name: content.metadata.name || prev.name,
                description: content.metadata.description || prev.description,
                category: content.metadata.category || prev.category,
              }));
            }
          } catch (error) {
            toast({
              title: 'Invalid Template',
              description: 'The uploaded file is not a valid JSON template.',
              variant: 'destructive',
            });
          }
        };
        reader.readAsText(file);
      } else {
        toast({
          title: 'Invalid File Type',
          description: 'Please upload a JSON template file.',
          variant: 'destructive',
        });
      }
    }
  };

  const handleScreenshotUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []);
    const imageFiles = files.filter(file => file.type.startsWith('image/'));
    
    if (imageFiles.length + screenshots.length > 5) {
      toast({
        title: 'Too Many Images',
        description: 'You can upload a maximum of 5 screenshots.',
        variant: 'destructive',
      });
      return;
    }

    setScreenshots(prev => [...prev, ...imageFiles]);
    
    // Create preview URLs
    imageFiles.forEach(file => {
      const url = URL.createObjectURL(file);
      setScreenshotPreviews(prev => [...prev, url]);
    });
  };

  const removeScreenshot = (index: number) => {
    URL.revokeObjectURL(screenshotPreviews[index]);
    setScreenshots(prev => prev.filter((_, i) => i !== index));
    setScreenshotPreviews(prev => prev.filter((_, i) => i !== index));
  };

  const addTag = () => {
    if (newTag.trim() && !metadata.tags.includes(newTag.trim())) {
      setMetadata(prev => ({
        ...prev,
        tags: [...prev.tags, newTag.trim()],
      }));
      setNewTag('');
    }
  };

  const removeTag = (tag: string) => {
    setMetadata(prev => ({
      ...prev,
      tags: prev.tags.filter(t => t !== tag),
    }));
  };

  const addCompatibility = () => {
    if (newCompatibility.trim() && !metadata.compatibility.includes(newCompatibility.trim())) {
      setMetadata(prev => ({
        ...prev,
        compatibility: [...prev.compatibility, newCompatibility.trim()],
      }));
      setNewCompatibility('');
    }
  };

  const removeCompatibility = (item: string) => {
    setMetadata(prev => ({
      ...prev,
      compatibility: prev.compatibility.filter(c => c !== item),
    }));
  };

  const addRequirement = () => {
    if (newRequirement.trim() && !metadata.requirements.includes(newRequirement.trim())) {
      setMetadata(prev => ({
        ...prev,
        requirements: [...prev.requirements, newRequirement.trim()],
      }));
      setNewRequirement('');
    }
  };

  const removeRequirement = (item: string) => {
    setMetadata(prev => ({
      ...prev,
      requirements: prev.requirements.filter(r => r !== item),
    }));
  };

  const validateStep = (step: number): ValidationError[] => {
    const errors: ValidationError[] = [];
    
    switch (step) {
      case 0:
        if (!templateFile) {
          errors.push({ field: 'templateFile', message: 'Template file is required' });
        }
        break;
      case 1:
        if (!metadata.name.trim()) {
          errors.push({ field: 'name', message: 'Template name is required' });
        }
        if (!metadata.description.trim()) {
          errors.push({ field: 'description', message: 'Description is required' });
        }
        if (!metadata.category) {
          errors.push({ field: 'category', message: 'Category is required' });
        }
        if (metadata.tags.length === 0) {
          errors.push({ field: 'tags', message: 'At least one tag is required' });
        }
        break;
      case 2:
        if (screenshots.length === 0) {
          errors.push({ field: 'screenshots', message: 'At least one screenshot is required' });
        }
        break;
    }
    
    return errors;
  };

  const nextStep = () => {
    const errors = validateStep(currentStep);
    setValidationErrors(errors);
    
    if (errors.length === 0) {
      setCurrentStep(prev => Math.min(prev + 1, steps.length - 1));
    }
  };

  const prevStep = () => {
    setCurrentStep(prev => Math.max(prev - 1, 0));
  };

  const handlePublish = async () => {
    try {
      setIsSubmitting(true);
      setUploadProgress(0);

      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return prev;
          }
          return prev + 10;
        });
      }, 200);

      // Create FormData for file upload
      const formData = new FormData();
      if (templateFile) {
        formData.append('template', templateFile);
      }
      
      screenshots.forEach((screenshot, index) => {
        formData.append(`screenshot_${index}`, screenshot);
      });
      
      formData.append('metadata', JSON.stringify(metadata));

      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      setUploadProgress(100);
      
      toast({
        title: 'Success',
        description: 'Template published successfully!',
      });
      
      router.push('/admin/template-marketplace');
    } catch (error) {
      console.error('Error publishing template:', error);
      toast({
        title: 'Error',
        description: 'Failed to publish template. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setIsSubmitting(false);
      setUploadProgress(0);
    }
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 0:
        return (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="w-5 h-5" />
                Upload Template
              </CardTitle>
              <CardDescription>
                Upload your dashboard template JSON file
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div
                className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                  templateFile ? 'border-green-300 bg-green-50' : 'border-gray-300 hover:border-gray-400'
                }`}
              >
                {templateFile ? (
                  <div className="space-y-2">
                    <CheckCircle className="w-12 h-12 text-green-600 mx-auto" />
                    <div className="font-medium">{templateFile.name}</div>
                    <div className="text-sm text-gray-600">
                      {(templateFile.size / 1024).toFixed(2)} KB
                    </div>
                    <Button
                      variant="outline"
                      onClick={() => setTemplateFile(null)}
                    >
                      Remove File
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <Upload className="w-12 h-12 text-gray-400 mx-auto" />
                    <div className="font-medium">Drop your template file here</div>
                    <div className="text-sm text-gray-600">
                      or click to browse (JSON files only)
                    </div>
                    <div>
                      <Input
                        type="file"
                        accept=".json"
                        onChange={handleFileUpload}
                        className="hidden"
                        id="template-upload"
                      />
                      <Label htmlFor="template-upload">
                        <Button variant="outline" className="cursor-pointer">
                          Browse Files
                        </Button>
                      </Label>
                    </div>
                  </div>
                )}
              </div>
              
              {validationErrors.find(e => e.field === 'templateFile') && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    {validationErrors.find(e => e.field === 'templateFile')?.message}
                  </AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>
        );

      case 1:
        return (
          <Card>
            <CardHeader>
              <CardTitle>Template Metadata</CardTitle>
              <CardDescription>
                Provide information about your template
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Template Name *</Label>
                  <Input
                    id="name"
                    value={metadata.name}
                    onChange={(e) => setMetadata(prev => ({ ...prev, name: e.target.value }))}
                    placeholder="Enter template name"
                  />
                  {validationErrors.find(e => e.field === 'name') && (
                    <div className="text-sm text-red-600">
                      {validationErrors.find(e => e.field === 'name')?.message}
                    </div>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="category">Category *</Label>
                  <Select
                    value={metadata.category}
                    onValueChange={(value) => setMetadata(prev => ({ ...prev, category: value }))}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select category" />
                    </SelectTrigger>
                    <SelectContent>
                      {CATEGORIES.map((category) => (
                        <SelectItem key={category.value} value={category.value}>
                          {category.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {validationErrors.find(e => e.field === 'category') && (
                    <div className="text-sm text-red-600">
                      {validationErrors.find(e => e.field === 'category')?.message}
                    </div>
                  )}
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Description *</Label>
                <Textarea
                  id="description"
                  value={metadata.description}
                  onChange={(e) => setMetadata(prev => ({ ...prev, description: e.target.value }))}
                  placeholder="Describe your template..."
                  rows={4}
                />
                {validationErrors.find(e => e.field === 'description') && (
                  <div className="text-sm text-red-600">
                    {validationErrors.find(e => e.field === 'description')?.message}
                  </div>
                )}
              </div>

              <div className="space-y-2">
                <Label>Tags *</Label>
                <div className="flex gap-2">
                  <Input
                    value={newTag}
                    onChange={(e) => setNewTag(e.target.value)}
                    placeholder="Add a tag"
                    onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addTag())}
                  />
                  <Button onClick={addTag} variant="outline">
                    <Plus className="w-4 h-4" />
                  </Button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {metadata.tags.map((tag) => (
                    <Badge key={tag} variant="secondary" className="flex items-center gap-1">
                      <Tag className="w-3 h-3" />
                      {tag}
                      <button onClick={() => removeTag(tag)}>
                        <X className="w-3 h-3 hover:text-red-600" />
                      </button>
                    </Badge>
                  ))}
                </div>
                {validationErrors.find(e => e.field === 'tags') && (
                  <div className="text-sm text-red-600">
                    {validationErrors.find(e => e.field === 'tags')?.message}
                  </div>
                )}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="license">License</Label>
                  <Select
                    value={metadata.license}
                    onValueChange={(value) => setMetadata(prev => ({ ...prev, license: value }))}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {LICENSES.map((license) => (
                        <SelectItem key={license.value} value={license.value}>
                          {license.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <Switch
                      id="is_public"
                      checked={metadata.is_public}
                      onCheckedChange={(checked) => setMetadata(prev => ({ ...prev, is_public: checked }))}
                    />
                    <Label htmlFor="is_public" className="flex items-center gap-2">
                      <Globe className="w-4 h-4" />
                      Public Template
                    </Label>
                  </div>
                  <div className="text-sm text-gray-600">
                    {metadata.is_public ? 'Available in public marketplace' : 'Private template'}
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="documentation_url">Documentation URL</Label>
                  <Input
                    id="documentation_url"
                    value={metadata.documentation_url}
                    onChange={(e) => setMetadata(prev => ({ ...prev, documentation_url: e.target.value }))}
                    placeholder="https://docs.example.com"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="source_url">Source URL</Label>
                  <Input
                    id="source_url"
                    value={metadata.source_url}
                    onChange={(e) => setMetadata(prev => ({ ...prev, source_url: e.target.value }))}
                    placeholder="https://github.com/..."
                  />
                </div>
              </div>

              // Compatibility
              <div className="space-y-2">
                <Label>Compatibility</Label>
                <div className="flex gap-2">
                  <Select value={newCompatibility} onValueChange={setNewCompatibility}>
                    <SelectTrigger className="flex-1">
                      <SelectValue placeholder="Select compatibility" />
                    </SelectTrigger>
                    <SelectContent>
                      {COMPATIBILITY_OPTIONS.filter(option => !metadata.compatibility.includes(option)).map((option) => (
                        <SelectItem key={option} value={option}>
                          {option}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Button onClick={addCompatibility} variant="outline" disabled={!newCompatibility}>
                    <Plus className="w-4 h-4" />
                  </Button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {metadata.compatibility.map((item) => (
                    <Badge key={item} variant="outline" className="flex items-center gap-1">
                      {item}
                      <button onClick={() => removeCompatibility(item)}>
                        <X className="w-3 h-3 hover:text-red-600" />
                      </button>
                    </Badge>
                  ))}
                </div>
              </div>

              // Requirements
              <div className="space-y-2">
                <Label>Requirements</Label>
                <div className="flex gap-2">
                  <Input
                    value={newRequirement}
                    onChange={(e) => setNewRequirement(e.target.value)}
                    placeholder="Add a requirement"
                    onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addRequirement())}
                  />
                  <Button onClick={addRequirement} variant="outline">
                    <Plus className="w-4 h-4" />
                  </Button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {metadata.requirements.map((item) => (
                    <Badge key={item} variant="secondary" className="flex items-center gap-1">
                      {item}
                      <button onClick={() => removeRequirement(item)}>
                        <X className="w-3 h-3 hover:text-red-600" />
                      </button>
                    </Badge>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        );

      case 2:
        return (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Image className="w-5 h-5" />
                Screenshots
              </CardTitle>
              <CardDescription>
                Add preview images of your template (max 5 images)
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                <Upload className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                <div className="text-sm text-gray-600 mb-2">
                  Drop images here or click to browse
                </div>
                <Input
                  type="file"
                  accept="image/*"
                  multiple
                  onChange={handleScreenshotUpload}
                  className="hidden"
                  id="screenshot-upload"
                />
                <Label htmlFor="screenshot-upload">
                  <Button variant="outline" className="cursor-pointer">
                    Browse Images
                  </Button>
                </Label>
              </div>

              {screenshotPreviews.length > 0 && (
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  {screenshotPreviews.map((preview, index) => (
                    <div key={index} className="relative group">
                      <img
                        src={preview}
                        alt={`Screenshot ${index + 1}`}
                        className="w-full h-32 object-cover rounded-lg border"
                      />
                      <button
                        onClick={() => removeScreenshot(index)}
                        className="absolute top-2 right-2 bg-red-600 text-white rounded-full p-1 opacity-0 group-hover:opacity-100 transition-opacity"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {validationErrors.find(e => e.field === 'screenshots') && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    {validationErrors.find(e => e.field === 'screenshots')?.message}
                  </AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>
        );

      case 3:
        return (
          <Card>
            <CardHeader>
              <CardTitle>Review & Publish</CardTitle>
              <CardDescription>
                Review your template details before publishing
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div>
                    <Label className="text-sm font-medium">Template File</Label>
                    <div className="text-sm text-gray-600">{templateFile?.name}</div>
                  </div>
                  
                  <div>
                    <Label className="text-sm font-medium">Name</Label>
                    <div className="text-sm text-gray-600">{metadata.name}</div>
                  </div>
                  
                  <div>
                    <Label className="text-sm font-medium">Category</Label>
                    <Badge variant="outline" className="capitalize">
                      {metadata.category}
                    </Badge>
                  </div>
                  
                  <div>
                    <Label className="text-sm font-medium">License</Label>
                    <div className="text-sm text-gray-600">{metadata.license}</div>
                  </div>
                </div>

                <div className="space-y-4">
                  <div>
                    <Label className="text-sm font-medium">Screenshots</Label>
                    <div className="text-sm text-gray-600">{screenshots.length} image(s)</div>
                  </div>
                  
                  <div>
                    <Label className="text-sm font-medium">Tags</Label>
                    <div className="flex flex-wrap gap-1">
                      {metadata.tags.map((tag) => (
                        <Badge key={tag} variant="secondary" className="text-xs">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  
                  <div>
                    <Label className="text-sm font-medium">Visibility</Label>
                    <div className="text-sm text-gray-600">
                      {metadata.is_public ? 'Public' : 'Private'}
                    </div>
                  </div>
                </div>
              </div>

              <div>
                <Label className="text-sm font-medium">Description</Label>
                <div className="text-sm text-gray-600 mt-1">{metadata.description}</div>
              </div>

              {isSubmitting && (
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span>Publishing template...</span>
                    <span>{uploadProgress}%</span>
                  </div>
                  <Progress value={uploadProgress} />
                </div>
              )}
            </CardContent>
          </Card>
        );

      default:
        return null;
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Publish Template</h1>
        <p className="text-gray-600">
          Share your dashboard template with the community
        </p>
      </div>

      // Progress Steps
      <div className="mb-8">
        <div className="flex items-center justify-between">
          {steps.map((step, index) => (
            <div
              key={step.id}
              className={`flex items-center ${index < steps.length - 1 ? 'flex-1' : ''}`}
            >
              <div className="flex items-center">
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                    index <= currentStep
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-200 text-gray-600'
                  }`}
                >
                  {index + 1}
                </div>
                <div className="ml-3 hidden md:block">
                  <div className="text-sm font-medium">{step.title}</div>
                  <div className="text-xs text-gray-600">{step.description}</div>
                </div>
              </div>
              {index < steps.length - 1 && (
                <div
                  className={`flex-1 h-0.5 mx-4 ${
                    index < currentStep ? 'bg-blue-600' : 'bg-gray-200'
                  }`}
                />
              )}
            </div>
          ))}
        </div>
      </div>

      // Step Content
      <div className="mb-8">
        {renderStepContent()}
      </div>

      // Navigation
      <div className="flex justify-between">
        <Button
          variant="outline"
          onClick={prevStep}
          disabled={currentStep === 0}
        >
          Previous
        </Button>
        
        {currentStep < steps.length - 1 ? (
          <Button onClick={nextStep}>
            Next
          </Button>
        ) : (
          <Button onClick={handlePublish} disabled={isSubmitting}>
            {isSubmitting ? 'Publishing...' : 'Publish Template'}
          </Button>
        )}
      </div>
    </div>
  );
}
*/