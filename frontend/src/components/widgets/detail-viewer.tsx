// ABOUTME: Detail viewer component for displaying drill-down detail views and expanded data
// ABOUTME: Renders detailed information for specific data points in various formats

'use client';

import React, { useState, useCallback, useMemo, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/components/ui/sheet';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  X, 
  Download, 
  Maximize2, 
  Minimize2,
  RefreshCw,
  Filter,
  ChevronDown,
  ChevronRight,
  Eye,
  Database,
  BarChart3
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useDrillDownManager } from './drill-down-manager';
import { BreadcrumbNavigation } from './breadcrumb-navigation';
import { WidgetRenderer } from './widget-renderer';

interface DetailViewerProps {
  pathId?: string;
  isOpen: boolean;
  onClose: () => void;
  variant?: 'sheet' | 'dialog' | 'fullscreen';
  className?: string;
}

export function DetailViewer({
  pathId,
  isOpen,
  onClose,
  variant = 'sheet',
  className,
}: DetailViewerProps) {
  const {
    getActivePath,
    getCurrentLevel,
    getBreadcrumbs,
    clearDrillDown,
    state,
  } = useDrillDownManager();

  const [activeTab, setActiveTab] = useState('table');
  const [isFullscreen, setIsFullscreen] = useState(false);

  const targetPath = pathId ? state.paths[pathId] : getActivePath();
  const currentLevel = getCurrentLevel(pathId);
  const breadcrumbs = getBreadcrumbs(pathId);
  const detailData = pathId ? state.detail_views[pathId] : null;

  // Mock detail data - in a real app, this would come from API
  const mockDetailData = useMemo(() => {
    if (!currentLevel) return null;

    return {
      summary: {
        title: `Details for ${currentLevel.title}`,
        field: currentLevel.field,
        value: currentLevel.value,
        level: currentLevel.level,
        timestamp: currentLevel.timestamp,
        context: currentLevel.context,
      },
      metrics: [
        { label: 'Total Records', value: 245, change: '+12%', trend: 'up' },
        { label: 'Active Items', value: 189, change: '+5%', trend: 'up' },
        { label: 'Completion Rate', value: '77%', change: '+2%', trend: 'up' },
        { label: 'Last Updated', value: '2 hours ago', change: null, trend: 'stable' },
      ],
      table_data: Array.from({ length: 20 }, (_, i) => ({
        id: i + 1,
        subject_id: `SUBJ-${1000 + i}`,
        visit_number: Math.floor(Math.random() * 5) + 1,
        visit_date: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        status: ['Completed', 'In Progress', 'Scheduled'][Math.floor(Math.random() * 3)],
        value: Math.round(Math.random() * 100),
      })),
      chart_data: {
        categories: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
        series: [
          {
            name: 'Completed',
            data: [45, 52, 48, 61],
          },
          {
            name: 'In Progress',
            data: [28, 31, 34, 29],
          },
        ],
      },
    };
  }, [currentLevel]);

  // Handle export
  const handleExport = useCallback((format: 'csv' | 'excel' | 'pdf') => {
    // Mock export functionality
    console.log(`Exporting detail view as ${format}`);
  }, []);

  // Handle refresh
  const handleRefresh = useCallback(() => {
    // Mock refresh functionality
    console.log('Refreshing detail view');
  }, []);

  // Handle clear drill-down
  const handleClear = useCallback(() => {
    clearDrillDown(pathId);
    onClose();
  }, [clearDrillDown, pathId, onClose]);

  // Close if no data
  useEffect(() => {
    if (isOpen && !targetPath) {
      onClose();
    }
  }, [isOpen, targetPath, onClose]);

  if (!targetPath || !currentLevel || !mockDetailData) {
    return null;
  }

  // Render content
  const content = (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex-shrink-0 border-b p-4">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h2 className="text-lg font-semibold">{mockDetailData.summary.title}</h2>
            <p className="text-sm text-muted-foreground">
              Level {currentLevel.level + 1} • {currentLevel.field}: {currentLevel.value}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="icon" onClick={handleRefresh}>
              <RefreshCw className="h-4 w-4" />
            </Button>
            {variant !== 'fullscreen' && (
              <Button
                variant="outline"
                size="icon"
                onClick={() => setIsFullscreen(!isFullscreen)}
              >
                {isFullscreen ? (
                  <Minimize2 className="h-4 w-4" />
                ) : (
                  <Maximize2 className="h-4 w-4" />
                )}
              </Button>
            )}
            <Button variant="outline" size="icon" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Breadcrumb navigation */}
        <BreadcrumbNavigation
          pathId={pathId}
          variant="compact"
          maxItems={4}
        />
      </div>

      {/* Summary metrics */}
      <div className="flex-shrink-0 p-4 border-b">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {mockDetailData.metrics.map((metric, index) => (
            <Card key={index} className="p-3">
              <div className="flex flex-col space-y-1">
                <span className="text-xs text-muted-foreground">{metric.label}</span>
                <div className="flex items-baseline gap-2">
                  <span className="text-lg font-semibold">{metric.value}</span>
                  {metric.change && (
                    <Badge
                      variant={metric.trend === 'up' ? 'default' : metric.trend === 'down' ? 'destructive' : 'secondary'}
                      className="text-xs"
                    >
                      {metric.change}
                    </Badge>
                  )}
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>

      {/* Content tabs */}
      <div className="flex-1 overflow-hidden">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full flex flex-col">
          <TabsList className="flex-shrink-0 grid w-full grid-cols-3 mx-4 mt-4">
            <TabsTrigger value="table" className="flex items-center gap-2">
              <Database className="h-4 w-4" />
              Data Table
            </TabsTrigger>
            <TabsTrigger value="chart" className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              Visualizations
            </TabsTrigger>
            <TabsTrigger value="details" className="flex items-center gap-2">
              <Eye className="h-4 w-4" />
              Details
            </TabsTrigger>
          </TabsList>

          {/* Table view */}
          <TabsContent value="table" className="flex-1 overflow-hidden">
            <ScrollArea className="h-full">
              <div className="p-4">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-medium">
                    Data Records ({mockDetailData.table_data.length})
                  </h3>
                  <div className="flex items-center gap-2">
                    <Button variant="outline" size="sm" onClick={() => handleExport('csv')}>
                      <Download className="mr-2 h-4 w-4" />
                      Export CSV
                    </Button>
                  </div>
                </div>

                <Card>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Subject ID</TableHead>
                        <TableHead>Visit</TableHead>
                        <TableHead>Date</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead className="text-right">Value</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {mockDetailData.table_data.map((row) => (
                        <TableRow key={row.id}>
                          <TableCell className="font-mono text-sm">{row.subject_id}</TableCell>
                          <TableCell>{row.visit_number}</TableCell>
                          <TableCell>{row.visit_date}</TableCell>
                          <TableCell>
                            <Badge
                              variant={
                                row.status === 'Completed' ? 'default' :
                                row.status === 'In Progress' ? 'secondary' : 'outline'
                              }
                            >
                              {row.status}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-right">{row.value}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </Card>
              </div>
            </ScrollArea>
          </TabsContent>

          {/* Chart view */}
          <TabsContent value="chart" className="flex-1 overflow-hidden">
            <ScrollArea className="h-full">
              <div className="p-4 space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-medium">Data Visualizations</h3>
                  <Button variant="outline" size="sm" onClick={() => handleExport('pdf')}>
                    <Download className="mr-2 h-4 w-4" />
                    Export PDF
                  </Button>
                </div>

                {/* Mock chart widget */}
                <Card className="p-4">
                  <div className="h-64 flex items-center justify-center bg-muted/30 rounded">
                    <div className="text-center">
                      <BarChart3 className="h-12 w-12 mx-auto text-muted-foreground mb-2" />
                      <p className="text-sm text-muted-foreground">
                        Chart visualization would render here
                      </p>
                      <p className="text-xs text-muted-foreground mt-1">
                        Data: {mockDetailData.chart_data.categories.length} time periods
                      </p>
                    </div>
                  </div>
                </Card>

                {/* Additional chart placeholder */}
                <Card className="p-4">
                  <div className="h-48 flex items-center justify-center bg-muted/30 rounded">
                    <div className="text-center">
                      <BarChart3 className="h-10 w-10 mx-auto text-muted-foreground mb-2" />
                      <p className="text-sm text-muted-foreground">
                        Additional chart visualization
                      </p>
                    </div>
                  </div>
                </Card>
              </div>
            </ScrollArea>
          </TabsContent>

          {/* Details view */}
          <TabsContent value="details" className="flex-1 overflow-hidden">
            <ScrollArea className="h-full">
              <div className="p-4 space-y-4">
                <h3 className="text-sm font-medium">Detailed Information</h3>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Drill-down Context</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-muted-foreground">Field:</span>
                        <span className="ml-2 font-mono">{currentLevel.field}</span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Value:</span>
                        <span className="ml-2">{currentLevel.value}</span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Level:</span>
                        <span className="ml-2">{currentLevel.level + 1}</span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Widget:</span>
                        <span className="ml-2">{currentLevel.widget_type}</span>
                      </div>
                    </div>

                    {currentLevel.context && (
                      <div>
                        <span className="text-sm text-muted-foreground">Additional Context:</span>
                        <pre className="mt-2 text-xs bg-muted p-2 rounded overflow-x-auto">
                          {JSON.stringify(currentLevel.context, null, 2)}
                        </pre>
                      </div>
                    )}
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Navigation Path</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {breadcrumbs.map((level, index) => (
                        <div
                          key={level.id}
                          className={cn(
                            "flex items-center gap-2 p-2 rounded",
                            index === breadcrumbs.length - 1 && "bg-muted"
                          )}
                        >
                          <div className="flex items-center gap-2 text-sm">
                            <Badge variant="outline" className="text-xs">
                              {index + 1}
                            </Badge>
                            <span className="font-mono text-xs">{level.field}</span>
                            <ChevronRight className="h-3 w-3 text-muted-foreground" />
                            <span>{level.title}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>
            </ScrollArea>
          </TabsContent>
        </Tabs>
      </div>

      {/* Footer actions */}
      <div className="flex-shrink-0 border-t p-4">
        <div className="flex items-center justify-between">
          <div className="text-xs text-muted-foreground">
            Showing detailed view for {currentLevel.field}: {currentLevel.value}
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" onClick={handleClear}>
              Clear Drill-down
            </Button>
            <Button onClick={onClose}>
              Close
            </Button>
          </div>
        </div>
      </div>
    </div>
  );

  // Render based on variant
  if (variant === 'dialog') {
    return (
      <Dialog open={isOpen} onOpenChange={onClose}>
        <DialogContent className="max-w-4xl h-[80vh] p-0">
          {content}
        </DialogContent>
      </Dialog>
    );
  }

  if (variant === 'fullscreen') {
    if (!isOpen) return null;
    return (
      <div className="fixed inset-0 z-50 bg-background">
        {content}
      </div>
    );
  }

  // Default to sheet
  return (
    <Sheet open={isOpen} onOpenChange={onClose}>
      <SheetContent side="right" className="w-full sm:w-[600px] lg:w-[800px] p-0">
        {content}
      </SheetContent>
    </Sheet>
  );
}

// Quick detail view for inline display
export function QuickDetailView({
  pathId,
  className,
}: {
  pathId?: string;
  className?: string;
}) {
  const { getCurrentLevel, state } = useDrillDownManager();
  
  const currentLevel = getCurrentLevel(pathId);
  
  if (!currentLevel) return null;

  return (
    <Card className={cn("p-3", className)}>
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Badge variant="secondary" className="text-xs">
            Level {currentLevel.level + 1}
          </Badge>
          <span className="text-xs text-muted-foreground">
            {currentLevel.widget_type}
          </span>
        </div>
        <div>
          <h4 className="text-sm font-medium">{currentLevel.title}</h4>
          <p className="text-xs text-muted-foreground">
            {currentLevel.field}: {currentLevel.value}
          </p>
        </div>
      </div>
    </Card>
  );
}