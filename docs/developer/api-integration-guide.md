# API Integration Guide

## Overview

This guide provides comprehensive information for integrating with the Clinical Dashboard Platform APIs. Whether you're building custom applications, integrating external systems, or extending platform functionality, this guide covers authentication, API usage patterns, and best practices.

## Table of Contents

1. [Authentication and Authorization](#authentication-and-authorization)
2. [API Client Setup](#api-client-setup)
3. [Core API Patterns](#core-api-patterns)
4. [Widget API Integration](#widget-api-integration)
5. [Data Pipeline Integration](#data-pipeline-integration)
6. [Export API Integration](#export-api-integration)
7. [Real-time Features](#real-time-features)
8. [Error Handling](#error-handling)
9. [Rate Limiting and Optimization](#rate-limiting-and-optimization)
10. [SDK and Libraries](#sdk-and-libraries)
11. [Integration Examples](#integration-examples)
12. [Best Practices](#best-practices)

## Authentication and Authorization

### JWT Authentication

The platform uses JWT (JSON Web Tokens) for authentication:

```typescript
// Authentication service
export class AuthService {
  private baseUrl: string;
  private token: string | null = null;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
    this.token = localStorage.getItem('auth_token');
  }

  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const response = await fetch(`${this.baseUrl}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(credentials),
    });

    if (!response.ok) {
      throw new Error('Authentication failed');
    }

    const data = await response.json();
    this.token = data.access_token;
    localStorage.setItem('auth_token', this.token);
    
    return data;
  }

  async refreshToken(): Promise<string> {
    const refreshToken = localStorage.getItem('refresh_token');
    
    const response = await fetch(`${this.baseUrl}/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${refreshToken}`,
      },
    });

    if (!response.ok) {
      throw new Error('Token refresh failed');
    }

    const data = await response.json();
    this.token = data.access_token;
    localStorage.setItem('auth_token', this.token);
    
    return this.token;
  }

  getAuthHeaders(): Record<string, string> {
    return {
      'Authorization': `Bearer ${this.token}`,
      'Content-Type': 'application/json',
    };
  }

  logout(): void {
    this.token = null;
    localStorage.removeItem('auth_token');
    localStorage.removeItem('refresh_token');
  }
}

interface LoginCredentials {
  email: string;
  password: string;
}

interface AuthResponse {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  user: User;
}
```

### API Key Authentication

For service-to-service communication:

```typescript
// API Key authentication
export class ApiKeyAuth {
  private apiKey: string;

  constructor(apiKey: string) {
    this.apiKey = apiKey;
  }

  getAuthHeaders(): Record<string, string> {
    return {
      'X-API-Key': this.apiKey,
      'Content-Type': 'application/json',
    };
  }
}

// Usage
const apiAuth = new ApiKeyAuth(process.env.CORTEX_API_KEY);
const headers = apiAuth.getAuthHeaders();
```

### OAuth 2.0 Integration

For third-party integrations:

```typescript
// OAuth 2.0 flow
export class OAuthService {
  private clientId: string;
  private redirectUri: string;
  private scopes: string[];

  constructor(config: OAuthConfig) {
    this.clientId = config.clientId;
    this.redirectUri = config.redirectUri;
    this.scopes = config.scopes;
  }

  getAuthorizationUrl(): string {
    const params = new URLSearchParams({
      client_id: this.clientId,
      redirect_uri: this.redirectUri,
      scope: this.scopes.join(' '),
      response_type: 'code',
      state: this.generateState(),
    });

    return `${this.baseUrl}/oauth/authorize?${params.toString()}`;
  }

  async exchangeCodeForToken(code: string, state: string): Promise<TokenResponse> {
    const response = await fetch(`${this.baseUrl}/oauth/token`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        grant_type: 'authorization_code',
        client_id: this.clientId,
        code,
        redirect_uri: this.redirectUri,
      }),
    });

    return response.json();
  }

  private generateState(): string {
    return Math.random().toString(36).substring(2, 15);
  }
}
```

## API Client Setup

### Base API Client

```typescript
// Base API client with common functionality
export class ApiClient {
  private baseUrl: string;
  private authService: AuthService;
  private requestInterceptors: RequestInterceptor[] = [];
  private responseInterceptors: ResponseInterceptor[] = [];

  constructor(baseUrl: string, authService: AuthService) {
    this.baseUrl = baseUrl;
    this.authService = authService;
  }

  addRequestInterceptor(interceptor: RequestInterceptor): void {
    this.requestInterceptors.push(interceptor);
  }

  addResponseInterceptor(interceptor: ResponseInterceptor): void {
    this.responseInterceptors.push(interceptor);
  }

  async request<T>(
    endpoint: string,
    options: RequestOptions = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`;
    
    // Prepare request
    let requestConfig: RequestInit = {
      method: options.method || 'GET',
      headers: {
        ...this.authService.getAuthHeaders(),
        ...options.headers,
      },
    };

    if (options.body) {
      requestConfig.body = typeof options.body === 'string' 
        ? options.body 
        : JSON.stringify(options.body);
    }

    // Apply request interceptors
    for (const interceptor of this.requestInterceptors) {
      requestConfig = await interceptor(requestConfig);
    }

    try {
      let response = await fetch(url, requestConfig);

      // Handle token refresh
      if (response.status === 401) {
        await this.authService.refreshToken();
        requestConfig.headers = {
          ...requestConfig.headers,
          ...this.authService.getAuthHeaders(),
        };
        response = await fetch(url, requestConfig);
      }

      // Apply response interceptors
      for (const interceptor of this.responseInterceptors) {
        response = await interceptor(response);
      }

      const data = await response.json();

      if (!response.ok) {
        throw new ApiError(response.status, data.message || 'Request failed', data);
      }

      return {
        data,
        status: response.status,
        headers: response.headers,
      };
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      throw new ApiError(0, 'Network error', error);
    }
  }

  // Convenience methods
  async get<T>(endpoint: string, params?: Record<string, any>): Promise<T> {
    const url = params ? `${endpoint}?${new URLSearchParams(params)}` : endpoint;
    const response = await this.request<T>(url);
    return response.data;
  }

  async post<T>(endpoint: string, body?: any): Promise<T> {
    const response = await this.request<T>(endpoint, {
      method: 'POST',
      body,
    });
    return response.data;
  }

  async put<T>(endpoint: string, body?: any): Promise<T> {
    const response = await this.request<T>(endpoint, {
      method: 'PUT',
      body,
    });
    return response.data;
  }

  async delete<T>(endpoint: string): Promise<T> {
    const response = await this.request<T>(endpoint, {
      method: 'DELETE',
    });
    return response.data;
  }
}

// Types
interface RequestOptions {
  method?: string;
  headers?: Record<string, string>;
  body?: any;
}

interface ApiResponse<T> {
  data: T;
  status: number;
  headers: Headers;
}

type RequestInterceptor = (config: RequestInit) => Promise<RequestInit>;
type ResponseInterceptor = (response: Response) => Promise<Response>;

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public data?: any
  ) {
    super(message);
    this.name = 'ApiError';
  }
}
```

### Typed API Clients

```typescript
// Widget API client
export class WidgetApiClient {
  constructor(private apiClient: ApiClient) {}

  async getWidgetTypes(category?: string): Promise<WidgetType[]> {
    const params = category ? { category } : undefined;
    return this.apiClient.get('/widget-types', params);
  }

  async validateConfig(config: WidgetConfigValidationRequest): Promise<ValidationResult> {
    return this.apiClient.post('/widgets/validate-config', config);
  }

  async getWidgetData(
    widgetId: string,
    dashboardId: string,
    options?: {
      refresh?: boolean;
      filters?: string;
    }
  ): Promise<WidgetData> {
    const params = {
      dashboard_id: dashboardId,
      ...options,
    };
    return this.apiClient.get(`/widgets/${widgetId}/data`, params);
  }

  async getBatchWidgetData(request: BatchDataRequest): Promise<BatchDataResponse> {
    return this.apiClient.post('/widgets/batch-data', request);
  }

  async refreshWidget(widgetId: string, dashboardId: string): Promise<RefreshResponse> {
    return this.apiClient.post(`/widgets/${widgetId}/refresh`, { dashboard_id: dashboardId });
  }

  async getDataSources(studyId: string, widgetType?: string): Promise<DataSource[]> {
    const params = { study_id: studyId, widget_type: widgetType };
    return this.apiClient.get('/widgets/data-sources', params);
  }

  async previewWidget(config: WidgetPreviewRequest, sampleSize?: number): Promise<WidgetPreview> {
    const params = sampleSize ? { sample_size: sampleSize } : undefined;
    return this.apiClient.post('/widgets/preview', config, { params });
  }
}

// Dashboard API client
export class DashboardApiClient {
  constructor(private apiClient: ApiClient) {}

  async getDashboards(studyId?: string): Promise<Dashboard[]> {
    const params = studyId ? { study_id: studyId } : undefined;
    return this.apiClient.get('/dashboards', params);
  }

  async getDashboard(dashboardId: string): Promise<Dashboard> {
    return this.apiClient.get(`/dashboards/${dashboardId}`);
  }

  async createDashboard(dashboard: CreateDashboardRequest): Promise<Dashboard> {
    return this.apiClient.post('/dashboards', dashboard);
  }

  async updateDashboard(dashboardId: string, updates: UpdateDashboardRequest): Promise<Dashboard> {
    return this.apiClient.put(`/dashboards/${dashboardId}`, updates);
  }

  async deleteDashboard(dashboardId: string): Promise<void> {
    return this.apiClient.delete(`/dashboards/${dashboardId}`);
  }

  async exportDashboard(dashboardId: string, options: ExportOptions): Promise<ExportResponse> {
    return this.apiClient.post(`/dashboards/${dashboardId}/export`, options);
  }
}

// Export API client
export class ExportApiClient {
  constructor(private apiClient: ApiClient) {}

  async createExport(exportRequest: ExportRequest): Promise<ExportResponse> {
    return this.apiClient.post('/exports', exportRequest);
  }

  async getExportStatus(exportId: string): Promise<ExportStatus> {
    return this.apiClient.get(`/exports/${exportId}/status`);
  }

  async downloadExport(exportId: string): Promise<Blob> {
    const response = await fetch(`${this.apiClient.baseUrl}/exports/${exportId}/download`, {
      headers: this.authService.getAuthHeaders(),
    });
    return response.blob();
  }

  async cancelExport(exportId: string): Promise<void> {
    return this.apiClient.post(`/exports/${exportId}/cancel`);
  }

  async listExports(filters?: ExportFilters): Promise<ExportList> {
    return this.apiClient.get('/exports', filters);
  }
}
```

## Core API Patterns

### Pagination

```typescript
// Pagination handler
export class PaginationHandler {
  static async getAllPages<T>(
    apiCall: (page: number, limit: number) => Promise<PaginatedResponse<T>>,
    limit: number = 100
  ): Promise<T[]> {
    const allItems: T[] = [];
    let page = 1;
    let hasMore = true;

    while (hasMore) {
      const response = await apiCall(page, limit);
      allItems.push(...response.items);
      
      hasMore = response.pagination.page < response.pagination.pages;
      page++;
    }

    return allItems;
  }

  static async *paginatedIterator<T>(
    apiCall: (page: number, limit: number) => Promise<PaginatedResponse<T>>,
    limit: number = 100
  ): AsyncGenerator<T[], void, unknown> {
    let page = 1;
    let hasMore = true;

    while (hasMore) {
      const response = await apiCall(page, limit);
      yield response.items;
      
      hasMore = response.pagination.page < response.pagination.pages;
      page++;
    }
  }
}

// Usage example
const getAllStudies = async (): Promise<Study[]> => {
  return PaginationHandler.getAllPages(
    (page, limit) => studyApiClient.getStudies({ page, limit })
  );
};

// Async iteration
for await (const studyBatch of PaginationHandler.paginatedIterator(
  (page, limit) => studyApiClient.getStudies({ page, limit }),
  50
)) {
  console.log(`Processing ${studyBatch.length} studies`);
  // Process batch
}
```

### Error Handling Patterns

```typescript
// API error handling utilities
export class ApiErrorHandler {
  static isRetryableError(error: ApiError): boolean {
    return [408, 429, 500, 502, 503, 504].includes(error.status);
  }

  static async withRetry<T>(
    operation: () => Promise<T>,
    maxRetries: number = 3,
    baseDelay: number = 1000
  ): Promise<T> {
    let lastError: Error;

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        return await operation();
      } catch (error) {
        lastError = error as Error;

        if (attempt === maxRetries || !(error instanceof ApiError) || !this.isRetryableError(error)) {
          throw error;
        }

        const delay = baseDelay * Math.pow(2, attempt);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }

    throw lastError!;
  }

  static async withCircuitBreaker<T>(
    operation: () => Promise<T>,
    options: CircuitBreakerOptions = {}
  ): Promise<T> {
    const circuitBreaker = new CircuitBreaker(operation, options);
    return circuitBreaker.execute();
  }
}

// Circuit breaker implementation
class CircuitBreaker {
  private failures = 0;
  private nextAttempt = Date.now();
  private state: 'CLOSED' | 'OPEN' | 'HALF_OPEN' = 'CLOSED';

  constructor(
    private operation: () => Promise<any>,
    private options: CircuitBreakerOptions = {}
  ) {
    this.options = {
      failureThreshold: 5,
      recoveryTimeout: 60000,
      monitoringPeriod: 10000,
      ...options,
    };
  }

  async execute(): Promise<any> {
    if (this.state === 'OPEN') {
      if (Date.now() < this.nextAttempt) {
        throw new Error('Circuit breaker is OPEN');
      }
      this.state = 'HALF_OPEN';
    }

    try {
      const result = await this.operation();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  private onSuccess(): void {
    this.failures = 0;
    this.state = 'CLOSED';
  }

  private onFailure(): void {
    this.failures++;
    if (this.failures >= this.options.failureThreshold!) {
      this.state = 'OPEN';
      this.nextAttempt = Date.now() + this.options.recoveryTimeout!;
    }
  }
}

interface CircuitBreakerOptions {
  failureThreshold?: number;
  recoveryTimeout?: number;
  monitoringPeriod?: number;
}
```

### Caching Strategies

```typescript
// API response caching
export class ApiCache {
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

  invalidate(pattern?: string): void {
    if (!pattern) {
      this.cache.clear();
      return;
    }

    const regex = new RegExp(pattern);
    for (const key of this.cache.keys()) {
      if (regex.test(key)) {
        this.cache.delete(key);
      }
    }
  }

  // Cache with stale-while-revalidate strategy
  async getWithSWR<T>(
    key: string,
    fetcher: () => Promise<T>,
    ttl?: number
  ): Promise<T> {
    const cached = this.get(key);
    
    if (cached) {
      // Return cached data immediately
      const result = cached;
      
      // Revalidate in background if approaching expiration
      const entry = this.cache.get(key);
      if (entry && (entry.expiresAt - Date.now()) < (ttl || this.defaultTTL) * 0.2) {
        fetcher().then(fresh => this.set(key, fresh, ttl)).catch(console.error);
      }
      
      return result;
    }

    // No cached data, fetch fresh
    const fresh = await fetcher();
    this.set(key, fresh, ttl);
    return fresh;
  }
}

interface CacheEntry {
  data: any;
  expiresAt: number;
}

// Usage with API client
export class CachedApiClient extends ApiClient {
  private cache = new ApiCache();

  async get<T>(endpoint: string, params?: Record<string, any>): Promise<T> {
    const cacheKey = `${endpoint}:${JSON.stringify(params || {})}`;
    
    return this.cache.getWithSWR(cacheKey, async () => {
      return super.get<T>(endpoint, params);
    });
  }

  invalidateCache(pattern?: string): void {
    this.cache.invalidate(pattern);
  }
}
```

## Widget API Integration

### Widget Data Management

```typescript
// Widget data manager
export class WidgetDataManager {
  private widgetApiClient: WidgetApiClient;
  private cache = new ApiCache();
  private subscriptions = new Map<string, EventSource>();

  constructor(apiClient: ApiClient) {
    this.widgetApiClient = new WidgetApiClient(apiClient);
  }

  async loadWidgetData(
    widgetId: string,
    config: WidgetConfig,
    options: LoadDataOptions = {}
  ): Promise<WidgetData> {
    const cacheKey = this.generateCacheKey(widgetId, config, options);
    
    if (!options.refresh) {
      const cached = this.cache.get(cacheKey);
      if (cached) return cached;
    }

    try {
      const data = await this.widgetApiClient.getWidgetData(
        widgetId,
        options.dashboardId,
        {
          refresh: options.refresh,
          filters: options.filters ? JSON.stringify(options.filters) : undefined,
        }
      );

      this.cache.set(cacheKey, data, options.cacheTTL);
      return data;
    } catch (error) {
      // Fallback to cached data if available
      const cached = this.cache.get(cacheKey);
      if (cached) {
        console.warn('Using cached data due to API error:', error);
        return cached;
      }
      throw error;
    }
  }

  async loadBatchWidgetData(
    widgets: Array<{ id: string; config: WidgetConfig }>,
    dashboardId: string,
    filters?: Record<string, any>
  ): Promise<Map<string, WidgetData>> {
    const request: BatchDataRequest = {
      widget_ids: widgets.map(w => w.id),
      dashboard_id: dashboardId,
      filters,
    };

    const response = await this.widgetApiClient.getBatchWidgetData(request);
    const results = new Map<string, WidgetData>();

    // Process successful results
    Object.entries(response.results).forEach(([widgetId, result]) => {
      results.set(widgetId, result.data);
      
      // Cache individual results
      const widget = widgets.find(w => w.id === widgetId);
      if (widget) {
        const cacheKey = this.generateCacheKey(widgetId, widget.config, { dashboardId });
        this.cache.set(cacheKey, result.data);
      }
    });

    // Handle errors
    Object.entries(response.errors).forEach(([widgetId, error]) => {
      console.error(`Widget ${widgetId} failed to load:`, error);
      
      // Try to use cached data
      const widget = widgets.find(w => w.id === widgetId);
      if (widget) {
        const cacheKey = this.generateCacheKey(widgetId, widget.config, { dashboardId });
        const cached = this.cache.get(cacheKey);
        if (cached) {
          results.set(widgetId, cached);
        }
      }
    });

    return results;
  }

  subscribeToWidgetUpdates(
    widgetId: string,
    onUpdate: (data: WidgetData) => void,
    onError?: (error: Error) => void
  ): () => void {
    const eventSource = new EventSource(`/api/v1/widgets/${widgetId}/stream`);
    
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onUpdate(data);
      } catch (error) {
        onError?.(error as Error);
      }
    };

    eventSource.onerror = (error) => {
      onError?.(error as Error);
    };

    this.subscriptions.set(widgetId, eventSource);

    // Return unsubscribe function
    return () => {
      eventSource.close();
      this.subscriptions.delete(widgetId);
    };
  }

  private generateCacheKey(
    widgetId: string,
    config: WidgetConfig,
    options: Partial<LoadDataOptions>
  ): string {
    const keyData = {
      widgetId,
      config,
      dashboardId: options.dashboardId,
      filters: options.filters,
    };
    return `widget-data:${btoa(JSON.stringify(keyData))}`;
  }

  dispose(): void {
    // Close all subscriptions
    this.subscriptions.forEach(eventSource => eventSource.close());
    this.subscriptions.clear();
    
    // Clear cache
    this.cache.invalidate();
  }
}

interface LoadDataOptions {
  dashboardId: string;
  refresh?: boolean;
  filters?: Record<string, any>;
  cacheTTL?: number;
}
```

### Widget Configuration Validation

```typescript
// Widget configuration validator
export class WidgetConfigValidator {
  private widgetApiClient: WidgetApiClient;
  private validationCache = new Map<string, ValidationResult>();

  constructor(apiClient: ApiClient) {
    this.widgetApiClient = new WidgetApiClient(apiClient);
  }

  async validateConfig(
    type: string,
    config: any,
    options: ValidationOptions = {}
  ): Promise<ValidationResult> {
    const cacheKey = `${type}:${JSON.stringify(config)}`;
    
    if (!options.skipCache) {
      const cached = this.validationCache.get(cacheKey);
      if (cached) return cached;
    }

    try {
      const result = await this.widgetApiClient.validateConfig({ type, config });
      
      // Cache successful validations
      if (result.is_valid) {
        this.validationCache.set(cacheKey, result);
      }
      
      return result;
    } catch (error) {
      return {
        is_valid: false,
        errors: [{ field: 'general', message: 'Validation service unavailable' }],
        warnings: [],
        suggestions: [],
      };
    }
  }

  async validateMultipleConfigs(
    configs: Array<{ type: string; config: any }>
  ): Promise<Map<string, ValidationResult>> {
    const results = new Map<string, ValidationResult>();
    
    // Validate in parallel
    const validationPromises = configs.map(async ({ type, config }, index) => {
      try {
        const result = await this.validateConfig(type, config);
        results.set(index.toString(), result);
      } catch (error) {
        results.set(index.toString(), {
          is_valid: false,
          errors: [{ field: 'general', message: error.message }],
          warnings: [],
          suggestions: [],
        });
      }
    });

    await Promise.all(validationPromises);
    return results;
  }

  clearValidationCache(): void {
    this.validationCache.clear();
  }
}

interface ValidationOptions {
  skipCache?: boolean;
  timeout?: number;
}
```

## Data Pipeline Integration

### Data Source Integration

```typescript
// Data source connector
export class DataSourceConnector {
  private apiClient: ApiClient;
  private connections = new Map<string, DataConnection>();

  constructor(apiClient: ApiClient) {
    this.apiClient = apiClient;
  }

  async registerDataSource(config: DataSourceConfig): Promise<DataSource> {
    const response = await this.apiClient.post('/data-sources', config);
    return response;
  }

  async testConnection(sourceId: string): Promise<ConnectionTestResult> {
    const response = await this.apiClient.post(`/data-sources/${sourceId}/test`);
    return response;
  }

  async syncData(sourceId: string, options?: SyncOptions): Promise<SyncResult> {
    const response = await this.apiClient.post(`/data-sources/${sourceId}/sync`, options);
    return response;
  }

  async getSchema(sourceId: string): Promise<DataSchema> {
    const response = await this.apiClient.get(`/data-sources/${sourceId}/schema`);
    return response;
  }

  async queryData(sourceId: string, query: DataQuery): Promise<QueryResult> {
    const response = await this.apiClient.post(`/data-sources/${sourceId}/query`, query);
    return response;
  }

  // Real-time data streaming
  async subscribeToDataUpdates(
    sourceId: string,
    onUpdate: (data: DataUpdate) => void,
    onError?: (error: Error) => void
  ): Promise<() => void> {
    const eventSource = new EventSource(`/api/v1/data-sources/${sourceId}/stream`);
    
    eventSource.onmessage = (event) => {
      try {
        const update = JSON.parse(event.data);
        onUpdate(update);
      } catch (error) {
        onError?.(error as Error);
      }
    };

    eventSource.onerror = (error) => {
      onError?.(error as Error);
    };

    return () => eventSource.close();
  }
}

interface DataSourceConfig {
  name: string;
  type: 'api' | 'database' | 'file' | 'stream';
  connection_string: string;
  credentials?: Record<string, any>;
  settings?: Record<string, any>;
}

interface DataQuery {
  fields?: string[];
  filters?: QueryFilter[];
  aggregations?: Aggregation[];
  sort?: SortOption[];
  limit?: number;
  offset?: number;
}

interface QueryFilter {
  field: string;
  operator: 'eq' | 'ne' | 'gt' | 'gte' | 'lt' | 'lte' | 'in' | 'like';
  value: any;
}

interface Aggregation {
  field: string;
  function: 'count' | 'sum' | 'avg' | 'min' | 'max';
  alias?: string;
}
```

### ETL Pipeline Management

```typescript
// ETL pipeline manager
export class ETLPipelineManager {
  private apiClient: ApiClient;
  private runningPipelines = new Map<string, PipelineExecution>();

  constructor(apiClient: ApiClient) {
    this.apiClient = apiClient;
  }

  async createPipeline(config: PipelineConfig): Promise<Pipeline> {
    return this.apiClient.post('/pipelines', config);
  }

  async runPipeline(
    pipelineId: string,
    options?: RunOptions
  ): Promise<PipelineExecution> {
    const execution = await this.apiClient.post(`/pipelines/${pipelineId}/run`, options);
    this.runningPipelines.set(execution.id, execution);
    return execution;
  }

  async getPipelineStatus(executionId: string): Promise<PipelineStatus> {
    return this.apiClient.get(`/pipeline-executions/${executionId}/status`);
  }

  async cancelPipeline(executionId: string): Promise<void> {
    await this.apiClient.post(`/pipeline-executions/${executionId}/cancel`);
    this.runningPipelines.delete(executionId);
  }

  async getPipelineLogs(
    executionId: string,
    options?: LogOptions
  ): Promise<PipelineLog[]> {
    const params = {
      level: options?.level,
      start_time: options?.startTime?.toISOString(),
      end_time: options?.endTime?.toISOString(),
      limit: options?.limit,
    };
    return this.apiClient.get(`/pipeline-executions/${executionId}/logs`, params);
  }

  async monitorPipeline(
    executionId: string,
    onStatusChange: (status: PipelineStatus) => void,
    onLog?: (log: PipelineLog) => void
  ): Promise<() => void> {
    const eventSource = new EventSource(
      `/api/v1/pipeline-executions/${executionId}/monitor`
    );

    eventSource.addEventListener('status', (event) => {
      const status = JSON.parse(event.data);
      onStatusChange(status);
    });

    if (onLog) {
      eventSource.addEventListener('log', (event) => {
        const log = JSON.parse(event.data);
        onLog(log);
      });
    }

    return () => eventSource.close();
  }

  // Scheduled pipeline management
  async schedulePipeline(
    pipelineId: string,
    schedule: PipelineSchedule
  ): Promise<ScheduledPipeline> {
    return this.apiClient.post(`/pipelines/${pipelineId}/schedule`, schedule);
  }

  async getScheduledPipelines(): Promise<ScheduledPipeline[]> {
    return this.apiClient.get('/scheduled-pipelines');
  }

  async pauseSchedule(scheduleId: string): Promise<void> {
    return this.apiClient.post(`/scheduled-pipelines/${scheduleId}/pause`);
  }

  async resumeSchedule(scheduleId: string): Promise<void> {
    return this.apiClient.post(`/scheduled-pipelines/${scheduleId}/resume`);
  }
}

interface PipelineConfig {
  name: string;
  description?: string;
  steps: PipelineStep[];
  settings?: Record<string, any>;
}

interface PipelineStep {
  id: string;
  type: 'extract' | 'transform' | 'load' | 'validate';
  config: Record<string, any>;
  dependencies?: string[];
}

interface PipelineSchedule {
  cron_expression: string;
  timezone?: string;
  enabled: boolean;
  max_runs?: number;
  timeout_minutes?: number;
}
```

## Export API Integration

### Export Management

```typescript
// Export manager with advanced features
export class ExportManager {
  private exportApiClient: ExportApiClient;
  private activeExports = new Map<string, ExportMonitor>();

  constructor(apiClient: ApiClient) {
    this.exportApiClient = new ExportApiClient(apiClient);
  }

  async createExport(request: ExportRequest): Promise<ExportMonitor> {
    const response = await this.exportApiClient.createExport(request);
    const monitor = new ExportMonitor(response.export_id, this.exportApiClient);
    this.activeExports.set(response.export_id, monitor);
    return monitor;
  }

  async createBulkExport(requests: ExportRequest[]): Promise<ExportMonitor[]> {
    const monitors = await Promise.all(
      requests.map(request => this.createExport(request))
    );
    return monitors;
  }

  async resumeExport(exportId: string): Promise<ExportMonitor> {
    const status = await this.exportApiClient.getExportStatus(exportId);
    const monitor = new ExportMonitor(exportId, this.exportApiClient);
    this.activeExports.set(exportId, monitor);
    return monitor;
  }

  getActiveExports(): ExportMonitor[] {
    return Array.from(this.activeExports.values());
  }

  async cancelAllExports(): Promise<void> {
    const cancelPromises = Array.from(this.activeExports.values()).map(
      monitor => monitor.cancel()
    );
    await Promise.all(cancelPromises);
    this.activeExports.clear();
  }
}

// Export monitor for tracking individual exports
export class ExportMonitor {
  private pollInterval: NodeJS.Timeout | null = null;
  private eventListeners = new Map<string, Function[]>();

  constructor(
    public readonly exportId: string,
    private exportApiClient: ExportApiClient
  ) {}

  async start(pollIntervalMs: number = 2000): Promise<void> {
    if (this.pollInterval) return;

    this.pollInterval = setInterval(async () => {
      try {
        const status = await this.exportApiClient.getExportStatus(this.exportId);
        this.emit('status', status);

        if (status.status === 'completed' || status.status === 'failed') {
          this.stop();
        }
      } catch (error) {
        this.emit('error', error);
      }
    }, pollIntervalMs);
  }

  stop(): void {
    if (this.pollInterval) {
      clearInterval(this.pollInterval);
      this.pollInterval = null;
    }
  }

  async cancel(): Promise<void> {
    await this.exportApiClient.cancelExport(this.exportId);
    this.stop();
    this.emit('cancelled');
  }

  async download(): Promise<Blob> {
    return this.exportApiClient.downloadExport(this.exportId);
  }

  async waitForCompletion(timeoutMs?: number): Promise<ExportStatus> {
    return new Promise((resolve, reject) => {
      const timeout = timeoutMs ? setTimeout(() => {
        this.off('status', statusHandler);
        this.off('error', errorHandler);
        reject(new Error('Export timeout'));
      }, timeoutMs) : null;

      const statusHandler = (status: ExportStatus) => {
        if (status.status === 'completed') {
          if (timeout) clearTimeout(timeout);
          this.off('status', statusHandler);
          this.off('error', errorHandler);
          resolve(status);
        } else if (status.status === 'failed') {
          if (timeout) clearTimeout(timeout);
          this.off('status', statusHandler);
          this.off('error', errorHandler);
          reject(new Error(`Export failed: ${status.error_message}`));
        }
      };

      const errorHandler = (error: Error) => {
        if (timeout) clearTimeout(timeout);
        this.off('status', statusHandler);
        this.off('error', errorHandler);
        reject(error);
      };

      this.on('status', statusHandler);
      this.on('error', errorHandler);
    });
  }

  on(event: string, handler: Function): void {
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, []);
    }
    this.eventListeners.get(event)!.push(handler);
  }

  off(event: string, handler: Function): void {
    const handlers = this.eventListeners.get(event);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }

  private emit(event: string, data?: any): void {
    const handlers = this.eventListeners.get(event);
    if (handlers) {
      handlers.forEach(handler => handler(data));
    }
  }
}
```

## Real-time Features

### WebSocket Integration

```typescript
// Real-time data service
export class RealTimeService {
  private websocket: WebSocket | null = null;
  private subscriptions = new Map<string, Set<Function>>();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  constructor(private wsUrl: string, private authToken: string) {}

  async connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      this.websocket = new WebSocket(`${this.wsUrl}?token=${this.authToken}`);

      this.websocket.onopen = () => {
        console.log('WebSocket connected');
        this.reconnectAttempts = 0;
        resolve();
      };

      this.websocket.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          this.handleMessage(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      this.websocket.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason);
        if (!event.wasClean && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.attemptReconnect();
        }
      };

      this.websocket.onerror = (error) => {
        console.error('WebSocket error:', error);
        reject(error);
      };
    });
  }

  disconnect(): void {
    if (this.websocket) {
      this.websocket.close(1000, 'Client disconnect');
      this.websocket = null;
    }
  }

  subscribe(channel: string, callback: Function): () => void {
    if (!this.subscriptions.has(channel)) {
      this.subscriptions.set(channel, new Set());
      this.sendMessage({ type: 'subscribe', channel });
    }

    this.subscriptions.get(channel)!.add(callback);

    // Return unsubscribe function
    return () => {
      const channelSubs = this.subscriptions.get(channel);
      if (channelSubs) {
        channelSubs.delete(callback);
        if (channelSubs.size === 0) {
          this.subscriptions.delete(channel);
          this.sendMessage({ type: 'unsubscribe', channel });
        }
      }
    };
  }

  // Subscribe to widget data updates
  subscribeToWidgetUpdates(
    widgetId: string,
    callback: (data: WidgetData) => void
  ): () => void {
    return this.subscribe(`widget:${widgetId}`, callback);
  }

  // Subscribe to dashboard updates
  subscribeToDashboardUpdates(
    dashboardId: string,
    callback: (update: DashboardUpdate) => void
  ): () => void {
    return this.subscribe(`dashboard:${dashboardId}`, callback);
  }

  // Subscribe to export status updates
  subscribeToExportUpdates(
    exportId: string,
    callback: (status: ExportStatus) => void
  ): () => void {
    return this.subscribe(`export:${exportId}`, callback);
  }

  private sendMessage(message: any): void {
    if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
      this.websocket.send(JSON.stringify(message));
    }
  }

  private handleMessage(message: any): void {
    const { channel, data } = message;
    const callbacks = this.subscriptions.get(channel);
    if (callbacks) {
      callbacks.forEach(callback => callback(data));
    }
  }

  private async attemptReconnect(): Promise<void> {
    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    
    console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`);
    
    await new Promise(resolve => setTimeout(resolve, delay));
    
    try {
      await this.connect();
    } catch (error) {
      console.error('Reconnection failed:', error);
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        this.attemptReconnect();
      }
    }
  }
}
```

### Server-Sent Events

```typescript
// Server-sent events service
export class SSEService {
  private eventSources = new Map<string, EventSource>();
  private subscriptions = new Map<string, Set<Function>>();

  subscribe(
    endpoint: string,
    callback: (data: any) => void,
    options?: SSEOptions
  ): () => void {
    const eventSource = this.getOrCreateEventSource(endpoint, options);
    
    if (!this.subscriptions.has(endpoint)) {
      this.subscriptions.set(endpoint, new Set());
    }
    
    this.subscriptions.get(endpoint)!.add(callback);

    // Return unsubscribe function
    return () => {
      const callbacks = this.subscriptions.get(endpoint);
      if (callbacks) {
        callbacks.delete(callback);
        if (callbacks.size === 0) {
          this.closeEventSource(endpoint);
        }
      }
    };
  }

  private getOrCreateEventSource(endpoint: string, options?: SSEOptions): EventSource {
    let eventSource = this.eventSources.get(endpoint);
    
    if (!eventSource) {
      const url = new URL(endpoint, window.location.origin);
      if (options?.params) {
        Object.entries(options.params).forEach(([key, value]) => {
          url.searchParams.set(key, String(value));
        });
      }

      eventSource = new EventSource(url.toString());
      
      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.notifySubscribers(endpoint, data);
        } catch (error) {
          console.error('Failed to parse SSE data:', error);
        }
      };

      eventSource.onerror = (error) => {
        console.error('SSE error:', error);
        // Auto-reconnect is handled by EventSource
      };

      this.eventSources.set(endpoint, eventSource);
    }

    return eventSource;
  }

  private closeEventSource(endpoint: string): void {
    const eventSource = this.eventSources.get(endpoint);
    if (eventSource) {
      eventSource.close();
      this.eventSources.delete(endpoint);
      this.subscriptions.delete(endpoint);
    }
  }

  private notifySubscribers(endpoint: string, data: any): void {
    const callbacks = this.subscriptions.get(endpoint);
    if (callbacks) {
      callbacks.forEach(callback => callback(data));
    }
  }

  dispose(): void {
    this.eventSources.forEach(eventSource => eventSource.close());
    this.eventSources.clear();
    this.subscriptions.clear();
  }
}

