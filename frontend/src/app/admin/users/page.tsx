// ABOUTME: User management page - system_admin sees all users, org_admin sees only their org users
// ABOUTME: Allows user creation, role assignment, and user management

'use client';

import { useState } from 'react';
import { useAuth } from '@/lib/auth-context';
import { AuthGuard } from '@/components/auth-guard';
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
  ArrowLeft,
  Users,
  UserCheck,
  Search,
  Activity,
  Building2
} from 'lucide-react';
import { UserRole } from '@/types';
import { apiClient } from '@/lib/api/client';
import { format } from 'date-fns';
import { useToast } from '@/hooks/use-toast';
import { UserMenu } from '@/components/user-menu';
import { ThemeToggle } from '@/components/ui/theme-toggle';
import { motion } from 'framer-motion';

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

function UsersContent() {
  const { user } = useAuth();
  const router = useRouter();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [searchTerm, setSearchTerm] = useState('');

  const canAccessPage = user?.role && 
    [UserRole.SYSTEM_ADMIN, UserRole.ORG_ADMIN].includes(user.role as UserRole);

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

  const filteredUsers = users.filter((userItem) => {
    const matchesSearch = 
      userItem.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      userItem.full_name.toLowerCase().includes(searchTerm.toLowerCase());
    
    // Org admins only see users from their organization
    if (user?.role === UserRole.ORG_ADMIN) {
      return matchesSearch && userItem.org_id === user.org_id;
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

  // Calculate stats
  const activeUsers = users.filter(u => u.is_active).length;
  const adminUsers = users.filter(u => u.role === UserRole.SYSTEM_ADMIN || u.role === UserRole.ORG_ADMIN).length;
  const recentUsers = users.filter(u => {
    const createdDate = new Date(u.created_at);
    const weekAgo = new Date();
    weekAgo.setDate(weekAgo.getDate() - 7);
    return createdDate > weekAgo;
  }).length;

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
            <span className="text-foreground">User Management</span>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 dark:from-blue-400 dark:to-purple-400 bg-clip-text text-transparent">
                User Management
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mt-2">
                {user?.role === UserRole.SYSTEM_ADMIN 
                  ? 'Manage all users across the platform'
                  : 'Manage users in your organization'
                }
              </p>
            </div>
            <div className="flex items-center gap-4">
              <Button 
                onClick={() => router.push('/admin/users/new')}
                className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white"
              >
                <Plus className="h-4 w-4 mr-2" />
                Add User
              </Button>
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
          className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8"
        >
          <Card className="border-0 shadow-lg bg-white dark:bg-gray-800 hover:shadow-xl transition-shadow">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Total Users</p>
                  <p className="text-3xl font-bold text-gray-900 dark:text-gray-100 mt-1">
                    {users.length}
                  </p>
                </div>
                <div className="h-12 w-12 bg-blue-100 dark:bg-blue-900/20 rounded-lg flex items-center justify-center">
                  <Users className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-lg bg-white dark:bg-gray-800 hover:shadow-xl transition-shadow">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Active Users</p>
                  <p className="text-3xl font-bold text-gray-900 dark:text-gray-100 mt-1">
                    {activeUsers}
                  </p>
                </div>
                <div className="h-12 w-12 bg-green-100 dark:bg-green-900/20 rounded-lg flex items-center justify-center">
                  <UserCheck className="h-6 w-6 text-green-600 dark:text-green-400" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-lg bg-white dark:bg-gray-800 hover:shadow-xl transition-shadow">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Admin Users</p>
                  <p className="text-3xl font-bold text-gray-900 dark:text-gray-100 mt-1">
                    {adminUsers}
                  </p>
                </div>
                <div className="h-12 w-12 bg-purple-100 dark:bg-purple-900/20 rounded-lg flex items-center justify-center">
                  <Shield className="h-6 w-6 text-purple-600 dark:text-purple-400" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-lg bg-white dark:bg-gray-800 hover:shadow-xl transition-shadow">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">New This Week</p>
                  <p className="text-3xl font-bold text-gray-900 dark:text-gray-100 mt-1">
                    {recentUsers}
                  </p>
                </div>
                <div className="h-12 w-12 bg-orange-100 dark:bg-orange-900/20 rounded-lg flex items-center justify-center">
                  <Activity className="h-6 w-6 text-orange-600 dark:text-orange-400" />
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Main Content */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.2 }}
        >
          <Card className="border-0 shadow-lg bg-white dark:bg-gray-800">
            <CardHeader className="bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-700 rounded-t-lg">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-xl text-gray-900 dark:text-gray-100">User Directory</CardTitle>
                  <CardDescription className="text-gray-600 dark:text-gray-400">
                    {filteredUsers?.length || 0} of {users.length} users shown
                  </CardDescription>
                </div>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <Input
                    placeholder="Search users..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10 w-64 bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-600"
                  />
                </div>
              </div>
            </CardHeader>
            <CardContent className="p-0">

              {isLoading ? (
                <div className="flex items-center justify-center h-64">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
                </div>
              ) : filteredUsers && filteredUsers.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow className="border-b border-gray-200 dark:border-gray-700">
                      <TableHead className="text-gray-700 dark:text-gray-300 font-semibold">User</TableHead>
                      <TableHead className="text-gray-700 dark:text-gray-300 font-semibold">Role</TableHead>
                      {user?.role === UserRole.SYSTEM_ADMIN && (
                        <TableHead className="text-gray-700 dark:text-gray-300 font-semibold">Organization</TableHead>
                      )}
                      <TableHead className="text-gray-700 dark:text-gray-300 font-semibold">Status</TableHead>
                      <TableHead className="text-gray-700 dark:text-gray-300 font-semibold">Last Login</TableHead>
                      <TableHead className="text-right text-gray-700 dark:text-gray-300 font-semibold">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredUsers.map((userItem, index) => (
                      <motion.tr
                        key={userItem.id}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ duration: 0.3, delay: index * 0.05 }}
                        className="border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                      >
                        <TableCell className="py-4">
                          <div className="flex items-center gap-3">
                            <div className="h-10 w-10 bg-gradient-to-br from-blue-500 to-purple-500 rounded-full flex items-center justify-center text-white font-semibold">
                              {userItem.full_name.charAt(0).toUpperCase()}
                            </div>
                            <div>
                              <div className="font-medium text-gray-900 dark:text-gray-100">{userItem.full_name}</div>
                              <div className="text-sm text-gray-500 dark:text-gray-400">
                                {userItem.email}
                              </div>
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge 
                            variant={getRoleBadgeVariant(userItem.role)}
                            className="font-medium"
                          >
                            {userItem.role.replace('_', ' ')}
                          </Badge>
                        </TableCell>
                        {user?.role === UserRole.SYSTEM_ADMIN && (
                          <TableCell>
                            <div className="flex items-center gap-2">
                              <Building2 className="h-4 w-4 text-gray-400" />
                              <span className="text-gray-700 dark:text-gray-300">
                                {userItem.organization?.name || '-'}
                              </span>
                            </div>
                          </TableCell>
                        )}
                        <TableCell>
                          <Badge 
                            variant={userItem.is_active ? 'default' : 'secondary'}
                            className={userItem.is_active ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' : ''}
                          >
                            {userItem.is_active ? 'Active' : 'Inactive'}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-gray-600 dark:text-gray-400">
                          {userItem.last_login 
                            ? format(new Date(userItem.last_login), 'MMM d, yyyy')
                            : 'Never'
                          }
                        </TableCell>
                        <TableCell className="text-right">
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" className="h-8 w-8 p-0 hover:bg-gray-100 dark:hover:bg-gray-700">
                                <span className="sr-only">Open menu</span>
                                <MoreHorizontal className="h-4 w-4 text-gray-600 dark:text-gray-400" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end" className="bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700">
                              <DropdownMenuLabel className="text-gray-700 dark:text-gray-300">Actions</DropdownMenuLabel>
                              <DropdownMenuItem
                                onClick={() => router.push(`/admin/users/${userItem.id}/edit`)}
                                className="text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                              >
                                <Edit className="mr-2 h-4 w-4" />
                                Edit User
                              </DropdownMenuItem>
                              <DropdownMenuItem className="text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700">
                                <Mail className="mr-2 h-4 w-4" />
                                Send Reset Email
                              </DropdownMenuItem>
                              <DropdownMenuSeparator className="bg-gray-200 dark:bg-gray-700" />
                              <DropdownMenuItem
                                onClick={() => toggleUserStatus.mutate({ 
                                  userId: userItem.id, 
                                  isActive: userItem.is_active 
                                })}
                                className="text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                              >
                                <UserX className="mr-2 h-4 w-4" />
                                {userItem.is_active ? 'Deactivate' : 'Activate'} User
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </TableCell>
                      </motion.tr>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <div className="flex flex-col items-center justify-center py-12">
                  <Users className="h-12 w-12 text-gray-400 mb-4" />
                  <p className="text-gray-500 dark:text-gray-400 text-lg">No users found</p>
                  <p className="text-gray-400 dark:text-gray-500 text-sm mt-1">
                    {searchTerm ? 'Try adjusting your search criteria' : 'Add your first user to get started'}
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}

export default function UsersPage() {
  return (
    <AuthGuard requiredRoles={['system_admin', 'org_admin']}>
      <UsersContent />
    </AuthGuard>
  );
}