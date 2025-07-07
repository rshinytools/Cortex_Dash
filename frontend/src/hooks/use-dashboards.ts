// ABOUTME: Hook for dashboard CRUD operations and state management
// ABOUTME: Provides interface for creating, reading, updating, and deleting dashboards

import { useState, useEffect } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import axios from "axios"

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
}

interface CreateDashboardData {
  name: string
  description?: string
  category?: string
  layout: any[]
  widgets: any[]
}

interface UpdateDashboardData extends Partial<CreateDashboardData> {}

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
      // In production, this would be an API call
      // const response = await axios.get("/api/v1/dashboards")
      // return response.data
      
      // Mock implementation
      return new Promise<Dashboard[]>((resolve) => {
        setTimeout(() => resolve(mockDashboards), 500)
      })
    }
  })

  // Get single dashboard
  const getDashboard = async (id: string): Promise<Dashboard> => {
    // In production, this would be an API call
    // const response = await axios.get(`/api/v1/dashboards/${id}`)
    // return response.data
    
    // Mock implementation
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        const dashboard = mockDashboards.find(d => d.id === id)
        if (dashboard) {
          resolve(dashboard)
        } else {
          reject(new Error("Dashboard not found"))
        }
      }, 300)
    })
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
      // In production, this would be an API call
      // const response = await axios.patch(`/api/v1/dashboards/${id}`, data)
      // return response.data
      
      // Mock implementation
      return new Promise<Dashboard>((resolve, reject) => {
        setTimeout(() => {
          const index = mockDashboards.findIndex(d => d.id === id)
          if (index === -1) {
            reject(new Error("Dashboard not found"))
            return
          }
          
          const updated = {
            ...mockDashboards[index],
            ...data,
            widgetCount: data.widgets?.length || mockDashboards[index].widgetCount,
            updatedAt: new Date().toISOString()
          }
          mockDashboards[index] = updated
          resolve(updated)
        }, 500)
      })
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