interface SSEOptions {
  params?: Record<string, any>;
  withCredentials?: boolean;
}
```

## Error Handling

### Comprehensive Error Handling

```typescript
// API error types
export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public code?: string,
    public details?: any
  ) {
    super(message);
    this.name = 'ApiError';
  }

  static fromResponse(response: Response, data: any): ApiError {
    return new ApiError(
      response.status,
      data.message || response.statusText,
      data.code,
      data.details
    );
  }

  isRetryable(): boolean {
    return [408, 429, 500, 502, 503, 504].includes(this.status);
  }

  isAuthError(): boolean {
    return this.status === 401;
  }

  isNotFound(): boolean {
    return this.status === 404;
  }

  isValidationError(): boolean {
    return this.status === 400 || this.status === 422;
  }
}

// Global error handler
export class GlobalErrorHandler {
  private errorCallbacks = new Set<(error: Error) => void>();
  private retryCallbacks = new Set<(error: ApiError) => Promise<boolean>>();

  onError(callback: (error: Error) => void): () => void {
    this.errorCallbacks.add(callback);
    return () => this.errorCallbacks.delete(callback);
  }

  onRetry(callback: (error: ApiError) => Promise<boolean>): () => void {
    this.retryCallbacks.add(callback);
    return () => this.retryCallbacks.delete(callback);
  }

