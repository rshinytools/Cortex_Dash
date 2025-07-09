// ABOUTME: Parameter binding component for connecting dashboard parameters to widget configurations
// ABOUTME: Handles parameter templating, substitution, and real-time updates in widget data

'use client';

import React, { useMemo, useCallback, useEffect } from 'react';
import { useParameterManager, useWidgetParameters } from './dashboard-parameters';

// Parameter substitution utilities
export class ParameterSubstitution {
  static readonly PARAMETER_REGEX = /\{\{([^}]+)\}\}/g;
  static readonly NESTED_PARAMETER_REGEX = /\{\{([^}]+(?:\.[^}]+)*)\}\}/g;

  // Extract parameter references from a text/object
  static extractParameterReferences(input: any): string[] {
    const references = new Set<string>();
    
    const extractFromString = (str: string) => {
      const matches = str.matchAll(this.PARAMETER_REGEX);
      for (const match of matches) {
        references.add(match[1].trim());
      }
    };

    const extractFromObject = (obj: any) => {
      if (typeof obj === 'string') {
        extractFromString(obj);
      } else if (Array.isArray(obj)) {
        obj.forEach(item => extractFromObject(item));
      } else if (obj && typeof obj === 'object') {
        Object.values(obj).forEach(value => extractFromObject(value));
      }
    };

    extractFromObject(input);
    return Array.from(references);
  }

  // Substitute parameters in a value
  static substitute(input: any, parameters: Record<string, any>): any {
    if (typeof input === 'string') {
      return this.substituteString(input, parameters);
    } else if (Array.isArray(input)) {
      return input.map(item => this.substitute(item, parameters));
    } else if (input && typeof input === 'object') {
      const result: any = {};
      for (const [key, value] of Object.entries(input)) {
        result[key] = this.substitute(value, parameters);
      }
      return result;
    }
    
    return input;
  }

  // Substitute parameters in a string
  static substituteString(input: string, parameters: Record<string, any>): any {
    // Check if the entire string is a parameter reference
    const fullMatch = input.match(/^\{\{([^}]+)\}\}$/);
    if (fullMatch) {
      const paramName = fullMatch[1].trim();
      const value = this.getNestedParameterValue(paramName, parameters);
      return value !== undefined ? value : input;
    }

    // Replace parameter references within the string
    return input.replace(this.PARAMETER_REGEX, (match, paramName) => {
      const value = this.getNestedParameterValue(paramName.trim(), parameters);
      return value !== undefined ? String(value) : match;
    });
  }

  // Get nested parameter value (supports dot notation)
  private static getNestedParameterValue(paramName: string, parameters: Record<string, any>): any {
    const parts = paramName.split('.');
    let value = parameters;
    
    for (const part of parts) {
      if (value && typeof value === 'object' && part in value) {
        value = value[part];
      } else {
        return undefined;
      }
    }
    
    return value;
  }

  // Validate parameter references
  static validateReferences(input: any, availableParameters: string[]): { valid: boolean; missing: string[] } {
    const references = this.extractParameterReferences(input);
    const missing = references.filter(ref => !availableParameters.includes(ref));
    
    return {
      valid: missing.length === 0,
      missing,
    };
  }

  // Create parameter-aware configuration
  static createParameterAwareConfig(baseConfig: any, parameters: Record<string, any>): any {
    return this.substitute(baseConfig, parameters);
  }
}

// Hook for binding parameters to widget configuration
export function useParameterBinding(widgetId: string, baseConfig: any) {
  const { parameterValues } = useWidgetParameters(widgetId);
  const { state } = useParameterManager();

  // Get all available parameter names
  const availableParameters = useMemo(() => {
    return Object.values(state.parameters).map(param => param.name);
  }, [state.parameters]);

  // Extract parameter references from base config
  const parameterReferences = useMemo(() => {
    return ParameterSubstitution.extractParameterReferences(baseConfig);
  }, [baseConfig]);

  // Validate parameter references
  const validation = useMemo(() => {
    return ParameterSubstitution.validateReferences(baseConfig, availableParameters);
  }, [baseConfig, availableParameters]);

  // Create parameter-substituted configuration
  const resolvedConfig = useMemo(() => {
    if (Object.keys(parameterValues).length === 0) {
      return baseConfig;
    }

    return ParameterSubstitution.createParameterAwareConfig(baseConfig, parameterValues);
  }, [baseConfig, parameterValues]);

  // Check if configuration has changed
  const hasParameterizedValues = useMemo(() => {
    return parameterReferences.length > 0;
  }, [parameterReferences]);

  return {
    resolvedConfig,
    baseConfig,
    parameterReferences,
    validation,
    hasParameterizedValues,
    parameterValues,
  };
}

