// ABOUTME: Drill-down manager for handling hierarchical data navigation in widgets
// ABOUTME: Manages drill-down state, navigation history, and detail view transitions

'use client';

import React, { createContext, useContext, useReducer, useCallback, useEffect } from 'react';
import { toast } from 'sonner';
import { useFilterManager } from './filter-manager';

export interface DrillDownLevel {
  id: string;
  title: string;
  field: string;
  value: any;
  display_value?: string;
  widget_id: string;
  widget_type: string;
  level: number;
  parent_level_id?: string;
  timestamp: Date;
  context?: Record<string, any>; // Additional context data
}

export interface DrillDownPath {
  id: string;
  dashboard_id: string;
  levels: DrillDownLevel[];
  current_level: number;
  max_depth: number;
  created_at: Date;
  updated_at: Date;
}

export interface DrillDownConfig {
  widget_id: string;
  enabled: boolean;
  max_depth: number;
  drill_fields: DrillDownField[];
  detail_view_config?: {
    widget_type: string;
    config: Record<string, any>;
  };
}

export interface DrillDownField {
  field: string;
  label: string;
  target_dataset?: string;
  target_widget_type?: string;
  filter_mapping?: Record<string, string>; // Maps drill field to filter fields
  display_format?: string;
  sort_order?: 'asc' | 'desc';
}

export interface DrillDownState {
  paths: Record<string, DrillDownPath>;
  active_path_id?: string;
  widget_configs: Record<string, DrillDownConfig>;
  detail_views: Record<string, any>; // Detail view states
  navigation_history: string[]; // Path IDs in order
  last_updated: Date;
}

export interface DrillDownAction {
  type: 'START_DRILL_DOWN' | 'ADD_DRILL_LEVEL' | 'NAVIGATE_TO_LEVEL' | 
        'GO_BACK' | 'CLEAR_DRILL_DOWN' | 'SET_WIDGET_CONFIG' |
        'SET_DETAIL_VIEW' | 'CLEAR_DETAIL_VIEWS';
  payload?: any;
}

const initialState: DrillDownState = {
  paths: {},
  widget_configs: {},
  detail_views: {},
  navigation_history: [],
  last_updated: new Date(),
};

