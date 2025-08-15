// ABOUTME: KPI Metric Card widget renderer component
// ABOUTME: Displays single metric with comparisons, trends, and sparklines

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ArrowUpIcon, ArrowDownIcon, MinusIcon, TrendingUpIcon, TrendingDownIcon } from 'lucide-react';
import { cn } from '@/lib/utils';

interface KPIMetricCardProps {
  data: {
    widget_type: string;
    value: number;
    formatted_value: string;
    comparison?: {
      show: boolean;
      type?: string;
      difference?: number;
      percentage?: number;
      status?: string;
      target_value?: number;
    };
    trend?: {
      trend: 'up' | 'down' | 'flat';
      trend_percentage?: number;
      spark_data?: number[];
      periods?: number;
    };
    grouped_data?: Array<{
      group: string;
      value: number;
    }>;
    time_series?: Array<{
      period: string;
      value: number;
    }>;
    metadata?: {
      last_updated: string;
      aggregation_type: string;
    };
  };
  config?: {
    title?: string;
    description?: string;
    icon?: React.ReactNode;
    color?: 'default' | 'primary' | 'success' | 'warning' | 'danger';
    size?: 'sm' | 'md' | 'lg';
    showTrend?: boolean;
    showComparison?: boolean;
    showSparkline?: boolean;
  };
}

export const KPIMetricCard: React.FC<KPIMetricCardProps> = ({ data, config = {} }) => {
  const {
    title = 'Metric',
    description,
    icon,
    color = 'default',
    size = 'md',
    showTrend = true,
    showComparison = true,
    showSparkline = false,
  } = config;

  const getTrendIcon = () => {
    if (!data.trend) return null;
    
    switch (data.trend.trend) {
      case 'up':
        return <TrendingUpIcon className="h-4 w-4 text-green-500" />;
      case 'down':
        return <TrendingDownIcon className="h-4 w-4 text-red-500" />;
      default:
        return <MinusIcon className="h-4 w-4 text-gray-500" />;
    }
  };

  const getComparisonIcon = () => {
    if (!data.comparison || !data.comparison.status) return null;
    
    switch (data.comparison.status) {
      case 'above':
        return <ArrowUpIcon className="h-4 w-4 text-green-500" />;
      case 'below':
        return <ArrowDownIcon className="h-4 w-4 text-red-500" />;
      default:
        return <MinusIcon className="h-4 w-4 text-gray-500" />;
    }
  };

  const getColorClasses = () => {
    switch (color) {
      case 'primary':
        return 'border-blue-200 bg-blue-50/50';
      case 'success':
        return 'border-green-200 bg-green-50/50';
      case 'warning':
        return 'border-yellow-200 bg-yellow-50/50';
      case 'danger':
        return 'border-red-200 bg-red-50/50';
      default:
        return '';
    }
  };

  const getSizeClasses = () => {
    switch (size) {
      case 'sm':
        return 'text-2xl';
      case 'lg':
        return 'text-5xl';
      default:
        return 'text-4xl';
    }
  };

  const renderSparkline = () => {
    if (!showSparkline || !data.trend?.spark_data) return null;
    
    const values = data.trend.spark_data;
    const max = Math.max(...values);
    const min = Math.min(...values);
    const range = max - min || 1;
    
    const width = 100;
    const height = 30;
    const points = values.map((value, index) => {
      const x = (index / (values.length - 1)) * width;
      const y = height - ((value - min) / range) * height;
      return `${x},${y}`;
    }).join(' ');
    
    return (
      <div className="mt-2">
        <svg width={width} height={height} className="w-full h-8">
          <polyline
            points={points}
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            className="text-blue-500"
          />
        </svg>
      </div>
    );
  };

  return (
    <Card className={cn('transition-all hover:shadow-lg', getColorClasses())}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {icon && <div className="text-muted-foreground">{icon}</div>}
            <CardTitle className="text-sm font-medium text-muted-foreground">
              {title}
            </CardTitle>
          </div>
          {showTrend && data.trend && (
            <div className="flex items-center gap-1">
              {getTrendIcon()}
              {data.trend.trend_percentage !== undefined && (
                <span className={cn(
                  'text-sm font-medium',
                  data.trend.trend === 'up' ? 'text-green-500' : 
                  data.trend.trend === 'down' ? 'text-red-500' : 
                  'text-gray-500'
                )}>
                  {data.trend.trend_percentage > 0 ? '+' : ''}{data.trend.trend_percentage}%
                </span>
              )}
            </div>
          )}
        </div>
        {description && (
          <CardDescription className="text-xs mt-1">
            {description}
          </CardDescription>
        )}
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div className={cn('font-bold', getSizeClasses())}>
            {data.formatted_value}
          </div>
          
          {showComparison && data.comparison?.show && (
            <div className="flex items-center gap-2">
              {getComparisonIcon()}
              {data.comparison.type === 'target' && (
                <span className="text-sm text-muted-foreground">
                  vs target: {data.comparison.target_value}
                  {data.comparison.percentage !== undefined && (
                    <span className={cn(
                      'ml-1 font-medium',
                      data.comparison.status === 'above' ? 'text-green-500' :
                      data.comparison.status === 'below' ? 'text-red-500' :
                      'text-gray-500'
                    )}>
                      ({data.comparison.percentage > 0 ? '+' : ''}{data.comparison.percentage}%)
                    </span>
                  )}
                </span>
              )}
              {data.comparison.type === 'percentage_of_total' && (
                <span className="text-sm text-muted-foreground">
                  {data.comparison.percentage}% of total
                </span>
              )}
            </div>
          )}
          
          {renderSparkline()}
          
          {data.grouped_data && data.grouped_data.length > 0 && (
            <div className="mt-3 space-y-1">
              {data.grouped_data.slice(0, 3).map((group, index) => (
                <div key={index} className="flex justify-between text-sm">
                  <span className="text-muted-foreground">{group.group}</span>
                  <span className="font-medium">{group.value}</span>
                </div>
              ))}
            </div>
          )}
          
          {data.metadata && (
            <div className="mt-3 pt-3 border-t">
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>Type: {data.metadata.aggregation_type}</span>
                <span>
                  Updated: {new Date(data.metadata.last_updated).toLocaleTimeString()}
                </span>
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};