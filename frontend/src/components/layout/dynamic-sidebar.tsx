// ABOUTME: Dynamic sidebar component that renders navigation based on menu templates
// ABOUTME: Loads menu configuration from API and handles permissions/visibility

'use client'

import { usePathname } from 'next/navigation'
import Link from 'next/link'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Skeleton } from '@/components/ui/skeleton'
import { useStudyMenu } from '@/hooks/use-study-menu'
import {
  ChevronDown,
  ChevronRight,
  Folder,
  FileText,
  BarChart2,
  Settings,
  Users,
  Database,
  Activity,
  Shield,
  Menu,
  LucideIcon,
} from 'lucide-react'
import { useState, useEffect } from 'react'

interface MenuItem {
  id: string
  label: string
  icon?: string
  path?: string
  children?: MenuItem[]
  permissions?: string[]
}

interface DynamicSidebarProps {
  studyId: string
  className?: string
  onNavigate?: () => void
}

const ICON_MAP: Record<string, LucideIcon> = {
  'folder': Folder,
  'file-text': FileText,
  'bar-chart-2': BarChart2,
  'settings': Settings,
  'users': Users,
  'database': Database,
  'activity': Activity,
  'shield': Shield,
  'menu': Menu,
}

export function DynamicSidebar({ studyId, className, onNavigate }: DynamicSidebarProps) {
  const pathname = usePathname()
  const { menuItems, loading, error } = useStudyMenu(studyId)
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set())

  useEffect(() => {
    // Auto-expand items that contain the current path
    if (menuItems.length > 0 && pathname) {
      const newExpanded = new Set<string>()
      
      const findActiveParents = (items: MenuItem[], parentIds: string[] = []) => {
        items.forEach((item) => {
          const itemPath = item.path?.replace('{studyId}', studyId)
          if (itemPath && pathname.startsWith(itemPath)) {
            parentIds.forEach(id => newExpanded.add(id))
          }
          if (item.children && item.children.length > 0) {
            findActiveParents(item.children, [...parentIds, item.id])
          }
        })
      }
      
      findActiveParents(menuItems)
      setExpandedItems(newExpanded)
    }
  }, [menuItems, pathname, studyId])

  const toggleExpanded = (itemId: string) => {
    setExpandedItems(prev => {
      const next = new Set(prev)
      if (next.has(itemId)) {
        next.delete(itemId)
      } else {
        next.add(itemId)
      }
      return next
    })
  }

  const isItemActive = (item: MenuItem): boolean => {
    if (!item.path) return false
    const itemPath = item.path.replace('{studyId}', studyId)
    return pathname === itemPath || pathname.startsWith(itemPath + '/')
  }

  const renderMenuItem = (item: MenuItem, depth: number = 0) => {
    const Icon = item.icon ? ICON_MAP[item.icon] || Folder : Folder
    const hasChildren = item.children && item.children.length > 0
    const isExpanded = expandedItems.has(item.id)
    const isActive = isItemActive(item)
    const itemPath = item.path?.replace('{studyId}', studyId)

    if (hasChildren) {
      return (
        <div key={item.id} className="w-full">
          <Button
            variant="ghost"
            className={cn(
              'w-full justify-start hover:bg-accent hover:text-accent-foreground',
              isActive && 'bg-accent text-accent-foreground',
              depth > 0 && 'pl-8'
            )}
            onClick={() => toggleExpanded(item.id)}
          >
            <span className="mr-2">
              {isExpanded ? (
                <ChevronDown className="h-4 w-4" />
              ) : (
                <ChevronRight className="h-4 w-4" />
              )}
            </span>
            <Icon className="mr-2 h-4 w-4" />
            <span className="flex-1 text-left">{item.label}</span>
          </Button>
          {isExpanded && (
            <div className="ml-4">
              {item.children.map((child) => renderMenuItem(child, depth + 1))}
            </div>
          )}
        </div>
      )
    }

    if (itemPath) {
      return (
        <Button
          key={item.id}
          variant="ghost"
          className={cn(
            'w-full justify-start hover:bg-accent hover:text-accent-foreground',
            isActive && 'bg-accent text-accent-foreground',
            depth > 0 && 'pl-12'
          )}
          asChild
          onClick={onNavigate}
        >
          <Link href={itemPath}>
            <Icon className="mr-2 h-4 w-4" />
            <span className="flex-1 text-left">{item.label}</span>
          </Link>
        </Button>
      )
    }

    return (
      <Button
        key={item.id}
        variant="ghost"
        className={cn(
          'w-full justify-start hover:bg-accent hover:text-accent-foreground cursor-default',
          depth > 0 && 'pl-12'
        )}
        disabled
      >
        <Icon className="mr-2 h-4 w-4" />
        <span className="flex-1 text-left">{item.label}</span>
      </Button>
    )
  }

  if (loading) {
    return (
      <div className={cn('flex h-full flex-col gap-2 p-4', className)}>
        <div className="space-y-2">
          {[...Array(5)].map((_, i) => (
            <Skeleton key={i} className="h-10 w-full" />
          ))}
        </div>
      </div>
    )
  }

  if (error || menuItems.length === 0) {
    return (
      <div className={cn('flex h-full flex-col p-4', className)}>
        <div className="flex flex-col items-center justify-center h-full text-center">
          <Menu className="h-8 w-8 text-muted-foreground mb-2" />
          <p className="text-sm text-muted-foreground">
            {error ? 'Failed to load menu' : 'No menu configured'}
          </p>
        </div>
      </div>
    )
  }

  return (
    <ScrollArea className={cn('flex h-full flex-col', className)}>
      <div className="flex flex-col gap-1 p-4">
        {menuItems.map((item) => renderMenuItem(item))}
      </div>
    </ScrollArea>
  )
}