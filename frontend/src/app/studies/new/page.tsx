// ABOUTME: Study creation page with complete initialization wizard
// ABOUTME: Guides users through the entire study setup process

'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { useSession } from 'next-auth/react';
import { UserMenu } from '@/components/user-menu';
import { InitializationWizard } from '@/components/study/initialization-wizard';
import { studiesApi } from '@/lib/api/studies';
import { useToast } from '@/hooks/use-toast';

export default function NewStudyPage() {
  const router = useRouter();
  const { data: session } = useSession();
  const { toast } = useToast();
  const [draftStudy, setDraftStudy] = useState<any>(null);
  const [checkingDraft, setCheckingDraft] = useState(true);
  const [resumingDraft, setResumingDraft] = useState(false);

  useEffect(() => {
    // Check for draft studies when component mounts
    const checkDraft = async () => {
      try {
        const draft = await studiesApi.checkDraftStudy();
        if (draft.has_draft) {
          // Check if this draft was created very recently (within last 5 minutes)
          const draftAge = new Date().getTime() - new Date(draft.created_at).getTime();
          const fiveMinutes = 5 * 60 * 1000;
          
          // If draft is very recent and user is on step 2 or later, automatically resume
          if (draftAge < fiveMinutes && draft.current_step && draft.current_step > 1) {
            // Don't auto-resume, just show the draft message
            // The initialization page is for progress tracking, not wizard continuation
          }
          
          setDraftStudy(draft);
        }
      } catch (error) {
        console.error('Failed to check for draft study:', error);
      } finally {
        setCheckingDraft(false);
      }
    };
    
    if (session) {
      checkDraft();
    }
  }, [session, router]);

  const handleComplete = (studyId: string) => {
    // Navigate to the initialization progress page
    router.push(`/studies/${studyId}/initialization`);
  };

  const handleCancel = () => {
    // Navigate back to studies list
    router.push('/studies');
  };

  const handleResumeDraft = () => {
    if (draftStudy && draftStudy.study_id) {
      // Set resuming flag to show wizard with draft data
      setResumingDraft(true);
    }
  };

  const handleStartNew = async () => {
    // Delete the draft and start fresh
    if (draftStudy && draftStudy.study_id) {
      try {
        await studiesApi.cancelWizard(draftStudy.study_id);
        setDraftStudy(null);
        toast({
          title: "Starting fresh",
          description: "Previous draft has been cleared. You can now create a new study.",
        });
      } catch (error) {
        console.error('Failed to cancel draft:', error);
        toast({
          title: "Error",
          description: "Failed to clear the draft. Please try again.",
          variant: "destructive",
        });
      }
    }
  };

  if (checkingDraft) {
    return (
      <div className="container mx-auto py-6">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-6">
      <div className="max-w-4xl mx-auto">
        {/* Breadcrumb */}
        <div className="flex items-center gap-2 text-sm text-muted-foreground mb-4">
          <Button
            variant="link"
            className="p-0 h-auto font-normal"
            onClick={() => router.push('/admin')}
          >
            Admin
          </Button>
          <span>/</span>
          <Button
            variant="link"
            className="p-0 h-auto font-normal"
            onClick={() => router.push('/studies')}
          >
            Studies
          </Button>
          <span>/</span>
          <span className="text-foreground">New</span>
        </div>

        <div className="flex items-center mb-6">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => router.push('/studies')}
            className="mr-4"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Studies
          </Button>
          <div className="flex-1">
            <h1 className="text-3xl font-bold">Create New Study</h1>
            <p className="text-muted-foreground mt-1">
              Complete the setup process to start using your study dashboard
            </p>
          </div>
          <UserMenu />
        </div>

        {/* Draft Study Alert - Only show when not resuming */}
        {draftStudy && !resumingDraft && (
          <Alert className="mb-6">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Draft Study Found</AlertTitle>
            <AlertDescription className="mt-2">
              <p>
                You have an incomplete study "{draftStudy.study_name}" started {' '}
                {(() => {
                  const draftDate = new Date(draftStudy.created_at);
                  const now = new Date();
                  const diffMs = now.getTime() - draftDate.getTime();
                  const diffMins = Math.floor(diffMs / (1000 * 60));
                  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
                  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
                  
                  if (diffMins < 1) return 'just now';
                  if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
                  if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
                  return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
                })()}.
              </p>
              <div className="flex gap-2 mt-4">
                <Button onClick={handleResumeDraft} size="sm">
                  Resume Draft
                </Button>
                <Button onClick={handleStartNew} variant="outline" size="sm">
                  Start New Study
                </Button>
                <Button 
                  onClick={async () => {
                    if (confirm(`Are you sure you want to delete the draft study "${draftStudy.study_name}"? This action cannot be undone.`)) {
                      try {
                        await studiesApi.cancelWizard(draftStudy.study_id);
                        toast({
                          title: "Draft deleted",
                          description: "The draft study has been deleted successfully.",
                        });
                        setDraftStudy(null);
                      } catch (error) {
                        toast({
                          title: "Delete failed",
                          description: "Failed to delete the draft study. Please try again.",
                          variant: "destructive",
                        });
                      }
                    }
                  }}
                  variant="destructive" 
                  size="sm"
                >
                  Delete Draft
                </Button>
              </div>
            </AlertDescription>
          </Alert>
        )}

        {(!draftStudy || resumingDraft) && (
          <Card className="p-6">
            <InitializationWizard
              studyId={resumingDraft ? draftStudy?.study_id : undefined}
              initialStep={resumingDraft ? (draftStudy?.current_step - 1 || 0) : 0}
              organizationId={session?.user?.org_id}
              onComplete={handleComplete}
              onCancel={handleCancel}
            />
          </Card>
        )}
      </div>
    </div>
  );
}