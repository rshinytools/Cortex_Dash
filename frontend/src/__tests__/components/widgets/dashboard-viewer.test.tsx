// ABOUTME: Comprehensive test suite for dashboard viewer functionality
// ABOUTME: Tests dashboard rendering, layout management, interactions, and real-time updates

import React from 'react'
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

// Dashboard Components
import DashboardViewer from '@/components/widgets/dashboard-viewer'
import DashboardRenderer from '@/components/widgets/dashboard-renderer'
import DashboardToolbar from '@/components/widgets/dashboard-toolbar'
import DashboardEditMode from '@/components/widgets/dashboard-edit-mode'
import FilterManager from '@/components/widgets/filter-manager'

// Test utilities
const createQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: { retry: false },
    mutations: { retry: false },
  },
})

const renderWithProviders = (component: React.ReactElement) => {
  const queryClient = createQueryClient()
  return render(
    <QueryClientProvider client={queryClient}>
      {component}
    </QueryClientProvider>
  )
}

// Mock data
const mockDashboard = global.createMockDashboard({
  id: 'dashboard-1',
  name: 'Clinical Overview Dashboard',
  description: 'Main dashboard for clinical trial overview',
  widgets: [
    global.createMockWidget({
      id: 'widget-1',
      type: 'metric',
      title: 'Total Subjects',
      position: { x: 0, y: 0, w: 3, h: 2 },
      config: { value: 150, format: 'number' }
    }),
    global.createMockWidget({
      id: 'widget-2',
      type: 'chart',
      title: 'Enrollment by Site',
      position: { x: 3, y: 0, w: 6, h: 4 },
      config: { 
        chartType: 'bar',
        data: [
          { category: 'Site 001', value: 45 },
          { category: 'Site 002', value: 38 }
        ]
      }
    }),
    global.createMockWidget({
      id: 'widget-3',
      type: 'table',
      title: 'Recent Enrollments',
      position: { x: 0, y: 4, w: 9, h: 4 },
      config: {
        data: [
          { subject_id: 'S001', site: 'Site 001', date: '2024-01-01' },
          { subject_id: 'S002', site: 'Site 002', date: '2024-01-02' }
        ]
      }
    })
  ],
  layout: {
    grid: { columns: 12, rows: 8 }
  },
  filters: [
    { id: 'site-filter', field: 'site', type: 'select', label: 'Study Site' },
    { id: 'date-filter', field: 'enrollment_date', type: 'daterange', label: 'Enrollment Date' }
  ]
})

describe('DashboardViewer', () => {
  it('renders dashboard with all widgets', () => {
    renderWithProviders(<DashboardViewer dashboard={mockDashboard} />)
    
    expect(screen.getByText('Clinical Overview Dashboard')).toBeInTheDocument()
    expect(screen.getByText('Total Subjects')).toBeInTheDocument()
    expect(screen.getByText('Enrollment by Site')).toBeInTheDocument()
    expect(screen.getByText('Recent Enrollments')).toBeInTheDocument()
  })

  it('displays dashboard description', () => {
    renderWithProviders(<DashboardViewer dashboard={mockDashboard} />)
    
    expect(screen.getByText('Main dashboard for clinical trial overview')).toBeInTheDocument()
  })

  it('supports fullscreen mode', async () => {
    const user = userEvent.setup()
    renderWithProviders(<DashboardViewer dashboard={mockDashboard} />)
    
    const fullscreenButton = screen.getByTitle('Enter fullscreen')
    await user.click(fullscreenButton)
    
    expect(document.querySelector('.dashboard-fullscreen')).toBeInTheDocument()
  })

  it('supports print mode', async () => {
    const user = userEvent.setup()
    
    // Mock window.print
    const printSpy = jest.spyOn(window, 'print').mockImplementation(() => {})
    
    renderWithProviders(<DashboardViewer dashboard={mockDashboard} />)
    
    const printButton = screen.getByTitle('Print dashboard')
    await user.click(printButton)
    
    expect(printSpy).toHaveBeenCalled()
    
    printSpy.mockRestore()
  })

  it('handles loading state', () => {
    renderWithProviders(<DashboardViewer dashboard={mockDashboard} isLoading={true} />)
    
    expect(screen.getByTestId('dashboard-skeleton')).toBeInTheDocument()
  })

  it('handles error state', () => {
    const error = 'Failed to load dashboard'
    renderWithProviders(<DashboardViewer dashboard={mockDashboard} error={error} />)
    
    expect(screen.getByText('Error loading dashboard')).toBeInTheDocument()
    expect(screen.getByText(error)).toBeInTheDocument()
  })

  it('supports responsive layout', () => {
    // Mock window size
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 768, // Mobile size
    })
    
    renderWithProviders(<DashboardViewer dashboard={mockDashboard} />)
    
    // Should adapt layout for mobile
    expect(document.querySelector('.dashboard-mobile')).toBeInTheDocument()
  })
})

