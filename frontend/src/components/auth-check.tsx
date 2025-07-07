// ABOUTME: Auth check component that validates session and shows loading state
// ABOUTME: Prevents showing content with expired tokens and handles redirects

'use client';

import { useSession } from 'next-auth/react';
import { useRouter, usePathname } from 'next/navigation';
import { useEffect } from 'react';
import { Loader2 } from 'lucide-react';

interface AuthCheckProps {
  children: React.ReactNode;
  requireAuth?: boolean;
}

export function AuthCheck({ children, requireAuth = true }: AuthCheckProps) {
  const { data: session, status } = useSession();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    // If auth is required and user is not authenticated, redirect to login
    if (requireAuth && status === 'unauthenticated') {
      router.push('/auth/login');
    }
  }, [requireAuth, status, router]);

  // Show loading state while checking authentication
  if (status === 'loading') {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-primary" />
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  // If auth is required and user is not authenticated, show loading
  // (redirect will happen in useEffect)
  if (requireAuth && status === 'unauthenticated') {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-primary" />
          <p className="text-muted-foreground">Redirecting to login...</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}