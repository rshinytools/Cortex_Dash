# Widget Development Guide

## Overview

This comprehensive guide provides everything developers need to create custom widgets for the Clinical Dashboard Platform. Whether you're building simple metric displays or complex interactive visualizations, this guide covers the complete development lifecycle from concept to deployment.

## Table of Contents

1. [Development Environment Setup](#development-environment-setup)
2. [Widget Architecture](#widget-architecture)
3. [Creating Your First Widget](#creating-your-first-widget)
4. [Widget Component API](#widget-component-api)
5. [Data Integration](#data-integration)
6. [Interactive Features](#interactive-features)
7. [Styling and Theming](#styling-and-theming)
8. [Testing Widgets](#testing-widgets)
9. [Performance Optimization](#performance-optimization)
10. [Deployment and Distribution](#deployment-and-distribution)
11. [Advanced Topics](#advanced-topics)
12. [Best Practices](#best-practices)

## Development Environment Setup

### Prerequisites

Before starting widget development, ensure you have the following installed:

```bash
# Required tools
node --version    # >= 18.0.0
npm --version     # >= 9.0.0
git --version     # >= 2.30.0

# Optional but recommended
docker --version  # >= 20.10.0
```

### Project Setup

#### Clone the Development Repository
```bash
# Clone the main repository
git clone https://github.com/sagarmatha-ai/cortex-dash.git
cd cortex-dash

# Install dependencies
npm install

# Set up development environment
cp .env.example .env.local
```

#### Development Environment Configuration
```env
# .env.local
NODE_ENV=development
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_STORYBOOK_MODE=true
DATABASE_URL=postgresql://user:password@localhost:5432/cortex_dash_dev
```

#### Start Development Services
```bash
# Start backend services
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start frontend development server
cd frontend
npm run dev

# Start Storybook (for widget development)
npm run storybook
```

### Development Tools

#### IDE Configuration
Recommended VS Code extensions:
- TypeScript and JavaScript
- ES7+ React/Redux/React-Native snippets
- Prettier - Code formatter
- ESLint
- Auto Import - ES6, TS, JSX, TSX

#### Code Quality Tools
```json
{
  "scripts": {
    "lint": "eslint src --ext .ts,.tsx,.js,.jsx",
    "lint:fix": "eslint src --ext .ts,.tsx,.js,.jsx --fix",
    "type-check": "tsc --noEmit",
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage"
  }
}
```

## Widget Architecture

### Widget Component Structure

Every widget in the platform follows a consistent architecture:

```
src/components/widgets/
├── widget-name/
│   ├── index.ts                 # Public exports
│   ├── widget-name.tsx          # Main component
│   ├── widget-name.types.ts     # TypeScript types
│   ├── widget-name.styles.ts    # Styled components
│   ├── widget-name.config.ts    # Configuration schema
│   ├── widget-name.stories.tsx  # Storybook stories
│   └── widget-name.test.tsx     # Unit tests
```

### Core Widget Interface

All widgets must implement the base widget interface:

```typescript
// src/components/widgets/base-widget.ts
export interface WidgetComponent<TConfig = any, TData = any> {
  // Required component function
  (props: WidgetProps<TConfig, TData>): React.ReactElement;
  
  // Widget metadata
  displayName: string;
  widgetType: string;
  category: WidgetCategory;
  
  // Configuration schema
  configSchema: WidgetConfigSchema<TConfig>;
  
  // Optional validation function
  validateConfiguration?: (config: TConfig) => ValidationResult;
  
  // Optional data transformation
  transformData?: (data: any) => TData;
  
  // Optional preview data generator
  generatePreviewData?: (config: TConfig) => TData;
}

export interface WidgetProps<TConfig = any, TData = any> {
  // Widget configuration
  config: TConfig;
  
  // Widget data
  data: TData;
  
  // Widget metadata
  id: string;
  title: string;
  
  // Dashboard context
  dashboardId: string;
  isEditMode: boolean;
  
  // Interaction handlers
  onDataChange?: (data: TData) => void;
  onConfigChange?: (config: TConfig) => void;
  onError?: (error: Error) => void;
  
  // Styling
  width: number;
  height: number;
  theme: WidgetTheme;
}
```

### Widget Registration System

Widgets are registered with the platform using the widget registry:

```typescript
// src/components/widgets/widget-registry.ts
import { WidgetRegistry } from './widget-registry';
import { MetricWidget } from './metric-widget';

// Register widget
WidgetRegistry.register({
  type: 'metric',
  component: MetricWidget,
  category: 'basic',
  displayName: 'Metric Card',
  description: 'Display a single metric with trend',
  configSchema: {
    metric: {
      type: 'select',
      label: 'Metric Type',
      options: ['count', 'sum', 'average', 'percentage'],
      required: true
    },
    dataset: {
      type: 'dataset-selector',
      label: 'Data Source',
      required: true
    }
  }
});
```

## Creating Your First Widget

### Step 1: Define Widget Structure

Let's create a simple "Patient Count" widget:

```typescript
// src/components/widgets/patient-count/patient-count.types.ts
export interface PatientCountConfig {
  dataset: string;
  filterField?: string;
  filterValue?: string;
  showTrend: boolean;
  trendPeriod: 'day' | 'week' | 'month';
}

export interface PatientCountData {
  currentCount: number;
  previousCount?: number;
  trend?: 'up' | 'down' | 'stable';
  changePercent?: number;
  lastUpdated: string;
}
```

### Step 2: Create Configuration Schema

```typescript
// src/components/widgets/patient-count/patient-count.config.ts
import { WidgetConfigSchema } from '../base-widget';
import { PatientCountConfig } from './patient-count.types';

export const patientCountConfigSchema: WidgetConfigSchema<PatientCountConfig> = {
  dataset: {
    type: 'dataset-selector',
    label: 'Dataset',
    description: 'Select the dataset containing patient data',
    required: true,
    validation: {
      required: 'Dataset selection is required'
    }
  },
  filterField: {
    type: 'field-selector',
    label: 'Filter Field',
    description: 'Optional field to filter patients',
    required: false,
    dependsOn: 'dataset'
  },
  filterValue: {
    type: 'text',
    label: 'Filter Value',
    description: 'Value to filter by',
    required: false,
    showIf: (config) => !!config.filterField
  },
  showTrend: {
    type: 'boolean',
    label: 'Show Trend',
    description: 'Display trend comparison',
    default: true
  },
  trendPeriod: {
    type: 'select',
    label: 'Trend Period',
    options: [
      { value: 'day', label: 'Daily' },
      { value: 'week', label: 'Weekly' },
      { value: 'month', label: 'Monthly' }
    ],
    default: 'week',
    showIf: (config) => config.showTrend
  }
};
```

### Step 3: Implement Widget Component

```tsx
// src/components/widgets/patient-count/patient-count.tsx
import React from 'react';
import { WidgetComponent, WidgetProps } from '../base-widget';
import { PatientCountConfig, PatientCountData } from './patient-count.types';
import { patientCountConfigSchema } from './patient-count.config';
import {
  WidgetContainer,
  MetricValue,
  MetricLabel,
  TrendIndicator,
  LastUpdated
} from './patient-count.styles';

const PatientCountWidget: WidgetComponent<PatientCountConfig, PatientCountData> = ({
  config,
  data,
  title,
  theme,
  width,
  height
}) => {
  const getTrendIcon = () => {
    if (!data.trend) return null;
    
    switch (data.trend) {
      case 'up':
        return '↗️';
      case 'down':
        return '↘️';
      default:
        return '➡️';
    }
  };

  const getTrendColor = () => {
    if (!data.trend) return theme.colors.text.secondary;
    
    switch (data.trend) {
      case 'up':
        return theme.colors.success;
      case 'down':
        return theme.colors.error;
      default:
        return theme.colors.text.secondary;
    }
  };

  return (
    <WidgetContainer width={width} height={height} theme={theme}>
      <MetricLabel theme={theme}>{title}</MetricLabel>
      
      <MetricValue theme={theme}>
        {data.currentCount.toLocaleString()}
      </MetricValue>
      
      {config.showTrend && data.trend && (
        <TrendIndicator color={getTrendColor()}>
          {getTrendIcon()} {data.changePercent?.toFixed(1)}%
        </TrendIndicator>
      )}
      
      <LastUpdated theme={theme}>
        Last updated: {new Date(data.lastUpdated).toLocaleString()}
      </LastUpdated>
    </WidgetContainer>
  );
};

// Widget metadata
PatientCountWidget.displayName = 'Patient Count';
PatientCountWidget.widgetType = 'patient-count';
PatientCountWidget.category = 'basic';
PatientCountWidget.configSchema = patientCountConfigSchema;

// Optional validation
PatientCountWidget.validateConfiguration = (config: PatientCountConfig) => {
  const errors: string[] = [];
  
  if (!config.dataset) {
    errors.push('Dataset is required');
  }
  
  if (config.filterField && !config.filterValue) {
    errors.push('Filter value is required when filter field is specified');
  }
  
  return {
    isValid: errors.length === 0,
    errors,
    warnings: []
  };
};

// Optional preview data generator
PatientCountWidget.generatePreviewData = (config: PatientCountConfig): PatientCountData => {
  const currentCount = Math.floor(Math.random() * 1000) + 100;
  const previousCount = Math.floor(Math.random() * 1000) + 100;
  const changePercent = ((currentCount - previousCount) / previousCount) * 100;
  
  return {
    currentCount,
    previousCount,
    changePercent,
    trend: changePercent > 5 ? 'up' : changePercent < -5 ? 'down' : 'stable',
    lastUpdated: new Date().toISOString()
  };
};

export default PatientCountWidget;
```

### Step 4: Create Styled Components

```typescript
// src/components/widgets/patient-count/patient-count.styles.ts
import styled from 'styled-components';
import { WidgetTheme } from '../base-widget';

interface ThemedProps {
  theme: WidgetTheme;
}

export const WidgetContainer = styled.div<{
  width: number;
  height: number;
  theme: WidgetTheme;
}>`
  width: ${props => props.width}px;
  height: ${props => props.height}px;
  background: ${props => props.theme.colors.background.primary};
  border: 1px solid ${props => props.theme.colors.border.primary};
  border-radius: ${props => props.theme.spacing.borderRadius}px;
  padding: ${props => props.theme.spacing.md}px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  box-shadow: ${props => props.theme.shadows.sm};
  
  &:hover {
    box-shadow: ${props => props.theme.shadows.md};
  }
`;

export const MetricLabel = styled.h3<ThemedProps>`
  margin: 0 0 ${props => props.theme.spacing.sm}px 0;
  color: ${props => props.theme.colors.text.secondary};
  font-size: ${props => props.theme.typography.fontSize.sm}px;
  font-weight: ${props => props.theme.typography.fontWeight.medium};
  text-align: center;
`;

export const MetricValue = styled.div<ThemedProps>`
  font-size: ${props => props.theme.typography.fontSize.xl * 2}px;
  font-weight: ${props => props.theme.typography.fontWeight.bold};
  color: ${props => props.theme.colors.text.primary};
  margin-bottom: ${props => props.theme.spacing.sm}px;
`;

export const TrendIndicator = styled.div<{ color: string }>`
  color: ${props => props.color};
  font-size: 14px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 4px;
`;

export const LastUpdated = styled.div<ThemedProps>`
  margin-top: auto;
  font-size: ${props => props.theme.typography.fontSize.xs}px;
  color: ${props => props.theme.colors.text.tertiary};
  text-align: center;
`;
```

### Step 5: Create Storybook Stories

```tsx
// src/components/widgets/patient-count/patient-count.stories.tsx
import type { Meta, StoryObj } from '@storybook/react';
import { PatientCountWidget } from './patient-count';
import { PatientCountConfig, PatientCountData } from './patient-count.types';

const meta: Meta<typeof PatientCountWidget> = {
  title: 'Widgets/PatientCount',
  component: PatientCountWidget,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    config: {
      control: 'object',
    },
    data: {
      control: 'object',
    },
  },
};

export default meta;
type Story = StoryObj<typeof meta>;

const defaultConfig: PatientCountConfig = {
  dataset: 'ADSL',
  showTrend: true,
  trendPeriod: 'week',
};

const defaultData: PatientCountData = {
  currentCount: 156,
  previousCount: 142,
  changePercent: 9.86,
  trend: 'up',
  lastUpdated: new Date().toISOString(),
};

export const Default: Story = {
  args: {
    config: defaultConfig,
    data: defaultData,
    title: 'Total Patients',
    width: 300,
    height: 200,
    id: 'patient-count-1',
    dashboardId: 'dashboard-1',
    isEditMode: false,
  },
};

export const WithoutTrend: Story = {
  args: {
    ...Default.args,
    config: {
      ...defaultConfig,
      showTrend: false,
    },
  },
};

export const DownwardTrend: Story = {
  args: {
    ...Default.args,
    data: {
      ...defaultData,
      currentCount: 132,
      previousCount: 156,
      changePercent: -15.38,
      trend: 'down',
    },
  },
};

export const LargeNumbers: Story = {
  args: {
    ...Default.args,
    data: {
      ...defaultData,
      currentCount: 12456,
      previousCount: 11892,
      changePercent: 4.74,
      trend: 'up',
    },
  },
};
```

### Step 6: Write Unit Tests

```tsx
// src/components/widgets/patient-count/patient-count.test.tsx
import React from 'react';
import { render, screen } from '@testing-library/react';
import { ThemeProvider } from 'styled-components';
import { PatientCountWidget } from './patient-count';
import { PatientCountConfig, PatientCountData } from './patient-count.types';
import { defaultTheme } from '../../../styles/theme';

const mockConfig: PatientCountConfig = {
  dataset: 'ADSL',
  showTrend: true,
  trendPeriod: 'week',
};

const mockData: PatientCountData = {
  currentCount: 156,
  previousCount: 142,
  changePercent: 9.86,
  trend: 'up',
  lastUpdated: '2024-01-15T10:30:00Z',
};

const renderWidget = (config = mockConfig, data = mockData) => {
  return render(
    <ThemeProvider theme={defaultTheme}>
      <PatientCountWidget
        config={config}
        data={data}
        title="Test Patient Count"
        width={300}
        height={200}
        id="test-widget"
        dashboardId="test-dashboard"
        isEditMode={false}
        theme={defaultTheme}
      />
    </ThemeProvider>
  );
};

describe('PatientCountWidget', () => {
  test('renders patient count correctly', () => {
    renderWidget();
    expect(screen.getByText('156')).toBeInTheDocument();
  });

  test('displays trend when enabled', () => {
    renderWidget();
    expect(screen.getByText(/9.9%/)).toBeInTheDocument();
  });

  test('hides trend when disabled', () => {
    const configWithoutTrend = { ...mockConfig, showTrend: false };
    renderWidget(configWithoutTrend);
    expect(screen.queryByText(/9.9%/)).not.toBeInTheDocument();
  });

  test('formats large numbers with commas', () => {
    const dataWithLargeNumber = { ...mockData, currentCount: 12456 };
    renderWidget(mockConfig, dataWithLargeNumber);
    expect(screen.getByText('12,456')).toBeInTheDocument();
  });

  test('displays last updated time', () => {
    renderWidget();
    expect(screen.getByText(/Last updated:/)).toBeInTheDocument();
  });

  test('validates configuration correctly', () => {
    const invalidConfig = { ...mockConfig, dataset: '' };
    const result = PatientCountWidget.validateConfiguration?.(invalidConfig);
    expect(result?.isValid).toBe(false);
    expect(result?.errors).toContain('Dataset is required');
  });

  test('generates preview data', () => {
    const previewData = PatientCountWidget.generatePreviewData?.(mockConfig);
    expect(previewData).toHaveProperty('currentCount');
    expect(previewData).toHaveProperty('trend');
    expect(previewData).toHaveProperty('lastUpdated');
  });
});
```

### Step 7: Register Widget

```typescript
// src/components/widgets/index.ts
import { WidgetRegistry } from './widget-registry';
import { PatientCountWidget } from './patient-count';

// Register the widget
WidgetRegistry.register({
  type: 'patient-count',
  component: PatientCountWidget,
  category: 'basic',
  displayName: 'Patient Count',
  description: 'Display total patient count with trend analysis',
  configSchema: PatientCountWidget.configSchema,
  previewImage: '/widget-previews/patient-count.png',
  tags: ['patients', 'metrics', 'enrollment'],
  version: '1.0.0'
});

// Export for direct usage
export { PatientCountWidget };
```

## Widget Component API

### Base Widget Interface

```typescript
interface BaseWidgetProps {
  // Configuration
  config: WidgetConfig;
  data: WidgetData;
  
  // Metadata
  id: string;
  title: string;
  description?: string;
  
  // Layout
  width: number;
  height: number;
  x?: number;
  y?: number;
  
  // State
  isEditMode: boolean;
  isSelected: boolean;
  isLoading?: boolean;
  error?: Error;
  
  // Context
  dashboardId: string;
  dashboardContext: DashboardContext;
  
  // Theme
  theme: WidgetTheme;
  
  // Callbacks
  onConfigChange?: (config: WidgetConfig) => void;
  onDataRequest?: (params: DataRequestParams) => void;
  onResize?: (size: { width: number; height: number }) => void;
  onError?: (error: Error) => void;
  onInteraction?: (interaction: WidgetInteraction) => void;
}
```

### Configuration Schema Types

```typescript
interface WidgetConfigSchema {
  [fieldName: string]: FieldSchema;
}

interface FieldSchema {
  type: FieldType;
  label: string;
  description?: string;
  required?: boolean;
  default?: any;
  validation?: ValidationRules;
  showIf?: (config: any) => boolean;
  dependsOn?: string | string[];
  options?: OptionDefinition[];
}

type FieldType = 
  | 'text'
  | 'number'
  | 'boolean'
  | 'select'
  | 'multiselect'
  | 'date'
  | 'date-range'
  | 'color'
  | 'dataset-selector'
  | 'field-selector'
  | 'calculation'
  | 'filter'
  | 'custom';
```

### Data Hooks

Use these hooks to manage widget data:

```typescript
// Hook for fetching widget data
export const useWidgetData = <T = any>(
  widgetId: string,
  config: WidgetConfig,
  options?: DataOptions
) => {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const refreshData = useCallback(async () => {
    try {
      setLoading(true);
      const result = await fetchWidgetData(widgetId, config, options);
      setData(result);
      setError(null);
    } catch (err) {
      setError(err as Error);
    } finally {
      setLoading(false);
    }
  }, [widgetId, config, options]);

  useEffect(() => {
    refreshData();
  }, [refreshData]);

  return { data, loading, error, refreshData };
};

// Hook for real-time data updates
export const useRealTimeData = <T = any>(
  widgetId: string,
  config: WidgetConfig
) => {
  const [data, setData] = useState<T | null>(null);

  useEffect(() => {
    const subscription = subscribeToWidgetData(widgetId, config, setData);
    return () => subscription.unsubscribe();
  }, [widgetId, config]);

  return data;
};
```

### Widget State Management

```typescript
// Widget state hook
export const useWidgetState = (initialConfig: WidgetConfig) => {
  const [config, setConfig] = useState(initialConfig);
  const [isDirty, setIsDirty] = useState(false);

  const updateConfig = useCallback((updates: Partial<WidgetConfig>) => {
    setConfig(prev => ({ ...prev, ...updates }));
    setIsDirty(true);
  }, []);

  const resetConfig = useCallback(() => {
    setConfig(initialConfig);
    setIsDirty(false);
  }, [initialConfig]);

  const saveConfig = useCallback(async () => {
    // Save logic here
    setIsDirty(false);
  }, [config]);

  return {
    config,
    isDirty,
    updateConfig,
    resetConfig,
    saveConfig
  };
};
```

## Data Integration

### Data Service Layer

Create a data service for your widget:

```typescript
// src/services/widget-data-service.ts
export class WidgetDataService {
  private apiClient: ApiClient;

  constructor(apiClient: ApiClient) {
    this.apiClient = apiClient;
  }

  async fetchPatientCount(config: PatientCountConfig): Promise<PatientCountData> {
    const query = this.buildQuery(config);
    const response = await this.apiClient.post('/widgets/data', {
      query,
      widget_type: 'patient-count'
    });

    return this.transformResponse(response.data);
  }

  private buildQuery(config: PatientCountConfig): DataQuery {
    const query: DataQuery = {
      dataset: config.dataset,
      aggregation: {
        type: 'count',
        field: 'USUBJID',
        distinct: true
      }
    };

    if (config.filterField && config.filterValue) {
      query.filters = [
        {
          field: config.filterField,
          operator: 'equals',
          value: config.filterValue
        }
      ];
    }

    if (config.showTrend) {
      query.comparison = {
        period: config.trendPeriod,
        type: 'previous_period'
      };
    }

    return query;
  }

  private transformResponse(response: any): PatientCountData {
    return {
      currentCount: response.current_value,
      previousCount: response.previous_value,
      changePercent: response.change_percent,
      trend: this.determineTrend(response.change_percent),
      lastUpdated: response.timestamp
    };
  }

  private determineTrend(changePercent?: number): 'up' | 'down' | 'stable' {
    if (!changePercent) return 'stable';
    if (changePercent > 5) return 'up';
    if (changePercent < -5) return 'down';
    return 'stable';
  }
}
```

### Data Transformation Patterns

```typescript
// Common data transformation utilities
export const DataTransformers = {
  // Transform raw data to chart format
  toChartData: (data: any[], xField: string, yField: string) => {
    return data.map(item => ({
      x: item[xField],
      y: item[yField]
    }));
  },

  // Aggregate data by field
  aggregateBy: (data: any[], groupField: string, valueField: string, aggregation: 'sum' | 'count' | 'avg') => {
    const groups = data.reduce((acc, item) => {
      const key = item[groupField];
      if (!acc[key]) acc[key] = [];
      acc[key].push(item);
      return acc;
    }, {});

    return Object.entries(groups).map(([key, items]: [string, any[]]) => ({
      [groupField]: key,
      value: aggregation === 'count' 
        ? items.length
        : aggregation === 'sum'
        ? items.reduce((sum, item) => sum + (item[valueField] || 0), 0)
        : items.reduce((sum, item) => sum + (item[valueField] || 0), 0) / items.length
    }));
  },

  // Calculate percentiles
  calculatePercentiles: (data: number[], percentiles: number[]) => {
    const sorted = [...data].sort((a, b) => a - b);
    return percentiles.map(p => {
      const index = (p / 100) * (sorted.length - 1);
      const lower = Math.floor(index);
      const upper = Math.ceil(index);
      if (lower === upper) return sorted[lower];
      return sorted[lower] * (upper - index) + sorted[upper] * (index - lower);
    });
  }
};
```

### Caching Strategy

```typescript
// Widget data cache
export class WidgetDataCache {
  private cache = new Map<string, CacheEntry>();
  private readonly defaultTTL = 5 * 60 * 1000; // 5 minutes

  set(key: string, data: any, ttl?: number): void {
    const expiresAt = Date.now() + (ttl || this.defaultTTL);
    this.cache.set(key, { data, expiresAt });
  }

  get(key: string): any | null {
    const entry = this.cache.get(key);
    if (!entry) return null;
    
    if (Date.now() > entry.expiresAt) {
      this.cache.delete(key);
      return null;
    }
    
    return entry.data;
  }

  invalidate(keyPattern?: string): void {
    if (!keyPattern) {
      this.cache.clear();
      return;
    }

    const regex = new RegExp(keyPattern);
    for (const key of this.cache.keys()) {
      if (regex.test(key)) {
        this.cache.delete(key);
      }
    }
  }

  generateKey(widgetId: string, config: any): string {
    const configHash = this.hashObject(config);
    return `widget:${widgetId}:${configHash}`;
  }

  private hashObject(obj: any): string {
    return btoa(JSON.stringify(obj)).replace(/[^a-zA-Z0-9]/g, '');
  }
}

interface CacheEntry {
  data: any;
  expiresAt: number;
}
```

## Interactive Features

### Event Handling

```typescript
// Widget event system
export interface WidgetInteraction {
  type: InteractionType;
  data: any;
  source: string;
  timestamp: number;
}

export type InteractionType = 
  | 'click'
  | 'hover'
  | 'select'
  | 'filter'
  | 'drill-down'
  | 'export'
  | 'refresh';

export const useWidgetInteractions = (widgetId: string) => {
  const [interactions, setInteractions] = useState<WidgetInteraction[]>([]);

  const emitInteraction = useCallback((type: InteractionType, data: any) => {
    const interaction: WidgetInteraction = {
      type,
      data,
      source: widgetId,
      timestamp: Date.now()
    };

    setInteractions(prev => [...prev, interaction]);
    
    // Emit to global event bus
    window.dispatchEvent(new CustomEvent('widget-interaction', {
      detail: interaction
    }));
  }, [widgetId]);

  return { interactions, emitInteraction };
};
```

### Cross-Widget Communication

```typescript
// Widget communication hook
export const useWidgetCommunication = (widgetId: string) => {
  const [messages, setMessages] = useState<WidgetMessage[]>([]);

  const sendMessage = useCallback((targetId: string, data: any) => {
    const message: WidgetMessage = {
      id: generateId(),
      from: widgetId,
      to: targetId,
      data,
      timestamp: Date.now()
    };

    window.dispatchEvent(new CustomEvent('widget-message', {
      detail: message
    }));
  }, [widgetId]);

  const broadcastMessage = useCallback((data: any) => {
    sendMessage('*', data);
  }, [sendMessage]);

  useEffect(() => {
    const handleMessage = (event: CustomEvent<WidgetMessage>) => {
      const message = event.detail;
      if (message.to === widgetId || message.to === '*') {
        setMessages(prev => [...prev, message]);
      }
    };

    window.addEventListener('widget-message', handleMessage as EventListener);
    return () => window.removeEventListener('widget-message', handleMessage as EventListener);
  }, [widgetId]);

  return { messages, sendMessage, broadcastMessage };
};
```

### Drill-Down Implementation

```tsx
// Drill-down example
const ChartWidgetWithDrillDown: React.FC<WidgetProps> = ({ config, data, onInteraction }) => {
  const handleDataPointClick = useCallback((dataPoint: any) => {
    // Prepare drill-down data
    const drillDownData = {
      filters: {
        [config.groupByField]: dataPoint.category,
        dateRange: dataPoint.dateRange
      },
      targetDashboard: config.drillDownDashboard,
      context: dataPoint
    };

    // Emit drill-down interaction
    onInteraction?.({
      type: 'drill-down',
      data: drillDownData,
      source: 'chart-widget',
      timestamp: Date.now()
    });
  }, [config, onInteraction]);

  return (
    <Chart
      data={data}
      onDataPointClick={handleDataPointClick}
      // ... other props
    />
  );
};
```

## Styling and Theming

### Theme System

The platform uses a comprehensive theme system:

```typescript
// src/styles/theme.ts
export interface WidgetTheme {
  colors: {
    primary: string;
    secondary: string;
    success: string;
    warning: string;
    error: string;
    info: string;
    background: {
      primary: string;
      secondary: string;
      tertiary: string;
    };
    text: {
      primary: string;
      secondary: string;
      tertiary: string;
    };
    border: {
      primary: string;
      secondary: string;
    };
  };
  typography: {
    fontFamily: string;
    fontSize: {
      xs: number;
      sm: number;
      md: number;
      lg: number;
      xl: number;
    };
    fontWeight: {
      normal: number;
      medium: number;
      bold: number;
    };
    lineHeight: {
      tight: number;
      normal: number;
      relaxed: number;
    };
  };
  spacing: {
    xs: number;
    sm: number;
    md: number;
    lg: number;
    xl: number;
    borderRadius: number;
  };
  shadows: {
    sm: string;
    md: string;
    lg: string;
  };
  breakpoints: {
    mobile: string;
    tablet: string;
    desktop: string;
  };
}

export const defaultTheme: WidgetTheme = {
  colors: {
    primary: '#1976D2',
    secondary: '#424242',
    success: '#4CAF50',
    warning: '#FF9800',
    error: '#F44336',
    info: '#2196F3',
    background: {
      primary: '#FFFFFF',
      secondary: '#F5F5F5',
      tertiary: '#EEEEEE',
    },
    text: {
      primary: '#212121',
      secondary: '#757575',
      tertiary: '#BDBDBD',
    },
    border: {
      primary: '#E0E0E0',
      secondary: '#BDBDBD',
    },
  },
  // ... rest of theme
};
```

### Responsive Design

```typescript
// Responsive utilities
export const useResponsiveSize = (baseWidth: number, baseHeight: number) => {
  const [size, setSize] = useState({ width: baseWidth, height: baseHeight });

  useEffect(() => {
    const updateSize = () => {
      const containerWidth = window.innerWidth;
      const scale = containerWidth < 768 ? 0.8 : containerWidth < 1024 ? 0.9 : 1;
      
      setSize({
        width: baseWidth * scale,
        height: baseHeight * scale
      });
    };

    updateSize();
    window.addEventListener('resize', updateSize);
    return () => window.removeEventListener('resize', updateSize);
  }, [baseWidth, baseHeight]);

  return size;
};

// Responsive styled component
export const ResponsiveContainer = styled.div<{
  width: number;
  height: number;
  theme: WidgetTheme;
}>`
  width: ${props => props.width}px;
  height: ${props => props.height}px;
  
  @media (max-width: ${props => props.theme.breakpoints.tablet}) {
    width: 100%;
    height: auto;
    min-height: ${props => props.height * 0.8}px;
  }
  
  @media (max-width: ${props => props.theme.breakpoints.mobile}) {
    padding: ${props => props.theme.spacing.sm}px;
  }
`;
```

### Custom Styling Options

```typescript
// Widget-specific styling
export interface WidgetStyling {
  colors?: Partial<WidgetTheme['colors']>;
  typography?: Partial<WidgetTheme['typography']>;
  spacing?: Partial<WidgetTheme['spacing']>;
  customCSS?: string;
  animations?: {
    enabled: boolean;
    duration: number;
    easing: string;
  };
}

export const useWidgetStyling = (
  baseTheme: WidgetTheme,
  customStyling?: WidgetStyling
) => {
  return useMemo(() => {
    if (!customStyling) return baseTheme;

    return {
      ...baseTheme,
      colors: { ...baseTheme.colors, ...customStyling.colors },
      typography: { ...baseTheme.typography, ...customStyling.typography },
      spacing: { ...baseTheme.spacing, ...customStyling.spacing },
    };
  }, [baseTheme, customStyling]);
};
```

## Testing Widgets

### Unit Testing Setup

```typescript
// test-utils.tsx
import React from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { ThemeProvider } from 'styled-components';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { defaultTheme } from '../src/styles/theme';

const AllTheProviders: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={defaultTheme}>
        {children}
      </ThemeProvider>
    </QueryClientProvider>
  );
};

const customRender = (ui: React.ReactElement, options?: RenderOptions) =>
  render(ui, { wrapper: AllTheProviders, ...options });

export * from '@testing-library/react';
export { customRender as render };
```

### Widget Testing Patterns

```typescript
// Widget test helpers
export const createMockWidgetProps = (overrides?: Partial<WidgetProps>) => ({
  id: 'test-widget',
  title: 'Test Widget',
  config: {},
  data: null,
  width: 400,
  height: 300,
  dashboardId: 'test-dashboard',
  isEditMode: false,
  theme: defaultTheme,
  ...overrides,
});

export const mockWidgetData = (type: string, data?: any) => {
  const generators = {
    'patient-count': () => ({
      currentCount: 156,
      previousCount: 142,
      changePercent: 9.86,
      trend: 'up' as const,
      lastUpdated: new Date().toISOString(),
    }),
    'chart': () => ({
      labels: ['Jan', 'Feb', 'Mar'],
      datasets: [
        { label: 'Series 1', data: [10, 20, 30] }
      ],
    }),
    // Add more data generators as needed
  };

  return data || generators[type]?.() || {};
};
```

### Integration Testing

```typescript
// Widget integration tests
describe('Widget Integration', () => {
  test('should fetch and display data correctly', async () => {
    const mockFetch = jest.fn().mockResolvedValue({
      json: () => Promise.resolve(mockWidgetData('patient-count'))
    });
    global.fetch = mockFetch;

    render(
      <PatientCountWidget
        {...createMockWidgetProps({
          config: { dataset: 'ADSL', showTrend: true, trendPeriod: 'week' }
        })}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('156')).toBeInTheDocument();
    });

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/widgets/data'),
      expect.objectContaining({
        method: 'POST',
        body: expect.stringContaining('patient-count')
      })
    );
  });

  test('should handle errors gracefully', async () => {
    const mockFetch = jest.fn().mockRejectedValue(new Error('API Error'));
    global.fetch = mockFetch;

    render(
      <PatientCountWidget
        {...createMockWidgetProps()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/Error loading data/)).toBeInTheDocument();
    });
  });
});
```

### Visual Testing with Storybook

```typescript
// Visual regression testing
import type { Meta, StoryObj } from '@storybook/react';
import { expect } from '@storybook/jest';
import { within, userEvent } from '@storybook/testing-library';

export const InteractiveTest: Story = {
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    
    // Test interactions
    const chartElement = canvas.getByRole('img', { name: /chart/ });
    await userEvent.click(chartElement);
    
    // Verify drill-down behavior
    await expect(canvas.getByText(/drill-down data/)).toBeVisible();
  },
};

export const ResponsiveTest: Story = {
  parameters: {
    viewport: {
      viewports: {
        mobile: { name: 'Mobile', styles: { width: '375px', height: '667px' } },
        tablet: { name: 'Tablet', styles: { width: '768px', height: '1024px' } },
      },
    },
  },
};
```

## Performance Optimization

### Rendering Optimization

```typescript
// Optimized widget component
export const OptimizedWidget: React.FC<WidgetProps> = React.memo(({
  config,
  data,
  ...props
}) => {
  // Memoize expensive calculations
  const processedData = useMemo(() => {
    return processData(data, config);
  }, [data, config]);

  // Debounce config changes
  const debouncedConfig = useDebounce(config, 300);

  // Virtualization for large datasets
  const virtualizedItems = useVirtualization(processedData, {
    itemHeight: 50,
    containerHeight: props.height,
  });

  return (
    <WidgetContainer>
      {virtualizedItems.map(item => (
        <VirtualizedItem key={item.id} {...item} />
      ))}
    </WidgetContainer>
  );
}, (prevProps, nextProps) => {
  // Custom comparison function
  return (
    prevProps.config === nextProps.config &&
    prevProps.data === nextProps.data &&
    prevProps.width === nextProps.width &&
    prevProps.height === nextProps.height
  );
});
```

### Data Processing Optimization

```typescript
// Web Worker for heavy data processing
// data-processor.worker.ts
self.onmessage = (event) => {
  const { data, operation, config } = event.data;

  try {
    let result;
    
    switch (operation) {
      case 'aggregate':
        result = aggregateData(data, config);
        break;
      case 'transform':
        result = transformData(data, config);
        break;
      case 'filter':
        result = filterData(data, config);
        break;
      default:
        throw new Error(`Unknown operation: ${operation}`);
    }

    self.postMessage({ success: true, result });
  } catch (error) {
    self.postMessage({ success: false, error: error.message });
  }
};

// Usage in widget
export const useDataProcessor = () => {
  const workerRef = useRef<Worker>();

  useEffect(() => {
    workerRef.current = new Worker('/data-processor.worker.js');
    return () => workerRef.current?.terminate();
  }, []);

  const processData = useCallback((data: any[], operation: string, config: any) => {
    return new Promise((resolve, reject) => {
      if (!workerRef.current) {
        reject(new Error('Worker not available'));
        return;
      }

      const handleMessage = (event: MessageEvent) => {
        workerRef.current?.removeEventListener('message', handleMessage);
        
        if (event.data.success) {
          resolve(event.data.result);
        } else {
          reject(new Error(event.data.error));
        }
      };

      workerRef.current.addEventListener('message', handleMessage);
      workerRef.current.postMessage({ data, operation, config });
    });
  }, []);

  return { processData };
};
```

### Memory Management

```typescript
// Memory-efficient data handling
export const useMemoryOptimizedData = <T>(
  dataFetcher: () => Promise<T[]>,
  dependencies: any[]
) => {
  const [data, setData] = useState<T[]>([]);
  const [loading, setLoading] = useState(false);
  const abortControllerRef = useRef<AbortController>();

  const fetchData = useCallback(async () => {
    // Cancel previous request
    abortControllerRef.current?.abort();
    abortControllerRef.current = new AbortController();

    setLoading(true);
    try {
      const result = await dataFetcher();
      
      // Check if component is still mounted
      if (!abortControllerRef.current.signal.aborted) {
        setData(result);
      }
    } catch (error) {
      if (!abortControllerRef.current.signal.aborted) {
        console.error('Data fetch error:', error);
      }
    } finally {
      if (!abortControllerRef.current.signal.aborted) {
        setLoading(false);
      }
    }
  }, dependencies);

  useEffect(() => {
    fetchData();
    
    // Cleanup on unmount
    return () => {
      abortControllerRef.current?.abort();
    };
  }, [fetchData]);

  // Clear data when component unmounts
  useEffect(() => {
    return () => {
      setData([]);
    };
  }, []);

  return { data, loading, refetch: fetchData };
};
```

## Deployment and Distribution

### Build Configuration

```typescript
// webpack.config.js for widget bundles
const path = require('path');

module.exports = {
  entry: './src/widgets/index.ts',
  output: {
    path: path.resolve(__dirname, 'dist/widgets'),
    filename: '[name].[contenthash].js',
    library: 'CortexWidgets',
    libraryTarget: 'umd',
  },
  externals: {
    'react': 'React',
    'react-dom': 'ReactDOM',
    'styled-components': 'styled',
  },
  module: {
    rules: [
      {
        test: /\.tsx?$/,
        use: 'ts-loader',
        exclude: /node_modules/,
      },
      {
        test: /\.css$/,
        use: ['style-loader', 'css-loader'],
      },
    ],
  },
  optimization: {
    splitChunks: {
      chunks: 'all',
      cacheGroups: {
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          chunks: 'all',
        },
      },
    },
  },
};
```

### Widget Packaging

```json
{
  "name": "@cortex-dash/custom-widgets",
  "version": "1.0.0",
  "description": "Custom widgets for Cortex Dashboard Platform",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "files": [
    "dist",
    "README.md"
  ],
  "scripts": {
    "build": "webpack --mode production",
    "build:dev": "webpack --mode development",
    "type-check": "tsc --noEmit",
    "test": "jest",
    "package": "npm run build && npm pack"
  },
  "peerDependencies": {
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "styled-components": "^5.3.0"
  },
  "devDependencies": {
    "@types/react": "^19.0.0",
    "typescript": "^5.0.0",
    "webpack": "^5.0.0"
  }
}
```

### Distribution Methods

#### NPM Package Distribution
```bash
# Build and publish widget package
npm run build
npm version patch
npm publish --access public

# Install in target project
npm install @cortex-dash/custom-widgets
```

#### CDN Distribution
```html
<!-- Load widget bundle from CDN -->
<script src="https://cdn.cortexdash.com/widgets/v1/custom-widgets.min.js"></script>
<script>
  // Register widgets
  CortexWidgets.registerAll();
</script>
```

#### Dynamic Loading
```typescript
// Dynamic widget loading
export const loadWidget = async (widgetType: string, version?: string) => {
  const widgetUrl = `https://widgets.cortexdash.com/${widgetType}/${version || 'latest'}/index.js`;
  
  try {
    const module = await import(widgetUrl);
    return module.default;
  } catch (error) {
    console.error(`Failed to load widget: ${widgetType}`, error);
    throw error;
  }
};

// Usage in widget registry
const registerDynamicWidget = async (type: string) => {
  const WidgetComponent = await loadWidget(type);
  WidgetRegistry.register({
    type,
    component: WidgetComponent,
    // ... other registration options
  });
};
```

## Advanced Topics

### Custom Data Sources

```typescript
// Custom data source adapter
export interface DataSourceAdapter {
  connect(): Promise<void>;
  disconnect(): Promise<void>;
  fetchData(query: DataQuery): Promise<any[]>;
  validateQuery(query: DataQuery): ValidationResult;
}

export class CustomDataSourceAdapter implements DataSourceAdapter {
  private connection: any;

  async connect(): Promise<void> {
    // Implement connection logic
  }

  async disconnect(): Promise<void> {
    // Implement disconnection logic
  }

  async fetchData(query: DataQuery): Promise<any[]> {
    // Implement data fetching logic
    return [];
  }

  validateQuery(query: DataQuery): ValidationResult {
    // Implement query validation
    return { isValid: true, errors: [] };
  }
}

// Register custom data source
DataSourceRegistry.register('custom-api', CustomDataSourceAdapter);
```

### Advanced Interactions

```typescript
// Advanced widget interaction system
export class WidgetInteractionManager {
  private subscribers = new Map<string, Function[]>();

  subscribe(eventType: string, callback: Function): () => void {
    if (!this.subscribers.has(eventType)) {
      this.subscribers.set(eventType, []);
    }
    
    this.subscribers.get(eventType)!.push(callback);
    
    // Return unsubscribe function
    return () => {
      const callbacks = this.subscribers.get(eventType);
      if (callbacks) {
        const index = callbacks.indexOf(callback);
        if (index > -1) {
          callbacks.splice(index, 1);
        }
      }
    };
  }

  emit(eventType: string, data: any): void {
    const callbacks = this.subscribers.get(eventType);
    if (callbacks) {
      callbacks.forEach(callback => callback(data));
    }
  }

  // Advanced interaction patterns
  setupCrossFiltering(sourceWidget: string, targetWidgets: string[]): void {
    this.subscribe(`${sourceWidget}:filter`, (filterData) => {
      targetWidgets.forEach(target => {
        this.emit(`${target}:apply-filter`, filterData);
      });
    });
  }

  setupDrillDownChain(widgets: string[]): void {
    widgets.forEach((widget, index) => {
      if (index < widgets.length - 1) {
        this.subscribe(`${widget}:drill-down`, (data) => {
          this.emit(`${widgets[index + 1]}:load-data`, data);
        });
      }
    });
  }
}
```

### Plugin Architecture

```typescript
// Widget plugin system
export interface WidgetPlugin {
  name: string;
  version: string;
  install(widgetInstance: any): void;
  uninstall(widgetInstance: any): void;
}

export class ExportPlugin implements WidgetPlugin {
  name = 'export-plugin';
  version = '1.0.0';

  install(widgetInstance: any): void {
    widgetInstance.addAction({
      id: 'export-data',
      label: 'Export Data',
      icon: 'download',
      handler: this.handleExport.bind(this)
    });
  }

  uninstall(widgetInstance: any): void {
    widgetInstance.removeAction('export-data');
  }

  private async handleExport(widget: any): Promise<void> {
    const data = widget.getData();
    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: 'application/json'
    });
    
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${widget.title}-data.json`;
    a.click();
    
    URL.revokeObjectURL(url);
  }
}

// Plugin manager
export class PluginManager {
  private plugins = new Map<string, WidgetPlugin>();
  private installedPlugins = new Map<string, Set<string>>();

  registerPlugin(plugin: WidgetPlugin): void {
    this.plugins.set(plugin.name, plugin);
  }

  installPlugin(widgetId: string, pluginName: string): void {
    const plugin = this.plugins.get(pluginName);
    if (!plugin) {
      throw new Error(`Plugin not found: ${pluginName}`);
    }

    const widget = WidgetRegistry.getInstance(widgetId);
    if (!widget) {
      throw new Error(`Widget not found: ${widgetId}`);
    }

    plugin.install(widget);

    if (!this.installedPlugins.has(widgetId)) {
      this.installedPlugins.set(widgetId, new Set());
    }
    this.installedPlugins.get(widgetId)!.add(pluginName);
  }

  uninstallPlugin(widgetId: string, pluginName: string): void {
    const plugin = this.plugins.get(pluginName);
    const widget = WidgetRegistry.getInstance(widgetId);
    
    if (plugin && widget) {
      plugin.uninstall(widget);
      this.installedPlugins.get(widgetId)?.delete(pluginName);
    }
  }
}
```

## Best Practices

### Code Organization

1. **Modular Structure**: Keep each widget in its own directory with clear separation of concerns
2. **TypeScript Types**: Define comprehensive types for configuration and data
3. **Error Boundaries**: Implement error boundaries to prevent widget crashes from affecting the entire dashboard
4. **Consistent Naming**: Use consistent naming conventions across all widgets

### Performance Guidelines

1. **Lazy Loading**: Implement lazy loading for widgets and their dependencies
2. **Memoization**: Use React.memo and useMemo for expensive operations
3. **Virtual Scrolling**: Implement virtual scrolling for large datasets
4. **Debouncing**: Debounce user interactions and API calls

### Security Considerations

1. **Input Validation**: Validate all configuration inputs
2. **XSS Prevention**: Sanitize user-provided content
3. **CSRF Protection**: Implement CSRF protection for API calls
4. **Content Security Policy**: Follow CSP guidelines for dynamic content

### Testing Strategy

1. **Unit Tests**: Test individual widget components and functions
2. **Integration Tests**: Test widget interactions with the platform
3. **Visual Regression Tests**: Use Storybook for visual testing
4. **Performance Tests**: Monitor rendering performance and memory usage

### Documentation

1. **API Documentation**: Document all configuration options and data formats
2. **Usage Examples**: Provide clear usage examples and tutorials
3. **Migration Guides**: Document breaking changes and migration paths
4. **Troubleshooting**: Include common issues and solutions

---

## Quick Reference

### Widget Development Checklist
- [ ] Create widget component with proper TypeScript types
- [ ] Implement configuration schema
- [ ] Add validation and error handling
- [ ] Create Storybook stories
- [ ] Write comprehensive tests
- [ ] Optimize for performance
- [ ] Document configuration options
- [ ] Register widget with platform

### Essential Files for New Widget
```
src/components/widgets/my-widget/
├── index.ts                 # Exports
├── my-widget.tsx           # Component
├── my-widget.types.ts      # Types
├── my-widget.config.ts     # Schema
├── my-widget.styles.ts     # Styles
├── my-widget.stories.tsx   # Stories
└── my-widget.test.tsx      # Tests
```

### Key Interfaces to Implement
- `WidgetComponent<TConfig, TData>`
- `WidgetConfigSchema<TConfig>`
- `validateConfiguration(config): ValidationResult`
- `generatePreviewData(config): TData`

### Development Commands
```bash
npm run dev          # Start development server
npm run storybook    # Start Storybook
npm run test         # Run tests
npm run build        # Build for production
npm run type-check   # TypeScript validation
```

---

*This guide provides comprehensive coverage of widget development. For specific technical questions or advanced use cases, consult the API documentation or contact the development team.*