describe('DashboardRenderer', () => {
  it('renders widgets in grid layout', () => {
    renderWithProviders(<DashboardRenderer dashboard={mockDashboard} />)
    
    const gridContainer = screen.getByTestId('dashboard-grid')
    expect(gridContainer).toBeInTheDocument()
    
    // Check widget positions
    const metricWidget = screen.getByTestId('widget-widget-1')
    expect(metricWidget).toHaveStyle({
      gridColumn: 'span 3',
      gridRow: 'span 2'
    })
  })

  it('handles widget interactions', async () => {
    const user = userEvent.setup()
    const onWidgetClick = jest.fn()
    
    renderWithProviders(
      <DashboardRenderer dashboard={mockDashboard} onWidgetClick={onWidgetClick} />
    )
    
    const metricWidget = screen.getByTestId('widget-widget-1')
    await user.click(metricWidget)
    
    expect(onWidgetClick).toHaveBeenCalledWith('widget-1')
  })

  it('supports widget drag and drop in edit mode', async () => {
    const user = userEvent.setup()
    const onLayoutChange = jest.fn()
    
    renderWithProviders(
      <DashboardRenderer 
        dashboard={mockDashboard} 
        editMode={true}
        onLayoutChange={onLayoutChange}
      />
    )
    
    const widget = screen.getByTestId('widget-widget-1')
    const dragHandle = within(widget).getByTestId('drag-handle')
    
    // Simulate drag
    await user.click(dragHandle)
    // Drag and drop simulation would need more setup
    
    expect(screen.getByTestId('drop-zone')).toBeInTheDocument()
  })

  it('handles widget resize in edit mode', async () => {
    const user = userEvent.setup()
    const onLayoutChange = jest.fn()
    
    renderWithProviders(
      <DashboardRenderer 
        dashboard={mockDashboard} 
        editMode={true}
        onLayoutChange={onLayoutChange}
      />
    )
    
    const widget = screen.getByTestId('widget-widget-1')
    const resizeHandle = within(widget).getByTestId('resize-handle')
    
    // Simulate resize
    await user.click(resizeHandle)
    
    expect(screen.getByTestId('resize-indicator')).toBeInTheDocument()
  })

  it('preserves widget aspect ratios', () => {
    const constrainedDashboard = {
      ...mockDashboard,
      layout: {
        ...mockDashboard.layout,
        preserveAspectRatio: true
      }
    }
    
    renderWithProviders(<DashboardRenderer dashboard={constrainedDashboard} />)
    
    const chartWidget = screen.getByTestId('widget-widget-2')
    expect(chartWidget).toHaveClass('aspect-ratio-preserved')
  })

  it('handles empty dashboard', () => {
    const emptyDashboard = { ...mockDashboard, widgets: [] }
    renderWithProviders(<DashboardRenderer dashboard={emptyDashboard} />)
    
    expect(screen.getByText('No widgets configured')).toBeInTheDocument()
    expect(screen.getByText('Add widgets to get started')).toBeInTheDocument()
  })
})

