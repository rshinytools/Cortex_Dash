// ABOUTME: Dynamic widget loader that automatically registers widgets based on backend definitions
// ABOUTME: Provides enterprise-level widget management with lazy loading and caching

import { WidgetRegistry } from './widget-registry';
import { WidgetComponent } from './base-widget';

// Map of widget types to their implementations
// This ensures type safety and allows for lazy loading
const WIDGET_IMPLEMENTATIONS: Record<string, () => Promise<{ default: WidgetComponent }>> = {
  // Primary widget types matching backend definitions
  'kpi_card': () => import('./implementations/kpi-card'),
  
  // TODO: Add more widget implementations as they are created
  // 'time_series_chart': () => import('./implementations/time-series-chart'),
  // 'distribution_chart': () => import('./implementations/distribution-chart'),
  // 'data_table': () => import('./implementations/data-table'),
  // 'subject_timeline': () => import('./implementations/subject-timeline'),
};

// Aliases for backward compatibility or alternative names
// These map to the primary implementations above
const WIDGET_ALIASES: Record<string, string> = {
  'metric-card': 'kpi_card',
  'kpi_metric_card': 'kpi_card',
  'metric_card': 'kpi_card',
};

// Cache for loaded widget components
const loadedWidgets = new Map<string, WidgetComponent>();

/**
 * Load and register a widget by type
 * This function is idempotent - calling it multiple times with the same type is safe
 */
export async function loadWidget(type: string): Promise<WidgetComponent | null> {
  // Check if this is an alias
  const actualType = WIDGET_ALIASES[type] || type;
  
  // Check if already loaded
  if (loadedWidgets.has(actualType)) {
    // Register the alias as well if needed
    if (type !== actualType && !WidgetRegistry.get(type)) {
      const component = loadedWidgets.get(actualType)!;
      WidgetRegistry.register({
        type,
        component,
        name: component.displayName || type,
        description: `Alias for ${actualType}`,
        category: 'Dynamic',
        configSchema: component.configSchema
      });
    }
    return loadedWidgets.get(actualType)!;
  }

  // Check if implementation exists
  const loader = WIDGET_IMPLEMENTATIONS[actualType];
  if (!loader) {
    console.warn(`No implementation found for widget type: ${type} (resolved to ${actualType})`);
    return null;
  }

  try {
    // Dynamically import the widget
    // eslint-disable-next-line @next/next/no-assign-module-variable
    const module = await loader();
    const component = module.default;
    
    // Cache the component with the actual type
    loadedWidgets.set(actualType, component);
    
    // Register the primary type
    WidgetRegistry.register({
      type: actualType,
      component,
      name: component.displayName || actualType,
      description: `Widget of type ${actualType}`,
      category: 'Dynamic',
      configSchema: component.configSchema
    });
    
    // If this was called with an alias, register that too
    if (type !== actualType) {
      WidgetRegistry.register({
        type,
        component,
        name: component.displayName || type,
        description: `Alias for ${actualType}`,
        category: 'Dynamic',
        configSchema: component.configSchema
      });
    }
    
    console.log(`Successfully loaded widget: ${actualType}${type !== actualType ? ` (via alias ${type})` : ''}`);
    return component;
  } catch (error) {
    console.error(`Failed to load widget ${type}:`, error);
    return null;
  }
}

/**
 * Load all available widgets
 * This should be called on application startup
 */
export async function loadAllWidgets(): Promise<void> {
  const types = Object.keys(WIDGET_IMPLEMENTATIONS);
  const aliases = Object.keys(WIDGET_ALIASES);
  
  console.log(`Loading ${types.length} widget types and ${aliases.length} aliases...`);
  
  // Load primary widget types first
  const results = await Promise.allSettled(
    types.map(type => loadWidget(type))
  );
  
  // Then register aliases (they'll use cached components)
  await Promise.allSettled(
    aliases.map(alias => loadWidget(alias))
  );
  
  // Log results
  const successful = results.filter(r => r.status === 'fulfilled' && r.value !== null).length;
  const failed = results.filter(r => r.status === 'rejected' || (r.status === 'fulfilled' && r.value === null)).length;
  
  console.log(`Widget loading complete: ${successful} widget types loaded, ${aliases.length} aliases registered`);
}

/**
 * Ensure a widget is loaded before rendering
 * This is useful for on-demand loading of widgets
 */
export async function ensureWidgetLoaded(type: string): Promise<boolean> {
  const component = await loadWidget(type);
  return component !== null;
}

/**
 * Get widget metadata from backend and register dynamically
 * This allows for server-driven widget configuration
 */
export async function syncWidgetsWithBackend(): Promise<void> {
  try {
    const response = await fetch('/api/v1/admin/widgets');
    if (!response.ok) {
      throw new Error('Failed to fetch widget definitions');
    }
    
    const { data: widgets } = await response.json();
    
    for (const widget of widgets) {
      // Check if we have an implementation for this widget
      if (WIDGET_IMPLEMENTATIONS[widget.code]) {
        await loadWidget(widget.code);
      } else {
        console.warn(`Backend widget ${widget.code} has no frontend implementation`);
      }
    }
  } catch (error) {
    console.error('Failed to sync widgets with backend:', error);
  }
}

/**
 * Initialize the widget system
 * This should be called once when the application starts
 */
export async function initializeWidgetSystem(): Promise<void> {
  console.log('Initializing widget system...');
  
  // Load all known widgets
  await loadAllWidgets();
  
  // Optionally sync with backend
  // await syncWidgetsWithBackend();
  
  console.log('Widget system initialized');
}