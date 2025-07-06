// ABOUTME: Studies list page showing all studies with consistent navigation
// ABOUTME: System admin only - provides study management interface

'use client';

import { useState } from 'react';
import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from '@/components/ui/table';
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from '@/components/ui/select';
import { 
  Search, 
  Plus, 
  BarChart3, 
  Users, 
  Calendar, 
  Settings, 
  Database, 
  GitBranch,
  ArrowLeft,
  FlaskConical,
  MoreHorizontal,
  Edit,
  Trash2,
  Power,
  PowerOff,
  Upload
} from 'lucide-react';
import { apiClient } from '@/lib/api/client';
import { UserRole, StudyStatus, StudyPhase } from '@/types';
import { format } from 'date-fns';
import { UserMenu } from '@/components/user-menu';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { studiesApi } from '@/lib/api/studies';
import { useToast } from '@/hooks/use-toast';
import { useMutation, useQueryClient } from '@tanstack/react-query';

interface Study {
  id: string;
  name: string;
  code: string;
  protocol_number: string;
  phase: StudyPhase;
  status: StudyStatus;
  therapeutic_area?: string;
  indication?: string;
  planned_start_date?: string;
  planned_end_date?: string;
  start_date?: string;
  end_date?: string;
  org_id: string;
  is_active?: boolean;
  organization?: {
    name: string;
  };
}

