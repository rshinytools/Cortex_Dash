// ABOUTME: Widget system initializer component that loads all widgets on app startup
// ABOUTME: Ensures widget registry is populated before any dashboard renders

'use client';

import { useEffect } from 'react';
import { initializeWidgetSystem } from './widget-loader';

export function WidgetSystemInitializer({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    // Initialize widget system on mount
    initializeWidgetSystem().catch(console.error);
  }, []);

  return <>{children}</>;
}