  async handleError(error: Error): Promise<boolean> {
    // Notify error callbacks
    this.errorCallbacks.forEach(callback => callback(error));

    // Handle retry logic for API errors
    if (error instanceof ApiError && error.isRetryable()) {
      for (const callback of this.retryCallbacks) {
        const shouldRetry = await callback(error);
        if (shouldRetry) {
          return true;
        }
      }
    }

    return false;
  }

  // Error recovery strategies
  static createRetryStrategy(maxRetries: number = 3, baseDelay: number = 1000) {
    return async (error: ApiError): Promise<boolean> => {
      if (!error.isRetryable()) return false;

      const attempt = (error as any)._retryAttempt || 0;
      if (attempt >= maxRetries) return false;

      const delay = baseDelay * Math.pow(2, attempt);
      await new Promise(resolve => setTimeout(resolve, delay));

      (error as any)._retryAttempt = attempt + 1;
      return true;
    };
  }

  static createCircuitBreakerStrategy(
    failureThreshold: number = 5,
    recoveryTimeout: number = 60000
  ) {
    let failures = 0;
    let lastFailure = 0;
    let circuitOpen = false;

    return async (error: ApiError): Promise<boolean> => {
      const now = Date.now();

      if (circuitOpen) {
        if (now - lastFailure > recoveryTimeout) {
          circuitOpen = false;
          failures = 0;
        } else {
          return false;
        }
      }

      failures++;
      lastFailure = now;

      if (failures >= failureThreshold) {
        circuitOpen = true;
        return false;
      }

      return true;
    };
  }
}
```

## Rate Limiting and Optimization

### Request Rate Limiting

```typescript
// Rate limiter implementation
export class RateLimiter {
  private requests = new Map<string, number[]>();