function drillDownReducer(state: DrillDownState, action: DrillDownAction): DrillDownState {
  switch (action.type) {
    case 'START_DRILL_DOWN': {
      const { dashboardId, widgetId, field, value, displayValue, context } = action.payload;
      
      const pathId = `drill_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      const levelId = `level_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      
      const level: DrillDownLevel = {
        id: levelId,
        title: displayValue || String(value),
        field,
        value,
        display_value: displayValue,
        widget_id: widgetId,
        widget_type: 'chart', // Would be determined from widget config
        level: 0,
        timestamp: new Date(),
        context,
      };

      const path: DrillDownPath = {
        id: pathId,
        dashboard_id: dashboardId,
        levels: [level],
        current_level: 0,
        max_depth: state.widget_configs[widgetId]?.max_depth || 5,
        created_at: new Date(),
        updated_at: new Date(),
      };

      return {
        ...state,
        paths: {
          ...state.paths,
          [pathId]: path,
        },
        active_path_id: pathId,
        navigation_history: [...state.navigation_history, pathId],
        last_updated: new Date(),
      };
    }

    case 'ADD_DRILL_LEVEL': {
      const { pathId, field, value, displayValue, widgetType, context } = action.payload;
      const path = state.paths[pathId];
      
      if (!path) return state;

      const levelId = `level_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      const newLevel: DrillDownLevel = {
        id: levelId,
        title: displayValue || String(value),
        field,
        value,
        display_value: displayValue,
        widget_id: path.levels[0].widget_id,
        widget_type: widgetType || 'table',
        level: path.current_level + 1,
        parent_level_id: path.levels[path.current_level].id,
        timestamp: new Date(),
        context,
      };

      const updatedPath: DrillDownPath = {
        ...path,
        levels: [...path.levels, newLevel],
        current_level: path.current_level + 1,
        updated_at: new Date(),
      };

      return {
        ...state,
        paths: {
          ...state.paths,
          [pathId]: updatedPath,
        },
        last_updated: new Date(),
      };
    }

    case 'NAVIGATE_TO_LEVEL': {
      const { pathId, level } = action.payload;
      const path = state.paths[pathId];
      
      if (!path || level < 0 || level >= path.levels.length) return state;

      const updatedPath: DrillDownPath = {
        ...path,
        current_level: level,
        updated_at: new Date(),
      };

      return {
        ...state,
        paths: {
          ...state.paths,
          [pathId]: updatedPath,
        },
        last_updated: new Date(),
      };
    }

    case 'GO_BACK': {
      const { pathId } = action.payload;
      const path = state.paths[pathId];
      
      if (!path || path.current_level <= 0) return state;

      const updatedPath: DrillDownPath = {
        ...path,
        current_level: path.current_level - 1,
        updated_at: new Date(),
      };

      return {
        ...state,
        paths: {
          ...state.paths,
          [pathId]: updatedPath,
        },
        last_updated: new Date(),
      };
    }

    case 'CLEAR_DRILL_DOWN': {
      const { pathId } = action.payload;
      if (!pathId) {
        // Clear all drill downs
        return {
          ...state,
          paths: {},
          active_path_id: undefined,
          detail_views: {},
          navigation_history: [],
          last_updated: new Date(),
        };
      }

      const newPaths = { ...state.paths };
      delete newPaths[pathId];

      const newDetailViews = { ...state.detail_views };
      delete newDetailViews[pathId];

      return {
        ...state,
        paths: newPaths,
        active_path_id: state.active_path_id === pathId ? undefined : state.active_path_id,
        detail_views: newDetailViews,
        navigation_history: state.navigation_history.filter(id => id !== pathId),
        last_updated: new Date(),
      };
    }

    case 'SET_WIDGET_CONFIG': {
      const { widgetId, config } = action.payload;
      return {
        ...state,
        widget_configs: {
          ...state.widget_configs,
          [widgetId]: config,
        },
        last_updated: new Date(),
      };
    }

    case 'SET_DETAIL_VIEW': {
      const { pathId, data } = action.payload;
      return {
        ...state,
        detail_views: {
          ...state.detail_views,
          [pathId]: data,
        },
        last_updated: new Date(),
      };
    }

    case 'CLEAR_DETAIL_VIEWS': {
      return {
        ...state,
        detail_views: {},
        last_updated: new Date(),
      };
    }

    default:
      return state;
  }
}

interface DrillDownManagerContextType {
  state: DrillDownState;
  startDrillDown: (widgetId: string, field: string, value: any, displayValue?: string, context?: Record<string, any>) => string;
  addDrillLevel: (pathId: string, field: string, value: any, displayValue?: string, widgetType?: string, context?: Record<string, any>) => void;
  navigateToLevel: (pathId: string, level: number) => void;
  goBack: (pathId?: string) => void;
  clearDrillDown: (pathId?: string) => void;
  setWidgetDrillConfig: (widgetId: string, config: DrillDownConfig) => void;
  setDetailView: (pathId: string, data: any) => void;
  clearDetailViews: () => void;
  getActivePath: () => DrillDownPath | null;
  getCurrentLevel: (pathId?: string) => DrillDownLevel | null;
  getBreadcrumbs: (pathId?: string) => DrillDownLevel[];
  canDrillDown: (widgetId: string) => boolean;
  canGoDeeper: (pathId?: string) => boolean;
}

const DrillDownManagerContext = createContext<DrillDownManagerContextType | null>(null);

export function useDrillDownManager() {
  const context = useContext(DrillDownManagerContext);
  if (!context) {
    throw new Error('useDrillDownManager must be used within a DrillDownManagerProvider');
  }
  return context;
}

interface DrillDownManagerProviderProps {
  children: React.ReactNode;
  dashboardId: string;
  onDrillDown?: (path: DrillDownPath) => void;
  onNavigate?: (level: DrillDownLevel) => void;
}

export function DrillDownManagerProvider({
  children,
  dashboardId,
  onDrillDown,
  onNavigate,
}: DrillDownManagerProviderProps) {
  const [state, dispatch] = useReducer(drillDownReducer, initialState);
  const { applyTemporaryFilters, clearTemporaryFilters } = useFilterManager();

  // Start a new drill-down
  const startDrillDown = useCallback((
    widgetId: string,
    field: string,
    value: any,
    displayValue?: string,
    context?: Record<string, any>
  ) => {
    // Clear any existing temporary filters
    clearTemporaryFilters();

    dispatch({
      type: 'START_DRILL_DOWN',
      payload: {
        dashboardId,
        widgetId,
        field,
        value,
        displayValue,
        context,
      },
    });

    // Apply filter for the drill-down
    const filters = [{
      field,
      label: `Drill-down: ${displayValue || String(value)}`,
      type: 'string' as const,
      scope: 'dashboard' as const,
      values: [{
        value,
        label: displayValue || String(value),
        operator: 'eq' as const,
      }],
      widget_bindings: [],
      active: true,
      temporary: true,
    }];

    applyTemporaryFilters(filters);

    // Generate unique ID for this drill-down path
    const pathId = `drill_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    toast.success(`Drilling down: ${displayValue || String(value)}`, {
      description: `Viewing detailed data for ${field}`,
      duration: 3000,
    });

    return pathId;
  }, [dashboardId, applyTemporaryFilters, clearTemporaryFilters]);

  // Add a new level to existing drill-down
  const addDrillLevel = useCallback((
    pathId: string,
    field: string,
    value: any,
    displayValue?: string,
    widgetType?: string,
    context?: Record<string, any>
  ) => {
    const path = state.paths[pathId];
    if (!path) return;

    // Check depth limit
    if (path.current_level >= path.max_depth - 1) {
      toast.warning('Maximum drill-down depth reached');
      return;
    }

    dispatch({
      type: 'ADD_DRILL_LEVEL',
      payload: {
        pathId,
        field,
        value,
        displayValue,
        widgetType,
        context,
      },
    });

    // Apply additional filter
    const filters = [{
      field,
      label: `Drill-down: ${displayValue || String(value)}`,
      type: 'string' as const,
      scope: 'dashboard' as const,
      values: [{
        value,
        label: displayValue || String(value),
        operator: 'eq' as const,
      }],
      widget_bindings: [],
      active: true,
      temporary: true,
    }];

    applyTemporaryFilters(filters);

    toast.success(`Drilling deeper: ${displayValue || String(value)}`);
  }, [state.paths, applyTemporaryFilters]);

  // Navigate to specific level
  const navigateToLevel = useCallback((pathId: string, level: number) => {
    dispatch({
      type: 'NAVIGATE_TO_LEVEL',
      payload: { pathId, level },
    });

    if (onNavigate) {
      const path = state.paths[pathId];
      if (path && path.levels[level]) {
        onNavigate(path.levels[level]);
      }
    }
  }, [state.paths, onNavigate]);

  // Go back one level
  const goBack = useCallback((pathId?: string) => {
    const targetPathId = pathId || state.active_path_id;
    if (!targetPathId) return;

    const path = state.paths[targetPathId];
    if (!path || path.current_level <= 0) return;

    dispatch({
      type: 'GO_BACK',
      payload: { pathId: targetPathId },
    });

    toast.info('Navigated back one level');
  }, [state.paths, state.active_path_id]);

  // Clear drill-down
  const clearDrillDown = useCallback((pathId?: string) => {
    if (!pathId) {
      clearTemporaryFilters();
    }

    dispatch({
      type: 'CLEAR_DRILL_DOWN',
      payload: { pathId },
    });

    toast.info(pathId ? 'Drill-down cleared' : 'All drill-downs cleared');
  }, [clearTemporaryFilters]);

  // Set widget drill configuration
  const setWidgetDrillConfig = useCallback((widgetId: string, config: DrillDownConfig) => {
    dispatch({
      type: 'SET_WIDGET_CONFIG',
      payload: { widgetId, config },
    });
  }, []);

  // Set detail view data
  const setDetailView = useCallback((pathId: string, data: any) => {
    dispatch({
      type: 'SET_DETAIL_VIEW',
      payload: { pathId, data },
    });
  }, []);

  // Clear detail views
  const clearDetailViews = useCallback(() => {
    dispatch({ type: 'CLEAR_DETAIL_VIEWS' });
  }, []);

  // Get active drill-down path
  const getActivePath = useCallback(() => {
    if (!state.active_path_id) return null;
    return state.paths[state.active_path_id] || null;
  }, [state.active_path_id, state.paths]);

  // Get current level
  const getCurrentLevel = useCallback((pathId?: string) => {
    const targetPathId = pathId || state.active_path_id;
    if (!targetPathId) return null;

    const path = state.paths[targetPathId];
    if (!path) return null;

    return path.levels[path.current_level] || null;
  }, [state.paths, state.active_path_id]);

  // Get breadcrumbs for navigation
  const getBreadcrumbs = useCallback((pathId?: string) => {
    const targetPathId = pathId || state.active_path_id;
    if (!targetPathId) return [];

    const path = state.paths[targetPathId];
    if (!path) return [];

    return path.levels.slice(0, path.current_level + 1);
  }, [state.paths, state.active_path_id]);

  // Check if widget can drill down
  const canDrillDown = useCallback((widgetId: string) => {
    const config = state.widget_configs[widgetId];
    return config?.enabled && config.drill_fields.length > 0;
  }, [state.widget_configs]);

  // Check if can go deeper
  const canGoDeeper = useCallback((pathId?: string) => {
    const targetPathId = pathId || state.active_path_id;
    if (!targetPathId) return false;

    const path = state.paths[targetPathId];
    if (!path) return false;

    return path.current_level < path.max_depth - 1;
  }, [state.paths, state.active_path_id]);

  // Notify about drill-down changes
  useEffect(() => {
    if (onDrillDown && state.active_path_id) {
      const path = state.paths[state.active_path_id];
      if (path) {
        onDrillDown(path);
      }
    }
  }, [state.active_path_id, state.paths, onDrillDown]);

  const contextValue: DrillDownManagerContextType = {
    state,
    startDrillDown,
    addDrillLevel,
    navigateToLevel,
    goBack,
    clearDrillDown,
    setWidgetDrillConfig,
    setDetailView,
    clearDetailViews,
    getActivePath,
    getCurrentLevel,
    getBreadcrumbs,
    canDrillDown,
    canGoDeeper,
  };

  return (
    <DrillDownManagerContext.Provider value={contextValue}>
      {children}
    </DrillDownManagerContext.Provider>
  );
}

