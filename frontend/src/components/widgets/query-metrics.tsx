// ABOUTME: Query metrics widget for displaying data quality and query resolution metrics
// ABOUTME: Shows query status, resolution times, and data quality indicators

'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { AlertCircle, Loader2, CheckCircle, Clock, AlertTriangle, XCircle } from 'lucide-react';
import { BaseWidgetProps, WidgetComponent } from './base-widget';
import { cn } from '@/lib/utils';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
} from 'recharts';

interface QueryMetricsConfig {
  displayType: 'summary' | 'status-breakdown' | 'aging-report' | 'by-form';
  showOpenQueries?: boolean;
  showAverageResolutionTime?: boolean;
  ageThresholds?: {
    warning: number; // days
    critical: number; // days
  };
}

interface QueryData {
  totalQueries?: number;
  openQueries?: number;
  closedQueries?: number;
  avgResolutionTime?: number; // in days
  queryRate?: number; // queries per subject
  statusBreakdown?: Array<{
    status: string;
    count: number;
    percentage?: number;
  }>;
  agingReport?: Array<{
    ageGroup: string;
    count: number;
    percentage?: number;
  }>;
  byForm?: Array<{
    formName: string;
    openQueries: number;
    closedQueries: number;
    total: number;
  }>;
  trends?: {
    newQueriesThisWeek: number;
    closedQueriesThisWeek: number;
    resolutionRate: number;
  };
}

const statusColors: Record<string, string> = {
  open: '#f59e0b',
  answered: '#3b82f6',
  closed: '#10b981',
  cancelled: '#6b7280',
  overdue: '#ef4444',
};

const QuerySummary: React.FC<{ data: QueryData; config: QueryMetricsConfig }> = ({ data, config }) => {
  const closureRate = data.totalQueries 
    ? ((data.closedQueries || 0) / data.totalQueries * 100)
    : 0;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-3 gap-4">
        <div>
          <p className="text-sm text-muted-foreground">Total Queries</p>
          <p className="text-2xl font-bold">{data.totalQueries || 0}</p>
        </div>
        <div>
          <p className="text-sm text-muted-foreground">Open Queries</p>
          <p className="text-2xl font-bold text-amber-600">{data.openQueries || 0}</p>
        </div>
        <div>
          <p className="text-sm text-muted-foreground">Closed Queries</p>
          <p className="text-2xl font-bold text-green-600">{data.closedQueries || 0}</p>
        </div>
      </div>

      <div className="space-y-3">
        <div>
          <div className="flex items-center justify-between mb-1">
            <span className="text-sm">Query Closure Rate</span>
            <span className="text-sm font-medium">{closureRate.toFixed(1)}%</span>
          </div>
          <Progress value={closureRate} className="h-2" />
        </div>

        {config.showAverageResolutionTime !== false && data.avgResolutionTime !== undefined && (
          <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm">Avg. Resolution Time</span>
            </div>
            <Badge variant={data.avgResolutionTime > 7 ? "destructive" : "default"}>
              {data.avgResolutionTime.toFixed(1)} days
            </Badge>
          </div>
        )}

        {data.queryRate !== undefined && (
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Queries per Subject</span>
            <span className="text-sm font-medium">{data.queryRate.toFixed(2)}</span>
          </div>
        )}
      </div>

      {data.trends && (
        <div className="grid grid-cols-2 gap-4 pt-4 border-t">
          <div className="text-center">
            <p className="text-2xl font-bold text-blue-600">
              {data.trends.newQueriesThisWeek}
            </p>
            <p className="text-xs text-muted-foreground">New This Week</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-green-600">
              {data.trends.closedQueriesThisWeek}
            </p>
            <p className="text-xs text-muted-foreground">Closed This Week</p>
          </div>
        </div>
      )}
    </div>
  );
};

export const QueryMetrics: WidgetComponent = ({
  title,
  description,
  configuration,
  data,
  loading,
  error,
  className
}) => {
  const config = configuration as QueryMetricsConfig;
  const queryData = data as QueryData;

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

  if (!queryData) {
    return (
      <Card className={cn("h-full", className)}>
        <CardContent className="flex items-center justify-center h-full">
          <p className="text-muted-foreground">No query data available</p>
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
          <QuerySummary data={queryData} config={config} />
        )}

        {config.displayType === 'status-breakdown' && queryData.statusBreakdown && (
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={queryData.statusBreakdown}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={80}
                fill="#8884d8"
                paddingAngle={5}
                dataKey="count"
              >
                {queryData.statusBreakdown.map((entry, index) => (
                  <Cell 
                    key={`cell-${index}`} 
                    fill={statusColors[entry.status.toLowerCase()] || '#6b7280'} 
                  />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        )}

        {config.displayType === 'aging-report' && queryData.agingReport && (
          <div className="space-y-3">
            {queryData.agingReport.map((ageGroup, index) => {
              const isWarning = ageGroup.ageGroup.includes('warning') || 
                               (config.ageThresholds?.warning && 
                                parseInt(ageGroup.ageGroup) > config.ageThresholds.warning);
              const isCritical = ageGroup.ageGroup.includes('critical') || 
                                 (config.ageThresholds?.critical && 
                                  parseInt(ageGroup.ageGroup) > config.ageThresholds.critical);

              return (
                <div key={index} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {isCritical ? (
                        <XCircle className="h-4 w-4 text-red-600" />
                      ) : isWarning ? (
                        <AlertTriangle className="h-4 w-4 text-amber-600" />
                      ) : (
                        <CheckCircle className="h-4 w-4 text-green-600" />
                      )}
                      <span className="text-sm">{ageGroup.ageGroup}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium">{ageGroup.count}</span>
                      {ageGroup.percentage !== undefined && (
                        <span className="text-xs text-muted-foreground">
                          ({ageGroup.percentage.toFixed(1)}%)
                        </span>
                      )}
                    </div>
                  </div>
                  <Progress 
                    value={ageGroup.percentage || 0} 
                    className={cn("h-2", {
                      "bg-red-100": isCritical,
                      "bg-amber-100": isWarning && !isCritical,
                    })}
                  />
                </div>
              );
            })}
          </div>
        )}

        {config.displayType === 'by-form' && queryData.byForm && (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={queryData.byForm}
              margin={{ top: 5, right: 30, left: 20, bottom: 60 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="formName" 
                angle={-45}
                textAnchor="end"
                height={100}
                tick={{ fontSize: 11 }}
              />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="openQueries" stackId="a" fill="#f59e0b" name="Open" />
              <Bar dataKey="closedQueries" stackId="a" fill="#10b981" name="Closed" />
            </BarChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
};

QueryMetrics.displayName = 'QueryMetrics';
QueryMetrics.defaultHeight = 4;
QueryMetrics.defaultWidth = 6;
QueryMetrics.supportedExportFormats = ['png', 'json', 'csv'];
QueryMetrics.validateConfiguration = (config: Record<string, any>) => {
  return ['summary', 'status-breakdown', 'aging-report', 'by-form'].includes(config.displayType);
};