  constructor(
    private maxRequests: number,
    private windowMs: number
  ) {}

  async checkLimit(key: string): Promise<boolean> {
    const now = Date.now();
    const windowStart = now - this.windowMs;
    
    if (!this.requests.has(key)) {
      this.requests.set(key, []);
    }

    const keyRequests = this.requests.get(key)!;
    
    // Remove old requests outside the window
    while (keyRequests.length > 0 && keyRequests[0] < windowStart) {
      keyRequests.shift();
    }

    if (keyRequests.length >= this.maxRequests) {
      return false;
    }

    keyRequests.push(now);
    return true;
  }

  async waitForSlot(key: string): Promise<void> {
    while (!(await this.checkLimit(key))) {
      await new Promise(resolve => setTimeout(resolve, 100));
    }
  }

  getRemainingRequests(key: string): number {
    const keyRequests = this.requests.get(key) || [];
    return Math.max(0, this.maxRequests - keyRequests.length);
  }

  getResetTime(key: string): Date {
    const keyRequests = this.requests.get(key) || [];
    if (keyRequests.length === 0) {
      return new Date();
    }
    return new Date(keyRequests[0] + this.windowMs);
  }
}

// Rate-limited API client
export class RateLimitedApiClient extends ApiClient {
  private rateLimiter: RateLimiter;

