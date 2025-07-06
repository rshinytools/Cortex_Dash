// ABOUTME: Create new organization page - system admin only
// ABOUTME: Form to create a new organization with all required fields

'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft, Building2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { organizationsApi, OrganizationCreate } from '@/lib/api/organizations';
import { useSession } from 'next-auth/react';
import { UserRole } from '@/types';
import { UserMenu } from '@/components/user-menu';

export default function NewOrganizationPage() {
  const router = useRouter();
  const { toast } = useToast();
  const { data: session } = useSession();
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState<Partial<OrganizationCreate>>({
    features: {},
  });
  const [licenseType, setLicenseType] = useState<string>('trial');

  // Check if user is system admin
  if (session?.user?.role !== UserRole.SYSTEM_ADMIN) {
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
            onClick={() => router.push('/organizations')}
          >
            Organizations
          </Button>
          <span>/</span>
          <span className="text-foreground">New</span>
        </div>

        <div className="flex items-center mb-6">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => router.push('/organizations')}
            className="mr-4"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Organizations
          </Button>
          <div className="flex-1">
            <h1 className="text-3xl font-bold">Create Organization</h1>
            <p className="text-muted-foreground mt-1">
              Set up a new organization for clinical trials
            </p>
          </div>
          <UserMenu />
        </div>

        <form onSubmit={handleSubmit}>
          <Card>
            <CardHeader>
              <CardTitle>Organization Details</CardTitle>
              <CardDescription>
                Basic information about the organization
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <Label htmlFor="name">Organization Name *</Label>
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
                />
                <p className="text-sm text-muted-foreground mt-1">
                  The full name of the organization
                </p>
              </div>

              <div>
                <Label htmlFor="slug">URL Slug *</Label>
                <Input
                  id="slug"
                  placeholder="e.g., pharma-corp"
                  value={formData.slug || ''}
                  onChange={(e) => setFormData({ ...formData, slug: e.target.value })}
                  pattern="[a-z0-9-]+"
                  required
                />
                <p className="text-sm text-muted-foreground mt-1">
                  Unique identifier used in URLs (lowercase letters, numbers, and hyphens only)
                </p>
              </div>

              <div>
                <Label htmlFor="license">License Type</Label>
                <Select
                  defaultValue="trial"
                  onValueChange={(value) => {
                    // This would be handled by the backend based on license type
                    const licenseDefaults = {
                      trial: { max_users: 10, max_studies: 5 },
                      basic: { max_users: 25, max_studies: 10 },
                      professional: { max_users: 100, max_studies: 50 },
                      enterprise: { max_users: -1, max_studies: -1 },
                    };
                  }}
                >
                  <SelectTrigger id="license">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="trial">Trial (10 users, 5 studies)</SelectItem>
                    <SelectItem value="basic">Basic (25 users, 10 studies)</SelectItem>
                    <SelectItem value="professional">Professional (100 users, 50 studies)</SelectItem>
                    <SelectItem value="enterprise">Enterprise (Unlimited)</SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-sm text-muted-foreground mt-1">
                  Determines user and study limits
                </p>
              </div>

              <div className="bg-muted/50 p-4 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <Building2 className="h-5 w-5 text-muted-foreground" />
                  <span className="font-medium">Default Features</span>
                </div>
                <p className="text-sm text-muted-foreground">
                  All organizations start with standard features enabled. Additional features
                  can be configured after creation.
                </p>
              </div>
            </CardContent>
          </Card>

          <div className="flex justify-between mt-6">
            <Button
              type="button"
              variant="outline"
              onClick={() => router.push('/organizations')}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={createOrganization.isPending}>
              {createOrganization.isPending ? 'Creating...' : 'Create Organization'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}