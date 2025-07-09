// ABOUTME: Scatter plot widget for displaying correlation between two variables
// ABOUTME: Supports trend line, color grouping, and size variations

'use client';

import React, { useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertCircle, Loader2 } from 'lucide-react';
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  TooltipProps,
  ZAxis,
  ReferenceLine,
  Cell,
} from 'recharts';
import { BaseWidgetProps, WidgetComponent } from './base-widget';
import { cn } from '@/lib/utils';

interface ScatterPlotConfig {
  xAxisField: string;
  yAxisField: string;
  xAxisLabel?: string;
  yAxisLabel?: string;
  groupByField?: string;
  sizeField?: string;
  colorField?: string;
  showGrid?: boolean;
  showLegend?: boolean;
  showTooltip?: boolean;
  showTrendLine?: boolean;
  trendLineType?: 'linear' | 'polynomial' | 'exponential';
  valueFormat?: 'number' | 'percentage' | 'currency';
  decimals?: number;
  minSize?: number;
  maxSize?: number;
  colors?: string[];
  referenceLines?: Array<{
    y?: number;
    x?: number;
    label?: string;
    color?: string;
    strokeDasharray?: string;
  }>;
  domain?: {
    x?: [number | 'auto', number | 'auto'];
    y?: [number | 'auto', number | 'auto'];
  };
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

// Calculate linear regression
const calculateLinearRegression = (data: any[], xField: string, yField: string) => {
  const validData = data.filter(d => d[xField] !== null && d[yField] !== null);
  const n = validData.length;
  
  if (n === 0) return null;
  
  const sumX = validData.reduce((sum, d) => sum + d[xField], 0);
  const sumY = validData.reduce((sum, d) => sum + d[yField], 0);
  const sumXY = validData.reduce((sum, d) => sum + d[xField] * d[yField], 0);
  const sumX2 = validData.reduce((sum, d) => sum + d[xField] * d[xField], 0);
  
  const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
  const intercept = (sumY - slope * sumX) / n;
  
  // Calculate R-squared
  const meanY = sumY / n;
  const ssTotal = validData.reduce((sum, d) => sum + Math.pow(d[yField] - meanY, 2), 0);
  const ssResidual = validData.reduce((sum, d) => {
    const predicted = slope * d[xField] + intercept;
    return sum + Math.pow(d[yField] - predicted, 2);
  }, 0);
  const rSquared = 1 - (ssResidual / ssTotal);
  
  return { slope, intercept, rSquared };
};

const CustomTooltip = ({ active, payload, config }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    
    return (
      <div className="bg-background border rounded-lg shadow-lg p-3">
        <div className="space-y-1 text-sm">
          <div className="flex items-center gap-2">
            <span className="text-muted-foreground">{config.xAxisLabel || config.xAxisField}:</span>
            <span className="font-medium">
              {formatValue(data[config.xAxisField], config.valueFormat, config.decimals)}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-muted-foreground">{config.yAxisLabel || config.yAxisField}:</span>
            <span className="font-medium">
              {formatValue(data[config.yAxisField], config.valueFormat, config.decimals)}
            </span>
          </div>
          {config.groupByField && data[config.groupByField] && (
            <div className="flex items-center gap-2">
              <span className="text-muted-foreground">Group:</span>
              <span className="font-medium">{data[config.groupByField]}</span>
            </div>
          )}
          {config.sizeField && data[config.sizeField] !== undefined && (
            <div className="flex items-center gap-2">
              <span className="text-muted-foreground">Size:</span>
              <span className="font-medium">
                {formatValue(data[config.sizeField], config.valueFormat, config.decimals)}
              </span>
            </div>
          )}
        </div>
      </div>
    );
  }
  return null;
};

