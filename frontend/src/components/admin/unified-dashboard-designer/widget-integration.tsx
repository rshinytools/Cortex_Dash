// ABOUTME: Widget integration component for dashboard designer
// ABOUTME: Bridges the new widget engine system with the dashboard designer

import React, { useState, useCallback } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { WidgetConfigurationPanel } from '@/components/widgets/WidgetConfigurationPanel';
import { WidgetRenderer } from '@/components/widgets/WidgetRenderer';
import {
  BarChartIcon,
  TrendingUpIcon,
  TableIcon,
  CalendarIcon,
  ActivityIcon,
  Grid3x3Icon,
  PieChartIcon,
  LineChartIcon,
  LayoutDashboardIcon,
} from 'lucide-react';

interface WidgetIntegrationProps {
  studyId: string;
  onAddWidget: (widget: any) => void;
  onUpdateWidget: (widgetId: string, config: any) => void;
  availableDatasets?: any[];
}

// Define available widget types with metadata
const WIDGET_CATALOG = [
  {
    id: 'kpi_metric_card',
    name: 'KPI Metric Card',
    description: 'Display single metrics with comparisons and trends',
    icon: TrendingUpIcon,
    category: 'metrics',
    tags: ['metric', 'kpi', 'comparison', 'trend'],
    preview: {
      value: 156,
      formatted_value: '156',
      comparison: { show: true, type: 'target', target_value: 150, percentage: 4 },
      trend: { trend: 'up', trend_percentage: 12.5 },
    },
  },
  {
    id: 'time_series_chart',
    name: 'Time Series Chart',
    description: 'Visualize data trends over time',
    icon: LineChartIcon,
    category: 'charts',
    tags: ['chart', 'time', 'trend', 'temporal'],
    preview: {
      chart_type: 'line',
      data: {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
        datasets: [{ label: 'Value', data: [45, 52, 58, 65, 72] }],
      },
    },
  },
  {
    id: 'distribution_chart',
    name: 'Distribution Chart',
    description: 'Show data distribution with various chart types',
    icon: BarChartIcon,
    category: 'charts',
    tags: ['chart', 'distribution', 'bar', 'pie', 'histogram'],
    subtypes: ['bar', 'pie', 'donut', 'histogram', 'pareto'],
    preview: {
      chart_subtype: 'bar',
      data: {
        labels: ['A', 'B', 'C', 'D'],
        datasets: [{ data: [45, 38, 52, 31] }],
      },
    },
  },
  {
    id: 'data_table',
    name: 'Data Table',
    description: 'Display detailed records with pagination and sorting',
    icon: TableIcon,
    category: 'tables',
    tags: ['table', 'data', 'list', 'details'],
    preview: {
      columns: [
        { key: 'id', label: 'ID' },
        { key: 'name', label: 'Name' },
        { key: 'status', label: 'Status' },
      ],
      rows: [
        { id: '001', name: 'Subject A', status: 'Active' },
        { id: '002', name: 'Subject B', status: 'Active' },
      ],
    },
  },
  {
    id: 'subject_timeline',
    name: 'Subject Timeline',
    description: 'Visualize individual subject journeys',
    icon: CalendarIcon,
    category: 'specialized',
    tags: ['timeline', 'subject', 'journey', 'events'],
    views: ['chronological', 'grouped', 'swim_lane', 'gantt'],
    preview: {
      view_type: 'chronological',
      subjects: [
        {
          subject_id: 'S001',
          events: [
            { event_type: 'Screening', event_date: '2024-01-01' },
            { event_type: 'Baseline', event_date: '2024-01-15' },
          ],
        },
      ],
    },
  },
];

