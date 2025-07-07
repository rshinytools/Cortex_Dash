// ABOUTME: Data quality indicator widget for displaying data completeness and accuracy metrics
// ABOUTME: Shows data quality score, missing data percentage, and quality trend

'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
  AlertCircle, 
  CheckCircle, 
  Info, 
  Loader2, 
  XCircle,
  TrendingUp,
  TrendingDown,
  Database,
  Activity
} from 'lucide-react';
import { BaseWidgetProps, WidgetComponent } from './base-widget';
import { cn } from '@/lib/utils';
import { DataContract } from '@/types/widget';

interface DataQualityConfig {
  displayType?: 'overview' | 'detailed' | 'compact';
  showTrend?: boolean;
  showBreakdown?: boolean;
  thresholds?: {
    excellent?: number;
    good?: number;
    warning?: number;
    critical?: number;
  };
  metrics?: string[];
}

interface DataQualityData {
  overallScore: number;
  completeness: number;
  accuracy: number;
  consistency: number;
  timeliness: number;
  validity: number;
  uniqueness: number;
  trend?: number;
  trendDirection?: 'up' | 'down' | 'neutral';
  breakdown?: {
    metric: string;
    score: number;
    issues: number;
    status: 'excellent' | 'good' | 'warning' | 'critical';
  }[];
  lastChecked?: Date;
}

const getQualityStatus = (score: number, thresholds?: DataQualityConfig['thresholds']) => {
  const t = thresholds || {
    excellent: 95,
    good: 85,
    warning: 70,
    critical: 50
  };

  if (score >= (t.excellent || 95)) return { status: 'excellent', color: 'text-green-600', icon: CheckCircle };
  if (score >= (t.good || 85)) return { status: 'good', color: 'text-blue-600', icon: Info };
  if (score >= (t.warning || 70)) return { status: 'warning', color: 'text-yellow-600', icon: AlertCircle };
  return { status: 'critical', color: 'text-destructive', icon: XCircle };
};

const MetricCard = ({ 
  label, 
  value, 
  max = 100,
  className 
}: { 
  label: string; 
  value: number; 
  max?: number;
  className?: string;
}) => {
  const percentage = (value / max) * 100;
  const { color } = getQualityStatus(percentage);
  
  return (
    <div className={cn("space-y-2", className)}>
      <div className="flex justify-between text-sm">
        <span className="text-muted-foreground">{label}</span>
        <span className={cn("font-medium", color)}>{value.toFixed(1)}%</span>
      </div>
      <Progress value={percentage} className="h-2" />
    </div>
  );
};

