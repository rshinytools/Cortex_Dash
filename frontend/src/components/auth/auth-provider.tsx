// ABOUTME: Authentication provider component that wraps the app with NextAuth session
// ABOUTME: Provides session context to all child components

'use client';

import { SessionProvider } from 'next-auth/react';
import { ReactNode } from 'react';

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  return (
    <SessionProvider
      // Re-fetch session every 5 minutes
      refetchInterval={5 * 60}
      // Re-fetch session when window regains focus
      refetchOnWindowFocus={true}
    >
      {children}
    </SessionProvider>
  );
}