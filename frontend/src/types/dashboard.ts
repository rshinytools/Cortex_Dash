// ABOUTME: TypeScript type definitions for dashboard-related entities
// ABOUTME: Defines interfaces and enums for dashboard system components

import { WidgetInstance } from "./widget";

/**
 * Dashboard category enumeration
 */
export enum DashboardCategory {
  EXECUTIVE = "executive",
  OPERATIONAL = "operational",
  SAFETY = "safety",
  EFFICACY = "efficacy",
  QUALITY = "quality",
  REGULATORY = "regulatory",
  CUSTOM = "custom"
}

/**
 * Dashboard visibility level
 */
export enum DashboardVisibility {
  PRIVATE = "private",
  STUDY = "study",
  ORGANIZATION = "organization",
  PUBLIC = "public"
}

/**
 * Dashboard layout type
 */
export enum LayoutType {
  GRID = "grid",
  FLEX = "flex",
  FIXED = "fixed"
}

/**
 * Dashboard widget configuration
 */
export interface DashboardWidget {
  /** Widget instance ID */
  widgetInstanceId: string;
  /** Widget instance (populated) */
  widgetInstance?: WidgetInstance;
  /** Position in the dashboard */
  position: {
    /** X coordinate in grid units */
    x: number;
    /** Y coordinate in grid units */
    y: number;
    /** Width in grid units */
    width: number;
    /** Height in grid units */
    height: number;
  };
  /** Display order (z-index) */
  order: number;
  /** Whether widget is visible */
  isVisible: boolean;
  /** Widget-specific overrides */
  overrides?: {
    /** Title override */
    title?: string;
    /** Configuration overrides */
    config?: Record<string, any>;
  };
}

/**
 * Dashboard layout configuration
 */
export interface DashboardLayout {
  /** Layout type */
  type: LayoutType;
  /** Number of columns in grid */
  columns?: number;
  /** Row height in pixels */
  rowHeight?: number;
  /** Margin between widgets [x, y] */
  margin?: [number, number];
  /** Container padding [top, right, bottom, left] */
  containerPadding?: [number, number, number, number];
  /** Whether layout is responsive */
  isResponsive?: boolean;
  /** Breakpoints for responsive design */
  breakpoints?: {
    lg?: number;
    md?: number;
    sm?: number;
    xs?: number;
  };
  /** Layouts per breakpoint */
  layouts?: {
    lg?: DashboardWidget[];
    md?: DashboardWidget[];
    sm?: DashboardWidget[];
    xs?: DashboardWidget[];
  };
}

/**
 * Dashboard template definition
 */
export interface DashboardTemplate {
  /** Unique identifier */
  id: string;
  /** Template name */
  name: string;
  /** Template description */
  description?: string;
  /** Dashboard category */
  category: DashboardCategory;
  /** Template version */
  version: string;
  /** Layout configuration */
  layout: DashboardLayout;
  /** Widgets in the template */
  widgets: DashboardWidget[];
  /** Default filters */
  defaultFilters?: Record<string, any>;
  /** Theme configuration */
  theme?: {
    /** Primary color */
    primaryColor?: string;
    /** Secondary color */
    secondaryColor?: string;
    /** Background color */
    backgroundColor?: string;
    /** Dark mode enabled */
    darkMode?: boolean;
  };
  /** Preview image URL */
  previewImageUrl?: string;
  /** Tags for categorization */
  tags?: string[];
  /** Whether template is active */
  isActive: boolean;
  /** Whether template is default for category */
  isDefault?: boolean;
  /** Required data sources */
  requiredDataSources?: string[];
  /** Custom properties */
  customProperties?: Record<string, any>;
  /** Creation timestamp */
  createdAt: string;
  /** Last update timestamp */
  updatedAt: string;
}

/**
 * Study-specific dashboard instance
 */
export interface StudyDashboard {
  /** Unique identifier */
  id: string;
  /** Study ID */
  studyId: string;
  /** Dashboard name */
  name: string;
  /** Dashboard description */
  description?: string;
  /** Based on template ID */
  templateId?: string;
  /** Dashboard template (populated) */
  template?: DashboardTemplate;
  /** Dashboard category */
  category: DashboardCategory;
  /** Visibility level */
  visibility: DashboardVisibility;
  /** Layout configuration (overrides template) */
  layout: DashboardLayout;
  /** Dashboard-specific filters */
  filters?: Record<string, any>;
  /** Dashboard-specific theme */
  theme?: {
    primaryColor?: string;
    secondaryColor?: string;
    backgroundColor?: string;
    darkMode?: boolean;
  };
  /** Whether dashboard is active */
  isActive: boolean;
  /** Whether dashboard is default for study */
  isDefault?: boolean;
  /** Display order */
  order: number;
  /** Access control */
  permissions?: {
    view?: string[];
    edit?: string[];
    share?: string[];
  };
  /** Sharing settings */
  sharing?: {
    /** Whether dashboard is shared */
    isShared: boolean;
    /** Share URL if shared */
    shareUrl?: string;
    /** Share expiration */
    shareExpiration?: string;
  };
  /** Custom metadata */
  metadata?: Record<string, any>;
  /** Creation timestamp */
  createdAt: string;
  /** Last update timestamp */
  updatedAt: string;
  /** Created by user ID */
  createdBy?: string;
  /** Last updated by user ID */
  updatedBy?: string;
}