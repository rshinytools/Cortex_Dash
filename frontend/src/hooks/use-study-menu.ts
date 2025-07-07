// ABOUTME: Hook for loading and managing study menu configurations
// ABOUTME: Handles menu fetching, caching, and permission filtering

import { useState, useEffect } from 'react'
import { useSession } from 'next-auth/react'

interface MenuItem {
  id: string
  label: string
  icon?: string
  path?: string
  children?: MenuItem[]
  permissions?: string[]
}

interface UseStudyMenuResult {
  menuItems: MenuItem[]
  loading: boolean
  error: string | null
  refetch: () => void
}

// Cache for menu items to avoid repeated API calls
const menuCache = new Map<string, { items: MenuItem[], timestamp: number }>()
const CACHE_DURATION = 5 * 60 * 1000 // 5 minutes

export function useStudyMenu(studyId: string): UseStudyMenuResult {
  const { data: session } = useSession()
  const [menuItems, setMenuItems] = useState<MenuItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const filterMenuItemsByPermissions = (items: MenuItem[], userPermissions: string[]): MenuItem[] => {
    return items
      .filter(item => {
        // If no permissions required, include the item
        if (!item.permissions || item.permissions.length === 0) {
          return true
        }
        // Check if user has at least one required permission
        return item.permissions.some(permission => userPermissions.includes(permission))
      })
      .map(item => ({
        ...item,
        children: item.children ? filterMenuItemsByPermissions(item.children, userPermissions) : undefined,
      }))
  }

  const fetchMenu = async () => {
    if (!studyId || !session?.user) {
      setLoading(false)
      return
    }

    // Check cache first
    const cached = menuCache.get(studyId)
    if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
      const userPermissions = session.user.permissions || []
      setMenuItems(filterMenuItemsByPermissions(cached.items, userPermissions))
      setLoading(false)
      return
    }

    try {
      setError(null)
      
      // First, get the study to find its menu template
      const studyResponse = await fetch(`/api/v1/studies/${studyId}`, {
        credentials: 'include',
      })

      if (!studyResponse.ok) {
        throw new Error('Failed to fetch study information')
      }

      const study = await studyResponse.json()
      
      if (!study.menu_template_id) {
        // No menu template assigned, use default or empty menu
        setMenuItems([])
        setLoading(false)
        return
      }

      // Fetch the menu template
      const menuResponse = await fetch(`/api/v1/menu-templates/${study.menu_template_id}`, {
        credentials: 'include',
      })

      if (!menuResponse.ok) {
        throw new Error('Failed to fetch menu template')
      }

      const menuTemplate = await menuResponse.json()
      
      // Cache the raw menu items
      menuCache.set(studyId, {
        items: menuTemplate.items,
        timestamp: Date.now(),
      })

      // Filter by user permissions
      const userPermissions = session.user.permissions || []
      const filteredItems = filterMenuItemsByPermissions(menuTemplate.items, userPermissions)
      
      setMenuItems(filteredItems)
    } catch (err) {
      console.error('Error fetching study menu:', err)
      setError(err instanceof Error ? err.message : 'Failed to load menu')
      setMenuItems([])
    } finally {
      setLoading(false)
    }
  }

  const refetch = () => {
    // Clear cache for this study
    menuCache.delete(studyId)
    setLoading(true)
    fetchMenu()
  }

  useEffect(() => {
    fetchMenu()
  }, [studyId, session])

  return {
    menuItems,
    loading,
    error,
    refetch,
  }
}