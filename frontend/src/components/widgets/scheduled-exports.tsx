// ABOUTME: Component for managing scheduled dashboard exports with recurring schedules
// ABOUTME: Allows creating, editing, and monitoring scheduled exports with email delivery

'use client';

import { useState, useEffect } from 'react';
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
import { Switch } from '@/components/ui/switch';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Calendar, Clock, Mail, FileText, Play, Pause, Trash2, Edit, Plus } from 'lucide-react';
import { toast } from 'sonner';
import { useSession } from 'next-auth/react';
import { format } from 'date-fns';

interface ScheduledExportsProps {
  dashboardId: string;
  dashboardName: string;
  isOpen: boolean;
  onClose: () => void;
}

interface ScheduledExport {
  id: string;
  name: string;
  format: 'pdf' | 'pptx' | 'xlsx';
  schedule: string;
  is_active: boolean;
  email_recipients: string[];
  email_subject?: string;
  email_body?: string;
  next_run_at?: string;
  last_run_at?: string;
  last_run_status?: string;
  created_at: string;
  creator_name: string;
}

const schedulePresets = [
  { value: '0 9 * * 1', label: 'Weekly (Monday 9am)' },
  { value: '0 9 * * 1-5', label: 'Weekdays (9am)' },
  { value: '0 9 1 * *', label: 'Monthly (1st day, 9am)' },
  { value: '0 9 * * *', label: 'Daily (9am)' },
  { value: '0 */6 * * *', label: 'Every 6 hours' },
  { value: 'custom', label: 'Custom (cron expression)' },
];

