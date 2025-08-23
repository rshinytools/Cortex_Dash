// ABOUTME: Secure API client that retrieves access token from memory
// ABOUTME: Works with httpOnly refresh tokens for enhanced security

import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios';

// Use the API URL as configured
const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_BASE_URL = baseUrl.endsWith('/api/v1') ? baseUrl : `${baseUrl}/api/v1`;

// Token getter function that will be set by auth context
let getAccessTokenFn: (() => Promise<string | null>) | null = null;

// Export function to set the token getter
export function setTokenGetter(getter: () => Promise<string | null>) {
  getAccessTokenFn = getter;
}

// Create axios instance
export const secureApiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Security: Include httpOnly cookies
});

// Request interceptor to add auth token from memory
secureApiClient.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    // Security: Get token from memory via auth context
    if (getAccessTokenFn) {
      try {
        const token = await getAccessTokenFn();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
      } catch (error) {
        console.error('Failed to get access token:', error);
      }
    }
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
secureApiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      // Try to refresh token
      if (getAccessTokenFn) {
        try {
          const newToken = await getAccessTokenFn();
          if (newToken) {
            originalRequest.headers.Authorization = `Bearer ${newToken}`;
            return secureApiClient(originalRequest);
          }
        } catch (refreshError) {
          console.error('Token refresh failed:', refreshError);
        }
      }
      
      // If refresh failed, redirect to login
      if (typeof window !== 'undefined') {
        // Security: Clear any remaining localStorage items
        localStorage.removeItem('auth_token');
        localStorage.removeItem('auth_user');
        sessionStorage.removeItem('auth_user');
        window.location.href = '/login';
      }
    }
    
    return Promise.reject(error);
  }
);

// Create a hook-friendly version that can be used in components
export function useSecureApiClient(): AxiosInstance {
  return secureApiClient;
}

// API error type
export interface ApiError {
  detail: string;
  code?: string;
  field?: string;
}

// Extract error message from axios error
export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as ApiError;
    return data?.detail || error.message || 'An unexpected error occurred';
  }
  return 'An unexpected error occurred';
}