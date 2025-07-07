// ABOUTME: Bar chart widget for displaying categorical data comparisons
// ABOUTME: Supports both vertical and horizontal orientations with customizable styling

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
  LabelList,
  ReferenceLine,
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
  orientation?: 'horizontal' | 'vertical';
  xAxisLabel?: string;
  yAxisLabel?: string;
  showGrid?: boolean;
  showLegend?: boolean;
  showTooltip?: boolean;
  showValues?: boolean;
  valueFormat?: 'number' | 'percentage' | 'currency';
  decimals?: number;
  sortBy?: 'value' | 'label' | 'none';
  sortOrder?: 'asc' | 'desc';
  maxBars?: number;
  referenceLines?: Array<{
    y?: number;
    x?: string | number;
    label?: string;
    color?: string;
    strokeDasharray?: string;
  }>;
  barSize?: number;
  barGap?: number;
  categoryGap?: number;
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

const CustomLabel = ({ x, y, width, height, value, config, orientation }: any) => {
  const formattedValue = formatValue(value, config.valueFormat, config.decimals);
  
  if (orientation === 'horizontal') {
    return (
      <text
        x={x + width + 5}
        y={y + height / 2}
        fill="#666"
        textAnchor="start"
        dominantBaseline="middle"
        fontSize={12}
      >
        {formattedValue}
      </text>
    );
  } else {
    return (
      <text
        x={x + width / 2}
        y={y - 5}
        fill="#666"
        textAnchor="middle"
        dominantBaseline="bottom"
        fontSize={12}
      >
        {formattedValue}
      </text>
    );
  }
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
  const orientation = config.orientation || 'vertical';

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

  let chartData = Array.isArray(data) ? data : data?.records || [];

  if (!chartData || chartData.length === 0) {
    return (
      <Card className={cn("h-full", className)}>
        <CardContent className="flex items-center justify-center h-full">
          <p className="text-muted-foreground">No data available</p>
        </CardContent>
      </Card>
    );
  }

  // Sort data if requested
  if (config.sortBy && config.sortBy !== 'none') {
    chartData = [...chartData].sort((a, b) => {
      if (config.sortBy === 'label') {
        const aVal = a[config.xAxisField] || '';
        const bVal = b[config.xAxisField] || '';
        return config.sortOrder === 'desc' 
          ? bVal.localeCompare(aVal)
          : aVal.localeCompare(bVal);
      } else if (config.sortBy === 'value' && config.yAxisFields.length > 0) {
        const field = config.yAxisFields[0].field;
        const aVal = a[field] || 0;
        const bVal = b[field] || 0;
        return config.sortOrder === 'desc' ? bVal - aVal : aVal - bVal;
      }
      return 0;
    });
  }

  // Limit number of bars if specified
  if (config.maxBars && config.maxBars > 0) {
    chartData = chartData.slice(0, config.maxBars);
  }

  // Swap axes for horizontal orientation
  const xKey = orientation === 'horizontal' ? 'value' : config.xAxisField;
  const yKey = orientation === 'horizontal' ? config.xAxisField : 'value';

  // Transform data for horizontal orientation
  if (orientation === 'horizontal' && config.yAxisFields.length > 0) {
    // For simplicity, we'll use the first yAxisField for horizontal bars
    const field = config.yAxisFields[0].field;
    chartData = chartData.map(item => ({
      ...item,
      value: item[field]
    }));
  }

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
            layout={orientation === 'horizontal' ? 'horizontal' : 'vertical'}
            margin={{ 
              top: config.showValues ? 20 : 5, 
              right: orientation === 'horizontal' ? 80 : 5, 
              left: 5, 
              bottom: 5 
            }}
            barSize={config.barSize}
            barGap={config.barGap}
            barCategoryGap={config.categoryGap}
          >
            {config.showGrid !== false && (
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            )}
            {orientation === 'horizontal' ? (
              <>
                <XAxis
                  type="number"
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value) => formatValue(value, config.valueFormat, 0)}
                  label={config.yAxisLabel ? {
                    value: config.yAxisLabel,
                    position: 'insideBottom',
                    offset: -5,
                    style: { fontSize: 12 }
                  } : undefined}
                />
                <YAxis
                  dataKey={yKey}
                  type="category"
                  tick={{ fontSize: 12 }}
                  width={100}
                  label={config.xAxisLabel ? {
                    value: config.xAxisLabel,
                    angle: -90,
                    position: 'insideLeft',
                    style: { fontSize: 12 }
                  } : undefined}
                />
              </>
            ) : (
              <>
                <XAxis
                  dataKey={xKey}
                  tick={{ fontSize: 12 }}
                  angle={-45}
                  textAnchor="end"
                  height={60}
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
            {orientation === 'horizontal' ? (
              <Bar
                dataKey="value"
                fill={config.yAxisFields[0]?.color || defaultColors[0]}
                name={config.yAxisFields[0]?.label}
              >
                {config.showValues && (
                  <LabelList
                    dataKey="value"
                    position="right"
                    content={(props) => <CustomLabel {...props} config={config} orientation={orientation} />}
                  />
                )}
              </Bar>
            ) : (
              config.yAxisFields.map((field, index) => (
                <Bar
                  key={field.field}
                  dataKey={field.field}
                  name={field.label}
                  fill={field.color || defaultColors[index % defaultColors.length]}
                  stackId={field.stackId}
                >
                  {config.showValues && config.yAxisFields.length === 1 && (
                    <LabelList
                      dataKey={field.field}
                      position="top"
                      content={(props) => <CustomLabel {...props} config={config} orientation={orientation} />}
                    />
                  )}
                </Bar>
              ))
            )}
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