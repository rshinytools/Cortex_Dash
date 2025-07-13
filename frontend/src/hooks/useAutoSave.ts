// ABOUTME: Hook for automatic saving of template drafts
// ABOUTME: Handles periodic saves, conflict detection, and save status

import { useEffect, useRef, useState, useCallback } from 'react';
import { useToast } from '@/hooks/use-toast';
import { dashboardTemplateApi } from '@/lib/api/dashboard-templates';
import { TemplateDraft } from '@/types/template-version';

interface UseAutoSaveOptions {
  templateId: string;
  content: any;
  enabled?: boolean;
  interval?: number; // milliseconds
  onSaveSuccess?: (draft: TemplateDraft) => void;
  onSaveError?: (error: Error) => void;
  onChange?: (content: any) => void;
}

interface AutoSaveState {
  isSaving: boolean;
  lastSaved: Date | null;
  hasChanges: boolean;
  draft: TemplateDraft | null;
  error: Error | null;
}

export function useAutoSave({
  templateId,
  content,
  enabled = true,
  interval = 30000, // 30 seconds default
  onSaveSuccess,
  onSaveError,
  onChange,
}: UseAutoSaveOptions) {
  const { toast } = useToast();
  const [state, setState] = useState<AutoSaveState>({
    isSaving: false,
    lastSaved: null,
    hasChanges: false,
    draft: null,
    error: null,
  });

  const saveTimeoutRef = useRef<NodeJS.Timeout | undefined>(undefined);
  const lastContentRef = useRef<string>('');
  const isInitializedRef = useRef(false);

  // Initialize draft
  useEffect(() => {
    if (!enabled || !templateId || isInitializedRef.current) return;

    const initializeDraft = async () => {
      try {
        const draft = await dashboardTemplateApi.getDraft(templateId);
        setState(prev => ({ ...prev, draft }));
        lastContentRef.current = JSON.stringify(draft.draft_content);
        isInitializedRef.current = true;
      } catch (error) {
        console.error('Failed to initialize draft:', error);
        setState(prev => ({ ...prev, error: error as Error }));
      }
    };

    initializeDraft();
  }, [templateId, enabled]);

  // Save draft function
  const saveDraft = useCallback(async () => {
    if (!enabled || !templateId || state.isSaving) return;

    setState(prev => ({ ...prev, isSaving: true, error: null }));

    try {
      const draft = await dashboardTemplateApi.updateDraft(templateId, content);
      
      setState(prev => ({
        ...prev,
        isSaving: false,
        lastSaved: new Date(),
        hasChanges: false,
        draft,
      }));

      lastContentRef.current = JSON.stringify(content);
      onSaveSuccess?.(draft);
    } catch (error) {
      const err = error as Error;
      setState(prev => ({
        ...prev,
        isSaving: false,
        error: err,
      }));

      toast({
        title: 'Auto-save failed',
        description: err.message || 'Failed to save changes',
        variant: 'destructive',
      });

      onSaveError?.(err);
    }
  }, [enabled, templateId, content, state.isSaving, onSaveSuccess, onSaveError, toast]);

  // Detect changes
  useEffect(() => {
    if (!enabled) return;

    const contentStr = JSON.stringify(content);
    const hasChanges = contentStr !== lastContentRef.current;

    setState(prev => ({ ...prev, hasChanges }));

    if (hasChanges) {
      // Clear existing timeout
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }

      // Set new timeout
      saveTimeoutRef.current = setTimeout(() => {
        saveDraft();
      }, interval);
    }

    return () => {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
    };
  }, [content, enabled, interval, saveDraft]);

  // Manual save function
  const saveNow = useCallback(async () => {
    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current);
    }
    await saveDraft();
  }, [saveDraft]);

  // Discard changes
  const discardChanges = useCallback(async () => {
    if (!templateId) return;

    try {
      await dashboardTemplateApi.discardDraft(templateId);
      setState(prev => ({
        ...prev,
        draft: null,
        hasChanges: false,
        lastSaved: null,
      }));
      
      toast({
        title: 'Changes discarded',
        description: 'Your draft has been discarded',
      });

      // Reset to original content if onChange is provided
      if (onChange && state.draft) {
        onChange(state.draft.draft_content);
      }
    } catch (error) {
      toast({
        title: 'Failed to discard changes',
        description: (error as Error).message,
        variant: 'destructive',
      });
    }
  }, [templateId, state.draft, onChange, toast]);

  // Get save status text
  const getSaveStatus = useCallback(() => {
    if (state.isSaving) return 'Saving...';
    if (state.error) return 'Save failed';
    if (state.hasChanges) return 'Unsaved changes';
    if (state.lastSaved) {
      const now = new Date();
      const diff = now.getTime() - state.lastSaved.getTime();
      const minutes = Math.floor(diff / 60000);
      
      if (minutes === 0) return 'Saved just now';
      if (minutes === 1) return 'Saved 1 minute ago';
      if (minutes < 60) return `Saved ${minutes} minutes ago`;
      
      const hours = Math.floor(minutes / 60);
      if (hours === 1) return 'Saved 1 hour ago';
      return `Saved ${hours} hours ago`;
    }
    return 'All changes saved';
  }, [state]);

  return {
    ...state,
    saveNow,
    discardChanges,
    getSaveStatus,
  };
}