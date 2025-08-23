// ABOUTME: Secure authentication context - stores access token in memory only
// ABOUTME: Uses httpOnly refresh token for automatic token renewal

'use client';

import React, { createContext, useContext, useState, useEffect, useRef, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import axios, { AxiosError } from 'axios';
import { User, UserRole } from '@/types';
import { setTokenGetter } from '@/lib/api/secure-client';

// Create a silent axios instance that doesn't log errors to console
const silentAxios = axios.create();
silentAxios.interceptors.response.use(
  response => response,
  error => {
    // Silently return the error without logging to console
    return Promise.reject(error);
  }
);

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  updateUser: (userData: Partial<User>) => void;
  isAuthenticated: boolean;
  getAccessToken: () => Promise<string | null>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Security: Store access token in memory only, not in localStorage
let memoryToken: string | null = null;

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();
  const refreshTimeoutRef = useRef<NodeJS.Timeout>();

  // Security: Refresh access token using httpOnly refresh token
  const refreshAccessToken = useCallback(async (): Promise<string | null> => {
    try {
      const response = await silentAxios.post(
        'http://localhost:8000/api/v1/login/refresh-token',
        {},
        {
          withCredentials: true, // Security: Include httpOnly cookies
        }
      );

      const { access_token } = response.data;
      memoryToken = access_token;
      
      // Schedule next refresh (5 minutes before expiry, assuming 30 min tokens)
      if (refreshTimeoutRef.current) {
        clearTimeout(refreshTimeoutRef.current);
      }
      refreshTimeoutRef.current = setTimeout(() => {
        refreshAccessToken();
      }, 25 * 60 * 1000); // 25 minutes

      return access_token;
    } catch (error: any) {
      // Only log error if it's not a 401 (expected when no refresh token exists)
      if (error?.response?.status !== 401) {
        console.error('Token refresh failed:', error);
      }
      memoryToken = null;
      return null;
    }
  }, []);

  // Security: Get current access token or refresh if needed
  const getAccessToken = useCallback(async (): Promise<string | null> => {
    if (memoryToken) {
      return memoryToken;
    }
    
    // Try to refresh
    return await refreshAccessToken();
  }, [refreshAccessToken]);

  // Set token getter for secure API client
  useEffect(() => {
    setTokenGetter(getAccessToken);
  }, [getAccessToken]);

  // Check for existing session on mount
  useEffect(() => {
    const checkAuth = async () => {
      try {
        // Check if we have a stored user in sessionStorage first
        const storedUser = sessionStorage.getItem('auth_user');
        
        // Try to refresh token using httpOnly cookie
        const token = await refreshAccessToken();
        
        if (token) {
          // Fetch user data with the new token
          const response = await axios.get<User>(
            'http://localhost:8000/api/v1/users/me',
            {
              headers: {
                Authorization: `Bearer ${token}`,
              },
            }
          );
          
          setUser(response.data);
          // Security: Store user data in sessionStorage instead of localStorage
          sessionStorage.setItem('auth_user', JSON.stringify(response.data));
        } else if (storedUser) {
          // Clear stale session data if refresh failed
          sessionStorage.removeItem('auth_user');
        }
      } catch (error: any) {
        // Only log error if it's not a 401 (expected when no refresh token exists)
        if (error?.response?.status !== 401) {
          console.error('Session restoration failed:', error);
        }
        // Clear any stale session data
        sessionStorage.removeItem('auth_user');
        // User needs to login again
      } finally {
        setIsLoading(false);
      }
    };
    
    checkAuth();
    
    // Cleanup on unmount
    return () => {
      if (refreshTimeoutRef.current) {
        clearTimeout(refreshTimeoutRef.current);
      }
    };
  }, [refreshAccessToken]);

  const login = async (email: string, password: string) => {
    try {
      // Login to get tokens
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);
      
      const loginResponse = await silentAxios.post(
        'http://localhost:8000/api/v1/login/access-token',
        formData.toString(),
        {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
          withCredentials: true, // Security: Include cookies for refresh token
        }
      );

      const { access_token } = loginResponse.data;
      
      // Security: Store access token in memory only
      memoryToken = access_token;

      // Get user details
      const userResponse = await axios.get<User>(
        'http://localhost:8000/api/v1/users/me',
        {
          headers: {
            Authorization: `Bearer ${access_token}`,
          },
        }
      );

      const userData = userResponse.data;

      // Store user in state and sessionStorage
      setUser(userData);
      sessionStorage.setItem('auth_user', JSON.stringify(userData));
      
      // Schedule token refresh
      if (refreshTimeoutRef.current) {
        clearTimeout(refreshTimeoutRef.current);
      }
      refreshTimeoutRef.current = setTimeout(() => {
        refreshAccessToken();
      }, 25 * 60 * 1000); // 25 minutes

      // Redirect based on role
      if (userData.role === UserRole.SYSTEM_ADMIN || userData.role === UserRole.ORG_ADMIN) {
        router.push('/admin');
      } else {
        router.push('/dashboard');
      }
    } catch (error: any) {
      // Don't log authentication failures to console (they're expected for wrong credentials)
      // The UI will handle displaying the error message
      const errorMessage = error.response?.data?.detail || 'Invalid credentials';
      throw new Error(errorMessage);
    }
  };

  const logout = async () => {
    console.log('Logout initiated');
    try {
      // Call the backend logout endpoint to log the action and clear refresh token
      if (memoryToken) {
        console.log('Calling logout endpoint...');
        const response = await axios.post(
          'http://localhost:8000/api/v1/logout',
          {},
          {
            headers: {
              Authorization: `Bearer ${memoryToken}`,
            },
            withCredentials: true, // Security: Include cookies to clear refresh token
          }
        );
        console.log('Logout response:', response.data);
      }
    } catch (error) {
      // Log error but continue with logout
      console.error('Failed to log logout action:', error);
    }
    
    // Clear refresh timeout
    if (refreshTimeoutRef.current) {
      clearTimeout(refreshTimeoutRef.current);
    }
    
    // Security: Clear memory token and session storage
    memoryToken = null;
    setUser(null);
    sessionStorage.removeItem('auth_user');
    
    // Security: Clear any remaining localStorage items from old implementation
    localStorage.removeItem('auth_token');
    localStorage.removeItem('auth_user');
    
    router.push('/login');
  };

  const updateUser = (userData: Partial<User>) => {
    if (user) {
      const updatedUser = { ...user, ...userData };
      setUser(updatedUser);
      sessionStorage.setItem('auth_user', JSON.stringify(updatedUser));
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token: memoryToken,
        isLoading,
        login,
        logout,
        updateUser,
        isAuthenticated: !!memoryToken && !!user,
        getAccessToken,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}