// ABOUTME: Organizations list page - system admin only
// ABOUTME: Displays all organizations and allows creation/management

'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Plus, Building2, Users, FlaskConical, Settings, ArrowLeft, Activity, Shield } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { motion } from 'framer-motion';
import { ThemeToggle } from '@/components/ui/theme-toggle';
import { useQuery } from '@tanstack/react-query';
import { organizationsApi } from '@/lib/api/organizations';
import { useAuth } from '@/lib/auth-context';
import { UserRole } from '@/types';
import { format } from 'date-fns';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { UserMenu } from '@/components/user-menu';

export default function OrganizationsPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();

  const { data: organizations, isLoading } = useQuery({
    queryKey: ['organizations'],
    queryFn: organizationsApi.getOrganizations,
    enabled: isAuthenticated && user?.role === UserRole.SYSTEM_ADMIN,
  });

  // Show loading state while auth is being checked
  if (authLoading || isLoading) {
    return (
      <div className="container mx-auto py-6">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      </div>
    );
  }

  // Check if user is system admin - after all hooks and loading check
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

  const getLicenseBadgeVariant = (type: string) => {
    switch (type) {
      case 'trial':
        return 'secondary';
      case 'basic':
        return 'default';
      case 'professional':
        return 'default';
      case 'enterprise':
        return 'default';
      default:
        return 'secondary';
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
            <span className="text-foreground">Organizations</span>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-indigo-600 to-blue-600 dark:from-indigo-400 dark:to-blue-400 bg-clip-text text-transparent flex items-center gap-3">
                <Building2 className="h-8 w-8 text-indigo-600 dark:text-indigo-400" />
                Organizations
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mt-2">
                Manage client organizations and their settings
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
                  <p className="text-sm text-gray-600 dark:text-gray-400">Total Organizations</p>
                  <p className="text-3xl font-bold text-gray-900 dark:text-gray-100 mt-1">
                    {organizations?.length || 0}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">Registered</p>
                </div>
                <div className="h-12 w-12 bg-indigo-100 dark:bg-indigo-900/20 rounded-lg flex items-center justify-center">
                  <Building2 className="h-6 w-6 text-indigo-600 dark:text-indigo-400" />
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="border-0 shadow-lg bg-white dark:bg-gray-800 hover:shadow-xl transition-shadow">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Active Organizations</p>
                  <p className="text-3xl font-bold text-gray-900 dark:text-gray-100 mt-1">
                    {organizations?.filter(org => org.active).length || 0}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">Currently active</p>
                </div>
                <div className="h-12 w-12 bg-green-100 dark:bg-green-900/20 rounded-lg flex items-center justify-center">
                  <Activity className="h-6 w-6 text-green-600 dark:text-green-400" />
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="border-0 shadow-lg bg-white dark:bg-gray-800 hover:shadow-xl transition-shadow">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Total Users</p>
                  <p className="text-3xl font-bold text-gray-900 dark:text-gray-100 mt-1">
                    {organizations?.reduce((sum, org) => sum + ((org as any).user_count || 0), 0) || 0}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">Across all orgs</p>
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
                  <p className="text-sm text-gray-600 dark:text-gray-400">Total Studies</p>
                  <p className="text-3xl font-bold text-gray-900 dark:text-gray-100 mt-1">
                    {organizations?.reduce((sum, org) => sum + ((org as any).study_count || 0), 0) || 0}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">All studies</p>
                </div>
                <div className="h-12 w-12 bg-purple-100 dark:bg-purple-900/20 rounded-lg flex items-center justify-center">
                  <FlaskConical className="h-6 w-6 text-purple-600 dark:text-purple-400" />
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
            onClick={() => router.push('/organizations/new')}
            className="bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-700 hover:to-blue-700 text-white shadow-lg"
          >
            <Plus className="h-4 w-4 mr-2" />
            New Organization
          </Button>
        </motion.div>

      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      ) : organizations && organizations.length > 0 ? (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.3 }}
        >
          <Card className="border-0 shadow-lg bg-white dark:bg-gray-800">
            <CardHeader className="bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-700 rounded-t-lg">
              <CardTitle className="text-xl text-gray-900 dark:text-gray-100">All Organizations</CardTitle>
              <CardDescription className="text-gray-600 dark:text-gray-400">
                {organizations.length} organizations registered
              </CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <Table>
                <TableHeader className="bg-gray-50 dark:bg-gray-700/50">
                  <TableRow className="border-gray-200 dark:border-gray-700">
                    <TableHead className="text-gray-700 dark:text-gray-300">Organization</TableHead>
                    <TableHead className="text-gray-700 dark:text-gray-300">License</TableHead>
                    <TableHead className="text-gray-700 dark:text-gray-300">Limits</TableHead>
                    <TableHead className="text-gray-700 dark:text-gray-300">Status</TableHead>
                    <TableHead className="text-gray-700 dark:text-gray-300">Created</TableHead>
                    <TableHead className="text-right text-gray-700 dark:text-gray-300">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {organizations.map((org) => (
                    <TableRow key={org.id} className="border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/30">
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <Building2 className="h-5 w-5 text-muted-foreground" />
                        <div>
                          <div className="font-medium">{org.name}</div>
                          <div className="text-sm text-muted-foreground">
                            {org.slug}
                          </div>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant={getLicenseBadgeVariant(org.license_type)}>
                        {org.license_type}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-4 text-sm">
                        <div className="flex items-center gap-1">
                          <Users className="h-4 w-4 text-muted-foreground" />
                          <span>{org.max_users} users</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <FlaskConical className="h-4 w-4 text-muted-foreground" />
                          <span>{org.max_studies} studies</span>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant={org.active ? 'default' : 'secondary'}>
                        {org.active ? 'Active' : 'Inactive'}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {format(new Date(org.created_at), 'MMM d, yyyy')}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => router.push(`/organizations/${org.id}`)}
                      >
                        <Settings className="h-4 w-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </motion.div>
      ) : (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.3 }}
        >
          <Card className="border-0 shadow-lg bg-white dark:bg-gray-800">
            <CardContent className="py-12">
              <div className="text-center">
                <Building2 className="h-12 w-12 mx-auto text-gray-400 dark:text-gray-500 mb-4" />
                <h3 className="text-lg font-semibold mb-2 text-gray-900 dark:text-gray-100">No organizations yet</h3>
                <p className="text-gray-600 dark:text-gray-400 mb-4">
                  Create your first organization to get started
                </p>
                <Button 
                  onClick={() => router.push('/organizations/new')}
                  className="bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-700 hover:to-blue-700 text-white shadow-lg"
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Create Organization
                </Button>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}
      </div>
    </div>
  );
}