  constructor(
    baseUrl: string,
    authService: AuthService,
    maxRequestsPerMinute: number = 60
  ) {
    super(baseUrl, authService);
    this.rateLimiter = new RateLimiter(maxRequestsPerMinute, 60000);
  }

  async request<T>(endpoint: string, options: RequestOptions = {}): Promise<ApiResponse<T>> {
    const rateLimitKey = this.getRateLimitKey(endpoint, options);
    await this.rateLimiter.waitForSlot(rateLimitKey);
    
    return super.request<T>(endpoint, options);
  }

  private getRateLimitKey(endpoint: string, options: RequestOptions): string {
    // Different endpoints might have different rate limits
    if (endpoint.includes('/exports/')) {
      return 'exports';
    } else if (endpoint.includes('/widgets/batch-data')) {
      return 'batch-data';
    }
    return 'default';
  }
}
```

### Request Optimization

```typescript
// Request batching and deduplication
export class RequestOptimizer {
  private pendingRequests = new Map<string, Promise<any>>();
  private batchQueue = new Map<string, BatchRequest[]>();
  private batchTimers = new Map<string, NodeJS.Timeout>();

  constructor(private apiClient: ApiClient) {}

  // Deduplicate identical requests
  async dedupedRequest<T>(
    key: string,
    requestFn: () => Promise<T>
  ): Promise<T> {
    if (this.pendingRequests.has(key)) {
      return this.pendingRequests.get(key);
    }

    const promise = requestFn();
    this.pendingRequests.set(key, promise);

    try {
      const result = await promise;
      return result;
    } finally {
      this.pendingRequests.delete(key);
    }
  }

