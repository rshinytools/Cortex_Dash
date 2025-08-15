// ABOUTME: Create new organization page - system admin only
// ABOUTME: Form to create a new organization with all required fields

'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft, Building2, Users, Shield, Settings, Info, Plus, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { motion } from 'framer-motion';
import { ThemeToggle } from '@/components/ui/theme-toggle';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { organizationsApi, OrganizationCreate } from '@/lib/api/organizations';
import { useAuth } from '@/lib/auth-context';
import { UserRole } from '@/types';
import { UserMenu } from '@/components/user-menu';

export default function NewOrganizationPage() {
  const router = useRouter();
  const { toast } = useToast();
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState<Partial<OrganizationCreate>>({
    features: {},
  });
  const [licenseType, setLicenseType] = useState<string>('trial');

  const createOrganization = useMutation({
    mutationFn: organizationsApi.createOrganization,
    onSuccess: () => {
      toast({
        title: 'Organization created successfully',
        description: 'The new organization has been created.',
      });
      // Invalidate the organizations query to refresh the list
      queryClient.invalidateQueries({ queryKey: ['organizations'] });
      router.push('/organizations');
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.detail || error.message || 'An error occurred';
      toast({
        title: 'Failed to create organization',
        description: errorMessage,
        variant: 'destructive',
      });
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.name || !formData.slug) {
      toast({
        title: 'Missing required fields',
        description: 'Please fill in all required fields',
        variant: 'destructive',
      });
      return;
    }

    createOrganization.mutate(formData as OrganizationCreate);
  };

  const generateSlug = (name: string) => {
    return name
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '');
  };

  // Check if user is system admin - after all hooks
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
                onClick={() => router.push('/organizations')}
              >
                Organizations
              </Button>
              <span>/</span>
              <span className="text-foreground">New</span>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-4xl font-bold bg-gradient-to-r from-indigo-600 to-blue-600 dark:from-indigo-400 dark:to-blue-400 bg-clip-text text-transparent flex items-center gap-3">
                  <Building2 className="h-8 w-8 text-indigo-600 dark:text-indigo-400" />
                  Create Organization
                </h1>
                <p className="text-gray-600 dark:text-gray-400 mt-2">
                  Set up a new organization for clinical trials
                </p>
              </div>
              <div className="flex items-center gap-3">
                <ThemeToggle />
                <UserMenu />
              </div>
            </div>
          </motion.div>

          {/* Information Alert */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.1 }}
            className="mb-6"
          >
            <Alert className="border-blue-200 bg-blue-50 dark:border-blue-800 dark:bg-blue-900/20">
              <Info className="h-4 w-4 text-blue-600 dark:text-blue-400" />
              <AlertDescription className="text-blue-800 dark:text-blue-200">
                Organizations are the top-level entities in the system. Each organization can have multiple studies, users, and custom configurations.
              </AlertDescription>
            </Alert>
          </motion.div>

          <motion.form 
            onSubmit={handleSubmit}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.2 }}
          >
            <Card className="border-0 shadow-lg bg-white dark:bg-gray-800">
              <CardHeader className="bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-700 rounded-t-lg">
                <CardTitle className="text-xl text-gray-900 dark:text-gray-100">Organization Details</CardTitle>
                <CardDescription className="text-gray-600 dark:text-gray-400">
                  Basic information about the organization
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6 p-6">
              <div>
                <Label htmlFor="name" className="text-gray-700 dark:text-gray-300">Organization Name *</Label>
                <Input
                  id="name"
                  placeholder="e.g., Pharma Corp International"
                  value={formData.name || ''}
                  onChange={(e) => {
                    const name = e.target.value;
                    setFormData({
                      ...formData,
                      name,
                      slug: generateSlug(name),
                    });
                  }}
                  required
                  className="mt-1 bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600"
                />
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  The full name of the organization
                </p>
              </div>

              <div>
                <Label htmlFor="slug" className="text-gray-700 dark:text-gray-300">URL Slug *</Label>
                <Input
                  id="slug"
                  placeholder="e.g., pharma-corp"
                  value={formData.slug || ''}
                  onChange={(e) => setFormData({ ...formData, slug: e.target.value })}
                  pattern="[a-z0-9-]+"
                  required
                  className="mt-1 bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600"
                />
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  Unique identifier used in URLs (lowercase letters, numbers, and hyphens only)
                </p>
              </div>

              <div>
                <Label htmlFor="license" className="text-gray-700 dark:text-gray-300">License Type</Label>
                <Select
                  defaultValue="trial"
                  onValueChange={(value) => {
                    setLicenseType(value);
                    // This would be handled by the backend based on license type
                    const licenseDefaults = {
                      trial: { max_users: 10, max_studies: 5 },
                      basic: { max_users: 25, max_studies: 10 },
                      professional: { max_users: 100, max_studies: 50 },
                      enterprise: { max_users: -1, max_studies: -1 },
                    };
                  }}
                >
                  <SelectTrigger id="license" className="mt-1 bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700">
                    <SelectItem value="trial">Trial (10 users, 5 studies)</SelectItem>
                    <SelectItem value="basic">Basic (25 users, 10 studies)</SelectItem>
                    <SelectItem value="professional">Professional (100 users, 50 studies)</SelectItem>
                    <SelectItem value="enterprise">Enterprise (Unlimited)</SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  Determines user and study limits
                </p>
              </div>

              <div className="bg-gradient-to-r from-indigo-50 to-blue-50 dark:from-indigo-900/20 dark:to-blue-900/20 p-4 rounded-lg border border-indigo-200 dark:border-indigo-800">
                <div className="flex items-center gap-2 mb-2">
                  <Shield className="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
                  <span className="font-medium text-gray-900 dark:text-gray-100">Default Features</span>
                </div>
                <p className="text-sm text-gray-700 dark:text-gray-300">
                  All organizations start with standard features enabled. Additional features
                  can be configured after creation.
                </p>
                <div className="mt-3 grid grid-cols-2 gap-2">
                  <div className="flex items-center gap-2">
                    <div className="h-2 w-2 bg-green-500 rounded-full"></div>
                    <span className="text-xs text-gray-600 dark:text-gray-400">Dashboard Access</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="h-2 w-2 bg-green-500 rounded-full"></div>
                    <span className="text-xs text-gray-600 dark:text-gray-400">Data Upload</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="h-2 w-2 bg-green-500 rounded-full"></div>
                    <span className="text-xs text-gray-600 dark:text-gray-400">User Management</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="h-2 w-2 bg-green-500 rounded-full"></div>
                    <span className="text-xs text-gray-600 dark:text-gray-400">Study Creation</span>
                  </div>
                </div>
              </div>
              </CardContent>
            </Card>

            <div className="flex justify-between mt-6">
              <Button
                type="button"
                variant="outline"
                onClick={() => router.push('/organizations')}
                className="border-gray-300 dark:border-gray-600"
              >
                Cancel
              </Button>
              <Button 
                type="submit" 
                disabled={createOrganization.isPending}
                className="bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-700 hover:to-blue-700 text-white shadow-lg"
              >
                {createOrganization.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Creating...
                  </>
                ) : (
                  <>
                    <Plus className="h-4 w-4 mr-2" />
                    Create Organization
                  </>
                )}
              </Button>
            </div>
          </motion.form>
        </div>
      </div>
    </div>
  );
}