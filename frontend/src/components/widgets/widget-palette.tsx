// ABOUTME: Widget palette component for browsing and adding available widgets
// ABOUTME: Shows widgets organized by category with search and filtering

'use client';

import React, { useState, useMemo } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Search,
  Plus,
  BarChart,
  PieChart,
  LineChart,
  Table,
  Activity,
  Map,
  AlertCircle,
  X,
} from 'lucide-react';
import { WidgetRegistry } from './widget-registry';
import { WidgetInstance, WidgetRegistration } from './base-widget';
import { v4 as uuidv4 } from 'uuid';

interface WidgetPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  onAddWidget: (widget: WidgetInstance) => void;
  existingWidgetIds?: string[];
}

// Widget icons mapping
const widgetIcons: Record<string, React.ReactNode> = {
  'metric-card': <Activity className="h-5 w-5" />,
  'line-chart': <LineChart className="h-5 w-5" />,
  'bar-chart': <BarChart className="h-5 w-5" />,
  'pie-chart': <PieChart className="h-5 w-5" />,
  'data-table': <Table className="h-5 w-5" />,
  'enrollment-map': <Map className="h-5 w-5" />,
  'safety-metrics': <AlertCircle className="h-5 w-5" />,
  'query-metrics': <Activity className="h-5 w-5" />,
};

const WidgetCard: React.FC<{
  registration: WidgetRegistration;
  onAdd: () => void;
  disabled?: boolean;
}> = ({ registration, onAdd, disabled }) => {
  const icon = widgetIcons[registration.type] || <Activity className="h-5 w-5" />;

  return (
    <Card className="h-full hover:shadow-md transition-shadow cursor-pointer">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-primary/10 text-primary">
              {icon}
            </div>
            <div>
              <CardTitle className="text-base">{registration.name}</CardTitle>
              {registration.category && (
                <Badge variant="secondary" className="mt-1 text-xs">
                  {registration.category}
                </Badge>
              )}
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent className="pb-3">
        <CardDescription className="text-xs mb-3">
          {registration.description}
        </CardDescription>
        <Button
          size="sm"
          className="w-full"
          onClick={(e) => {
            e.stopPropagation();
            onAdd();
          }}
          disabled={disabled}
        >
          <Plus className="h-4 w-4 mr-1" />
          Add to Dashboard
        </Button>
      </CardContent>
    </Card>
  );
};

export const WidgetPalette: React.FC<WidgetPaletteProps> = ({
  isOpen,
  onClose,
  onAddWidget,
  existingWidgetIds = [],
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  // Get all available widgets
  const allWidgets = useMemo(() => WidgetRegistry.getAll(), []);
  const categories = useMemo(() => {
    const cats = ['all', ...WidgetRegistry.getCategories()];
    return cats;
  }, []);

  // Filter widgets based on search and category
  const filteredWidgets = useMemo(() => {
    return allWidgets.filter((widget) => {
      const matchesSearch =
        searchQuery === '' ||
        widget.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        widget.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
        widget.type.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesCategory =
        selectedCategory === 'all' || widget.category === selectedCategory;

      return matchesSearch && matchesCategory;
    });
  }, [allWidgets, searchQuery, selectedCategory]);

  // Group widgets by category
  const groupedWidgets = useMemo(() => {
    const groups: Record<string, WidgetRegistration[]> = {};

    if (selectedCategory === 'all') {
      // Group by category
      filteredWidgets.forEach((widget) => {
        const category = widget.category || 'Other';
        if (!groups[category]) {
          groups[category] = [];
        }
        groups[category].push(widget);
      });
    } else {
      // Single category
      groups[selectedCategory] = filteredWidgets;
    }

    return groups;
  }, [filteredWidgets, selectedCategory]);

  const handleAddWidget = (registration: WidgetRegistration) => {
    // Create new widget instance with default configuration
    const widgetId = `${registration.type}-${uuidv4().substring(0, 8)}`;
    
    // Get default configuration from schema
    const defaultConfig: Record<string, any> = {};
    if (registration.configSchema) {
      Object.entries(registration.configSchema).forEach(([field, schema]: [string, any]) => {
        if (schema.default !== undefined) {
          defaultConfig[field] = schema.default;
        }
      });
    }

    const widgetInstance: WidgetInstance = {
      id: widgetId,
      type: registration.type,
      title: registration.name,
      description: registration.description,
      configuration: defaultConfig,
      layout: {
        x: 0,
        y: 0,
        w: registration.component.defaultWidth || 3,
        h: registration.component.defaultHeight || 2,
        minW: 1,
        minH: 1,
      },
    };

    onAddWidget(widgetInstance);
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh]">
        <DialogHeader>
          <DialogTitle>Add Widget</DialogTitle>
          <DialogDescription>
            Choose a widget to add to your dashboard
          </DialogDescription>
        </DialogHeader>

        <div className="mt-4 space-y-4">
          {/* Search Bar */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search widgets..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>

          {/* Category Tabs */}
          <Tabs value={selectedCategory} onValueChange={setSelectedCategory}>
            <TabsList className="w-full justify-start">
              {categories.map((category) => (
                <TabsTrigger key={category} value={category}>
                  {category === 'all' ? 'All Widgets' : category}
                </TabsTrigger>
              ))}
            </TabsList>

            <TabsContent value={selectedCategory} className="mt-4">
              <ScrollArea className="h-[400px] pr-4">
                {Object.entries(groupedWidgets).map(([category, widgets]) => (
                  <div key={category} className="mb-6">
                    {selectedCategory === 'all' && (
                      <h3 className="text-sm font-semibold mb-3">{category}</h3>
                    )}
                    <div className="grid grid-cols-2 gap-4">
                      {widgets.map((widget) => (
                        <WidgetCard
                          key={widget.type}
                          registration={widget}
                          onAdd={() => handleAddWidget(widget)}
                        />
                      ))}
                    </div>
                  </div>
                ))}

                {filteredWidgets.length === 0 && (
                  <div className="text-center py-12">
                    <p className="text-muted-foreground">
                      No widgets found matching your search.
                    </p>
                  </div>
                )}
              </ScrollArea>
            </TabsContent>
          </Tabs>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            <X className="h-4 w-4 mr-2" />
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};