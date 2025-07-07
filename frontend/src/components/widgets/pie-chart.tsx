// ABOUTME: Pie chart widget for displaying categorical distribution data
// ABOUTME: Uses recharts library with customizable segments and labels

'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertCircle, Loader2 } from 'lucide-react';
import {
  PieChart as RechartsPieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
  TooltipProps,
  Sector,
} from 'recharts';
import { BaseWidgetProps, WidgetComponent } from './base-widget';
import { cn } from '@/lib/utils';

interface PieChartConfig {
  dataField: string;
  labelField: string;
  valueField: string;
  showLegend?: boolean;
  showTooltip?: boolean;
  showLabels?: boolean;
  showPercentage?: boolean;
  innerRadius?: number; // For donut charts
  startAngle?: number;
  endAngle?: number;
  colors?: string[];
  activeOnHover?: boolean;
  valueFormat?: 'number' | 'percentage' | 'currency';
  decimals?: number;
  legendPosition?: 'top' | 'bottom' | 'left' | 'right';
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
  '#6366f1', // indigo
  '#84cc16', // lime
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

const CustomTooltip = ({ active, payload, config }: TooltipProps<any, any> & { config: PieChartConfig }) => {
  if (active && payload && payload.length) {
    const data = payload[0];
    const percentage = ((data.value / data.payload.total) * 100).toFixed(1);
    
    return (
      <div className="bg-background border rounded-lg shadow-lg p-3">
        <p className="font-medium mb-1">{data.name}</p>
        <div className="flex items-center gap-2 text-sm">
          <div 
            className="w-3 h-3 rounded-full" 
            style={{ backgroundColor: data.payload.fill }}
          />
          <span className="font-medium">
            {formatValue(data.value, config.valueFormat, config.decimals)}
          </span>
          <span className="text-muted-foreground">({percentage}%)</span>
        </div>
      </div>
    );
  }
  return null;
};

const renderActiveShape = (props: any) => {
  const {
    cx, cy, innerRadius, outerRadius, startAngle, endAngle,
    fill, payload, value, percent
  } = props;

  return (
    <g>
      <Sector
        cx={cx}
        cy={cy}
        innerRadius={innerRadius}
        outerRadius={outerRadius + 5}
        startAngle={startAngle}
        endAngle={endAngle}
        fill={fill}
      />
      <Sector
        cx={cx}
        cy={cy}
        startAngle={startAngle}
        endAngle={endAngle}
        innerRadius={outerRadius + 8}
        outerRadius={outerRadius + 10}
        fill={fill}
      />
    </g>
  );
};

const renderCustomLabel = (props: any, config: PieChartConfig) => {
  const { cx, cy, midAngle, innerRadius, outerRadius, value, index, name, percent } = props;
  const RADIAN = Math.PI / 180;
  const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
  const x = cx + radius * Math.cos(-midAngle * RADIAN);
  const y = cy + radius * Math.sin(-midAngle * RADIAN);

  if (config.showPercentage) {
    return (
      <text 
        x={x} 
        y={y} 
        fill="white" 
        textAnchor={x > cx ? 'start' : 'end'} 
        dominantBaseline="central"
        className="text-xs font-medium"
      >
        {`${(percent * 100).toFixed(0)}%`}
      </text>
    );
  }

  return null;
};

export const PieChart: WidgetComponent = ({
  title,
  description,
  configuration,
  data,
  loading,
  error,
  className
}) => {
  const config = configuration as PieChartConfig;
  const [activeIndex, setActiveIndex] = React.useState<number | undefined>();

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

  // Process data for pie chart
  const processedData = chartData.map((item, index) => {
    const value = item[config.valueField];
    const name = item[config.labelField];
    return {
      name,
      value: typeof value === 'number' ? value : parseFloat(value) || 0,
      fill: config.colors?.[index % config.colors.length] || defaultColors[index % defaultColors.length],
    };
  });

  // Calculate total for percentage calculations
  const total = processedData.reduce((sum, item) => sum + item.value, 0);
  processedData.forEach(item => {
    (item as any).total = total;
  });

  const onPieEnter = (_: any, index: number) => {
    if (config.activeOnHover) {
      setActiveIndex(index);
    }
  };

  const onPieLeave = () => {
    if (config.activeOnHover) {
      setActiveIndex(undefined);
    }
  };

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
          <RechartsPieChart margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
            {config.showTooltip !== false && (
              <Tooltip content={<CustomTooltip config={config} />} />
            )}
            {config.showLegend !== false && (
              <Legend
                wrapperStyle={{ fontSize: '12px' }}
                iconType="circle"
                layout={config.legendPosition === 'left' || config.legendPosition === 'right' ? 'vertical' : 'horizontal'}
                align={config.legendPosition === 'left' ? 'left' : config.legendPosition === 'right' ? 'right' : 'center'}
                verticalAlign={config.legendPosition === 'top' ? 'top' : config.legendPosition === 'bottom' ? 'bottom' : 'middle'}
              />
            )}
            <Pie
              data={processedData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={config.showLabels !== false ? (props) => renderCustomLabel(props, config) : undefined}
              outerRadius="80%"
              innerRadius={config.innerRadius || 0}
              startAngle={config.startAngle || 90}
              endAngle={config.endAngle || -270}
              activeIndex={activeIndex}
              activeShape={config.activeOnHover ? renderActiveShape : undefined}
              onMouseEnter={onPieEnter}
              onMouseLeave={onPieLeave}
            >
              {processedData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.fill} />
              ))}
            </Pie>
          </RechartsPieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};

PieChart.displayName = 'PieChart';
PieChart.defaultHeight = 4;
PieChart.defaultWidth = 4;
PieChart.supportedExportFormats = ['png', 'json', 'csv'];
PieChart.validateConfiguration = (config: Record<string, any>) => {
  return config.labelField && config.valueField;
};