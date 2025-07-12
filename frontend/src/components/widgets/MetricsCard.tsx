// ABOUTME: Metrics Card widget component for displaying single metrics with comparison
// ABOUTME: Supports flexible aggregations, filters, and various display formats

"use client";

import { useMemo } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import {
  TrendingUp,
  TrendingDown,
  Users,
  Activity,
  AlertCircle,
  CheckCircle,
  Info,
  BarChart,
  PieChart,
  Calendar,
  Clock,
  Database,
  FileText,
  Heart,
  Shield,
  Star,
  Target,
  Zap,
  LucideIcon,
} from "lucide-react";

interface MetricsCardProps {
  // Widget instance configuration
  config: {
    title: string;
    subtitle?: string;
    dataMode?: "dynamic" | "static";
    staticValue?: {
      value: number;
      comparisonValue?: number;
    };
    aggregation?: {
      method: "COUNT" | "COUNT_DISTINCT" | "SUM" | "AVG" | "MIN" | "MAX" | "MEDIAN";
      field?: string;
      distinctField?: string;
    };
    comparison?: {
      enabled: boolean;
      type: "previous_extract" | "previous_period" | "baseline";
      showPercentChange: boolean;
      showAbsoluteChange: boolean;
    };
    display?: {
      format: "number" | "percentage" | "currency" | "decimal";
      decimals: number;
      prefix?: string;
      suffix?: string;
      thousandsSeparator: boolean;
      trend?: {
        show: boolean;
        inverted: boolean;
      };
      icon?: string;
      color?: "default" | "primary" | "success" | "warning" | "danger" | "info";
    };
  };
  
  // Data passed from the widget data service
  data?: {
    value: number;
    comparison?: {
      previousValue: number;
      percentChange: number;
      absoluteChange: number;
    };
    lastUpdated?: string;
  };
  
  // Loading and error states
  loading?: boolean;
  error?: string;
}

const iconMap: Record<string, LucideIcon> = {
  users: Users,
  activity: Activity,
  "trending-up": TrendingUp,
  "trending-down": TrendingDown,
  "alert-circle": AlertCircle,
  "check-circle": CheckCircle,
  info: Info,
  "bar-chart": BarChart,
  "pie-chart": PieChart,
  calendar: Calendar,
  clock: Clock,
  database: Database,
  "file-text": FileText,
  heart: Heart,
  shield: Shield,
  star: Star,
  target: Target,
  zap: Zap,
};

const colorClasses = {
  default: "",
  primary: "text-primary",
  success: "text-green-600",
  warning: "text-yellow-600",
  danger: "text-red-600",
  info: "text-blue-600",
};

const backgroundClasses = {
  default: "bg-muted/50",
  primary: "bg-primary/10",
  success: "bg-green-50",
  warning: "bg-yellow-50",
  danger: "bg-red-50",
  info: "bg-blue-50",
};

