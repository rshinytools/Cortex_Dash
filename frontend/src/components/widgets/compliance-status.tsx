// ABOUTME: Compliance status widget for showing regulatory compliance status and metrics
// ABOUTME: Displays compliance score, regulatory checks, and violations

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
  Shield,
  ShieldAlert,
  ShieldCheck,
  FileCheck,
  AlertTriangle
} from 'lucide-react';
import { BaseWidgetProps, WidgetComponent } from './base-widget';
import { cn } from '@/lib/utils';
import { DataContract } from '@/types/widget';

interface ComplianceConfig {
  displayType?: 'overview' | 'detailed' | 'regulatory' | 'compact';
  showViolations?: boolean;
  showChecks?: boolean;
  showTrend?: boolean;
  regulations?: string[];
  priorityThreshold?: 'critical' | 'high' | 'medium' | 'low';
}

interface ComplianceData {
  overallCompliance: number;
  regulations: {
    name: string;
    code: string;
    compliance: number;
    status: 'compliant' | 'warning' | 'violation';
    lastAudit?: Date;
  }[];
  checks: {
    category: string;
    passed: number;
    failed: number;
    total: number;
    critical: number;
  }[];
  violations: {
    id: string;
    regulation: string;
    description: string;
    severity: 'critical' | 'high' | 'medium' | 'low';
    dateIdentified: Date;
    status: 'open' | 'resolved' | 'pending';
  }[];
  trend?: number;
  lastAuditDate?: Date;
  nextAuditDate?: Date;
}

const getComplianceStatus = (score: number) => {
  if (score >= 95) return { status: 'compliant', color: 'text-green-600', bgColor: 'bg-green-50', icon: ShieldCheck };
  if (score >= 80) return { status: 'warning', color: 'text-yellow-600', bgColor: 'bg-yellow-50', icon: ShieldAlert };
  return { status: 'violation', color: 'text-destructive', bgColor: 'bg-red-50', icon: Shield };
};

const getSeverityColor = (severity: string) => {
  switch (severity) {
    case 'critical': return 'text-red-600';
    case 'high': return 'text-orange-600';
    case 'medium': return 'text-yellow-600';
    case 'low': return 'text-blue-600';
    default: return 'text-muted-foreground';
  }
};

const RegulationCard = ({ regulation }: { regulation: ComplianceData['regulations'][0] }) => {
  const { status, color, icon: StatusIcon } = getComplianceStatus(regulation.compliance);
  
  return (
    <div className="flex items-center justify-between p-3 border rounded-lg">
      <div className="flex items-center gap-3">
        <StatusIcon className={cn("h-5 w-5", color)} />
        <div>
          <p className="font-medium text-sm">{regulation.name}</p>
          <p className="text-xs text-muted-foreground">{regulation.code}</p>
        </div>
      </div>
      <div className="text-right">
        <p className={cn("font-semibold", color)}>{regulation.compliance}%</p>
        <Badge 
          variant={status === 'compliant' ? 'default' : status === 'warning' ? 'secondary' : 'destructive'}
          className="text-xs"
        >
          {status}
        </Badge>
      </div>
    </div>
  );
};

