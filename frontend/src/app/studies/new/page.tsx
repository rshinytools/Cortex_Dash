// ABOUTME: Study creation page - first step in study setup workflow
// ABOUTME: Allows system admins to create new clinical studies

'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';
import { StudyPhase, StudyStatus, UserRole } from '@/types';
import { format } from 'date-fns';
import { useSession } from 'next-auth/react';
import { UserMenu } from '@/components/user-menu';

interface StudyCreateData {
  name: string;
  code: string;
  protocol_number: string;
  description?: string;
  phase: StudyPhase;
  therapeutic_area?: string;
  indication?: string;
  planned_start_date?: string | null;
  planned_end_date?: string | null;
  status: StudyStatus;
  org_id: string;
}

export default function NewStudyPage() {
  const router = useRouter();
  const { toast } = useToast();
  const { data: session } = useSession();
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState<Partial<StudyCreateData>>({
    status: StudyStatus.PLANNING,
  });
  const [selectedOrgId, setSelectedOrgId] = useState<string>('');

  // Fetch organizations for system admins
  const { data: organizations } = useQuery({
    queryKey: ['organizations'],
    queryFn: async () => {
      const response = await apiClient.get('/organizations/');
      return response.data;
    },
    enabled: session?.user?.role === UserRole.SYSTEM_ADMIN,
  });

  // Set default org for non-system admins
  useEffect(() => {
    if (session && session.user.org_id && session.user.role !== UserRole.SYSTEM_ADMIN) {
      setSelectedOrgId(session.user.org_id);
    }
  }, [session]);

  const createStudy = useMutation({
    mutationFn: async (data: StudyCreateData) => {
      const response = await apiClient.post('/studies/', data);
      return response.data;
    },
    onSuccess: (data) => {
      toast({
        title: 'Study created successfully',
        description: 'Redirecting to study initialization...',
      });
      // Invalidate the studies query to refresh the list
      queryClient.invalidateQueries({ queryKey: ['studies'] });
      // Redirect to study initialization wizard
      router.push(`/studies/${data.id}/initialize`);
    },
    onError: (error: any) => {
      console.error('Study creation error:', error);
      if (error.code === 'ERR_NETWORK') {
        toast({
          title: 'Network Error',
          description: 'Unable to connect to the server. Please check if the backend is running.',
          variant: 'destructive',
        });
      } else {
        const errorMessage = error.response?.data?.detail || error.message || 'An error occurred';
        toast({
          title: 'Failed to create study',
          description: errorMessage,
          variant: 'destructive',
        });
      }
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.name || !formData.code || !formData.protocol_number || !formData.phase) {
      toast({
        title: 'Missing required fields',
        description: 'Please fill in all required fields',
        variant: 'destructive',
      });
      return;
    }

    const orgId = session?.user?.role === UserRole.SYSTEM_ADMIN ? selectedOrgId : session?.user?.org_id;
    
    if (!orgId) {
      toast({
        title: 'No organization selected',
        description: 'Please select an organization for this study',
        variant: 'destructive',
      });
      return;
    }

    // Add the organization ID and convert dates
    const studyData = {
      ...formData,
      org_id: orgId,
      // Convert date strings to ISO format with time
      planned_start_date: formData.planned_start_date 
        ? new Date(formData.planned_start_date).toISOString()
        : null,
      planned_end_date: formData.planned_end_date
        ? new Date(formData.planned_end_date).toISOString()
        : null,
    } as StudyCreateData;

    createStudy.mutate(studyData);
  };

  return (
    <div className="container mx-auto py-6">
      <div className="max-w-3xl mx-auto">
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
            onClick={() => router.push('/studies')}
          >
            Studies
          </Button>
          <span>/</span>
          <span className="text-foreground">New</span>
        </div>

        <div className="flex items-center mb-6">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => router.push('/studies')}
            className="mr-4"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Studies
          </Button>
          <div className="flex-1">
            <h1 className="text-3xl font-bold">Create New Study</h1>
            <p className="text-muted-foreground mt-1">
              Enter basic study information to get started
            </p>
          </div>
          <UserMenu />
        </div>

        <form onSubmit={handleSubmit}>
          <Card>
            <CardHeader>
              <CardTitle>Study Information</CardTitle>
              <CardDescription>
                Basic details about the clinical study
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Organization selector for system admins */}
              {session?.user?.role === UserRole.SYSTEM_ADMIN && (
                <div>
                  <Label htmlFor="organization">Organization *</Label>
                  <Select
                    value={selectedOrgId}
                    onValueChange={setSelectedOrgId}
                  >
                    <SelectTrigger id="organization">
                      <SelectValue placeholder="Select organization" />
                    </SelectTrigger>
                    <SelectContent>
                      {organizations && organizations.length > 0 ? (
                        organizations.map((org: any) => (
                          <SelectItem key={org.id} value={org.id}>
                            {org.name}
                          </SelectItem>
                        ))
                      ) : (
                        <div className="p-2 text-center text-muted-foreground">
                          No organizations found. Please create one first.
                        </div>
                      )}
                    </SelectContent>
                  </Select>
                  <p className="text-sm text-muted-foreground mt-1">
                    Select the organization this study belongs to. 
                    {(!organizations || organizations.length === 0) && (
                      <>
                        <span className="text-destructive"> You need to create an organization first.</span>
                        <Button
                          type="button"
                          variant="link"
                          size="sm"
                          className="ml-2 h-auto p-0"
                          onClick={() => router.push('/organizations/new')}
                        >
                          Create Organization
                        </Button>
                      </>
                    )}
                  </p>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="name">Study Name *</Label>
                  <Input
                    id="name"
                    placeholder="e.g., COVID-19 Vaccine Phase 3"
                    value={formData.name || ''}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="code">Study Code *</Label>
                  <Input
                    id="code"
                    placeholder="e.g., COV-VAC-P3"
                    value={formData.code || ''}
                    onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                    required
                  />
                </div>
              </div>

              <div>
                <Label htmlFor="protocol_number">Protocol Number *</Label>
                <Input
                  id="protocol_number"
                  placeholder="e.g., PROT-2024-001"
                  value={formData.protocol_number || ''}
                  onChange={(e) => setFormData({ ...formData, protocol_number: e.target.value })}
                  required
                />
                <p className="text-sm text-muted-foreground mt-1">
                  Unique protocol identifier for this study
                </p>
              </div>

              <div>
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  placeholder="Describe the purpose and objectives of this study..."
                  value={formData.description || ''}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={4}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="phase">Study Phase *</Label>
                  <Select
                    value={formData.phase}
                    onValueChange={(value) => setFormData({ ...formData, phase: value as StudyPhase })}
                  >
                    <SelectTrigger id="phase">
                      <SelectValue placeholder="Select phase" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value={StudyPhase.PHASE_1}>Phase 1</SelectItem>
                      <SelectItem value={StudyPhase.PHASE_2}>Phase 2</SelectItem>
                      <SelectItem value={StudyPhase.PHASE_3}>Phase 3</SelectItem>
                      <SelectItem value={StudyPhase.PHASE_4}>Phase 4</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="therapeutic_area">Therapeutic Area</Label>
                  <Input
                    id="therapeutic_area"
                    placeholder="e.g., Oncology, Cardiology"
                    value={formData.therapeutic_area || ''}
                    onChange={(e) => setFormData({ ...formData, therapeutic_area: e.target.value })}
                  />
                </div>
              </div>

              <div>
                <Label htmlFor="indication">Indication</Label>
                <Input
                  id="indication"
                  placeholder="e.g., Advanced Non-Small Cell Lung Cancer"
                  value={formData.indication || ''}
                  onChange={(e) => setFormData({ ...formData, indication: e.target.value })}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="planned_start_date">Planned Start Date</Label>
                  <Input
                    id="planned_start_date"
                    type="date"
                    value={formData.planned_start_date || ''}
                    onChange={(e) => setFormData({ ...formData, planned_start_date: e.target.value })}
                  />
                </div>
                <div>
                  <Label htmlFor="planned_end_date">Planned End Date</Label>
                  <Input
                    id="planned_end_date"
                    type="date"
                    value={formData.planned_end_date || ''}
                    onChange={(e) => setFormData({ ...formData, planned_end_date: e.target.value })}
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          <div className="flex justify-between mt-6">
            <Button
              type="button"
              variant="outline"
              onClick={() => router.push('/studies')}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={createStudy.isPending}>
              {createStudy.isPending ? 'Creating...' : 'Create Study'}
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}