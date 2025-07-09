// ABOUTME: Dashboard configuration step in study initialization wizard
// ABOUTME: Allows designing the study dashboard layout and widgets

'use client';

import { useState, useEffect } from 'react';
import { 
  Plus, 
  Trash2, 
  GripVertical, 
  BarChart3, 
  TrendingUp, 
  Users, 
  Calendar,
  Map,
  Table,
  Activity,
  AlertCircle,
  FileQuestion,
  Shield
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface DashboardStepProps {
  studyId: string;
  data: any;
  onDataChange: (data: any) => void;
}

// Widget types based on the screenshot
const widgetTypes = [
  { 
    id: 'metric_card', 
    name: 'Metric Card', 
    icon: TrendingUp, 
    description: 'Single metric with trend',
    category: 'metrics',
    defaultConfig: {
      dataset: 'ADSL',
      field: '',
      calculation: 'count',
      showTrend: true,
      showPercentage: false
    }
  },
  { 
    id: 'enrollment_map', 
    name: 'Enrollment Map', 
    icon: Map, 
    description: 'Geographic enrollment visualization',
    category: 'geographic',
    defaultConfig: {
      dataset: 'ADSL',
      locationField: 'SITEID',
      valueField: 'USUBJID',
      mapType: 'world'
    }
  },
  { 
    id: 'line_chart', 
    name: 'Line Chart', 
    icon: Activity, 
    description: 'Trend over time',
    category: 'charts',
    defaultConfig: {
      dataset: 'ADSL',
      xAxis: 'RFSTDTC',
      yAxis: [],
      groupBy: null
    }
  },
  { 
    id: 'bar_chart', 
    name: 'Bar Chart', 
    icon: BarChart3, 
    description: 'Category comparison',
    category: 'charts',
    defaultConfig: {
      dataset: 'ADSL',
      xAxis: '',
      yAxis: '',
      orientation: 'vertical'
    }
  },
  { 
    id: 'data_table', 
    name: 'Data Table', 
    icon: Table, 
    description: 'Tabular data display',
    category: 'tables',
    defaultConfig: {
      dataset: 'ADSL',
      columns: [],
      pageSize: 10,
      enableExport: true
    }
  },
  { 
    id: 'safety_metrics', 
    name: 'Safety Metrics', 
    icon: Shield, 
    description: 'AE/SAE summary',
    category: 'safety',
    defaultConfig: {
      showAE: true,
      showSAE: true,
      showDeaths: true,
      groupBySOC: true
    }
  },
  { 
    id: 'query_metrics', 
    name: 'Query Metrics', 
    icon: FileQuestion, 
    description: 'Data query statistics',
    category: 'quality',
    defaultConfig: {
      showTotal: true,
      showOpen: true,
      showAnswered: true,
      showCancelled: true,
      showClosed: true
    }
  }
];

// Predefined dashboard templates based on screenshot
const dashboardTemplates = [
  {
    id: 'clinical_overview',
    name: 'Clinical Overview',
    description: 'Comprehensive view with enrollment, safety, and quality metrics',
    widgets: [
      // Top row metrics
      { type: 'metric_card', title: 'Total Screened', position: { x: 0, y: 0, w: 2, h: 2 } },
      { type: 'metric_card', title: 'Safety Population', position: { x: 2, y: 0, w: 2, h: 2 } },
      { type: 'metric_card', title: 'ITT Population', position: { x: 4, y: 0, w: 2, h: 2 } },
      { type: 'metric_card', title: 'Screen Failures', position: { x: 6, y: 0, w: 2, h: 2 } },
      { type: 'metric_card', title: 'Total Deaths', position: { x: 8, y: 0, w: 2, h: 2 } },
      // Second row metrics
      { type: 'metric_card', title: 'Treatment Discontinuation', position: { x: 0, y: 2, w: 2, h: 2 } },
      { type: 'metric_card', title: 'Study Discontinuation', position: { x: 2, y: 2, w: 2, h: 2 } },
      { type: 'metric_card', title: 'Total AEs', position: { x: 4, y: 2, w: 2, h: 2 } },
      { type: 'metric_card', title: 'Total SAEs', position: { x: 6, y: 2, w: 2, h: 2 } },
      { type: 'metric_card', title: 'Total Issues', position: { x: 8, y: 2, w: 2, h: 2 } },
      // Query metrics row
      { type: 'query_metrics', title: 'Query Overview', position: { x: 0, y: 4, w: 10, h: 2 } },
      // Map and chart
      { type: 'enrollment_map', title: 'Site Enrollment Map', position: { x: 0, y: 6, w: 5, h: 4 } },
      { type: 'line_chart', title: 'Enrollment & Screen Failure Trend', position: { x: 5, y: 6, w: 5, h: 4 } }
    ]
  },
  {
    id: 'enrollment_focus',
    name: 'Enrollment Dashboard',
    description: 'Focus on recruitment and enrollment metrics',
    widgets: [
      { type: 'metric_card', title: 'Total Enrolled', position: { x: 0, y: 0, w: 3, h: 2 } },
      { type: 'metric_card', title: 'Target Enrollment', position: { x: 3, y: 0, w: 3, h: 2 } },
      { type: 'metric_card', title: 'Enrollment Rate', position: { x: 6, y: 0, w: 3, h: 2 } },
      { type: 'enrollment_map', title: 'Enrollment by Site', position: { x: 0, y: 2, w: 6, h: 4 } },
      { type: 'line_chart', title: 'Enrollment Progress', position: { x: 6, y: 2, w: 4, h: 4 } }
    ]
  },
  {
    id: 'safety_focus',
    name: 'Safety Dashboard',
    description: 'Safety monitoring and adverse events',
    widgets: [
      { type: 'safety_metrics', title: 'Safety Overview', position: { x: 0, y: 0, w: 10, h: 2 } },
      { type: 'bar_chart', title: 'AEs by System Organ Class', position: { x: 0, y: 2, w: 5, h: 4 } },
      { type: 'data_table', title: 'Serious Adverse Events', position: { x: 5, y: 2, w: 5, h: 4 } }
    ]
  },
  {
    id: 'custom',
    name: 'Custom Layout',
    description: 'Build your own dashboard from scratch',
    widgets: []
  }
];

export function DashboardStep({ studyId, data, onDataChange }: DashboardStepProps) {
  const [selectedTemplate, setSelectedTemplate] = useState(data.selectedTemplate || 'clinical_overview');
  const [widgets, setWidgets] = useState(data.widgets || []);
  const [dashboardName, setDashboardName] = useState(data.dashboardName || 'Study Overview Dashboard');
  const [dashboardDescription, setDashboardDescription] = useState(data.dashboardDescription || '');
  const [selectedTab, setSelectedTab] = useState('template');
  const [showWidgetConfig, setShowWidgetConfig] = useState<string | null>(null);

  useEffect(() => {
    // Load template widgets when template changes
    if (selectedTemplate !== 'custom' && (!widgets.length || data.selectedTemplate !== selectedTemplate)) {
      const template = dashboardTemplates.find(t => t.id === selectedTemplate);
      if (template) {
        const templateWidgets = template.widgets.map((w, index) => ({
          id: `widget-${Date.now()}-${index}`,
          ...w,
          config: widgetTypes.find(wt => wt.id === w.type)?.defaultConfig || {}
        }));
        setWidgets(templateWidgets);
      }
    }
  }, [selectedTemplate]);

  useEffect(() => {
    onDataChange({ 
      selectedTemplate,
      widgets,
      dashboardName,
      dashboardDescription,
      layout: {
        type: 'grid',
        columns: 10,
        rows: 10,
        gap: 16
      }
    });
  }, [selectedTemplate, widgets, dashboardName, dashboardDescription]);

  const addWidget = (typeId: string) => {
    const widgetType = widgetTypes.find(w => w.id === typeId);
    if (!widgetType) return;

    const newWidget = {
      id: `widget-${Date.now()}`,
      type: typeId,
      title: widgetType.name,
      position: { x: 0, y: 0, w: 3, h: 2 },
      config: { ...widgetType.defaultConfig }
    };
    setWidgets([...widgets, newWidget]);
  };

  const updateWidget = (widgetId: string, updates: any) => {
    setWidgets(widgets.map((w: any) => 
      w.id === widgetId ? { ...w, ...updates } : w
    ));
  };

  const removeWidget = (widgetId: string) => {
    setWidgets(widgets.filter((w: any) => w.id !== widgetId));
  };

  const getWidgetIcon = (type: string) => {
    const widgetType = widgetTypes.find(w => w.id === type);
    return widgetType?.icon || BarChart3;
  };

  return (
    <div className="space-y-6">
      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          Configure your study dashboard to visualize key metrics and track study progress.
          You can choose a pre-built template or create a custom dashboard.
        </AlertDescription>
      </Alert>

      <Tabs value={selectedTab} onValueChange={setSelectedTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="template">Choose Template</TabsTrigger>
          <TabsTrigger value="widgets">Configure Widgets</TabsTrigger>
          <TabsTrigger value="preview">Preview</TabsTrigger>
        </TabsList>

        <TabsContent value="template" className="space-y-4">
          <div>
            <Label>Dashboard Name</Label>
            <Input
              value={dashboardName}
              onChange={(e) => setDashboardName(e.target.value)}
              placeholder="Enter dashboard name"
              className="mt-2"
            />
          </div>

          <div>
            <Label>Description (Optional)</Label>
            <Textarea
              value={dashboardDescription}
              onChange={(e) => setDashboardDescription(e.target.value)}
              placeholder="Describe the purpose of this dashboard"
              className="mt-2"
              rows={3}
            />
          </div>

          <div>
            <Label>Select Dashboard Template</Label>
            <div className="grid gap-4 mt-2">
              {dashboardTemplates.map((template) => (
                <Card
                  key={template.id}
                  className={cn(
                    'cursor-pointer transition-colors',
                    selectedTemplate === template.id ? 'border-primary' : ''
                  )}
                  onClick={() => setSelectedTemplate(template.id)}
                >
                  <CardHeader>
                    <div className="flex justify-between items-start">
                      <div>
                        <CardTitle className="text-lg">{template.name}</CardTitle>
                        <p className="text-sm text-muted-foreground mt-1">
                          {template.description}
                        </p>
                      </div>
                      {selectedTemplate === template.id && (
                        <Badge>Selected</Badge>
                      )}
                    </div>
                  </CardHeader>
                  {template.widgets.length > 0 && (
                    <CardContent>
                      <p className="text-sm text-muted-foreground">
                        {template.widgets.length} pre-configured widgets
                      </p>
                    </CardContent>
                  )}
                </Card>
              ))}
            </div>
          </div>
        </TabsContent>

        <TabsContent value="widgets" className="space-y-4">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-medium">Dashboard Widgets</h3>
            <Select onValueChange={addWidget}>
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="Add widget" />
              </SelectTrigger>
              <SelectContent>
                {widgetTypes.map((type) => (
                  <SelectItem key={type.id} value={type.id}>
                    <div className="flex items-center gap-2">
                      <type.icon className="h-4 w-4" />
                      {type.name}
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {widgets.length === 0 ? (
            <Card>
              <CardContent className="py-8 text-center">
                <p className="text-muted-foreground mb-4">
                  No widgets configured. Add widgets to build your dashboard.
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-2">
              {widgets.map((widget: any) => {
                const Icon = getWidgetIcon(widget.type);
                return (
                  <Card key={widget.id}>
                    <CardContent className="py-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <GripVertical className="h-4 w-4 text-muted-foreground cursor-move" />
                          <Icon className="h-4 w-4 text-muted-foreground" />
                          <div>
                            <Input
                              value={widget.title}
                              onChange={(e) => updateWidget(widget.id, { title: e.target.value })}
                              className="h-8 w-[200px]"
                              placeholder="Widget title"
                            />
                            <p className="text-xs text-muted-foreground mt-1">
                              {widgetTypes.find(t => t.id === widget.type)?.description}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge variant="outline">
                            {widget.position.w}x{widget.position.h}
                          </Badge>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => setShowWidgetConfig(widget.id === showWidgetConfig ? null : widget.id)}
                          >
                            Configure
                          </Button>
                          <Button
                            size="icon"
                            variant="ghost"
                            onClick={() => removeWidget(widget.id)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                      
                      {showWidgetConfig === widget.id && (
                        <div className="mt-4 p-4 bg-muted rounded-md">
                          <p className="text-sm text-muted-foreground">
                            Widget configuration will be available in the next step.
                            Position: ({widget.position.x}, {widget.position.y})
                          </p>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </TabsContent>

        <TabsContent value="preview">
          <Card>
            <CardHeader>
              <CardTitle>Dashboard Preview</CardTitle>
              <p className="text-sm text-muted-foreground">
                Visual preview of your dashboard layout
              </p>
            </CardHeader>
            <CardContent>
              <div className="bg-muted rounded-lg p-4 min-h-[400px]">
                <div className="grid grid-cols-10 gap-2">
                  {widgets.map((widget: any) => {
                    const Icon = getWidgetIcon(widget.type);
                    return (
                      <div
                        key={widget.id}
                        className="bg-background border rounded p-3 flex flex-col items-center justify-center text-center"
                        style={{
                          gridColumn: `${widget.position.x + 1} / span ${widget.position.w}`,
                          gridRow: `${widget.position.y + 1} / span ${widget.position.h}`,
                          minHeight: `${widget.position.h * 60}px`
                        }}
                      >
                        <Icon className="h-6 w-6 text-muted-foreground mb-2" />
                        <p className="text-xs font-medium">{widget.title}</p>
                        <Badge variant="outline" className="mt-2 text-xs">
                          {widget.type.replace('_', ' ')}
                        </Badge>
                      </div>
                    );
                  })}
                </div>
              </div>
              <p className="text-sm text-muted-foreground mt-4">
                <strong>Note:</strong> This is a simplified preview. The actual dashboard will display real data
                with interactive widgets and visualizations.
              </p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

function cn(...classes: string[]) {
  return classes.filter(Boolean).join(' ');
}