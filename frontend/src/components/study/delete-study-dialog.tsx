// ABOUTME: Delete study confirmation dialog component
// ABOUTME: Provides UI dialogs for archiving and permanently deleting studies

'use client';

import { useState } from 'react';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Trash2, AlertTriangle } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface DeleteStudyDialogProps {
  study: {
    id: string;
    name: string;
    protocol_number: string;
    status: string;
  };
  onArchive: (studyId: string) => void;
  onDelete: (studyId: string) => void;
  isArchiving?: boolean;
  isDeleting?: boolean;
  isSuperuser?: boolean;
}

export function DeleteStudyDialog({
  study,
  onArchive,
  onDelete,
  isArchiving,
  isDeleting,
  isSuperuser = false,
}: DeleteStudyDialogProps) {
  const [showArchiveDialog, setShowArchiveDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [deleteConfirmText, setDeleteConfirmText] = useState('');
  const { toast } = useToast();

  const handleArchive = () => {
    onArchive(study.id);
    setShowArchiveDialog(false);
  };

  const handleDelete = () => {
    if (deleteConfirmText === study.name) {
      onDelete(study.id);
      setShowDeleteDialog(false);
      setDeleteConfirmText('');
    }
  };

  const isArchived = study.status === 'ARCHIVED';

  return (
    <>
      {/* Archive Button (only show if not already archived) */}
      {!isArchived && (
        <>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowArchiveDialog(true)}
            disabled={isArchiving}
            className="w-full justify-start"
          >
            <Trash2 className="mr-2 h-4 w-4" />
            Archive Study
          </Button>

          <AlertDialog open={showArchiveDialog} onOpenChange={setShowArchiveDialog}>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Archive Study</AlertDialogTitle>
                <AlertDialogDescription>
                  Are you sure you want to archive <strong>{study.name}</strong> (Protocol: {study.protocol_number})?
                  <br /><br />
                  The study will be marked as archived and can be restored later if needed.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction onClick={handleArchive}>
                  Archive Study
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </>
      )}

      {/* Permanent Delete Button (only for superusers) */}
      {isSuperuser && (
        <>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowDeleteDialog(true)}
            disabled={isDeleting}
            className="w-full justify-start text-destructive hover:text-destructive"
          >
            <AlertTriangle className="mr-2 h-4 w-4" />
            Permanently Delete
          </Button>

          <AlertDialog open={showDeleteDialog} onOpenChange={(open) => {
            setShowDeleteDialog(open);
            if (!open) setDeleteConfirmText('');
          }}>
            <AlertDialogContent>
              <AlertDialogHeader>
                <div className="flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-destructive" />
                  <AlertDialogTitle className="text-destructive">
                    Permanently Delete Study
                  </AlertDialogTitle>
                </div>
                <div className="space-y-3">
                  <AlertDialogDescription>
                    <strong className="text-destructive">⚠️ WARNING: This action cannot be undone!</strong>
                  </AlertDialogDescription>
                  
                  <div className="text-sm text-muted-foreground">
                    You are about to permanently delete <strong className="text-foreground">{study.name}</strong> (Protocol: {study.protocol_number}).
                  </div>
                  
                  <div className="text-sm text-muted-foreground">
                    <span>This will permanently remove:</span>
                    <ul className="list-disc list-inside mt-2 space-y-1">
                      <li>All study data and configurations</li>
                      <li>All dashboards and visualizations</li>
                      <li>All uploaded files and documents</li>
                      <li>All audit logs and activity history</li>
                      <li>All user assignments and permissions</li>
                    </ul>
                  </div>
                  
                  <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-md text-sm">
                    <strong>Final Confirmation:</strong> Type the study name <strong className="font-mono">{study.name}</strong> below to confirm deletion.
                  </div>
                  
                  <Input
                    type="text"
                    placeholder={`Type "${study.name}" to confirm`}
                    value={deleteConfirmText}
                    onChange={(e) => setDeleteConfirmText(e.target.value)}
                    className="w-full"
                  />
                </div>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <Button
                  variant="destructive"
                  onClick={handleDelete}
                  disabled={deleteConfirmText !== study.name}
                >
                  Permanently Delete
                </Button>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </>
      )}
    </>
  );
}