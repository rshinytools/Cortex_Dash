// ABOUTME: Component for switching between different upload versions
// ABOUTME: Displays version list with activation controls and comparison options

import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Check,
  Clock,
  Database,
  GitCompare,
  AlertCircle,
} from 'lucide-react';
import { format } from 'date-fns';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useToast } from '@/hooks/use-toast';
import { dataUploadsApi, DataSourceUpload } from '@/lib/api/data-uploads';
import { VersionComparison } from './VersionComparison';
import { formatBytes } from '@/lib/utils';

interface VersionSwitcherProps {
  studyId: string;
  currentVersionId: string;
  availableVersions: DataSourceUpload[];
  onClose?: () => void;
}

export function VersionSwitcher({
  studyId,
  currentVersionId,
  availableVersions,
  onClose,
}: VersionSwitcherProps) {
  const [selectedVersionId, setSelectedVersionId] = useState(currentVersionId);
  const [compareMode, setCompareMode] = useState(false);
  const [compareVersionId, setCompareVersionId] = useState<string>('');
  const { toast } = useToast();
  const queryClient = useQueryClient();

  // Sort versions by version number descending
  const sortedVersions = [...availableVersions].sort((a, b) => b.version_number - a.version_number);

  const activateMutation = useMutation({
    mutationFn: (versionId: string) => dataUploadsApi.activateVersion(studyId, versionId),
    onSuccess: () => {
      toast({
        title: 'Version activated',
        description: 'The selected version is now active.',
      });
      queryClient.invalidateQueries({ queryKey: ['dataUploads', studyId] });
      onClose?.();
    },
    onError: (err: any) => {
      toast({
        title: 'Activation failed',
        description: err.response?.data?.detail || 'Failed to activate version',
        variant: 'destructive',
      });
    },
  });

  const handleActivate = () => {
    if (selectedVersionId !== currentVersionId) {
      activateMutation.mutate(selectedVersionId);
    }
  };

  const handleCompare = () => {
    const otherVersions = sortedVersions.filter(v => v.id !== selectedVersionId);
    if (otherVersions.length > 0) {
      setCompareVersionId(otherVersions[0].id);
      setCompareMode(true);
    }
  };

  if (compareMode && compareVersionId) {
    return (
      <div>
        <div className="mb-4">
          <Button 
            variant="ghost" 
            size="sm"
            onClick={() => setCompareMode(false)}
          >
            ← Back to Version List
          </Button>
        </div>
        <VersionComparison
          studyId={studyId}
          version1Id={selectedVersionId}
          version2Id={compareVersionId}
          onVersionSwitch={(versionId) => {
            setSelectedVersionId(versionId);
            setCompareMode(false);
            handleActivate();
          }}
          onClose={() => setCompareMode(false)}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium mb-1">Select Version</h3>
        <p className="text-sm text-muted-foreground">
          Choose which version of the data to use for dashboards and analysis.
        </p>
      </div>

      <RadioGroup value={selectedVersionId} onValueChange={setSelectedVersionId}>
        <div className="space-y-3">
          {sortedVersions.map((version) => (
            <label
              key={version.id}
              className="flex items-start space-x-3 p-4 rounded-lg border cursor-pointer hover:bg-muted/50 transition-colors"
              htmlFor={version.id}
            >
              <RadioGroupItem value={version.id} id={version.id} className="mt-1" />
              <div className="flex-1 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-medium">Version {version.version_number}</span>
                    {version.id === currentVersionId && (
                      <Badge variant="default" className="text-xs">
                        <Check className="mr-1 h-3 w-3" />
                        Active
                      </Badge>
                    )}
                    {version.status === 'completed' && (
                      <Badge variant="outline" className="text-xs">
                        <Database className="mr-1 h-3 w-3" />
                        Ready
                      </Badge>
                    )}
                  </div>
                  <span className="text-sm text-muted-foreground">
                    {format(new Date(version.upload_timestamp), 'MMM d, yyyy h:mm a')}
                  </span>
                </div>
                
                <div className="text-sm text-muted-foreground">
                  <div className="flex items-center gap-4">
                    <span>{version.upload_name}</span>
                    <span>•</span>
                    <span>{version.files_extracted?.length || 0} files</span>
                    <span>•</span>
                    <span>{formatBytes(version.file_size_mb * 1024 * 1024)}</span>
                    {version.total_rows && (
                      <>
                        <span>•</span>
                        <span>{version.total_rows.toLocaleString()} rows</span>
                      </>
                    )}
                  </div>
                  {version.description && (
                    <p className="mt-1">{version.description}</p>
                  )}
                </div>
              </div>
            </label>
          ))}
        </div>
      </RadioGroup>

      {selectedVersionId !== currentVersionId && (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Switching versions will affect all dashboards and widgets using this study's data. 
            Consider comparing versions first to understand the changes.
          </AlertDescription>
        </Alert>
      )}

      <div className="flex items-center justify-between">
        <Button
          variant="outline"
          onClick={handleCompare}
          disabled={sortedVersions.length < 2}
        >
          <GitCompare className="mr-2 h-4 w-4" />
          Compare Versions
        </Button>
        
        <div className="flex gap-2">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button 
            onClick={handleActivate}
            disabled={selectedVersionId === currentVersionId || activateMutation.isPending}
          >
            {activateMutation.isPending ? (
              <>
                <Clock className="mr-2 h-4 w-4 animate-spin" />
                Activating...
              </>
            ) : (
              'Activate Version'
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}