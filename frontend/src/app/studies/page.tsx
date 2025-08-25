// ABOUTME: Studies list page showing all studies with consistent navigation
// ABOUTME: System admin only - provides study management interface

'use client';

import { useState } from 'react';
import { useAuth } from '@/lib/auth-context';
import { useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { motion } from 'framer-motion';
import { ThemeToggle } from '@/components/ui/theme-toggle';
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
  Power,
  PowerOff,
  Upload,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Rocket
} from 'lucide-react';
import { secureApiClient } from '@/lib/api/secure-client';
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
import { DeleteStudyDialog } from '@/components/study/delete-study-dialog';

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
  // Initialization tracking
  initialization_status?: string;
  initialization_progress?: number;
  template_applied_at?: string;
  data_uploaded_at?: string;
  mappings_configured_at?: string;
  activated_at?: string;
}

export default function StudiesPage() {
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [initializationFilter, setInitializationFilter] = useState<string>('all');

  // Declare all hooks before any conditional logic
  const { data: studies, isLoading } = useQuery({
    queryKey: ['studies', searchTerm, statusFilter, initializationFilter],
    queryFn: async () => {
      const response = await secureApiClient.get<Study[]>('/studies/');
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
      
      if (initializationFilter !== 'all') {
        filtered = filtered.filter(study => {
          const initStatus = study.initialization_status || 'not_started';
          return initStatus === initializationFilter;
        });
      }
      
      return filtered;
    },
    enabled: isAuthenticated && user?.role === UserRole.SYSTEM_ADMIN,
  });

  const archiveStudy = useMutation({
    mutationFn: (studyId: string) => studiesApi.deleteStudy(studyId, false),
    onSuccess: () => {
      toast({
        title: 'Study archived',
        description: 'The study has been archived successfully.',
      });
      queryClient.invalidateQueries({ queryKey: ['studies'] });
    },
    onError: (error) => {
      toast({
        title: 'Archive failed',
        description: error instanceof Error ? error.message : 'An error occurred',
        variant: 'destructive',
      });
    },
  });

  const deleteStudy = useMutation({
    mutationFn: (studyId: string) => studiesApi.deleteStudy(studyId, true),
    onSuccess: () => {
      toast({
        title: 'Study deleted',
        description: 'The study has been permanently deleted.',
        variant: 'default',
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
  if (authLoading || isLoading) {
    return (
      <div className="container mx-auto py-6">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      </div>
    );
  }

  // Check if user is system admin - after loading check
  if (user?.role !== UserRole.SYSTEM_ADMIN) {
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
      case StudyStatus.DRAFT:
        return 'outline';
      case StudyStatus.ACTIVE:
        return 'default';
      case StudyStatus.PLANNING:
        return 'secondary';
      case StudyStatus.COMPLETED:
        return 'outline';
      case StudyStatus.ARCHIVED:
        return 'destructive';
      case StudyStatus.PAUSED:
        return 'outline';
      case StudyStatus.SETUP:
        return 'secondary';
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

  const getInitializationStatus = (study: Study) => {
    const status = study.initialization_status || 'not_started';
    const progress = study.initialization_progress || 0;

    switch (status) {
      case 'not_started':
        return (
          <Badge variant="outline" className="gap-1">
            <AlertCircle className="h-3 w-3" />
            Not Started
          </Badge>
        );
      case 'pending':
      case 'in_progress':
        return (
          <div className="flex items-center gap-2">
            <Loader2 className="h-3 w-3 animate-spin text-blue-500" />
            <span className="text-sm text-muted-foreground">{progress}%</span>
          </div>
        );
      case 'completed':
        return (
          <Badge variant="default" className="gap-1 bg-green-500">
            <CheckCircle2 className="h-3 w-3" />
            Completed
          </Badge>
        );
      case 'failed':
        return (
          <Badge variant="destructive" className="gap-1">
            <AlertCircle className="h-3 w-3" />
            Failed
          </Badge>
        );
      default:
        return (
          <Badge variant="secondary">
            {status}
          </Badge>
        );
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="container mx-auto py-8 px-4">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="mb-8"
        >
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

          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 dark:from-blue-400 dark:to-purple-400 bg-clip-text text-transparent flex items-center gap-3">
                <FlaskConical className="h-8 w-8 text-blue-600 dark:text-blue-400" />
                Clinical Studies
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mt-2">
                Manage and monitor all clinical studies across organizations
              </p>
            </div>
            <div className="flex items-center gap-3">
              <ThemeToggle />
              <UserMenu />
            </div>
          </div>
        </motion.div>

        {/* Stats Cards */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.1 }}
          className="grid gap-6 md:grid-cols-4 mb-8"
        >
          <Card className="border-0 shadow-lg bg-white dark:bg-gray-800 hover:shadow-xl transition-shadow">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Total Studies</p>
                  <p className="text-3xl font-bold text-gray-900 dark:text-gray-100 mt-1">
                    {studies?.length || 0}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">All organizations</p>
                </div>
                <div className="h-12 w-12 bg-blue-100 dark:bg-blue-900/20 rounded-lg flex items-center justify-center">
                  <FlaskConical className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="border-0 shadow-lg bg-white dark:bg-gray-800 hover:shadow-xl transition-shadow">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Active Studies</p>
                  <p className="text-3xl font-bold text-gray-900 dark:text-gray-100 mt-1">
                    {studies?.filter(s => s.status === StudyStatus.ACTIVE).length || 0}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">Currently running</p>
                </div>
                <div className="h-12 w-12 bg-green-100 dark:bg-green-900/20 rounded-lg flex items-center justify-center">
                  <CheckCircle2 className="h-6 w-6 text-green-600 dark:text-green-400" />
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="border-0 shadow-lg bg-white dark:bg-gray-800 hover:shadow-xl transition-shadow">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Setup Phase</p>
                  <p className="text-3xl font-bold text-gray-900 dark:text-gray-100 mt-1">
                    {studies?.filter(s => s.status === StudyStatus.SETUP).length || 0}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">Being configured</p>
                </div>
                <div className="h-12 w-12 bg-yellow-100 dark:bg-yellow-900/20 rounded-lg flex items-center justify-center">
                  <Settings className="h-6 w-6 text-yellow-600 dark:text-yellow-400" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-lg bg-white dark:bg-gray-800 hover:shadow-xl transition-shadow">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Completed</p>
                  <p className="text-3xl font-bold text-gray-900 dark:text-gray-100 mt-1">
                    {studies?.filter(s => s.status === StudyStatus.COMPLETED).length || 0}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">Finished studies</p>
                </div>
                <div className="h-12 w-12 bg-purple-100 dark:bg-purple-900/20 rounded-lg flex items-center justify-center">
                  <Database className="h-6 w-6 text-purple-600 dark:text-purple-400" />
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Action Button */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.2 }}
          className="flex justify-end mb-6"
        >
          <Button 
            onClick={() => router.push('/studies/new')}
            className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white shadow-lg"
          >
            <Plus className="h-4 w-4 mr-2" />
            New Study
          </Button>
        </motion.div>

        {/* Main Content */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.3 }}
        >
          <Card className="border-0 shadow-lg bg-white dark:bg-gray-800">
            <CardHeader className="bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-700 rounded-t-lg">
          <div className="flex items-center gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-500 dark:text-gray-400" />
              <Input
                placeholder="Search studies by name, code, or protocol..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600"
              />
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[180px] bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent className="bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700">
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value={StudyStatus.DRAFT}>Draft</SelectItem>
                <SelectItem value={StudyStatus.PLANNING}>Planning</SelectItem>
                <SelectItem value={StudyStatus.SETUP}>Setup</SelectItem>
                <SelectItem value={StudyStatus.ACTIVE}>Active</SelectItem>
                <SelectItem value={StudyStatus.PAUSED}>Paused</SelectItem>
                <SelectItem value={StudyStatus.COMPLETED}>Completed</SelectItem>
                <SelectItem value={StudyStatus.ARCHIVED}>Archived</SelectItem>
              </SelectContent>
            </Select>
            <Select value={initializationFilter} onValueChange={setInitializationFilter}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Initialization status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Initialization</SelectItem>
                <SelectItem value="not_started">Not Started</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="in_progress">In Progress</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
                <SelectItem value="failed">Failed</SelectItem>
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
              <TableHeader className="bg-gray-50 dark:bg-gray-700/50">
                <TableRow className="border-gray-200 dark:border-gray-700">
                  <TableHead className="text-gray-700 dark:text-gray-300">Study</TableHead>
                  <TableHead className="text-gray-700 dark:text-gray-300">Organization</TableHead>
                  <TableHead className="text-gray-700 dark:text-gray-300">Phase</TableHead>
                  <TableHead className="text-gray-700 dark:text-gray-300">Status</TableHead>
                  <TableHead className="text-gray-700 dark:text-gray-300">Initialization</TableHead>
                  <TableHead className="text-gray-700 dark:text-gray-300">Activation Date</TableHead>
                  <TableHead className="text-right text-gray-700 dark:text-gray-300">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {studies.map((study) => (
                  <TableRow key={study.id} className="border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/30">
                    <TableCell className="text-gray-900 dark:text-gray-100">
                      <div>
                        <div className="font-medium">{study.name}</div>
                        <div className="text-sm text-gray-500 dark:text-gray-400">
                          {study.code} • {study.protocol_number}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="text-gray-700 dark:text-gray-300">
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
                      {getInitializationStatus(study)}
                    </TableCell>
                    <TableCell className="text-gray-700 dark:text-gray-300">
                      {study.activated_at 
                        ? format(new Date(study.activated_at), 'MMM d, yyyy')
                        : study.start_date 
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
                            onClick={() => router.push(`/studies/${study.id}/manage`)}
                          >
                            <Settings className="mr-2 h-4 w-4" />
                            Manage Study
                          </DropdownMenuItem>
                          {study.initialization_status && study.initialization_status !== 'completed' && (
                            <DropdownMenuItem 
                              onClick={() => router.push(`/initialization/${study.id}`)}
                            >
                              <Rocket className="mr-2 h-4 w-4" />
                              View Initialization
                            </DropdownMenuItem>
                          )}
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
                          <DeleteStudyDialog
                            study={study}
                            onArchive={(id) => archiveStudy.mutate(id)}
                            onDelete={(id) => deleteStudy.mutate(id)}
                            isArchiving={archiveStudy.isPending}
                            isDeleting={deleteStudy.isPending}
                            isSuperuser={user?.is_superuser}
                          />
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
    </motion.div>
      </div>
    </div>
  );
}