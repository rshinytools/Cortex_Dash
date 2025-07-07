// ABOUTME: Alert notification widget for displaying data alerts and notifications
// ABOUTME: Shows critical alerts, warnings, and informational messages for data quality issues

'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  AlertCircle, 
  AlertTriangle, 
  Info, 
  Loader2, 
  CheckCircle,
  Bell,
  BellOff,
  XCircle,
  Clock,
  TrendingUp,
  Database,
  FileWarning,
  ShieldAlert
} from 'lucide-react';
import { BaseWidgetProps, WidgetComponent } from './base-widget';
import { cn } from '@/lib/utils';
import { DataContract } from '@/types/widget';

interface AlertConfig {
  displayType?: 'list' | 'grouped' | 'summary' | 'timeline';
  showResolved?: boolean;
  maxAlerts?: number;
  severityFilter?: ('critical' | 'high' | 'medium' | 'low' | 'info')[];
  categoryFilter?: string[];
  autoRefresh?: boolean;
  groupBy?: 'severity' | 'category' | 'date';
}

interface Alert {
  id: string;
  title: string;
  message: string;
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  category: 'data_quality' | 'compliance' | 'system' | 'performance' | 'security';
  timestamp: Date;
  status: 'active' | 'acknowledged' | 'resolved';
  source?: string;
  affectedRecords?: number;
  resolution?: string;
  acknowledgedBy?: string;
  acknowledgedAt?: Date;
  resolvedAt?: Date;
}

interface AlertData {
  alerts: Alert[];
  summary: {
    total: number;
    active: number;
    acknowledged: number;
    resolved: number;
    bySeverity: {
      critical: number;
      high: number;
      medium: number;
      low: number;
      info: number;
    };
  };
  lastUpdated?: Date;
}

const getSeverityIcon = (severity: string) => {
  switch (severity) {
    case 'critical': return { icon: XCircle, color: 'text-red-600', bgColor: 'bg-red-50' };
    case 'high': return { icon: AlertTriangle, color: 'text-orange-600', bgColor: 'bg-orange-50' };
    case 'medium': return { icon: AlertCircle, color: 'text-yellow-600', bgColor: 'bg-yellow-50' };
    case 'low': return { icon: Info, color: 'text-blue-600', bgColor: 'bg-blue-50' };
    case 'info': return { icon: Info, color: 'text-gray-600', bgColor: 'bg-gray-50' };
    default: return { icon: Info, color: 'text-gray-600', bgColor: 'bg-gray-50' };
  }
};

const getCategoryIcon = (category: string) => {
  switch (category) {
    case 'data_quality': return Database;
    case 'compliance': return ShieldAlert;
    case 'system': return AlertCircle;
    case 'performance': return TrendingUp;
    case 'security': return ShieldAlert;
    default: return FileWarning;
  }
};

