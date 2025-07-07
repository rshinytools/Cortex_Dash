// ABOUTME: Dashboard parameters system for global dashboard settings and variables
// ABOUTME: Manages parameter state, validation, and binding to widgets across the dashboard

'use client';

import React, { createContext, useContext, useReducer, useCallback, useEffect } from 'react';
import { toast } from 'sonner';

export interface ParameterDefinition {
  id: string;
  name: string;
  label: string;
  type: 'string' | 'number' | 'date' | 'boolean' | 'select' | 'multi_select' | 'date_range';
  description?: string;
  default_value?: any;
  current_value?: any;
  required?: boolean;
  validation?: {
    min?: number;
    max?: number;
    pattern?: string;
    options?: { value: any; label: string }[];
  };
  scope: 'global' | 'dashboard' | 'study';
  widget_bindings: string[]; // Widget IDs that use this parameter
  created_at: Date;
  updated_at: Date;
}

export interface ParameterState {
  parameters: Record<string, ParameterDefinition>;
  parameter_values: Record<string, any>;
  validation_errors: Record<string, string>;
  has_unsaved_changes: boolean;
  last_updated: Date;
}

export interface ParameterAction {
  type: 'ADD_PARAMETER' | 'UPDATE_PARAMETER' | 'REMOVE_PARAMETER' | 
        'SET_PARAMETER_VALUE' | 'SET_PARAMETER_VALUES' | 'VALIDATE_PARAMETERS' |
        'CLEAR_VALIDATION_ERRORS' | 'SAVE_PARAMETERS' | 'RESET_TO_DEFAULTS';
  payload?: any;
}

const initialState: ParameterState = {
  parameters: {},
  parameter_values: {},
  validation_errors: {},
  has_unsaved_changes: false,
  last_updated: new Date(),
};

function parameterReducer(state: ParameterState, action: ParameterAction): ParameterState {
  switch (action.type) {
    case 'ADD_PARAMETER': {
      const parameter = action.payload as ParameterDefinition;
      return {
        ...state,
        parameters: {
          ...state.parameters,
          [parameter.id]: parameter,
        },
        parameter_values: {
          ...state.parameter_values,
          [parameter.id]: parameter.current_value ?? parameter.default_value,
        },
        has_unsaved_changes: true,
        last_updated: new Date(),
      };
    }

    case 'UPDATE_PARAMETER': {
      const { id, updates } = action.payload;
      if (!state.parameters[id]) return state;

      const updatedParameter = {
        ...state.parameters[id],
        ...updates,
        updated_at: new Date(),
      };

      return {
        ...state,
        parameters: {
          ...state.parameters,
          [id]: updatedParameter,
        },
        has_unsaved_changes: true,
        last_updated: new Date(),
      };
    }

    case 'REMOVE_PARAMETER': {
      const { id } = action.payload;
      const newParameters = { ...state.parameters };
      const newParameterValues = { ...state.parameter_values };
      const newValidationErrors = { ...state.validation_errors };
      
      delete newParameters[id];
      delete newParameterValues[id];
      delete newValidationErrors[id];

      return {
        ...state,
        parameters: newParameters,
        parameter_values: newParameterValues,
        validation_errors: newValidationErrors,
        has_unsaved_changes: true,
        last_updated: new Date(),
      };
    }

    case 'SET_PARAMETER_VALUE': {
      const { id, value } = action.payload;
      if (!state.parameters[id]) return state;

      return {
        ...state,
        parameter_values: {
          ...state.parameter_values,
          [id]: value,
        },
        validation_errors: {
          ...state.validation_errors,
          [id]: '', // Clear validation error when value changes
        },
        has_unsaved_changes: true,
        last_updated: new Date(),
      };
    }

    case 'SET_PARAMETER_VALUES': {
      const { values } = action.payload;
      return {
        ...state,
        parameter_values: {
          ...state.parameter_values,
          ...values,
        },
        has_unsaved_changes: true,
        last_updated: new Date(),
      };
    }

    case 'VALIDATE_PARAMETERS': {
      const { errors } = action.payload;
      return {
        ...state,
        validation_errors: errors || {},
        last_updated: new Date(),
      };
    }

    case 'CLEAR_VALIDATION_ERRORS': {
      return {
        ...state,
        validation_errors: {},
        last_updated: new Date(),
      };
    }

    case 'SAVE_PARAMETERS': {
      return {
        ...state,
        has_unsaved_changes: false,
        last_updated: new Date(),
      };
    }

    case 'RESET_TO_DEFAULTS': {
      const defaultValues: Record<string, any> = {};
      Object.values(state.parameters).forEach(param => {
        defaultValues[param.id] = param.default_value;
      });

      return {
        ...state,
        parameter_values: defaultValues,
        validation_errors: {},
        has_unsaved_changes: true,
        last_updated: new Date(),
      };
    }

    default:
      return state;
  }
}

