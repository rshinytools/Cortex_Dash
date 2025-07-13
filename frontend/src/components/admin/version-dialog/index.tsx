// ABOUTME: Dialog component for creating new template versions
// ABOUTME: Allows users to specify version type, description, and breaking changes

import React, { useState } from 'react';
import {
  GitBranch,
  AlertTriangle,
  Info,
  Save,
  Loader2,
} from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Checkbox } from '@/components/ui/checkbox';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/components/ui/use-toast';
import { dashboardTemplateApi } from '@/lib/api/dashboard-templates';
import { CreateVersionRequest, ChangeType, TemplateVersionStatus } from '@/types/template-version';

interface VersionDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  templateId: string;
  currentVersion?: string;
  versionStatus?: TemplateVersionStatus;
  onVersionCreated?: (version: string) => void;
}

export function VersionDialog({
  open,
  onOpenChange,
  templateId,
  currentVersion,
  versionStatus,
  onVersionCreated,
}: VersionDialogProps) {
  const { toast } = useToast();
  const [isCreating, setIsCreating] = useState(false);
  const [formData, setFormData] = useState<CreateVersionRequest>({
    version_type: versionStatus?.suggested_version_type || 'patch',
    change_description: '',
    breaking_changes: false,
    migration_notes: '',
  });

  const handleSubmit = async () => {
    if (!formData.change_description.trim()) {
      toast({
        title: 'Description required',
        description: 'Please provide a description of the changes',
        variant: 'destructive',
      });
      return;
    }

    try {
      setIsCreating(true);
      const response = await dashboardTemplateApi.createVersion(templateId, formData);
      
      toast({
        title: 'Version created',
        description: `Version ${response.version} has been created successfully`,
      });

      onVersionCreated?.(response.version);
      onOpenChange(false);
      
      // Reset form
      setFormData({
        version_type: 'patch',
        change_description: '',
        breaking_changes: false,
        migration_notes: '',
      });
    } catch (error) {
      toast({
        title: 'Failed to create version',
        description: (error as Error).message,
        variant: 'destructive',
      });
    } finally {
      setIsCreating(false);
    }
  };

  const getNextVersion = () => {
    if (!currentVersion) return '0.1.0';
    
    const [major, minor, patch] = currentVersion.split('.').map(Number);
    
    switch (formData.version_type) {
      case 'major':
        return `${major + 1}.0.0`;
      case 'minor':
        return `${major}.${minor + 1}.0`;
      case 'patch':
      default:
        return `${major}.${minor}.${patch + 1}`;
    }
  };

  const getVersionTypeDescription = (type: ChangeType) => {
    switch (type) {
      case 'major':
        return 'Breaking changes that are not backward compatible';
      case 'minor':
        return 'New features that are backward compatible';
      case 'patch':
        return 'Bug fixes and minor improvements';
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <GitBranch className="h-5 w-5" />
            Create New Version
          </DialogTitle>
          <DialogDescription>
            Create a new version of the template with your current changes
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Current Version Info */}
          <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
            <div>
              <div className="text-sm font-medium">Current Version</div>
              <div className="text-2xl font-mono">{currentVersion || '0.0.0'}</div>
            </div>
            <div className="text-right">
              <div className="text-sm font-medium">New Version</div>
              <div className="text-2xl font-mono text-primary">{getNextVersion()}</div>
            </div>
          </div>

          {/* Version Status Info */}
          {versionStatus && versionStatus.recent_changes > 0 && (
            <Alert>
              <Info className="h-4 w-4" />
              <AlertDescription>
                You have {versionStatus.recent_changes} changes since the last version.
                {versionStatus.change_breakdown.major > 0 && (
                  <span className="block mt-1">
                    Including {versionStatus.change_breakdown.major} major changes
                  </span>
                )}
              </AlertDescription>
            </Alert>
          )}

          {/* Version Type Selection */}
          <div className="space-y-3">
            <Label>Version Type</Label>
            <RadioGroup
              value={formData.version_type}
              onValueChange={(value) => 
                setFormData({ ...formData, version_type: value as ChangeType })
              }
            >
              <div className="space-y-2">
                <div className="flex items-start space-x-3 p-3 rounded-lg border hover:bg-muted/50">
                  <RadioGroupItem value="patch" id="patch" className="mt-1" />
                  <div className="flex-1">
                    <Label htmlFor="patch" className="flex items-center gap-2 cursor-pointer">
                      <Badge variant="secondary">PATCH</Badge>
                      <span>Bug fixes and minor improvements</span>
                    </Label>
                    <p className="text-sm text-muted-foreground mt-1">
                      {getVersionTypeDescription('patch')}
                    </p>
                  </div>
                </div>

                <div className="flex items-start space-x-3 p-3 rounded-lg border hover:bg-muted/50">
                  <RadioGroupItem value="minor" id="minor" className="mt-1" />
                  <div className="flex-1">
                    <Label htmlFor="minor" className="flex items-center gap-2 cursor-pointer">
                      <Badge variant="default">MINOR</Badge>
                      <span>New features</span>
                    </Label>
                    <p className="text-sm text-muted-foreground mt-1">
                      {getVersionTypeDescription('minor')}
                    </p>
                  </div>
                </div>

                <div className="flex items-start space-x-3 p-3 rounded-lg border hover:bg-muted/50">
                  <RadioGroupItem value="major" id="major" className="mt-1" />
                  <div className="flex-1">
                    <Label htmlFor="major" className="flex items-center gap-2 cursor-pointer">
                      <Badge variant="destructive">MAJOR</Badge>
                      <span>Breaking changes</span>
                    </Label>
                    <p className="text-sm text-muted-foreground mt-1">
                      {getVersionTypeDescription('major')}
                    </p>
                  </div>
                </div>
              </div>
            </RadioGroup>
          </div>

          {/* Change Description */}
          <div className="space-y-2">
            <Label htmlFor="description">Change Description</Label>
            <Textarea
              id="description"
              placeholder="Describe the changes in this version..."
              value={formData.change_description}
              onChange={(e) => 
                setFormData({ ...formData, change_description: e.target.value })
              }
              rows={3}
            />
          </div>

          {/* Breaking Changes Checkbox */}
          <div className="flex items-start space-x-3">
            <Checkbox
              id="breaking"
              checked={formData.breaking_changes}
              onCheckedChange={(checked) =>
                setFormData({ ...formData, breaking_changes: checked as boolean })
              }
            />
            <div className="space-y-1">
              <Label htmlFor="breaking" className="flex items-center gap-2 cursor-pointer">
                <AlertTriangle className="h-4 w-4 text-orange-500" />
                This version contains breaking changes
              </Label>
              <p className="text-sm text-muted-foreground">
                Check this if the changes break backward compatibility
              </p>
            </div>
          </div>

          {/* Migration Notes (shown if breaking changes) */}
          {formData.breaking_changes && (
            <div className="space-y-2">
              <Label htmlFor="migration">Migration Notes</Label>
              <Textarea
                id="migration"
                placeholder="Provide instructions for migrating from the previous version..."
                value={formData.migration_notes}
                onChange={(e) => 
                  setFormData({ ...formData, migration_notes: e.target.value })
                }
                rows={3}
              />
            </div>
          )}
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={isCreating}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={isCreating || !formData.change_description.trim()}
          >
            {isCreating ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Creating...
              </>
            ) : (
              <>
                <Save className="h-4 w-4 mr-2" />
                Create Version
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}