export const DataQualityIndicator: WidgetComponent = ({
  title,
  description,
  configuration,
  data,
  loading,
  error,
  className
}) => {
  const config = configuration as DataQualityConfig;
  const qualityData = data as DataQualityData;

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

  if (!qualityData) {
    return (
      <Card className={cn("h-full", className)}>
        <CardContent className="flex items-center justify-center h-full">
          <p className="text-muted-foreground">No data quality information available</p>
        </CardContent>
      </Card>
    );
  }

  const { overallScore = 0 } = qualityData;
  const { status, color, icon: StatusIcon } = getQualityStatus(overallScore, config.thresholds);
  const displayType = config.displayType || 'overview';

  if (displayType === 'compact') {
    return (
      <Card className={cn("h-full", className)}>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <StatusIcon className={cn("h-8 w-8", color)} />
              <div>
                <p className="text-sm font-medium">{title}</p>
                <p className={cn("text-2xl font-bold", color)}>{overallScore.toFixed(1)}%</p>
              </div>
            </div>
            {config.showTrend && qualityData.trend !== undefined && (
              <div className="flex items-center gap-1">
                {qualityData.trendDirection === 'up' ? (
                  <TrendingUp className="h-4 w-4 text-green-600" />
                ) : qualityData.trendDirection === 'down' ? (
                  <TrendingDown className="h-4 w-4 text-red-600" />
                ) : null}
                <span className={cn(
                  "text-sm",
                  qualityData.trendDirection === 'up' ? "text-green-600" : "text-red-600"
                )}>
                  {qualityData.trend > 0 ? '+' : ''}{qualityData.trend.toFixed(1)}%
                </span>
              </div>
            )}
          </div>
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
          <StatusIcon className={cn("h-6 w-6", color)} />
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="text-center">
          <p className={cn("text-3xl font-bold", color)}>{overallScore.toFixed(1)}%</p>
          <Badge 
            variant={status === 'excellent' ? 'default' : status === 'good' ? 'secondary' : 'destructive'}
            className="mt-1"
          >
            {status.toUpperCase()}
          </Badge>
        </div>

        {displayType === 'overview' && (
          <div className="space-y-3">
            <MetricCard label="Completeness" value={qualityData.completeness || 0} />
            <MetricCard label="Accuracy" value={qualityData.accuracy || 0} />
            <MetricCard label="Consistency" value={qualityData.consistency || 0} />
            <MetricCard label="Timeliness" value={qualityData.timeliness || 0} />
          </div>
        )}

        {displayType === 'detailed' && (
          <div className="space-y-3">
            <MetricCard label="Completeness" value={qualityData.completeness || 0} />
            <MetricCard label="Accuracy" value={qualityData.accuracy || 0} />
            <MetricCard label="Consistency" value={qualityData.consistency || 0} />
            <MetricCard label="Timeliness" value={qualityData.timeliness || 0} />
            <MetricCard label="Validity" value={qualityData.validity || 0} />
            <MetricCard label="Uniqueness" value={qualityData.uniqueness || 0} />
          </div>
        )}

        {config.showBreakdown && qualityData.breakdown && (
          <div className="space-y-2">
            <p className="text-xs font-medium text-muted-foreground">Quality Breakdown</p>
            {qualityData.breakdown.map((item, index) => (
              <div key={index} className="flex items-center justify-between text-xs">
                <span>{item.metric}</span>
                <div className="flex items-center gap-2">
                  <Badge 
                    variant={item.status === 'excellent' || item.status === 'good' ? 'secondary' : 'destructive'}
                    className="text-xs"
                  >
                    {item.score.toFixed(0)}%
                  </Badge>
                  {item.issues > 0 && (
                    <span className="text-muted-foreground">({item.issues} issues)</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {qualityData.lastChecked && (
          <div className="text-xs text-muted-foreground text-center">
            Last checked: {new Date(qualityData.lastChecked).toLocaleString()}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

DataQualityIndicator.displayName = 'DataQualityIndicator';
DataQualityIndicator.defaultHeight = 4;
DataQualityIndicator.defaultWidth = 3;
DataQualityIndicator.supportedExportFormats = ['json', 'csv'];

// Data contract for the widget
export const dataQualityIndicatorDataContract: DataContract = {
  requiredFields: [
    {
      name: 'overallScore',
      type: 'number',
      description: 'Overall data quality score (0-100)',
      commonPatterns: ['quality_score', 'overall_score', 'dq_score'],
      validation: {
        min: 0,
        max: 100,
      },
    },
  ],
  optionalFields: [
    {
      name: 'completeness',
      type: 'number',
      description: 'Data completeness percentage',
      commonPatterns: ['completeness', 'complete_pct', 'data_completeness'],
      validation: {
        min: 0,
        max: 100,
      },
    },
    {
      name: 'accuracy',
      type: 'number',
      description: 'Data accuracy percentage',
      commonPatterns: ['accuracy', 'accurate_pct', 'data_accuracy'],
      validation: {
        min: 0,
        max: 100,
      },
    },
    {
      name: 'consistency',
      type: 'number',
      description: 'Data consistency percentage',
      commonPatterns: ['consistency', 'consistent_pct', 'data_consistency'],
      validation: {
        min: 0,
        max: 100,
      },
    },
    {
      name: 'timeliness',
      type: 'number',
      description: 'Data timeliness percentage',
      commonPatterns: ['timeliness', 'timely_pct', 'data_timeliness'],
      validation: {
        min: 0,
        max: 100,
      },
    },
    {
      name: 'validity',
      type: 'number',
      description: 'Data validity percentage',
      commonPatterns: ['validity', 'valid_pct', 'data_validity'],
      validation: {
        min: 0,
        max: 100,
      },
    },
    {
      name: 'uniqueness',
      type: 'number',
      description: 'Data uniqueness percentage',
      commonPatterns: ['uniqueness', 'unique_pct', 'data_uniqueness'],
      validation: {
        min: 0,
        max: 100,
      },
    },
    {
      name: 'trend',
      type: 'number',
      description: 'Quality score trend percentage',
      commonPatterns: ['trend', 'change', 'delta'],
    },
    {
      name: 'trendDirection',
      type: 'string',
      description: 'Direction of quality trend',
      commonPatterns: ['trend_direction', 'direction'],
      validation: {
        enum: ['up', 'down', 'neutral'],
      },
    },
    {
      name: 'lastChecked',
      type: 'datetime',
      description: 'Timestamp of last quality check',
      commonPatterns: ['last_checked', 'checked_at', 'updated_at'],
    },
  ],
  calculatedFields: [
    {
      name: 'overallScore',
      type: 'number',
      description: 'Calculate overall score if not provided',
      calculation: '(completeness + accuracy + consistency + timeliness + validity + uniqueness) / 6',
      dependsOn: ['completeness', 'accuracy', 'consistency', 'timeliness', 'validity', 'uniqueness'],
    },
  ],
  dataSources: {
    primary: {
      datasetType: 'quality_metrics',
      refreshRate: 3600,
    },
  },
};

DataQualityIndicator.dataContract = dataQualityIndicatorDataContract;
DataQualityIndicator.validateConfiguration = (config: Record<string, any>) => {
  return true;
};