interface ParameterManagerContextType {
  state: ParameterState;
  addParameter: (parameter: Omit<ParameterDefinition, 'id' | 'created_at' | 'updated_at'>) => string;
  updateParameter: (id: string, updates: Partial<ParameterDefinition>) => void;
  removeParameter: (id: string) => void;
  setParameterValue: (id: string, value: any) => void;
  setParameterValues: (values: Record<string, any>) => void;
  validateParameters: () => boolean;
  clearValidationErrors: () => void;
  saveParameters: () => Promise<void>;
  resetToDefaults: () => void;
  getParameterValue: (id: string) => any;
  getParametersByWidget: (widgetId: string) => ParameterDefinition[];
  getParameterContext: () => Record<string, any>;
  bindParameterToWidget: (parameterId: string, widgetId: string) => void;
  unbindParameterFromWidget: (parameterId: string, widgetId: string) => void;
}

const ParameterManagerContext = createContext<ParameterManagerContextType | null>(null);

export function useParameterManager() {
  const context = useContext(ParameterManagerContext);
  if (!context) {
    throw new Error('useParameterManager must be used within a ParameterManagerProvider');
  }
  return context;
}

interface ParameterManagerProviderProps {
  children: React.ReactNode;
  dashboardId: string;
  initialParameters?: ParameterDefinition[];
  onParametersChange?: (parameters: Record<string, any>) => void;
  onSave?: (parameters: Record<string, any>) => Promise<void>;
}