describe('DashboardToolbar', () => {
  const mockToolbarProps = {
    dashboard: mockDashboard,
    editMode: false,
    onEditToggle: jest.fn(),
    onRefresh: jest.fn(),
    onExport: jest.fn(),
    onShare: jest.fn()
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders all toolbar actions', () => {
    renderWithProviders(<DashboardToolbar {...mockToolbarProps} />)
    
    expect(screen.getByTitle('Refresh dashboard')).toBeInTheDocument()
    expect(screen.getByTitle('Export dashboard')).toBeInTheDocument()
    expect(screen.getByTitle('Share dashboard')).toBeInTheDocument()
    expect(screen.getByTitle('Edit dashboard')).toBeInTheDocument()
  })

  it('handles edit mode toggle', async () => {
    const user = userEvent.setup()
    renderWithProviders(<DashboardToolbar {...mockToolbarProps} />)
    
    const editButton = screen.getByTitle('Edit dashboard')
    await user.click(editButton)
    
    expect(mockToolbarProps.onEditToggle).toHaveBeenCalledWith(true)
  })

  it('shows save/cancel buttons in edit mode', () => {
    renderWithProviders(<DashboardToolbar {...mockToolbarProps} editMode={true} />)
    
    expect(screen.getByText('Save')).toBeInTheDocument()
    expect(screen.getByText('Cancel')).toBeInTheDocument()
  })

  it('handles dashboard refresh', async () => {
    const user = userEvent.setup()
    renderWithProviders(<DashboardToolbar {...mockToolbarProps} />)
    
    const refreshButton = screen.getByTitle('Refresh dashboard')
    await user.click(refreshButton)
    
    expect(mockToolbarProps.onRefresh).toHaveBeenCalled()
  })

  it('opens export dialog', async () => {
    const user = userEvent.setup()
    renderWithProviders(<DashboardToolbar {...mockToolbarProps} />)
    
    const exportButton = screen.getByTitle('Export dashboard')
    await user.click(exportButton)
    
    await waitFor(() => {
      expect(screen.getByText('Export Dashboard')).toBeInTheDocument()
      expect(screen.getByText('PDF')).toBeInTheDocument()
      expect(screen.getByText('Excel')).toBeInTheDocument()
    })
  })

  it('displays last updated timestamp', () => {
    const dashboardWithTimestamp = {
      ...mockDashboard,
      lastUpdated: '2024-01-07T10:30:00Z'
    }
    
    renderWithProviders(<DashboardToolbar {...mockToolbarProps} dashboard={dashboardWithTimestamp} />)
    
    expect(screen.getByText(/Last updated/)).toBeInTheDocument()
  })

  it('shows auto-refresh status', () => {
    renderWithProviders(<DashboardToolbar {...mockToolbarProps} autoRefresh={true} refreshInterval={30} />)
    
    expect(screen.getByText('Auto-refresh: 30s')).toBeInTheDocument()
    expect(screen.getByTestId('auto-refresh-indicator')).toBeInTheDocument()
  })
})