  // Batch similar requests
  async batchRequest<T>(
    batchKey: string,
    request: BatchRequest,
    batchSize: number = 10,
    batchDelay: number = 100
  ): Promise<T> {
    return new Promise((resolve, reject) => {
      if (!this.batchQueue.has(batchKey)) {
        this.batchQueue.set(batchKey, []);
      }

      const queue = this.batchQueue.get(batchKey)!;
      queue.push({ ...request, resolve, reject });

      // Clear existing timer
      const existingTimer = this.batchTimers.get(batchKey);
      if (existingTimer) {
        clearTimeout(existingTimer);
      }

      // Set new timer or execute immediately if batch is full
      if (queue.length >= batchSize) {
        this.executeBatch(batchKey);
      } else {
        const timer = setTimeout(() => {
          this.executeBatch(batchKey);
        }, batchDelay);
        this.batchTimers.set(batchKey, timer);
      }
    });
  }

  private async executeBatch(batchKey: string): Promise<void> {
    const queue = this.batchQueue.get(batchKey);
    if (!queue || queue.length === 0) return;

    this.batchQueue.set(batchKey, []);
    this.batchTimers.delete(batchKey);

    try {
      const results = await this.processBatch(batchKey, queue);
      
      queue.forEach((request, index) => {
        request.resolve(results[index]);
      });
    } catch (error) {
      queue.forEach(request => {
        request.reject(error);
      });
    }
  }

