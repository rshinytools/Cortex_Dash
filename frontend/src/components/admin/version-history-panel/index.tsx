// ABOUTME: Panel component for viewing and managing template version history
// ABOUTME: Shows version timeline, allows comparison, and version restoration

import React, { useEffect, useState } from 'react';
import {
  GitBranch,
  Clock,
  User,
  FileText,
  AlertTriangle,
  CheckCircle,
  Loader2,
  RotateCcw,
  GitCompare,
  Download,
  ChevronRight,
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { useToast } from '@/components/ui/use-toast';
import { cn } from '@/lib/utils';
import { dashboardTemplateApi } from '@/lib/api/dashboard-templates';
import { TemplateVersion, VersionListResponse } from '@/types/template-version';
import { format, formatDistanceToNow } from 'date-fns';

interface VersionHistoryPanelProps {
  templateId: string;
  currentVersion?: string;
  onVersionRestore?: () => void;
  onCompare?: (version1Id: string, version2Id: string) => void;
  className?: string;
}

export function VersionHistoryPanel({
  templateId,
  currentVersion,
  onVersionRestore,
  onCompare,
  className,
}: VersionHistoryPanelProps) {
  const { toast } = useToast();
  const [versions, setVersions] = useState<TemplateVersion[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedVersions, setSelectedVersions] = useState<string[]>([]);
  const [restoreDialogOpen, setRestoreDialogOpen] = useState(false);
  const [versionToRestore, setVersionToRestore] = useState<TemplateVersion | null>(null);
  const [isRestoring, setIsRestoring] = useState(false);

  useEffect(() => {
    fetchVersions();
  }, [templateId]);

  const fetchVersions = async () => {
    try {
      setLoading(true);
      const response = await dashboardTemplateApi.getVersions(templateId, 0, 100);
      setVersions(response.versions);
    } catch (error) {
      console.error('Failed to fetch versions:', error);
      toast({
        title: 'Failed to load version history',
        description: 'Please try again later',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleVersionSelect = (versionId: string) => {
    setSelectedVersions(prev => {
      if (prev.includes(versionId)) {
        return prev.filter(id => id !== versionId);
      }
      if (prev.length >= 2) {
        return [prev[1], versionId];
      }
      return [...prev, versionId];
    });
  };

  const handleRestore = async () => {
    if (!versionToRestore || isRestoring) return;

    try {
      setIsRestoring(true);
      await dashboardTemplateApi.restoreVersion(templateId, versionToRestore.id);
      
      toast({
        title: 'Version restored successfully',
        description: `Template has been restored to version ${versionToRestore.version}`,
      });

      setRestoreDialogOpen(false);
      setVersionToRestore(null);
      onVersionRestore?.();
      fetchVersions(); // Refresh the list
    } catch (error) {
      toast({
        title: 'Failed to restore version',
        description: (error as Error).message,
        variant: 'destructive',
      });
    } finally {
      setIsRestoring(false);
    }
  };

  const getVersionIcon = (version: TemplateVersion) => {
    if (version.auto_created) return <Clock className="h-4 w-4" />;
    if (version.breaking_changes) return <AlertTriangle className="h-4 w-4 text-red-500" />;
    return <GitBranch className="h-4 w-4" />;
  };

  const getVersionBadgeVariant = (versionType: string) => {
    switch (versionType) {
      case 'major':
        return 'destructive';
      case 'minor':
        return 'default';
      case 'patch':
        return 'secondary';
      default:
        return 'outline';
    }
  };

  if (loading) {
    return (
      <Card className={className}>
        <CardContent className="flex items-center justify-center py-8">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <GitBranch className="h-5 w-5" />
            Version History
          </CardTitle>
          <CardDescription>
            View and manage template versions
          </CardDescription>
        </CardHeader>
        <CardContent>
          {selectedVersions.length === 2 && (
            <div className="mb-4 p-3 bg-muted rounded-lg">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">
                  Selected for comparison: {selectedVersions.length} versions
                </span>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    onClick={() => onCompare?.(selectedVersions[0], selectedVersions[1])}
                  >
                    <GitCompare className="h-4 w-4 mr-1" />
                    Compare
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setSelectedVersions([])}
                  >
                    Clear
                  </Button>
                </div>
              </div>
            </div>
          )}

          <ScrollArea className="h-[500px]">
            <div className="space-y-4">
              {versions.map((version, index) => {
                const isSelected = selectedVersions.includes(version.id);
                const isCurrent = version.version === currentVersion;

                return (
                  <div
                    key={version.id}
                    className={cn(
                      'relative p-4 rounded-lg border transition-colors cursor-pointer',
                      isSelected && 'border-primary bg-primary/5',
                      isCurrent && 'bg-muted',
                      !isSelected && !isCurrent && 'hover:bg-muted/50'
                    )}
                    onClick={() => handleVersionSelect(version.id)}
                  >
                    {/* Version Line Connector */}
                    {index < versions.length - 1 && (
                      <div className="absolute left-6 top-12 bottom-0 w-0.5 bg-border" />
                    )}

                    <div className="flex items-start gap-3">
                      {/* Version Icon */}
                      <div className={cn(
                        'flex h-8 w-8 items-center justify-center rounded-full bg-background border-2',
                        isSelected && 'border-primary',
                        isCurrent && 'border-green-500 bg-green-50'
                      )}>
                        {getVersionIcon(version)}
                      </div>

                      {/* Version Content */}
                      <div className="flex-1 space-y-2">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold">v{version.version}</span>
                          <Badge variant={getVersionBadgeVariant(version.version_type)}>
                            {version.version_type}
                          </Badge>
                          {version.auto_created && (
                            <Badge variant="outline" className="text-xs">
                              Auto
                            </Badge>
                          )}
                          {version.breaking_changes && (
                            <Badge variant="destructive" className="text-xs">
                              Breaking Changes
                            </Badge>
                          )}
                          {isCurrent && (
                            <Badge variant="outline" className="text-xs border-green-500 text-green-600">
                              Current
                            </Badge>
                          )}
                        </div>

                        <p className="text-sm text-muted-foreground">
                          {version.change_description}
                        </p>

                        <div className="flex items-center gap-4 text-xs text-muted-foreground">
                          <div className="flex items-center gap-1">
                            <User className="h-3 w-3" />
                            {version.created_by_name}
                          </div>
                          <div className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            <TooltipProvider>
                              <Tooltip>
                                <TooltipTrigger>
                                  {formatDistanceToNow(new Date(version.created_at), { addSuffix: true })}
                                </TooltipTrigger>
                                <TooltipContent>
                                  {format(new Date(version.created_at), 'PPpp')}
                                </TooltipContent>
                              </Tooltip>
                            </TooltipProvider>
                          </div>
                        </div>

                        {/* Version Actions */}
                        <div className="flex gap-2 mt-2">
                          {!isCurrent && (
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={(e) => {
                                e.stopPropagation();
                                setVersionToRestore(version);
                                setRestoreDialogOpen(true);
                              }}
                            >
                              <RotateCcw className="h-3 w-3 mr-1" />
                              Restore
                            </Button>
                          )}
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={(e) => {
                              e.stopPropagation();
                              // TODO: Implement version details view
                            }}
                          >
                            <FileText className="h-3 w-3 mr-1" />
                            Details
                          </Button>
                        </div>
                      </div>

                      {/* Selection Indicator */}
                      {isSelected && (
                        <div className="absolute right-3 top-3">
                          <CheckCircle className="h-5 w-5 text-primary" />
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </ScrollArea>

          {versions.length === 0 && (
            <div className="text-center py-8 text-muted-foreground">
              <GitBranch className="h-12 w-12 mx-auto mb-3 opacity-50" />
              <p>No version history available</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Restore Confirmation Dialog */}
      <Dialog open={restoreDialogOpen} onOpenChange={setRestoreDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Restore Version</DialogTitle>
            <DialogDescription>
              Are you sure you want to restore the template to version {versionToRestore?.version}?
              This will create a new version with the content from the selected version.
            </DialogDescription>
          </DialogHeader>
          {versionToRestore && (
            <div className="space-y-2 py-4">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium">Version:</span>
                <Badge variant={getVersionBadgeVariant(versionToRestore.version_type)}>
                  v{versionToRestore.version}
                </Badge>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium">Created by:</span>
                <span className="text-sm">{versionToRestore.created_by_name}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium">Date:</span>
                <span className="text-sm">
                  {format(new Date(versionToRestore.created_at), 'PPp')}
                </span>
              </div>
              {versionToRestore.breaking_changes && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-md">
                  <div className="flex items-center gap-2 text-red-800">
                    <AlertTriangle className="h-4 w-4" />
                    <span className="text-sm font-medium">
                      This version contains breaking changes
                    </span>
                  </div>
                </div>
              )}
            </div>
          )}
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setRestoreDialogOpen(false)}
              disabled={isRestoring}
            >
              Cancel
            </Button>
            <Button
              onClick={handleRestore}
              disabled={isRestoring}
            >
              {isRestoring ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Restoring...
                </>
              ) : (
                <>
                  <RotateCcw className="h-4 w-4 mr-2" />
                  Restore Version
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}