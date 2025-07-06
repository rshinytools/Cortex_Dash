// ABOUTME: Edit user page - allows admins to update user information
// ABOUTME: System admins can edit all users, org admins can only edit users in their org

'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useSession } from 'next-auth/react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ArrowLeft, Save, User } from 'lucide-react';
import { UserRole } from '@/types';
import { apiClient } from '@/lib/api/client';
import { useToast } from '@/hooks/use-toast';

interface UserUpdateData {
  full_name?: string;
  email?: string;
  role?: string;
  department?: string;
  is_active?: boolean;
}

export default function EditUserPage() {
  const router = useRouter();
  const params = useParams();
  const { data: session } = useSession();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const userId = params.id as string;

  const [formData, setFormData] = useState<UserUpdateData>({});

  // Check permissions
  const canAccessPage = session?.user?.role && 
    [UserRole.SYSTEM_ADMIN, UserRole.ORG_ADMIN].includes(session.user.role as UserRole);

  // Fetch user data
  const { data: user, isLoading } = useQuery({
    queryKey: ['user', userId],
    queryFn: async () => {
      const response = await apiClient.get(`/users/${userId}`);
      return response.data;
    },
    enabled: !!userId && canAccessPage,
  });

  // Update form when user data is loaded
  useEffect(() => {
    if (user) {
      setFormData({
        full_name: user.full_name || '',
        email: user.email || '',
        role: user.role || '',
        department: user.department || '',
        is_active: user.is_active !== undefined ? user.is_active : true,
      });
    }
  }, [user]);

  // Update user mutation
  const updateUser = useMutation({
    mutationFn: async (data: UserUpdateData) => {
      const response = await apiClient.patch(`/users/${userId}`, data);
      return response.data;
    },
    onSuccess: () => {
      toast({
        title: 'User updated',
        description: 'User information has been updated successfully.',
      });
      queryClient.invalidateQueries({ queryKey: ['users'] });
      queryClient.invalidateQueries({ queryKey: ['user', userId] });
      router.push('/admin/users');
    },
    onError: (error) => {
      toast({
        title: 'Update failed',
        description: error instanceof Error ? error.message : 'Failed to update user',
        variant: 'destructive',
      });
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateUser.mutate(formData);
  };

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

  if (isLoading) {
    return (
      <div className="container mx-auto py-6">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="container mx-auto py-6">
        <Card>
          <CardContent className="py-6">
            <p className="text-center text-muted-foreground">
              User not found.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Check if org admin can edit this user
  if (session?.user?.role === UserRole.ORG_ADMIN && user.org_id !== session.user.org_id) {
    return (
      <div className="container mx-auto py-6">
        <Card>
          <CardContent className="py-6">
            <p className="text-center text-muted-foreground">
              You can only edit users in your organization.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const availableRoles = session?.user?.role === UserRole.SYSTEM_ADMIN
    ? [
        UserRole.SYSTEM_ADMIN,
        UserRole.ORG_ADMIN,
        UserRole.STUDY_MANAGER,
        UserRole.DATA_ANALYST,
        UserRole.VIEWER,
      ]
    : [
        UserRole.STUDY_MANAGER,
        UserRole.DATA_ANALYST,
        UserRole.VIEWER,
      ];

  return (
    <div className="container mx-auto py-6">
      <div className="max-w-2xl mx-auto">
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
          <span className="text-foreground">Edit</span>
        </div>

        <div className="flex items-center mb-6">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => router.push('/admin/users')}
            className="mr-4"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Users
          </Button>
          <div>
            <h1 className="text-3xl font-bold">Edit User</h1>
            <p className="text-muted-foreground mt-1">
              Update user information and permissions
            </p>
          </div>
        </div>

        <form onSubmit={handleSubmit}>
          <Card>
            <CardHeader>
              <CardTitle>User Information</CardTitle>
              <CardDescription>
                Update the user's details and role
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <Label htmlFor="full_name">Full Name</Label>
                <Input
                  id="full_name"
                  value={formData.full_name || ''}
                  onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                  placeholder="Enter full name"
                />
              </div>

              <div>
                <Label htmlFor="email">Email Address</Label>
                <Input
                  id="email"
                  type="email"
                  value={formData.email || ''}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  placeholder="user@example.com"
                />
              </div>

              <div>
                <Label htmlFor="department">Department</Label>
                <Input
                  id="department"
                  value={formData.department || ''}
                  onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                  placeholder="e.g., Clinical Research"
                />
              </div>

              <div>
                <Label htmlFor="role">Role</Label>
                <Select
                  value={formData.role}
                  onValueChange={(value) => setFormData({ ...formData, role: value })}
                >
                  <SelectTrigger id="role">
                    <SelectValue placeholder="Select a role" />
                  </SelectTrigger>
                  <SelectContent>
                    {availableRoles.map((role) => (
                      <SelectItem key={role} value={role}>
                        {role.replace('_', ' ')}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="is_active"
                  checked={formData.is_active}
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  className="rounded border-gray-300"
                />
                <Label htmlFor="is_active" className="font-normal cursor-pointer">
                  User is active
                </Label>
              </div>

              {user.id === session?.user?.id && (
                <div className="bg-yellow-50 dark:bg-yellow-900/20 p-4 rounded-lg">
                  <p className="text-sm text-yellow-800 dark:text-yellow-200">
                    You are editing your own account. Some changes may require you to log in again.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          <div className="flex justify-between mt-6">
            <Button
              type="button"
              variant="outline"
              onClick={() => router.push('/admin/users')}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={updateUser.isPending}>
              <Save className="h-4 w-4 mr-2" />
              {updateUser.isPending ? 'Saving...' : 'Save Changes'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}