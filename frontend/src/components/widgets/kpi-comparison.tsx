// ABOUTME: KPI comparison widget for comparing metrics across different periods or groups
// ABOUTME: Supports multiple comparison types with variance analysis and visual indicators

'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertCircle, Loader2, TrendingUp, TrendingDown, Minus, ArrowUp, ArrowDown } from 'lucide-react';
import { BaseWidgetProps, WidgetComponent } from './base-widget';
import { cn } from '@/lib/utils';
import { Progress } from '@/components/ui/progress';

interface KpiComparisonConfig {
  kpiField: string;
  groupByField?: string;
  comparisonType: 'period-over-period' | 'group-comparison' | 'target-vs-actual' | 'benchmark';
  currentPeriodField?: string;
  previousPeriodField?: string;
  targetField?: string;
  benchmarkField?: string;
  groups?: string[];
  displayType?: 'cards' | 'table' | 'progress' | 'gauge';
  valueFormat?: 'number' | 'percentage' | 'currency';
  decimals?: number;
  showTrend?: boolean;
  showVariance?: boolean;
  showSparkline?: boolean;
  trendThreshold?: number;
  goodDirection?: 'up' | 'down';
  colorCoding?: boolean;
  sortBy?: 'name' | 'value' | 'change';
  sortOrder?: 'asc' | 'desc';
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

const calculateChange = (current: number, previous: number): number => {
  if (previous === 0) return current > 0 ? 100 : 0;
  return ((current - previous) / Math.abs(previous)) * 100;
};

const getTrendIcon = (change: number, goodDirection?: string) => {
  const isPositive = change > 0;
  const isGood = goodDirection === 'down' ? !isPositive : isPositive;
  
  if (Math.abs(change) < 0.1) {
    return <Minus className="h-4 w-4 text-muted-foreground" />;
  }
  
  if (isPositive) {
    return <TrendingUp className={cn("h-4 w-4", isGood ? "text-green-600" : "text-red-600")} />;
  }
  
  return <TrendingDown className={cn("h-4 w-4", isGood ? "text-green-600" : "text-red-600")} />;
};

const getChangeColor = (change: number, goodDirection?: string) => {
  const isPositive = change > 0;
  const isGood = goodDirection === 'down' ? !isPositive : isPositive;
  
  if (Math.abs(change) < 0.1) return "text-muted-foreground";
  return isGood ? "text-green-600" : "text-red-600";
};

const KpiCard: React.FC<{
  title: string;
  value: number;
  previousValue?: number;
  target?: number;
  change?: number;
  config: KpiComparisonConfig;
}> = ({ title, value, previousValue, target, change, config }) => {
  const showChange = config.showTrend !== false && change !== undefined;
  const achievement = target ? (value / target) * 100 : null;
  
  return (
    <div className="p-4 border rounded-lg space-y-2">
      <h4 className="text-sm font-medium text-muted-foreground">{title}</h4>
      <div className="flex items-baseline gap-2">
        <span className="text-2xl font-bold">
          {formatValue(value, config.valueFormat, config.decimals)}
        </span>
        {showChange && (
          <div className={cn("flex items-center gap-1", getChangeColor(change, config.goodDirection))}>
            {getTrendIcon(change, config.goodDirection)}
            <span className="text-sm font-medium">
              {change > 0 ? '+' : ''}{change.toFixed(1)}%
            </span>
          </div>
        )}
      </div>
      {previousValue !== undefined && (
        <p className="text-xs text-muted-foreground">
          Previous: {formatValue(previousValue, config.valueFormat, config.decimals)}
        </p>
      )}
      {target !== undefined && (
        <div className="space-y-1">
          <div className="flex justify-between text-xs">
            <span className="text-muted-foreground">Target</span>
            <span>{formatValue(target, config.valueFormat, config.decimals)}</span>
          </div>
          {achievement !== null && (
            <Progress value={Math.min(achievement, 100)} className="h-2" />
          )}
        </div>
      )}
    </div>
  );
};

const ComparisonTable: React.FC<{
  data: any[];
  config: KpiComparisonConfig;
}> = ({ data, config }) => {
  return (
    <div className="overflow-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b">
            <th className="text-left p-2">Group</th>
            <th className="text-right p-2">Current</th>
            {config.comparisonType === 'period-over-period' && (
              <>
                <th className="text-right p-2">Previous</th>
                <th className="text-right p-2">Change</th>
              </>
            )}
            {config.comparisonType === 'target-vs-actual' && (
              <>
                <th className="text-right p-2">Target</th>
                <th className="text-right p-2">Achievement</th>
              </>
            )}
            {config.comparisonType === 'benchmark' && (
              <>
                <th className="text-right p-2">Benchmark</th>
                <th className="text-right p-2">Variance</th>
              </>
            )}
          </tr>
        </thead>
        <tbody>
          {data.map((row, index) => (
            <tr key={index} className="border-b">
              <td className="p-2">{row.name}</td>
              <td className="text-right p-2 font-medium">
                {formatValue(row.value, config.valueFormat, config.decimals)}
              </td>
              {config.comparisonType === 'period-over-period' && (
                <>
                  <td className="text-right p-2 text-muted-foreground">
                    {formatValue(row.previousValue, config.valueFormat, config.decimals)}
                  </td>
                  <td className={cn("text-right p-2 flex items-center justify-end gap-1", 
                    getChangeColor(row.change || 0, config.goodDirection))}>
                    {getTrendIcon(row.change || 0, config.goodDirection)}
                    {row.change !== undefined && (
                      <span>{row.change > 0 ? '+' : ''}{row.change.toFixed(1)}%</span>
                    )}
                  </td>
                </>
              )}
              {config.comparisonType === 'target-vs-actual' && (
                <>
                  <td className="text-right p-2 text-muted-foreground">
                    {formatValue(row.target, config.valueFormat, config.decimals)}
                  </td>
                  <td className="text-right p-2">
                    <div className="flex items-center justify-end gap-2">
                      <span className={cn(
                        row.achievement >= 100 ? "text-green-600" : "text-amber-600"
                      )}>
                        {row.achievement?.toFixed(1)}%
                      </span>
                      <Progress value={Math.min(row.achievement || 0, 100)} className="w-16 h-2" />
                    </div>
                  </td>
                </>
              )}
              {config.comparisonType === 'benchmark' && (
                <>
                  <td className="text-right p-2 text-muted-foreground">
                    {formatValue(row.benchmark, config.valueFormat, config.decimals)}
                  </td>
                  <td className={cn("text-right p-2", 
                    row.variance > 0 ? 
                      (config.goodDirection === 'down' ? "text-red-600" : "text-green-600") :
                      (config.goodDirection === 'down' ? "text-green-600" : "text-red-600")
                  )}>
                    {row.variance > 0 ? '+' : ''}{row.variance?.toFixed(1)}%
                  </td>
                </>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export const KpiComparison: WidgetComponent = ({
  title,
  description,
  configuration,
  data,
  loading,
  error,
  className
}) => {
  const config = configuration as KpiComparisonConfig;

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

  const records = Array.isArray(data) ? data : data?.records || [];

  if (!records || records.length === 0) {
    return (
      <Card className={cn("h-full", className)}>
        <CardContent className="flex items-center justify-center h-full">
          <p className="text-muted-foreground">No data available</p>
        </CardContent>
      </Card>
    );
  }

  // Process data based on comparison type
  let processedData: any[] = [];

  if (config.comparisonType === 'period-over-period') {
    if (config.groupByField) {
      // Group comparison across periods
      const groups = [...new Set(records.map((r: any) => r[config.groupByField!]))];
      processedData = groups.map(group => {
        const groupRecords = records.filter((r: any) => r[config.groupByField!] === group);
        const current = groupRecords[0]?.[config.currentPeriodField || config.kpiField] || 0;
        const previous = groupRecords[0]?.[config.previousPeriodField || 'previousValue'] || 0;
        const change = calculateChange(current, previous);
        
        return {
          name: group,
          value: current,
          previousValue: previous,
          change
        };
      });
    } else {
      // Single KPI period comparison
      const current = records[0]?.[config.currentPeriodField || config.kpiField] || 0;
      const previous = records[0]?.[config.previousPeriodField || 'previousValue'] || 0;
      const change = calculateChange(current, previous);
      
      processedData = [{
        name: 'KPI',
        value: current,
        previousValue: previous,
        change
      }];
    }
  } else if (config.comparisonType === 'target-vs-actual') {
    if (config.groupByField) {
      const groups = [...new Set(records.map((r: any) => r[config.groupByField!]))];
      processedData = groups.map(group => {
        const groupRecord = records.find((r: any) => r[config.groupByField!] === group);
        const actual = groupRecord?.[config.kpiField] || 0;
        const target = groupRecord?.[config.targetField || 'target'] || 0;
        const achievement = target > 0 ? (actual / target) * 100 : 0;
        
        return {
          name: group,
          value: actual,
          target,
          achievement
        };
      });
    } else {
      const actual = records[0]?.[config.kpiField] || 0;
      const target = records[0]?.[config.targetField || 'target'] || 0;
      const achievement = target > 0 ? (actual / target) * 100 : 0;
      
      processedData = [{
        name: 'KPI',
        value: actual,
        target,
        achievement
      }];
    }
  } else if (config.comparisonType === 'benchmark') {
    if (config.groupByField) {
      const groups = [...new Set(records.map((r: any) => r[config.groupByField!]))];
      processedData = groups.map(group => {
        const groupRecord = records.find((r: any) => r[config.groupByField!] === group);
        const actual = groupRecord?.[config.kpiField] || 0;
        const benchmark = groupRecord?.[config.benchmarkField || 'benchmark'] || 0;
        const variance = benchmark > 0 ? ((actual - benchmark) / benchmark) * 100 : 0;
        
        return {
          name: group,
          value: actual,
          benchmark,
          variance
        };
      });
    } else {
      const actual = records[0]?.[config.kpiField] || 0;
      const benchmark = records[0]?.[config.benchmarkField || 'benchmark'] || 0;
      const variance = benchmark > 0 ? ((actual - benchmark) / benchmark) * 100 : 0;
      
      processedData = [{
        name: 'KPI',
        value: actual,
        benchmark,
        variance
      }];
    }
  } else if (config.comparisonType === 'group-comparison') {
    // Simple group comparison
    const groups = config.groups || [...new Set(records.map((r: any) => r[config.groupByField!]))];
    processedData = groups.map(group => {
      const groupRecord = records.find((r: any) => r[config.groupByField!] === group);
      return {
        name: group,
        value: groupRecord?.[config.kpiField] || 0
      };
    });
  }

  // Sort data if requested
  if (config.sortBy) {
    processedData.sort((a, b) => {
      let aVal, bVal;
      
      switch (config.sortBy) {
        case 'name':
          aVal = a.name;
          bVal = b.name;
          break;
        case 'value':
          aVal = a.value;
          bVal = b.value;
          break;
        case 'change':
          aVal = a.change || a.variance || 0;
          bVal = b.change || b.variance || 0;
          break;
        default:
          return 0;
      }
      
      if (config.sortOrder === 'desc') {
        return bVal > aVal ? 1 : -1;
      }
      return aVal > bVal ? 1 : -1;
    });
  }

  const displayType = config.displayType || 'cards';

  return (
    <Card className={cn("h-full flex flex-col", className)}>
      <CardHeader className="pb-2 flex-shrink-0">
        <CardTitle className="text-base">{title}</CardTitle>
        {description && (
          <CardDescription className="text-xs">{description}</CardDescription>
        )}
      </CardHeader>
      <CardContent className="flex-1 overflow-auto">
        {displayType === 'cards' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {processedData.map((item, index) => (
              <KpiCard
                key={index}
                title={item.name}
                value={item.value}
                previousValue={item.previousValue}
                target={item.target}
                change={item.change}
                config={config}
              />
            ))}
          </div>
        )}
        
        {displayType === 'table' && (
          <ComparisonTable data={processedData} config={config} />
        )}
        
        {displayType === 'progress' && (
          <div className="space-y-4">
            {processedData.map((item, index) => (
              <div key={index} className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium">{item.name}</span>
                  <span className="text-sm text-muted-foreground">
                    {formatValue(item.value, config.valueFormat, config.decimals)}
                  </span>
                </div>
                <Progress 
                  value={item.achievement || ((item.value / (item.target || item.benchmark || 100)) * 100)} 
                  className="h-3"
                />
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

KpiComparison.displayName = 'KpiComparison';
KpiComparison.defaultHeight = 4;
KpiComparison.defaultWidth = 6;
KpiComparison.supportedExportFormats = ['png', 'json', 'csv'];
KpiComparison.validateConfiguration = (config: Record<string, any>) => {
  return config.kpiField && config.comparisonType;
};