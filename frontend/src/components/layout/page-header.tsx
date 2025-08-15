// ABOUTME: Page header component with breadcrumbs and title
// ABOUTME: Provides consistent navigation and page structure

'use client';

import { ChevronRight, Home } from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Button } from '@/components/ui/button';

interface BreadcrumbItem {
  label: string;
  href?: string;
}

interface PageHeaderProps {
  title: string;
  description?: string;
  breadcrumbs?: BreadcrumbItem[];
  actions?: React.ReactNode;
}

export function PageHeader({ title, description, breadcrumbs, actions }: PageHeaderProps) {
  const pathname = usePathname();
  
  // Generate default breadcrumbs from pathname if not provided
  const defaultBreadcrumbs = (): BreadcrumbItem[] => {
    const paths = pathname.split('/').filter(Boolean);
    const items: BreadcrumbItem[] = [
      { label: 'Home', href: '/' }
    ];
    
    let currentPath = '';
    paths.forEach((path, index) => {
      currentPath += `/${path}`;
      const label = path
        .split('-')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
      
      items.push({
        label,
        href: index === paths.length - 1 ? undefined : currentPath
      });
    });
    
    return items;
  };
  
  const finalBreadcrumbs = breadcrumbs || defaultBreadcrumbs();
  
  return (
    <div className="border-b">
      <div className="flex flex-col gap-4 py-4">
        {/* Breadcrumbs */}
        <nav className="flex items-center text-sm text-muted-foreground">
          {finalBreadcrumbs.map((item, index) => (
            <div key={index} className="flex items-center">
              {index > 0 && <ChevronRight className="h-4 w-4 mx-2" />}
              {item.href ? (
                <Link
                  href={item.href}
                  className="hover:text-foreground transition-colors"
                >
                  {index === 0 && <Home className="h-4 w-4 mr-1 inline" />}
                  {item.label}
                </Link>
              ) : (
                <span className="text-foreground font-medium">
                  {item.label}
                </span>
              )}
            </div>
          ))}
        </nav>
        
        {/* Title and Actions */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">{title}</h1>
            {description && (
              <p className="text-muted-foreground mt-1">{description}</p>
            )}
          </div>
          {actions && <div className="flex items-center gap-2">{actions}</div>}
        </div>
      </div>
    </div>
  );
}