// ABOUTME: Create new user page - allows admins to add users
// ABOUTME: System admins can create users for any org, org admins only for their org

'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, UserPlus, Mail, Building2, Shield, Key, Info } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';
import { UserRole } from '@/types';
import { secureApiClient } from '@/lib/api/secure-client';
import { organizationsApi } from '@/lib/api/organizations';
import { UserMenu } from '@/components/user-menu';
import { ThemeToggle } from '@/components/ui/theme-toggle';
import { motion } from 'framer-motion';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface UserCreateData {
  email: string;
  full_name: string;
  password: string;
  role: string;
  org_id: string;
}

export default function NewUserPage() {
  const router = useRouter();
  const { user } = useAuth();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState<Partial<UserCreateData>>({
    role: UserRole.VIEWER,
  });

  // Check permissions
  const canAccessPage = user?.role && 
    [UserRole.SYSTEM_ADMIN, UserRole.ORG_ADMIN].includes(user.role as UserRole);

  // Fetch organizations for system admins
  const { data: organizations } = useQuery({
    queryKey: ['organizations'],
    queryFn: organizationsApi.getOrganizations,
    enabled: user?.role === UserRole.SYSTEM_ADMIN,
  });

  // Set org_id for org admins
  useEffect(() => {
    if (user?.role === UserRole.ORG_ADMIN && user.org_id) {
      setFormData(prev => ({ ...prev, org_id: user.org_id }));
    }
  }, [user]);

  const createUser = useMutation({
    mutationFn: async (data: UserCreateData) => {
      const response = await secureApiClient.post('/users/', data);
      return response.data;
    },
    onSuccess: () => {
      toast({
        title: 'User created successfully',
        description: 'The new user has been added to the system.',
      });
      queryClient.invalidateQueries({ queryKey: ['users'] });
      router.push('/admin/users');
    },
    onError: (error: any) => {
      toast({
        title: 'Failed to create user',
        description: error.response?.data?.detail || 'An error occurred',
        variant: 'destructive',
      });
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.email || !formData.full_name || !formData.password || !formData.role) {
      toast({
        title: 'Missing required fields',
        description: 'Please fill in all required fields',
        variant: 'destructive',
      });
      return;
    }

    const orgId = user?.role === UserRole.SYSTEM_ADMIN 
      ? formData.org_id 
      : user?.org_id;

    if (!orgId) {
      toast({
        title: 'No organization selected',
        description: 'Please select an organization for this user',
        variant: 'destructive',
      });
      return;
    }

    createUser.mutate({
      ...formData,
      org_id: orgId,
    } as UserCreateData);
  };

  // Available roles based on current user's role
  const availableRoles = user?.role === UserRole.SYSTEM_ADMIN
    ? Object.values(UserRole).filter(role => role !== UserRole.SYSTEM_ADMIN)
    : Object.values(UserRole).filter(role => 
        ![UserRole.SYSTEM_ADMIN, UserRole.ORG_ADMIN].includes(role)
      );

  // Check permissions after all hooks
  if (!canAccessPage) {
    router.push('/dashboard');
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="container mx-auto py-8 px-4">
        <div className="max-w-3xl mx-auto">
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
              <Button
                variant="link"
                className="p-0 h-auto font-normal"
                onClick={() => router.push('/admin/users')}
              >
                Users
              </Button>
              <span>/</span>
              <span className="text-foreground">New User</span>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 dark:from-blue-400 dark:to-purple-400 bg-clip-text text-transparent flex items-center gap-3">
                  <UserPlus className="h-8 w-8 text-blue-600 dark:text-blue-400" />
                  Add New User
                </h1>
                <p className="text-gray-600 dark:text-gray-400 mt-2">
                  Create a new user account and assign permissions
                </p>
              </div>
              <div className="flex items-center gap-3">
                <ThemeToggle />
                <UserMenu />
              </div>
            </div>
          </motion.div>

          <form onSubmit={handleSubmit}>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: 0.1 }}
            >
              <Card className="border-0 shadow-lg bg-white dark:bg-gray-800">
                <CardHeader className="bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-700 rounded-t-lg">
                  <CardTitle className="text-xl text-gray-900 dark:text-gray-100 flex items-center gap-2">
                    <Shield className="h-5 w-5" />
                    User Information
                  </CardTitle>
                  <CardDescription className="text-gray-600 dark:text-gray-400">
                    Enter the details for the new user account
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6 p-6">
                  {/* Organization selector for system admins */}
                  {user?.role === UserRole.SYSTEM_ADMIN && (
                    <div className="space-y-2">
                      <Label htmlFor="organization" className="text-gray-700 dark:text-gray-300 flex items-center gap-2">
                        <Building2 className="h-4 w-4" />
                        Organization *
                      </Label>
                      <Select
                        value={formData.org_id}
                        onValueChange={(value) => setFormData({ ...formData, org_id: value })}
                      >
                        <SelectTrigger 
                          id="organization"
                          className="bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600"
                        >
                          <SelectValue placeholder="Select organization" />
                        </SelectTrigger>
                        <SelectContent className="bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700">
                          {organizations && organizations.length > 0 ? (
                            organizations.map((org) => (
                              <SelectItem key={org.id} value={org.id}>
                                {org.name}
                              </SelectItem>
                            ))
                          ) : (
                            <div className="p-2 text-center text-gray-500 dark:text-gray-400">
                              No organizations found
                            </div>
                          )}
                        </SelectContent>
                      </Select>
                    </div>
                  )}

                  <div className="space-y-2">
                    <Label htmlFor="email" className="text-gray-700 dark:text-gray-300 flex items-center gap-2">
                      <Mail className="h-4 w-4" />
                      Email Address *
                    </Label>
                    <Input
                      id="email"
                      type="email"
                      placeholder="user@example.com"
                      value={formData.email || ''}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      className="bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600"
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="full_name" className="text-gray-700 dark:text-gray-300 flex items-center gap-2">
                      <UserPlus className="h-4 w-4" />
                      Full Name *
                    </Label>
                    <Input
                      id="full_name"
                      placeholder="John Doe"
                      value={formData.full_name || ''}
                      onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                      className="bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600"
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="password" className="text-gray-700 dark:text-gray-300 flex items-center gap-2">
                      <Key className="h-4 w-4" />
                      Temporary Password *
                    </Label>
                    <Input
                      id="password"
                      type="password"
                      placeholder="Enter a temporary password"
                      value={formData.password || ''}
                      onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                      className="bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600"
                      required
                    />
                    <Alert className="bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800">
                      <Info className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                      <AlertDescription className="text-blue-700 dark:text-blue-300">
                        User will be required to change this password on first login
                      </AlertDescription>
                    </Alert>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="role" className="text-gray-700 dark:text-gray-300 flex items-center gap-2">
                      <Shield className="h-4 w-4" />
                      Role *
                    </Label>
                    <Select
                      value={formData.role}
                      onValueChange={(value) => setFormData({ ...formData, role: value })}
                    >
                      <SelectTrigger 
                        id="role"
                        className="bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600"
                      >
                        <SelectValue placeholder="Select role" />
                      </SelectTrigger>
                      <SelectContent className="bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700">
                        {availableRoles.map((role) => (
                          <SelectItem key={role} value={role}>
                            {role.replace('_', ' ')}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Determines what the user can access and modify in the system
                    </p>
                  </div>
                </CardContent>
              </Card>
            </motion.div>

            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.3, delay: 0.2 }}
              className="flex justify-between mt-6"
            >
              <Button
                type="button"
                variant="outline"
                onClick={() => router.push('/admin/users')}
                className="border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                Cancel
              </Button>
              <Button 
                type="submit" 
                disabled={createUser.isPending}
                className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white shadow-lg"
              >
                {createUser.isPending ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                    Creating...
                  </>
                ) : (
                  <>
                    <UserPlus className="h-4 w-4 mr-2" />
                    Create User
                  </>
                )}
              </Button>
            </motion.div>
          </form>
        </div>
      </div>
    </div>
  );
}