const AlertItem = ({ alert, showDetails = false }: { alert: Alert; showDetails?: boolean }) => {
  const { icon: SeverityIcon, color, bgColor } = getSeverityIcon(alert.severity);
  const CategoryIcon = getCategoryIcon(alert.category);
  const timeAgo = getTimeAgo(new Date(alert.timestamp));

  return (
    <div className={cn(
      "p-3 rounded-lg border transition-colors",
      alert.status === 'resolved' && "opacity-60",
      alert.status === 'active' && alert.severity === 'critical' && "border-red-200 bg-red-50/50"
    )}>
      <div className="flex items-start gap-3">
        <div className={cn("p-1.5 rounded", bgColor)}>
          <SeverityIcon className={cn("h-4 w-4", color)} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2 mb-1">
            <p className="font-medium text-sm">{alert.title}</p>
            <Badge 
              variant={alert.status === 'active' ? 'default' : 'secondary'}
              className="text-xs"
            >
              {alert.status}
            </Badge>
          </div>
          <p className="text-xs text-muted-foreground mb-2">{alert.message}</p>
          <div className="flex items-center gap-4 text-xs text-muted-foreground">
            <div className="flex items-center gap-1">
              <CategoryIcon className="h-3 w-3" />
              <span>{alert.category.replace('_', ' ')}</span>
            </div>
            <div className="flex items-center gap-1">
              <Clock className="h-3 w-3" />
              <span>{timeAgo}</span>
            </div>
            {alert.affectedRecords && (
              <span>{alert.affectedRecords.toLocaleString()} records</span>
            )}
          </div>
          {showDetails && (
            <>
              {alert.source && (
                <p className="text-xs text-muted-foreground mt-1">Source: {alert.source}</p>
              )}
              {alert.resolution && (
                <p className="text-xs text-green-600 mt-1">Resolution: {alert.resolution}</p>
              )}
              {alert.acknowledgedBy && (
                <p className="text-xs text-muted-foreground mt-1">
                  Acknowledged by {alert.acknowledgedBy} at {new Date(alert.acknowledgedAt!).toLocaleString()}
                </p>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

const getTimeAgo = (date: Date): string => {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  
  if (diffMins < 1) return 'just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays}d ago`;
};

export const AlertNotification: WidgetComponent = ({
  title,
  description,
  configuration,
  data,
  loading,
  error,
  className
}) => {
  const config = configuration as AlertConfig;
  const alertData = data as AlertData;

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

  if (!alertData || !alertData.alerts) {
    return (
      <Card className={cn("h-full", className)}>
        <CardContent className="flex flex-col items-center justify-center h-full">
          <BellOff className="h-8 w-8 text-muted-foreground mb-2" />
          <p className="text-sm text-muted-foreground">No alerts</p>
        </CardContent>
      </Card>
    );
  }

  const displayType = config.displayType || 'list';
  let filteredAlerts = alertData.alerts;

  // Apply filters
  if (!config.showResolved) {
    filteredAlerts = filteredAlerts.filter(a => a.status !== 'resolved');
  }
  if (config.severityFilter && config.severityFilter.length > 0) {
    filteredAlerts = filteredAlerts.filter(a => config.severityFilter!.includes(a.severity));
  }
  if (config.categoryFilter && config.categoryFilter.length > 0) {
    filteredAlerts = filteredAlerts.filter(a => config.categoryFilter!.includes(a.category));
  }

  // Sort by severity and timestamp
  filteredAlerts.sort((a, b) => {
    const severityOrder = { critical: 0, high: 1, medium: 2, low: 3, info: 4 };
    if (a.severity !== b.severity) {
      return severityOrder[a.severity] - severityOrder[b.severity];
    }
    return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
  });

  // Limit number of alerts
  if (config.maxAlerts) {
    filteredAlerts = filteredAlerts.slice(0, config.maxAlerts);
  }

  const hasActiveAlerts = alertData.summary.active > 0;
  const hasCriticalAlerts = alertData.summary.bySeverity.critical > 0;

  if (displayType === 'summary') {
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
            <div className={cn("p-2 rounded-lg", hasActiveAlerts ? "bg-red-50" : "bg-green-50")}>
              <Bell className={cn("h-5 w-5", hasActiveAlerts ? "text-red-600" : "text-green-600")} />
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="text-center">
              <p className="text-3xl font-bold">{alertData.summary.active}</p>
              <p className="text-xs text-muted-foreground">Active Alerts</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold">{alertData.summary.acknowledged}</p>
              <p className="text-xs text-muted-foreground">Acknowledged</p>
            </div>
          </div>

          <div className="space-y-2">
            <p className="text-sm font-medium">By Severity</p>
            <div className="space-y-1">
              {Object.entries(alertData.summary.bySeverity).map(([severity, count]) => {
                const { color } = getSeverityIcon(severity);
                return (
                  <div key={severity} className="flex items-center justify-between">
                    <span className={cn("text-xs capitalize", color)}>{severity}</span>
                    <Badge variant={count > 0 ? "default" : "secondary"}>{count}</Badge>
                  </div>
                );
              })}
            </div>
          </div>

          {hasCriticalAlerts && (
            <div className="flex items-center gap-2 p-2 bg-red-50 rounded-md">
              <AlertTriangle className="h-4 w-4 text-red-600" />
              <span className="text-xs text-red-600">
                {alertData.summary.bySeverity.critical} critical alerts require immediate attention
              </span>
            </div>
          )}
        </CardContent>
      </Card>
    );
  }

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
          <div className="flex items-center gap-2">
            {hasCriticalAlerts && (
              <Badge variant="destructive" className="animate-pulse">
                {alertData.summary.bySeverity.critical} Critical
              </Badge>
            )}
            <Badge variant="secondary">
              {alertData.summary.active} Active
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {filteredAlerts.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8">
            <CheckCircle className="h-8 w-8 text-green-600 mb-2" />
            <p className="text-sm text-muted-foreground">All clear!</p>
          </div>
        ) : (
          <ScrollArea className="h-[400px] pr-4">
            <div className="space-y-3">
              {displayType === 'grouped' ? (
                // Group alerts by severity
                Object.entries(
                  filteredAlerts.reduce((acc, alert) => {
                    if (!acc[alert.severity]) acc[alert.severity] = [];
                    acc[alert.severity].push(alert);
                    return acc;
                  }, {} as Record<string, Alert[]>)
                ).map(([severity, alerts]) => (
                  <div key={severity} className="space-y-2">
                    <p className="text-sm font-medium capitalize flex items-center gap-2">
                      {(() => {
                        const { icon: Icon, color } = getSeverityIcon(severity);
                        return (
                          <>
                            <Icon className={cn("h-4 w-4", color)} />
                            {severity} ({alerts.length})
                          </>
                        );
                      })()}
                    </p>
                    <div className="space-y-2 ml-6">
                      {alerts.map(alert => (
                        <AlertItem key={alert.id} alert={alert} />
                      ))}
                    </div>
                  </div>
                ))
              ) : (
                // List view
                filteredAlerts.map(alert => (
                  <AlertItem key={alert.id} alert={alert} showDetails={displayType === 'timeline'} />
                ))
              )}
            </div>
          </ScrollArea>
        )}
      </CardContent>
    </Card>
  );
};

AlertNotification.displayName = 'AlertNotification';
AlertNotification.defaultHeight = 5;
AlertNotification.defaultWidth = 4;
AlertNotification.supportedExportFormats = ['json', 'csv'];

// Data contract for the widget
export const alertNotificationDataContract: DataContract = {
  requiredFields: [
    {
      name: 'alerts',
      type: 'array',
      description: 'List of alert objects',
      commonPatterns: ['alerts', 'notifications', 'messages'],
    },
  ],
  optionalFields: [
    {
      name: 'summary',
      type: 'object',
      description: 'Summary statistics for alerts',
      commonPatterns: ['summary', 'stats', 'overview'],
    },
    {
      name: 'lastUpdated',
      type: 'datetime',
      description: 'Timestamp of last update',
      commonPatterns: ['last_updated', 'updated_at', 'timestamp'],
    },
  ],
  dataSources: {
    primary: {
      datasetType: 'alerts',
      refreshRate: 300, // 5 minutes
    },
  },
};

AlertNotification.dataContract = alertNotificationDataContract;
AlertNotification.validateConfiguration = (config: Record<string, any>) => {
  return true;
};