describe('DashboardEditMode', () => {
  const mockEditProps = {
    dashboard: mockDashboard,
    onLayoutChange: jest.fn(),
    onWidgetAdd: jest.fn(),
    onWidgetRemove: jest.fn(),
    onWidgetEdit: jest.fn()
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('shows widget palette', () => {
    renderWithProviders(<DashboardEditMode {...mockEditProps} />)
    
    expect(screen.getByText('Widget Palette')).toBeInTheDocument()
    expect(screen.getByText('Metric')).toBeInTheDocument()
    expect(screen.getByText('Chart')).toBeInTheDocument()
    expect(screen.getByText('Table')).toBeInTheDocument()
  })

  it('handles widget addition from palette', async () => {
    const user = userEvent.setup()
    renderWithProviders(<DashboardEditMode {...mockEditProps} />)
    
    const metricWidget = screen.getByTestId('palette-metric')
    await user.click(metricWidget)
    
    expect(mockEditProps.onWidgetAdd).toHaveBeenCalledWith('metric')
  })

  it('shows widget edit controls', () => {
    renderWithProviders(<DashboardEditMode {...mockEditProps} />)
    
    // Each widget should have edit controls
    const widgets = screen.getAllByTestId(/^widget-/)
    widgets.forEach(widget => {
      expect(within(widget).getByTitle('Edit widget')).toBeInTheDocument()
      expect(within(widget).getByTitle('Delete widget')).toBeInTheDocument()
    })
  })

  it('handles widget removal', async () => {
    const user = userEvent.setup()
    renderWithProviders(<DashboardEditMode {...mockEditProps} />)
    
    const firstWidget = screen.getByTestId('widget-widget-1')
    const deleteButton = within(firstWidget).getByTitle('Delete widget')
    
    await user.click(deleteButton)
    
    // Should show confirmation dialog
    expect(screen.getByText('Delete Widget')).toBeInTheDocument()
    
    const confirmButton = screen.getByText('Delete')
    await user.click(confirmButton)
    
    expect(mockEditProps.onWidgetRemove).toHaveBeenCalledWith('widget-1')
  })

  it('shows grid guidelines', () => {
    renderWithProviders(<DashboardEditMode {...mockEditProps} />)
    
    expect(screen.getByTestId('grid-guidelines')).toBeInTheDocument()
    expect(document.querySelectorAll('.grid-line')).toHaveLength(20) // 12 columns + 8 rows
  })

  it('supports widget duplication', async () => {
    const user = userEvent.setup()
    renderWithProviders(<DashboardEditMode {...mockEditProps} />)
    
    const widget = screen.getByTestId('widget-widget-1')
    const duplicateButton = within(widget).getByTitle('Duplicate widget')
    
    await user.click(duplicateButton)
    
    expect(mockEditProps.onWidgetAdd).toHaveBeenCalledWith('metric', expect.objectContaining({
      title: 'Total Subjects (Copy)',
      config: expect.objectContaining({ value: 150 })
    }))
  })
})

describe('FilterManager', () => {
  const mockFilters = [
    {
      id: 'site-filter',
      field: 'site',
      type: 'select' as const,
      label: 'Study Site',
      options: [
        { value: 'site-001', label: 'Site 001' },
        { value: 'site-002', label: 'Site 002' }
      ]
    },
    {
      id: 'date-filter',
      field: 'enrollment_date',
      type: 'daterange' as const,
      label: 'Enrollment Date'
    }
  ]

  const mockFilterProps = {
    filters: mockFilters,
    values: {},
    onChange: jest.fn()
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders all filter controls', () => {
    renderWithProviders(<FilterManager {...mockFilterProps} />)
    
    expect(screen.getByText('Study Site')).toBeInTheDocument()
    expect(screen.getByText('Enrollment Date')).toBeInTheDocument()
  })

  it('handles select filter changes', async () => {
    const user = userEvent.setup()
    renderWithProviders(<FilterManager {...mockFilterProps} />)
    
    const siteSelect = screen.getByLabelText('Study Site')
    await user.click(siteSelect)
    
    const option = screen.getByText('Site 001')
    await user.click(option)
    
    expect(mockFilterProps.onChange).toHaveBeenCalledWith({
      'site-filter': 'site-001'
    })
  })

  it('handles date range filter changes', async () => {
    const user = userEvent.setup()
    renderWithProviders(<FilterManager {...mockFilterProps} />)
    
    const dateInput = screen.getByLabelText('Enrollment Date')
    await user.click(dateInput)
    
    // Date picker should open
    expect(screen.getByTestId('date-picker')).toBeInTheDocument()
  })

  it('shows filter clear button when filters are applied', () => {
    const propsWithValues = {
      ...mockFilterProps,
      values: { 'site-filter': 'site-001' }
    }
    
    renderWithProviders(<FilterManager {...propsWithValues} />)
    
    expect(screen.getByTitle('Clear all filters')).toBeInTheDocument()
  })

  it('handles filter clearing', async () => {
    const user = userEvent.setup()
    const propsWithValues = {
      ...mockFilterProps,
      values: { 'site-filter': 'site-001' }
    }
    
    renderWithProviders(<FilterManager {...propsWithValues} />)
    
    const clearButton = screen.getByTitle('Clear all filters')
    await user.click(clearButton)
    
    expect(mockFilterProps.onChange).toHaveBeenCalledWith({})
  })

  it('supports collapsed/expanded states', async () => {
    const user = userEvent.setup()
    renderWithProviders(<FilterManager {...mockFilterProps} collapsible={true} />)
    
    const toggleButton = screen.getByTitle('Toggle filters')
    await user.click(toggleButton)
    
    expect(screen.getByTestId('filters-collapsed')).toBeInTheDocument()
  })
})

