// ABOUTME: User profile page - shows current user information
// ABOUTME: Allows users to view and edit their profile details

'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/lib/auth-context';
import { useRouter } from 'next/navigation';
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { useToast } from '@/hooks/use-toast';
import { 
  User,
  Mail,
  Shield,
  Building2,
  Calendar,
  Edit2,
  Save,
  X,
  ArrowLeft,
  Lock,
  Eye,
  EyeOff
} from 'lucide-react';
import { secureApiClient } from '@/lib/api/secure-client';
import { format } from 'date-fns';
import { UserRole } from '@/types';

interface ProfileUpdateData {
  full_name?: string;
  email?: string;
}

interface PasswordChangeData {
  current_password: string;
  new_password: string;
  confirm_password: string;
}

export default function ProfilePage() {
  const { user, updateUser, isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState<ProfileUpdateData>({
    full_name: '',
    email: '',
  });
  const [showPasswordDialog, setShowPasswordDialog] = useState(false);
  const [passwordData, setPasswordData] = useState<PasswordChangeData>({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [passwordErrors, setPasswordErrors] = useState<string[]>([]);

  // Fetch current user data from the server
  const { data: currentUser, refetch: refetchUser } = useQuery({
    queryKey: ['currentUser'],
    queryFn: async () => {
      const response = await secureApiClient.get('/users/me');
      return response.data;
    },
    enabled: !!user,
  });

  // Update form data when user data loads
  useEffect(() => {
    if (currentUser) {
      setFormData({
        full_name: currentUser.full_name || '',
        email: currentUser.email || '',
      });
    }
  }, [currentUser]);

  const changePassword = useMutation({
    mutationFn: async (data: { current_password: string; new_password: string }) => {
      const response = await secureApiClient.patch('/users/me/password', data);
      return response.data;
    },
    onSuccess: () => {
      toast({
        title: 'Password changed',
        description: 'Your password has been changed successfully.',
      });
      setShowPasswordDialog(false);
      // Reset password form
      setPasswordData({
        current_password: '',
        new_password: '',
        confirm_password: '',
      });
      setPasswordErrors([]);
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.detail || 'Failed to change password';
      toast({
        title: 'Password change failed',
        description: errorMessage,
        variant: 'destructive',
      });
    },
  });

  const validatePassword = (password: string): string[] => {
    const errors: string[] = [];
    if (password.length < 8) {
      errors.push('Password must be at least 8 characters');
    }
    if (password.length > 40) {
      errors.push('Password must be less than 40 characters');
    }
    if (!/[a-z]/.test(password)) {
      errors.push('Password must contain at least one lowercase letter');
    }
    if (!/[A-Z]/.test(password)) {
      errors.push('Password must contain at least one uppercase letter');
    }
    if (!/[0-9]/.test(password)) {
      errors.push('Password must contain at least one number');
    }
    return errors;
  };

  const handlePasswordSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate passwords
    const errors = validatePassword(passwordData.new_password);
    if (errors.length > 0) {
      setPasswordErrors(errors);
      return;
    }
    
    if (passwordData.new_password !== passwordData.confirm_password) {
      setPasswordErrors(['Passwords do not match']);
      return;
    }
    
    if (passwordData.current_password === passwordData.new_password) {
      setPasswordErrors(['New password must be different from current password']);
      return;
    }
    
    setPasswordErrors([]);
    changePassword.mutate({
      current_password: passwordData.current_password,
      new_password: passwordData.new_password,
    });
  };

  const updateProfile = useMutation({
    mutationFn: async (data: ProfileUpdateData) => {
      const response = await secureApiClient.patch('/users/me', data);
      return response.data;
    },
    onSuccess: async (updatedUser) => {
      // Refetch user data from server to ensure we have the latest
      await refetchUser();
      
      // Update the auth context with new user data
      updateUser(updatedUser);
      
      // Invalidate queries that might depend on user data
      queryClient.invalidateQueries({ queryKey: ['currentUser'] });
      
      toast({
        title: 'Profile updated',
        description: 'Your profile has been updated successfully.',
      });
      setIsEditing(false);
    },
    onError: (error) => {
      toast({
        title: 'Update failed',
        description: error instanceof Error ? error.message : 'Failed to update profile',
        variant: 'destructive',
      });
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateProfile.mutate(formData);
  };

  const handleCancel = () => {
    // Reset form data from the server data, not session
    setFormData({
      full_name: currentUser?.full_name || '',
      email: currentUser?.email || '',
    });
    setIsEditing(false);
  };

  // Determine where to go back based on user role
  const getBackPath = () => {
    if (!user) return '/dashboard';
    
    const role = user.role as UserRole;
    if (role === UserRole.SYSTEM_ADMIN || role === UserRole.ORG_ADMIN) {
      return '/admin';
    }
    return '/dashboard';
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-200px)]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    router.push('/');
    return null;
  }

  const getRoleBadgeVariant = (role: string) => {
    switch (role) {
      case 'system_admin':
        return 'destructive';
      case 'org_admin':
        return 'default';
      default:
        return 'secondary';
    }
  };

  // Use currentUser data if available, otherwise fall back to user data
  const userData = currentUser || user;

  return (
    <div className="container mx-auto py-6 max-w-4xl">
      {/* Breadcrumb Navigation */}
      <div className="flex items-center gap-2 text-sm text-muted-foreground mb-4">
        <Button
          variant="link"
          className="p-0 h-auto font-normal"
          onClick={() => router.push('/dashboard')}
        >
          Dashboard
        </Button>
        <span>/</span>
        {(user?.role === UserRole.SYSTEM_ADMIN || user?.role === UserRole.ORG_ADMIN) && (
          <>
            <Button
              variant="link"
              className="p-0 h-auto font-normal"
              onClick={() => router.push('/admin')}
            >
              Admin
            </Button>
            <span>/</span>
          </>
        )}
        <span className="text-foreground">Profile</span>
      </div>

      <div className="mb-6">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => router.push(getBackPath())}
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Button>
          <div>
            <h1 className="text-3xl font-bold">My Profile</h1>
            <p className="text-muted-foreground mt-1">
              Manage your personal information and account settings
            </p>
          </div>
        </div>
      </div>

      <div className="grid gap-6">
        {/* Profile Information */}
        <Card>
          <CardHeader>
            <div className="flex justify-between items-center">
              <div>
                <CardTitle>Profile Information</CardTitle>
                <CardDescription>
                  Your personal details and account information
                </CardDescription>
              </div>
              {!isEditing && (
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => setIsEditing(true)}
                >
                  <Edit2 className="h-4 w-4 mr-2" />
                  Edit
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {isEditing ? (
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <Label htmlFor="full_name">Full Name</Label>
                  <Input
                    id="full_name"
                    value={formData.full_name}
                    onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                    placeholder="Enter your full name"
                  />
                </div>
                <div>
                  <Label htmlFor="email">Email Address</Label>
                  <Input
                    id="email"
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    placeholder="Enter your email"
                  />
                </div>
                <div className="flex gap-2">
                  <Button type="submit" disabled={updateProfile.isPending}>
                    <Save className="h-4 w-4 mr-2" />
                    {updateProfile.isPending ? 'Saving...' : 'Save Changes'}
                  </Button>
                  <Button 
                    type="button" 
                    variant="outline"
                    onClick={handleCancel}
                    disabled={updateProfile.isPending}
                  >
                    <X className="h-4 w-4 mr-2" />
                    Cancel
                  </Button>
                </div>
              </form>
            ) : (
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <User className="h-5 w-5 text-muted-foreground" />
                  <div>
                    <p className="text-sm text-muted-foreground">Full Name</p>
                    <p className="font-medium">{userData?.full_name || 'Not set'}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <Mail className="h-5 w-5 text-muted-foreground" />
                  <div>
                    <p className="text-sm text-muted-foreground">Email Address</p>
                    <p className="font-medium">{userData?.email}</p>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Account Details */}
        <Card>
          <CardHeader>
            <CardTitle>Account Details</CardTitle>
            <CardDescription>
              Your role and organization information
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-3">
              <Shield className="h-5 w-5 text-muted-foreground" />
              <div>
                <p className="text-sm text-muted-foreground">Role</p>
                <Badge variant={getRoleBadgeVariant(userData?.role || '')}>
                  {(userData?.role || '').replace('_', ' ')}
                </Badge>
              </div>
            </div>
            {userData?.org_id && (
              <div className="flex items-center gap-3">
                <Building2 className="h-5 w-5 text-muted-foreground" />
                <div>
                  <p className="text-sm text-muted-foreground">Organization</p>
                  <p className="font-medium">
                    {userData?.organization?.name || userData?.org_id}
                  </p>
                </div>
              </div>
            )}
            <div className="flex items-center gap-3">
              <Calendar className="h-5 w-5 text-muted-foreground" />
              <div>
                <p className="text-sm text-muted-foreground">Member Since</p>
                <p className="font-medium">
                  {userData?.created_at 
                    ? format(new Date(userData.created_at), 'MMMM d, yyyy')
                    : 'Unknown'
                  }
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Security Settings */}
        <Card>
          <CardHeader>
            <CardTitle>Security Settings</CardTitle>
            <CardDescription>
              Manage your password and security preferences
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button 
              variant="outline"
              onClick={() => setShowPasswordDialog(true)}
            >
              <Lock className="h-4 w-4 mr-2" />
              Change Password
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Change Password Dialog */}
      <Dialog open={showPasswordDialog} onOpenChange={setShowPasswordDialog}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Change Password</DialogTitle>
            <DialogDescription>
              Enter your current password and choose a new password.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handlePasswordSubmit}>
            <div className="grid gap-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="current_password">Current Password</Label>
                <div className="relative">
                  <Input
                    id="current_password"
                    type={showCurrentPassword ? 'text' : 'password'}
                    value={passwordData.current_password}
                    onChange={(e) => setPasswordData({ ...passwordData, current_password: e.target.value })}
                    placeholder="Enter current password"
                    required
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                    onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                  >
                    {showCurrentPassword ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="new_password">New Password</Label>
                <div className="relative">
                  <Input
                    id="new_password"
                    type={showNewPassword ? 'text' : 'password'}
                    value={passwordData.new_password}
                    onChange={(e) => {
                      setPasswordData({ ...passwordData, new_password: e.target.value });
                      if (passwordErrors.length > 0) {
                        setPasswordErrors(validatePassword(e.target.value));
                      }
                    }}
                    placeholder="Enter new password"
                    required
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                    onClick={() => setShowNewPassword(!showNewPassword)}
                  >
                    {showNewPassword ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="confirm_password">Confirm New Password</Label>
                <div className="relative">
                  <Input
                    id="confirm_password"
                    type={showConfirmPassword ? 'text' : 'password'}
                    value={passwordData.confirm_password}
                    onChange={(e) => setPasswordData({ ...passwordData, confirm_password: e.target.value })}
                    placeholder="Confirm new password"
                    required
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  >
                    {showConfirmPassword ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              </div>
              {passwordErrors.length > 0 && (
                <div className="rounded-md bg-destructive/15 p-3">
                  <ul className="list-disc list-inside text-sm text-destructive">
                    {passwordErrors.map((error, index) => (
                      <li key={index}>{error}</li>
                    ))}
                  </ul>
                </div>
              )}
              <div className="text-xs text-muted-foreground">
                Password must be 8-40 characters and contain uppercase, lowercase, and numbers.
              </div>
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setShowPasswordDialog(false);
                  setPasswordData({
                    current_password: '',
                    new_password: '',
                    confirm_password: '',
                  });
                  setPasswordErrors([]);
                }}
                disabled={changePassword.isPending}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={changePassword.isPending}>
                {changePassword.isPending ? 'Changing...' : 'Change Password'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}