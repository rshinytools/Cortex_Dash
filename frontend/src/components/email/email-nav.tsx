// ABOUTME: Email navigation component for consistent navigation across email pages
// ABOUTME: Provides tabs navigation between settings, templates, queue, and history

'use client';

import { useRouter, usePathname } from 'next/navigation';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Settings, FileText, Clock, History } from 'lucide-react';

export function EmailNav() {
  const router = useRouter();
  const pathname = usePathname();
  
  // Determine active tab based on current path
  const getActiveTab = () => {
    if (pathname.includes('/email/templates')) return 'templates';
    if (pathname.includes('/email/queue')) return 'queue';
    if (pathname.includes('/email/history')) return 'history';
    return 'settings';
  };

  return (
    <Tabs value={getActiveTab()} className="w-full">
      <TabsList className="grid w-full grid-cols-4">
        <TabsTrigger 
          value="settings" 
          onClick={() => router.push('/admin/email')}
          className="flex items-center gap-2"
        >
          <Settings className="h-4 w-4" />
          Settings
        </TabsTrigger>
        <TabsTrigger 
          value="templates"
          onClick={() => router.push('/admin/email/templates')}
          className="flex items-center gap-2"
        >
          <FileText className="h-4 w-4" />
          Templates
        </TabsTrigger>
        <TabsTrigger 
          value="queue"
          onClick={() => router.push('/admin/email/queue')}
          className="flex items-center gap-2"
        >
          <Clock className="h-4 w-4" />
          Queue
        </TabsTrigger>
        <TabsTrigger 
          value="history"
          onClick={() => router.push('/admin/email/history')}
          className="flex items-center gap-2"
        >
          <History className="h-4 w-4" />
          History
        </TabsTrigger>
      </TabsList>
    </Tabs>
  );
}