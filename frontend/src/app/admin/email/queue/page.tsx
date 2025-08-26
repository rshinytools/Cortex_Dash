// ABOUTME: Email queue monitoring page for viewing and managing queued emails
// ABOUTME: Provides real-time monitoring of email delivery status and manual controls

'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { useToast } from '@/components/ui/use-toast';
import { 
  Loader2, Mail, Clock, CheckCircle2, XCircle, X, AlertCircle, 
  RefreshCw, Play, Pause, Trash2, Eye, Search, Filter,
  Send, MoreVertical, ArrowUpRight, Timer, ChevronLeft,
  FileText, Settings, History
} from 'lucide-react';
import { AuthGuard } from '@/components/auth-guard';
import { EmailNav } from '@/components/email/email-nav';
import { emailApi, type EmailQueueItem, type EmailHistory } from '@/lib/api/email';
import { formatDistanceToNow, format } from 'date-fns';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

export default function EmailQueuePage() {
  const router = useRouter();
  const [queueItems, setQueueItems] = useState<EmailQueueItem[]>([]);
  const [history, setHistory] = useState<EmailHistory[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [selectedItem, setSelectedItem] = useState<EmailQueueItem | null>(null);
  const [viewDetails, setViewDetails] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const { toast } = useToast();

  // Auto-refresh
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(5000);

  useEffect(() => {
    loadData();
  }, [statusFilter]);

  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(() => {
        loadData(true);
      }, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval]);

  const loadData = async (silent = false) => {
    try {
      if (!silent) setLoading(true);
      
      // Load queue items
      const queueData = await emailApi.queue.getQueue(
        statusFilter === 'all' ? undefined : statusFilter,
        100
      );
      setQueueItems(queueData);

      // Load recent history
      const historyData = await emailApi.history.getHistory({
        limit: 10
      });
      setHistory(historyData.items);
    } catch (error) {
      console.error('Failed to load email data:', error);
      if (!silent) {
        toast({
          title: 'Error',
          description: 'Failed to load email queue',
          variant: 'destructive',
        });
      }
    } finally {
      if (!silent) setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
    toast({
      title: 'Refreshed',
      description: 'Email queue data updated',
    });
  };

  const handleProcessQueue = async () => {
    try {
      setProcessing(true);
      const result = await emailApi.queue.processQueue();
      toast({
        title: 'Queue Processed',
        description: `Processed: ${result.processed}, Sent: ${result.sent}, Failed: ${result.failed}`,
      });
      await loadData();
    } catch (error) {
      console.error('Failed to process queue:', error);
      toast({
        title: 'Error',
        description: 'Failed to process email queue',
        variant: 'destructive',
      });
    } finally {
      setProcessing(false);
    }
  };

  const handleCancelEmail = async (id: string) => {
    try {
      await emailApi.queue.cancelEmail(id);
      toast({
        title: 'Email Cancelled',
        description: 'The email has been cancelled',
      });
      await loadData();
    } catch (error) {
      console.error('Failed to cancel email:', error);
      toast({
        title: 'Error',
        description: 'Failed to cancel email',
        variant: 'destructive',
      });
    }
  };

  const handleRetryEmail = async (id: string) => {
    try {
      await emailApi.queue.retryEmail(id);
      toast({
        title: 'Retry Scheduled',
        description: 'The email will be retried',
      });
      await loadData();
    } catch (error) {
      console.error('Failed to retry email:', error);
      toast({
        title: 'Error',
        description: 'Failed to retry email',
        variant: 'destructive',
      });
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'pending':
        return <Badge variant="outline" className="border-yellow-500 text-yellow-600"><Clock className="h-3 w-3 mr-1" /> Pending</Badge>;
      case 'processing':
        return <Badge variant="outline" className="border-blue-500 text-blue-600"><Loader2 className="h-3 w-3 mr-1 animate-spin" /> Processing</Badge>;
      case 'sent':
        return <Badge variant="outline" className="border-green-500 text-green-600"><CheckCircle2 className="h-3 w-3 mr-1" /> Sent</Badge>;
      case 'failed':
        return <Badge variant="outline" className="border-red-500 text-red-600"><XCircle className="h-3 w-3 mr-1" /> Failed</Badge>;
      case 'cancelled':
        return <Badge variant="outline" className="border-gray-500 text-gray-600"><X className="h-3 w-3 mr-1" /> Cancelled</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const filteredItems = (queueItems || []).filter(item => {
    if (searchTerm) {
      const search = searchTerm.toLowerCase();
      return item.recipient_email.toLowerCase().includes(search) ||
             item.subject.toLowerCase().includes(search);
    }
    return true;
  });

  // Stats calculation
  const stats = {
    total: (queueItems || []).length,
    pending: (queueItems || []).filter(i => i.status === 'pending').length,
    processing: (queueItems || []).filter(i => i.status === 'processing').length,
    sent: (queueItems || []).filter(i => i.status === 'sent').length,
    failed: (queueItems || []).filter(i => i.status === 'failed').length,
  };

  if (loading) {
    return (
      <AuthGuard>
        <div className="flex items-center justify-center h-96">
          <Loader2 className="h-8 w-8 animate-spin" />
        </div>
      </AuthGuard>
    );
  }

  return (
    <AuthGuard>
      <div className="container mx-auto py-6 space-y-6">
        {/* Navigation */}
        <div>
          <Button
            variant="ghost"
            onClick={() => router.push('/admin')}
            className="mb-4"
          >
            <ChevronLeft className="mr-2 h-4 w-4" />
            Back to Admin Dashboard
          </Button>
        </div>

        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <Mail className="h-8 w-8" />
            Email Management
          </h1>
          <p className="text-muted-foreground">
            Configure email settings, templates, and monitor delivery
          </p>
        </div>

        {/* Tab Navigation */}
        <EmailNav />

        {/* Auto-refresh Controls */}
        <div className="flex justify-end items-center gap-2">
          <Select value={refreshInterval.toString()} onValueChange={(v) => setRefreshInterval(parseInt(v))}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="5000">5 seconds</SelectItem>
              <SelectItem value="10000">10 seconds</SelectItem>
              <SelectItem value="30000">30 seconds</SelectItem>
              <SelectItem value="60000">1 minute</SelectItem>
            </SelectContent>
          </Select>
          <Button
            variant={autoRefresh ? "default" : "outline"}
            size="sm"
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            {autoRefresh ? (
              <>
                <Timer className="h-4 w-4 mr-2" />
                Auto-refresh ON
              </>
            ) : (
              <>
                <Timer className="h-4 w-4 mr-2" />
                Auto-refresh OFF
              </>
            )}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={refreshing}
          >
            {refreshing ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4" />
            )}
          </Button>
          <Button
            onClick={handleProcessQueue}
            disabled={processing}
          >
            {processing ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Processing...
              </>
            ) : (
              <>
                <Play className="mr-2 h-4 w-4" />
                Process Queue
              </>
            )}
          </Button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-5 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Total</CardDescription>
              <CardTitle className="text-2xl">{stats.total}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Pending</CardDescription>
              <CardTitle className="text-2xl text-yellow-600">{stats.pending}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Processing</CardDescription>
              <CardTitle className="text-2xl text-blue-600">{stats.processing}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Sent</CardDescription>
              <CardTitle className="text-2xl text-green-600">{stats.sent}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Failed</CardDescription>
              <CardTitle className="text-2xl text-red-600">{stats.failed}</CardTitle>
            </CardHeader>
          </Card>
        </div>

        <Tabs defaultValue="queue" className="space-y-4">
          <TabsList>
            <TabsTrigger value="queue">
              <Clock className="h-4 w-4 mr-2" />
              Queue ({stats.total})
            </TabsTrigger>
            <TabsTrigger value="history">
              <CheckCircle2 className="h-4 w-4 mr-2" />
              Recent History
            </TabsTrigger>
          </TabsList>

          <TabsContent value="queue" className="space-y-4">
            {/* Filters */}
            <Card>
              <CardHeader>
                <div className="flex justify-between items-center">
                  <CardTitle>Email Queue</CardTitle>
                  <div className="flex gap-2">
                    <div className="relative">
                      <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                      <Input
                        placeholder="Search emails..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="pl-8 w-64"
                      />
                    </div>
                    <Select value={statusFilter} onValueChange={setStatusFilter}>
                      <SelectTrigger className="w-32">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All Status</SelectItem>
                        <SelectItem value="pending">Pending</SelectItem>
                        <SelectItem value="processing">Processing</SelectItem>
                        <SelectItem value="sent">Sent</SelectItem>
                        <SelectItem value="failed">Failed</SelectItem>
                        <SelectItem value="cancelled">Cancelled</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="p-0">
                {filteredItems.length === 0 ? (
                  <div className="p-8 text-center text-muted-foreground">
                    {searchTerm || statusFilter !== 'all' 
                      ? 'No emails match your filters'
                      : 'No emails in queue'}
                  </div>
                ) : (
                  <div className="divide-y">
                    {filteredItems.map((item) => (
                      <div key={item.id} className="p-4 hover:bg-muted/50 transition-colors">
                        <div className="flex justify-between items-start">
                          <div className="space-y-2 flex-1">
                            <div className="flex items-center gap-2">
                              {getStatusBadge(item.status)}
                              <span className="font-medium">{item.recipient_email}</span>
                              {item.priority > 1 && (
                                <Badge variant="outline">
                                  <ArrowUpRight className="h-3 w-3 mr-1" />
                                  Priority {item.priority}
                                </Badge>
                              )}
                            </div>
                            <p className="text-sm font-medium">{item.subject}</p>
                            <div className="flex items-center gap-4 text-xs text-muted-foreground">
                              <span>Created: {formatDistanceToNow(new Date(item.created_at), { addSuffix: true })}</span>
                              {item.attempts > 0 && (
                                <span>Attempts: {item.attempts}/{item.max_attempts}</span>
                              )}
                              {item.scheduled_at && (
                                <span>Scheduled: {format(new Date(item.scheduled_at), 'PPp')}</span>
                              )}
                              {item.next_retry_at && (
                                <span className="text-yellow-600">Next retry: {formatDistanceToNow(new Date(item.next_retry_at), { addSuffix: true })}</span>
                              )}
                            </div>
                            {item.error_message && (
                              <Alert className="mt-2">
                                <AlertCircle className="h-4 w-4" />
                                <AlertDescription className="text-xs">
                                  {item.error_message}
                                </AlertDescription>
                              </Alert>
                            )}
                          </div>
                          <div className="flex gap-2">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => {
                                setSelectedItem(item);
                                setViewDetails(true);
                              }}
                            >
                              <Eye className="h-4 w-4" />
                            </Button>
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="sm">
                                  <MoreVertical className="h-4 w-4" />
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end">
                                <DropdownMenuLabel>Actions</DropdownMenuLabel>
                                <DropdownMenuSeparator />
                                {item.status === 'failed' && (
                                  <DropdownMenuItem onClick={() => handleRetryEmail(item.id)}>
                                    <RefreshCw className="h-4 w-4 mr-2" />
                                    Retry Now
                                  </DropdownMenuItem>
                                )}
                                {(item.status === 'pending' || item.status === 'processing') && (
                                  <DropdownMenuItem 
                                    onClick={() => handleCancelEmail(item.id)}
                                    className="text-red-600"
                                  >
                                    <XCircle className="h-4 w-4 mr-2" />
                                    Cancel
                                  </DropdownMenuItem>
                                )}
                                <DropdownMenuItem onClick={() => {
                                  setSelectedItem(item);
                                  setViewDetails(true);
                                }}>
                                  <Eye className="h-4 w-4 mr-2" />
                                  View Details
                                </DropdownMenuItem>
                              </DropdownMenuContent>
                            </DropdownMenu>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="history" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Recent Email History</CardTitle>
                <CardDescription>
                  Last 10 processed emails
                </CardDescription>
              </CardHeader>
              <CardContent className="p-0">
                {!history || history.length === 0 ? (
                  <div className="p-8 text-center text-muted-foreground">
                    No email history available
                  </div>
                ) : (
                  <div className="divide-y">
                    {history.map((item) => (
                      <div key={item.id} className="p-4">
                        <div className="flex justify-between items-start">
                          <div className="space-y-2">
                            <div className="flex items-center gap-2">
                              {getStatusBadge(item.status)}
                              <span className="font-medium">{item.recipient_email}</span>
                              {item.template_key && (
                                <Badge variant="outline">{item.template_key}</Badge>
                              )}
                            </div>
                            <p className="text-sm">{item.subject}</p>
                            <div className="flex items-center gap-4 text-xs text-muted-foreground">
                              <span>Sent: {formatDistanceToNow(new Date(item.created_at), { addSuffix: true })}</span>
                              <span>From: {item.sender_email}</span>
                              {item.message_id && (
                                <span>ID: {item.message_id.substring(0, 8)}...</span>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Email Details Dialog */}
        <Dialog open={viewDetails} onOpenChange={setViewDetails}>
          <DialogContent className="max-w-3xl max-h-[80vh] overflow-auto">
            <DialogHeader>
              <DialogTitle>Email Details</DialogTitle>
            </DialogHeader>
            {selectedItem && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Recipient</Label>
                    <p className="text-sm">{selectedItem.recipient_email}</p>
                  </div>
                  <div className="space-y-2">
                    <Label>Status</Label>
                    {getStatusBadge(selectedItem.status)}
                  </div>
                  <div className="space-y-2">
                    <Label>Subject</Label>
                    <p className="text-sm">{selectedItem.subject}</p>
                  </div>
                  <div className="space-y-2">
                    <Label>Priority</Label>
                    <p className="text-sm">{selectedItem.priority}</p>
                  </div>
                  <div className="space-y-2">
                    <Label>Attempts</Label>
                    <p className="text-sm">{selectedItem.attempts} / {selectedItem.max_attempts}</p>
                  </div>
                  <div className="space-y-2">
                    <Label>Created</Label>
                    <p className="text-sm">{format(new Date(selectedItem.created_at), 'PPpp')}</p>
                  </div>
                </div>
                
                {selectedItem.error_message && (
                  <div className="space-y-2">
                    <Label>Error Message</Label>
                    <Alert className="border-red-500">
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription>{selectedItem.error_message}</AlertDescription>
                    </Alert>
                  </div>
                )}

                <Tabs defaultValue="html" className="w-full">
                  <TabsList>
                    <TabsTrigger value="html">HTML Content</TabsTrigger>
                    {selectedItem.plain_content && (
                      <TabsTrigger value="plain">Plain Text</TabsTrigger>
                    )}
                  </TabsList>
                  <TabsContent value="html">
                    <div className="border rounded-md p-4 bg-white max-h-96 overflow-auto">
                      <div dangerouslySetInnerHTML={{ __html: selectedItem.html_content }} />
                    </div>
                  </TabsContent>
                  {selectedItem.plain_content && (
                    <TabsContent value="plain">
                      <div className="border rounded-md p-4 bg-muted/50 max-h-96 overflow-auto">
                        <pre className="whitespace-pre-wrap text-sm">
                          {selectedItem.plain_content}
                        </pre>
                      </div>
                    </TabsContent>
                  )}
                </Tabs>
              </div>
            )}
            <DialogFooter>
              <Button variant="outline" onClick={() => setViewDetails(false)}>
                Close
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </AuthGuard>
  );
}