describe('Dashboard Real-time Updates', () => {
  it('handles real-time data updates', async () => {
    const { rerender } = renderWithProviders(<DashboardViewer dashboard={mockDashboard} />)
    
    // Initial render
    expect(screen.getByText('150')).toBeInTheDocument()
    
    // Update dashboard data
    const updatedDashboard = {
      ...mockDashboard,
      widgets: [
        {
          ...mockDashboard.widgets[0],
          config: { ...mockDashboard.widgets[0].config, value: 175 }
        },
        ...mockDashboard.widgets.slice(1)
      ]
    }
    
    rerender(<DashboardViewer dashboard={updatedDashboard} />)
    
    await waitFor(() => {
      expect(screen.getByText('175')).toBeInTheDocument()
    })
  })

  it('shows update indicators for changed widgets', async () => {
    renderWithProviders(<DashboardViewer dashboard={mockDashboard} showUpdateIndicators={true} />)
    
    // Simulate widget update
    fireEvent(window, new CustomEvent('widget-updated', {
      detail: { widgetId: 'widget-1' }
    }))
    
    await waitFor(() => {
      expect(screen.getByTestId('update-indicator-widget-1')).toBeInTheDocument()
    })
  })

  it('handles websocket connection status', () => {
    renderWithProviders(<DashboardViewer dashboard={mockDashboard} realtimeEnabled={true} />)
    
    // Should show connection status
    expect(screen.getByTestId('realtime-status')).toBeInTheDocument()
  })
})

describe('Dashboard Performance', () => {
  it('renders large dashboards efficiently', () => {
    const largeDashboard = {
      ...mockDashboard,
      widgets: Array(50).fill(null).map((_, i) => global.createMockWidget({
        id: `widget-${i}`,
        title: `Widget ${i}`,
        position: { x: i % 12, y: Math.floor(i / 12), w: 3, h: 2 }
      }))
    }
    
    const start = performance.now()
    renderWithProviders(<DashboardViewer dashboard={largeDashboard} />)
    const end = performance.now()
    
    // Should render within reasonable time
    expect(end - start).toBeLessThan(1000) // 1 second
  })

  it('implements virtual scrolling for large widget lists', () => {
    const largeDashboard = {
      ...mockDashboard,
      widgets: Array(200).fill(null).map((_, i) => global.createMockWidget({
        id: `widget-${i}`,
        position: { x: 0, y: i * 2, w: 12, h: 2 }
      }))
    }
    
    renderWithProviders(<DashboardViewer dashboard={largeDashboard} virtualScrolling={true} />)
    
    // Should only render visible widgets
    const renderedWidgets = screen.getAllByTestId(/^widget-/)
    expect(renderedWidgets.length).toBeLessThan(50) // Much less than 200
  })
})

describe('Dashboard Accessibility', () => {
  it('supports keyboard navigation', async () => {
    const user = userEvent.setup()
    renderWithProviders(<DashboardViewer dashboard={mockDashboard} />)
    
    // Tab through widgets
    await user.tab()
    expect(document.activeElement).toHaveAttribute('data-testid', 'widget-widget-1')
    
    await user.tab()
    expect(document.activeElement).toHaveAttribute('data-testid', 'widget-widget-2')
  })

  it('has proper ARIA structure', () => {
    renderWithProviders(<DashboardViewer dashboard={mockDashboard} />)
    
    expect(screen.getByRole('main')).toBeInTheDocument()
    expect(screen.getByLabelText('Clinical Overview Dashboard')).toBeInTheDocument()
    
    const widgets = screen.getAllByRole('region')
    expect(widgets).toHaveLength(3) // One for each widget
  })

  it('supports screen reader announcements', async () => {
    renderWithProviders(<DashboardViewer dashboard={mockDashboard} />)
    
    // Simulate data update
    fireEvent(window, new CustomEvent('dashboard-updated'))
    
    await waitFor(() => {
      expect(screen.getByRole('status')).toHaveTextContent('Dashboard updated')
    })
  })

  it('provides skip links for large dashboards', () => {
    renderWithProviders(<DashboardViewer dashboard={mockDashboard} />)
    
    expect(screen.getByText('Skip to dashboard content')).toBeInTheDocument()
    expect(screen.getByText('Skip to filters')).toBeInTheDocument()
  })
})