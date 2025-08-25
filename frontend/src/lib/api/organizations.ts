// ABOUTME: API functions for organization management
// ABOUTME: Handles organization CRUD operations

import { secureApiClient } from './secure-client';

export interface Organization {
  id: string;
  name: string;
  slug: string;
  features?: Record<string, any>;
  active: boolean;
  created_at: string;
  updated_at: string;
  license_type: string;
  max_users: number;
  max_studies: number;
}

export interface OrganizationCreate {
  name: string;
  slug: string;
  features?: Record<string, any>;
}

export const organizationsApi = {
  // Get all organizations (system admin only)
  async getOrganizations() {
    const response = await secureApiClient.get<Organization[]>('/organizations/');
    return response.data;
  },

  // Get single organization
  async getOrganization(orgId: string) {
    const response = await secureApiClient.get<Organization>(`/organizations/${orgId}/`);
    return response.data;
  },

  // Create organization (system admin only)
  async createOrganization(data: OrganizationCreate) {
    const response = await secureApiClient.post<Organization>('/organizations/', data);
    return response.data;
  },

  // Update organization
  async updateOrganization(orgId: string, data: Partial<OrganizationCreate>) {
    const response = await secureApiClient.patch<Organization>(`/organizations/${orgId}/`, data);
    return response.data;
  },

  // Delete organization
  async deleteOrganization(orgId: string, hardDelete: boolean = false, force: boolean = false) {
    const params = new URLSearchParams();
    if (hardDelete) params.append('hard_delete', 'true');
    if (force) params.append('force', 'true');
    
    const response = await secureApiClient.delete(`/organizations/${orgId}/?${params.toString()}`);
    return response.data;
  },

  // Get organization statistics
  async getOrganizationStats(orgId: string) {
    const response = await secureApiClient.get<{
      organization_id: string;
      name: string;
      user_count: number;
      study_count: number;
      max_users: number;
      max_studies: number;
      license_type: string;
      active: boolean;
    }>(`/organizations/${orgId}/stats/`);
    return response.data;
  },
};