  private async processBatch(batchKey: string, requests: BatchRequest[]): Promise<any[]> {
    switch (batchKey) {
      case 'widget-data':
        return this.processWidgetDataBatch(requests);
      case 'validation':
        return this.processValidationBatch(requests);
      default:
        throw new Error(`Unknown batch type: ${batchKey}`);
    }
  }

  private async processWidgetDataBatch(requests: BatchRequest[]): Promise<any[]> {
    const batchRequest = {
      widget_ids: requests.map(r => r.widgetId),
      dashboard_id: requests[0].dashboardId,
      filters: requests[0].filters,
    };

    const response = await this.apiClient.post('/widgets/batch-data', batchRequest);
    
    return requests.map(request => {
      const result = response.results[request.widgetId];
      if (result) {
        return result.data;
      } else {
        const error = response.errors[request.widgetId];
        throw new Error(error?.message || 'Unknown error');
      }
    });
  }

  private async processValidationBatch(requests: BatchRequest[]): Promise<any[]> {
    const validationPromises = requests.map(request =>
      this.apiClient.post('/widgets/validate-config', {
        type: request.type,
        config: request.config,
      })
    );

    return Promise.all(validationPromises);
  }
}

interface BatchRequest {
  [key: string]: any;
  resolve?: (value: any) => void;
  reject?: (error: any) => void;
}
```

## SDK and Libraries

### TypeScript SDK

```typescript
// Main SDK export
export class CortexDashboardSDK {
  public readonly auth: AuthService;
  public readonly widgets: WidgetApiClient;
  public readonly dashboards: DashboardApiClient;
  public readonly exports: ExportApiClient;
  public readonly dataSources: DataSourceConnector;
  public readonly pipelines: ETLPipelineManager;
  public readonly realTime: RealTimeService;

  private apiClient: ApiClient;

  constructor(config: SDKConfig) {
    this.auth = new AuthService(config.baseUrl);
    this.apiClient = new RateLimitedApiClient(
      config.baseUrl,
      this.auth,
      config.rateLimits?.requestsPerMinute
    );

    // Initialize service clients
    this.widgets = new WidgetApiClient(this.apiClient);
    this.dashboards = new DashboardApiClient(this.apiClient);
    this.exports = new ExportApiClient(this.apiClient);
    this.dataSources = new DataSourceConnector(this.apiClient);
    this.pipelines = new ETLPipelineManager(this.apiClient);
    this.realTime = new RealTimeService(config.wsUrl, ''); // Token set after auth

    // Setup error handling
    if (config.errorHandler) {
      this.apiClient.addResponseInterceptor(config.errorHandler);
    }
  }

  async initialize(credentials?: LoginCredentials): Promise<void> {
    if (credentials) {
      await this.auth.login(credentials);
    }

    // Connect real-time services
    if (this.auth.token) {
      await this.realTime.connect();
    }
  }

  async dispose(): Promise<void> {
    this.realTime.disconnect();
    this.auth.logout();
  }
}

interface SDKConfig {
  baseUrl: string;
  wsUrl: string;
  rateLimits?: {
    requestsPerMinute?: number;
  };
  errorHandler?: ResponseInterceptor;
}

// SDK factory function
export function createCortexSDK(config: SDKConfig): CortexDashboardSDK {
  return new CortexDashboardSDK(config);
}

