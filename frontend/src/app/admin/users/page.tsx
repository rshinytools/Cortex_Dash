// ABOUTME: User management page - system_admin sees all users, org_admin sees only their org users
// ABOUTME: Allows user creation, role assignment, and user management

'use client';

import { useState } from 'react';
import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { 
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { 
  Plus,
  MoreHorizontal,
  Shield,
  UserX,
  Mail,
  Edit,
  ArrowLeft
} from 'lucide-react';
import { UserRole } from '@/types';
import { apiClient } from '@/lib/api/client';
import { format } from 'date-fns';
import { useToast } from '@/hooks/use-toast';
import { UserMenu } from '@/components/user-menu';

interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  created_at: string;
  last_login?: string;
  org_id?: string;
  organization?: {
    name: string;
  };
}

export default function UsersPage() {
  const { data: session } = useSession();
  const router = useRouter();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [searchTerm, setSearchTerm] = useState('');

  const canAccessPage = session?.user?.role && 
    [UserRole.SYSTEM_ADMIN, UserRole.ORG_ADMIN].includes(session.user.role as UserRole);

  const { data: usersResponse, isLoading } = useQuery({
    queryKey: ['users'],
    queryFn: async () => {
      const response = await apiClient.get<{ data: User[]; count: number }>('/users/');
      return response.data;
    },
    enabled: canAccessPage,
  });

  const users = usersResponse?.data || [];

  const toggleUserStatus = useMutation({
    mutationFn: async ({ userId, isActive }: { userId: string; isActive: boolean }) => {
      const response = await apiClient.patch(`/users/${userId}/`, {
        is_active: !isActive,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      toast({
        title: 'User status updated',
        description: 'The user status has been changed successfully.',
      });
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to update user status.',
        variant: 'destructive',
      });
    },
  });

  const filteredUsers = users.filter((user) => {
    const matchesSearch = 
      user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.full_name.toLowerCase().includes(searchTerm.toLowerCase());
    
    // Org admins only see users from their organization
    if (session?.user?.role === UserRole.ORG_ADMIN) {
      return matchesSearch && user.org_id === session.user.org_id;
    }
    
    return matchesSearch;
  });

  const getRoleBadgeVariant = (role: string) => {
    switch (role) {
      case UserRole.SYSTEM_ADMIN:
        return 'destructive';
      case UserRole.ORG_ADMIN:
        return 'default';
      default:
        return 'secondary';
    }
  };

  // Check permissions after all hooks
  if (!canAccessPage) {
    return (
      <div className="container mx-auto py-6">
        <Card>
          <CardContent className="py-6">
            <p className="text-center text-muted-foreground">
              You don't have permission to access this page.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

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
        <span className="text-foreground">User Management</span>
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
          <h1 className="text-3xl font-bold">User Management</h1>
          <p className="text-muted-foreground mt-1">
            {session?.user?.role === UserRole.SYSTEM_ADMIN 
              ? 'Manage all users in the system'
              : 'Manage users in your organization'
            }
          </p>
        </div>
        <div className="flex items-center gap-4">
          <Button onClick={() => router.push('/admin/users/new')}>
            <Plus className="h-4 w-4 mr-2" />
            Add User
          </Button>
          <UserMenu />
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Users</CardTitle>
          <CardDescription>
            {filteredUsers?.length || 0} users found
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="mb-4">
            <Input
              placeholder="Search by name or email..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="max-w-sm"
            />
          </div>

          {isLoading ? (
            <div className="flex items-center justify-center h-32">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          ) : filteredUsers && filteredUsers.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>User</TableHead>
                  <TableHead>Role</TableHead>
                  {session?.user?.role === UserRole.SYSTEM_ADMIN && (
                    <TableHead>Organization</TableHead>
                  )}
                  <TableHead>Status</TableHead>
                  <TableHead>Last Login</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredUsers.map((user) => (
                  <TableRow key={user.id}>
                    <TableCell>
                      <div>
                        <div className="font-medium">{user.full_name}</div>
                        <div className="text-sm text-muted-foreground">
                          {user.email}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant={getRoleBadgeVariant(user.role)}>
                        {user.role.replace('_', ' ')}
                      </Badge>
                    </TableCell>
                    {session?.user?.role === UserRole.SYSTEM_ADMIN && (
                      <TableCell>
                        {user.organization?.name || '-'}
                      </TableCell>
                    )}
                    <TableCell>
                      <Badge variant={user.is_active ? 'default' : 'secondary'}>
                        {user.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {user.last_login 
                        ? format(new Date(user.last_login), 'MMM d, yyyy')
                        : 'Never'
                      }
                    </TableCell>
                    <TableCell className="text-right">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" className="h-8 w-8 p-0">
                            <span className="sr-only">Open menu</span>
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuLabel>Actions</DropdownMenuLabel>
                          <DropdownMenuItem
                            onClick={() => router.push(`/admin/users/${user.id}/edit`)}
                          >
                            <Edit className="mr-2 h-4 w-4" />
                            Edit User
                          </DropdownMenuItem>
                          <DropdownMenuItem>
                            <Mail className="mr-2 h-4 w-4" />
                            Send Reset Email
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem
                            onClick={() => toggleUserStatus.mutate({ 
                              userId: user.id, 
                              isActive: user.is_active 
                            })}
                          >
                            <UserX className="mr-2 h-4 w-4" />
                            {user.is_active ? 'Deactivate' : 'Activate'} User
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="text-center py-8">
              <p className="text-muted-foreground">No users found</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}