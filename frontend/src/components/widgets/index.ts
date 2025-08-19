// ABOUTME: Widget system exports - provides the core widget infrastructure
// ABOUTME: Uses dynamic loading with registry pattern for enterprise scalability

// Core widget system exports
export { WidgetRegistry } from './widget-registry';
export { WidgetRenderer } from './widget-renderer';
export { initializeWidgetSystem, ensureWidgetLoaded } from './widget-loader';

// Widget base types and utilities
export type { 
  BaseWidgetProps,
  WidgetInstance,
  WidgetDefinition,
  WidgetComponent,
  DataRequirement,
  WidgetExportFormat
} from './base-widget';

export {
  exportWidgetDataAsCSV,
  exportWidgetDataAsJSON,
  exportWidgetAsImage
} from './base-widget';