// ABOUTME: Configuration component for the Metrics Card widget
// ABOUTME: Allows users to configure aggregation, filters, comparison, and display options

"use client";

import { useState, useEffect } from "react";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Plus, Trash2 } from "lucide-react";

interface MetricsCardConfigProps {
  config: any;
  datasets?: Array<{
    name: string;
    fields: Array<{
      name: string;
      type: "string" | "number" | "date" | "boolean";
    }>;
  }>;
  onChange: (config: any) => void;
}

const aggregationMethods = [
  { value: "COUNT", label: "Count", requiresField: false },
  { value: "COUNT_DISTINCT", label: "Count Distinct", requiresField: true },
  { value: "SUM", label: "Sum", requiresField: true },
  { value: "AVG", label: "Average", requiresField: true },
  { value: "MIN", label: "Minimum", requiresField: true },
  { value: "MAX", label: "Maximum", requiresField: true },
  { value: "MEDIAN", label: "Median", requiresField: true },
];

const filterOperators = {
  string: [
    { value: "=", label: "Equals" },
    { value: "!=", label: "Not Equals" },
    { value: "CONTAINS", label: "Contains" },
    { value: "NOT CONTAINS", label: "Not Contains" },
    { value: "IS NULL", label: "Is Empty" },
    { value: "IS NOT NULL", label: "Is Not Empty" },
    { value: "IN", label: "In List" },
    { value: "NOT IN", label: "Not In List" },
  ],
  number: [
    { value: "=", label: "Equals" },
    { value: "!=", label: "Not Equals" },
    { value: ">", label: "Greater Than" },
    { value: ">=", label: "Greater Than or Equal" },
    { value: "<", label: "Less Than" },
    { value: "<=", label: "Less Than or Equal" },
    { value: "IS NULL", label: "Is Empty" },
    { value: "IS NOT NULL", label: "Is Not Empty" },
  ],
  date: [
    { value: "=", label: "Equals" },
    { value: "!=", label: "Not Equals" },
    { value: ">", label: "After" },
    { value: ">=", label: "On or After" },
    { value: "<", label: "Before" },
    { value: "<=", label: "On or Before" },
    { value: "IS NULL", label: "Is Empty" },
    { value: "IS NOT NULL", label: "Is Not Empty" },
  ],
  boolean: [
    { value: "=", label: "Equals" },
    { value: "!=", label: "Not Equals" },
  ],
};

const displayFormats = [
  { value: "number", label: "Number" },
  { value: "percentage", label: "Percentage" },
  { value: "currency", label: "Currency" },
  { value: "decimal", label: "Decimal" },
];

const colorOptions = [
  { value: "default", label: "Default" },
  { value: "primary", label: "Primary" },
  { value: "success", label: "Success (Green)" },
  { value: "warning", label: "Warning (Yellow)" },
  { value: "danger", label: "Danger (Red)" },
  { value: "info", label: "Info (Blue)" },
];

const iconOptions = [
  { value: "", label: "None" },
  { value: "users", label: "Users" },
  { value: "activity", label: "Activity" },
  { value: "trending-up", label: "Trending Up" },
  { value: "trending-down", label: "Trending Down" },
  { value: "alert-circle", label: "Alert" },
  { value: "check-circle", label: "Check" },
  { value: "info", label: "Info" },
  { value: "bar-chart", label: "Bar Chart" },
  { value: "pie-chart", label: "Pie Chart" },
  { value: "calendar", label: "Calendar" },
  { value: "clock", label: "Clock" },
  { value: "database", label: "Database" },
  { value: "file-text", label: "File" },
  { value: "heart", label: "Heart" },
  { value: "shield", label: "Shield" },
  { value: "star", label: "Star" },
  { value: "target", label: "Target" },
  { value: "zap", label: "Zap" },
];

