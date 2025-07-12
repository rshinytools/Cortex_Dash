// ABOUTME: Hook for dashboard CRUD operations and state management
// ABOUTME: Provides interface for creating, reading, updating, and deleting dashboards

import { useState, useEffect } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { dashboardTemplatesApi, CreateUnifiedDashboardTemplateDto } from "@/lib/api/dashboard-templates"
import { MenuPosition } from "@/types/menu"

interface Dashboard {
  id: string
  name: string
  description?: string
  category?: string
  layout: any[]
  widgets: any[]
  studyCount?: number
  widgetCount?: number
  status: "active" | "draft"
  createdAt: string
  updatedAt: string
  menuTemplateId?: string
  menuLayouts?: Record<string, any[]>
}

interface CreateDashboardData {
  name: string
  description?: string
  category?: string
  layout: any[]
  widgets: any[]
  menuTemplateId?: string
  menuLayouts?: Record<string, any[]>
}

type UpdateDashboardData = Partial<CreateDashboardData>;

// For development, we'll use mock data
const MOCK_DASHBOARDS: Dashboard[] = [
  {
    id: "1",
    name: "Safety Monitoring Dashboard",
    description: "Monitor adverse events and safety signals",
    category: "safety",
    layout: [],
    widgets: [],
    studyCount: 3,
    widgetCount: 8,
    status: "active",
    createdAt: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString()
  },
  {
    id: "2",
    name: "Enrollment Overview",
    description: "Track patient enrollment and screening",
    category: "enrollment",
    layout: [],
    widgets: [],
    studyCount: 5,
    widgetCount: 6,
    status: "active",
    createdAt: new Date(Date.now() - 45 * 24 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString()
  },
  {
    id: "3",
    name: "Study Performance",
    description: "Overall study metrics and KPIs",
    category: "general",
    layout: [],
    widgets: [],
    studyCount: 2,
    widgetCount: 12,
    status: "draft",
    createdAt: new Date(Date.now() - 15 * 24 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString()
  }
]

// Mock storage for development
let mockDashboards = [...MOCK_DASHBOARDS]

export function useDashboards() {
  const queryClient = useQueryClient()

  // Fetch all dashboards
  const { data: dashboards = [], isLoading, error } = useQuery({
    queryKey: ["dashboards"],
    queryFn: async () => {
      try {
        const response = await dashboardTemplatesApi.list()
        // Transform API response to match our Dashboard interface
        return response.data.map(template => {
          const dashboards = template.template_structure?.dashboards || []
          const defaultDashboard = dashboards.find((d: any) => d.id === "default") || dashboards[0]
          
          return {
            id: template.id,
            name: template.name,
            description: template.description,
            category: template.category,
            layout: defaultDashboard?.layout || defaultDashboard?.widgets || [],
            widgets: defaultDashboard?.widgets || [],
            studyCount: 0, // TODO: Get from API
            widgetCount: defaultDashboard?.widgets?.length || 0,
            status: template.is_active ? "active" : "draft" as const,
            createdAt: template.created_at,
            updatedAt: template.updated_at,
            menuTemplateId: template.template_structure?.menu_template_id || "none",
            menuLayouts: dashboards.reduce((acc: any, dashboard: any) => ({
              ...acc,
              [dashboard.id]: dashboard.layout || dashboard.widgets || []
            }), {})
          }
        })
      } catch (error) {
        console.error("Failed to fetch dashboards:", error)
        // Fallback to mock data in case of error
        return mockDashboards
      }
    }
  })

  // Get single dashboard
  const getDashboard = async (id: string): Promise<Dashboard> => {
    try {
      const template = await dashboardTemplatesApi.get(id)
      
      // Extract dashboard layouts from template structure
      const dashboards = template.template_structure?.dashboards || []
      const defaultDashboard = dashboards.find((d: any) => d.id === "default") || dashboards[0]
      
      // Build menu layouts from dashboards
      const menuLayouts = dashboards.reduce((acc: any, dashboard: any) => ({
        ...acc,
        [dashboard.id]: dashboard.layout || dashboard.widgets || []
      }), {})
      
      console.log('Loaded dashboard:', {
        id: template.id,
        dashboards,
        defaultDashboard,
        menuLayouts,
        menu_template_id: template.template_structure?.menu_template_id
      })
      
      // Transform API response to match our Dashboard interface
      return {
        id: template.id,
        name: template.name,
        description: template.description,
        category: template.category,
        layout: defaultDashboard?.layout || defaultDashboard?.widgets || [],
        widgets: defaultDashboard?.widgets || [],
        studyCount: 0, // TODO: Get from API
        widgetCount: defaultDashboard?.widgets?.length || 0,
        status: template.is_active ? "active" : "draft" as const,
        createdAt: template.created_at,
        updatedAt: template.updated_at,
        menuTemplateId: template.template_structure?.menu_template_id || "none",
        menuLayouts
      }
    } catch (error) {
      console.error("Failed to fetch dashboard:", error)
      // Fallback to mock data
      const dashboard = mockDashboards.find(d => d.id === id)
      if (dashboard) {
        return dashboard
      }
      throw new Error("Dashboard not found")
    }
  }

  // Create dashboard mutation
  const createMutation = useMutation({
    mutationFn: async (data: CreateDashboardData) => {
      // In production, this would be an API call
      // const response = await axios.post("/api/v1/dashboards", data)
      // return response.data
      
      // Mock implementation
      return new Promise<Dashboard>((resolve) => {
        setTimeout(() => {
          const newDashboard: Dashboard = {
            id: String(Date.now()),
            ...data,
            studyCount: 0,
            widgetCount: data.widgets.length,
            status: "draft",
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString()
          }
          mockDashboards = [...mockDashboards, newDashboard]
          resolve(newDashboard)
        }, 500)
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dashboards"] })
    }
  })

  // Update dashboard mutation
  const updateMutation = useMutation({
    mutationFn: async ({ id, data }: { id: string; data: UpdateDashboardData }) => {
      try {
        // Get current dashboard to preserve existing structure
        const current = await dashboardTemplatesApi.get(id)
        
        // Build the template structure with menu and dashboard layouts
        const template_structure = {
          ...(current.template_structure || {}),
          menu_template_id: data.menuTemplateId,
          dashboards: data.menuLayouts 
            ? Object.entries(data.menuLayouts).map(([menuItemId, layout]) => ({
                id: menuItemId,
                layout: layout,
                widgets: layout
              }))
            : [{
                id: "default",
                layout: data.layout || [],
                widgets: data.widgets || []
              }]
        }
        
        // Transform our data format to API format
        const updateData: CreateUnifiedDashboardTemplateDto = {
          name: data.name || '',
          description: data.description || '',
          category: data.category || 'custom',
          menuTemplate: {
            name: `${data.name || 'Dashboard'} Menu`,
            position: MenuPosition.SIDEBAR,
            items: [],
            version: "1.0.0",
            isActive: true,
          },
          dashboardTemplates: []
        }
        
        console.log('Updating dashboard with data:', {
          id,
          updateData,
          menuLayouts: data.menuLayouts,
          layout: data.layout
        })
        
        const response = await dashboardTemplatesApi.update(id, updateData)
        
        // Transform back to our format
        const dashboards = response.template_structure?.dashboards || []
        const defaultDashboard = dashboards.find((d: any) => d.id === "default") || dashboards[0]
        
        return {
          id: response.id,
          name: response.name,
          description: response.description,
          category: response.category,
          layout: defaultDashboard?.layout || defaultDashboard?.widgets || [],
          widgets: defaultDashboard?.widgets || [],
          studyCount: 0,
          widgetCount: defaultDashboard?.widgets?.length || 0,
          status: response.is_active ? "active" : "draft" as const,
          createdAt: response.created_at,
          updatedAt: response.updated_at,
          menuTemplateId: data.menuTemplateId,
          menuLayouts: dashboards.reduce((acc: any, dashboard: any) => ({
            ...acc,
            [dashboard.id]: dashboard.layout || dashboard.widgets || []
          }), {})
        }
      } catch (error) {
        console.error("Failed to update dashboard:", error)
        // Fallback to mock update
        const index = mockDashboards.findIndex(d => d.id === id)
        if (index === -1) {
          throw new Error("Dashboard not found")
        }
        
        const updated = {
          ...mockDashboards[index],
          ...data,
          widgetCount: data.widgets?.length || mockDashboards[index].widgetCount,
          updatedAt: new Date().toISOString()
        }
        mockDashboards[index] = updated
        return updated
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dashboards"] })
    }
  })

  // Delete dashboard mutation
  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      // In production, this would be an API call
      // await axios.delete(`/api/v1/dashboards/${id}`)
      
      // Mock implementation
      return new Promise<void>((resolve, reject) => {
        setTimeout(() => {
          const index = mockDashboards.findIndex(d => d.id === id)
          if (index === -1) {
            reject(new Error("Dashboard not found"))
            return
          }
          mockDashboards = mockDashboards.filter(d => d.id !== id)
          resolve()
        }, 500)
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dashboards"] })
    }
  })

  return {
    dashboards,
    isLoading,
    error,
    getDashboard,
    createDashboard: createMutation.mutate,
    updateDashboard: (id: string, data: UpdateDashboardData) => 
      updateMutation.mutate({ id, data }),
    deleteDashboard: deleteMutation.mutate,
    isCreating: createMutation.isPending,
    isUpdating: updateMutation.isPending,
    isDeleting: deleteMutation.isPending
  }
}