// ABOUTME: Central filter manager for coordinating filters across all widgets in a dashboard
// ABOUTME: Handles filter state, propagation, and interaction events between widgets

'use client';

import React, { createContext, useContext, useReducer, useCallback, useEffect } from 'react';
import { toast } from 'sonner';

export interface FilterValue {
  value: any;
  label?: string;
  operator?: 'eq' | 'ne' | 'gt' | 'gte' | 'lt' | 'lte' | 'in' | 'not_in' | 'contains' | 'starts_with' | 'ends_with';
}

export interface FilterDefinition {
  id: string;
  field: string;
  label: string;
  type: 'string' | 'number' | 'date' | 'boolean' | 'select' | 'multi_select';
  widget_id?: string; // Widget that created this filter
  source_widget_id?: string; // Widget that triggered this filter
  scope: 'dashboard' | 'widget' | 'global'; // Filter scope
  values: FilterValue[];
  active: boolean;
  temporary?: boolean; // For drill-down filters
  created_at: Date;
  applied_at?: Date;
}

export interface FilterState {
  filters: Record<string, FilterDefinition>;
  active_filters: string[];
  filter_groups: Record<string, string[]>; // Grouped filters
  last_updated: Date;
}

export interface FilterAction {
  type: 'ADD_FILTER' | 'UPDATE_FILTER' | 'REMOVE_FILTER' | 'TOGGLE_FILTER' | 
        'CLEAR_FILTERS' | 'CLEAR_WIDGET_FILTERS' | 'SET_FILTER_GROUP' | 
        'APPLY_TEMPORARY_FILTERS' | 'CLEAR_TEMPORARY_FILTERS';
  payload?: any;
}

const initialState: FilterState = {
  filters: {},
  active_filters: [],
  filter_groups: {},
  last_updated: new Date(),
};

function filterReducer(state: FilterState, action: FilterAction): FilterState {
  switch (action.type) {
    case 'ADD_FILTER': {
      const filter = action.payload as FilterDefinition;
      const newState = {
        ...state,
        filters: {
          ...state.filters,
          [filter.id]: filter,
        },
        last_updated: new Date(),
      };

      // Auto-activate filter if it has values
      if (filter.active && filter.values.length > 0) {
        newState.active_filters = [...state.active_filters, filter.id];
        newState.filters[filter.id].applied_at = new Date();
      }

      return newState;
    }

    case 'UPDATE_FILTER': {
      const { id, updates } = action.payload;
      if (!state.filters[id]) return state;

      const updatedFilter = {
        ...state.filters[id],
        ...updates,
      };

      return {
        ...state,
        filters: {
          ...state.filters,
          [id]: updatedFilter,
        },
        last_updated: new Date(),
      };
    }

    case 'REMOVE_FILTER': {
      const { id } = action.payload;
      const newFilters = { ...state.filters };
      delete newFilters[id];

      return {
        ...state,
        filters: newFilters,
        active_filters: state.active_filters.filter(fId => fId !== id),
        last_updated: new Date(),
      };
    }

    case 'TOGGLE_FILTER': {
      const { id } = action.payload;
      if (!state.filters[id]) return state;

      const isActive = state.active_filters.includes(id);
      const newActiveFilters = isActive
        ? state.active_filters.filter(fId => fId !== id)
        : [...state.active_filters, id];

      const updatedFilter = {
        ...state.filters[id],
        active: !isActive,
        applied_at: !isActive ? new Date() : undefined,
      };

      return {
        ...state,
        filters: {
          ...state.filters,
          [id]: updatedFilter,
        },
        active_filters: newActiveFilters,
        last_updated: new Date(),
      };
    }

    case 'CLEAR_FILTERS': {
      return {
        ...state,
        filters: {},
        active_filters: [],
        filter_groups: {},
        last_updated: new Date(),
      };
    }

    case 'CLEAR_WIDGET_FILTERS': {
      const { widget_id } = action.payload;
      const newFilters = Object.fromEntries(
        Object.entries(state.filters).filter(([_, filter]) => 
          filter.widget_id !== widget_id && filter.source_widget_id !== widget_id
        )
      );

      const newActiveFilters = state.active_filters.filter(id => 
        newFilters[id] !== undefined
      );

      return {
        ...state,
        filters: newFilters,
        active_filters: newActiveFilters,
        last_updated: new Date(),
      };
    }

    case 'SET_FILTER_GROUP': {
      const { group_id, filter_ids } = action.payload;
      return {
        ...state,
        filter_groups: {
          ...state.filter_groups,
          [group_id]: filter_ids,
        },
        last_updated: new Date(),
      };
    }

    case 'APPLY_TEMPORARY_FILTERS': {
      const { filters } = action.payload;
      const newFilters = { ...state.filters };
      const newActiveFilters = [...state.active_filters];

      filters.forEach((filter: FilterDefinition) => {
        newFilters[filter.id] = { ...filter, temporary: true, active: true };
        if (!newActiveFilters.includes(filter.id)) {
          newActiveFilters.push(filter.id);
        }
      });

      return {
        ...state,
        filters: newFilters,
        active_filters: newActiveFilters,
        last_updated: new Date(),
      };
    }

    case 'CLEAR_TEMPORARY_FILTERS': {
      const newFilters = Object.fromEntries(
        Object.entries(state.filters).filter(([_, filter]) => !filter.temporary)
      );

      const newActiveFilters = state.active_filters.filter(id => 
        newFilters[id] !== undefined
      );

      return {
        ...state,
        filters: newFilters,
        active_filters: newActiveFilters,
        last_updated: new Date(),
      };
    }

    default:
      return state;
  }
}

