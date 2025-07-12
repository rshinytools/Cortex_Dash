// ABOUTME: TypeScript type definitions for menu-related entities
// ABOUTME: Defines interfaces and enums for navigation menu system

/**
 * Menu item type enumeration
 */
export enum MenuItemType {
  DASHBOARD_PAGE = "dashboard_page",  // Has its own canvas in the dashboard
  GROUP = "group",                     // Placeholder for submenus
  DIVIDER = "divider",                 // Visual separator
  EXTERNAL = "external"                // External link
}

/**
 * Menu item target enumeration
 */
export enum MenuItemTarget {
  SELF = "_self",
  BLANK = "_blank",
  PARENT = "_parent",
  TOP = "_top"
}

/**
 * Menu position enumeration
 */
export enum MenuPosition {
  TOP = "top",
  SIDEBAR = "sidebar",
  BOTTOM = "bottom"
}

/**
 * Individual menu item configuration
 */
export interface MenuItem {
  /** Unique identifier */
  id: string;
  /** Menu item label */
  label: string;
  /** Menu item type */
  type: MenuItemType;
  /** Navigation URL (for external links) */
  url?: string;
  /** Icon name or path */
  icon?: string;
  /** Target for external links */
  target?: MenuItemTarget;
  /** Display order */
  order: number;
  /** Whether item is visible */
  isVisible: boolean;
  /** Whether item is enabled */
  isEnabled: boolean;
  /** Child menu items (for GROUP type) */
  children?: MenuItem[];
  /** Dashboard configuration (for DASHBOARD_PAGE type) */
  dashboardConfig?: {
    /** Unique dashboard view ID */
    viewId: string;
    /** Canvas layout configuration */
    layout?: {
      type: string;
      columns?: number;
      rows?: number;
    };
  };
  /** Required permissions to view */
  permissions?: string[];
  /** Badge configuration */
  badge?: {
    /** Badge text */
    text?: string;
    /** Badge count */
    count?: number;
    /** Badge color */
    color?: string;
  };
  /** Custom CSS classes */
  className?: string;
  /** Custom properties */
  customProperties?: Record<string, any>;
}

/**
 * Menu template definition
 */
export interface MenuTemplate {
  /** Unique identifier */
  id: string;
  /** Template name */
  name: string;
  /** Template description */
  description?: string;
  /** Menu position */
  position: MenuPosition;
  /** Menu items */
  items: MenuItem[];
  /** Template version */
  version: string;
  /** Whether template is active */
  isActive: boolean;
  /** Whether template is default */
  isDefault?: boolean;
  /** Study types this menu applies to */
  studyTypes?: string[];
  /** Theme configuration */
  theme?: {
    /** Background color */
    backgroundColor?: string;
    /** Text color */
    textColor?: string;
    /** Active item color */
    activeColor?: string;
    /** Hover color */
    hoverColor?: string;
  };
  /** Custom properties */
  customProperties?: Record<string, any>;
  /** Creation timestamp */
  createdAt: string;
  /** Last update timestamp */
  updatedAt: string;
}

/**
 * Study-specific menu configuration
 */
export interface StudyMenu {
  /** Unique identifier */
  id: string;
  /** Study ID */
  studyId: string;
  /** Based on template ID */
  templateId?: string;
  /** Menu template (populated) */
  template?: MenuTemplate;
  /** Menu position */
  position: MenuPosition;
  /** Menu items (overrides template) */
  items: MenuItem[];
  /** Whether menu is active */
  isActive: boolean;
  /** Theme overrides */
  theme?: {
    backgroundColor?: string;
    textColor?: string;
    activeColor?: string;
    hoverColor?: string;
  };
  /** Custom metadata */
  metadata?: Record<string, any>;
  /** Creation timestamp */
  createdAt: string;
  /** Last update timestamp */
  updatedAt: string;
}