export function ParameterManagerProvider({
  children,
  dashboardId,
  initialParameters = [],
  onParametersChange,
  onSave,
}: ParameterManagerProviderProps) {
  const [state, dispatch] = useReducer(parameterReducer, {
    ...initialState,
    parameters: initialParameters.reduce((acc, param) => {
      acc[param.id] = param;
      return acc;
    }, {} as Record<string, ParameterDefinition>),
    parameter_values: initialParameters.reduce((acc, param) => {
      acc[param.id] = param.current_value ?? param.default_value;
      return acc;
    }, {} as Record<string, any>),
  });

  // Generate unique parameter ID
  const generateParameterId = useCallback(() => {
    return `param_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }, []);

  // Add a new parameter
  const addParameter = useCallback((parameterData: Omit<ParameterDefinition, 'id' | 'created_at' | 'updated_at'>) => {
    const id = generateParameterId();
    const parameter: ParameterDefinition = {
      ...parameterData,
      id,
      created_at: new Date(),
      updated_at: new Date(),
    };

    dispatch({ type: 'ADD_PARAMETER', payload: parameter });
    return id;
  }, [generateParameterId]);

  // Update existing parameter
  const updateParameter = useCallback((id: string, updates: Partial<ParameterDefinition>) => {
    dispatch({ type: 'UPDATE_PARAMETER', payload: { id, updates } });
  }, []);

  // Remove parameter
  const removeParameter = useCallback((id: string) => {
    dispatch({ type: 'REMOVE_PARAMETER', payload: { id } });
    toast.info('Parameter removed');
  }, []);

  // Set parameter value
  const setParameterValue = useCallback((id: string, value: any) => {
    dispatch({ type: 'SET_PARAMETER_VALUE', payload: { id, value } });
  }, []);

  // Set multiple parameter values
  const setParameterValues = useCallback((values: Record<string, any>) => {
    dispatch({ type: 'SET_PARAMETER_VALUES', payload: { values } });
  }, []);

  // Validate all parameters
  const validateParameters = useCallback(() => {
    const errors: Record<string, string> = {};
    let hasErrors = false;

    Object.values(state.parameters).forEach(param => {
      const value = state.parameter_values[param.id];
      
      // Required validation
      if (param.required && (value === undefined || value === null || value === '')) {
        errors[param.id] = `${param.label} is required`;
        hasErrors = true;
        return;
      }

      // Type-specific validation
      if (value !== undefined && value !== null && value !== '') {
        switch (param.type) {
          case 'number':
            if (isNaN(Number(value))) {
              errors[param.id] = `${param.label} must be a number`;
              hasErrors = true;
            } else {
              const numValue = Number(value);
              if (param.validation?.min !== undefined && numValue < param.validation.min) {
                errors[param.id] = `${param.label} must be at least ${param.validation.min}`;
                hasErrors = true;
              }
              if (param.validation?.max !== undefined && numValue > param.validation.max) {
                errors[param.id] = `${param.label} must be at most ${param.validation.max}`;
                hasErrors = true;
              }
            }
            break;

          case 'string':
            if (param.validation?.pattern) {
              const regex = new RegExp(param.validation.pattern);
              if (!regex.test(String(value))) {
                errors[param.id] = `${param.label} format is invalid`;
                hasErrors = true;
              }
            }
            break;

          case 'select':
            if (param.validation?.options) {
              const validValues = param.validation.options.map(opt => opt.value);
              if (!validValues.includes(value)) {
                errors[param.id] = `${param.label} has an invalid value`;
                hasErrors = true;
              }
            }
            break;

          case 'multi_select':
            if (param.validation?.options && Array.isArray(value)) {
              const validValues = param.validation.options.map(opt => opt.value);
              const invalidValues = value.filter(v => !validValues.includes(v));
              if (invalidValues.length > 0) {
                errors[param.id] = `${param.label} has invalid values: ${invalidValues.join(', ')}`;
                hasErrors = true;
              }
            }
            break;

          case 'date':
            if (isNaN(Date.parse(value))) {
              errors[param.id] = `${param.label} must be a valid date`;
              hasErrors = true;
            }
            break;

          case 'date_range':
            if (Array.isArray(value) && value.length === 2) {
              const [start, end] = value;
              if (isNaN(Date.parse(start)) || isNaN(Date.parse(end))) {
                errors[param.id] = `${param.label} must have valid start and end dates`;
                hasErrors = true;
              } else if (new Date(start) > new Date(end)) {
                errors[param.id] = `${param.label} start date must be before end date`;
                hasErrors = true;
              }
            } else {
              errors[param.id] = `${param.label} must be a date range`;
              hasErrors = true;
            }
            break;
        }
      }
    });

    dispatch({ type: 'VALIDATE_PARAMETERS', payload: { errors } });
    return !hasErrors;
  }, [state.parameters, state.parameter_values]);

  // Clear validation errors
  const clearValidationErrors = useCallback(() => {
    dispatch({ type: 'CLEAR_VALIDATION_ERRORS' });
  }, []);

  // Save parameters
  const saveParameters = useCallback(async () => {
    if (!validateParameters()) {
      toast.error('Please fix validation errors before saving');
      return;
    }

    try {
      if (onSave) {
        await onSave(state.parameter_values);
      }
      dispatch({ type: 'SAVE_PARAMETERS' });
      toast.success('Parameters saved successfully');
    } catch (error) {
      toast.error('Failed to save parameters');
      throw error;
    }
  }, [validateParameters, onSave, state.parameter_values]);

  // Reset to defaults
  const resetToDefaults = useCallback(() => {
    dispatch({ type: 'RESET_TO_DEFAULTS' });
    toast.info('Parameters reset to defaults');
  }, []);

  // Get parameter value
  const getParameterValue = useCallback((id: string) => {
    return state.parameter_values[id];
  }, [state.parameter_values]);

  // Get parameters by widget
  const getParametersByWidget = useCallback((widgetId: string) => {
    return Object.values(state.parameters).filter(param => 
      param.widget_bindings.includes(widgetId)
    );
  }, [state.parameters]);

  // Get parameter context for widgets
  const getParameterContext = useCallback(() => {
    return { ...state.parameter_values };
  }, [state.parameter_values]);

  // Bind parameter to widget
  const bindParameterToWidget = useCallback((parameterId: string, widgetId: string) => {
    const parameter = state.parameters[parameterId];
    if (parameter && !parameter.widget_bindings.includes(widgetId)) {
      updateParameter(parameterId, {
        widget_bindings: [...parameter.widget_bindings, widgetId],
      });
    }
  }, [state.parameters, updateParameter]);

  // Unbind parameter from widget
  const unbindParameterFromWidget = useCallback((parameterId: string, widgetId: string) => {
    const parameter = state.parameters[parameterId];
    if (parameter) {
      updateParameter(parameterId, {
        widget_bindings: parameter.widget_bindings.filter(id => id !== widgetId),
      });
    }
  }, [state.parameters, updateParameter]);

  // Notify about parameter changes
  useEffect(() => {
    if (onParametersChange) {
      onParametersChange(state.parameter_values);
    }
  }, [state.parameter_values, onParametersChange]);

  const contextValue: ParameterManagerContextType = {
    state,
    addParameter,
    updateParameter,
    removeParameter,
    setParameterValue,
    setParameterValues,
    validateParameters,
    clearValidationErrors,
    saveParameters,
    resetToDefaults,
    getParameterValue,
    getParametersByWidget,
    getParameterContext,
    bindParameterToWidget,
    unbindParameterFromWidget,
  };

  return (
    <ParameterManagerContext.Provider value={contextValue}>
      {children}
    </ParameterManagerContext.Provider>
  );
}

// Hook for widgets to access parameter values
export function useWidgetParameters(widgetId: string) {
  const { state, getParametersByWidget, getParameterContext } = useParameterManager();
  
  const widgetParameters = getParametersByWidget(widgetId);
  const parameterContext = getParameterContext();
  
  // Filter context to only include parameters bound to this widget
  const relevantContext = widgetParameters.reduce((acc, param) => {
    acc[param.name] = parameterContext[param.id];
    return acc;
  }, {} as Record<string, any>);

  return {
    parameters: widgetParameters,
    parameterValues: relevantContext,
    hasParameters: widgetParameters.length > 0,
    lastUpdated: state.last_updated,
  };
}