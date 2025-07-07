// ABOUTME: Safety metrics widget for displaying adverse events and safety signals
// ABOUTME: Specialized visualization for clinical trial safety data

'use client';

import React, { useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AlertCircle, Loader2, AlertTriangle, Activity, TrendingUp } from 'lucide-react';
import { BaseWidgetProps, WidgetComponent } from './base-widget';
import { cn } from '@/lib/utils';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
  PieChart,
  Pie,
} from 'recharts';

interface SafetyMetricsConfig {
  displayType: 'summary' | 'ae-by-severity' | 'ae-by-system' | 'sae-timeline';
  severityColors?: {
    mild: string;
    moderate: string;
    severe: string;
    lifeThreatening: string;
  };
  showTrends?: boolean;
  showRelatedOnly?: boolean;
}

interface SafetyData {
  totalAEs?: number;
  totalSAEs?: number;
  totalSubjectsWithAE?: number;
  totalSubjects?: number;
  aesBySeverity?: Array<{
    severity: string;
    count: number;
    percentage?: number;
  }>;
  aesBySystem?: Array<{
    system: string;
    count: number;
    percentage?: number;
  }>;
  saeTimeline?: Array<{
    date: string;
    count: number;
    cumulative: number;
  }>;
  trends?: {
    aeRate: number;
    saeRate: number;
    rateChange: number;
  };
}

const defaultSeverityColors = {
  mild: '#10b981',
  moderate: '#f59e0b',
  severe: '#ef4444',
  lifeThreatening: '#7c3aed',
};

const SafetySummary: React.FC<{ data: SafetyData }> = ({ data }) => {
  const aeRate = data.totalSubjects 
    ? ((data.totalSubjectsWithAE || 0) / data.totalSubjects * 100).toFixed(1)
    : '0';

  return (
    <div className="grid grid-cols-2 gap-4">
      <div className="space-y-4">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Activity className="h-4 w-4 text-blue-600" />
            <p className="text-sm font-medium">Total Adverse Events</p>
          </div>
          <p className="text-2xl font-bold">{data.totalAEs || 0}</p>
          <p className="text-xs text-muted-foreground">
            {data.totalSubjectsWithAE || 0} subjects ({aeRate}%)
          </p>
        </div>
        
        <div>
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="h-4 w-4 text-amber-600" />
            <p className="text-sm font-medium">Serious Adverse Events</p>
          </div>
          <p className="text-2xl font-bold text-amber-600">{data.totalSAEs || 0}</p>
        </div>
      </div>

      <div className="space-y-3">
        {data.aesBySeverity?.slice(0, 4).map((item, index) => (
          <div key={index} className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div 
                className="w-3 h-3 rounded-full"
                style={{ 
                  backgroundColor: defaultSeverityColors[item.severity.toLowerCase() as keyof typeof defaultSeverityColors] || '#6b7280'
                }}
              />
              <span className="text-sm capitalize">{item.severity}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium">{item.count}</span>
              {item.percentage !== undefined && (
                <span className="text-xs text-muted-foreground">
                  ({item.percentage.toFixed(1)}%)
                </span>
              )}
            </div>
          </div>
        ))}
      </div>

      {data.trends && (
        <div className="col-span-2 pt-4 border-t">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <TrendingUp className={cn(
                "h-4 w-4",
                data.trends.rateChange > 0 ? "text-red-600" : "text-green-600"
              )} />
              <span className="text-sm">AE Rate Trend</span>
            </div>
            <Badge variant={data.trends.rateChange > 0 ? "destructive" : "default"}>
              {data.trends.rateChange > 0 ? '+' : ''}{data.trends.rateChange.toFixed(1)}%
            </Badge>
          </div>
        </div>
      )}
    </div>
  );
};

export const SafetyMetrics: WidgetComponent = ({
  title,
  description,
  configuration,
  data,
  loading,
  error,
  className
}) => {
  const config = configuration as SafetyMetricsConfig;
  const safetyData = data as SafetyData;

  const severityColors = config.severityColors || defaultSeverityColors;

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

  if (!safetyData) {
    return (
      <Card className={cn("h-full", className)}>
        <CardContent className="flex items-center justify-center h-full">
          <p className="text-muted-foreground">No safety data available</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={cn("h-full flex flex-col", className)}>
      <CardHeader className="pb-2 flex-shrink-0">
        <CardTitle className="text-base">{title}</CardTitle>
        {description && (
          <CardDescription className="text-xs">{description}</CardDescription>
        )}
      </CardHeader>
      <CardContent className="flex-1">
        {config.displayType === 'summary' && (
          <SafetySummary data={safetyData} />
        )}

        {config.displayType === 'ae-by-severity' && safetyData.aesBySeverity && (
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={safetyData.aesBySeverity}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ severity, count, percentage }) => 
                  `${severity}: ${count} (${percentage?.toFixed(1)}%)`
                }
                outerRadius={80}
                fill="#8884d8"
                dataKey="count"
              >
                {safetyData.aesBySeverity.map((entry, index) => (
                  <Cell 
                    key={`cell-${index}`} 
                    fill={severityColors[entry.severity.toLowerCase() as keyof typeof severityColors] || '#6b7280'} 
                  />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        )}

        {config.displayType === 'ae-by-system' && safetyData.aesBySystem && (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={safetyData.aesBySystem}
              layout="horizontal"
              margin={{ top: 5, right: 30, left: 100, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis dataKey="system" type="category" width={90} />
              <Tooltip />
              <Bar dataKey="count" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        )}

        {config.displayType === 'sae-timeline' && safetyData.saeTimeline && (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={safetyData.saeTimeline}
              margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="date" 
                tick={{ fontSize: 12 }}
                tickFormatter={(value) => {
                  const date = new Date(value);
                  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                }}
              />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Legend />
              <Bar dataKey="count" fill="#ef4444" name="New SAEs" />
              <Bar dataKey="cumulative" fill="#fbbf24" name="Cumulative" />
            </BarChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
};

SafetyMetrics.displayName = 'SafetyMetrics';
SafetyMetrics.defaultHeight = 4;
SafetyMetrics.defaultWidth = 6;
SafetyMetrics.supportedExportFormats = ['png', 'json', 'csv'];
SafetyMetrics.validateConfiguration = (config: Record<string, any>) => {
  return ['summary', 'ae-by-severity', 'ae-by-system', 'sae-timeline'].includes(config.displayType);
};