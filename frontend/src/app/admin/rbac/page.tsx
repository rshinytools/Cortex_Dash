// ABOUTME: RBAC management page for dynamic permission control
// ABOUTME: Allows admins to manage roles, permissions, and user assignments

'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import { AuthGuard } from '@/components/auth-guard';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { 
  Shield, 
  Lock, 
  Users, 
  Key,
  Plus,
  Settings,
  CheckCircle,
  XCircle,
  ArrowLeft,
  UserCheck,
  ShieldCheck
} from 'lucide-react';
import { RolePermissionsDialog } from '@/components/admin/rbac/role-permissions-dialog';
import { PermissionMatrix } from '@/components/admin/rbac/permission-matrix';
import { motion } from 'framer-motion';
import { ThemeToggle } from '@/components/ui/theme-toggle';
import { UserMenu } from '@/components/user-menu';
import { secureApiClient } from '@/lib/api/secure-client';

interface Permission {
  id: string;
  name: string;
  resource: string;
  action: string;
  description: string;
  is_system: boolean;
}

interface Role {
  id: string;
  name: string;
  display_name: string;
  description: string;
  is_system: boolean;
  is_active: boolean;
  permission_count: number;
}

function RBACContent() {
  const { user, isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedRole, setSelectedRole] = useState<Role | null>(null);
  const [permissionDialogOpen, setPermissionDialogOpen] = useState(false);

  const fetchData = async () => {
    try {
      const [rolesRes, permissionsRes] = await Promise.all([
        secureApiClient.get('/rbac/roles'),
        secureApiClient.get('/rbac/permissions')
      ]);
      
      setRoles(rolesRes.data);
      setPermissions(permissionsRes.data);
    } catch (error) {
      console.error('Failed to fetch RBAC data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, isLoading, router]);

  useEffect(() => {
    if (isAuthenticated) {
      fetchData();
    }
  }, [isAuthenticated]);

  const handleConfigureRole = (role: Role) => {
    setSelectedRole(role);
    setPermissionDialogOpen(true);
  };

  const handleDialogClose = () => {
    setSelectedRole(null);
    setPermissionDialogOpen(false);
  };

  const handlePermissionsUpdate = () => {
    fetchData(); // Refresh the data after updating permissions
  };

  if (isLoading || loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  // Calculate stats
  const activeRoles = roles.filter(r => r.is_active).length;
  const customRoles = roles.filter(r => !r.is_system).length;
  const customPermissions = permissions.filter(p => !p.is_system).length;

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
            <span className="text-foreground">RBAC</span>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 dark:from-indigo-400 dark:to-purple-400 bg-clip-text text-transparent">
                Role-Based Access Control
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mt-2">
                Manage roles, permissions, and access control for the platform
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
                  <p className="text-sm text-gray-600 dark:text-gray-400">Total Roles</p>
                  <p className="text-3xl font-bold text-gray-900 dark:text-gray-100 mt-1">
                    {roles.length}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                    {activeRoles} active
                  </p>
                </div>
                <div className="h-12 w-12 bg-indigo-100 dark:bg-indigo-900/20 rounded-lg flex items-center justify-center">
                  <Shield className="h-6 w-6 text-indigo-600 dark:text-indigo-400" />
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="border-0 shadow-lg bg-white dark:bg-gray-800 hover:shadow-xl transition-shadow">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Total Permissions</p>
                  <p className="text-3xl font-bold text-gray-900 dark:text-gray-100 mt-1">
                    {permissions.length}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                    Across all resources
                  </p>
                </div>
                <div className="h-12 w-12 bg-purple-100 dark:bg-purple-900/20 rounded-lg flex items-center justify-center">
                  <Key className="h-6 w-6 text-purple-600 dark:text-purple-400" />
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="border-0 shadow-lg bg-white dark:bg-gray-800 hover:shadow-xl transition-shadow">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">System Roles</p>
                  <p className="text-3xl font-bold text-gray-900 dark:text-gray-100 mt-1">
                    {roles.filter(r => r.is_system).length}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                    Built-in roles
                  </p>
                </div>
                <div className="h-12 w-12 bg-blue-100 dark:bg-blue-900/20 rounded-lg flex items-center justify-center">
                  <ShieldCheck className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-lg bg-white dark:bg-gray-800 hover:shadow-xl transition-shadow">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Custom Config</p>
                  <p className="text-3xl font-bold text-gray-900 dark:text-gray-100 mt-1">
                    {customRoles + customPermissions}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                    User-defined
                  </p>
                </div>
                <div className="h-12 w-12 bg-green-100 dark:bg-green-900/20 rounded-lg flex items-center justify-center">
                  <UserCheck className="h-6 w-6 text-green-600 dark:text-green-400" />
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
          <Tabs defaultValue="roles" className="space-y-4">
            <TabsList className="bg-white dark:bg-gray-800 border-0 shadow-lg p-1">
              <TabsTrigger value="roles" className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-indigo-500 data-[state=active]:to-purple-500 data-[state=active]:text-white">
                Roles
              </TabsTrigger>
              <TabsTrigger value="permissions" className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-indigo-500 data-[state=active]:to-purple-500 data-[state=active]:text-white">
                Permissions
              </TabsTrigger>
              <TabsTrigger value="matrix" className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-indigo-500 data-[state=active]:to-purple-500 data-[state=active]:text-white">
                Permission Matrix
              </TabsTrigger>
            </TabsList>

            <TabsContent value="roles" className="space-y-4">
              <Card className="border-0 shadow-lg bg-white dark:bg-gray-800">
                <CardHeader className="bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-700 rounded-t-lg">
                  <CardTitle className="text-xl text-gray-900 dark:text-gray-100">System Roles</CardTitle>
                  <CardDescription className="text-gray-600 dark:text-gray-400">
                    Manage roles and their associated permissions
                  </CardDescription>
                </CardHeader>
                <CardContent className="p-0">
                  <Table>
                    <TableHeader>
                      <TableRow className="border-b border-gray-200 dark:border-gray-700">
                        <TableHead className="text-gray-700 dark:text-gray-300 font-semibold">Role Name</TableHead>
                        <TableHead className="text-gray-700 dark:text-gray-300 font-semibold">Display Name</TableHead>
                        <TableHead className="text-gray-700 dark:text-gray-300 font-semibold">Permissions</TableHead>
                        <TableHead className="text-gray-700 dark:text-gray-300 font-semibold">Type</TableHead>
                        <TableHead className="text-gray-700 dark:text-gray-300 font-semibold">Status</TableHead>
                        <TableHead className="text-gray-700 dark:text-gray-300 font-semibold">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {roles.map((role, index) => (
                        <motion.tr
                          key={role.id}
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ duration: 0.3, delay: index * 0.05 }}
                          className="border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                        >
                          <TableCell className="font-medium text-gray-900 dark:text-gray-100 py-4">
                            {role.name}
                          </TableCell>
                          <TableCell className="text-gray-700 dark:text-gray-300">
                            {role.display_name}
                          </TableCell>
                          <TableCell>
                            <Badge className="bg-indigo-100 text-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-400">
                              {role.permission_count} permissions
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <Badge 
                              variant={role.is_system ? "secondary" : "default"}
                              className={role.is_system ? "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300" : ""}
                            >
                              {role.is_system ? "System" : "Custom"}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            {role.is_active ? (
                              <div className="flex items-center gap-2">
                                <CheckCircle className="h-4 w-4 text-green-600 dark:text-green-400" />
                                <span className="text-sm text-green-600 dark:text-green-400">Active</span>
                              </div>
                            ) : (
                              <div className="flex items-center gap-2">
                                <XCircle className="h-4 w-4 text-red-600 dark:text-red-400" />
                                <span className="text-sm text-red-600 dark:text-red-400">Inactive</span>
                              </div>
                            )}
                          </TableCell>
                          <TableCell>
                            <Button 
                              variant="outline" 
                              size="sm"
                              onClick={() => handleConfigureRole(role)}
                              className="border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300"
                            >
                              <Settings className="h-4 w-4 mr-2" />
                              Configure
                            </Button>
                          </TableCell>
                        </motion.tr>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

            <TabsContent value="permissions" className="space-y-4">
              <Card className="border-0 shadow-lg bg-white dark:bg-gray-800">
                <CardHeader className="bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-700 rounded-t-lg">
                  <CardTitle className="text-xl text-gray-900 dark:text-gray-100">System Permissions</CardTitle>
                  <CardDescription className="text-gray-600 dark:text-gray-400">
                    All available permissions in the system
                  </CardDescription>
                </CardHeader>
                <CardContent className="p-0">
                  <Table>
                    <TableHeader>
                      <TableRow className="border-b border-gray-200 dark:border-gray-700">
                        <TableHead className="text-gray-700 dark:text-gray-300 font-semibold">Permission Name</TableHead>
                        <TableHead className="text-gray-700 dark:text-gray-300 font-semibold">Resource</TableHead>
                        <TableHead className="text-gray-700 dark:text-gray-300 font-semibold">Action</TableHead>
                        <TableHead className="text-gray-700 dark:text-gray-300 font-semibold">Description</TableHead>
                        <TableHead className="text-gray-700 dark:text-gray-300 font-semibold">Type</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {permissions.map((permission, index) => (
                        <motion.tr
                          key={permission.id}
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ duration: 0.3, delay: index * 0.02 }}
                          className="border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                        >
                          <TableCell className="font-medium text-gray-900 dark:text-gray-100 py-3">
                            {permission.name}
                          </TableCell>
                          <TableCell className="text-gray-700 dark:text-gray-300">
                            <Badge variant="outline" className="font-normal">
                              {permission.resource}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <Badge className="bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400">
                              {permission.action}
                            </Badge>
                          </TableCell>
                          <TableCell className="max-w-xs truncate text-gray-600 dark:text-gray-400">
                            {permission.description || '-'}
                          </TableCell>
                          <TableCell>
                            <Badge 
                              variant={permission.is_system ? "secondary" : "default"}
                              className={permission.is_system ? "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300" : ""}
                            >
                              {permission.is_system ? "System" : "Custom"}
                            </Badge>
                          </TableCell>
                        </motion.tr>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="matrix" className="space-y-4">
              <PermissionMatrix />
            </TabsContent>
          </Tabs>
        </motion.div>

        <RolePermissionsDialog
          role={selectedRole}
          isOpen={permissionDialogOpen}
          onClose={handleDialogClose}
          onUpdate={handlePermissionsUpdate}
        />
      </div>
    </div>
  );
}

export default function RBACPage() {
  // AuthGuard is already applied in admin/layout.tsx
  return <RBACContent />;
}