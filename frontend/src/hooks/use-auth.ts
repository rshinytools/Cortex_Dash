// ABOUTME: Custom authentication hook for session management
// ABOUTME: Provides utilities for checking auth status and handling logout

import { useSession, signOut } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { useCallback } from 'react';

export function useAuth() {
  const { data: session, status } = useSession();
  const router = useRouter();

  const isAuthenticated = status === 'authenticated' && session?.accessToken;
  const isLoading = status === 'loading';

  const logout = useCallback(async () => {
    // Clear session on both client and server
    await signOut({ redirect: false });
    // Force reload to clear any cached data
    window.location.href = '/auth/login';
  }, []);

  const checkAuth = useCallback(() => {
    if (status === 'authenticated' && !session?.accessToken) {
      // Session exists but no valid token
      console.warn('Invalid session detected, logging out');
      logout();
      return false;
    }
    return isAuthenticated;
  }, [status, session, isAuthenticated, logout]);

  return {
    session,
    isAuthenticated,
    isLoading,
    logout,
    checkAuth,
    user: session?.user,
    accessToken: session?.accessToken,
  };
}