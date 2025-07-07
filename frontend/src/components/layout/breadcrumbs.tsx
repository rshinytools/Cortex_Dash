// ABOUTME: Dynamic breadcrumbs component that generates navigation trail from menu structure
// ABOUTME: Automatically builds breadcrumb path based on current location and menu hierarchy

'use client'

import { usePathname } from 'next/navigation'
import Link from 'next/link'
import { ChevronRight, Home } from 'lucide-react'
import { Fragment } from 'react'
import { useStudyMenu } from '@/hooks/use-study-menu'

interface BreadcrumbsProps {
  studyId?: string
  homeLabel?: string
  homeHref?: string
}

interface MenuItem {
  id: string
  label: string
  icon?: string
  path?: string
  children?: MenuItem[]
  permissions?: string[]
}

interface BreadcrumbItem {
  label: string
  href?: string
}

export function Breadcrumbs({ studyId, homeLabel = 'Home', homeHref = '/' }: BreadcrumbsProps) {
  const pathname = usePathname()
  const { menuItems } = useStudyMenu(studyId || '')

  const findBreadcrumbPath = (
    items: MenuItem[],
    targetPath: string,
    currentPath: BreadcrumbItem[] = []
  ): BreadcrumbItem[] | null => {
    for (const item of items) {
      const itemPath = item.path?.replace('{studyId}', studyId || '')
      
      if (itemPath === targetPath) {
        return [...currentPath, { label: item.label, href: itemPath }]
      }
      
      if (item.children && item.children.length > 0) {
        const childPath = findBreadcrumbPath(
          item.children,
          targetPath,
          [...currentPath, { label: item.label, href: itemPath }]
        )
        if (childPath) return childPath
      }
    }
    return null
  }

  const generateBreadcrumbs = (): BreadcrumbItem[] => {
    const breadcrumbs: BreadcrumbItem[] = [{ label: homeLabel, href: homeHref }]

    // If we have a study menu, try to find the path in the menu structure
    if (studyId && menuItems.length > 0) {
      const menuPath = findBreadcrumbPath(menuItems, pathname)
      if (menuPath) {
        return [...breadcrumbs, ...menuPath]
      }
    }

    // Fallback to path-based breadcrumbs
    const pathSegments = pathname.split('/').filter(Boolean)
    let currentPath = ''

    pathSegments.forEach((segment, index) => {
      currentPath += `/${segment}`
      
      // Skip IDs and certain segments
      if (segment.match(/^[0-9a-fA-F-]+$/) || segment === 'edit' || segment === 'new') {
        return
      }

      let label = segment
        .split('-')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ')

      // Special case handling
      if (segment === 'studies' && index === 0) {
        label = 'Studies'
      } else if (segment === 'admin') {
        label = 'Admin'
      } else if (segment === 'dashboard') {
        label = 'Dashboard'
      }

      breadcrumbs.push({
        label,
        href: index === pathSegments.length - 1 ? undefined : currentPath,
      })
    })

    return breadcrumbs
  }

  const breadcrumbs = generateBreadcrumbs()

  if (breadcrumbs.length <= 1) {
    return null
  }

  return (
    <nav aria-label="Breadcrumb" className="flex items-center space-x-1 text-sm text-muted-foreground">
      {breadcrumbs.map((breadcrumb, index) => (
        <Fragment key={index}>
          {index > 0 && <ChevronRight className="h-4 w-4" />}
          {breadcrumb.href ? (
            <Link
              href={breadcrumb.href}
              className="hover:text-foreground transition-colors"
            >
              {index === 0 && <Home className="h-4 w-4 inline mr-1" />}
              {breadcrumb.label}
            </Link>
          ) : (
            <span className="text-foreground font-medium">
              {index === 0 && <Home className="h-4 w-4 inline mr-1" />}
              {breadcrumb.label}
            </span>
          )}
        </Fragment>
      ))}
    </nav>
  )
}