export function MetricsCard({ config, data, loading, error }: MetricsCardProps) {
  const displayConfig = config.display || {
    format: "number",
    decimals: 0,
    thousandsSeparator: true,
    trend: { show: true, inverted: false },
    color: "default",
  };

  const comparisonConfig = config.comparison || {
    enabled: false,
    type: "previous_extract",
    showPercentChange: true,
    showAbsoluteChange: false,
  };

  // Determine if we're using static or dynamic data
  const isStatic = config.dataMode === "static";
  
  // Get the value to display (static or dynamic)
  const displayValue = useMemo(() => {
    if (isStatic) {
      return config.staticValue?.value ?? 0;
    }
    return data?.value ?? 0;
  }, [isStatic, config.staticValue?.value, data?.value]);

  // Get comparison data for static mode
  const staticComparison = useMemo(() => {
    if (!isStatic || !config.staticValue?.comparisonValue || !comparisonConfig.enabled) {
      return null;
    }
    
    const current = config.staticValue.value ?? 0;
    const previous = config.staticValue.comparisonValue;
    const absoluteChange = current - previous;
    const percentChange = previous !== 0 ? ((current - previous) / previous) * 100 : 0;
    
    return {
      previousValue: previous,
      percentChange,
      absoluteChange,
    };
  }, [isStatic, config.staticValue, comparisonConfig.enabled]);

  // Format the main value
  const formattedValue = useMemo(() => {
    if (displayValue === null || displayValue === undefined) return "—";
    
    let formatted = "";
    const value = displayValue;
    
    switch (displayConfig.format) {
      case "percentage":
        formatted = `${(value * 100).toFixed(displayConfig.decimals)}%`;
        break;
      case "currency":
        formatted = new Intl.NumberFormat("en-US", {
          style: "currency",
          currency: "USD",
          minimumFractionDigits: displayConfig.decimals,
          maximumFractionDigits: displayConfig.decimals,
        }).format(value);
        break;
      case "decimal":
        formatted = value.toFixed(displayConfig.decimals);
        break;
      default: // number
        if (displayConfig.thousandsSeparator) {
          formatted = new Intl.NumberFormat("en-US", {
            minimumFractionDigits: displayConfig.decimals,
            maximumFractionDigits: displayConfig.decimals,
          }).format(value);
        } else {
          formatted = value.toFixed(displayConfig.decimals);
        }
    }
    
    // Add prefix and suffix
    if (displayConfig.prefix) formatted = displayConfig.prefix + formatted;
    if (displayConfig.suffix) formatted = formatted + displayConfig.suffix;
    
    return formatted;
  }, [displayValue, displayConfig]);

  // Determine trend direction and color
  const trendInfo = useMemo(() => {
    if (!comparisonConfig.enabled || !displayConfig.trend?.show) {
      return null;
    }
    
    // Use static comparison if in static mode, otherwise use dynamic data
    const comparison = isStatic ? staticComparison : data?.comparison;
    if (!comparison) {
      return null;
    }
    
    const change = comparison.percentChange;
    const isPositive = change > 0;
    const isNegative = change < 0;
    
    // Invert logic if specified (e.g., for metrics where lower is better)
    const isGood = displayConfig.trend.inverted ? isNegative : isPositive;
    const isBad = displayConfig.trend.inverted ? isPositive : isNegative;
    
    return {
      icon: isPositive ? TrendingUp : isNegative ? TrendingDown : null,
      color: isGood ? "text-green-600" : isBad ? "text-red-600" : "text-muted-foreground",
      text: `${isPositive ? "+" : ""}${change.toFixed(1)}%`,
    };
  }, [comparisonConfig.enabled, displayConfig.trend, isStatic, staticComparison, data?.comparison]);

  // Get icon component
  const IconComponent = displayConfig.icon ? iconMap[displayConfig.icon] : null;

  // Skip loading state for static values
  if (loading && !isStatic) {
    return (
      <Card className="h-full">
        <CardContent className="flex h-full items-center justify-center p-6">
          <div className="animate-pulse">
            <div className="h-4 w-32 bg-muted rounded mb-2" />
            <div className="h-8 w-24 bg-muted rounded" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="h-full border-destructive/50">
        <CardContent className="flex h-full items-center justify-center p-6">
          <div className="text-center">
            <AlertCircle className="h-8 w-8 text-destructive mx-auto mb-2" />
            <p className="text-sm text-destructive">{error}</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="h-full">
      <CardContent className="flex h-full flex-col justify-between p-6">
        <div>
          <div className="flex items-start justify-between mb-2">
            <div className="flex-1">
              <h3 className="text-sm font-medium text-muted-foreground">
                {config.title}
              </h3>
              {config.subtitle && (
                <p className="text-xs text-muted-foreground mt-0.5">
                  {config.subtitle}
                </p>
              )}
            </div>
            {IconComponent && (
              <div
                className={cn(
                  "p-2 rounded-lg",
                  backgroundClasses[displayConfig.color || "default"]
                )}
              >
                <IconComponent
                  className={cn(
                    "h-5 w-5",
                    colorClasses[displayConfig.color || "default"]
                  )}
                />
              </div>
            )}
          </div>
          
          <div className="mt-4">
            <div
              className={cn(
                "text-3xl font-bold",
                colorClasses[displayConfig.color || "default"]
              )}
            >
              {formattedValue}
            </div>
          </div>
        </div>
        
        {trendInfo && (
          <div className="mt-4 flex items-center gap-2">
            {trendInfo.icon && (
              <trendInfo.icon className={cn("h-4 w-4", trendInfo.color)} />
            )}
            <span className={cn("text-sm font-medium", trendInfo.color)}>
              {trendInfo.text}
            </span>
            {comparisonConfig.showAbsoluteChange && (
              <span className="text-sm text-muted-foreground">
                {(() => {
                  const comparison = isStatic ? staticComparison : data?.comparison;
                  if (!comparison) return null;
                  const change = comparison.absoluteChange;
                  return `(${change > 0 ? "+" : ""}${change.toFixed(displayConfig.decimals)})`;
                })()}
              </span>
            )}
            <span className="text-xs text-muted-foreground">
              vs {comparisonConfig.type.replace("_", " ")}
            </span>
          </div>
        )}
        
        {!isStatic && data?.lastUpdated && (
          <div className="mt-2 text-xs text-muted-foreground">
            Last updated: {new Date(data.lastUpdated).toLocaleString()}
          </div>
        )}
      </CardContent>
    </Card>
  );
}