export const ScatterPlot: WidgetComponent = ({
  title,
  description,
  configuration,
  data,
  loading,
  error,
  className
}) => {
  const config = configuration as ScatterPlotConfig;

  const processedData = useMemo(() => {
    if (!data) return { scatterData: [], groups: [], regression: null };
    
    const records = Array.isArray(data) ? data : data?.records || [];
    
    // Filter valid data points
    const validData = records.filter((d: any) => 
      d[config.xAxisField] !== null && 
      d[config.xAxisField] !== undefined &&
      d[config.yAxisField] !== null &&
      d[config.yAxisField] !== undefined
    );
    
    // Group data if groupByField is specified
    const groups = config.groupByField 
      ? [...new Set(validData.map((d: any) => d[config.groupByField!]))]
      : ['all'];
    
    // Calculate regression if requested
    const regression = config.showTrendLine 
      ? calculateLinearRegression(validData, config.xAxisField, config.yAxisField)
      : null;
    
    return { scatterData: validData, groups, regression };
  }, [data, config]);

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

  const { scatterData, groups, regression } = processedData;

  if (!scatterData || scatterData.length === 0) {
    return (
      <Card className={cn("h-full", className)}>
        <CardContent className="flex items-center justify-center h-full">
          <p className="text-muted-foreground">No data available</p>
        </CardContent>
      </Card>
    );
  }

  // Calculate trend line points
  const trendLineData = useMemo(() => {
    if (!regression || !config.showTrendLine) return [];
    
    const xValues = scatterData.map((d: any) => d[config.xAxisField]);
    const minX = Math.min(...xValues);
    const maxX = Math.max(...xValues);
    
    return [
      { x: minX, y: regression.slope * minX + regression.intercept },
      { x: maxX, y: regression.slope * maxX + regression.intercept }
    ];
  }, [regression, config.showTrendLine, scatterData, config.xAxisField]);

  // Calculate size range
  const sizeRange = useMemo(() => {
    if (!config.sizeField) return [64, 64]; // Fixed size if no size field
    
    const sizes = scatterData.map((d: any) => d[config.sizeField!]).filter((s: any) => s !== null && s !== undefined);
    if (sizes.length === 0) return [64, 64];
    
    const minData = Math.min(...sizes);
    const maxData = Math.max(...sizes);
    const minSize = config.minSize || 32;
    const maxSize = config.maxSize || 400;
    
    return [minSize, maxSize];
  }, [config.sizeField, config.minSize, config.maxSize, scatterData]);

  const colors = config.colors || defaultColors;

  return (
    <Card className={cn("h-full flex flex-col", className)}>
      <CardHeader className="pb-2 flex-shrink-0">
        <CardTitle className="text-base">{title}</CardTitle>
        {description && (
          <CardDescription className="text-xs">{description}</CardDescription>
        )}
        {regression && config.showTrendLine && (
          <CardDescription className="text-xs">
            R² = {regression.rSquared.toFixed(3)}
          </CardDescription>
        )}
      </CardHeader>
      <CardContent className="flex-1 pb-0">
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
            {config.showGrid !== false && (
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            )}
            <XAxis
              type="number"
              dataKey={config.xAxisField}
              name={config.xAxisLabel || config.xAxisField}
              tick={{ fontSize: 12 }}
              domain={config.domain?.x || ['auto', 'auto']}
              tickFormatter={(value) => formatValue(value, config.valueFormat, 0)}
              label={config.xAxisLabel ? {
                value: config.xAxisLabel,
                position: 'insideBottom',
                offset: -5,
                style: { fontSize: 12 }
              } : undefined}
            />
            <YAxis
              type="number"
              dataKey={config.yAxisField}
              name={config.yAxisLabel || config.yAxisField}
              tick={{ fontSize: 12 }}
              domain={config.domain?.y || ['auto', 'auto']}
              tickFormatter={(value) => formatValue(value, config.valueFormat, 0)}
              label={config.yAxisLabel ? {
                value: config.yAxisLabel,
                angle: -90,
                position: 'insideLeft',
                style: { fontSize: 12 }
              } : undefined}
            />
            {config.sizeField && (
              <ZAxis 
                type="number" 
                dataKey={config.sizeField} 
                range={sizeRange as [number, number]}
                name={config.sizeField}
              />
            )}
            {config.showTooltip !== false && (
              <Tooltip content={<CustomTooltip config={config} />} />
            )}
            {config.showLegend !== false && config.groupByField && groups.length > 1 && (
              <Legend 
                wrapperStyle={{ fontSize: '12px' }}
                iconType="circle"
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
            {/* Trend line */}
            {config.showTrendLine && trendLineData.length > 0 && (
              <Scatter
                name="Trend"
                data={trendLineData}
                fill="none"
                line={{ stroke: '#666', strokeWidth: 2, strokeDasharray: '5 5' }}
                shape={undefined}
              />
            )}
            {/* Data points */}
            {config.groupByField && groups.length > 1 ? (
              groups.map((group, index) => (
                <Scatter
                  key={String(group)}
                  name={String(group)}
                  data={scatterData.filter((d: any) => d[config.groupByField!] === group)}
                  fill={colors[index % colors.length]}
                />
              ))
            ) : (
              <Scatter
                data={scatterData}
                fill={colors[0]}
              >
                {config.colorField && scatterData.map((entry: any, index: number) => (
                  <Cell 
                    key={`cell-${index}`} 
                    fill={entry[config.colorField!] || colors[0]}
                  />
                ))}
              </Scatter>
            )}
          </ScatterChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};

ScatterPlot.displayName = 'ScatterPlot';
ScatterPlot.defaultHeight = 4;
ScatterPlot.defaultWidth = 6;
ScatterPlot.supportedExportFormats = ['png', 'json', 'csv'];
ScatterPlot.validateConfiguration = (config: Record<string, any>) => {
  return config.xAxisField && config.yAxisField;
};