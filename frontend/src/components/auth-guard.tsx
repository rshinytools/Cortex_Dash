// ABOUTME: Authentication guard component that protects pages from unauthorized access
// ABOUTME: Redirects to login if user is not authenticated and shows loading state

'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';

interface AuthGuardProps {
  children: React.ReactNode;
  requiredRoles?: string[];
}

export function AuthGuard({ children, requiredRoles }: AuthGuardProps) {
  const { user, isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    // Only redirect if we're done loading and definitely not authenticated
    if (!isLoading) {
      console.log('AuthGuard check:', { 
        isAuthenticated, 
        user: user?.email, 
        role: user?.role,
        requiredRoles,
        path: window.location.pathname 
      });
      
      if (!isAuthenticated) {
        console.log('Not authenticated, redirecting to login');
        router.push('/login');
      } else if (requiredRoles && user && !requiredRoles.includes(user.role)) {
        // Check if user has required role
        console.log('User lacks required role, redirecting to dashboard');
        router.push('/dashboard');
      }
    }
  }, [isAuthenticated, isLoading, router, requiredRoles, user]);

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  if (requiredRoles && user && !requiredRoles.includes(user.role)) {
    return null;
  }

  return <>{children}</>;
}