// ABOUTME: Bar chart widget for displaying categorical data comparisons
// ABOUTME: Uses recharts library with customizable bars and grouping

'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertCircle, Loader2 } from 'lucide-react';
import {
  BarChart as RechartsBarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  TooltipProps,
  Cell,
  ReferenceLine,
  LabelList,
} from 'recharts';
import { BaseWidgetProps, WidgetComponent } from './base-widget';
import { cn } from '@/lib/utils';

interface BarChartConfig {
  xAxisField: string;
  yAxisFields: Array<{
    field: string;
    label: string;
    color?: string;
    stackId?: string;
  }>;
  xAxisLabel?: string;
  yAxisLabel?: string;
  showGrid?: boolean;
  showLegend?: boolean;
  showTooltip?: boolean;
  showValues?: boolean;
  orientation?: 'horizontal' | 'vertical';
  valueFormat?: 'number' | 'percentage' | 'currency';
  decimals?: number;
  referenceLines?: Array<{
    y?: number;
    x?: string | number;
    label?: string;
    color?: string;
    strokeDasharray?: string;
  }>;
  colorByValue?: {
    field: string;
    thresholds: Array<{
      value: number;
      color: string;
    }>;
  };
  maxBarWidth?: number;
}

const defaultColors = [
  '#3b82f6', // blue
  '#10b981', // emerald
  '#f59e0b', // amber
  '#ef4444', // red
  '#8b5cf6', // violet
  '#ec4899', // pink
  '#14b8a6', // teal
  '#f97316', // orange
];

const formatValue = (value: number, format?: string, decimals: number = 2): string => {
  if (value === null || value === undefined) return 'N/A';
  
  switch (format) {
    case 'percentage':
      return `${(value * 100).toFixed(decimals)}%`;
    case 'currency':
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
      }).format(value);
    default:
      return new Intl.NumberFormat('en-US', {
        minimumFractionDigits: 0,
        maximumFractionDigits: decimals,
      }).format(value);
  }
};

const CustomTooltip = ({ active, payload, label, config }: TooltipProps<any, any> & { config: BarChartConfig }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-background border rounded-lg shadow-lg p-3">
        <p className="font-medium mb-2">{label}</p>
        {payload.map((entry: any, index: number) => (
          <div key={index} className="flex items-center gap-2 text-sm">
            <div 
              className="w-3 h-3 rounded-full" 
              style={{ backgroundColor: entry.color }}
            />
            <span className="text-muted-foreground">{entry.name}:</span>
            <span className="font-medium">
              {formatValue(entry.value, config.valueFormat, config.decimals)}
            </span>
          </div>
        ))}
      </div>
    );
  }
  return null;
};

const getColorForValue = (value: number, colorConfig?: BarChartConfig['colorByValue']): string | undefined => {
  if (!colorConfig) return undefined;
  
  const sortedThresholds = [...colorConfig.thresholds].sort((a, b) => b.value - a.value);
  for (const threshold of sortedThresholds) {
    if (value >= threshold.value) {
      return threshold.color;
    }
  }
  return undefined;
};

export const BarChart: WidgetComponent = ({
  title,
  description,
  configuration,
  data,
  loading,
  error,
  className
}) => {
  const config = configuration as BarChartConfig;

  if (loading) {
    return (
      <Card className={cn("h-full", className)}>
        <CardContent className="flex items-center justify-center h-full">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={cn("h-full", className)}>
        <CardContent className="flex flex-col items-center justify-center h-full">
          <AlertCircle className="h-8 w-8 text-destructive mb-2" />
          <p className="text-sm text-muted-foreground text-center">{error}</p>
        </CardContent>
      </Card>
    );
  }

  const chartData = Array.isArray(data) ? data : data?.records || [];

  if (!chartData || chartData.length === 0) {
    return (
      <Card className={cn("h-full", className)}>
        <CardContent className="flex items-center justify-center h-full">
          <p className="text-muted-foreground">No data available</p>
        </CardContent>
      </Card>
    );
  }

  const isHorizontal = config.orientation === 'horizontal';

  return (
    <Card className={cn("h-full flex flex-col", className)}>
      <CardHeader className="pb-2 flex-shrink-0">
        <CardTitle className="text-base">{title}</CardTitle>
        {description && (
          <CardDescription className="text-xs">{description}</CardDescription>
        )}
      </CardHeader>
      <CardContent className="flex-1 pb-0">
        <ResponsiveContainer width="100%" height="100%">
          <RechartsBarChart
            data={chartData}
            layout={isHorizontal ? 'horizontal' : 'vertical'}
            margin={{ top: 5, right: 5, left: 5, bottom: 5 }}
          >
            {config.showGrid !== false && (
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            )}
            {isHorizontal ? (
              <>
                <XAxis
                  type="number"
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value) => formatValue(value, config.valueFormat, 0)}
                  label={config.xAxisLabel ? {
                    value: config.xAxisLabel,
                    position: 'insideBottom',
                    offset: -5,
                    style: { fontSize: 12 }
                  } : undefined}
                />
                <YAxis
                  type="category"
                  dataKey={config.xAxisField}
                  tick={{ fontSize: 12 }}
                  width={100}
                />
              </>
            ) : (
              <>
                <XAxis
                  dataKey={config.xAxisField}
                  tick={{ fontSize: 12 }}
                  label={config.xAxisLabel ? {
                    value: config.xAxisLabel,
                    position: 'insideBottom',
                    offset: -5,
                    style: { fontSize: 12 }
                  } : undefined}
                />
                <YAxis
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value) => formatValue(value, config.valueFormat, 0)}
                  label={config.yAxisLabel ? {
                    value: config.yAxisLabel,
                    angle: -90,
                    position: 'insideLeft',
                    style: { fontSize: 12 }
                  } : undefined}
                />
              </>
            )}
            {config.showTooltip !== false && (
              <Tooltip content={<CustomTooltip config={config} />} />
            )}
            {config.showLegend !== false && config.yAxisFields.length > 1 && (
              <Legend
                wrapperStyle={{ fontSize: '12px' }}
                iconType="rect"
              />
            )}
            {config.referenceLines?.map((refLine, index) => (
              <ReferenceLine
                key={index}
                {...refLine}
                stroke={refLine.color || '#666'}
                strokeDasharray={refLine.strokeDasharray || '3 3'}
              />
            ))}
            {config.yAxisFields.map((field, index) => (
              <Bar
                key={field.field}
                dataKey={field.field}
                name={field.label}
                fill={field.color || defaultColors[index % defaultColors.length]}
                stackId={field.stackId}
                maxBarSize={config.maxBarWidth || 50}
              >
                {config.showValues && (
                  <LabelList
                    dataKey={field.field}
                    position={isHorizontal ? 'right' : 'top'}
                    formatter={(value: number) => formatValue(value, config.valueFormat, config.decimals)}
                    style={{ fontSize: 11 }}
                  />
                )}
                {config.colorByValue && field.field === config.colorByValue.field && (
                  chartData.map((entry, idx) => (
                    <Cell
                      key={`cell-${idx}`}
                      fill={getColorForValue(entry[field.field], config.colorByValue) || field.color || defaultColors[index % defaultColors.length]}
                    />
                  ))
                )}
              </Bar>
            ))}
          </RechartsBarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};

BarChart.displayName = 'BarChart';
BarChart.defaultHeight = 4;
BarChart.defaultWidth = 6;
BarChart.supportedExportFormats = ['png', 'json', 'csv'];
BarChart.validateConfiguration = (config: Record<string, any>) => {
  return config.xAxisField && config.yAxisFields?.length > 0;
};