// ABOUTME: Template selection step for study initialization wizard
// ABOUTME: Allows users to browse and select from available dashboard templates

'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';
import { Loader2, Search, Layout, BarChart3, Shield, Activity, Briefcase } from 'lucide-react';
import { cn } from '@/lib/utils';

interface DashboardTemplate {
  id: string;
  code: string;
  name: string;
  description: string;
  category: string;
  version: number;
  dashboard_count: number;
  widget_count: number;
  created_at: string;
  updated_at: string;
}

interface TemplateSelectionStepProps {
  studyId: string;
  data: {
    templateId?: string;
    templateDetails?: DashboardTemplate;
  };
  onDataChange: (data: any) => void;
}

const categoryIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  overview: Layout,
  safety: Shield,
  efficacy: Activity,
  operational: Briefcase,
  custom: BarChart3,
};

export function TemplateSelectionStep({ studyId, data, onDataChange }: TemplateSelectionStepProps) {
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>(data.templateId || '');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  // Fetch available templates
  const { data: templatesResponse, isLoading } = useQuery({
    queryKey: ['dashboard-templates'],
    queryFn: async () => {
      const response = await apiClient.get('/dashboard-templates/');
      return response.data;
    },
  });

  const templates: DashboardTemplate[] = templatesResponse?.data || [];

  // Filter templates based on search and category
  const filteredTemplates = templates.filter(template => {
    const matchesSearch = searchQuery === '' || 
      template.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      template.description?.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesCategory = selectedCategory === 'all' || template.category === selectedCategory;
    
    return matchesSearch && matchesCategory;
  });

  // Get unique categories
  const categories = ['all', ...Array.from(new Set(templates.map(t => t.category)))];

  // Handle template selection
  const handleTemplateSelect = (templateId: string) => {
    const template = templates.find(t => t.id === templateId);
    setSelectedTemplateId(templateId);
    onDataChange({
      templateId,
      templateDetails: template,
    });
  };

  // Get selected template details
  const selectedTemplate = templates.find(t => t.id === selectedTemplateId);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Search and filters */}
      <div className="space-y-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search templates..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>

        <Tabs value={selectedCategory} onValueChange={setSelectedCategory}>
          <TabsList className="grid grid-cols-6 w-full">
            {categories.map(category => {
              const Icon = categoryIcons[category] || Layout;
              return (
                <TabsTrigger key={category} value={category} className="capitalize">
                  <Icon className="h-4 w-4 mr-2" />
                  {category}
                </TabsTrigger>
              );
            })}
          </TabsList>
        </Tabs>
      </div>

      {/* Template grid */}
      <RadioGroup value={selectedTemplateId} onValueChange={handleTemplateSelect}>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredTemplates.map(template => {
            const Icon = categoryIcons[template.category] || Layout;
            const isSelected = selectedTemplateId === template.id;
            
            return (
              <Card 
                key={template.id} 
                className={cn(
                  "cursor-pointer transition-all",
                  isSelected && "border-primary ring-2 ring-primary ring-offset-2"
                )}
                onClick={() => handleTemplateSelect(template.id)}
              >
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className={cn(
                        "p-2 rounded-lg",
                        isSelected ? "bg-primary text-primary-foreground" : "bg-muted"
                      )}>
                        <Icon className="h-5 w-5" />
                      </div>
                      <div>
                        <CardTitle className="text-lg flex items-center gap-2">
                          <RadioGroupItem value={template.id} />
                          {template.name}
                        </CardTitle>
                        <CardDescription className="mt-1">
                          {template.code} • v{template.version}
                        </CardDescription>
                      </div>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground mb-4">
                    {template.description}
                  </p>
                  <div className="flex gap-4 text-sm">
                    <div className="flex items-center gap-1">
                      <Layout className="h-4 w-4 text-muted-foreground" />
                      <span>{template.dashboard_count} dashboards</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <BarChart3 className="h-4 w-4 text-muted-foreground" />
                      <span>{template.widget_count} widgets</span>
                    </div>
                  </div>
                  <div className="mt-3">
                    <Badge variant="secondary" className="capitalize">
                      {template.category}
                    </Badge>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </RadioGroup>

      {filteredTemplates.length === 0 && (
        <Card>
          <CardContent className="text-center py-12">
            <p className="text-muted-foreground">
              No templates found matching your criteria.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Selected template preview */}
      {selectedTemplate && (
        <Card className="mt-6 border-primary">
          <CardHeader>
            <CardTitle>Selected Template</CardTitle>
            <CardDescription>
              You've selected the {selectedTemplate.name} template
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 text-sm">
              <p><strong>Category:</strong> {selectedTemplate.category}</p>
              <p><strong>Dashboards:</strong> {selectedTemplate.dashboard_count}</p>
              <p><strong>Total Widgets:</strong> {selectedTemplate.widget_count}</p>
              <p><strong>Last Updated:</strong> {new Date(selectedTemplate.updated_at).toLocaleDateString()}</p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}