export default function StudiesPage() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  // Declare all hooks before any conditional logic
  const { data: studies, isLoading } = useQuery({
    queryKey: ['studies', searchTerm, statusFilter],
    queryFn: async () => {
      const response = await apiClient.get<Study[]>('/studies/');
      let filtered = response.data;
      
      // Apply filters
      if (searchTerm) {
        filtered = filtered.filter(study => 
          study.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          study.code.toLowerCase().includes(searchTerm.toLowerCase()) ||
          study.protocol_number.toLowerCase().includes(searchTerm.toLowerCase())
        );
      }
      
      if (statusFilter !== 'all') {
        filtered = filtered.filter(study => study.status === statusFilter);
      }
      
      return filtered;
    },
    enabled: status === 'authenticated' && session?.user?.role === UserRole.SYSTEM_ADMIN,
  });

  const deleteStudy = useMutation({
    mutationFn: (studyId: string) => studiesApi.deleteStudy(studyId),
    onSuccess: () => {
      toast({
        title: 'Study deleted',
        description: 'The study has been deleted successfully.',
      });
      queryClient.invalidateQueries({ queryKey: ['studies'] });
    },
    onError: (error) => {
      toast({
        title: 'Delete failed',
        description: error instanceof Error ? error.message : 'An error occurred',
        variant: 'destructive',
      });
    },
  });

  const activateStudy = useMutation({
    mutationFn: (studyId: string) => studiesApi.activateStudy(studyId),
    onSuccess: () => {
      toast({
        title: 'Study activated',
        description: 'The study has been activated successfully.',
      });
      queryClient.invalidateQueries({ queryKey: ['studies'] });
    },
    onError: (error) => {
      toast({
        title: 'Activation failed',
        description: error instanceof Error ? error.message : 'An error occurred',
        variant: 'destructive',
      });
    },
  });

  const deactivateStudy = useMutation({
    mutationFn: (studyId: string) => studiesApi.deactivateStudy(studyId),
    onSuccess: () => {
      toast({
        title: 'Study deactivated',
        description: 'The study has been deactivated successfully.',
      });
      queryClient.invalidateQueries({ queryKey: ['studies'] });
    },
    onError: (error) => {
      toast({
        title: 'Deactivation failed',
        description: error instanceof Error ? error.message : 'An error occurred',
        variant: 'destructive',
      });
    },
  });

  // Show loading state while session is being fetched
  if (status === 'loading') {
    return (
      <div className="container mx-auto py-6">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      </div>
    );
  }

  // Check if user is system admin - after loading check
  if (session?.user?.role !== UserRole.SYSTEM_ADMIN) {
    return (
      <div className="container mx-auto py-6">
        <Card>
          <CardContent className="py-6">
            <p className="text-center text-muted-foreground">
              Access denied. This page is only available to system administrators.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const getStatusBadgeVariant = (status: StudyStatus) => {
    switch (status) {
      case StudyStatus.ACTIVE:
        return 'default';
      case StudyStatus.PLANNING:
        return 'secondary';
      case StudyStatus.COMPLETED:
        return 'outline';
      case StudyStatus.TERMINATED:
        return 'destructive';
      default:
        return 'secondary';
    }
  };

  const getPhaseBadgeVariant = (phase: StudyPhase) => {
    switch (phase) {
      case StudyPhase.PHASE_1:
        return 'secondary';
      case StudyPhase.PHASE_2:
        return 'secondary';
      case StudyPhase.PHASE_3:
        return 'default';
      case StudyPhase.PHASE_4:
        return 'default';
      default:
        return 'secondary';
    }
  };

  return (
    <div className="container mx-auto py-6">
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
        <span className="text-foreground">Studies</span>
      </div>

      <div className="flex items-center mb-6">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => router.push('/admin')}
          className="mr-4"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Admin
        </Button>
        <div className="flex-1">
          <h1 className="text-3xl font-bold">Clinical Studies</h1>
          <p className="text-muted-foreground mt-1">
            Manage and monitor all clinical studies across organizations
          </p>
        </div>
        <div className="flex items-center gap-4">
          <Button onClick={() => router.push('/studies/new')}>
            <Plus className="h-4 w-4 mr-2" />
            New Study
          </Button>
          <UserMenu />
        </div>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search studies by name, code, or protocol..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value={StudyStatus.PLANNING}>Planning</SelectItem>
                <SelectItem value={StudyStatus.ACTIVE}>Active</SelectItem>
                <SelectItem value={StudyStatus.COMPLETED}>Completed</SelectItem>
                <SelectItem value={StudyStatus.TERMINATED}>Terminated</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          ) : studies && studies.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Study</TableHead>
                  <TableHead>Organization</TableHead>
                  <TableHead>Phase</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Start Date</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {studies.map((study) => (
                  <TableRow key={study.id}>
                    <TableCell>
                      <div>
                        <div className="font-medium">{study.name}</div>
                        <div className="text-sm text-muted-foreground">
                          {study.code} • {study.protocol_number}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      {study.organization?.name || 'Unknown'}
                    </TableCell>
                    <TableCell>
                      <Badge variant={getPhaseBadgeVariant(study.phase)}>
                        {study.phase.replace('_', ' ')}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant={getStatusBadgeVariant(study.status)}>
                        {study.status}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {study.start_date 
                        ? format(new Date(study.start_date), 'MMM d, yyyy')
                        : study.planned_start_date
                        ? format(new Date(study.planned_start_date), 'MMM d, yyyy')
                        : 'Not set'
                      }
                    </TableCell>
                    <TableCell className="text-right">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem 
                            onClick={() => router.push(`/studies/${study.id}/dashboard`)}
                          >
                            <BarChart3 className="mr-2 h-4 w-4" />
                            View Dashboard
                          </DropdownMenuItem>
                          <DropdownMenuItem 
                            onClick={() => router.push(`/studies/${study.id}/data-sources`)}
                          >
                            <Database className="mr-2 h-4 w-4" />
                            Data Sources
                          </DropdownMenuItem>
                          <DropdownMenuItem 
                            onClick={() => router.push(`/studies/${study.id}/data-sources/upload`)}
                          >
                            <Upload className="mr-2 h-4 w-4" />
                            Upload Data
                          </DropdownMenuItem>
                          <DropdownMenuItem 
                            onClick={() => router.push(`/studies/${study.id}/pipeline`)}
                          >
                            <GitBranch className="mr-2 h-4 w-4" />
                            Pipeline
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem 
                            onClick={() => router.push(`/studies/${study.id}/edit`)}
                          >
                            <Edit className="mr-2 h-4 w-4" />
                            Edit Study
                          </DropdownMenuItem>
                          <DropdownMenuItem 
                            onClick={() => router.push(`/studies/${study.id}/settings`)}
                          >
                            <Settings className="mr-2 h-4 w-4" />
                            Settings
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          {study.is_active ? (
                            <DropdownMenuItem 
                              onClick={() => {
                                if (confirm(`Are you sure you want to deactivate ${study.name}?`)) {
                                  deactivateStudy.mutate(study.id);
                                }
                              }}
                            >
                              <PowerOff className="mr-2 h-4 w-4" />
                              Deactivate Study
                            </DropdownMenuItem>
                          ) : (
                            <DropdownMenuItem 
                              onClick={() => {
                                if (confirm(`Are you sure you want to activate ${study.name}?`)) {
                                  activateStudy.mutate(study.id);
                                }
                              }}
                            >
                              <Power className="mr-2 h-4 w-4" />
                              Activate Study
                            </DropdownMenuItem>
                          )}
                          <DropdownMenuItem 
                            className="text-destructive"
                            onClick={() => {
                              if (confirm(`Are you sure you want to delete ${study.name}? This action cannot be undone.`)) {
                                deleteStudy.mutate(study.id);
                              }
                            }}
                          >
                            <Trash2 className="mr-2 h-4 w-4" />
                            Delete Study
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="text-center py-12">
              <FlaskConical className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">
                {searchTerm || statusFilter !== 'all' ? 'No studies found' : 'No studies yet'}
              </h3>
              <p className="text-muted-foreground mb-4">
                {searchTerm || statusFilter !== 'all' 
                  ? 'Try adjusting your search or filters'
                  : 'Create your first study to get started'
                }
              </p>
              {!searchTerm && statusFilter === 'all' && (
                <Button onClick={() => router.push('/studies/new')}>
                  <Plus className="h-4 w-4 mr-2" />
                  Create Study
                </Button>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}