export function MetricsCardConfig({ config, datasets = [], onChange }: MetricsCardConfigProps) {
  const [localConfig, setLocalConfig] = useState(config);

  useEffect(() => {
    setLocalConfig(config);
  }, [config]);

  const updateConfig = (updates: any) => {
    const newConfig = { ...localConfig, ...updates };
    setLocalConfig(newConfig);
    onChange(newConfig);
  };

  const updateNestedConfig = (path: string[], value: any) => {
    const newConfig = { ...localConfig };
    let current = newConfig;
    
    for (let i = 0; i < path.length - 1; i++) {
      if (!current[path[i]]) {
        current[path[i]] = {};
      }
      current = current[path[i]];
    }
    
    current[path[path.length - 1]] = value;
    setLocalConfig(newConfig);
    onChange(newConfig);
  };

  const addFilter = () => {
    const filters = localConfig.filters || [];
    const newFilter = {
      logic: filters.length === 0 ? "AND" : filters[filters.length - 1].logic,
      conditions: [{ field: "", operator: "=", value: "" }],
    };
    updateConfig({ filters: [...filters, newFilter] });
  };

  const removeFilter = (index: number) => {
    const filters = localConfig.filters || [];
    updateConfig({ filters: filters.filter((_filter: any, i: number) => i !== index) });
  };

  const updateFilter = (index: number, updates: any) => {
    const filters = localConfig.filters || [];
    filters[index] = { ...filters[index], ...updates };
    updateConfig({ filters });
  };

  const addCondition = (filterIndex: number) => {
    const filters = localConfig.filters || [];
    const conditions = filters[filterIndex].conditions || [];
    conditions.push({ field: "", operator: "=", value: "" });
    updateFilter(filterIndex, { conditions });
  };

  const removeCondition = (filterIndex: number, conditionIndex: number) => {
    const filters = localConfig.filters || [];
    const conditions = filters[filterIndex].conditions || [];
    updateFilter(filterIndex, {
      conditions: conditions.filter((_condition: any, i: number) => i !== conditionIndex),
    });
  };

  const updateCondition = (filterIndex: number, conditionIndex: number, updates: any) => {
    const filters = localConfig.filters || [];
    const conditions = filters[filterIndex].conditions || [];
    conditions[conditionIndex] = { ...conditions[conditionIndex], ...updates };
    updateFilter(filterIndex, { conditions });
  };

  const selectedMethod = aggregationMethods.find(
    (m) => m.value === localConfig.aggregation?.method
  );

  return (
    <div className="space-y-6">
      <div>
        <Label htmlFor="title">Title</Label>
        <Input
          id="title"
          value={localConfig.title || ""}
          onChange={(e) => updateConfig({ title: e.target.value })}
          placeholder="Enter metric title"
        />
      </div>

      <div>
        <Label htmlFor="subtitle">Subtitle (optional)</Label>
        <Input
          id="subtitle"
          value={localConfig.subtitle || ""}
          onChange={(e) => updateConfig({ subtitle: e.target.value })}
          placeholder="Enter optional subtitle"
        />
      </div>

      <div className="space-y-4">
        <div>
          <Label>Data Mode</Label>
          <Select
            value={localConfig.dataMode || "dynamic"}
            onValueChange={(value) => updateConfig({ dataMode: value })}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="dynamic">Dynamic (From Data Source)</SelectItem>
              <SelectItem value="static">Static (Fixed Value)</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {localConfig.dataMode === "static" ? (
          <div className="space-y-4">
            <div>
              <Label htmlFor="static-value">Static Value</Label>
              <Input
                id="static-value"
                type="number"
                value={localConfig.staticValue?.value || ""}
                onChange={(e) => updateNestedConfig(["staticValue", "value"], parseFloat(e.target.value) || 0)}
                placeholder="Enter a numeric value"
              />
            </div>

            {localConfig.comparison?.enabled && (
              <div>
                <Label htmlFor="static-comparison">Comparison Value (Optional)</Label>
                <Input
                  id="static-comparison"
                  type="number"
                  value={localConfig.staticValue?.comparisonValue || ""}
                  onChange={(e) => updateNestedConfig(["staticValue", "comparisonValue"], parseFloat(e.target.value) || 0)}
                  placeholder="Enter comparison value"
                />
              </div>
            )}
          </div>
        ) : null}
      </div>

      <Tabs defaultValue="aggregation" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="aggregation" disabled={localConfig.dataMode === "static"}>
            Aggregation
          </TabsTrigger>
          <TabsTrigger value="filters" disabled={localConfig.dataMode === "static"}>
            Filters
          </TabsTrigger>
          <TabsTrigger value="comparison">Comparison</TabsTrigger>
          <TabsTrigger value="display">Display</TabsTrigger>
        </TabsList>

        <TabsContent value="aggregation" className="space-y-4">
          <div>
            <Label>Aggregation Method</Label>
            <Select
              value={localConfig.aggregation?.method || "COUNT"}
              onValueChange={(value) =>
                updateNestedConfig(["aggregation", "method"], value)
              }
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {aggregationMethods.map((method) => (
                  <SelectItem key={method.value} value={method.value}>
                    {method.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {selectedMethod?.requiresField && (
            <div>
              <Label>Field to Aggregate</Label>
              <Select
                value={localConfig.aggregation?.field || ""}
                onValueChange={(value) =>
                  updateNestedConfig(["aggregation", "field"], value)
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select a field" />
                </SelectTrigger>
                <SelectContent>
                  {datasets.flatMap((dataset) =>
                    dataset.fields
                      .filter((field) => field.type === "number")
                      .map((field) => (
                        <SelectItem
                          key={`${dataset.name}.${field.name}`}
                          value={`${dataset.name}.${field.name}`}
                        >
                          {dataset.name}.{field.name}
                        </SelectItem>
                      ))
                  )}
                </SelectContent>
              </Select>
            </div>
          )}

          {localConfig.aggregation?.method === "COUNT_DISTINCT" && (
            <div>
              <Label>Distinct Field</Label>
              <Select
                value={localConfig.aggregation?.distinctField || ""}
                onValueChange={(value) =>
                  updateNestedConfig(["aggregation", "distinctField"], value)
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select field for distinct count" />
                </SelectTrigger>
                <SelectContent>
                  {datasets.flatMap((dataset) =>
                    dataset.fields.map((field) => (
                      <SelectItem
                        key={`${dataset.name}.${field.name}`}
                        value={`${dataset.name}.${field.name}`}
                      >
                        {dataset.name}.{field.name}
                      </SelectItem>
                    ))
                  )}
                </SelectContent>
              </Select>
            </div>
          )}
        </TabsContent>

        <TabsContent value="filters" className="space-y-4">
          <div className="flex justify-between items-center">
            <Label>Filter Conditions</Label>
            <Button
              variant="outline"
              size="sm"
              onClick={addFilter}
              className="gap-2"
            >
              <Plus className="h-4 w-4" />
              Add Filter Group
            </Button>
          </div>

          {(localConfig.filters || []).map((filter: any, filterIndex: number) => (
            <Accordion key={filterIndex} type="single" collapsible>
              <AccordionItem value={`filter-${filterIndex}`}>
                <AccordionTrigger className="hover:no-underline">
                  <div className="flex items-center justify-between w-full pr-2">
                    <span>Filter Group {filterIndex + 1}</span>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        removeFilter(filterIndex);
                      }}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </AccordionTrigger>
                <AccordionContent className="space-y-4">
                  {filterIndex > 0 && (
                    <div>
                      <Label>Logic Operator</Label>
                      <Select
                        value={filter.logic}
                        onValueChange={(value) => updateFilter(filterIndex, { logic: value })}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="AND">AND</SelectItem>
                          <SelectItem value="OR">OR</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  )}

                  <div className="space-y-4">
                    {(filter.conditions || []).map((condition: any, conditionIndex: number) => (
                      <div key={conditionIndex} className="flex gap-2">
                        <Select
                          value={condition.field}
                          onValueChange={(value) =>
                            updateCondition(filterIndex, conditionIndex, { field: value })
                          }
                        >
                          <SelectTrigger className="w-[200px]">
                            <SelectValue placeholder="Select field" />
                          </SelectTrigger>
                          <SelectContent>
                            {datasets.flatMap((dataset) =>
                              dataset.fields.map((field) => (
                                <SelectItem
                                  key={`${dataset.name}.${field.name}`}
                                  value={`${dataset.name}.${field.name}`}
                                >
                                  {dataset.name}.{field.name}
                                </SelectItem>
                              ))
                            )}
                          </SelectContent>
                        </Select>

                        <Select
                          value={condition.operator}
                          onValueChange={(value) =>
                            updateCondition(filterIndex, conditionIndex, { operator: value })
                          }
                        >
                          <SelectTrigger className="w-[150px]">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {(filterOperators.string || []).map((op) => (
                              <SelectItem key={op.value} value={op.value}>
                                {op.label}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>

                        {!["IS NULL", "IS NOT NULL"].includes(condition.operator) && (
                          <Input
                            value={condition.value || ""}
                            onChange={(e) =>
                              updateCondition(filterIndex, conditionIndex, {
                                value: e.target.value,
                              })
                            }
                            placeholder="Value"
                            className="flex-1"
                          />
                        )}

                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => removeCondition(filterIndex, conditionIndex)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    ))}

                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => addCondition(filterIndex)}
                      className="gap-2"
                    >
                      <Plus className="h-4 w-4" />
                      Add Condition
                    </Button>
                  </div>
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          ))}
        </TabsContent>

        <TabsContent value="comparison" className="space-y-4">
          <div className="flex items-center justify-between">
            <Label htmlFor="comparison-enabled">Enable Comparison</Label>
            <Switch
              id="comparison-enabled"
              checked={localConfig.comparison?.enabled || false}
              onCheckedChange={(checked) =>
                updateNestedConfig(["comparison", "enabled"], checked)
              }
            />
          </div>

          {localConfig.comparison?.enabled && (
            <>
              <div>
                <Label>Comparison Type</Label>
                <Select
                  value={localConfig.comparison?.type || "previous_extract"}
                  onValueChange={(value) =>
                    updateNestedConfig(["comparison", "type"], value)
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="previous_extract">Previous Extract</SelectItem>
                    <SelectItem value="previous_period">Previous Period</SelectItem>
                    <SelectItem value="baseline">Baseline</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="flex items-center justify-between">
                <Label htmlFor="show-percent">Show Percentage Change</Label>
                <Switch
                  id="show-percent"
                  checked={localConfig.comparison?.showPercentChange ?? true}
                  onCheckedChange={(checked) =>
                    updateNestedConfig(["comparison", "showPercentChange"], checked)
                  }
                />
              </div>

              <div className="flex items-center justify-between">
                <Label htmlFor="show-absolute">Show Absolute Change</Label>
                <Switch
                  id="show-absolute"
                  checked={localConfig.comparison?.showAbsoluteChange || false}
                  onCheckedChange={(checked) =>
                    updateNestedConfig(["comparison", "showAbsoluteChange"], checked)
                  }
                />
              </div>
            </>
          )}
        </TabsContent>

        <TabsContent value="display" className="space-y-4">
          <div>
            <Label>Display Format</Label>
            <Select
              value={localConfig.display?.format || "number"}
              onValueChange={(value) => updateNestedConfig(["display", "format"], value)}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {displayFormats.map((format) => (
                  <SelectItem key={format.value} value={format.value}>
                    {format.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label>Decimal Places</Label>
            <Select
              value={String(localConfig.display?.decimals || 0)}
              onValueChange={(value) =>
                updateNestedConfig(["display", "decimals"], parseInt(value))
              }
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {[0, 1, 2, 3, 4, 5, 6].map((num) => (
                  <SelectItem key={num} value={String(num)}>
                    {num}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="prefix">Prefix</Label>
              <Input
                id="prefix"
                value={localConfig.display?.prefix || ""}
                onChange={(e) => updateNestedConfig(["display", "prefix"], e.target.value)}
                placeholder="e.g., $"
              />
            </div>
            <div>
              <Label htmlFor="suffix">Suffix</Label>
              <Input
                id="suffix"
                value={localConfig.display?.suffix || ""}
                onChange={(e) => updateNestedConfig(["display", "suffix"], e.target.value)}
                placeholder="e.g., %"
              />
            </div>
          </div>

          <div className="flex items-center justify-between">
            <Label htmlFor="thousands">Use Thousands Separator</Label>
            <Switch
              id="thousands"
              checked={localConfig.display?.thousandsSeparator ?? true}
              onCheckedChange={(checked) =>
                updateNestedConfig(["display", "thousandsSeparator"], checked)
              }
            />
          </div>

          <div>
            <Label>Icon</Label>
            <Select
              value={localConfig.display?.icon || ""}
              onValueChange={(value) => updateNestedConfig(["display", "icon"], value)}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {iconOptions.map((icon) => (
                  <SelectItem key={icon.value} value={icon.value}>
                    {icon.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label>Color Scheme</Label>
            <Select
              value={localConfig.display?.color || "default"}
              onValueChange={(value) => updateNestedConfig(["display", "color"], value)}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {colorOptions.map((color) => (
                  <SelectItem key={color.value} value={color.value}>
                    {color.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="show-trend">Show Trend Indicator</Label>
              <Switch
                id="show-trend"
                checked={localConfig.display?.trend?.show ?? true}
                onCheckedChange={(checked) =>
                  updateNestedConfig(["display", "trend", "show"], checked)
                }
              />
            </div>

            {localConfig.display?.trend?.show && (
              <div className="flex items-center justify-between">
                <Label htmlFor="invert-trend">
                  Invert Trend Colors
                  <span className="block text-xs text-muted-foreground">
                    (Good when lower is better)
                  </span>
                </Label>
                <Switch
                  id="invert-trend"
                  checked={localConfig.display?.trend?.inverted || false}
                  onCheckedChange={(checked) =>
                    updateNestedConfig(["display", "trend", "inverted"], checked)
                  }
                />
              </div>
            )}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}