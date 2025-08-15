// ABOUTME: Simple home page that redirects to login or dashboard
// ABOUTME: No complex logic, just check auth and redirect

'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import { UserRole } from '@/types';

export default function HomePage() {
  const { user, isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isLoading) return;

    if (!isAuthenticated) {
      router.push('/login');
    } else if (user) {
      // Redirect based on role
      if (user.role === UserRole.SYSTEM_ADMIN || user.role === UserRole.ORG_ADMIN) {
        router.push('/admin');
      } else {
        router.push('/dashboard');
      }
    }
  }, [isAuthenticated, user, isLoading, router]);

  // Show loading while checking auth
  return (
    <div className="flex h-screen items-center justify-center">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
    </div>
  );
}