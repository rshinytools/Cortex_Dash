// ABOUTME: Statistical summary widget for displaying statistical analysis of datasets
// ABOUTME: Shows mean, median, standard deviation, and other statistical measures

'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  AlertCircle, 
  BarChart3, 
  Loader2, 
  TrendingUp,
  TrendingDown,
  Activity,
  Calculator,
  Percent,
  Hash,
  Sigma
} from 'lucide-react';
import { BaseWidgetProps, WidgetComponent } from './base-widget';
import { cn } from '@/lib/utils';
import { DataContract } from '@/types/widget';

interface StatisticalSummaryConfig {
  displayType?: 'overview' | 'detailed' | 'comparison' | 'distribution';
  showOutliers?: boolean;
  showDistribution?: boolean;
  showTrend?: boolean;
  variables?: string[];
  groupBy?: string;
  decimals?: number;
}

interface StatisticalData {
  variables: {
    name: string;
    displayName?: string;
    statistics: {
      count: number;
      missing: number;
      mean: number;
      median: number;
      mode?: number;
      stdDev: number;
      variance: number;
      min: number;
      max: number;
      q1: number;
      q3: number;
      iqr: number;
      skewness?: number;
      kurtosis?: number;
      cv?: number; // coefficient of variation
    };
    outliers?: {
      count: number;
      percentage: number;
      values?: number[];
    };
    distribution?: {
      bins: { range: string; count: number; percentage: number }[];
      type?: 'normal' | 'skewed' | 'bimodal' | 'uniform';
    };
    trend?: {
      direction: 'increasing' | 'decreasing' | 'stable';
      strength: number;
      pValue?: number;
    };
  }[];
  groups?: {
    name: string;
    variables: StatisticalData['variables'];
  }[];
  lastUpdated?: Date;
}

const formatNumber = (value: number, decimals: number = 2): string => {
  if (value === null || value === undefined) return 'N/A';
  return value.toFixed(decimals);
};

const StatCard = ({ 
  label, 
  value, 
  icon: Icon,
  trend,
  className 
}: { 
  label: string; 
  value: string | number;
  icon?: any;
  trend?: 'up' | 'down';
  className?: string;
}) => {
  return (
    <div className={cn("p-3 border rounded-lg", className)}>
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs text-muted-foreground">{label}</span>
        {Icon && <Icon className="h-3 w-3 text-muted-foreground" />}
      </div>
      <div className="flex items-center gap-2">
        <span className="text-lg font-semibold">{value}</span>
        {trend && (
          trend === 'up' ? 
            <TrendingUp className="h-4 w-4 text-green-600" /> :
            <TrendingDown className="h-4 w-4 text-red-600" />
        )}
      </div>
    </div>
  );
};

const DistributionBar = ({ percentage, label }: { percentage: number; label: string }) => {
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-muted-foreground">{label}</span>
        <span>{percentage.toFixed(1)}%</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div 
          className="bg-primary h-2 rounded-full transition-all duration-300"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};

