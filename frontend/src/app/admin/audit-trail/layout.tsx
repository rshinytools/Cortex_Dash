// ABOUTME: Layout file for audit trail page to force dynamic rendering
// ABOUTME: Ensures the page is not statically generated in production builds

export const dynamic = 'force-dynamic';
export const revalidate = 0;

export default function AuditTrailLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}