export const WidgetIntegration: React.FC<WidgetIntegrationProps> = ({
  studyId,
  onAddWidget,
  onUpdateWidget,
  availableDatasets = [],
}) => {
  const [selectedWidget, setSelectedWidget] = useState<any>(null);
  const [showConfigDialog, setShowConfigDialog] = useState(false);
  const [activeCategory, setActiveCategory] = useState('all');

  const handleWidgetSelect = (widget: any) => {
    setSelectedWidget(widget);
    setShowConfigDialog(true);
  };

  const handleSaveWidget = async (config: any) => {
    // Validate configuration
    try {
      const response = await fetch('/api/widget-execution/validate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          widget_type: selectedWidget.id,
          mapping_config: config,
        }),
      });

      const result = await response.json();

      if (result.valid) {
        // Create widget instance
        const widgetInstance = {
          id: `widget_${Date.now()}`,
          type: selectedWidget.id,
          name: config.display_config?.title || selectedWidget.name,
          config: config,
          position: { x: 0, y: 0, w: 4, h: 3 },
        };

        onAddWidget(widgetInstance);
        setShowConfigDialog(false);
        setSelectedWidget(null);
      } else {
        // Show validation errors
        console.error('Validation errors:', result.errors);
      }
    } catch (error) {
      console.error('Failed to validate widget configuration:', error);
    }
  };

  const getWidgetsByCategory = (category: string) => {
    if (category === 'all') return WIDGET_CATALOG;
    return WIDGET_CATALOG.filter((w) => w.category === category);
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'metrics':
        return <ActivityIcon className="h-4 w-4" />;
      case 'charts':
        return <LineChartIcon className="h-4 w-4" />;
      case 'tables':
        return <Grid3x3Icon className="h-4 w-4" />;
      case 'specialized':
        return <LayoutDashboardIcon className="h-4 w-4" />;
      default:
        return null;
    }
  };

  return (
    <>
      {/* Widget Catalog */}
      <div className="space-y-4">
        <Tabs value={activeCategory} onValueChange={setActiveCategory}>
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="all">All</TabsTrigger>
            <TabsTrigger value="metrics">Metrics</TabsTrigger>
            <TabsTrigger value="charts">Charts</TabsTrigger>
            <TabsTrigger value="tables">Tables</TabsTrigger>
            <TabsTrigger value="specialized">Specialized</TabsTrigger>
          </TabsList>

          <TabsContent value={activeCategory}>
            <ScrollArea className="h-[600px]">
              <div className="grid grid-cols-1 gap-4">
                {getWidgetsByCategory(activeCategory).map((widget) => (
                  <Card
                    key={widget.id}
                    className="cursor-pointer hover:shadow-lg transition-shadow"
                    onClick={() => handleWidgetSelect(widget)}
                  >
                    <CardHeader className="pb-3">
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-2">
                          <widget.icon className="h-5 w-5 text-muted-foreground" />
                          <CardTitle className="text-sm">{widget.name}</CardTitle>
                        </div>
                        <Badge variant="secondary" className="text-xs">
                          {widget.category}
                        </Badge>
                      </div>
                      <CardDescription className="text-xs mt-1">
                        {widget.description}
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      {/* Widget Preview */}
                      <div className="bg-muted/50 rounded-lg p-3 h-32 flex items-center justify-center">
                        {widget.id === 'kpi_metric_card' && (
                          <div className="text-center">
                            <div className="text-2xl font-bold">156</div>
                            <div className="text-xs text-muted-foreground">+12.5%</div>
                          </div>
                        )}
                        {widget.id === 'time_series_chart' && (
                          <LineChartIcon className="h-16 w-16 text-muted-foreground/50" />
                        )}
                        {widget.id === 'distribution_chart' && (
                          <BarChartIcon className="h-16 w-16 text-muted-foreground/50" />
                        )}
                        {widget.id === 'data_table' && (
                          <TableIcon className="h-16 w-16 text-muted-foreground/50" />
                        )}
                        {widget.id === 'subject_timeline' && (
                          <CalendarIcon className="h-16 w-16 text-muted-foreground/50" />
                        )}
                      </div>

                      {/* Tags */}
                      <div className="flex flex-wrap gap-1 mt-3">
                        {widget.tags.map((tag) => (
                          <Badge key={tag} variant="outline" className="text-xs">
                            {tag}
                          </Badge>
                        ))}
                      </div>

                      {/* Subtypes or Views */}
                      {widget.subtypes && (
                        <div className="mt-2">
                          <span className="text-xs text-muted-foreground">
                            Subtypes: {widget.subtypes.join(', ')}
                          </span>
                        </div>
                      )}
                      {widget.views && (
                        <div className="mt-2">
                          <span className="text-xs text-muted-foreground">
                            Views: {widget.views.join(', ')}
                          </span>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            </ScrollArea>
          </TabsContent>
        </Tabs>
      </div>

      {/* Widget Configuration Dialog */}
      <Dialog open={showConfigDialog} onOpenChange={setShowConfigDialog}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden">
          <DialogHeader>
            <DialogTitle>Configure {selectedWidget?.name}</DialogTitle>
          </DialogHeader>
          {selectedWidget && (
            <WidgetConfigurationPanel
              widgetType={selectedWidget.id}
              studyId={studyId}
              availableDatasets={availableDatasets}
              onSave={handleSaveWidget}
              onCancel={() => {
                setShowConfigDialog(false);
                setSelectedWidget(null);
              }}
              onValidate={async (config) => {
                const response = await fetch('/api/widget-execution/validate', {
                  method: 'POST',
                  headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${localStorage.getItem('token')}`,
                  },
                  body: JSON.stringify({
                    widget_type: selectedWidget.id,
                    mapping_config: config,
                  }),
                });

                const result = await response.json();
                return result;
              }}
            />
          )}
        </DialogContent>
      </Dialog>
    </>
  );
};

// Export widget catalog for use in other components
export { WIDGET_CATALOG };