interface FilterManagerContextType {
  state: FilterState;
  addFilter: (filter: Omit<FilterDefinition, 'id' | 'created_at'>) => string;
  updateFilter: (id: string, updates: Partial<FilterDefinition>) => void;
  removeFilter: (id: string) => void;
  toggleFilter: (id: string) => void;
  clearFilters: () => void;
  clearWidgetFilters: (widget_id: string) => void;
  setFilterGroup: (group_id: string, filter_ids: string[]) => void;
  applyTemporaryFilters: (filters: Omit<FilterDefinition, 'id' | 'created_at'>[]) => void;
  clearTemporaryFilters: () => void;
  getActiveFilters: () => FilterDefinition[];
  getFiltersForField: (field: string) => FilterDefinition[];
  getWidgetFilters: (widget_id: string) => FilterDefinition[];
  generateFilterQuery: (excludeWidgetId?: string) => Record<string, any>;
}

const FilterManagerContext = createContext<FilterManagerContextType | null>(null);

export function useFilterManager() {
  const context = useContext(FilterManagerContext);
  if (!context) {
    throw new Error('useFilterManager must be used within a FilterManagerProvider');
  }
  return context;
}

interface FilterManagerProviderProps {
  children: React.ReactNode;
  dashboardId: string;
  onFiltersChange?: (filters: FilterDefinition[]) => void;
}

