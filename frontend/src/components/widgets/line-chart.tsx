// ABOUTME: Line chart widget for displaying time series data
// ABOUTME: Uses recharts library with customizable axes and series

'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertCircle, Loader2 } from 'lucide-react';
import {
  LineChart as RechartsLineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  TooltipProps,
  Area,
  AreaChart,
  ReferenceLine,
} from 'recharts';
import { BaseWidgetProps, WidgetComponent } from './base-widget';
import { cn } from '@/lib/utils';
import { format } from 'date-fns';
import { lineChartDataContract } from './data-contracts';

interface LineChartConfig {
  xAxisField: string;
  yAxisFields: Array<{
    field: string;
    label: string;
    color?: string;
    strokeWidth?: number;
    strokeDasharray?: string;
    type?: 'monotone' | 'linear' | 'step';
    showArea?: boolean;
  }>;
  xAxisLabel?: string;
  yAxisLabel?: string;
  showGrid?: boolean;
  showLegend?: boolean;
  showTooltip?: boolean;
  dateFormat?: string;
  valueFormat?: 'number' | 'percentage' | 'currency';
  decimals?: number;
  referenceLines?: Array<{
    y?: number;
    x?: string | number;
    label?: string;
    color?: string;
    strokeDasharray?: string;
  }>;
  areaChart?: boolean;
  stacked?: boolean;
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
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
      }).format(value);
  }
};

const CustomTooltip = ({ active, payload, label, config }: TooltipProps<any, any> & { config: LineChartConfig }) => {
  if (active && payload && payload.length) {
    const isDate = !isNaN(Date.parse(label));
    const formattedLabel = isDate && config.dateFormat
      ? format(new Date(label), config.dateFormat)
      : label;

    return (
      <div className="bg-background border rounded-lg shadow-lg p-3">
        <p className="font-medium mb-2">{formattedLabel}</p>
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

export const LineChart: WidgetComponent = ({
  title,
  description,
  configuration,
  data,
  loading,
  error,
  className
}) => {
  const config = configuration as LineChartConfig;

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

  const ChartComponent = config.areaChart ? AreaChart : RechartsLineChart;
  const LineComponent = config.areaChart ? Area : Line;

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
          <ChartComponent
            data={chartData}
            margin={{ top: 5, right: 5, left: 5, bottom: 5 }}
          >
            {config.showGrid !== false && (
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            )}
            <XAxis
              dataKey={config.xAxisField}
              tick={{ fontSize: 12 }}
              tickFormatter={(value) => {
                if (!value) return '';
                const isDate = !isNaN(Date.parse(value));
                return isDate && config.dateFormat
                  ? format(new Date(value), 'MMM dd')
                  : value;
              }}
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
            {config.showTooltip !== false && (
              <Tooltip content={<CustomTooltip config={config} />} />
            )}
            {config.showLegend !== false && (
              <Legend
                wrapperStyle={{ fontSize: '12px' }}
                iconType="line"
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
              <LineComponent
                key={field.field}
                type={field.type || 'monotone'}
                dataKey={field.field}
                name={field.label}
                stroke={field.color || defaultColors[index % defaultColors.length]}
                fill={field.color || defaultColors[index % defaultColors.length]}
                strokeWidth={field.strokeWidth || 2}
                strokeDasharray={field.strokeDasharray}
                fillOpacity={config.areaChart ? 0.3 : 0}
                stackId={config.stacked ? 'stack' : undefined}
              />
            ))}
          </ChartComponent>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};

LineChart.displayName = 'LineChart';
LineChart.defaultHeight = 4;
LineChart.defaultWidth = 6;
LineChart.supportedExportFormats = ['png', 'json', 'csv'];
LineChart.dataContract = lineChartDataContract;
LineChart.validateConfiguration = (config: Record<string, any>) => {
  return config.xAxisField && config.yAxisFields?.length > 0;
};