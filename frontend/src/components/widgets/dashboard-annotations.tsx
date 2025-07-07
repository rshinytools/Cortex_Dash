// ABOUTME: Dashboard annotations component for adding notes and comments to widgets
// ABOUTME: Enables collaborative annotation of dashboard elements with real-time updates

'use client';

import React, { useState, useCallback, useEffect, useMemo } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { 
  MessageSquare, 
  Plus, 
  Pin, 
  Edit3, 
  Trash2, 
  Reply,
  MoreVertical,
  Check,
  X,
  User,
  Calendar,
  Tag
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { formatDistanceToNow } from 'date-fns';
import { toast } from 'sonner';

export interface Annotation {
  id: string;
  widget_id: string;
  dashboard_id: string;
  user_id: string;
  user_name: string;
  user_avatar?: string;
  content: string;
  type: 'note' | 'comment' | 'highlight' | 'question';
  position?: {
    x: number;
    y: number;
    element?: string;
  };
  tags: string[];
  replies: AnnotationReply[];
  pinned: boolean;
  resolved: boolean;
  created_at: Date;
  updated_at: Date;
  mentions: string[];
}

export interface AnnotationReply {
  id: string;
  user_id: string;
  user_name: string;
  user_avatar?: string;
  content: string;
  created_at: Date;
  updated_at: Date;
}

interface AnnotationMarkerProps {
  annotation: Annotation;
  onClick: () => void;
  className?: string;
}

function AnnotationMarker({ annotation, onClick, className }: AnnotationMarkerProps) {
  const getMarkerIcon = () => {
    switch (annotation.type) {
      case 'question':
        return '?';
      case 'highlight':
        return '★';
      case 'note':
        return '📝';
      default:
        return '💬';
    }
  };

  const getMarkerColor = () => {
    if (annotation.resolved) return 'bg-green-500';
    if (annotation.pinned) return 'bg-yellow-500';
    switch (annotation.type) {
      case 'question':
        return 'bg-blue-500';
      case 'highlight':
        return 'bg-purple-500';
      case 'note':
        return 'bg-gray-500';
      default:
        return 'bg-orange-500';
    }
  };

  return (
    <button
      onClick={onClick}
      className={cn(
        "absolute z-20 w-6 h-6 rounded-full text-white text-xs font-bold",
        "flex items-center justify-center cursor-pointer",
        "hover:scale-110 transition-transform",
        "shadow-lg border-2 border-white",
        getMarkerColor(),
        className
      )}
      style={{
        left: annotation.position?.x || 0,
        top: annotation.position?.y || 0,
      }}
      title={`${annotation.type}: ${annotation.content.substring(0, 50)}...`}
    >
      {getMarkerIcon()}
    </button>
  );
}

interface AnnotationPopoverProps {
  annotation: Annotation;
  onUpdate: (annotation: Annotation) => void;
  onDelete: (annotationId: string) => void;
  onReply: (annotationId: string, content: string) => void;
  currentUserId: string;
}

function AnnotationPopover({
  annotation,
  onUpdate,
  onDelete,
  onReply,
  currentUserId,
}: AnnotationPopoverProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState(annotation.content);
  const [replyContent, setReplyContent] = useState('');
  const [showReplies, setShowReplies] = useState(false);

  const canEdit = annotation.user_id === currentUserId;

  const handleSaveEdit = useCallback(() => {
    if (editContent.trim()) {
      onUpdate({
        ...annotation,
        content: editContent.trim(),
        updated_at: new Date(),
      });
      setIsEditing(false);
      toast.success('Annotation updated');
    }
  }, [annotation, editContent, onUpdate]);

  const handleCancelEdit = useCallback(() => {
    setEditContent(annotation.content);
    setIsEditing(false);
  }, [annotation.content]);

  const handleReply = useCallback(() => {
    if (replyContent.trim()) {
      onReply(annotation.id, replyContent.trim());
      setReplyContent('');
      toast.success('Reply added');
    }
  }, [annotation.id, replyContent, onReply]);

  const handleToggleResolved = useCallback(() => {
    onUpdate({
      ...annotation,
      resolved: !annotation.resolved,
      updated_at: new Date(),
    });
    toast.success(annotation.resolved ? 'Annotation reopened' : 'Annotation resolved');
  }, [annotation, onUpdate]);

  const handleTogglePinned = useCallback(() => {
    onUpdate({
      ...annotation,
      pinned: !annotation.pinned,
      updated_at: new Date(),
    });
    toast.success(annotation.pinned ? 'Annotation unpinned' : 'Annotation pinned');
  }, [annotation, onUpdate]);

  return (
    <Card className="w-80 max-h-96 overflow-hidden">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            <Avatar className="h-6 w-6">
              <AvatarImage src={annotation.user_avatar} />
              <AvatarFallback className="text-xs">
                {annotation.user_name.charAt(0).toUpperCase()}
              </AvatarFallback>
            </Avatar>
            <div>
              <p className="text-sm font-medium">{annotation.user_name}</p>
              <p className="text-xs text-muted-foreground">
                {formatDistanceToNow(annotation.created_at, { addSuffix: true })}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-1">
            <Badge
              variant={annotation.type === 'question' ? 'default' : 'secondary'}
              className="text-xs"
            >
              {annotation.type}
            </Badge>
            <Popover>
              <PopoverTrigger asChild>
                <Button variant="ghost" size="icon" className="h-6 w-6">
                  <MoreVertical className="h-3 w-3" />
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-40" align="end">
                <div className="space-y-1">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="w-full justify-start"
                    onClick={handleTogglePinned}
                  >
                    <Pin className="mr-2 h-3 w-3" />
                    {annotation.pinned ? 'Unpin' : 'Pin'}
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="w-full justify-start"
                    onClick={handleToggleResolved}
                  >
                    <Check className="mr-2 h-3 w-3" />
                    {annotation.resolved ? 'Reopen' : 'Resolve'}
                  </Button>
                  {canEdit && (
                    <>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="w-full justify-start"
                        onClick={() => setIsEditing(true)}
                      >
                        <Edit3 className="mr-2 h-3 w-3" />
                        Edit
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="w-full justify-start text-destructive"
                        onClick={() => onDelete(annotation.id)}
                      >
                        <Trash2 className="mr-2 h-3 w-3" />
                        Delete
                      </Button>
                    </>
                  )}
                </div>
              </PopoverContent>
            </Popover>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-3">
        {/* Content */}
        {isEditing ? (
          <div className="space-y-2">
            <Textarea
              value={editContent}
              onChange={(e) => setEditContent(e.target.value)}
              placeholder="Edit annotation..."
              rows={3}
            />
            <div className="flex gap-2">
              <Button size="sm" onClick={handleSaveEdit}>
                <Check className="mr-1 h-3 w-3" />
                Save
              </Button>
              <Button size="sm" variant="outline" onClick={handleCancelEdit}>
                <X className="mr-1 h-3 w-3" />
                Cancel
              </Button>
            </div>
          </div>
        ) : (
          <p className="text-sm">{annotation.content}</p>
        )}

        {/* Tags */}
        {annotation.tags.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {annotation.tags.map((tag) => (
              <Badge key={tag} variant="outline" className="text-xs">
                <Tag className="mr-1 h-2 w-2" />
                {tag}
              </Badge>
            ))}
          </div>
        )}

        {/* Status indicators */}
        <div className="flex items-center gap-2">
          {annotation.pinned && (
            <Badge variant="secondary" className="text-xs">
              <Pin className="mr-1 h-2 w-2" />
              Pinned
            </Badge>
          )}
          {annotation.resolved && (
            <Badge variant="default" className="text-xs">
              <Check className="mr-1 h-2 w-2" />
              Resolved
            </Badge>
          )}
        </div>

        {/* Replies */}
        {annotation.replies.length > 0 && (
          <div className="space-y-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowReplies(!showReplies)}
              className="text-xs"
            >
              {showReplies ? 'Hide' : 'Show'} {annotation.replies.length} replies
            </Button>

            {showReplies && (
              <div className="space-y-2 pl-2 border-l-2 border-muted">
                {annotation.replies.map((reply) => (
                  <div key={reply.id} className="space-y-1">
                    <div className="flex items-center gap-2">
                      <Avatar className="h-4 w-4">
                        <AvatarImage src={reply.user_avatar} />
                        <AvatarFallback className="text-xs">
                          {reply.user_name.charAt(0).toUpperCase()}
                        </AvatarFallback>
                      </Avatar>
                      <span className="text-xs font-medium">{reply.user_name}</span>
                      <span className="text-xs text-muted-foreground">
                        {formatDistanceToNow(reply.created_at, { addSuffix: true })}
                      </span>
                    </div>
                    <p className="text-xs pl-6">{reply.content}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Reply input */}
        <div className="space-y-2">
          <Textarea
            value={replyContent}
            onChange={(e) => setReplyContent(e.target.value)}
            placeholder="Add a reply..."
            rows={2}
            className="text-sm"
          />
          <Button
            size="sm"
            onClick={handleReply}
            disabled={!replyContent.trim()}
          >
            <Reply className="mr-1 h-3 w-3" />
            Reply
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

interface CreateAnnotationDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (annotation: Omit<Annotation, 'id' | 'created_at' | 'updated_at'>) => void;
  widgetId: string;
  dashboardId: string;
  position?: { x: number; y: number };
  currentUserId: string;
  currentUserName: string;
}

function CreateAnnotationDialog({
  isOpen,
  onClose,
  onSave,
  widgetId,
  dashboardId,
  position,
  currentUserId,
  currentUserName,
}: CreateAnnotationDialogProps) {
  const [content, setContent] = useState('');
  const [type, setType] = useState<Annotation['type']>('comment');
  const [tags, setTags] = useState('');

  const handleSave = useCallback(() => {
    if (content.trim()) {
      const annotation: Omit<Annotation, 'id' | 'created_at' | 'updated_at'> = {
        widget_id: widgetId,
        dashboard_id: dashboardId,
        user_id: currentUserId,
        user_name: currentUserName,
        content: content.trim(),
        type,
        position,
        tags: tags.split(',').map(t => t.trim()).filter(Boolean),
        replies: [],
        pinned: false,
        resolved: false,
        mentions: [],
      };

      onSave(annotation);
      
      // Reset form
      setContent('');
      setTags('');
      onClose();
      
      toast.success('Annotation created');
    }
  }, [content, type, tags, widgetId, dashboardId, currentUserId, currentUserName, position, onSave, onClose]);

  const handleClose = useCallback(() => {
    setContent('');
    setTags('');
    onClose();
  }, [onClose]);

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Add Annotation</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <div className="space-y-2">
            <Label>Type</Label>
            <div className="grid grid-cols-2 gap-2">
              {(['comment', 'note', 'question', 'highlight'] as const).map((t) => (
                <Button
                  key={t}
                  variant={type === t ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setType(t)}
                  className="justify-start"
                >
                  {t.charAt(0).toUpperCase() + t.slice(1)}
                </Button>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <Label>Content</Label>
            <Textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Enter your annotation..."
              rows={4}
            />
          </div>

          <div className="space-y-2">
            <Label>Tags (optional)</Label>
            <Input
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              placeholder="tag1, tag2, tag3"
            />
          </div>

          {position && (
            <div className="text-xs text-muted-foreground">
              Position: ({position.x}, {position.y})
            </div>
          )}

          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={handleClose}>
              Cancel
            </Button>
            <Button onClick={handleSave} disabled={!content.trim()}>
              Create Annotation
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

interface DashboardAnnotationsProps {
  widgetId: string;
  dashboardId: string;
  className?: string;
  currentUserId?: string;
  currentUserName?: string;
  onAnnotationsChange?: (annotations: Annotation[]) => void;
}

export function DashboardAnnotations({
  widgetId,
  dashboardId,
  className,
  currentUserId = 'user-1',
  currentUserName = 'Current User',
  onAnnotationsChange,
}: DashboardAnnotationsProps) {
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const [selectedAnnotation, setSelectedAnnotation] = useState<Annotation | null>(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [createPosition, setCreatePosition] = useState<{ x: number; y: number } | undefined>();
  const [showAnnotations, setShowAnnotations] = useState(true);

  // Mock data - in a real app, this would come from API
  useEffect(() => {
    const mockAnnotations: Annotation[] = [
      {
        id: '1',
        widget_id: widgetId,
        dashboard_id: dashboardId,
        user_id: 'user-1',
        user_name: 'John Doe',
        content: 'This data point looks unusual. Can we verify the source?',
        type: 'question',
        position: { x: 100, y: 50 },
        tags: ['data-quality', 'verification'],
        replies: [
          {
            id: 'reply-1',
            user_id: 'user-2',
            user_name: 'Jane Smith',
            content: 'I checked the source data and it appears to be correct.',
            created_at: new Date(Date.now() - 2 * 60 * 60 * 1000),
            updated_at: new Date(Date.now() - 2 * 60 * 60 * 1000),
          },
        ],
        pinned: false,
        resolved: false,
        created_at: new Date(Date.now() - 24 * 60 * 60 * 1000),
        updated_at: new Date(Date.now() - 24 * 60 * 60 * 1000),
        mentions: [],
      },
      {
        id: '2',
        widget_id: widgetId,
        dashboard_id: dashboardId,
        user_id: 'user-2',
        user_name: 'Jane Smith',
        content: 'Great visualization! This clearly shows the trend we discussed.',
        type: 'comment',
        position: { x: 200, y: 150 },
        tags: ['feedback'],
        replies: [],
        pinned: true,
        resolved: false,
        created_at: new Date(Date.now() - 12 * 60 * 60 * 1000),
        updated_at: new Date(Date.now() - 12 * 60 * 60 * 1000),
        mentions: [],
      },
    ];

    setAnnotations(mockAnnotations);
  }, [widgetId, dashboardId]);

  // Handle double-click to create annotation
  const handleWidgetDoubleClick = useCallback((event: React.MouseEvent) => {
    if (event.detail === 2) { // Double-click
      const rect = event.currentTarget.getBoundingClientRect();
      const position = {
        x: event.clientX - rect.left,
        y: event.clientY - rect.top,
      };
      setCreatePosition(position);
      setShowCreateDialog(true);
    }
  }, []);

  // Handle annotation creation
  const handleCreateAnnotation = useCallback((
    annotationData: Omit<Annotation, 'id' | 'created_at' | 'updated_at'>
  ) => {
    const newAnnotation: Annotation = {
      ...annotationData,
      id: `annotation-${Date.now()}`,
      created_at: new Date(),
      updated_at: new Date(),
    };

    setAnnotations(prev => [...prev, newAnnotation]);
    onAnnotationsChange?.([...annotations, newAnnotation]);
  }, [annotations, onAnnotationsChange]);

  // Handle annotation update
  const handleUpdateAnnotation = useCallback((updatedAnnotation: Annotation) => {
    setAnnotations(prev =>
      prev.map(a => a.id === updatedAnnotation.id ? updatedAnnotation : a)
    );
    onAnnotationsChange?.(annotations.map(a => 
      a.id === updatedAnnotation.id ? updatedAnnotation : a
    ));
  }, [annotations, onAnnotationsChange]);

  // Handle annotation deletion
  const handleDeleteAnnotation = useCallback((annotationId: string) => {
    setAnnotations(prev => prev.filter(a => a.id !== annotationId));
    setSelectedAnnotation(null);
    onAnnotationsChange?.(annotations.filter(a => a.id !== annotationId));
    toast.success('Annotation deleted');
  }, [annotations, onAnnotationsChange]);

  // Handle reply
  const handleReply = useCallback((annotationId: string, content: string) => {
    const reply: AnnotationReply = {
      id: `reply-${Date.now()}`,
      user_id: currentUserId,
      user_name: currentUserName,
      content,
      created_at: new Date(),
      updated_at: new Date(),
    };

    setAnnotations(prev =>
      prev.map(a =>
        a.id === annotationId
          ? { ...a, replies: [...a.replies, reply], updated_at: new Date() }
          : a
      )
    );
  }, [currentUserId, currentUserName]);

  return (
    <div 
      className={cn("relative h-full", className)}
      onDoubleClick={handleWidgetDoubleClick}
    >
      {/* Annotation markers */}
      {showAnnotations && annotations.map((annotation) => (
        <Popover
          key={annotation.id}
          open={selectedAnnotation?.id === annotation.id}
          onOpenChange={(open) => {
            if (!open) setSelectedAnnotation(null);
          }}
        >
          <PopoverTrigger asChild>
            <div>
              <AnnotationMarker
                annotation={annotation}
                onClick={() => setSelectedAnnotation(annotation)}
              />
            </div>
          </PopoverTrigger>
          <PopoverContent 
            className="p-0 w-auto" 
            align="start"
            side="right"
          >
            <AnnotationPopover
              annotation={annotation}
              onUpdate={handleUpdateAnnotation}
              onDelete={handleDeleteAnnotation}
              onReply={handleReply}
              currentUserId={currentUserId}
            />
          </PopoverContent>
        </Popover>
      ))}

      {/* Annotation controls */}
      <div className="absolute top-2 right-2 z-10 flex items-center gap-1">
        <Button
          variant={showAnnotations ? 'default' : 'outline'}
          size="icon"
          className="h-6 w-6"
          onClick={() => setShowAnnotations(!showAnnotations)}
          title={showAnnotations ? 'Hide annotations' : 'Show annotations'}
        >
          <MessageSquare className="h-3 w-3" />
        </Button>
        <Button
          variant="outline"
          size="icon"
          className="h-6 w-6"
          onClick={() => setShowCreateDialog(true)}
          title="Add annotation"
        >
          <Plus className="h-3 w-3" />
        </Button>
      </div>

      {/* Create annotation dialog */}
      <CreateAnnotationDialog
        isOpen={showCreateDialog}
        onClose={() => {
          setShowCreateDialog(false);
          setCreatePosition(undefined);
        }}
        onSave={handleCreateAnnotation}
        widgetId={widgetId}
        dashboardId={dashboardId}
        position={createPosition}
        currentUserId={currentUserId}
        currentUserName={currentUserName}
      />
    </div>
  );
}