// ABOUTME: Email history page for viewing audit trail of all sent emails
// ABOUTME: Provides complete audit history for compliance and tracking

'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { useToast } from '@/components/ui/use-toast';
import { 
  Loader2, History, ChevronLeft, Mail, FileText, Clock,
  CheckCircle2, XCircle, AlertCircle, Search, Filter,
  Calendar, Download, Settings, Eye
} from 'lucide-react';
import { AuthGuard } from '@/components/auth-guard';
import { EmailNav } from '@/components/email/email-nav';
import { emailApi, type EmailHistory as EmailHistoryItem } from '@/lib/api/email';
import { formatDistanceToNow, format } from 'date-fns';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

export default function EmailHistoryPage() {
  const router = useRouter();
  const [history, setHistory] = useState<EmailHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [selectedItem, setSelectedItem] = useState<EmailHistoryItem | null>(null);
  const [viewDetails, setViewDetails] = useState(false);
  const [totalCount, setTotalCount] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(20);
  const { toast } = useToast();

  useEffect(() => {
    loadHistory();
  }, [statusFilter, currentPage]);

  const loadHistory = async () => {
    try {
      setLoading(true);
      
      const response = await emailApi.history.getHistory({
        status: statusFilter === 'all' ? undefined : statusFilter,
        limit: itemsPerPage,
        offset: (currentPage - 1) * itemsPerPage
      });
      
      setHistory(response.items);
      setTotalCount(response.total);
    } catch (error) {
      console.error('Failed to load email history:', error);
      toast({
        title: 'Error',
        description: 'Failed to load email history',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    setCurrentPage(1);
    loadHistory();
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'sent':
        return <Badge variant="outline" className="border-green-500 text-green-600"><CheckCircle2 className="h-3 w-3 mr-1" /> Sent</Badge>;
      case 'failed':
        return <Badge variant="outline" className="border-red-500 text-red-600"><XCircle className="h-3 w-3 mr-1" /> Failed</Badge>;
      case 'bounced':
        return <Badge variant="outline" className="border-yellow-500 text-yellow-600"><AlertCircle className="h-3 w-3 mr-1" /> Bounced</Badge>;
      case 'complained':
        return <Badge variant="outline" className="border-orange-500 text-orange-600"><AlertCircle className="h-3 w-3 mr-1" /> Complained</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const filteredHistory = (history || []).filter(item => {
    if (searchTerm) {
      const search = searchTerm.toLowerCase();
      return item.recipient_email.toLowerCase().includes(search) ||
             item.subject.toLowerCase().includes(search) ||
             (item.sender_email && item.sender_email.toLowerCase().includes(search));
    }
    return true;
  });

  // Stats calculation
  const stats = {
    total: totalCount,
    sent: (history || []).filter(i => i.status === 'sent').length,
    failed: (history || []).filter(i => i.status === 'failed').length,
    bounced: (history || []).filter(i => i.status === 'bounced').length,
  };

  const totalPages = Math.ceil(totalCount / itemsPerPage);

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
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
              <Mail className="h-8 w-8" />
              Email Management
            </h1>
            <p className="text-muted-foreground">
              Configure email settings, templates, and monitor delivery
            </p>
          </div>
          
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              toast({
                title: 'Export Started',
                description: 'Email history export will be downloaded shortly',
              });
            }}
          >
            <Download className="mr-2 h-4 w-4" />
            Export History
          </Button>
        </div>

        {/* Tab Navigation */}
        <EmailNav />

        {/* Stats Cards */}
        <div className="grid grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Total Emails</CardDescription>
              <CardTitle className="text-2xl">{stats.total}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Successfully Sent</CardDescription>
              <CardTitle className="text-2xl text-green-600">{stats.sent}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Failed</CardDescription>
              <CardTitle className="text-2xl text-red-600">{stats.failed}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Bounced</CardDescription>
              <CardTitle className="text-2xl text-yellow-600">{stats.bounced}</CardTitle>
            </CardHeader>
          </Card>
        </div>

        {/* Filters and Search */}
        <Card>
          <CardHeader>
            <div className="flex justify-between items-center">
              <CardTitle>Email History</CardTitle>
              <div className="flex gap-2">
                <div className="relative">
                  <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search emails..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                    className="pl-8 w-64"
                  />
                </div>
                <Select value={statusFilter} onValueChange={(v) => { setStatusFilter(v); setCurrentPage(1); }}>
                  <SelectTrigger className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Status</SelectItem>
                    <SelectItem value="sent">Sent</SelectItem>
                    <SelectItem value="failed">Failed</SelectItem>
                    <SelectItem value="bounced">Bounced</SelectItem>
                    <SelectItem value="complained">Complained</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {filteredHistory.length === 0 ? (
              <div className="p-8 text-center text-muted-foreground">
                No email history found
              </div>
            ) : (
              <>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Status</TableHead>
                      <TableHead>Recipient</TableHead>
                      <TableHead>Subject</TableHead>
                      <TableHead>Template</TableHead>
                      <TableHead>Sent At</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredHistory.map((item) => (
                      <TableRow key={item.id}>
                        <TableCell>{getStatusBadge(item.status)}</TableCell>
                        <TableCell className="font-medium">{item.recipient_email}</TableCell>
                        <TableCell className="max-w-xs truncate">{item.subject}</TableCell>
                        <TableCell>
                          {item.template_key && (
                            <Badge variant="outline">{item.template_key}</Badge>
                          )}
                        </TableCell>
                        <TableCell>
                          <span className="text-sm text-muted-foreground">
                            {formatDistanceToNow(new Date(item.created_at), { addSuffix: true })}
                          </span>
                        </TableCell>
                        <TableCell>
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
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>

                {/* Pagination */}
                <div className="flex justify-between items-center mt-4">
                  <div className="text-sm text-muted-foreground">
                    Showing {((currentPage - 1) * itemsPerPage) + 1} to {Math.min(currentPage * itemsPerPage, totalCount)} of {totalCount} emails
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                      disabled={currentPage === 1}
                    >
                      Previous
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                      disabled={currentPage === totalPages}
                    >
                      Next
                    </Button>
                  </div>
                </div>
              </>
            )}
          </CardContent>
        </Card>

        {/* Details Dialog */}
        <Dialog open={viewDetails} onOpenChange={setViewDetails}>
          <DialogContent className="max-w-2xl max-h-[80vh] overflow-auto">
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
                    <Label>Sender</Label>
                    <p className="text-sm">{selectedItem.sender_email}</p>
                  </div>
                  <div className="space-y-2">
                    <Label>Sent At</Label>
                    <p className="text-sm">{format(new Date(selectedItem.created_at), 'PPpp')}</p>
                  </div>
                </div>
                
                <div className="space-y-2">
                  <Label>Subject</Label>
                  <p className="text-sm font-medium">{selectedItem.subject}</p>
                </div>

                {selectedItem.message_id && (
                  <div className="space-y-2">
                    <Label>Message ID</Label>
                    <p className="text-xs font-mono bg-muted p-2 rounded">{selectedItem.message_id}</p>
                  </div>
                )}

                {selectedItem.error_message && (
                  <div className="space-y-2">
                    <Label>Error Message</Label>
                    <div className="p-3 border border-red-500 rounded-md bg-red-50 dark:bg-red-950/20">
                      <p className="text-sm text-red-600 dark:text-red-400">{selectedItem.error_message}</p>
                    </div>
                  </div>
                )}

                {selectedItem.template_key && (
                  <div className="space-y-2">
                    <Label>Template Used</Label>
                    <Badge>{selectedItem.template_key}</Badge>
                  </div>
                )}

                {selectedItem.variables && Object.keys(selectedItem.variables).length > 0 && (
                  <div className="space-y-2">
                    <Label>Template Variables</Label>
                    <div className="p-3 bg-muted rounded-md">
                      <pre className="text-xs overflow-auto">
                        {JSON.stringify(selectedItem.variables, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}
              </div>
            )}
          </DialogContent>
        </Dialog>
      </div>
    </AuthGuard>
  );
}