export function ScheduledExports({ dashboardId, dashboardName, isOpen, onClose }: ScheduledExportsProps) {
  const [scheduledExports, setScheduledExports] = useState<ScheduledExport[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [editingExport, setEditingExport] = useState<ScheduledExport | null>(null);
  const { data: session } = useSession();

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    format: 'pdf' as 'pdf' | 'pptx' | 'xlsx',
    schedule: '0 9 * * 1',
    schedulePreset: '0 9 * * 1',
    is_active: true,
    email_recipients: '',
    email_subject: `${dashboardName} - Scheduled Export`,
    email_body: `Please find attached the scheduled export of the ${dashboardName} dashboard.`,
  });

  useEffect(() => {
    if (isOpen) {
      fetchScheduledExports();
    }
  }, [isOpen]);

  const fetchScheduledExports = async () => {
    if (!session?.user?.accessToken) return;

    setIsLoading(true);
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/dashboards/${dashboardId}/scheduled-exports`,
        {
          headers: {
            Authorization: `Bearer ${session.user.accessToken}`,
          },
        }
      );

      if (!response.ok) throw new Error('Failed to fetch scheduled exports');

      const data = await response.json();
      setScheduledExports(data);
    } catch (error) {
      console.error('Error fetching scheduled exports:', error);
      toast.error('Failed to load scheduled exports');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreate = async () => {
    if (!session?.user?.accessToken) return;

    try {
      const recipients = formData.email_recipients
        .split(',')
        .map(email => email.trim())
        .filter(email => email);

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/dashboards/${dashboardId}/scheduled-exports`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${session.user.accessToken}`,
          },
          body: JSON.stringify({
            ...formData,
            dashboard_id: dashboardId,
            email_recipients: recipients,
          }),
        }
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create scheduled export');
      }

      toast.success('Scheduled export created successfully');
      setShowCreateDialog(false);
      resetForm();
      fetchScheduledExports();
    } catch (error) {
      console.error('Error creating scheduled export:', error);
      toast.error(error instanceof Error ? error.message : 'Failed to create scheduled export');
    }
  };

  const handleUpdate = async () => {
    if (!session?.user?.accessToken || !editingExport) return;

    try {
      const recipients = formData.email_recipients
        .split(',')
        .map(email => email.trim())
        .filter(email => email);

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/scheduled-exports/${editingExport.id}`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${session.user.accessToken}`,
          },
          body: JSON.stringify({
            ...formData,
            email_recipients: recipients,
          }),
        }
      );

      if (!response.ok) throw new Error('Failed to update scheduled export');

      toast.success('Scheduled export updated successfully');
      setEditingExport(null);
      resetForm();
      fetchScheduledExports();
    } catch (error) {
      console.error('Error updating scheduled export:', error);
      toast.error('Failed to update scheduled export');
    }
  };

  const handleDelete = async (id: string) => {
    if (!session?.user?.accessToken) return;

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/scheduled-exports/${id}`,
        {
          method: 'DELETE',
          headers: {
            Authorization: `Bearer ${session.user.accessToken}`,
          },
        }
      );

      if (!response.ok) throw new Error('Failed to delete scheduled export');

      toast.success('Scheduled export deleted successfully');
      fetchScheduledExports();
    } catch (error) {
      console.error('Error deleting scheduled export:', error);
      toast.error('Failed to delete scheduled export');
    }
  };

  const handleToggleActive = async (exportItem: ScheduledExport) => {
    if (!session?.user?.accessToken) return;

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/scheduled-exports/${exportItem.id}`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${session.user.accessToken}`,
          },
          body: JSON.stringify({
            is_active: !exportItem.is_active,
          }),
        }
      );

      if (!response.ok) throw new Error('Failed to update scheduled export');

      toast.success(
        exportItem.is_active ? 'Export schedule paused' : 'Export schedule activated'
      );
      fetchScheduledExports();
    } catch (error) {
      console.error('Error toggling scheduled export:', error);
      toast.error('Failed to update scheduled export');
    }
  };

  const handleRunNow = async (id: string) => {
    if (!session?.user?.accessToken) return;

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/scheduled-exports/${id}/run`,
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${session.user.accessToken}`,
          },
        }
      );

      if (!response.ok) throw new Error('Failed to trigger export');

      toast.success('Export triggered successfully');
    } catch (error) {
      console.error('Error triggering export:', error);
      toast.error('Failed to trigger export');
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      format: 'pdf',
      schedule: '0 9 * * 1',
      schedulePreset: '0 9 * * 1',
      is_active: true,
      email_recipients: '',
      email_subject: `${dashboardName} - Scheduled Export`,
      email_body: `Please find attached the scheduled export of the ${dashboardName} dashboard.`,
    });
  };

  const startEdit = (exportItem: ScheduledExport) => {
    setEditingExport(exportItem);
    setFormData({
      name: exportItem.name,
      format: exportItem.format,
      schedule: exportItem.schedule,
      schedulePreset: schedulePresets.find(p => p.value === exportItem.schedule)?.value || 'custom',
      is_active: exportItem.is_active,
      email_recipients: exportItem.email_recipients.join(', '),
      email_subject: exportItem.email_subject || '',
      email_body: exportItem.email_body || '',
    });
  };

  const getStatusBadge = (status?: string) => {
    if (!status) return null;

    const variants: Record<string, 'default' | 'success' | 'destructive'> = {
      success: 'success',
      failed: 'destructive',
      skipped: 'default',
    };

    return <Badge variant={variants[status] || 'default'}>{status}</Badge>;
  };

  return (
    <>
      <Dialog open={isOpen} onOpenChange={onClose}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Scheduled Exports</DialogTitle>
            <DialogDescription>
              Manage recurring exports for "{dashboardName}"
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="flex justify-end">
              <Button onClick={() => setShowCreateDialog(true)}>
                <Plus className="mr-2 h-4 w-4" />
                Create Schedule
              </Button>
            </div>

            {isLoading ? (
              <div className="text-center py-8 text-muted-foreground">
                Loading scheduled exports...
              </div>
            ) : scheduledExports.length === 0 ? (
              <Card>
                <CardContent className="text-center py-8">
                  <p className="text-muted-foreground">
                    No scheduled exports configured yet.
                  </p>
                  <Button
                    variant="outline"
                    className="mt-4"
                    onClick={() => setShowCreateDialog(true)}
                  >
                    Create your first schedule
                  </Button>
                </CardContent>
              </Card>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Format</TableHead>
                    <TableHead>Schedule</TableHead>
                    <TableHead>Recipients</TableHead>
                    <TableHead>Next Run</TableHead>
                    <TableHead>Last Run</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {scheduledExports.map((exportItem) => (
                    <TableRow key={exportItem.id}>
                      <TableCell className="font-medium">{exportItem.name}</TableCell>
                      <TableCell>
                        <Badge variant="outline">{exportItem.format.toUpperCase()}</Badge>
                      </TableCell>
                      <TableCell>
                        {schedulePresets.find(p => p.value === exportItem.schedule)?.label || exportItem.schedule}
                      </TableCell>
                      <TableCell>{exportItem.email_recipients.length} recipients</TableCell>
                      <TableCell>
                        {exportItem.next_run_at && format(new Date(exportItem.next_run_at), 'MMM d, HH:mm')}
                      </TableCell>
                      <TableCell>
                        {exportItem.last_run_at && format(new Date(exportItem.last_run_at), 'MMM d, HH:mm')}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Switch
                            checked={exportItem.is_active}
                            onCheckedChange={() => handleToggleActive(exportItem)}
                          />
                          {getStatusBadge(exportItem.last_run_status)}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1">
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleRunNow(exportItem.id)}
                            title="Run now"
                          >
                            <Play className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => startEdit(exportItem)}
                            title="Edit"
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleDelete(exportItem.id)}
                            title="Delete"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Create/Edit Dialog */}
      <Dialog open={showCreateDialog || !!editingExport} onOpenChange={(open) => {
        if (!open) {
          setShowCreateDialog(false);
          setEditingExport(null);
          resetForm();
        }
      }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {editingExport ? 'Edit Scheduled Export' : 'Create Scheduled Export'}
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="name">Name</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="e.g., Weekly Management Report"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="format">Export Format</Label>
              <Select
                value={formData.format}
                onValueChange={(value: 'pdf' | 'pptx' | 'xlsx') =>
                  setFormData({ ...formData, format: value })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="pdf">PDF Document</SelectItem>
                  <SelectItem value="pptx">PowerPoint Presentation</SelectItem>
                  <SelectItem value="xlsx">Excel Workbook</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="schedule">Schedule</Label>
              <Select
                value={formData.schedulePreset}
                onValueChange={(value) => {
                  setFormData({
                    ...formData,
                    schedulePreset: value,
                    schedule: value === 'custom' ? formData.schedule : value,
                  });
                }}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {schedulePresets.map((preset) => (
                    <SelectItem key={preset.value} value={preset.value}>
                      {preset.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {formData.schedulePreset === 'custom' && (
                <Input
                  value={formData.schedule}
                  onChange={(e) => setFormData({ ...formData, schedule: e.target.value })}
                  placeholder="Cron expression (e.g., 0 9 * * 1)"
                  className="mt-2"
                />
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="recipients">Email Recipients</Label>
              <Input
                id="recipients"
                value={formData.email_recipients}
                onChange={(e) => setFormData({ ...formData, email_recipients: e.target.value })}
                placeholder="email1@example.com, email2@example.com"
              />
              <p className="text-xs text-muted-foreground">
                Separate multiple emails with commas
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="subject">Email Subject</Label>
              <Input
                id="subject"
                value={formData.email_subject}
                onChange={(e) => setFormData({ ...formData, email_subject: e.target.value })}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="body">Email Body</Label>
              <Textarea
                id="body"
                value={formData.email_body}
                onChange={(e) => setFormData({ ...formData, email_body: e.target.value })}
                rows={3}
              />
            </div>

            <div className="flex items-center space-x-2">
              <Switch
                id="active"
                checked={formData.is_active}
                onCheckedChange={(checked) => setFormData({ ...formData, is_active: checked })}
              />
              <Label htmlFor="active">Active</Label>
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setShowCreateDialog(false);
                setEditingExport(null);
                resetForm();
              }}
            >
              Cancel
            </Button>
            <Button onClick={editingExport ? handleUpdate : handleCreate}>
              {editingExport ? 'Update' : 'Create'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}