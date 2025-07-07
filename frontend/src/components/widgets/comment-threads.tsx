// ABOUTME: Comment threads component for managing discussion threads on dashboard elements
// ABOUTME: Provides structured commenting system with threading, mentions, and real-time updates

'use client';

import React, { useState, useCallback, useEffect, useMemo } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { 
  MessageCircle, 
  Send, 
  Reply, 
  MoreVertical,
  Pin,
  Trash2,
  Edit3,
  Heart,
  AtSign,
  Hash,
  Check,
  X,
  Plus,
  Filter,
  Search
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { formatDistanceToNow, format } from 'date-fns';
import { toast } from 'sonner';

export interface CommentThread {
  id: string;
  dashboard_id: string;
  widget_id?: string;
  title: string;
  description?: string;
  status: 'open' | 'resolved' | 'closed';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  tags: string[];
  participants: string[];
  created_by: string;
  created_at: Date;
  updated_at: Date;
  resolved_at?: Date;
  resolved_by?: string;
  comments: Comment[];
  pinned: boolean;
}

export interface Comment {
  id: string;
  thread_id: string;
  user_id: string;
  user_name: string;
  user_avatar?: string;
  content: string;
  parent_comment_id?: string;
  mentions: string[];
  reactions: CommentReaction[];
  edited: boolean;
  created_at: Date;
  updated_at: Date;
}

export interface CommentReaction {
  id: string;
  comment_id: string;
  user_id: string;
  emoji: string;
  created_at: Date;
}

interface CommentThreadCardProps {
  thread: CommentThread;
  currentUserId: string;
  onUpdate: (thread: CommentThread) => void;
  onDelete: (threadId: string) => void;
  className?: string;
}

function CommentThreadCard({
  thread,
  currentUserId,
  onUpdate,
  onDelete,
  className,
}: CommentThreadCardProps) {
  const [showComments, setShowComments] = useState(false);
  const [newComment, setNewComment] = useState('');
  const [replyingTo, setReplyingTo] = useState<string | null>(null);
  const [editingComment, setEditingComment] = useState<string | null>(null);
  const [editContent, setEditContent] = useState('');

  const getStatusColor = (status: CommentThread['status']) => {
    switch (status) {
      case 'open':
        return 'bg-blue-500';
      case 'resolved':
        return 'bg-green-500';
      case 'closed':
        return 'bg-gray-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getPriorityColor = (priority: CommentThread['priority']) => {
    switch (priority) {
      case 'urgent':
        return 'bg-red-500';
      case 'high':
        return 'bg-orange-500';
      case 'medium':
        return 'bg-yellow-500';
      case 'low':
        return 'bg-green-500';
      default:
        return 'bg-gray-500';
    }
  };

  const handleAddComment = useCallback(() => {
    if (!newComment.trim()) return;

    const comment: Comment = {
      id: `comment-${Date.now()}`,
      thread_id: thread.id,
      user_id: currentUserId,
      user_name: 'Current User', // Would come from user context
      content: newComment.trim(),
      parent_comment_id: replyingTo || undefined,
      mentions: extractMentions(newComment),
      reactions: [],
      edited: false,
      created_at: new Date(),
      updated_at: new Date(),
    };

    const updatedThread = {
      ...thread,
      comments: [...thread.comments, comment],
      updated_at: new Date(),
      participants: Array.from(new Set([...thread.participants, currentUserId])),
    };

    onUpdate(updatedThread);
    setNewComment('');
    setReplyingTo(null);
    toast.success('Comment added');
  }, [newComment, replyingTo, thread, currentUserId, onUpdate]);

  const handleEditComment = useCallback((commentId: string) => {
    const comment = thread.comments.find(c => c.id === commentId);
    if (comment) {
      setEditingComment(commentId);
      setEditContent(comment.content);
    }
  }, [thread.comments]);

  const handleSaveEdit = useCallback(() => {
    if (!editContent.trim() || !editingComment) return;

    const updatedComments = thread.comments.map(comment =>
      comment.id === editingComment
        ? { 
            ...comment, 
            content: editContent.trim(),
            edited: true,
            updated_at: new Date(),
            mentions: extractMentions(editContent)
          }
        : comment
    );

    onUpdate({
      ...thread,
      comments: updatedComments,
      updated_at: new Date(),
    });

    setEditingComment(null);
    setEditContent('');
    toast.success('Comment updated');
  }, [editContent, editingComment, thread, onUpdate]);

  const handleDeleteComment = useCallback((commentId: string) => {
    const updatedComments = thread.comments.filter(c => c.id !== commentId);
    onUpdate({
      ...thread,
      comments: updatedComments,
      updated_at: new Date(),
    });
    toast.success('Comment deleted');
  }, [thread, onUpdate]);

  const handleToggleStatus = useCallback(() => {
    const newStatus = thread.status === 'open' ? 'resolved' : 'open';
    onUpdate({
      ...thread,
      status: newStatus,
      updated_at: new Date(),
      resolved_at: newStatus === 'resolved' ? new Date() : undefined,
      resolved_by: newStatus === 'resolved' ? currentUserId : undefined,
    });
    toast.success(`Thread ${newStatus}`);
  }, [thread, currentUserId, onUpdate]);

  const handleAddReaction = useCallback((commentId: string, emoji: string) => {
    const updatedComments = thread.comments.map(comment => {
      if (comment.id === commentId) {
        // Check if user already reacted with this emoji
        const existingReaction = comment.reactions.find(
          r => r.user_id === currentUserId && r.emoji === emoji
        );

        if (existingReaction) {
          // Remove reaction
          return {
            ...comment,
            reactions: comment.reactions.filter(r => r.id !== existingReaction.id),
          };
        } else {
          // Add reaction
          const reaction: CommentReaction = {
            id: `reaction-${Date.now()}`,
            comment_id: commentId,
            user_id: currentUserId,
            emoji,
            created_at: new Date(),
          };
          return {
            ...comment,
            reactions: [...comment.reactions, reaction],
          };
        }
      }
      return comment;
    });

    onUpdate({
      ...thread,
      comments: updatedComments,
      updated_at: new Date(),
    });
  }, [thread, currentUserId, onUpdate]);

  // Group comments by parent/child relationship
  const organizedComments = useMemo(() => {
    const topLevel = thread.comments.filter(c => !c.parent_comment_id);
    const replies = thread.comments.filter(c => c.parent_comment_id);
    
    return topLevel.map(comment => ({
      ...comment,
      replies: replies.filter(r => r.parent_comment_id === comment.id),
    }));
  }, [thread.comments]);

  return (
    <Card className={cn("w-full", className)}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex-1 space-y-2">
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-sm">{thread.title}</h3>
              {thread.pinned && (
                <Pin className="h-3 w-3 text-yellow-500" />
              )}
            </div>
            
            {thread.description && (
              <p className="text-xs text-muted-foreground">{thread.description}</p>
            )}
            
            <div className="flex items-center gap-2 flex-wrap">
              <Badge 
                className={cn("text-white text-xs", getStatusColor(thread.status))}
              >
                {thread.status}
              </Badge>
              <Badge 
                className={cn("text-white text-xs", getPriorityColor(thread.priority))}
              >
                {thread.priority}
              </Badge>
              {thread.tags.map(tag => (
                <Badge key={tag} variant="outline" className="text-xs">
                  <Hash className="mr-1 h-2 w-2" />
                  {tag}
                </Badge>
              ))}
            </div>
            
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <span>{thread.comments.length} comments</span>
              <span>•</span>
              <span>{thread.participants.length} participants</span>
              <span>•</span>
              <span>Updated {formatDistanceToNow(thread.updated_at, { addSuffix: true })}</span>
            </div>
          </div>
          
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowComments(!showComments)}
            >
              <MessageCircle className="mr-1 h-3 w-3" />
              {showComments ? 'Hide' : 'Show'}
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleToggleStatus}
              className={thread.status === 'resolved' ? 'text-green-600' : ''}
            >
              <Check className="h-3 w-3" />
            </Button>
          </div>
        </div>
      </CardHeader>

      {showComments && (
        <CardContent className="pt-0">
          <Separator className="mb-3" />
          
          {/* Comments list */}
          <ScrollArea className="max-h-96 mb-3">
            <div className="space-y-3">
              {organizedComments.map((comment) => (
                <div key={comment.id} className="space-y-2">
                  {/* Main comment */}
                  <div className="flex gap-2">
                    <Avatar className="h-6 w-6 mt-1">
                      <AvatarImage src={comment.user_avatar} />
                      <AvatarFallback className="text-xs">
                        {comment.user_name.charAt(0).toUpperCase()}
                      </AvatarFallback>
                    </Avatar>
                    
                    <div className="flex-1 space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium">{comment.user_name}</span>
                        <span className="text-xs text-muted-foreground">
                          {formatDistanceToNow(comment.created_at, { addSuffix: true })}
                        </span>
                        {comment.edited && (
                          <Badge variant="outline" className="text-xs">edited</Badge>
                        )}
                      </div>
                      
                      {editingComment === comment.id ? (
                        <div className="space-y-2">
                          <Textarea
                            value={editContent}
                            onChange={(e) => setEditContent(e.target.value)}
                            rows={2}
                            className="text-sm"
                          />
                          <div className="flex gap-2">
                            <Button size="sm" onClick={handleSaveEdit}>
                              <Check className="mr-1 h-3 w-3" />
                              Save
                            </Button>
                            <Button 
                              size="sm" 
                              variant="outline" 
                              onClick={() => setEditingComment(null)}
                            >
                              Cancel
                            </Button>
                          </div>
                        </div>
                      ) : (
                        <p className="text-sm">{comment.content}</p>
                      )}
                      
                      {/* Reactions */}
                      {comment.reactions.length > 0 && (
                        <div className="flex gap-1">
                          {Object.entries(
                            comment.reactions.reduce((acc, reaction) => {
                              acc[reaction.emoji] = (acc[reaction.emoji] || 0) + 1;
                              return acc;
                            }, {} as Record<string, number>)
                          ).map(([emoji, count]) => (
                            <button
                              key={emoji}
                              onClick={() => handleAddReaction(comment.id, emoji)}
                              className="text-xs px-2 py-1 rounded-full bg-muted hover:bg-muted/80 transition-colors"
                            >
                              {emoji} {count}
                            </button>
                          ))}
                        </div>
                      )}
                      
                      {/* Comment actions */}
                      <div className="flex items-center gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setReplyingTo(comment.id)}
                          className="text-xs h-6"
                        >
                          <Reply className="mr-1 h-2 w-2" />
                          Reply
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleAddReaction(comment.id, '👍')}
                          className="text-xs h-6"
                        >
                          👍
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleAddReaction(comment.id, '❤️')}
                          className="text-xs h-6"
                        >
                          ❤️
                        </Button>
                        {comment.user_id === currentUserId && (
                          <>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleEditComment(comment.id)}
                              className="text-xs h-6"
                            >
                              <Edit3 className="h-2 w-2" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleDeleteComment(comment.id)}
                              className="text-xs h-6 text-destructive"
                            >
                              <Trash2 className="h-2 w-2" />
                            </Button>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                  
                  {/* Replies */}
                  {comment.replies.length > 0 && (
                    <div className="ml-8 space-y-2 border-l-2 border-muted pl-3">
                      {comment.replies.map((reply) => (
                        <div key={reply.id} className="flex gap-2">
                          <Avatar className="h-5 w-5 mt-1">
                            <AvatarImage src={reply.user_avatar} />
                            <AvatarFallback className="text-xs">
                              {reply.user_name.charAt(0).toUpperCase()}
                            </AvatarFallback>
                          </Avatar>
                          <div className="flex-1 space-y-1">
                            <div className="flex items-center gap-2">
                              <span className="text-xs font-medium">{reply.user_name}</span>
                              <span className="text-xs text-muted-foreground">
                                {formatDistanceToNow(reply.created_at, { addSuffix: true })}
                              </span>
                            </div>
                            <p className="text-xs">{reply.content}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                  
                  {/* Reply input */}
                  {replyingTo === comment.id && (
                    <div className="ml-8 space-y-2">
                      <Textarea
                        value={newComment}
                        onChange={(e) => setNewComment(e.target.value)}
                        placeholder="Write a reply..."
                        rows={2}
                        className="text-sm"
                      />
                      <div className="flex gap-2">
                        <Button size="sm" onClick={handleAddComment}>
                          <Send className="mr-1 h-3 w-3" />
                          Reply
                        </Button>
                        <Button 
                          size="sm" 
                          variant="outline" 
                          onClick={() => setReplyingTo(null)}
                        >
                          Cancel
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </ScrollArea>
          
          {/* New comment input */}
          {!replyingTo && (
            <div className="space-y-2">
              <Textarea
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
                placeholder="Add a comment..."
                rows={2}
                className="text-sm"
              />
              <Button 
                size="sm" 
                onClick={handleAddComment}
                disabled={!newComment.trim()}
              >
                <Send className="mr-1 h-3 w-3" />
                Comment
              </Button>
            </div>
          )}
        </CardContent>
      )}
    </Card>
  );
}

interface CreateThreadDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (thread: Omit<CommentThread, 'id' | 'created_at' | 'updated_at' | 'comments'>) => void;
  dashboardId: string;
  widgetId?: string;
  currentUserId: string;
}

function CreateThreadDialog({
  isOpen,
  onClose,
  onSave,
  dashboardId,
  widgetId,
  currentUserId,
}: CreateThreadDialogProps) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState<CommentThread['priority']>('medium');
  const [tags, setTags] = useState('');

  const handleSave = useCallback(() => {
    if (title.trim()) {
      const thread: Omit<CommentThread, 'id' | 'created_at' | 'updated_at' | 'comments'> = {
        dashboard_id: dashboardId,
        widget_id: widgetId,
        title: title.trim(),
        description: description.trim() || undefined,
        status: 'open',
        priority,
        tags: tags.split(',').map(t => t.trim()).filter(Boolean),
        participants: [currentUserId],
        created_by: currentUserId,
        pinned: false,
      };

      onSave(thread);
      
      // Reset form
      setTitle('');
      setDescription('');
      setPriority('medium');
      setTags('');
      onClose();
      
      toast.success('Discussion thread created');
    }
  }, [title, description, priority, tags, dashboardId, widgetId, currentUserId, onSave, onClose]);

  return (
    <Sheet open={isOpen} onOpenChange={onClose}>
      <SheetContent>
        <SheetHeader>
          <SheetTitle>Start Discussion</SheetTitle>
        </SheetHeader>

        <div className="space-y-4 mt-6">
          <div className="space-y-2">
            <label className="text-sm font-medium">Title</label>
            <Input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="What would you like to discuss?"
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Description (optional)</label>
            <Textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Provide more context..."
              rows={3}
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Priority</label>
            <div className="grid grid-cols-2 gap-2">
              {(['low', 'medium', 'high', 'urgent'] as const).map((p) => (
                <Button
                  key={p}
                  variant={priority === p ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setPriority(p)}
                >
                  {p.charAt(0).toUpperCase() + p.slice(1)}
                </Button>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Tags (optional)</label>
            <Input
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              placeholder="tag1, tag2, tag3"
            />
          </div>

          <div className="flex gap-2 pt-4">
            <Button onClick={handleSave} disabled={!title.trim()}>
              Create Thread
            </Button>
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}

interface CommentThreadsProps {
  dashboardId: string;
  widgetId?: string;
  currentUserId?: string;
  className?: string;
  onThreadsChange?: (threads: CommentThread[]) => void;
}

export function CommentThreads({
  dashboardId,
  widgetId,
  currentUserId = 'user-1',
  className,
  onThreadsChange,
}: CommentThreadsProps) {
  const [threads, setThreads] = useState<CommentThread[]>([]);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [filterStatus, setFilterStatus] = useState<CommentThread['status'] | 'all'>('all');
  const [searchQuery, setSearchQuery] = useState('');

  // Mock data - in a real app, this would come from API
  useEffect(() => {
    const mockThreads: CommentThread[] = [
      {
        id: 'thread-1',
        dashboard_id: dashboardId,
        widget_id: widgetId,
        title: 'Data Quality Issue in Patient Enrollment Chart',
        description: 'There seems to be a discrepancy in the enrollment numbers for Site 001.',
        status: 'open',
        priority: 'high',
        tags: ['data-quality', 'enrollment'],
        participants: ['user-1', 'user-2'],
        created_by: 'user-1',
        created_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000),
        updated_at: new Date(Date.now() - 1 * 60 * 60 * 1000),
        pinned: true,
        comments: [
          {
            id: 'comment-1',
            thread_id: 'thread-1',
            user_id: 'user-1',
            user_name: 'John Doe',
            content: 'I noticed that the enrollment count for Site 001 shows 45 patients, but our source data shows 48. Can someone verify this?',
            mentions: ['user-2'],
            reactions: [
              {
                id: 'reaction-1',
                comment_id: 'comment-1',
                user_id: 'user-2',
                emoji: '👍',
                created_at: new Date(Date.now() - 30 * 60 * 1000),
              },
            ],
            edited: false,
            created_at: new Date(Date.now() - 2 * 60 * 60 * 1000),
            updated_at: new Date(Date.now() - 2 * 60 * 60 * 1000),
          },
          {
            id: 'comment-2',
            thread_id: 'thread-1',
            user_id: 'user-2',
            user_name: 'Jane Smith',
            content: 'I checked the source data and confirmed there are indeed 48 patients. The discrepancy might be due to a recent data refresh.',
            mentions: [],
            reactions: [],
            edited: false,
            created_at: new Date(Date.now() - 1 * 60 * 60 * 1000),
            updated_at: new Date(Date.now() - 1 * 60 * 60 * 1000),
          },
        ],
      },
    ];

    setThreads(mockThreads);
  }, [dashboardId, widgetId]);

  const handleCreateThread = useCallback((
    threadData: Omit<CommentThread, 'id' | 'created_at' | 'updated_at' | 'comments'>
  ) => {
    const newThread: CommentThread = {
      ...threadData,
      id: `thread-${Date.now()}`,
      created_at: new Date(),
      updated_at: new Date(),
      comments: [],
    };

    setThreads(prev => [newThread, ...prev]);
    onThreadsChange?.([newThread, ...threads]);
  }, [threads, onThreadsChange]);

  const handleUpdateThread = useCallback((updatedThread: CommentThread) => {
    setThreads(prev =>
      prev.map(t => t.id === updatedThread.id ? updatedThread : t)
    );
    onThreadsChange?.(threads.map(t => 
      t.id === updatedThread.id ? updatedThread : t
    ));
  }, [threads, onThreadsChange]);

  const handleDeleteThread = useCallback((threadId: string) => {
    setThreads(prev => prev.filter(t => t.id !== threadId));
    onThreadsChange?.(threads.filter(t => t.id !== threadId));
    toast.success('Discussion thread deleted');
  }, [threads, onThreadsChange]);

  const filteredThreads = useMemo(() => {
    let filtered = threads;

    if (filterStatus !== 'all') {
      filtered = filtered.filter(t => t.status === filterStatus);
    }

    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(t =>
        t.title.toLowerCase().includes(query) ||
        t.description?.toLowerCase().includes(query) ||
        t.tags.some(tag => tag.toLowerCase().includes(query))
      );
    }

    return filtered.sort((a, b) => {
      // Sort by pinned first, then by updated date
      if (a.pinned && !b.pinned) return -1;
      if (!a.pinned && b.pinned) return 1;
      return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
    });
  }, [threads, filterStatus, searchQuery]);

  return (
    <div className={cn("space-y-4", className)}>
      {/* Header with controls */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <h2 className="text-lg font-semibold">Discussions</h2>
          <Badge variant="secondary">{filteredThreads.length}</Badge>
        </div>
        
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search discussions..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-8 w-48"
            />
          </div>
          
          <Button
            variant="outline"
            size="sm"
            onClick={() => setFilterStatus(filterStatus === 'all' ? 'open' : 'all')}
          >
            <Filter className="mr-1 h-3 w-3" />
            {filterStatus === 'all' ? 'All' : 'Open'}
          </Button>
          
          <Button size="sm" onClick={() => setShowCreateDialog(true)}>
            <Plus className="mr-1 h-4 w-4" />
            New Discussion
          </Button>
        </div>
      </div>

      {/* Threads list */}
      <div className="space-y-4">
        {filteredThreads.map((thread) => (
          <CommentThreadCard
            key={thread.id}
            thread={thread}
            currentUserId={currentUserId}
            onUpdate={handleUpdateThread}
            onDelete={handleDeleteThread}
          />
        ))}
        
        {filteredThreads.length === 0 && (
          <Card className="p-8 text-center">
            <MessageCircle className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <h3 className="text-lg font-medium mb-2">No discussions yet</h3>
            <p className="text-muted-foreground mb-4">
              Start a discussion to collaborate with your team on this dashboard.
            </p>
            <Button onClick={() => setShowCreateDialog(true)}>
              <Plus className="mr-2 h-4 w-4" />
              Start Discussion
            </Button>
          </Card>
        )}
      </div>

      {/* Create thread dialog */}
      <CreateThreadDialog
        isOpen={showCreateDialog}
        onClose={() => setShowCreateDialog(false)}
        onSave={handleCreateThread}
        dashboardId={dashboardId}
        widgetId={widgetId}
        currentUserId={currentUserId}
      />
    </div>
  );
}

// Utility function to extract mentions from text
function extractMentions(text: string): string[] {
  const mentionRegex = /@(\w+)/g;
  const mentions = [];
  let match;
  
  while ((match = mentionRegex.exec(text)) !== null) {
    mentions.push(match[1]);
  }
  
  return mentions;
}