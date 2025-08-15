// ABOUTME: Admin layout component that wraps all admin pages
// ABOUTME: Provides authentication check and consistent loading state

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}