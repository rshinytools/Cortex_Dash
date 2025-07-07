// ABOUTME: Widget registration index that registers all available widgets
// ABOUTME: Import and register new widgets here

import { WidgetRegistry } from './widget-registry';
import { MetricCard } from './metric-card';
import { LineChart } from './line-chart';
import { BarChart } from './bar-chart';
import { PieChart } from './pie-chart';
import { DataTable } from './data-table';
import { EnrollmentMap } from './enrollment-map';
import { SafetyMetrics } from './safety-metrics';
import { QueryMetrics } from './query-metrics';
import { ScatterPlot } from './scatter-plot';
import { Heatmap } from './heatmap';
import { KpiComparison } from './kpi-comparison';
import { PatientTimeline } from './patient-timeline';

// Register all widgets
export function registerAllWidgets() {
  // Basic widgets
  WidgetRegistry.register({
    type: 'metric-card',
    component: MetricCard,
    name: 'Metric Card',
    description: 'Display a single metric with trend',
    category: 'Basic',
    configSchema: {
      format: { type: 'string', enum: ['number', 'percentage', 'currency', 'decimal'] },
      decimals: { type: 'number', min: 0, max: 4 },
      showTrend: { type: 'boolean' },
    },
  });

  WidgetRegistry.register({
    type: 'line-chart',
    component: LineChart,
    name: 'Line Chart',
    description: 'Time series data visualization',
    category: 'Charts',
    configSchema: {
      xAxisField: { type: 'string', required: true },
      yAxisFields: { type: 'array', required: true },
      dateFormat: { type: 'string' },
      showLegend: { type: 'boolean' },
    },
  });

  WidgetRegistry.register({
    type: 'bar-chart',
    component: BarChart,
    name: 'Bar Chart',
    description: 'Categorical data comparison',
    category: 'Charts',
    configSchema: {
      xAxisField: { type: 'string', required: true },
      yAxisFields: { type: 'array', required: true },
      orientation: { type: 'string', enum: ['horizontal', 'vertical'] },
      showValues: { type: 'boolean' },
    },
  });

  WidgetRegistry.register({
    type: 'pie-chart',
    component: PieChart,
    name: 'Pie Chart',
    description: 'Distribution and proportion visualization',
    category: 'Charts',
    configSchema: {
      labelField: { type: 'string', required: true },
      valueField: { type: 'string', required: true },
      showLegend: { type: 'boolean' },
      showPercentage: { type: 'boolean' },
      innerRadius: { type: 'number', min: 0, max: 100 },
    },
  });

  WidgetRegistry.register({
    type: 'data-table',
    component: DataTable,
    name: 'Data Table',
    description: 'Tabular data display with sorting and filtering',
    category: 'Basic',
    configSchema: {
      columns: { type: 'array', required: true },
      pageSize: { type: 'number', min: 5, max: 100 },
      showPagination: { type: 'boolean' },
      showSearch: { type: 'boolean' },
    },
  });

  // Specialized widgets
  WidgetRegistry.register({
    type: 'enrollment-map',
    component: EnrollmentMap,
    name: 'Enrollment Map',
    description: 'Geographic distribution of study participants',
    category: 'Clinical',
    configSchema: {
      mapType: { type: 'string', enum: ['world', 'usa', 'europe'], required: true },
      dataField: { type: 'string', required: true },
      locationField: { type: 'string', required: true },
      showMarkers: { type: 'boolean' },
    },
  });

  WidgetRegistry.register({
    type: 'safety-metrics',
    component: SafetyMetrics,
    name: 'Safety Metrics',
    description: 'Adverse events and safety monitoring',
    category: 'Clinical',
    configSchema: {
      displayType: { 
        type: 'string', 
        enum: ['summary', 'ae-by-severity', 'ae-by-system', 'sae-timeline'],
        required: true 
      },
      showTrends: { type: 'boolean' },
    },
  });

  WidgetRegistry.register({
    type: 'query-metrics',
    component: QueryMetrics,
    name: 'Query Metrics',
    description: 'Data quality and query resolution tracking',
    category: 'Clinical',
    configSchema: {
      displayType: { 
        type: 'string', 
        enum: ['summary', 'status-breakdown', 'aging-report', 'by-form'],
        required: true 
      },
      showAverageResolutionTime: { type: 'boolean' },
    },
  });

  // Advanced visualization widgets
  WidgetRegistry.register({
    type: 'scatter-plot',
    component: ScatterPlot,
    name: 'Scatter Plot',
    description: 'Correlation analysis between two variables',
    category: 'Charts',
    configSchema: {
      xAxisField: { type: 'string', required: true },
      yAxisField: { type: 'string', required: true },
      groupByField: { type: 'string' },
      sizeField: { type: 'string' },
      showTrendLine: { type: 'boolean' },
      trendLineType: { type: 'string', enum: ['linear', 'polynomial', 'exponential'] },
    },
  });

  WidgetRegistry.register({
    type: 'heatmap',
    component: Heatmap,
    name: 'Heatmap',
    description: 'Matrix visualization with color intensity',
    category: 'Charts',
    configSchema: {
      xAxisField: { type: 'string', required: true },
      yAxisField: { type: 'string', required: true },
      valueField: { type: 'string', required: true },
      colorScale: { type: 'string', enum: ['sequential', 'diverging', 'custom'] },
      showValues: { type: 'boolean' },
      cellSize: { type: 'number', min: 20, max: 100 },
    },
  });

  WidgetRegistry.register({
    type: 'kpi-comparison',
    component: KpiComparison,
    name: 'KPI Comparison',
    description: 'Compare metrics across periods or groups',
    category: 'Clinical',
    configSchema: {
      kpiField: { type: 'string', required: true },
      comparisonType: { 
        type: 'string', 
        enum: ['period-over-period', 'group-comparison', 'target-vs-actual', 'benchmark'],
        required: true 
      },
      displayType: { type: 'string', enum: ['cards', 'table', 'progress', 'gauge'] },
      groupByField: { type: 'string' },
      showTrend: { type: 'boolean' },
      goodDirection: { type: 'string', enum: ['up', 'down'] },
    },
  });

  WidgetRegistry.register({
    type: 'patient-timeline',
    component: PatientTimeline,
    name: 'Patient Timeline',
    description: 'Chronological view of patient events',
    category: 'Clinical',
    configSchema: {
      dateField: { type: 'string', required: true },
      eventTypeField: { type: 'string', required: true },
      eventDescriptionField: { type: 'string' },
      patientIdField: { type: 'string' },
      displayType: { type: 'string', enum: ['vertical', 'horizontal', 'gantt'] },
      groupByPatient: { type: 'boolean' },
      compactMode: { type: 'boolean' },
      highlightSevere: { type: 'boolean' },
    },
  });
}

// Export all widgets and related types
export { WidgetRegistry } from './widget-registry';
export { DashboardRenderer } from './dashboard-renderer';
export { WidgetRenderer } from './widget-renderer';
export { WidgetContainer } from './widget-container';
export { DashboardViewer } from './dashboard-viewer';
export { DashboardToolbar } from './dashboard-toolbar';
export { DashboardEditMode } from './dashboard-edit-mode';
export { WidgetConfigDialog } from './widget-config-dialog';
export { WidgetPalette } from './widget-palette';
export type { 
  BaseWidgetProps, 
  WidgetComponent, 
  WidgetInstance, 
  DashboardConfiguration 
} from './base-widget';
export type { Dashboard } from './dashboard-viewer';

// Initialize widgets on import
registerAllWidgets();