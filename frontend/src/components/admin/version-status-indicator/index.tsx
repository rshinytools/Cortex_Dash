// ABOUTME: Component that displays current version and auto-save status
// ABOUTME: Shows version number, save status, and provides quick actions

import React, { useEffect, useState } from 'react';
import { Clock, Save, GitBranch, AlertCircle, CheckCircle, Loader2 } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';
import { TemplateVersionStatus } from '@/types/template-version';
import { dashboardTemplateApi } from '@/lib/api/dashboard-templates';

interface VersionStatusIndicatorProps {
  templateId: string;
  currentVersion?: string;
  saveStatus?: string;
  isSaving?: boolean;
  hasChanges?: boolean;
  onSaveNow?: () => void;
  onViewHistory?: () => void;
  className?: string;
}

export function VersionStatusIndicator({
  templateId,
  currentVersion,
  saveStatus,
  isSaving = false,
  hasChanges = false,
  onSaveNow,
  onViewHistory,
  className,
}: VersionStatusIndicatorProps) {
  const [versionStatus, setVersionStatus] = useState<TemplateVersionStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchVersionStatus = async () => {
      try {
        const status = await dashboardTemplateApi.getVersionStatus(templateId);
        setVersionStatus(status);
      } catch (error) {
        console.error('Failed to fetch version status:', error);
      } finally {
        setLoading(false);
      }
    };

    if (templateId) {
      fetchVersionStatus();
    }
  }, [templateId]);

  const getSaveIcon = () => {
    if (isSaving) return <Loader2 className="h-4 w-4 animate-spin" />;
    if (hasChanges) return <AlertCircle className="h-4 w-4 text-yellow-500" />;
    return <CheckCircle className="h-4 w-4 text-green-500" />;
  };

  const getSaveStatusColor = () => {
    if (isSaving) return 'text-muted-foreground';
    if (hasChanges) return 'text-yellow-600';
    return 'text-green-600';
  };

  return (
    <div className={cn('flex items-center gap-4', className)}>
      {/* Version Badge */}
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <Badge
              variant="outline"
              className="flex items-center gap-1 cursor-pointer"
              onClick={onViewHistory}
            >
              <GitBranch className="h-3 w-3" />
              <span>v{currentVersion || versionStatus?.current_version || '0.0.0'}</span>
            </Badge>
          </TooltipTrigger>
          <TooltipContent>
            <div className="space-y-1">
              <p className="font-semibold">Version Information</p>
              {loading ? (
                <p className="text-sm text-muted-foreground">Loading...</p>
              ) : versionStatus ? (
                <>
                  <p className="text-sm">Current: v{versionStatus.current_version}</p>
                  {versionStatus.active_drafts > 0 && (
                    <p className="text-sm text-yellow-600">
                      {versionStatus.active_drafts} active draft{versionStatus.active_drafts > 1 ? 's' : ''}
                    </p>
                  )}
                  {versionStatus.recent_changes > 0 && (
                    <p className="text-sm">
                      {versionStatus.recent_changes} recent change{versionStatus.recent_changes > 1 ? 's' : ''}
                    </p>
                  )}
                  {versionStatus.suggested_version_type && (
                    <p className="text-sm">
                      Next version: {versionStatus.suggested_version_type}
                    </p>
                  )}
                </>
              ) : (
                <p className="text-sm text-muted-foreground">No version data available</p>
              )}
              <p className="text-xs text-muted-foreground mt-2">Click to view history</p>
            </div>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>

      {/* Save Status */}
      {saveStatus && (
        <div className="flex items-center gap-2">
          {getSaveIcon()}
          <span className={cn('text-sm', getSaveStatusColor())}>{saveStatus}</span>
          {hasChanges && onSaveNow && (
            <Button
              size="sm"
              variant="ghost"
              onClick={onSaveNow}
              className="h-7 px-2"
            >
              <Save className="h-3 w-3 mr-1" />
              Save Now
            </Button>
          )}
        </div>
      )}

      {/* Active Users Indicator */}
      {versionStatus && versionStatus.draft_users.length > 1 && (
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Badge variant="secondary" className="flex items-center gap-1">
                <AlertCircle className="h-3 w-3" />
                {versionStatus.draft_users.length} editing
              </Badge>
            </TooltipTrigger>
            <TooltipContent>
              <div className="space-y-1">
                <p className="font-semibold">Active Editors</p>
                {versionStatus.draft_users.map(user => (
                  <p key={user.user_id} className="text-sm">
                    {user.user_name} - {new Date(user.last_update).toLocaleString()}
                  </p>
                ))}
              </div>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      )}

      {/* Last Saved Time */}
      {!isSaving && !hasChanges && versionStatus?.last_version_created && (
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <div className="flex items-center gap-1 text-xs text-muted-foreground">
                <Clock className="h-3 w-3" />
                <span>
                  {new Date(versionStatus.last_version_created).toLocaleDateString()}
                </span>
              </div>
            </TooltipTrigger>
            <TooltipContent>
              Last version created: {new Date(versionStatus.last_version_created).toLocaleString()}
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      )}
    </div>
  );
}