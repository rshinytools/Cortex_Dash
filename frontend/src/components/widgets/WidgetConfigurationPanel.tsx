// ABOUTME: Widget configuration panel for mapping fields and setting parameters
// ABOUTME: Allows users to configure widget data sources, field mappings, and display options

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Settings2Icon,
  DatabaseIcon,
  LinkIcon,
  PaletteIcon,
  AlertCircleIcon,
  CheckCircle2Icon,
  PlusIcon,
  TrashIcon,
  RefreshCwIcon,
} from 'lucide-react';

interface WidgetConfigurationPanelProps {
  widgetType: string;
  widgetId?: string;
  studyId: string;
  currentConfig?: any;
  dataContract?: any;
  availableDatasets?: Array<{
    id: string;
    name: string;
    description?: string;
    fields: Array<{
      name: string;
      type: string;
      description?: string;
    }>;
  }>;
  onSave: (config: any) => void;
  onCancel: () => void;
  onValidate?: (config: any) => Promise<{ valid: boolean; errors: string[] }>;
}

export const WidgetConfigurationPanel: React.FC<WidgetConfigurationPanelProps> = ({
  widgetType,
  widgetId,
  studyId,
  currentConfig = {},
  dataContract,
  availableDatasets = [],
  onSave,
  onCancel,
  onValidate,
}) => {
  const [config, setConfig] = useState(currentConfig);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [isValidating, setIsValidating] = useState(false);
  const [activeTab, setActiveTab] = useState('data');

  // Initialize config with current values
  useEffect(() => {
    setConfig({
      field_mappings: currentConfig.field_mappings || {},
      primary_dataset: currentConfig.primary_dataset || '',
      aggregation_type: currentConfig.aggregation_type || '',
      display_config: currentConfig.display_config || {},
      filters: currentConfig.filters || [],
      joins: currentConfig.joins || [],
      ...currentConfig,
    });
  }, [currentConfig]);

  const handleFieldMapping = (fieldName: string, sourceField: string, dataset?: string) => {
    setConfig((prev: any) => ({
      ...prev,
      field_mappings: {
        ...prev.field_mappings,
        [fieldName]: {
          source_field: sourceField,
          dataset: dataset || prev.primary_dataset,
        },
      },
    }));
  };

  const handleDisplayConfig = (key: string, value: any) => {
    setConfig((prev: any) => ({
      ...prev,
      display_config: {
        ...prev.display_config,
        [key]: value,
      },
    }));
  };

  const addFilter = () => {
    setConfig((prev: any) => ({
      ...prev,
      filters: [
        ...prev.filters,
        { field: '', operator: 'equals', value: '' },
      ],
    }));
  };

  const removeFilter = (index: number) => {
    setConfig((prev: any) => ({
      ...prev,
      filters: prev.filters.filter((_: any, i: number) => i !== index),
    }));
  };

  const addJoin = () => {
    setConfig((prev: any) => ({
      ...prev,
      joins: [
        ...prev.joins,
        { dataset: '', type: 'inner', left_key: '', right_key: '' },
      ],
    }));
  };

  const removeJoin = (index: number) => {
    setConfig((prev: any) => ({
      ...prev,
      joins: prev.joins.filter((_: any, i: number) => i !== index),
    }));
  };

  const handleValidate = async () => {
    if (!onValidate) return;

    setIsValidating(true);
    setValidationErrors([]);

    try {
      const result = await onValidate(config);
      if (!result.valid) {
        setValidationErrors(result.errors);
      } else {
        setValidationErrors([]);
      }
    } catch (error) {
      setValidationErrors(['Validation failed: ' + (error as Error).message]);
    } finally {
      setIsValidating(false);
    }
  };

  const handleSave = () => {
    if (validationErrors.length === 0) {
      onSave(config);
    }
  };

  const renderDataTab = () => (
    <ScrollArea className="h-[500px] pr-4">
      <div className="space-y-6">
        {/* Primary Dataset Selection */}
        <div>
          <Label htmlFor="primary-dataset">Primary Dataset</Label>
          <Select
            value={config.primary_dataset}
            onValueChange={(value) => setConfig({ ...config, primary_dataset: value })}
          >
            <SelectTrigger id="primary-dataset">
              <SelectValue placeholder="Select primary dataset" />
            </SelectTrigger>
            <SelectContent>
              {availableDatasets.map((dataset) => (
                <SelectItem key={dataset.id} value={dataset.id}>
                  {dataset.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Required Fields Mapping */}
        {dataContract?.required_fields && (
          <div>
            <h4 className="font-medium mb-3 flex items-center gap-2">
              <DatabaseIcon className="h-4 w-4" />
              Required Fields
            </h4>
            <div className="space-y-3">
              {dataContract.required_fields.map((field: any) => (
                <div key={field.name} className="grid grid-cols-2 gap-3">
                  <div>
                    <Label className="text-sm">
                      {field.description || field.name}
                      <Badge variant="outline" className="ml-2 text-xs">
                        {field.type}
                      </Badge>
                    </Label>
                  </div>
                  <Select
                    value={config.field_mappings[field.name]?.source_field || ''}
                    onValueChange={(value) => handleFieldMapping(field.name, value)}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select field" />
                    </SelectTrigger>
                    <SelectContent>
                      {availableDatasets
                        .find((d) => d.id === config.primary_dataset)
                        ?.fields.filter((f) => f.type === field.type || field.type === 'any')
                        .map((f) => (
                          <SelectItem key={f.name} value={f.name}>
                            {f.name}
                          </SelectItem>
                        ))}
                    </SelectContent>
                  </Select>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Optional Fields Mapping */}
        {dataContract?.optional_fields && (
          <div>
            <h4 className="font-medium mb-3 flex items-center gap-2">
              <DatabaseIcon className="h-4 w-4" />
              Optional Fields
            </h4>
            <div className="space-y-3">
              {dataContract.optional_fields.map((field: any) => (
                <div key={field.name} className="grid grid-cols-2 gap-3">
                  <div>
                    <Label className="text-sm text-muted-foreground">
                      {field.description || field.name}
                      <Badge variant="secondary" className="ml-2 text-xs">
                        {field.type}
                      </Badge>
                    </Label>
                  </div>
                  <Select
                    value={config.field_mappings[field.name]?.source_field || ''}
                    onValueChange={(value) => handleFieldMapping(field.name, value)}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select field (optional)" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="">None</SelectItem>
                      {availableDatasets
                        .find((d) => d.id === config.primary_dataset)
                        ?.fields.filter((f) => f.type === field.type || field.type === 'any')
                        .map((f) => (
                          <SelectItem key={f.name} value={f.name}>
                            {f.name}
                          </SelectItem>
                        ))}
                    </SelectContent>
                  </Select>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Aggregation Type */}
        {dataContract?.supported_aggregations && (
          <div>
            <Label htmlFor="aggregation-type">Aggregation Type</Label>
            <Select
              value={config.aggregation_type}
              onValueChange={(value) => setConfig({ ...config, aggregation_type: value })}
            >
              <SelectTrigger id="aggregation-type">
                <SelectValue placeholder="Select aggregation" />
              </SelectTrigger>
              <SelectContent>
                {dataContract.supported_aggregations.map((agg: string) => (
                  <SelectItem key={agg} value={agg}>
                    {agg}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}
      </div>
    </ScrollArea>
  );

  const renderFiltersTab = () => (
    <ScrollArea className="h-[500px] pr-4">
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <h4 className="font-medium">Data Filters</h4>
          <Button onClick={addFilter} size="sm" variant="outline">
            <PlusIcon className="h-4 w-4 mr-1" />
            Add Filter
          </Button>
        </div>

        {config.filters.map((filter: any, index: number) => (
          <Card key={index}>
            <CardContent className="pt-4">
              <div className="grid grid-cols-3 gap-3">
                <Input
                  placeholder="Field"
                  value={filter.field}
                  onChange={(e) => {
                    const newFilters = [...config.filters];
                    newFilters[index].field = e.target.value;
                    setConfig({ ...config, filters: newFilters });
                  }}
                />
                <Select
                  value={filter.operator}
                  onValueChange={(value) => {
                    const newFilters = [...config.filters];
                    newFilters[index].operator = value;
                    setConfig({ ...config, filters: newFilters });
                  }}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="equals">Equals</SelectItem>
                    <SelectItem value="not_equals">Not Equals</SelectItem>
                    <SelectItem value="greater_than">Greater Than</SelectItem>
                    <SelectItem value="less_than">Less Than</SelectItem>
                    <SelectItem value="contains">Contains</SelectItem>
                    <SelectItem value="in">In List</SelectItem>
                  </SelectContent>
                </Select>
                <div className="flex gap-2">
                  <Input
                    placeholder="Value"
                    value={filter.value}
                    onChange={(e) => {
                      const newFilters = [...config.filters];
                      newFilters[index].value = e.target.value;
                      setConfig({ ...config, filters: newFilters });
                    }}
                  />
                  <Button
                    onClick={() => removeFilter(index)}
                    size="icon"
                    variant="ghost"
                  >
                    <TrashIcon className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </ScrollArea>
  );

  const renderJoinsTab = () => (
    <ScrollArea className="h-[500px] pr-4">
      <div className="space-y-4">
        {dataContract?.supports_joins ? (
          <>
            <div className="flex justify-between items-center">
              <h4 className="font-medium">Dataset Joins</h4>
              <Button
                onClick={addJoin}
                size="sm"
                variant="outline"
                disabled={config.joins.length >= (dataContract.max_join_datasets || 0)}
              >
                <PlusIcon className="h-4 w-4 mr-1" />
                Add Join
              </Button>
            </div>

            {config.joins.map((join: any, index: number) => (
              <Card key={index}>
                <CardContent className="pt-4">
                  <div className="space-y-3">
                    <div className="grid grid-cols-2 gap-3">
                      <Select
                        value={join.dataset}
                        onValueChange={(value) => {
                          const newJoins = [...config.joins];
                          newJoins[index].dataset = value;
                          setConfig({ ...config, joins: newJoins });
                        }}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select dataset" />
                        </SelectTrigger>
                        <SelectContent>
                          {availableDatasets
                            .filter((d) => d.id !== config.primary_dataset)
                            .map((dataset) => (
                              <SelectItem key={dataset.id} value={dataset.id}>
                                {dataset.name}
                              </SelectItem>
                            ))}
                        </SelectContent>
                      </Select>
                      <Select
                        value={join.type}
                        onValueChange={(value) => {
                          const newJoins = [...config.joins];
                          newJoins[index].type = value;
                          setConfig({ ...config, joins: newJoins });
                        }}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="inner">Inner Join</SelectItem>
                          <SelectItem value="left">Left Join</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <Input
                        placeholder="Left key (primary dataset)"
                        value={join.left_key}
                        onChange={(e) => {
                          const newJoins = [...config.joins];
                          newJoins[index].left_key = e.target.value;
                          setConfig({ ...config, joins: newJoins });
                        }}
                      />
                      <div className="flex gap-2">
                        <Input
                          placeholder="Right key (joined dataset)"
                          value={join.right_key}
                          onChange={(e) => {
                            const newJoins = [...config.joins];
                            newJoins[index].right_key = e.target.value;
                            setConfig({ ...config, joins: newJoins });
                          }}
                        />
                        <Button
                          onClick={() => removeJoin(index)}
                          size="icon"
                          variant="ghost"
                        >
                          <TrashIcon className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </>
        ) : (
          <Alert>
            <AlertCircleIcon className="h-4 w-4" />
            <AlertDescription>
              This widget type does not support dataset joins.
            </AlertDescription>
          </Alert>
        )}
      </div>
    </ScrollArea>
  );

  const renderDisplayTab = () => (
    <ScrollArea className="h-[500px] pr-4">
      <div className="space-y-6">
        <div>
          <Label htmlFor="widget-title">Widget Title</Label>
          <Input
            id="widget-title"
            value={config.display_config.title || ''}
            onChange={(e) => handleDisplayConfig('title', e.target.value)}
            placeholder="Enter widget title"
          />
        </div>

        <div>
          <Label htmlFor="widget-description">Description</Label>
          <Input
            id="widget-description"
            value={config.display_config.description || ''}
            onChange={(e) => handleDisplayConfig('description', e.target.value)}
            placeholder="Enter widget description"
          />
        </div>

        {/* Widget-specific display options */}
        {widgetType === 'kpi_metric_card' && (
          <>
            <div>
              <Label htmlFor="format">Value Format</Label>
              <Select
                value={config.display_config.format || 'number'}
                onValueChange={(value) => handleDisplayConfig('format', value)}
              >
                <SelectTrigger id="format">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="number">Number</SelectItem>
                  <SelectItem value="percentage">Percentage</SelectItem>
                  <SelectItem value="currency">Currency</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="decimals">Decimal Places</Label>
              <Input
                id="decimals"
                type="number"
                min="0"
                max="4"
                value={config.display_config.decimals || 0}
                onChange={(e) => handleDisplayConfig('decimals', parseInt(e.target.value))}
              />
            </div>

            <div className="flex items-center space-x-2">
              <Switch
                id="show-comparison"
                checked={config.display_config.show_comparison || false}
                onCheckedChange={(checked) => handleDisplayConfig('show_comparison', checked)}
              />
              <Label htmlFor="show-comparison">Show Comparison</Label>
            </div>

            <div className="flex items-center space-x-2">
              <Switch
                id="show-trend"
                checked={config.display_config.show_trend || false}
                onCheckedChange={(checked) => handleDisplayConfig('show_trend', checked)}
              />
              <Label htmlFor="show-trend">Show Trend</Label>
            </div>
          </>
        )}

        {widgetType === 'time_series_chart' && (
          <>
            <div>
              <Label htmlFor="chart-type">Chart Type</Label>
              <Select
                value={config.display_config.chart_type || 'line'}
                onValueChange={(value) => handleDisplayConfig('chart_type', value)}
              >
                <SelectTrigger id="chart-type">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="line">Line</SelectItem>
                  <SelectItem value="area">Area</SelectItem>
                  <SelectItem value="step">Step</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="time-granularity">Time Granularity</Label>
              <Select
                value={config.time_granularity || 'day'}
                onValueChange={(value) => setConfig({ ...config, time_granularity: value })}
              >
                <SelectTrigger id="time-granularity">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="hour">Hour</SelectItem>
                  <SelectItem value="day">Day</SelectItem>
                  <SelectItem value="week">Week</SelectItem>
                  <SelectItem value="month">Month</SelectItem>
                  <SelectItem value="quarter">Quarter</SelectItem>
                  <SelectItem value="year">Year</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-center space-x-2">
              <Switch
                id="cumulative"
                checked={config.cumulative || false}
                onCheckedChange={(checked) => setConfig({ ...config, cumulative: checked })}
              />
              <Label htmlFor="cumulative">Cumulative Values</Label>
            </div>
          </>
        )}

        {widgetType === 'distribution_chart' && (
          <>
            <div>
              <Label htmlFor="chart-subtype">Chart Subtype</Label>
              <Select
                value={config.chart_subtype || 'bar'}
                onValueChange={(value) => setConfig({ ...config, chart_subtype: value })}
              >
                <SelectTrigger id="chart-subtype">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="bar">Bar Chart</SelectItem>
                  <SelectItem value="horizontal_bar">Horizontal Bar</SelectItem>
                  <SelectItem value="pie">Pie Chart</SelectItem>
                  <SelectItem value="donut">Donut Chart</SelectItem>
                  <SelectItem value="stacked_bar">Stacked Bar</SelectItem>
                  <SelectItem value="grouped_bar">Grouped Bar</SelectItem>
                  <SelectItem value="histogram">Histogram</SelectItem>
                  <SelectItem value="pareto">Pareto Chart</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="top-n">Top N Categories</Label>
              <Input
                id="top-n"
                type="number"
                min="0"
                value={config.top_n || ''}
                onChange={(e) => setConfig({ ...config, top_n: parseInt(e.target.value) || undefined })}
                placeholder="Show all"
              />
            </div>
          </>
        )}
      </div>
    </ScrollArea>
  );

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Settings2Icon className="h-5 w-5" />
          Configure {widgetType.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
        </CardTitle>
        <CardDescription>
          Map data fields and configure display options for this widget
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="data">
              <DatabaseIcon className="h-4 w-4 mr-2" />
              Data
            </TabsTrigger>
            <TabsTrigger value="filters">
              <Settings2Icon className="h-4 w-4 mr-2" />
              Filters
            </TabsTrigger>
            <TabsTrigger value="joins">
              <LinkIcon className="h-4 w-4 mr-2" />
              Joins
            </TabsTrigger>
            <TabsTrigger value="display">
              <PaletteIcon className="h-4 w-4 mr-2" />
              Display
            </TabsTrigger>
          </TabsList>

          <div className="mt-6">
            <TabsContent value="data">{renderDataTab()}</TabsContent>
            <TabsContent value="filters">{renderFiltersTab()}</TabsContent>
            <TabsContent value="joins">{renderJoinsTab()}</TabsContent>
            <TabsContent value="display">{renderDisplayTab()}</TabsContent>
          </div>
        </Tabs>

        {/* Validation Errors */}
        {validationErrors.length > 0 && (
          <Alert variant="destructive" className="mt-4">
            <AlertCircleIcon className="h-4 w-4" />
            <AlertDescription>
              <div className="space-y-1">
                {validationErrors.map((error, index) => (
                  <div key={index}>{error}</div>
                ))}
              </div>
            </AlertDescription>
          </Alert>
        )}

        {/* Actions */}
        <Separator className="my-6" />
        <div className="flex justify-between">
          <Button
            onClick={handleValidate}
            variant="outline"
            disabled={isValidating}
          >
            {isValidating ? (
              <>
                <RefreshCwIcon className="h-4 w-4 mr-2 animate-spin" />
                Validating...
              </>
            ) : (
              <>
                <CheckCircle2Icon className="h-4 w-4 mr-2" />
                Validate
              </>
            )}
          </Button>
          <div className="flex gap-3">
            <Button onClick={onCancel} variant="outline">
              Cancel
            </Button>
            <Button
              onClick={handleSave}
              disabled={validationErrors.length > 0}
            >
              Save Configuration
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};