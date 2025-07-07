// ABOUTME: Custom hooks for widget management operations
// ABOUTME: Provides React Query hooks for widget CRUD operations with caching and optimistic updates

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { widgetsApi, CreateWidgetRequest, UpdateWidgetRequest, WidgetFilters } from '@/lib/api/widgets'
import { WidgetDefinition } from '@/types/widget'
import { PaginationParams } from '@/types'
import { useToast } from '@/hooks/use-toast'

// Query keys factory
const widgetKeys = {
  all: ['widgets'] as const,
  lists: () => [...widgetKeys.all, 'list'] as const,
  list: (params?: PaginationParams & WidgetFilters) => [...widgetKeys.lists(), params] as const,
  details: () => [...widgetKeys.all, 'detail'] as const,
  detail: (id: string) => [...widgetKeys.details(), id] as const,
}

// Hook to get all widgets with pagination and filtering
export function useWidgets(params?: PaginationParams & WidgetFilters) {
  return useQuery({
    queryKey: widgetKeys.list(params),
    queryFn: () => widgetsApi.getWidgets(params),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

// Hook to get a single widget by ID
export function useWidget(id: string) {
  return useQuery({
    queryKey: widgetKeys.detail(id),
    queryFn: () => widgetsApi.getWidget(id),
    enabled: !!id,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

// Hook to create a new widget
export function useCreateWidget() {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: (widget: CreateWidgetRequest) => widgetsApi.createWidget(widget),
    onSuccess: (data) => {
      // Invalidate all widget lists
      queryClient.invalidateQueries({ queryKey: widgetKeys.lists() })
      
      // Add the new widget to the cache
      queryClient.setQueryData(widgetKeys.detail(data.id), data)
      
      toast({
        title: 'Widget created',
        description: `${data.name} has been created successfully.`,
      })
    },
    onError: (error: any) => {
      toast({
        title: 'Error creating widget',
        description: error.response?.data?.detail || 'An error occurred while creating the widget.',
        variant: 'destructive',
      })
    },
  })
}

// Hook to update a widget
export function useUpdateWidget(id: string) {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: (updates: UpdateWidgetRequest) => widgetsApi.updateWidget(id, updates),
    onMutate: async (updates) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: widgetKeys.detail(id) })

      // Snapshot the previous value
      const previousWidget = queryClient.getQueryData<WidgetDefinition>(widgetKeys.detail(id))

      // Optimistically update the widget
      if (previousWidget) {
        queryClient.setQueryData(widgetKeys.detail(id), {
          ...previousWidget,
          ...updates,
          updatedAt: new Date().toISOString(),
        })
      }

      return { previousWidget }
    },
    onError: (error: any, _, context) => {
      // If the mutation fails, use the context returned from onMutate to roll back
      if (context?.previousWidget) {
        queryClient.setQueryData(widgetKeys.detail(id), context.previousWidget)
      }
      
      toast({
        title: 'Error updating widget',
        description: error.response?.data?.detail || 'An error occurred while updating the widget.',
        variant: 'destructive',
      })
    },
    onSuccess: (data) => {
      // Update the cache with the server response
      queryClient.setQueryData(widgetKeys.detail(id), data)
      
      // Invalidate all widget lists
      queryClient.invalidateQueries({ queryKey: widgetKeys.lists() })
      
      toast({
        title: 'Widget updated',
        description: `${data.name} has been updated successfully.`,
      })
    },
  })
}

// Hook to delete a widget
export function useDeleteWidget() {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: (id: string) => widgetsApi.deleteWidget(id),
    onMutate: async (id) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: widgetKeys.lists() })
      await queryClient.cancelQueries({ queryKey: widgetKeys.detail(id) })
    },
    onSuccess: (_, id) => {
      // Remove from cache
      queryClient.removeQueries({ queryKey: widgetKeys.detail(id) })
      
      // Invalidate all widget lists
      queryClient.invalidateQueries({ queryKey: widgetKeys.lists() })
      
      toast({
        title: 'Widget deleted',
        description: 'The widget has been deleted successfully.',
      })
    },
    onError: (error: any) => {
      toast({
        title: 'Error deleting widget',
        description: error.response?.data?.detail || 'An error occurred while deleting the widget.',
        variant: 'destructive',
      })
    },
  })
}

// Hook to toggle widget status
export function useToggleWidgetStatus(id: string) {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: (isActive: boolean) => widgetsApi.toggleWidgetStatus(id, isActive),
    onMutate: async (isActive) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: widgetKeys.detail(id) })

      // Snapshot the previous value
      const previousWidget = queryClient.getQueryData<WidgetDefinition>(widgetKeys.detail(id))

      // Optimistically update the widget
      if (previousWidget) {
        queryClient.setQueryData(widgetKeys.detail(id), {
          ...previousWidget,
          isActive,
          updatedAt: new Date().toISOString(),
        })
      }

      return { previousWidget }
    },
    onError: (error: any, _, context) => {
      // If the mutation fails, use the context returned from onMutate to roll back
      if (context?.previousWidget) {
        queryClient.setQueryData(widgetKeys.detail(id), context.previousWidget)
      }
      
      toast({
        title: 'Error updating widget status',
        description: error.response?.data?.detail || 'An error occurred while updating the widget status.',
        variant: 'destructive',
      })
    },
    onSuccess: (data) => {
      // Update the cache with the server response
      queryClient.setQueryData(widgetKeys.detail(id), data)
      
      // Invalidate all widget lists
      queryClient.invalidateQueries({ queryKey: widgetKeys.lists() })
      
      toast({
        title: 'Widget status updated',
        description: `${data.name} has been ${data.isActive ? 'activated' : 'deactivated'}.`,
      })
    },
  })
}

// Hook to duplicate a widget
export function useDuplicateWidget() {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: ({ id, name }: { id: string; name: string }) => widgetsApi.duplicateWidget(id, name),
    onSuccess: (data) => {
      // Invalidate all widget lists
      queryClient.invalidateQueries({ queryKey: widgetKeys.lists() })
      
      // Add the new widget to the cache
      queryClient.setQueryData(widgetKeys.detail(data.id), data)
      
      toast({
        title: 'Widget duplicated',
        description: `${data.name} has been created successfully.`,
      })
    },
    onError: (error: any) => {
      toast({
        title: 'Error duplicating widget',
        description: error.response?.data?.detail || 'An error occurred while duplicating the widget.',
        variant: 'destructive',
      })
    },
  })
}