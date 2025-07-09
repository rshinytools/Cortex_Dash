// ABOUTME: Heatmap widget for visualizing correlation matrices and grid data
// ABOUTME: Supports custom color scales, tooltips, and interactive features

'use client';

import React, { useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertCircle, Loader2 } from 'lucide-react';
import { BaseWidgetProps, WidgetComponent } from './base-widget';
import { cn } from '@/lib/utils';

interface HeatmapConfig {
  xAxisField: string;
  yAxisField: string;
  valueField: string;
  xAxisLabel?: string;
  yAxisLabel?: string;
  colorScale?: 'sequential' | 'diverging' | 'custom';
  minColor?: string;
  midColor?: string;
  maxColor?: string;
  showValues?: boolean;
  showTooltip?: boolean;
  valueFormat?: 'number' | 'percentage' | 'currency';
  decimals?: number;
  cellSize?: number;
  cellGap?: number;
  showLegend?: boolean;
  legendTitle?: string;
  sortX?: 'asc' | 'desc' | 'none';
  sortY?: 'asc' | 'desc' | 'none';
  minValue?: number;
  maxValue?: number;
  midValue?: number;
}

const formatValue = (value: number | null | undefined, format?: string, decimals: number = 2): string => {
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

const getColor = (value: number, config: HeatmapConfig, minVal: number, maxVal: number): string => {
  const { colorScale = 'sequential', minColor = '#eff6ff', midColor = '#3b82f6', maxColor = '#1e3a8a' } = config;
  
  // Normalize value between 0 and 1
  let normalizedValue = (value - minVal) / (maxVal - minVal);
  normalizedValue = Math.max(0, Math.min(1, normalizedValue)); // Clamp between 0 and 1
  
  if (colorScale === 'diverging') {
    const midVal = config.midValue ?? (minVal + maxVal) / 2;
    if (value < midVal) {
      // Interpolate between minColor and midColor
      const t = (value - minVal) / (midVal - minVal);
      return interpolateColor(minColor, midColor, t);
    } else {
      // Interpolate between midColor and maxColor
      const t = (value - midVal) / (maxVal - midVal);
      return interpolateColor(midColor, maxColor, t);
    }
  } else {
    // Sequential scale
    if (normalizedValue < 0.5) {
      return interpolateColor(minColor, midColor, normalizedValue * 2);
    } else {
      return interpolateColor(midColor, maxColor, (normalizedValue - 0.5) * 2);
    }
  }
};

// Simple color interpolation
const interpolateColor = (color1: string, color2: string, t: number): string => {
  // Convert hex to RGB
  const hex2rgb = (hex: string) => {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? {
      r: parseInt(result[1], 16),
      g: parseInt(result[2], 16),
      b: parseInt(result[3], 16)
    } : { r: 0, g: 0, b: 0 };
  };
  
  const c1 = hex2rgb(color1);
  const c2 = hex2rgb(color2);
  
  const r = Math.round(c1.r + (c2.r - c1.r) * t);
  const g = Math.round(c1.g + (c2.g - c1.g) * t);
  const b = Math.round(c1.b + (c2.b - c1.b) * t);
  
  return `rgb(${r}, ${g}, ${b})`;
};

const HeatmapCell: React.FC<{
  x: string;
  y: string;
  value: number | null;
  color: string;
  size: number;
  gap: number;
  showValue: boolean;
  config: HeatmapConfig;
  onHover: (x: string, y: string, value: number | null) => void;
  onLeave: () => void;
}> = ({ x, y, value, color, size, gap, showValue, config, onHover, onLeave }) => {
  const textColor = value !== null && value !== undefined ? 
    (parseInt(color.replace(/[^0-9,]/g, '').split(',')[0]) < 128 ? '#ffffff' : '#000000') : 
    '#666666';
  
  return (
    <div
      className="cursor-pointer transition-all duration-200 hover:opacity-80 flex items-center justify-center"
      style={{
        backgroundColor: color,
        width: size,
        height: size,
        margin: gap / 2,
      }}
      onMouseEnter={() => onHover(x, y, value)}
      onMouseLeave={onLeave}
    >
      {showValue && (
        <span 
          className="text-xs font-medium"
          style={{ color: textColor }}
        >
          {formatValue(value, config.valueFormat, config.decimals)}
        </span>
      )}
    </div>
  );
};

export const Heatmap: WidgetComponent = ({
  title,
  description,
  configuration,
  data,
  loading,
  error,
  className
}) => {
  const config = configuration as HeatmapConfig;
  const [hoveredCell, setHoveredCell] = React.useState<{ x: string; y: string; value: number | null } | null>(null);

  const processedData = useMemo(() => {
    if (!data) return { matrix: [], xLabels: [], yLabels: [], minValue: 0, maxValue: 1 };
    
    const records = Array.isArray(data) ? data : data?.records || [];
    
    // Get unique x and y values
    const xLabels = [...new Set(records.map((d: any) => d[config.xAxisField]))].filter(Boolean);
    const yLabels = [...new Set(records.map((d: any) => d[config.yAxisField]))].filter(Boolean);
    
    // Sort if requested
    if (config.sortX === 'asc') xLabels.sort();
    else if (config.sortX === 'desc') xLabels.sort().reverse();
    
    if (config.sortY === 'asc') yLabels.sort();
    else if (config.sortY === 'desc') yLabels.sort().reverse();
    
    // Create value map for quick lookup
    const valueMap = new Map<string, number>();
    records.forEach((record: any) => {
      const x = record[config.xAxisField];
      const y = record[config.yAxisField];
      const value = record[config.valueField];
      if (x && y && value !== null && value !== undefined) {
        valueMap.set(`${x}-${y}`, value);
      }
    });
    
    // Build matrix
    const matrix: (number | null)[][] = yLabels.map(y =>
      xLabels.map(x => valueMap.get(`${x}-${y}`) ?? null)
    );
    
    // Find min and max values
    const values = Array.from(valueMap.values());
    const minValue = config.minValue ?? Math.min(...values);
    const maxValue = config.maxValue ?? Math.max(...values);
    
    return { matrix, xLabels, yLabels, minValue, maxValue };
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

  const { matrix, xLabels, yLabels, minValue, maxValue } = processedData;

  if (matrix.length === 0 || xLabels.length === 0 || yLabels.length === 0) {
    return (
      <Card className={cn("h-full", className)}>
        <CardContent className="flex items-center justify-center h-full">
          <p className="text-muted-foreground">No data available</p>
        </CardContent>
      </Card>
    );
  }

  const cellSize = config.cellSize || 40;
  const cellGap = config.cellGap || 2;
  const showValues = config.showValues !== false && cellSize >= 30;

  return (
    <Card className={cn("h-full flex flex-col", className)}>
      <CardHeader className="pb-2 flex-shrink-0">
        <CardTitle className="text-base">{title}</CardTitle>
        {description && (
          <CardDescription className="text-xs">{description}</CardDescription>
        )}
      </CardHeader>
      <CardContent className="flex-1 overflow-auto pb-0">
        <div className="min-w-fit">
          {/* Y-axis label */}
          {config.yAxisLabel && (
            <div className="flex items-center mb-2">
              <div className="w-16" />
              <div className="text-xs font-medium text-muted-foreground">
                {config.yAxisLabel}
              </div>
            </div>
          )}
          
          <div className="flex">
            {/* Y-axis labels */}
            <div className="flex flex-col justify-between pr-2">
              <div style={{ height: cellSize + cellGap }} />
              {yLabels.map(label => (
                <div
                  key={label as React.Key}
                  className="text-xs text-muted-foreground flex items-center justify-end"
                  style={{ height: cellSize + cellGap }}
                >
                  {label as React.ReactNode}
                </div>
              ))}
            </div>
            
            {/* Heatmap grid */}
            <div>
              {/* X-axis labels */}
              <div className="flex mb-1">
                {xLabels.map(label => (
                  <div
                    key={label as React.Key}
                    className="text-xs text-muted-foreground text-center truncate"
                    style={{ width: cellSize + cellGap }}
                  >
                    {label as React.ReactNode}
                  </div>
                ))}
              </div>
              
              {/* Cells */}
              {matrix.map((row, rowIndex) => (
                <div key={yLabels[rowIndex] as React.Key} className="flex">
                  {row.map((value, colIndex) => (
                    <HeatmapCell
                      key={`${xLabels[colIndex] as string}-${yLabels[rowIndex] as string}`}
                      x={xLabels[colIndex] as string}
                      y={yLabels[rowIndex] as string}
                      value={value}
                      color={value !== null ? getColor(value, config, minValue, maxValue) : '#f3f4f6'}
                      size={cellSize}
                      gap={cellGap}
                      showValue={showValues}
                      config={config}
                      onHover={(x, y, v) => setHoveredCell({ x, y, value: v })}
                      onLeave={() => setHoveredCell(null)}
                    />
                  ))}
                </div>
              ))}
              
              {/* X-axis label */}
              {config.xAxisLabel && (
                <div className="text-xs font-medium text-muted-foreground text-center mt-2">
                  {config.xAxisLabel}
                </div>
              )}
            </div>
          </div>
          
          {/* Legend */}
          {config.showLegend !== false && (
            <div className="mt-4 flex items-center gap-4">
              <span className="text-xs text-muted-foreground">
                {config.legendTitle || 'Value'}:
              </span>
              <div className="flex items-center gap-2">
                <span className="text-xs">{formatValue(minValue, config.valueFormat, config.decimals)}</span>
                <div 
                  className="h-4 w-32 rounded"
                  style={{
                    background: `linear-gradient(to right, ${config.minColor || '#eff6ff'}, ${config.midColor || '#3b82f6'}, ${config.maxColor || '#1e3a8a'})`
                  }}
                />
                <span className="text-xs">{formatValue(maxValue, config.valueFormat, config.decimals)}</span>
              </div>
            </div>
          )}
          
          {/* Tooltip */}
          {config.showTooltip !== false && hoveredCell && (
            <div className="mt-2 text-sm">
              <span className="text-muted-foreground">
                {config.xAxisField}: {hoveredCell.x}, {config.yAxisField}: {hoveredCell.y}
              </span>
              {hoveredCell.value !== null && (
                <span className="ml-2 font-medium">
                  = {formatValue(hoveredCell.value, config.valueFormat, config.decimals)}
                </span>
              )}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

Heatmap.displayName = 'Heatmap';
Heatmap.defaultHeight = 6;
Heatmap.defaultWidth = 8;
Heatmap.supportedExportFormats = ['png', 'json', 'csv'];
Heatmap.validateConfiguration = (config: Record<string, any>) => {
  return config.xAxisField && config.yAxisField && config.valueField;
};