// ABOUTME: Dashboard toolbar component with actions for refresh, export, and view controls
// ABOUTME: Provides centralized dashboard management actions and view mode toggles

'use client';

import React, { useState, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import {
  RefreshCw,
  Download,
  Maximize2,
  Minimize2,
  Settings,
  Share2,
  Clock,
  Filter,
  Calendar,
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { format } from 'date-fns';
import { cn } from '@/lib/utils';
import { ExportManager } from './export-manager';
import { ParameterControls } from '../dashboard/parameter-controls';

interface DashboardToolbarProps {
  dashboardId?: string;
  title?: string;
  description?: string;
  lastUpdated?: Date;
  isFullscreen?: boolean;
  isRefreshing?: boolean;
  onRefresh?: () => void;
  onToggleFullscreen?: () => void;
  onExport?: (format: 'pdf' | 'png' | 'excel') => void;
  onShare?: () => void;
  onSettings?: () => void;
  onTimeRangeChange?: (range: string) => void;
  timeRange?: string;
  className?: string;
  showTimeRange?: boolean;
  showFilters?: boolean;
  onFiltersClick?: () => void;
  filtersActive?: boolean;
  onScheduledExports?: () => void;
  showAdvancedExport?: boolean;
}

const timeRangeOptions = [
  { value: '1h', label: 'Last hour' },
  { value: '24h', label: 'Last 24 hours' },
  { value: '7d', label: 'Last 7 days' },
  { value: '30d', label: 'Last 30 days' },
  { value: '90d', label: 'Last 90 days' },
  { value: '1y', label: 'Last year' },
  { value: 'all', label: 'All time' },
  { value: 'custom', label: 'Custom range' },
];

export function DashboardToolbar({
  dashboardId,
  title,
  description,
  lastUpdated,
  isFullscreen = false,
  isRefreshing = false,
  onRefresh,
  onToggleFullscreen,
  onExport,
  onShare,
  onSettings,
  onTimeRangeChange,
  timeRange = '7d',
  className,
  showTimeRange = true,
  showFilters = false,
  onFiltersClick,
  filtersActive = false,
  onScheduledExports,
  showAdvancedExport = false,
}: DashboardToolbarProps) {
  const [isExporting, setIsExporting] = useState(false);
  const [showExportManager, setShowExportManager] = useState(false);

  const handleExport = useCallback(async (format: 'pdf' | 'png' | 'excel') => {
    if (!onExport) return;
    
    setIsExporting(true);
    try {
      await onExport(format);
    } finally {
      setIsExporting(false);
    }
  }, [onExport]);

  const handleAdvancedExport = useCallback(() => {
    setShowExportManager(true);
  }, []);

  return (
    <div className={cn(
      "flex flex-col gap-4 p-4 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60",
      className
    )}>
      {/* Header row */}
      <div className="flex items-start justify-between">
        <div className="flex-1">
          {title && (
            <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
          )}
          {description && (
            <p className="text-sm text-muted-foreground mt-1">{description}</p>
          )}
          {lastUpdated && (
            <p className="text-xs text-muted-foreground mt-2 flex items-center gap-1">
              <Clock className="h-3 w-3" />
              Last updated: {format(lastUpdated, 'MMM d, yyyy HH:mm:ss')}
            </p>
          )}
        </div>

        {/* Action buttons */}
        <div className="flex items-center gap-2">
          {/* Time range selector */}
          {showTimeRange && onTimeRangeChange && (
            <Select value={timeRange} onValueChange={onTimeRangeChange}>
              <SelectTrigger className="w-[140px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {timeRangeOptions.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}

          {/* Parameters button */}
          <ParameterControls variant="sheet">
            <Button variant="outline" size="default">
              <Settings className="mr-2 h-4 w-4" />
              Parameters
            </Button>
          </ParameterControls>

          {/* Filters button */}
          {showFilters && onFiltersClick && (
            <Button
              variant={filtersActive ? "default" : "outline"}
              size="default"
              onClick={onFiltersClick}
            >
              <Filter className="mr-2 h-4 w-4" />
              Filters
              {filtersActive && (
                <span className="ml-2 h-2 w-2 rounded-full bg-background" />
              )}
            </Button>
          )}

          {/* Refresh button */}
          {onRefresh && (
            <Button
              variant="outline"
              size="icon"
              onClick={onRefresh}
              disabled={isRefreshing}
            >
              <RefreshCw className={cn("h-4 w-4", isRefreshing && "animate-spin")} />
            </Button>
          )}

          {/* Export menu */}
          {onExport && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="icon" disabled={isExporting}>
                  <Download className={cn("h-4 w-4", isExporting && "animate-pulse")} />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuLabel>Export Dashboard</DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => handleExport('pdf')}>
                  Export as PDF
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => handleExport('png')}>
                  Export as Image
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => handleExport('excel')}>
                  Export as Excel
                </DropdownMenuItem>
                {showAdvancedExport && (
                  <>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem onClick={handleAdvancedExport}>
                      Advanced Export...
                    </DropdownMenuItem>
                    {onScheduledExports && (
                      <DropdownMenuItem onClick={onScheduledExports}>
                        <Calendar className="mr-2 h-4 w-4" />
                        Scheduled Exports
                      </DropdownMenuItem>
                    )}
                  </>
                )}
              </DropdownMenuContent>
            </DropdownMenu>
          )}

          {/* Share button */}
          {onShare && (
            <Button variant="outline" size="icon" onClick={onShare}>
              <Share2 className="h-4 w-4" />
            </Button>
          )}

          {/* Settings button */}
          {onSettings && (
            <Button variant="outline" size="icon" onClick={onSettings}>
              <Settings className="h-4 w-4" />
            </Button>
          )}

          {/* Fullscreen toggle */}
          {onToggleFullscreen && (
            <Button variant="outline" size="icon" onClick={onToggleFullscreen}>
              {isFullscreen ? (
                <Minimize2 className="h-4 w-4" />
              ) : (
                <Maximize2 className="h-4 w-4" />
              )}
            </Button>
          )}
        </div>
      </div>

      {/* Export Manager Dialog */}
      {showAdvancedExport && dashboardId && title && (
        <ExportManager
          dashboardId={dashboardId}
          dashboardName={title}
          isOpen={showExportManager}
          onClose={() => setShowExportManager(false)}
        />
      )}
    </div>
  );
}