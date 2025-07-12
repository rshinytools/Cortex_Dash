// ABOUTME: MetricCard widget component that displays aggregated values with flexible configuration
// ABOUTME: Supports COUNT, COUNT_DISTINCT, SUM, AVG, MIN, MAX, MEDIAN with comparisons and filters

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { TrendingUp, TrendingDown, Minus, Info } from 'lucide-react';
import { cn } from '@/lib/utils';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface MetricWidgetProps {
  title: string;
  subtitle?: string;
  value: number | string;
  comparison?: {
    value: number;
    text?: string;
    period?: string;
    change?: number;
    type?: 'previous_extract' | 'target_value' | 'previous_period';
  };
  format?: 'number' | 'percentage' | 'currency';
  decimalPlaces?: number;
  prefix?: string;
  suffix?: string;
  loading?: boolean;
  error?: string;
  size?: 'small' | 'medium' | 'large';
  className?: string;
  aggregationType?: string;
  lastUpdated?: string;
}

export function MetricWidget({
  title,
  subtitle,
  value,
  comparison,
  format = 'number',
  decimalPlaces = 0,
  prefix = '',
  suffix = '',
  loading = false,
  error,
  size = 'small',
  className,
  aggregationType,
  lastUpdated
}: MetricWidgetProps) {
  const sizeClasses = {
    small: 'col-span-1',
    medium: 'col-span-2',
    large: 'col-span-3'
  };

  const getTrendIcon = (change: number) => {
    if (change > 0) return <TrendingUp className="h-3 w-3" />;
    if (change < 0) return <TrendingDown className="h-3 w-3" />;
    return <Minus className="h-3 w-3" />;
  };

  const getTrendColor = (change: number, comparisonType?: string) => {
    // For target comparisons, being below target (negative) might be good or bad depending on context
    if (comparisonType === 'target_value') {
      return 'text-blue-600';
    }
    if (change > 0) return 'text-green-600';
    if (change < 0) return 'text-red-600';
    return 'text-gray-600';
  };
  
  const getComparisonChange = (comparison: any) => {
    return comparison.change !== undefined ? comparison.change : comparison.value || 0;
  };

  const formatValue = (val: number | string): string => {
    if (typeof val === 'string') return val;
    
    let formattedValue: string;
    
    switch (format) {
      case 'percentage':
        formattedValue = `${val.toFixed(decimalPlaces)}%`;
        break;
      case 'currency':
        formattedValue = new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
          minimumFractionDigits: decimalPlaces,
          maximumFractionDigits: decimalPlaces
        }).format(val);
        break;
      default:
        formattedValue = val.toLocaleString('en-US', {
          minimumFractionDigits: decimalPlaces,
          maximumFractionDigits: decimalPlaces
        });
    }
    
    return `${prefix}${formattedValue}${suffix}`;
  };

  const getComparisonText = (comparison: any) => {
    if (comparison.type === 'target_value') {
      return comparison.text || 'vs target';
    }
    return comparison.text || comparison.period || 'vs last extract';
  };

  return (
    <TooltipProvider>
      <Card className={cn('h-full', sizeClasses[size], className)}>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <div className="flex items-center gap-2">
            <CardTitle className="text-sm font-medium">{title}</CardTitle>
            {aggregationType && (
              <Tooltip>
                <TooltipTrigger asChild>
                  <Info className="h-3 w-3 text-muted-foreground cursor-help" />
                </TooltipTrigger>
                <TooltipContent>
                  <p className="text-xs">Aggregation: {aggregationType}</p>
                  {lastUpdated && (
                    <p className="text-xs mt-1">Updated: {lastUpdated}</p>
                  )}
                </TooltipContent>
              </Tooltip>
            )}
          </div>
          {subtitle && (
            <span className="text-xs text-muted-foreground">{subtitle}</span>
          )}
        </CardHeader>
        <CardContent>
          {loading ? (
            <>
              <Skeleton className="h-7 w-20 mb-1" />
              <Skeleton className="h-4 w-16" />
            </>
          ) : error ? (
            <div className="text-sm text-red-600">Error: {error}</div>
          ) : (
            <>
              <div className="text-2xl font-bold">
                {formatValue(value)}
              </div>
              {comparison && (
                <div className="flex items-center gap-1 text-xs text-muted-foreground">
                  <span className={cn('flex items-center gap-0.5', getTrendColor(getComparisonChange(comparison), comparison.type))}>
                    {getTrendIcon(getComparisonChange(comparison))}
                    {Math.abs(getComparisonChange(comparison))}%
                  </span>
                  <span>{getComparisonText(comparison)}</span>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </TooltipProvider>
  );
}