// ABOUTME: Create new user page - allows admins to add users
// ABOUTME: System admins can create users for any org, org admins only for their org

'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useSession } from 'next-auth/react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';
import { UserRole } from '@/types';
import { apiClient } from '@/lib/api/client';
import { organizationsApi } from '@/lib/api/organizations';
import { UserMenu } from '@/components/user-menu';

interface UserCreateData {
  email: string;
  full_name: string;
  password: string;
  role: string;
  org_id: string;
}

export default function NewUserPage() {
  const router = useRouter();
  const { data: session } = useSession();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState<Partial<UserCreateData>>({
    role: UserRole.VIEWER,
  });

  // Check permissions
  const canAccessPage = session?.user?.role && 
    [UserRole.SYSTEM_ADMIN, UserRole.ORG_ADMIN].includes(session.user.role as UserRole);

  // Fetch organizations for system admins
  const { data: organizations } = useQuery({
    queryKey: ['organizations'],
    queryFn: organizationsApi.getOrganizations,
    enabled: session?.user?.role === UserRole.SYSTEM_ADMIN,
  });

  // Set org_id for org admins
  useEffect(() => {
    if (session?.user?.role === UserRole.ORG_ADMIN && session.user.org_id) {
      setFormData(prev => ({ ...prev, org_id: session.user.org_id }));
    }
  }, [session]);

  const createUser = useMutation({
    mutationFn: async (data: UserCreateData) => {
      const response = await apiClient.post('/users/', data);
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

    const orgId = session?.user?.role === UserRole.SYSTEM_ADMIN 
      ? formData.org_id 
      : session?.user?.org_id;

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
  const availableRoles = session?.user?.role === UserRole.SYSTEM_ADMIN
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
    <div className="container mx-auto py-6">
      <div className="max-w-2xl mx-auto">
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
          <div className="flex-1">
            <h1 className="text-3xl font-bold">Add New User</h1>
            <p className="text-muted-foreground mt-1">
              Create a new user account
            </p>
          </div>
          <UserMenu />
        </div>

        <form onSubmit={handleSubmit}>
          <Card>
            <CardHeader>
              <CardTitle>User Information</CardTitle>
              <CardDescription>
                Enter the details for the new user
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Organization selector for system admins */}
              {session?.user?.role === UserRole.SYSTEM_ADMIN && (
                <div>
                  <Label htmlFor="organization">Organization *</Label>
                  <Select
                    value={formData.org_id}
                    onValueChange={(value) => setFormData({ ...formData, org_id: value })}
                  >
                    <SelectTrigger id="organization">
                      <SelectValue placeholder="Select organization" />
                    </SelectTrigger>
                    <SelectContent>
                      {organizations && organizations.length > 0 ? (
                        organizations.map((org) => (
                          <SelectItem key={org.id} value={org.id}>
                            {org.name}
                          </SelectItem>
                        ))
                      ) : (
                        <div className="p-2 text-center text-muted-foreground">
                          No organizations found
                        </div>
                      )}
                    </SelectContent>
                  </Select>
                </div>
              )}

              <div>
                <Label htmlFor="email">Email Address *</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="user@example.com"
                  value={formData.email || ''}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  required
                />
              </div>

              <div>
                <Label htmlFor="full_name">Full Name *</Label>
                <Input
                  id="full_name"
                  placeholder="John Doe"
                  value={formData.full_name || ''}
                  onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                  required
                />
              </div>

              <div>
                <Label htmlFor="password">Temporary Password *</Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="Enter a temporary password"
                  value={formData.password || ''}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  required
                />
                <p className="text-sm text-muted-foreground mt-1">
                  User will be required to change this on first login
                </p>
              </div>

              <div>
                <Label htmlFor="role">Role *</Label>
                <Select
                  value={formData.role}
                  onValueChange={(value) => setFormData({ ...formData, role: value })}
                >
                  <SelectTrigger id="role">
                    <SelectValue placeholder="Select role" />
                  </SelectTrigger>
                  <SelectContent>
                    {availableRoles.map((role) => (
                      <SelectItem key={role} value={role}>
                        {role.replace('_', ' ')}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-sm text-muted-foreground mt-1">
                  Determines what the user can access and modify
                </p>
              </div>
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
            <Button type="submit" disabled={createUser.isPending}>
              {createUser.isPending ? 'Creating...' : 'Create User'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}