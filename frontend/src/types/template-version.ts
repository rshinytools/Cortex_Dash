// ABOUTME: TypeScript types for template versioning system
// ABOUTME: Defines interfaces for drafts, versions, changes, and API responses

export interface TemplateDraft {
  id: string;
  template_id: string;
  draft_content: any;
  changes_summary: ChangeSummary[];
  created_at: string;
  updated_at: string;
  auto_save_at: string;
  is_active: boolean;
}

export interface ChangeSummary {
  timestamp: string;
  user_id: string;
  change_type: ChangeType;
  summary: string;
}

export type ChangeType = 'major' | 'minor' | 'patch';

export interface TemplateVersion {
  id: string;
  version: string;
  version_type: ChangeType;
  auto_created: boolean;
  change_description: string;
  change_summary: ChangeSummary[];
  created_by_name: string;
  created_at: string;
  breaking_changes: boolean;
  migration_notes?: string;
}

export interface TemplateVersionFull extends TemplateVersion {
  template_structure: any;
}

export interface VersionComparison {
  version1: {
    id: string;
    version: string;
    created_at: string;
  };
  version2: {
    id: string;
    version: string;
    created_at: string;
  };
  change_type: ChangeType;
  changes: ChangeDetail[];
  summary: string;
  has_breaking_changes: boolean;
}

export interface ChangeDetail {
  type: 'removal' | 'addition' | 'type_change' | 'value_change';
  path: string;
  severity: ChangeType;
  category: ChangeCategory;
  description: string;
  breaking: boolean;
  old_value?: string;
  new_value?: string;
  old_type?: string;
  new_type?: string;
}

export type ChangeCategory = 'structure' | 'widget' | 'data_source' | 'styling' | 'metadata' | 'menu' | 'permission';

export interface TemplateVersionStatus {
  current_version: string;
  active_drafts: number;
  draft_users: DraftUser[];
  recent_changes: number;
  change_breakdown: {
    major: number;
    minor: number;
    patch: number;
  };
  suggested_version_type: ChangeType;
  last_version_created: string;
}

export interface DraftUser {
  user_id: string;
  user_name: string;
  last_update: string;
}

export interface TemplateChangeLog {
  id: string;
  change_type: ChangeType;
  change_category: ChangeCategory;
  change_description: string;
  created_by_name: string;
  created_at: string;
}

export interface VersionListResponse {
  versions: TemplateVersion[];
  total: number;
}

export interface ChangeListResponse {
  changes: TemplateChangeLog[];
  total: number;
}

export interface CreateVersionRequest {
  version_type: ChangeType;
  change_description: string;
  migration_notes?: string;
  breaking_changes?: boolean;
}