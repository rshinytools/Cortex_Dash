// ABOUTME: Mappings Tab - Manage field mappings for widgets
// ABOUTME: Shows mapping status and allows updating mappings for existing and new widgets

'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
  GitBranch,
  CheckCircle,
  AlertCircle,
  XCircle,
  Settings,
  Sparkles,
  ArrowRight
} from 'lucide-react';
import { useState } from 'react';
import { useToast } from '@/hooks/use-toast';
import { FieldMappingStep } from '@/components/study/initialization-wizard/steps/field-mapping';

interface MappingsTabProps {
  study: any;
  onUpdate: () => void;
}

export function MappingsTab({ study, onUpdate }: MappingsTabProps) {
  const { toast } = useToast();
  const [selectedWidget, setSelectedWidget] = useState<string | null>(null);
  const [showOnlyUnmapped, setShowOnlyUnmapped] = useState(false);

  // Mock widget mapping data
  const widgetMappings = [
    {
      id: 'widget-1',
      name: 'Total Enrollment',
      type: 'kpi_card',
      status: 'mapped',
      requiredFields: 3,
      mappedFields: 3,
      isNew: false,
    },
    {
      id: 'widget-2',
      name: 'SAE Count',
      type: 'kpi_card',
      status: 'mapped',
      requiredFields: 2,
      mappedFields: 2,
      isNew: false,
    },
    {
      id: 'widget-3',
      name: 'Site Performance',
      type: 'table',
      status: 'partial',
      requiredFields: 5,
      mappedFields: 3,
      isNew: false,
    },
    {
      id: 'widget-4',
      name: 'Dropout Rate',
      type: 'kpi_card',
      status: 'unmapped',
      requiredFields: 2,
      mappedFields: 0,
      isNew: true,
    },
    {
      id: 'widget-5',
      name: 'Lab Results',
      type: 'time_series',
      status: 'unmapped',
      requiredFields: 3,
      mappedFields: 0,
      isNew: true,
    },
  ];

  const totalWidgets = widgetMappings.length;
  const mappedWidgets = widgetMappings.filter(w => w.status === 'mapped').length;
  const partialWidgets = widgetMappings.filter(w => w.status === 'partial').length;
  const unmappedWidgets = widgetMappings.filter(w => w.status === 'unmapped').length;
  const completionPercentage = Math.round((mappedWidgets / totalWidgets) * 100);

  const handleConfigureMapping = (widgetId: string) => {
    setSelectedWidget(widgetId);
    // In real implementation, this would open the mapping interface
    toast({
      title: 'Opening Mapping Interface',
      description: `Configure mappings for widget ${widgetId}`,
    });
  };

  const handleSaveMappings = async () => {
    toast({
      title: 'Success',
      description: 'Mappings saved successfully.',
    });
    onUpdate();
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'mapped':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'partial':
        return <AlertCircle className="h-4 w-4 text-yellow-500" />;
      case 'unmapped':
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return null;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'mapped':
        return <Badge className="bg-green-100 text-green-800">Fully Mapped</Badge>;
      case 'partial':
        return <Badge className="bg-yellow-100 text-yellow-800">Partially Mapped</Badge>;
      case 'unmapped':
        return <Badge className="bg-red-100 text-red-800">Not Mapped</Badge>;
      default:
        return null;
    }
  };

  return (
    <div className="space-y-6">
      {/* Mapping Overview */}
      <Card className="bg-white dark:bg-slate-900">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <GitBranch className="h-5 w-5" />
            Mapping Status Overview
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span>Overall Completion</span>
                <span className="font-medium">{completionPercentage}%</span>
              </div>
              <Progress value={completionPercentage} className="h-2" />
            </div>
            
            <div className="grid grid-cols-3 gap-4 pt-4">
              <div className="text-center">
                <div className="flex items-center justify-center gap-2 mb-1">
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  <span className="text-2xl font-bold">{mappedWidgets}</span>
                </div>
                <p className="text-sm text-gray-500 dark:text-slate-500">Fully Mapped</p>
              </div>
              <div className="text-center">
                <div className="flex items-center justify-center gap-2 mb-1">
                  <AlertCircle className="h-5 w-5 text-yellow-500" />
                  <span className="text-2xl font-bold">{partialWidgets}</span>
                </div>
                <p className="text-sm text-gray-500 dark:text-slate-500">Partially Mapped</p>
              </div>
              <div className="text-center">
                <div className="flex items-center justify-center gap-2 mb-1">
                  <XCircle className="h-5 w-5 text-red-500" />
                  <span className="text-2xl font-bold">{unmappedWidgets}</span>
                </div>
                <p className="text-sm text-gray-500 dark:text-slate-500">Need Mapping</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* New Widgets Alert */}
      {unmappedWidgets > 0 && (
        <Alert className="border-yellow-200 bg-yellow-50 dark:bg-yellow-950/20">
          <Sparkles className="h-4 w-4 text-yellow-600" />
          <AlertDescription className="text-yellow-800 dark:text-yellow-200">
            <strong>{unmappedWidgets} new widget(s)</strong> have been added to the template and need mapping configuration.
          </AlertDescription>
        </Alert>
      )}

      {/* Widget Mapping List */}
      <Card className="bg-white dark:bg-slate-900">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Widget Mappings</CardTitle>
              <CardDescription>
                Configure field mappings for each widget
              </CardDescription>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowOnlyUnmapped(!showOnlyUnmapped)}
            >
              {showOnlyUnmapped ? 'Show All' : 'Show Unmapped Only'}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {widgetMappings
              .filter(widget => !showOnlyUnmapped || widget.status !== 'mapped')
              .map((widget) => (
                <div
                  key={widget.id}
                  className="flex items-center justify-between p-4 rounded-lg border border-gray-200 dark:border-slate-800 hover:bg-gray-50 dark:hover:bg-slate-800/50 transition-colors"
                >
                  <div className="flex items-center gap-4">
                    {getStatusIcon(widget.status)}
                    <div>
                      <div className="flex items-center gap-2">
                        <p className="font-medium">{widget.name}</p>
                        {widget.isNew && (
                          <Badge variant="secondary" className="text-xs">
                            <Sparkles className="h-3 w-3 mr-1" />
                            New
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm text-gray-500 dark:text-slate-500">
                        Type: {widget.type} • {widget.mappedFields}/{widget.requiredFields} fields mapped
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {getStatusBadge(widget.status)}
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleConfigureMapping(widget.id)}
                    >
                      <Settings className="h-4 w-4 mr-1" />
                      Configure
                    </Button>
                  </div>
                </div>
              ))}
          </div>
        </CardContent>
      </Card>

      {/* Mapping Interface (Placeholder) */}
      {selectedWidget && (
        <Card className="bg-white dark:bg-slate-900">
          <CardHeader>
            <CardTitle>Configure Widget Mapping</CardTitle>
            <CardDescription>
              Map required fields to available data columns
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                The field mapping interface will be displayed here, reusing the FieldMappingStep component from initialization.
              </AlertDescription>
            </Alert>
            <div className="mt-4 flex justify-end">
              <Button onClick={handleSaveMappings} className="bg-blue-600 hover:bg-blue-700">
                Save Mappings
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}