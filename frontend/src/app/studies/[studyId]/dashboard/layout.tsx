// ABOUTME: Dashboard-specific layout that completely bypasses the parent layout
// ABOUTME: Dashboard page has its own navigation built-in, no sidebar needed

'use client';

// This layout completely replaces the parent layout for the dashboard route
export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  // Return a complete layout structure that doesn't inherit from parent
  return (
    <div className="min-h-screen bg-background">
      {children}
    </div>
  );
}