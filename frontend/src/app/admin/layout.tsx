// ABOUTME: Admin layout component that wraps all admin pages
// ABOUTME: Provides authentication check and consistent loading state

'use client';

import { useEffect } from 'react';
import { AuthGuard } from '@/components/auth-guard';

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  useEffect(() => {
    console.log('Admin layout mounted');
    return () => console.log('Admin layout unmounted');
  }, []);
  
  // Security: Protect all admin routes with authentication and role check
  return (
    <AuthGuard requiredRoles={['system_admin', 'org_admin']}>
      {children}
    </AuthGuard>
  );
}