// ABOUTME: Sidebar navigation component with role-based menu items
// ABOUTME: Provides navigation for different sections of the clinical dashboard

'use client';

import { useSession } from 'next-auth/react';
import { usePathname } from 'next/navigation';
import Link from 'next/link';
import { cn } from '@/lib/utils';
import {
  BarChart3,
  Database,
  FileText,
  FolderOpen,
  LayoutDashboard,
  Settings,
  Shield,
  Users,
  Activity,
  Calendar,
  ClipboardList,
  Plus,
  Building2,
  Package,
  Menu,
} from 'lucide-react';
import { UserRole } from '@/types';
import { ScrollArea } from '@/components/ui/scroll-area';

interface NavItem {
  title: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  roles?: UserRole[];
  children?: NavItem[];
}

const navItems: NavItem[] = [
  {
    title: 'Dashboard',
    href: '/dashboard',
    icon: LayoutDashboard,
    roles: [UserRole.STUDY_MANAGER, UserRole.DATA_ANALYST, UserRole.VIEWER], // Only for non-admin users
  },
  {
    title: 'Overview',
    href: '/admin',
    icon: LayoutDashboard,
    roles: [UserRole.SYSTEM_ADMIN, UserRole.ORG_ADMIN], // Admin users see this instead
  },
  {
    title: 'Studies',
    href: '/studies',
    icon: FolderOpen,
    roles: [UserRole.SYSTEM_ADMIN], // Only system admin sees this in sidebar
  },
  {
    title: 'Analytics',
    href: '/analytics',
    icon: BarChart3,
    roles: [UserRole.SYSTEM_ADMIN], // System admin feature
    children: [
      {
        title: 'Reports',
        href: '/analytics/reports',
        icon: FileText,
      },
      {
        title: 'Visualizations',
        href: '/analytics/visualizations',
        icon: BarChart3,
      },
    ],
  },
  {
    title: 'Dashboards',
    href: '/admin/dashboards',
    icon: LayoutDashboard,
    roles: [UserRole.SYSTEM_ADMIN], // System admin feature
    children: [
      {
        title: 'All Dashboards',
        href: '/admin/dashboards',
        icon: LayoutDashboard,
      },
      {
        title: 'Create Dashboard',
        href: '/admin/dashboards/new',
        icon: Plus,
      },
    ],
  },
  {
    title: 'Widget Library',
    href: '/admin/widgets',
    icon: Package,
    roles: [UserRole.SYSTEM_ADMIN], // System admin feature
  },
  {
    title: 'Menu Templates',
    href: '/admin/menus',
    icon: Menu,
    roles: [UserRole.SYSTEM_ADMIN], // System admin feature
  },
  {
    title: 'Settings',
    href: '/settings',
    icon: Settings,
    roles: [UserRole.SYSTEM_ADMIN, UserRole.ORG_ADMIN],
  },
];

export function Sidebar() {
  const { data: session } = useSession();
  const pathname = usePathname();

  const filteredNavItems = navItems.filter((item) => {
    if (!item.roles) return true;
    return item.roles.includes(session?.user?.role as UserRole);
  }).map((item) => ({
    ...item,
    children: item.children?.filter((child) => {
      if (!child.roles) return true;
      return child.roles.includes(session?.user?.role as UserRole);
    })
  }));

  return (
    <aside className="w-64 border-r bg-background dark:bg-gray-900">
      <ScrollArea className="h-full py-6">
        <nav className="space-y-2 px-3">
          {filteredNavItems.map((item) => (
            <div key={item.href}>
              <Link
                href={item.href}
                className={cn(
                  'flex items-center space-x-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                  pathname === item.href
                    ? 'bg-secondary text-secondary-foreground'
                    : 'text-muted-foreground hover:bg-secondary/50 hover:text-secondary-foreground'
                )}
              >
                <item.icon className="h-5 w-5" />
                <span>{item.title}</span>
              </Link>
              {item.children && pathname.startsWith(item.href) && (
                <div className="ml-9 mt-2 space-y-1">
                  {item.children.map((child) => (
                    <Link
                      key={child.href}
                      href={child.href}
                      className={cn(
                        'block rounded-lg px-3 py-2 text-sm transition-colors',
                        pathname === child.href
                          ? 'bg-secondary text-secondary-foreground'
                          : 'text-muted-foreground hover:bg-secondary/50 hover:text-secondary-foreground'
                      )}
                    >
                      {child.title}
                    </Link>
                  ))}
                </div>
              )}
            </div>
          ))}
        </nav>
      </ScrollArea>
    </aside>
  );
}