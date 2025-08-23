// ABOUTME: API functions for study management
// ABOUTME: Handles study CRUD operations and study-specific endpoints

import { apiClient } from './client';
import { StudyStatus, StudyPhase } from '@/types';

export interface Study {
  id: string;
  org_id: string;
  name: string;
  code: string;
  protocol_number: string;
  description?: string;
  phase: StudyPhase;
  therapeutic_area?: string;
  indication?: string;
  planned_start_date?: string;
  planned_end_date?: string;
  start_date?: string;
  end_date?: string;
  status: StudyStatus;
  created_at: string;
  updated_at: string;
  organization?: {
    name: string;
  };
  // Initialization tracking
  initialization_status?: string;
  initialization_progress?: number;
  dashboard_template_id?: string;
  template_applied_at?: string;
  data_uploaded_at?: string;
  mappings_configured_at?: string;
  activated_at?: string;
}

export interface StudyCreate {
  org_id: string;
  name: string;
  code: string;
  protocol_number: string;
  description?: string;
  phase: StudyPhase;
  therapeutic_area?: string;
  indication?: string;
  planned_start_date?: string;
  planned_end_date?: string;
  status?: StudyStatus;
}

export interface StudyUpdate {
  name?: string;
  description?: string;
  phase?: StudyPhase;
  therapeutic_area?: string;
  indication?: string;
  planned_start_date?: string;
  planned_end_date?: string;
  start_date?: string;
  end_date?: string;
  status?: StudyStatus;
}

export interface StudyMenuResponse {
  menu_structure: {
    items: Array<{
      id: string;
      type: 'dashboard' | 'group' | 'link';
      label: string;
      icon?: string;
      dashboard_code?: string;
      order?: number;
      children?: Array<any>;
      required_permissions?: string[];
    }>;
  };
  version: number;
  last_updated: string;
}

