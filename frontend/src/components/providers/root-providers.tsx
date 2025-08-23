// ABOUTME: Client-side root providers wrapper to prevent remounting issues
// ABOUTME: Consolidates all providers in a single client component

'use client';

import { AuthProvider } from "@/lib/auth-context";
import { RBACProvider } from "@/lib/rbac-context";
import { QueryProvider } from "@/components/providers/query-provider";
import { ThemeProvider } from "@/components/providers/theme-provider";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from 'sonner';
import { WidgetSystemInitializer } from "@/components/widgets/widget-system-initializer";

export function RootProviders({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider
      attribute="class"
      defaultTheme="system"
      enableSystem
      disableTransitionOnChange
    >
      <AuthProvider>
        <RBACProvider>
          <QueryProvider>
            <WidgetSystemInitializer>
              {children}
            </WidgetSystemInitializer>
            <Toaster />
            <Sonner />
          </QueryProvider>
        </RBACProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}