const VariableSummary = ({ 
  variable, 
  config,
  detailed = false 
}: { 
  variable: StatisticalData['variables'][0];
  config: StatisticalSummaryConfig;
  detailed?: boolean;
}) => {
  const { statistics: stats } = variable;
  const decimals = config.decimals || 2;
  const missingPercentage = (stats.missing / (stats.count + stats.missing)) * 100;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="font-medium">{variable.displayName || variable.name}</h4>
        <div className="flex items-center gap-2">
          {missingPercentage > 10 && (
            <Badge variant="destructive" className="text-xs">
              {missingPercentage.toFixed(0)}% missing
            </Badge>
          )}
          <Badge variant="secondary" className="text-xs">
            n={stats.count}
          </Badge>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <StatCard label="Mean" value={formatNumber(stats.mean, decimals)} icon={Calculator} />
        <StatCard label="Median" value={formatNumber(stats.median, decimals)} icon={Activity} />
        <StatCard label="Std Dev" value={formatNumber(stats.stdDev, decimals)} icon={Sigma} />
        <StatCard label="Range" value={`${formatNumber(stats.min, decimals)} - ${formatNumber(stats.max, decimals)}`} />
      </div>

      {detailed && (
        <>
          <div className="grid grid-cols-3 gap-2">
            <StatCard label="Q1" value={formatNumber(stats.q1, decimals)} />
            <StatCard label="Q3" value={formatNumber(stats.q3, decimals)} />
            <StatCard label="IQR" value={formatNumber(stats.iqr, decimals)} />
          </div>

          {stats.cv !== undefined && (
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Coefficient of Variation</span>
              <span>{formatNumber(stats.cv * 100, 1)}%</span>
            </div>
          )}

          {stats.skewness !== undefined && (
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Skewness</span>
              <span className={cn(
                Math.abs(stats.skewness) > 1 ? "text-yellow-600" : ""
              )}>
                {formatNumber(stats.skewness, 3)}
              </span>
            </div>
          )}
        </>
      )}

      {config.showOutliers && variable.outliers && variable.outliers.count > 0 && (
        <div className="p-2 bg-yellow-50 rounded-md">
          <div className="flex items-center gap-2 text-sm">
            <AlertCircle className="h-4 w-4 text-yellow-600" />
            <span className="text-yellow-800">
              {variable.outliers.count} outliers detected ({variable.outliers.percentage.toFixed(1)}%)
            </span>
          </div>
        </div>
      )}

      {config.showDistribution && variable.distribution && (
        <div className="space-y-2">
          <p className="text-sm font-medium">Distribution</p>
          {variable.distribution.bins.slice(0, 5).map((bin, index) => (
            <DistributionBar key={index} percentage={bin.percentage} label={bin.range} />
          ))}
          {variable.distribution.type && (
            <Badge variant="outline" className="text-xs">
              {variable.distribution.type} distribution
            </Badge>
          )}
        </div>
      )}

      {config.showTrend && variable.trend && (
        <div className="flex items-center justify-between p-2 bg-gray-50 rounded-md">
          <span className="text-sm">Trend</span>
          <div className="flex items-center gap-2">
            {variable.trend.direction === 'increasing' && <TrendingUp className="h-4 w-4 text-green-600" />}
            {variable.trend.direction === 'decreasing' && <TrendingDown className="h-4 w-4 text-red-600" />}
            <span className="text-sm font-medium capitalize">{variable.trend.direction}</span>
            {variable.trend.pValue !== undefined && (
              <Badge variant={variable.trend.pValue < 0.05 ? "default" : "secondary"} className="text-xs">
                p={variable.trend.pValue.toFixed(3)}
              </Badge>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export const StatisticalSummary: WidgetComponent = ({
  title,
  description,
  configuration,
  data,
  loading,
  error,
  className
}) => {
  const config = configuration as StatisticalSummaryConfig;
  const statsData = data as StatisticalData;

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

  if (!statsData || !statsData.variables || statsData.variables.length === 0) {
    return (
      <Card className={cn("h-full", className)}>
        <CardContent className="flex items-center justify-center h-full">
          <p className="text-muted-foreground">No statistical data available</p>
        </CardContent>
      </Card>
    );
  }

  const displayType = config.displayType || 'overview';
  
  // Filter variables if specified
  let variables = statsData.variables;
  if (config.variables && config.variables.length > 0) {
    variables = variables.filter(v => config.variables!.includes(v.name));
  }

  if (displayType === 'overview') {
    return (
      <Card className={cn("h-full", className)}>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-base">{title}</CardTitle>
              {description && (
                <CardDescription className="text-xs mt-1">{description}</CardDescription>
              )}
            </div>
            <BarChart3 className="h-5 w-5 text-muted-foreground" />
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {variables.slice(0, 3).map((variable, index) => (
              <VariableSummary key={index} variable={variable} config={config} />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (displayType === 'detailed') {
    return (
      <Card className={cn("h-full", className)}>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-base">{title}</CardTitle>
              {description && (
                <CardDescription className="text-xs mt-1">{description}</CardDescription>
              )}
            </div>
            <BarChart3 className="h-5 w-5 text-muted-foreground" />
          </div>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue={variables[0]?.name} className="w-full">
            <TabsList className="grid w-full" style={{ gridTemplateColumns: `repeat(${Math.min(variables.length, 4)}, 1fr)` }}>
              {variables.map((variable) => (
                <TabsTrigger key={variable.name} value={variable.name} className="text-xs">
                  {variable.displayName || variable.name}
                </TabsTrigger>
              ))}
            </TabsList>
            {variables.map((variable) => (
              <TabsContent key={variable.name} value={variable.name} className="mt-4">
                <VariableSummary variable={variable} config={config} detailed />
              </TabsContent>
            ))}
          </Tabs>
        </CardContent>
      </Card>
    );
  }

  if (displayType === 'comparison' && statsData.groups) {
    return (
      <Card className={cn("h-full", className)}>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-base">{title}</CardTitle>
              {description && (
                <CardDescription className="text-xs mt-1">{description}</CardDescription>
              )}
            </div>
            <BarChart3 className="h-5 w-5 text-muted-foreground" />
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {statsData.groups.map((group, index) => (
              <div key={index} className="space-y-2">
                <h4 className="font-medium text-sm">{group.name}</h4>
                <div className="grid grid-cols-2 gap-4">
                  {group.variables.slice(0, 2).map((variable, vIndex) => (
                    <div key={vIndex} className="space-y-1">
                      <p className="text-xs text-muted-foreground">{variable.displayName || variable.name}</p>
                      <p className="text-lg font-semibold">{formatNumber(variable.statistics.mean)}</p>
                      <p className="text-xs text-muted-foreground">±{formatNumber(variable.statistics.stdDev)}</p>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  // Default to overview if display type not recognized
  return (
    <Card className={cn("h-full", className)}>
      <CardHeader>
        <CardTitle className="text-base">{title}</CardTitle>
        {description && <CardDescription>{description}</CardDescription>}
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {variables.map((variable, index) => (
            <VariableSummary key={index} variable={variable} config={config} />
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

StatisticalSummary.displayName = 'StatisticalSummary';
StatisticalSummary.defaultHeight = 5;
StatisticalSummary.defaultWidth = 4;
StatisticalSummary.supportedExportFormats = ['json', 'csv'];

// Data contract for the widget
export const statisticalSummaryDataContract: DataContract = {
  requiredFields: [
    {
      name: 'variables',
      type: 'array',
      description: 'Array of variables with their statistical summaries',
      commonPatterns: ['variables', 'statistics', 'summaries'],
    },
  ],
  optionalFields: [
    {
      name: 'groups',
      type: 'array',
      description: 'Grouped statistical summaries',
      commonPatterns: ['groups', 'categories', 'cohorts'],
    },
    {
      name: 'lastUpdated',
      type: 'datetime',
      description: 'Timestamp of last calculation',
      commonPatterns: ['last_updated', 'calculated_at', 'timestamp'],
    },
  ],
  dataSources: {
    primary: {
      datasetType: 'statistical_analysis',
      refreshRate: 3600,
    },
  },
};

StatisticalSummary.dataContract = statisticalSummaryDataContract;
StatisticalSummary.validateConfiguration = (config: Record<string, any>) => {
  return true;
};