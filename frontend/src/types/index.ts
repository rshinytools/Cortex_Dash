// ABOUTME: Type definitions for the clinical dashboard application
// ABOUTME: Mirrors the backend models and API response types

// User and Auth types
export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  org_id: string;
  organization?: Organization;
  is_active: boolean;
  is_mfa_enabled: boolean;
  created_at: string;
  updated_at: string;
}

export enum UserRole {
  SYSTEM_ADMIN = 'system_admin',
  ORG_ADMIN = 'org_admin',
  STUDY_MANAGER = 'study_manager',
  DATA_ANALYST = 'data_analyst',
  VIEWER = 'viewer',
  AUDITOR = 'auditor',
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

// Organization types
export interface Organization {
  id: string;
  name: string;
  subdomain: string;
  settings: Record<string, any>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// Study types
export interface Study {
  id: string;
  org_id: string;
  name: string;
  protocol_number: string;
  phase: StudyPhase;
  status: StudyStatus;
  therapeutic_area: string;
  indication: string;
  start_date: string;
  end_date?: string;
  configuration: StudyConfiguration;
  created_at: string;
  updated_at: string;
}

export enum StudyPhase {
  PHASE_1 = 'phase_1',
  PHASE_2 = 'phase_2',
  PHASE_3 = 'phase_3',
  PHASE_4 = 'phase_4',
}

export enum StudyStatus {
  PLANNING = 'planning',
  ACTIVE = 'active',
  COMPLETED = 'completed',
  TERMINATED = 'terminated',
}

export interface StudyConfiguration {
  data_sources: DataSourceConfig[];
  pipeline_config: PipelineConfig;
  dashboard_config: DashboardConfig;
  branding?: BrandingConfig;
}

export interface DataSourceConfig {
  id: string;
  name: string;
  type: 'api' | 'sftp' | 'folder' | 's3';
  connection_params: Record<string, any>;
  sync_schedule?: string;
  is_active: boolean;
}

export interface PipelineConfig {
  steps: PipelineStep[];
  schedule?: string;
  notifications?: NotificationConfig;
}

export interface PipelineStep {
  id: string;
  name: string;
  type: string;
  config: Record<string, any>;
  order: number;
}

export interface NotificationConfig {
  email_on_success: boolean;
  email_on_failure: boolean;
  recipients: string[];
}

export interface DashboardConfig {
  layout: LayoutConfig;
  widgets: WidgetConfig[];
  filters: FilterConfig[];
  theme?: ThemeConfig;
}

export interface LayoutConfig {
  type: 'grid' | 'tabs' | 'sections';
  config: Record<string, any>;
}

export interface WidgetConfig {
  id: string;
  type: WidgetType;
  title: string;
  config: Record<string, any>;
  position: WidgetPosition;
  permissions?: string[];
}

export enum WidgetType {
  METRIC = 'metric',
  LINE_CHART = 'line_chart',
  BAR_CHART = 'bar_chart',
  PIE_CHART = 'pie_chart',
  SCATTER_PLOT = 'scatter_plot',
  HEATMAP = 'heatmap',
  TABLE = 'table',
  PATIENT_FLOW = 'patient_flow',
  ENROLLMENT_TIMELINE = 'enrollment_timeline',
}

export interface WidgetPosition {
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface FilterConfig {
  id: string;
  field: string;
  label: string;
  type: 'select' | 'multiselect' | 'daterange' | 'search';
  options?: FilterOption[];
  default_value?: any;
}

export interface FilterOption {
  value: string;
  label: string;
}

export interface ThemeConfig {
  primary_color?: string;
  secondary_color?: string;
  chart_colors?: string[];
  font_family?: string;
}

export interface BrandingConfig {
  logo_light?: string;
  logo_dark?: string;
  favicon?: string;
  colors?: Record<string, string>;
}

// Data types
export interface DataPoint {
  id: string;
  study_id: string;
  subject_id: string;
  visit_name: string;
  visit_date: string;
  data_type: string;
  data_values: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface Metric {
  id: string;
  study_id: string;
  name: string;
  type: MetricType;
  calculation: string;
  filters?: Record<string, any>;
  group_by?: string[];
  time_window?: string;
  created_at: string;
  updated_at: string;
}

export enum MetricType {
  COUNT = 'count',
  SUM = 'sum',
  AVERAGE = 'average',
  PERCENTAGE = 'percentage',
  RATE = 'rate',
  CUSTOM = 'custom',
}

// Visualization types
export interface ChartData {
  labels: string[];
  datasets: Dataset[];
}

export interface Dataset {
  label: string;
  data: number[];
  backgroundColor?: string | string[];
  borderColor?: string | string[];
  borderWidth?: number;
}

export interface TableData {
  columns: TableColumn[];
  rows: Record<string, any>[];
}

export interface TableColumn {
  key: string;
  label: string;
  type?: 'string' | 'number' | 'date' | 'boolean';
  sortable?: boolean;
  filterable?: boolean;
}

// Audit types
export interface AuditLog {
  id: string;
  user_id: string;
  action: string;
  resource_type: string;
  resource_id: string;
  details: Record<string, any>;
  ip_address: string;
  user_agent: string;
  created_at: string;
}

// Pagination
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// Common request types
export interface PaginationParams {
  page?: number;
  size?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface FilterParams {
  [key: string]: any;
}

// Export new widget and dashboard types
export * from './widget';
export * from './dashboard';
export * from './menu';