// Component for binding parameters to widgets
interface ParameterBindingProps {
  widgetId: string;
  config: any;
  onConfigChange?: (resolvedConfig: any) => void;
  children: (props: {
    resolvedConfig: any;
    hasParameterizedValues: boolean;
    validation: { valid: boolean; missing: string[] };
  }) => React.ReactNode;
}

export function ParameterBinding({
  widgetId,
  config,
  onConfigChange,
  children,
}: ParameterBindingProps) {
  const bindingResult = useParameterBinding(widgetId, config);

  // Notify parent of config changes
  useEffect(() => {
    if (onConfigChange) {
      onConfigChange(bindingResult.resolvedConfig);
    }
  }, [bindingResult.resolvedConfig, onConfigChange]);

  return (
    <>
      {children({
        resolvedConfig: bindingResult.resolvedConfig,
        hasParameterizedValues: bindingResult.hasParameterizedValues,
        validation: bindingResult.validation,
      })}
    </>
  );
}

// Hook for widgets to get resolved parameter values in queries
export function useParameterizedQuery(widgetId: string, baseQuery: any) {
  const { parameterValues } = useWidgetParameters(widgetId);
  
  // Resolve query with parameters
  const resolvedQuery = useMemo(() => {
    if (Object.keys(parameterValues).length === 0) {
      return baseQuery;
    }

    return ParameterSubstitution.substitute(baseQuery, parameterValues);
  }, [baseQuery, parameterValues]);

  // Check if query has parameters
  const hasParameters = useMemo(() => {
    const references = ParameterSubstitution.extractParameterReferences(baseQuery);
    return references.length > 0;
  }, [baseQuery]);

  return {
    resolvedQuery,
    baseQuery,
    hasParameters,
    parameterValues,
  };
}

// Component for template preview with parameter substitution
interface ParameterTemplatePreviewProps {
  template: string;
  parameters: Record<string, any>;
  className?: string;
}

export function ParameterTemplatePreview({
  template,
  parameters,
  className,
}: ParameterTemplatePreviewProps) {
  const resolved = useMemo(() => {
    return ParameterSubstitution.substituteString(template, parameters);
  }, [template, parameters]);

  const references = useMemo(() => {
    return ParameterSubstitution.extractParameterReferences(template);
  }, [template]);

  return (
    <div className={className}>
      <div className="text-sm font-medium mb-2">Preview:</div>
      <div className="bg-muted p-3 rounded-md text-sm font-mono">
        {resolved}
      </div>
      {references.length > 0 && (
        <div className="mt-2 text-xs text-muted-foreground">
          Uses parameters: {references.join(', ')}
        </div>
      )}
    </div>
  );
}

// Auto-binding component that automatically binds parameters to widget configs
interface AutoParameterBindingProps {
  widgetId: string;
  children: React.ReactNode;
}

export function AutoParameterBinding({ widgetId, children }: AutoParameterBindingProps) {
  const { bindParameterToWidget, getParametersByWidget } = useParameterManager();
  const boundParameters = getParametersByWidget(widgetId);

  // Auto-bind compatible parameters based on naming conventions
  useEffect(() => {
    // This could be enhanced to automatically bind parameters based on
    // widget type, field names, or other heuristics
    
    // For now, we'll skip auto-binding to avoid unwanted side effects
    // In a real implementation, you might want to:
    // 1. Analyze widget configuration for parameter patterns
    // 2. Suggest parameter bindings to the user
    // 3. Auto-bind based on explicit rules or user preferences
  }, [widgetId, bindParameterToWidget]);

  return <>{children}</>;
}

// Utility functions for parameter management
export const ParameterUtils = {
  // Create a parameter reference string
  createReference: (parameterName: string): string => {
    return `{{${parameterName}}}`;
  },

  // Check if a string contains parameter references
  hasParameters: (input: string): boolean => {
    return ParameterSubstitution.PARAMETER_REGEX.test(input);
  },

  // Get parameter names from a string
  getParameterNames: (input: string): string[] => {
    return ParameterSubstitution.extractParameterReferences(input);
  },

  // Create a parameterized filter query
  createParameterizedFilter: (field: string, parameterName: string, operator = 'eq'): any => {
    return {
      [field]: {
        [`$${operator}`]: ParameterUtils.createReference(parameterName),
      },
    };
  },

  // Create a parameterized date range filter
  createParameterizedDateRange: (field: string, startParam: string, endParam: string): any => {
    return {
      [field]: {
        $gte: ParameterUtils.createReference(startParam),
        $lte: ParameterUtils.createReference(endParam),
      },
    };
  },

  // Validate parameter type compatibility
  validateParameterType: (parameterType: string, expectedType: string): boolean => {
    const typeMap: Record<string, string[]> = {
      string: ['string', 'select'],
      number: ['number'],
      date: ['date'],
      boolean: ['boolean'],
      array: ['multi_select'],
    };

    return typeMap[expectedType]?.includes(parameterType) || false;
  },
};