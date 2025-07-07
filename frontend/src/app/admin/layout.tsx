// ABOUTME: Admin layout component that wraps all admin pages
// ABOUTME: Provides authentication check and consistent loading state

import { AuthCheck } from '@/components/auth-check';

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <AuthCheck requireAuth>{children}</AuthCheck>;
}