export const ComplianceStatus: WidgetComponent = ({
  title,
  description,
  configuration,
  data,
  loading,
  error,
  className
}) => {
  const config = configuration as ComplianceConfig;
  const complianceData = data as ComplianceData;

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

  if (!complianceData) {
    return (
      <Card className={cn("h-full", className)}>
        <CardContent className="flex items-center justify-center h-full">
          <p className="text-muted-foreground">No compliance data available</p>
        </CardContent>
      </Card>
    );
  }

  const { overallCompliance = 0 } = complianceData;
  const { status, color, bgColor, icon: StatusIcon } = getComplianceStatus(overallCompliance);
  const displayType = config.displayType || 'overview';

  const openViolations = complianceData.violations?.filter(v => v.status === 'open') || [];
  const criticalViolations = openViolations.filter(v => v.severity === 'critical');

  if (displayType === 'compact') {
    return (
      <Card className={cn("h-full", className)}>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={cn("p-2 rounded-lg", bgColor)}>
                <StatusIcon className={cn("h-6 w-6", color)} />
              </div>
              <div>
                <p className="text-sm font-medium">{title}</p>
                <p className={cn("text-2xl font-bold", color)}>{overallCompliance.toFixed(0)}%</p>
              </div>
            </div>
            {criticalViolations.length > 0 && (
              <Badge variant="destructive" className="animate-pulse">
                {criticalViolations.length} Critical
              </Badge>
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
          <div className={cn("p-2 rounded-lg", bgColor)}>
            <StatusIcon className={cn("h-6 w-6", color)} />
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm text-muted-foreground">Overall Compliance</span>
            <span className={cn("font-bold text-lg", color)}>{overallCompliance.toFixed(0)}%</span>
          </div>
          <Progress value={overallCompliance} className="h-2" />
        </div>

        {displayType === 'overview' && (
          <>
            {complianceData.regulations && complianceData.regulations.length > 0 && (
              <div className="space-y-2">
                {complianceData.regulations.slice(0, 3).map((reg, index) => (
                  <RegulationCard key={index} regulation={reg} />
                ))}
              </div>
            )}

            {openViolations.length > 0 && config.showViolations !== false && (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium">Open Violations</p>
                  <Badge variant="destructive">{openViolations.length}</Badge>
                </div>
                {criticalViolations.length > 0 && (
                  <div className="flex items-center gap-2 p-2 bg-red-50 rounded-md">
                    <AlertTriangle className="h-4 w-4 text-red-600" />
                    <span className="text-xs text-red-600">{criticalViolations.length} critical violations require immediate attention</span>
                  </div>
                )}
              </div>
            )}
          </>
        )}

        {displayType === 'detailed' && (
          <>
            {complianceData.regulations && (
              <div className="space-y-2">
                <p className="text-sm font-medium">Regulatory Compliance</p>
                {complianceData.regulations.map((reg, index) => (
                  <RegulationCard key={index} regulation={reg} />
                ))}
              </div>
            )}

            {config.showChecks && complianceData.checks && (
              <div className="space-y-2">
                <p className="text-sm font-medium">Compliance Checks</p>
                {complianceData.checks.map((check, index) => (
                  <div key={index} className="flex items-center justify-between text-sm">
                    <span>{check.category}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-green-600">{check.passed}</span>
                      <span className="text-muted-foreground">/</span>
                      <span>{check.total}</span>
                      {check.critical > 0 && (
                        <Badge variant="destructive" className="text-xs">{check.critical} critical</Badge>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {config.showViolations && complianceData.violations && (
              <div className="space-y-2">
                <p className="text-sm font-medium">Recent Violations</p>
                {complianceData.violations.slice(0, 5).map((violation) => (
                  <div key={violation.id} className="text-xs space-y-1 p-2 border rounded">
                    <div className="flex items-center justify-between">
                      <span className={cn("font-medium", getSeverityColor(violation.severity))}>
                        {violation.severity.toUpperCase()}
                      </span>
                      <Badge variant={violation.status === 'open' ? 'destructive' : 'secondary'}>
                        {violation.status}
                      </Badge>
                    </div>
                    <p className="text-muted-foreground">{violation.description}</p>
                    <p className="text-muted-foreground">{violation.regulation}</p>
                  </div>
                ))}
              </div>
            )}
          </>
        )}

        {displayType === 'regulatory' && complianceData.regulations && (
          <div className="space-y-3">
            {complianceData.regulations.map((reg, index) => (
              <div key={index} className="space-y-2">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-sm">{reg.name}</p>
                    <p className="text-xs text-muted-foreground">{reg.code}</p>
                  </div>
                  <Badge 
                    variant={reg.status === 'compliant' ? 'default' : reg.status === 'warning' ? 'secondary' : 'destructive'}
                  >
                    {reg.compliance}%
                  </Badge>
                </div>
                <Progress value={reg.compliance} className="h-1.5" />
                {reg.lastAudit && (
                  <p className="text-xs text-muted-foreground">
                    Last audit: {new Date(reg.lastAudit).toLocaleDateString()}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}

        {complianceData.nextAuditDate && (
          <div className="flex items-center justify-between text-xs text-muted-foreground pt-2 border-t">
            <span>Next audit</span>
            <span>{new Date(complianceData.nextAuditDate).toLocaleDateString()}</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

ComplianceStatus.displayName = 'ComplianceStatus';
ComplianceStatus.defaultHeight = 4;
ComplianceStatus.defaultWidth = 4;
ComplianceStatus.supportedExportFormats = ['json', 'csv'];

// Data contract for the widget
export const complianceStatusDataContract: DataContract = {
  requiredFields: [
    {
      name: 'overallCompliance',
      type: 'number',
      description: 'Overall compliance percentage (0-100)',
      commonPatterns: ['compliance_score', 'overall_compliance', 'compliance_pct'],
      validation: {
        min: 0,
        max: 100,
      },
    },
  ],
  optionalFields: [
    {
      name: 'regulations',
      type: 'array',
      description: 'List of regulations with compliance status',
      commonPatterns: ['regulations', 'regulatory_compliance'],
    },
    {
      name: 'checks',
      type: 'array',
      description: 'Compliance check results by category',
      commonPatterns: ['compliance_checks', 'audit_checks'],
    },
    {
      name: 'violations',
      type: 'array',
      description: 'List of compliance violations',
      commonPatterns: ['violations', 'non_compliance', 'findings'],
    },
    {
      name: 'trend',
      type: 'number',
      description: 'Compliance trend percentage',
      commonPatterns: ['trend', 'change', 'delta'],
    },
    {
      name: 'lastAuditDate',
      type: 'datetime',
      description: 'Date of last compliance audit',
      commonPatterns: ['last_audit', 'audit_date', 'last_review'],
    },
    {
      name: 'nextAuditDate',
      type: 'datetime',
      description: 'Date of next scheduled audit',
      commonPatterns: ['next_audit', 'scheduled_audit', 'next_review'],
    },
  ],
  dataSources: {
    primary: {
      datasetType: 'compliance_metrics',
      refreshRate: 86400, // 24 hours
    },
  },
};

ComplianceStatus.dataContract = complianceStatusDataContract;
ComplianceStatus.validateConfiguration = (config: Record<string, any>) => {
  return true;
};