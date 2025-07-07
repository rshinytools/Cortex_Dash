// ABOUTME: Breadcrumb navigation component for hierarchical page navigation
// ABOUTME: Provides consistent breadcrumb UI across the application

import Link from 'next/link'
import { ChevronRight, Home } from 'lucide-react'
import { cn } from '@/lib/utils'

export interface BreadcrumbItem {
  label: string
  href?: string
  icon?: React.ReactNode
}

interface BreadcrumbsProps {
  items: BreadcrumbItem[]
  className?: string
}

export function Breadcrumbs({ items, className }: BreadcrumbsProps) {
  return (
    <nav 
      aria-label="Breadcrumb" 
      className={cn("flex items-center space-x-1 text-sm text-muted-foreground", className)}
    >
      <Link 
        href="/admin" 
        className="flex items-center hover:text-foreground transition-colors"
      >
        <Home className="h-4 w-4" />
      </Link>
      
      {items.map((item, index) => {
        const isLast = index === items.length - 1
        
        return (
          <div key={index} className="flex items-center">
            <ChevronRight className="h-4 w-4 mx-1" />
            {item.href && !isLast ? (
              <Link 
                href={item.href} 
                className="flex items-center hover:text-foreground transition-colors"
              >
                {item.icon && <span className="mr-1">{item.icon}</span>}
                {item.label}
              </Link>
            ) : (
              <span className={cn(
                "flex items-center",
                isLast && "text-foreground font-medium"
              )}>
                {item.icon && <span className="mr-1">{item.icon}</span>}
                {item.label}
              </span>
            )}
          </div>
        )
      })}
    </nav>
  )
}