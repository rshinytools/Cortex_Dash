// ABOUTME: TypeScript type definitions for widget-related entities
// ABOUTME: Defines interfaces and enums for widget system components

/**
 * Widget category enumeration - matches backend categories
 */
export enum WidgetCategory {
  METRICS = "metrics",
  CHARTS = "charts", 
  TABLES = "tables",
  MAPS = "maps",
  SPECIALIZED = "specialized"
}

/**
 * Widget type enumeration
 */
export enum WidgetType {
  METRIC = "metric",
  CHART = "chart",
  TABLE = "table",
  TEXT = "text",
  IMAGE = "image",
  IFRAME = "iframe"
}

/**
 * Widget size configuration
 */
export interface WidgetSize {
  /** Minimum width in grid units */
  minWidth: number;
  /** Minimum height in grid units */
  minHeight: number;
  /** Default width in grid units */
  defaultWidth: number;
  /** Default height in grid units */
  defaultHeight: number;
}

/**
 * Widget data requirement specification
 */
export interface WidgetDataRequirement {
  /** Type of data source required */
  sourceType: "dataset" | "api" | "static";
  /** Required fields from the data source */
  requiredFields?: string[];
  /** Optional fields from the data source */
  optionalFields?: string[];
  /** Refresh interval in seconds */
  refreshInterval?: number;
}

/**
 * Field type enumeration for data contracts
 */
export type DataFieldType = "string" | "number" | "date" | "datetime" | "boolean" | "array" | "object";

/**
 * Data field definition in a widget's data contract
 */
export interface DataFieldDefinition {
  /** Field name used within the widget */
  name: string;
  /** Data type of the field */
  type: DataFieldType;
  /** Human-readable description of the field */
  description: string;
  /** Standard CDISC SDTM mapping if applicable */
  sdtmMapping?: string;
  /** Standard CDISC ADaM mapping if applicable */
  adamMapping?: string;
  /** Common field name patterns that could map to this field */
  commonPatterns?: string[];
  /** Default value if field is missing */
  defaultValue?: any;
  /** Validation rules */
  validation?: {
    required?: boolean;
    min?: number;
    max?: number;
    pattern?: string;
    enum?: any[];
  };
}

/**
 * Calculated field definition
 */
export interface CalculatedFieldDefinition {
  /** Field name for the calculated value */
  name: string;
  /** Data type of the result */
  type: DataFieldType;
  /** Description of what this field calculates */
  description: string;
  /** Calculation expression or function */
  calculation: string;
  /** Fields required for this calculation */
  dependsOn: string[];
}

/**
 * Data source definition for a widget
 */
export interface DataSourceDefinition {
  /** Type of dataset (e.g., ADSL, ADAE, custom) */
  datasetType: string;
  /** How often to refresh data in seconds */
  refreshRate?: number;
  /** Field to join on if this is a secondary source */
  joinOn?: string;
  /** Join type if applicable */
  joinType?: "inner" | "left" | "right" | "full";
}

/**
 * Complete data contract for a widget
 */
export interface DataContract {
  /** Required fields that must be present */
  requiredFields: DataFieldDefinition[];
  /** Optional fields that enhance the widget if available */
  optionalFields?: DataFieldDefinition[];
  /** Fields calculated from other fields */
  calculatedFields?: CalculatedFieldDefinition[];
  /** Data source requirements */
  dataSources: {
    /** Primary data source */
    primary: DataSourceDefinition;
    /** Secondary data sources */
    secondary?: DataSourceDefinition[];
  };
  /** Field mapping suggestions for common scenarios */
  mappingSuggestions?: {
    [scenario: string]: {
      [fieldName: string]: string;
    };
  };
}

/**
 * Widget configuration schema
 */
export interface WidgetConfig {
  /** Data source configuration */
  dataSource?: {
    /** Type of data source */
    type: "dataset" | "api" | "static";
    /** Dataset ID if type is dataset */
    datasetId?: string;
    /** API endpoint if type is api */
    endpoint?: string;
    /** Static data if type is static */
    staticData?: any;
  };
  /** Display configuration */
  display?: {
    /** Title override */
    title?: string;
    /** Subtitle */
    subtitle?: string;
    /** Color scheme */
    colorScheme?: string;
    /** Show/hide elements */
    showTitle?: boolean;
    showBorder?: boolean;
    showRefreshTime?: boolean;
  };
  /** Chart-specific configuration */
  chartConfig?: {
    /** Chart type */
    type?: "line" | "bar" | "pie" | "scatter" | "area";
    /** X-axis configuration */
    xAxis?: any;
    /** Y-axis configuration */
    yAxis?: any;
    /** Series configuration */
    series?: any[];
  };
  /** Table-specific configuration */
  tableConfig?: {
    /** Columns configuration */
    columns?: any[];
    /** Pagination settings */
    pagination?: boolean;
    /** Sorting settings */
    sortable?: boolean;
    /** Filtering settings */
    filterable?: boolean;
  };
  /** Metric-specific configuration */
  metricConfig?: {
    /** Metric value field */
    valueField?: string;
    /** Comparison configuration */
    comparison?: {
      enabled: boolean;
      type: "previous" | "target";
      value?: number;
    };
    /** Formatting configuration */
    format?: {
      type: "number" | "percentage" | "currency";
      decimals?: number;
      prefix?: string;
      suffix?: string;
    };
  };
}

/**
 * Widget definition (template)
 */
export interface WidgetDefinition {
  /** Unique identifier */
  id: string;
  /** Widget code (unique identifier) */
  code: string;
  /** Widget name */
  name: string;
  /** Widget description */
  description?: string;
  /** Widget category */
  category: WidgetCategory;
  /** Widget version */
  version: string;
  /** Size constraints */
  size_constraints: {
    minWidth: number;
    minHeight: number;
    maxWidth?: number;
    maxHeight?: number;
    defaultWidth: number;
    defaultHeight: number;
  };
  /** Configuration schema for validation */
  config_schema?: any;
  /** Default configuration */
  default_config?: any;
  /** Data requirements */
  data_requirements?: any;
  /** Data contract defining field requirements and mappings */
  data_contract?: any;
  /** Whether widget is active */
  is_active: boolean;
  /** Creation timestamp */
  created_at?: string;
  /** Last update timestamp */
  updated_at?: string;
  
  // Frontend compatibility fields (for gradual migration)
  type?: WidgetType;
  componentPath?: string;
  defaultConfig?: WidgetConfig;
  size?: WidgetSize;
  dataRequirements?: WidgetDataRequirement;
  dataContract?: DataContract;
  tags?: string[];
  isActive?: boolean;
  createdAt?: string;
  updatedAt?: string;
}

/**
 * Widget instance (specific configuration of a widget)
 */
export interface WidgetInstance {
  /** Unique identifier */
  id: string;
  /** Reference to widget definition */
  widgetDefinitionId: string;
  /** Widget definition (populated) */
  widgetDefinition?: WidgetDefinition;
  /** Study ID this instance belongs to */
  studyId: string;
  /** Dashboard ID this instance belongs to */
  dashboardId?: string;
  /** Instance configuration (overrides defaults) */
  config: WidgetConfig;
  /** Layout position */
  position?: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  /** Display order */
  order?: number;
  /** Whether instance is visible */
  isVisible: boolean;
  /** Access control */
  permissions?: {
    view?: string[];
    edit?: string[];
  };
  /** Custom metadata */
  metadata?: Record<string, any>;
  /** Creation timestamp */
  createdAt: string;
  /** Last update timestamp */
  updatedAt: string;
}