// Hook for widgets to handle drill-down interactions
export function useWidgetDrillDown(widgetId: string) {
  const {
    startDrillDown,
    addDrillLevel,
    canDrillDown,
    setWidgetDrillConfig,
    state,
  } = useDrillDownManager();

  // Initialize widget drill configuration
  useEffect(() => {
    // Set default drill configuration for widget
    // In a real app, this would come from widget definition or user configuration
    const defaultConfig: DrillDownConfig = {
      widget_id: widgetId,
      enabled: true,
      max_depth: 3,
      drill_fields: [
        { field: 'SITEID', label: 'Site' },
        { field: 'USUBJID', label: 'Subject' },
        { field: 'VISITNUM', label: 'Visit' },
      ],
    };

    if (!state.widget_configs[widgetId]) {
      setWidgetDrillConfig(widgetId, defaultConfig);
    }
  }, [widgetId, setWidgetDrillConfig, state.widget_configs]);

  // Handle click on data point for drill-down
  const handleDataPointClick = useCallback((field: string, value: any, displayValue?: string) => {
    if (!canDrillDown(widgetId)) return;

    const config = state.widget_configs[widgetId];
    if (!config) return;

    // Check if field is configured for drill-down
    const drillField = config.drill_fields.find(df => df.field === field);
    if (!drillField) return;

    return startDrillDown(widgetId, field, value, displayValue);
  }, [widgetId, canDrillDown, state.widget_configs, startDrillDown]);

  return {
    canDrillDown: canDrillDown(widgetId),
    handleDataPointClick,
    drillConfig: state.widget_configs[widgetId],
  };
}