export function FilterManagerProvider({ 
  children, 
  dashboardId,
  onFiltersChange 
}: FilterManagerProviderProps) {
  const [state, dispatch] = useReducer(filterReducer, initialState);

  // Generate unique filter ID
  const generateFilterId = useCallback(() => {
    return `filter_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }, []);

  // Add a new filter
  const addFilter = useCallback((filterData: Omit<FilterDefinition, 'id' | 'created_at'>) => {
    const id = generateFilterId();
    const filter: FilterDefinition = {
      ...filterData,
      id,
      created_at: new Date(),
    };

    dispatch({ type: 'ADD_FILTER', payload: filter });
    
    // Notify about filter addition
    if (filter.active && filter.values.length > 0) {
      toast.success(`Filter applied: ${filter.label}`, {
        description: `${filter.values.length} value(s) selected`,
        duration: 3000,
      });
    }

    return id;
  }, [generateFilterId]);

  // Update existing filter
  const updateFilter = useCallback((id: string, updates: Partial<FilterDefinition>) => {
    dispatch({ type: 'UPDATE_FILTER', payload: { id, updates } });
  }, []);

  // Remove filter
  const removeFilter = useCallback((id: string) => {
    const filter = state.filters[id];
    if (filter) {
      dispatch({ type: 'REMOVE_FILTER', payload: { id } });
      toast.info(`Filter removed: ${filter.label}`);
    }
  }, [state.filters]);

  // Toggle filter active state
  const toggleFilter = useCallback((id: string) => {
    const filter = state.filters[id];
    if (filter) {
      dispatch({ type: 'TOGGLE_FILTER', payload: { id } });
      
      const newState = !filter.active;
      toast.success(
        `Filter ${newState ? 'enabled' : 'disabled'}: ${filter.label}`,
        { duration: 2000 }
      );
    }
  }, [state.filters]);

  // Clear all filters
  const clearFilters = useCallback(() => {
    dispatch({ type: 'CLEAR_FILTERS' });
    toast.info('All filters cleared');
  }, []);

  // Clear filters for specific widget
  const clearWidgetFilters = useCallback((widget_id: string) => {
    dispatch({ type: 'CLEAR_WIDGET_FILTERS', payload: { widget_id } });
  }, []);

  // Set filter group
  const setFilterGroup = useCallback((group_id: string, filter_ids: string[]) => {
    dispatch({ type: 'SET_FILTER_GROUP', payload: { group_id, filter_ids } });
  }, []);

  // Apply temporary filters (for drill-down)
  const applyTemporaryFilters = useCallback((filters: Omit<FilterDefinition, 'id' | 'created_at'>[]) => {
    const filtersWithIds = filters.map(filter => ({
      ...filter,
      id: generateFilterId(),
      created_at: new Date(),
    }));

    dispatch({ type: 'APPLY_TEMPORARY_FILTERS', payload: { filters: filtersWithIds } });
    
    toast.info(`${filters.length} drill-down filter(s) applied`, {
      duration: 3000,
    });
  }, [generateFilterId]);

  // Clear temporary filters
  const clearTemporaryFilters = useCallback(() => {
    dispatch({ type: 'CLEAR_TEMPORARY_FILTERS' });
    toast.info('Drill-down filters cleared');
  }, []);

  // Get active filters
  const getActiveFilters = useCallback(() => {
    return state.active_filters
      .map(id => state.filters[id])
      .filter(Boolean);
  }, [state.active_filters, state.filters]);

  // Get filters for specific field
  const getFiltersForField = useCallback((field: string) => {
    return Object.values(state.filters).filter(filter => filter.field === field);
  }, [state.filters]);

  // Get filters for specific widget
  const getWidgetFilters = useCallback((widget_id: string) => {
    return Object.values(state.filters).filter(filter => 
      filter.widget_id === widget_id || filter.source_widget_id === widget_id
    );
  }, [state.filters]);

  // Generate query object for API calls
  const generateFilterQuery = useCallback((excludeWidgetId?: string) => {
    const activeFilters = getActiveFilters().filter(filter => 
      filter.widget_id !== excludeWidgetId && filter.source_widget_id !== excludeWidgetId
    );

    const query: Record<string, any> = {};

    activeFilters.forEach(filter => {
      if (filter.values.length === 0) return;

      const fieldQuery: any = {};
      
      if (filter.values.length === 1) {
        const value = filter.values[0];
        const operator = value.operator || 'eq';
        
        switch (operator) {
          case 'eq':
            fieldQuery.$eq = value.value;
            break;
          case 'ne':
            fieldQuery.$ne = value.value;
            break;
          case 'gt':
            fieldQuery.$gt = value.value;
            break;
          case 'gte':
            fieldQuery.$gte = value.value;
            break;
          case 'lt':
            fieldQuery.$lt = value.value;
            break;
          case 'lte':
            fieldQuery.$lte = value.value;
            break;
          case 'contains':
            fieldQuery.$contains = value.value;
            break;
          case 'starts_with':
            fieldQuery.$startsWith = value.value;
            break;
          case 'ends_with':
            fieldQuery.$endsWith = value.value;
            break;
          default:
            fieldQuery.$eq = value.value;
        }
      } else {
        // Multiple values - use $in
        const values = filter.values.map(v => v.value);
        fieldQuery.$in = values;
      }

      query[filter.field] = fieldQuery;
    });

    return query;
  }, [getActiveFilters]);

  // Notify about filter changes
  useEffect(() => {
    if (onFiltersChange) {
      onFiltersChange(getActiveFilters());
    }
  }, [state.last_updated, onFiltersChange, getActiveFilters]);

  const contextValue: FilterManagerContextType = {
    state,
    addFilter,
    updateFilter,
    removeFilter,
    toggleFilter,
    clearFilters,
    clearWidgetFilters,
    setFilterGroup,
    applyTemporaryFilters,
    clearTemporaryFilters,
    getActiveFilters,
    getFiltersForField,
    getWidgetFilters,
    generateFilterQuery,
  };

  return (
    <FilterManagerContext.Provider value={contextValue}>
      {children}
    </FilterManagerContext.Provider>
  );
}

// Hook for widgets to subscribe to filter changes
export function useWidgetFilters(widgetId: string) {
  const { state, generateFilterQuery } = useFilterManager();

  const relevantFilters = Object.values(state.filters).filter(filter => 
    filter.active && 
    filter.widget_id !== widgetId && 
    filter.source_widget_id !== widgetId
  );

  const filterQuery = generateFilterQuery(widgetId);

  return {
    filters: relevantFilters,
    filterQuery,
    hasFilters: relevantFilters.length > 0,
    lastUpdated: state.last_updated,
  };
}