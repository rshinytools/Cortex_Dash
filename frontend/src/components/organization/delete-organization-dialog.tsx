// ABOUTME: Delete organization confirmation dialog with safety checks
// ABOUTME: Supports both soft delete (deactivate) and hard delete with cascade options

import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { AlertTriangle, Trash2, Power } from 'lucide-react';

interface DeleteOrganizationDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  organization: {
    id: string;
    name: string;
    slug: string;
  };
  stats?: {
    user_count: number;
    study_count: number;
  };
  onDelete: (hardDelete: boolean, force: boolean) => void;
  isDeleting: boolean;
}

export function DeleteOrganizationDialog({
  open,
  onOpenChange,
  organization,
  stats,
  onDelete,
  isDeleting,
}: DeleteOrganizationDialogProps) {
  const [hardDelete, setHardDelete] = useState(false);
  const [force, setForce] = useState(false);
  const [confirmName, setConfirmName] = useState('');

  const hasData = stats && (stats.user_count > 0 || stats.study_count > 0);
  const isConfirmed = confirmName === organization.name;

  const handleDelete = () => {
    if (isConfirmed) {
      onDelete(hardDelete, force);
    }
  };

  const handleClose = () => {
    // Reset state when closing
    setHardDelete(false);
    setForce(false);
    setConfirmName('');
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-red-600">
            <AlertTriangle className="h-5 w-5" />
            Delete Organization
          </DialogTitle>
          <DialogDescription>
            This action cannot be undone. Please review carefully before proceeding.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Organization Info */}
          <div className="rounded-lg border p-3 bg-gray-50 dark:bg-gray-800">
            <div className="text-sm space-y-1">
              <div className="font-medium">{organization.name}</div>
              <div className="text-muted-foreground">ID: {organization.slug}</div>
              {stats && (
                <div className="text-muted-foreground mt-2">
                  Contains: {stats.user_count} users, {stats.study_count} studies
                </div>
              )}
            </div>
          </div>

          {/* Warning for organizations with data */}
          {hasData && (
            <Alert variant="destructive">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                <strong>Warning:</strong> This organization has {stats.user_count} user(s) and {stats.study_count} study(ies). 
                {hardDelete ? ' All associated data will be permanently deleted!' : ' Deactivating will preserve the data but prevent access.'}
              </AlertDescription>
            </Alert>
          )}

          {/* Delete Options */}
          <div className="space-y-3">
            <div className="flex items-center space-x-2">
              <Checkbox
                id="hardDelete"
                checked={hardDelete}
                onCheckedChange={(checked) => setHardDelete(checked as boolean)}
              />
              <Label 
                htmlFor="hardDelete" 
                className="text-sm font-normal cursor-pointer"
              >
                Permanently delete (cannot be recovered)
              </Label>
            </div>

            {hardDelete && hasData && (
              <div className="flex items-center space-x-2 pl-6">
                <Checkbox
                  id="force"
                  checked={force}
                  onCheckedChange={(checked) => setForce(checked as boolean)}
                />
                <Label 
                  htmlFor="force" 
                  className="text-sm font-normal cursor-pointer text-red-600"
                >
                  Force delete all associated users and studies
                </Label>
              </div>
            )}
          </div>

          {/* Confirmation Input */}
          <div className="space-y-2">
            <Label htmlFor="confirmName">
              Type <span className="font-mono font-semibold">{organization.name}</span> to confirm:
            </Label>
            <input
              id="confirmName"
              type="text"
              value={confirmName}
              onChange={(e) => setConfirmName(e.target.value)}
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              placeholder="Enter organization name"
              autoComplete="off"
            />
          </div>

          {/* Action Description */}
          <div className="text-sm text-muted-foreground">
            {hardDelete ? (
              <div className="flex items-center gap-2">
                <Trash2 className="h-4 w-4" />
                <span>
                  Organization will be permanently deleted
                  {hasData && force && ' along with all associated data'}
                </span>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Power className="h-4 w-4" />
                <span>Organization will be deactivated (can be reactivated later)</span>
              </div>
            )}
          </div>
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={handleClose}
            disabled={isDeleting}
          >
            Cancel
          </Button>
          <Button
            variant="destructive"
            onClick={handleDelete}
            disabled={!isConfirmed || isDeleting || (hardDelete && hasData && !force)}
            className="gap-2"
          >
            {isDeleting ? (
              <>Deleting...</>
            ) : hardDelete ? (
              <>
                <Trash2 className="h-4 w-4" />
                Delete Permanently
              </>
            ) : (
              <>
                <Power className="h-4 w-4" />
                Deactivate
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}