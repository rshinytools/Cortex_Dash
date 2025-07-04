// ABOUTME: Studies list page showing all studies the user has access to
// ABOUTME: Provides filtering, sorting, and navigation to individual study dashboards

'use client';

import { useState } from 'react';
import { useSession } from 'next-auth/react';
import { useQuery } from '@tanstack/react-query';
import { MainLayout } from '@/components/layout/main-layout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Search, Plus, BarChart3, Users, Calendar } from 'lucide-react';
import { apiClient, getErrorMessage } from '@/lib/api/client';
import { Study, StudyStatus, StudyPhase, PaginatedResponse } from '@/types';
import Link from 'next/link';
import { format } from 'date-fns';

export default function StudiesPage() {
  const { data: session } = useSession();
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [page, setPage] = useState(1);

  const { data, isLoading, error } = useQuery({
    queryKey: ['studies', searchTerm, statusFilter, page],
    queryFn: async () => {
      const params = new URLSearchParams({
        page: page.toString(),
        size: '10',
        ...(searchTerm && { search: searchTerm }),
        ...(statusFilter !== 'all' && { status: statusFilter }),
      });
      const response = await apiClient.get<PaginatedResponse<Study>>(`/studies?${params}`);
      return response.data;
    },
  });

  const getStatusColor = (status: StudyStatus) => {
    switch (status) {
      case StudyStatus.ACTIVE:
        return 'bg-green-100 text-green-800';
      case StudyStatus.PLANNING:
        return 'bg-blue-100 text-blue-800';
      case StudyStatus.COMPLETED:
        return 'bg-gray-100 text-gray-800';
      case StudyStatus.TERMINATED:
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getPhaseLabel = (phase: StudyPhase) => {
    return phase.replace('_', ' ').toUpperCase();
  };

  return (
    <MainLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Studies</h1>
            <p className="text-muted-foreground">
              Manage and monitor your clinical studies
            </p>
          </div>
          {(session?.user?.role === 'system_admin' || session?.user?.role === 'org_admin') && (
            <Button asChild>
              <Link href="/studies/new">
                <Plus className="mr-2 h-4 w-4" />
                New Study
              </Link>
            </Button>
          )}
        </div>

        <Card>
          <CardHeader>
            <div className="flex items-center space-x-4">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder="Search studies..."
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
              <div className="space-y-3">
                {[...Array(5)].map((_, i) => (
                  <Skeleton key={i} className="h-20" />
                ))}
              </div>
            ) : error ? (
              <div className="text-center py-8 text-destructive">
                {getErrorMessage(error)}
              </div>
            ) : data?.items.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                No studies found
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Study Name</TableHead>
                    <TableHead>Protocol</TableHead>
                    <TableHead>Phase</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Therapeutic Area</TableHead>
                    <TableHead>Start Date</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data?.items.map((study) => (
                    <TableRow key={study.id}>
                      <TableCell className="font-medium">{study.name}</TableCell>
                      <TableCell>{study.protocol_number}</TableCell>
                      <TableCell>{getPhaseLabel(study.phase)}</TableCell>
                      <TableCell>
                        <Badge variant="secondary" className={getStatusColor(study.status)}>
                          {study.status.replace('_', ' ')}
                        </Badge>
                      </TableCell>
                      <TableCell>{study.therapeutic_area}</TableCell>
                      <TableCell>{format(new Date(study.start_date), 'MMM d, yyyy')}</TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end space-x-2">
                          <Button variant="ghost" size="sm" asChild>
                            <Link href={`/studies/${study.id}/dashboard`}>
                              <BarChart3 className="h-4 w-4" />
                            </Link>
                          </Button>
                          <Button variant="ghost" size="sm" asChild>
                            <Link href={`/studies/${study.id}/enrollment`}>
                              <Users className="h-4 w-4" />
                            </Link>
                          </Button>
                          <Button variant="ghost" size="sm" asChild>
                            <Link href={`/studies/${study.id}/timeline`}>
                              <Calendar className="h-4 w-4" />
                            </Link>
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}

            {data && data.pages > 1 && (
              <div className="flex justify-center space-x-2 mt-4">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(page - 1)}
                  disabled={page === 1}
                >
                  Previous
                </Button>
                <span className="py-2 px-4 text-sm">
                  Page {page} of {data.pages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(page + 1)}
                  disabled={page === data.pages}
                >
                  Next
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  );
}