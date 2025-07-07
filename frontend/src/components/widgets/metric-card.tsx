// ABOUTME: Metric card widget for displaying single metric values with trend
// ABOUTME: Supports various display formats and comparison values

'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { TrendingUp, TrendingDown, Minus, AlertCircle, Loader2 } from 'lucide-react';
import { BaseWidgetProps, WidgetComponent } from './base-widget';
import { cn } from '@/lib/utils';
import { metricCardDataContract } from './data-contracts';

interface MetricCardConfig {
  format?: 'number' | 'percentage' | 'currency' | 'decimal';
  decimals?: number;
  prefix?: string;
  suffix?: string;
  comparisonValue?: number;
  comparisonLabel?: string;
  targetValue?: number;
  targetLabel?: string;
  trend?: 'up' | 'down' | 'neutral';
  trendIsGood?: boolean;
  showTrend?: boolean;
  thresholds?: {
    good?: number;
    warning?: number;
    critical?: number;
  };
}

interface MetricData {
  value: number;
  previousValue?: number;
  trend?: number;
  trendDirection?: 'up' | 'down' | 'neutral';
}

const formatValue = (value: number, config: MetricCardConfig): string => {
  const { format = 'number', decimals = 0, prefix = '', suffix = '' } = config;

  let formatted: string;
  switch (format) {
    case 'percentage':
      formatted = `${(value * 100).toFixed(decimals)}%`;
      break;
    case 'currency':
      formatted = new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
      }).format(value);
      break;
    case 'decimal':
      formatted = value.toFixed(decimals);
      break;
    default:
      formatted = new Intl.NumberFormat('en-US', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
      }).format(value);
  }

  return `${prefix}${formatted}${suffix}`;
};

const getStatusColor = (value: number, thresholds?: MetricCardConfig['thresholds']): string => {
  if (!thresholds) return '';

  if (thresholds.critical !== undefined && value >= thresholds.critical) {
    return 'text-destructive';
  }
  if (thresholds.warning !== undefined && value >= thresholds.warning) {
    return 'text-yellow-600';
  }
  if (thresholds.good !== undefined && value >= thresholds.good) {
    return 'text-green-600';
  }
  return '';
};

export const MetricCard: WidgetComponent = ({
  title,
  description,
  configuration,
  data,
  loading,
  error,
  className
}) => {
  const config = configuration as MetricCardConfig;
  const metricData = data as MetricData;

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

  if (!metricData || metricData.value === undefined) {
    return (
      <Card className={cn("h-full", className)}>
        <CardContent className="flex items-center justify-center h-full">
          <p className="text-muted-foreground">No data available</p>
        </CardContent>
      </Card>
    );
  }

  const { value, previousValue, trend, trendDirection } = metricData;
  const formattedValue = formatValue(value, config);
  const statusColor = getStatusColor(value, config.thresholds);

  const showTrend = config.showTrend !== false && (trend !== undefined || trendDirection);
  const actualTrendDirection = trendDirection || (trend && trend > 0 ? 'up' : trend && trend < 0 ? 'down' : 'neutral');
  const trendIsPositive = config.trendIsGood !== undefined 
    ? config.trendIsGood 
    : actualTrendDirection === 'up';

  return (
    <Card className={cn("h-full", className)}>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        {description && (
          <CardDescription className="text-xs">{description}</CardDescription>
        )}
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          <div className={cn("text-2xl font-bold", statusColor)}>
            {formattedValue}
          </div>

          {showTrend && (
            <div className="flex items-center gap-2">
              {actualTrendDirection === 'up' && (
                <TrendingUp className={cn(
                  "h-4 w-4",
                  trendIsPositive ? "text-green-600" : "text-red-600"
                )} />
              )}
              {actualTrendDirection === 'down' && (
                <TrendingDown className={cn(
                  "h-4 w-4",
                  !trendIsPositive ? "text-green-600" : "text-red-600"
                )} />
              )}
              {actualTrendDirection === 'neutral' && (
                <Minus className="h-4 w-4 text-muted-foreground" />
              )}
              
              {trend !== undefined && (
                <span className={cn(
                  "text-sm",
                  trendIsPositive ? "text-green-600" : "text-red-600"
                )}>
                  {trend > 0 ? '+' : ''}{trend.toFixed(1)}%
                </span>
              )}
              
              {config.comparisonLabel && (
                <span className="text-xs text-muted-foreground">
                  {config.comparisonLabel}
                </span>
              )}
            </div>
          )}

          {config.targetValue !== undefined && (
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground">
                {config.targetLabel || 'Target'}
              </span>
              <Badge variant={value >= config.targetValue ? "default" : "secondary"}>
                {formatValue(config.targetValue, config)}
              </Badge>
            </div>
          )}

          {previousValue !== undefined && (
            <div className="text-xs text-muted-foreground">
              Previous: {formatValue(previousValue, config)}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

MetricCard.displayName = 'MetricCard';
MetricCard.defaultHeight = 2;
MetricCard.defaultWidth = 3;
MetricCard.supportedExportFormats = ['json', 'csv'];
MetricCard.dataContract = metricCardDataContract;
MetricCard.validateConfiguration = (config: Record<string, any>) => {
  return true; // Add validation logic here
};