// ABOUTME: Hook for loading and managing study menu configurations from dashboard templates
// ABOUTME: Extracts menu structure from unified dashboard templates with permission filtering

import { useState, useEffect } from 'react'
import { useAuth } from '@/lib/auth-context'

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
  const { user } = useAuth()
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
    if (!studyId || !user) {
      setLoading(false)
      return
    }

    // Check cache first
    const cached = menuCache.get(studyId)
    if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
      const userPermissions = (user as any).permissions || []
      setMenuItems(filterMenuItemsByPermissions(cached.items, userPermissions))
      setLoading(false)
      return
    }

    try {
      setError(null)
      
      // First, get the study to find its menu template
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const studyResponse = await fetch(`${baseUrl}/studies/${studyId}/`, {
        credentials: 'include',
        headers: {
          'Authorization': `Bearer ${(user as any).access_token}`,
        },
      })

      if (!studyResponse.ok) {
        throw new Error('Failed to fetch study information')
      }

      const study = await studyResponse.json()
      
      if (!study.dashboard_template_id) {
        // No dashboard template assigned, use default or empty menu
        setMenuItems([])
        setLoading(false)
        return
      }

      // Fetch the dashboard template which includes the menu structure
      const templateResponse = await fetch(`${baseUrl}/dashboard-templates/${study.dashboard_template_id}`, {
        credentials: 'include',
        headers: {
          'Authorization': `Bearer ${(user as any).access_token}`,
        },
      })

      if (!templateResponse.ok) {
        throw new Error('Failed to fetch dashboard template')
      }

      const dashboardTemplate = await templateResponse.json()
      
      // Extract menu items from the template structure
      // Check both old and new structure formats
      const menuStructure = dashboardTemplate.template_structure?.menuStructure || dashboardTemplate.template_structure?.menu
      const menuItems = menuStructure?.items || []
      
      // Cache the raw menu items
      menuCache.set(studyId, {
        items: menuItems,
        timestamp: Date.now(),
      })

      // Filter by user permissions
      const userPermissions = (user as any).permissions || []
      const filteredItems = filterMenuItemsByPermissions(menuItems, userPermissions)
      
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
  }, [studyId, user])

  return {
    menuItems,
    loading,
    error,
    refetch,
  }
}