export const studiesApi = {
  // Get all studies (filtered by user permissions)
  async getStudies() {
    const response = await apiClient.get<Study[]>('/studies/');
    return response.data;
  },

  // Get single study
  async getStudy(studyId: string) {
    const response = await apiClient.get<Study>(`/studies/${studyId}`);
    return response.data;
  },

  // Create study (system admin only)
  async createStudy(data: StudyCreate) {
    const response = await apiClient.post<Study>('/studies/', data);
    return response.data;
  },

  // Update study
  async updateStudy(studyId: string, data: StudyUpdate) {
    const response = await apiClient.patch<Study>(`/studies/${studyId}`, data);
    return response.data;
  },

  // Delete study (soft delete/archive by default)
  async deleteStudy(studyId: string, hardDelete: boolean = false) {
    const url = hardDelete ? `/studies/${studyId}?hard_delete=true` : `/studies/${studyId}`;
    await apiClient.delete(url);
  },

  // Get study statistics
  async getStudyStats(studyId: string) {
    const response = await apiClient.get(`/studies/${studyId}/stats`);
    return response.data;
  },

  // Initialize study (configure data sources, pipelines, dashboards)
  async initializeStudy(studyId: string, config: any) {
    const response = await apiClient.post(`/studies/${studyId}/initialize`, config);
    return response.data;
  },

  // Activate study
  async activateStudy(studyId: string) {
    const response = await apiClient.post(`/studies/${studyId}/activate`);
    return response.data;
  },

  // Deactivate study
  async deactivateStudy(studyId: string) {
    const response = await apiClient.post(`/studies/${studyId}/deactivate`);
    return response.data;
  },

  // Get study dashboard configuration
  async getStudyDashboard(studyId: string) {
    const response = await apiClient.get(`/studies/${studyId}/dashboard`);
    return response.data;
  },

  // Get study menu structure
  async getStudyMenu(studyId: string) {
    const response = await apiClient.get<StudyMenuResponse>(`/runtime/${studyId}/menus`);
    return response.data;
  },

  // Get complete dashboard configuration with menu layouts
  async getStudyDashboardConfig(studyId: string) {
    const response = await apiClient.get<{
      id: string;
      dashboard_template_id: string;
      dashboard_code: string;
      dashboard_name: string;
      template_structure: any;
      menu_layouts: Record<string, any[]>;
      default_layout: any[];
      customizations: any;
    }>(`/runtime/${studyId}/dashboard-config`);
    return response.data;
  },

  // New initialization endpoints
  async initializeStudyWithProgress(studyId: string, data: {
    template_id: string;
    skip_data_upload?: boolean;
  }) {
    const response = await apiClient.post(`/studies/${studyId}/initialize`, data);
    return response.data;
  },

  async uploadStudyData(studyId: string, formData: FormData) {
    const response = await apiClient.post(
      `/studies/wizard/${studyId}/upload`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },

  async getInitializationStatus(studyId: string) {
    const response = await apiClient.get(`/studies/${studyId}/initialization/status`);
    return response.data;
  },

  async retryInitialization(studyId: string) {
    const response = await apiClient.post(`/studies/${studyId}/initialization/retry`);
    return response.data;
  },

  async cancelInitialization(studyId: string) {
    const response = await apiClient.delete(`/studies/${studyId}/initialization`);
    return response.data;
  },

  // Wizard endpoints
  async checkDraftStudy() {
    const response = await apiClient.get('/studies/wizard/check-draft');
    return response.data;
  },

  async startInitializationWizard(data: {
    name: string;
    protocol_number: string;
    description?: string;
    phase?: string;
    therapeutic_area?: string;
    indication?: string;
    org_id?: string;
  }) {
    const response = await apiClient.post('/studies/wizard/start', data);
    return response.data;
  },

  async getWizardState(studyId: string) {
    const response = await apiClient.get(`/studies/wizard/${studyId}/state`);
    return response.data;
  },

  async updateWizardState(studyId: string, data: {
    current_step: number;
    data?: any;
    completed_steps?: string[];
  }) {
    const response = await apiClient.patch(`/studies/wizard/${studyId}/state`, data);
    return response.data;
  },

  async getAvailableTemplates(studyId: string) {
    const response = await apiClient.get(`/studies/wizard/${studyId}/templates`);
    return response.data;
  },

  async selectTemplate(studyId: string, data: { template_id: string }) {
    const response = await apiClient.post(`/studies/wizard/${studyId}/select-template`, data);
    return response.data;
  },

  async getUploadStatus(studyId: string) {
    const response = await apiClient.get(`/studies/wizard/${studyId}/upload-status`);
    return response.data;
  },

  async completeUploadStep(studyId: string) {
    const response = await apiClient.post(`/studies/wizard/${studyId}/complete-upload`);
    return response.data;
  },

  async getTemplateRequirements(templateId: string) {
    const response = await apiClient.get(`/dashboard-templates/${templateId}/requirements`);
    return response.data;
  },

  async getFieldMappings(studyId: string) {
    const response = await apiClient.get(`/studies/${studyId}/field-mappings`);
    return response.data;
  },

  async getDatasetSchemas(studyId: string) {
    const response = await apiClient.get(`/studies/${studyId}/dataset-schemas`);
    return response.data;
  },

  async updateFieldMappings(studyId: string, data: {
    widget_id: string;
    mappings: Record<string, any>;
  }) {
    const response = await apiClient.put(`/studies/${studyId}/field-mappings`, data);
    return response.data;
  },

  async getDataVersions(studyId: string) {
    const response = await apiClient.get(`/studies/${studyId}/data-versions`);
    return response.data;
  },

  async activateDataVersion(studyId: string, version: string) {
    const response = await apiClient.post(`/studies/${studyId}/data-versions/${version}/activate`);
    return response.data;
  },

  async saveFieldMappings(studyId: string, data: {
    mappings: Record<string, any>;
    accept_auto_mappings: boolean;
  }) {
    const response = await apiClient.post(`/studies/${studyId}/field-mappings`, data);
    return response.data;
  },

  async completeWizard(studyId: string, data: {
    accept_auto_mappings: boolean;
    custom_mappings?: any;
  }) {
    const response = await apiClient.post(`/studies/wizard/${studyId}/complete`, data);
    return response.data;
  },

  async cancelWizard(studyId: string) {
    const response = await apiClient.post(`/studies/wizard/${studyId}/cancel`);
    return response.data;
  },

  async getMappingData(studyId: string) {
    const response = await apiClient.get(`/studies/wizard/${studyId}/mapping-data`);
    return response.data;
  },

  // Transformation step endpoints
  async createPipelines(studyId: string, pipelines: any[]) {
    const response = await apiClient.post(`/studies/wizard/${studyId}/pipelines`, { pipelines });
    return response.data;
  },

  async executePipelines(studyId: string, pipelineIds: string[]) {
    const response = await apiClient.post(`/studies/wizard/${studyId}/execute-pipelines`, { pipeline_ids: pipelineIds });
    return response.data;
  },

  async getTransformationStatus(studyId: string) {
    const response = await apiClient.get(`/studies/wizard/${studyId}/transformation-status`);
    return response.data;
  },

  async getDerivedDatasets(studyId: string) {
    const response = await apiClient.get(`/studies/wizard/${studyId}/derived-datasets`);
    return response.data;
  },

  async getTransformationReady(studyId: string) {
    const response = await apiClient.get(`/studies/wizard/${studyId}/transformation-ready`);
    return response.data;
  },

  async getSuggestedTransformations(studyId: string) {
    const response = await apiClient.get(`/studies/wizard/${studyId}/suggested-transformations`);
    return response.data;
  },

  async completeTransformationStep(studyId: string, data: {
    skipped: boolean;
    pipeline_ids?: string[];
  }) {
    const response = await apiClient.post(`/studies/wizard/${studyId}/complete-transformation`, data);
    return response.data;
  },

  // Widget filter endpoints
  async saveWidgetFilter(studyId: string, widgetId: string, data: {
    expression: string;
    enabled?: boolean;
  }) {
    const response = await apiClient.put(`/studies/${studyId}/widgets/${widgetId}/filter`, data);
    return response.data;
  },

  async getWidgetFilter(studyId: string, widgetId: string) {
    const response = await apiClient.get(`/studies/${studyId}/widgets/${widgetId}/filter`);
    return response.data;
  },

  async getAllWidgetFilters(studyId: string) {
    const response = await apiClient.get(`/studies/${studyId}/filters`);
    return response.data;
  },

  async deleteWidgetFilter(studyId: string, widgetId: string) {
    const response = await apiClient.delete(`/studies/${studyId}/widgets/${widgetId}/filter`);
    return response.data;
  },
};