// React hooks for SDK
export function useCortexSDK(): CortexDashboardSDK {
  const context = useContext(CortexSDKContext);
  if (!context) {
    throw new Error('useCortexSDK must be used within CortexSDKProvider');
  }
  return context;
}

export const CortexSDKProvider: React.FC<{
  sdk: CortexDashboardSDK;
  children: React.ReactNode;
}> = ({ sdk, children }) => {
  return (
    <CortexSDKContext.Provider value={sdk}>
      {children}
    </CortexSDKContext.Provider>
  );
};

const CortexSDKContext = createContext<CortexDashboardSDK | null>(null);
```

## Integration Examples

### Complete Integration Example

```typescript
// Example: Custom dashboard application
import { createCortexSDK, CortexDashboardSDK } from '@cortex-dash/sdk';

class DashboardApplication {
  private sdk: CortexDashboardSDK;
  private currentDashboard: Dashboard | null = null;
  private widgets = new Map<string, WidgetData>();

  constructor() {
    this.sdk = createCortexSDK({
      baseUrl: 'https://api.cortexdash.com/v1',
      wsUrl: 'wss://api.cortexdash.com/ws',
      rateLimits: {
        requestsPerMinute: 120,
      },
      errorHandler: this.handleApiError.bind(this),
    });
  }

  async initialize(credentials: LoginCredentials): Promise<void> {
    await this.sdk.initialize(credentials);
    this.setupRealTimeUpdates();
  }

  async loadDashboard(dashboardId: string): Promise<void> {
    try {
      // Load dashboard configuration
      this.currentDashboard = await this.sdk.dashboards.getDashboard(dashboardId);
      
      // Load widget data in batch
      const widgetIds = this.currentDashboard.widgets.map(w => w.id);
      const widgetData = await this.sdk.widgets.getBatchWidgetData({
        widget_ids: widgetIds,
        dashboard_id: dashboardId,
      });

      // Store widget data
      Object.entries(widgetData.results).forEach(([widgetId, result]) => {
        this.widgets.set(widgetId, result.data);
      });

      // Setup real-time updates for widgets
      this.subscribeToWidgetUpdates(widgetIds);
      
      console.log(`Dashboard loaded with ${widgetIds.length} widgets`);
    } catch (error) {
      console.error('Failed to load dashboard:', error);
      throw error;
    }
  }

  async exportDashboard(format: 'pdf' | 'excel' = 'pdf'): Promise<Blob> {
    if (!this.currentDashboard) {
      throw new Error('No dashboard loaded');
    }

    // Create export
    const monitor = await this.sdk.exports.createExport({
      type: 'dashboard',
      dashboard_id: this.currentDashboard.id,
      format,
      options: {
        include_data: true,
        page_orientation: 'landscape',
      },
    });

    // Wait for completion with progress updates
    monitor.on('status', (status) => {
      console.log(`Export progress: ${status.progress?.percentage || 0}%`);
    });

    await monitor.waitForCompletion(300000); // 5 minute timeout
    return monitor.download();
  }

  private setupRealTimeUpdates(): void {
    // Subscribe to dashboard updates
    this.sdk.realTime.subscribeToDashboardUpdates(
      this.currentDashboard?.id!,
      (update) => {
        console.log('Dashboard updated:', update);
        this.handleDashboardUpdate(update);
      }
    );
  }

  private subscribeToWidgetUpdates(widgetIds: string[]): void {
    widgetIds.forEach(widgetId => {
      this.sdk.realTime.subscribeToWidgetUpdates(
        widgetId,
        (data) => {
          this.widgets.set(widgetId, data);
          this.handleWidgetUpdate(widgetId, data);
        }
      );
    });
  }

  private async handleApiError(response: Response): Promise<Response> {
    if (response.status === 401) {
      // Handle authentication error
      try {
        await this.sdk.auth.refreshToken();
        // Retry the original request
        return fetch(response.url, {
          method: response.request?.method || 'GET',
          headers: this.sdk.auth.getAuthHeaders(),
        });
      } catch (error) {
        // Redirect to login
        window.location.href = '/login';
      }
    }
    return response;
  }

  private handleDashboardUpdate(update: DashboardUpdate): void {
    // Handle dashboard configuration changes
    console.log('Dashboard configuration updated');
  }

  private handleWidgetUpdate(widgetId: string, data: WidgetData): void {
    // Update UI with new widget data
    console.log(`Widget ${widgetId} updated`);
  }

  async dispose(): Promise<void> {
    await this.sdk.dispose();
  }
}

// Usage
const app = new DashboardApplication();
await app.initialize({
  email: 'user@example.com',
  password: 'password',
});

await app.loadDashboard('dashboard-123');
const exportBlob = await app.exportDashboard('pdf');
```

## Best Practices

### API Integration Best Practices

1. **Authentication Management**
   - Implement automatic token refresh
   - Handle authentication errors gracefully
   - Store tokens securely

2. **Error Handling**
   - Implement comprehensive error handling
   - Use circuit breakers for unstable endpoints
   - Provide meaningful error messages to users

3. **Performance Optimization**
   - Use request batching where possible
   - Implement intelligent caching
   - Avoid unnecessary API calls

4. **Real-time Features**
   - Use appropriate real-time technology (WebSocket vs SSE)
   - Implement reconnection logic
   - Handle connection state properly

5. **Security**
   - Validate all input data
   - Use HTTPS for all communications
   - Implement proper CORS handling

6. **Monitoring and Logging**
   - Log API requests and responses
   - Monitor API performance
   - Track error rates and patterns

---

## Quick Reference

### SDK Initialization
```typescript
const sdk = createCortexSDK({
  baseUrl: 'https://api.cortexdash.com/v1',
  wsUrl: 'wss://api.cortexdash.com/ws'
});
await sdk.initialize(credentials);
```

### Common API Patterns
```typescript
// Widget data
const data = await sdk.widgets.getWidgetData(widgetId, dashboardId);

// Batch operations
const batchData = await sdk.widgets.getBatchWidgetData(request);

// Export with monitoring
const monitor = await sdk.exports.createExport(request);
await monitor.waitForCompletion();
const blob = await monitor.download();

// Real-time updates
sdk.realTime.subscribeToWidgetUpdates(widgetId, callback);
```

### Error Handling
```typescript
try {
  const result = await sdk.widgets.getWidgetData(widgetId, dashboardId);
} catch (error) {
  if (error instanceof ApiError) {
    if (error.isRetryable()) {
      // Implement retry logic
    } else if (error.isAuthError()) {
      // Handle authentication
    }
  }
}
```

---

*This guide provides comprehensive API integration patterns. For specific endpoint documentation, refer to the OpenAPI specification or individual API documentation files.*