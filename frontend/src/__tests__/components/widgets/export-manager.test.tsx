// ABOUTME: Comprehensive test suite for dashboard export functionality
// ABOUTME: Tests export formats, options, progress tracking, and error handling

import React from 'react'
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

// Export Components
import ExportManager from '@/components/widgets/export-manager'
import ScheduledExports from '@/components/widgets/scheduled-exports'

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
  widgets: [
    global.createMockWidget({
      id: 'widget-1',
      type: 'metric',
      title: 'Total Subjects',
      config: { value: 150 }
    }),
    global.createMockWidget({
      id: 'widget-2',
      type: 'chart',
      title: 'Enrollment Chart',
      config: { chartType: 'bar' }
    })
  ]
})

// Mock fetch for API calls
const mockFetch = jest.fn()
global.fetch = mockFetch

describe('ExportManager', () => {
  const mockExportProps = {
    dashboard: mockDashboard,
    onExportComplete: jest.fn(),
    onExportError: jest.fn()
  }

  beforeEach(() => {
    jest.clearAllMocks()
    mockFetch.mockClear()
  })

  it('renders export dialog with format options', () => {
    renderWithProviders(<ExportManager {...mockExportProps} open={true} />)
    
    expect(screen.getByText('Export Dashboard')).toBeInTheDocument()
    expect(screen.getByText('Select Export Format')).toBeInTheDocument()
    
    // Check available formats
    expect(screen.getByLabelText('PDF')).toBeInTheDocument()
    expect(screen.getByLabelText('Excel')).toBeInTheDocument()
    expect(screen.getByLabelText('PowerPoint')).toBeInTheDocument()
    expect(screen.getByLabelText('PNG Image')).toBeInTheDocument()
  })

  it('shows format-specific options when format is selected', async () => {
    const user = userEvent.setup()
    renderWithProviders(<ExportManager {...mockExportProps} open={true} />)
    
    // Select PDF format
    const pdfOption = screen.getByLabelText('PDF')
    await user.click(pdfOption)
    
    // Should show PDF-specific options
    expect(screen.getByText('Page Orientation')).toBeInTheDocument()
    expect(screen.getByLabelText('Portrait')).toBeInTheDocument()
    expect(screen.getByLabelText('Landscape')).toBeInTheDocument()
    expect(screen.getByText('Page Size')).toBeInTheDocument()
    expect(screen.getByText('Include Header/Footer')).toBeInTheDocument()
  })

  it('shows Excel-specific options for Excel export', async () => {
    const user = userEvent.setup()
    renderWithProviders(<ExportManager {...mockExportProps} open={true} />)
    
    const excelOption = screen.getByLabelText('Excel')
    await user.click(excelOption)
    
    expect(screen.getByText('Include Charts')).toBeInTheDocument()
    expect(screen.getByText('Separate Sheets')).toBeInTheDocument()
    expect(screen.getByText('Apply Formatting')).toBeInTheDocument()
  })

  it('shows PowerPoint-specific options for PowerPoint export', async () => {
    const user = userEvent.setup()
    renderWithProviders(<ExportManager {...mockExportProps} open={true} />)
    
    const pptOption = screen.getByLabelText('PowerPoint')
    await user.click(pptOption)
    
    expect(screen.getByText('Slides per Widget')).toBeInTheDocument()
    expect(screen.getByText('Include Title Slide')).toBeInTheDocument()
    expect(screen.getByText('Template')).toBeInTheDocument()
  })

  it('shows image-specific options for image export', async () => {
    const user = userEvent.setup()
    renderWithProviders(<ExportManager {...mockExportProps} open={true} />)
    
    const imageOption = screen.getByLabelText('PNG Image')
    await user.click(imageOption)
    
    expect(screen.getByText('Resolution')).toBeInTheDocument()
    expect(screen.getByText('Width')).toBeInTheDocument()
    expect(screen.getByText('Height')).toBeInTheDocument()
    expect(screen.getByText('Quality')).toBeInTheDocument()
  })

  it('handles export initiation', async () => {
    const user = userEvent.setup()
    
    // Mock successful export response
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        success: true,
        exportId: 'export-123',
        estimatedTime: 30
      })
    })
    
    renderWithProviders(<ExportManager {...mockExportProps} open={true} />)
    
    // Select format and start export
    const pdfOption = screen.getByLabelText('PDF')
    await user.click(pdfOption)
    
    const exportButton = screen.getByText('Start Export')
    await user.click(exportButton)
    
    expect(mockFetch).toHaveBeenCalledWith('/api/v1/dashboards/dashboard-1/export', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        format: 'pdf',
        options: expect.any(Object)
      })
    })
  })

  it('shows progress during export', async () => {
    const user = userEvent.setup()
    
    // Mock export start
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        success: true,
        exportId: 'export-123'
      })
    })
    
    renderWithProviders(<ExportManager {...mockExportProps} open={true} />)
    
    const pdfOption = screen.getByLabelText('PDF')
    await user.click(pdfOption)
    
    const exportButton = screen.getByText('Start Export')
    await user.click(exportButton)
    
    await waitFor(() => {
      expect(screen.getByText('Exporting...')).toBeInTheDocument()
      expect(screen.getByRole('progressbar')).toBeInTheDocument()
    })
  })

  it('handles export completion', async () => {
    const user = userEvent.setup()
    
    // Mock export completion
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true, exportId: 'export-123' })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          status: 'completed',
          downloadUrl: '/downloads/dashboard-export.pdf',
          fileSize: 1024000
        })
      })
    
    renderWithProviders(<ExportManager {...mockExportProps} open={true} />)
    
    const pdfOption = screen.getByLabelText('PDF')
    await user.click(pdfOption)
    
    const exportButton = screen.getByText('Start Export')
    await user.click(exportButton)
    
    await waitFor(() => {
      expect(screen.getByText('Export Complete')).toBeInTheDocument()
      expect(screen.getByText('Download')).toBeInTheDocument()
      expect(screen.getByText('1.0 MB')).toBeInTheDocument()
    })
    
    expect(mockExportProps.onExportComplete).toHaveBeenCalledWith({
      downloadUrl: '/downloads/dashboard-export.pdf',
      fileSize: 1024000
    })
  })

  it('handles export errors', async () => {
    const user = userEvent.setup()
    
    // Mock export error
    mockFetch.mockRejectedValueOnce(new Error('Export failed'))
    
    renderWithProviders(<ExportManager {...mockExportProps} open={true} />)
    
    const pdfOption = screen.getByLabelText('PDF')
    await user.click(pdfOption)
    
    const exportButton = screen.getByText('Start Export')
    await user.click(exportButton)
    
    await waitFor(() => {
      expect(screen.getByText('Export Failed')).toBeInTheDocument()
      expect(screen.getByText('Export failed')).toBeInTheDocument()
    })
    
    expect(mockExportProps.onExportError).toHaveBeenCalledWith('Export failed')
  })

  it('supports export cancellation', async () => {
    const user = userEvent.setup()
    
    // Mock ongoing export
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true, exportId: 'export-123' })
    })
    
    renderWithProviders(<ExportManager {...mockExportProps} open={true} />)
    
    const pdfOption = screen.getByLabelText('PDF')
    await user.click(pdfOption)
    
    const exportButton = screen.getByText('Start Export')
    await user.click(exportButton)
    
    // Cancel export
    await waitFor(() => {
      expect(screen.getByText('Cancel')).toBeInTheDocument()
    })
    
    const cancelButton = screen.getByText('Cancel')
    await user.click(cancelButton)
    
    expect(mockFetch).toHaveBeenCalledWith('/api/v1/exports/export-123/cancel', {
      method: 'POST'
    })
  })

  it('validates export options', async () => {
    const user = userEvent.setup()
    renderWithProviders(<ExportManager {...mockExportProps} open={true} />)
    
    // Try to export without selecting format
    const exportButton = screen.getByText('Start Export')
    await user.click(exportButton)
    
    expect(screen.getByText('Please select an export format')).toBeInTheDocument()
  })

  it('shows export history', async () => {
    const user = userEvent.setup()
    
    // Mock export history
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        exports: [
          {
            id: 'export-1',
            format: 'pdf',
            createdAt: '2024-01-07T10:00:00Z',
            status: 'completed',
            fileSize: 512000
          },
          {
            id: 'export-2',
            format: 'excel',
            createdAt: '2024-01-06T15:30:00Z',
            status: 'completed',
            fileSize: 256000
          }
        ]
      })
    })
    
    renderWithProviders(<ExportManager {...mockExportProps} open={true} />)
    
    const historyTab = screen.getByText('Export History')
    await user.click(historyTab)
    
    await waitFor(() => {
      expect(screen.getByText('PDF')).toBeInTheDocument()
      expect(screen.getByText('Excel')).toBeInTheDocument()
      expect(screen.getByText('512 KB')).toBeInTheDocument()
      expect(screen.getByText('256 KB')).toBeInTheDocument()
    })
  })

  it('supports bulk widget selection for export', async () => {
    const user = userEvent.setup()
    renderWithProviders(<ExportManager {...mockExportProps} open={true} />)
    
    // Go to widget selection tab
    const widgetTab = screen.getByText('Select Widgets')
    await user.click(widgetTab)
    
    // Should show all widgets with checkboxes
    expect(screen.getByText('Select widgets to include in export')).toBeInTheDocument()
    expect(screen.getByLabelText('Total Subjects')).toBeInTheDocument()
    expect(screen.getByLabelText('Enrollment Chart')).toBeInTheDocument()
    
    // Uncheck one widget
    const chartCheckbox = screen.getByLabelText('Enrollment Chart')
    await user.click(chartCheckbox)
    
    expect(screen.getByText('1 of 2 widgets selected')).toBeInTheDocument()
  })
})

describe('ScheduledExports', () => {
  const mockSchedules = [
    {
      id: 'schedule-1',
      name: 'Daily Summary Report',
      format: 'pdf',
      frequency: 'daily',
      time: '09:00',
      recipients: ['user1@example.com', 'user2@example.com'],
      lastRun: '2024-01-07T09:00:00Z',
      nextRun: '2024-01-08T09:00:00Z',
      status: 'active'
    },
    {
      id: 'schedule-2',
      name: 'Weekly Data Export',
      format: 'excel',
      frequency: 'weekly',
      dayOfWeek: 'monday',
      time: '08:00',
      recipients: ['manager@example.com'],
      lastRun: '2024-01-01T08:00:00Z',
      nextRun: '2024-01-08T08:00:00Z',
      status: 'active'
    }
  ]

  const mockScheduleProps = {
    dashboard: mockDashboard,
    schedules: mockSchedules,
    onScheduleCreate: jest.fn(),
    onScheduleUpdate: jest.fn(),
    onScheduleDelete: jest.fn()
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders scheduled export list', () => {
    renderWithProviders(<ScheduledExports {...mockScheduleProps} />)
    
    expect(screen.getByText('Scheduled Exports')).toBeInTheDocument()
    expect(screen.getByText('Daily Summary Report')).toBeInTheDocument()
    expect(screen.getByText('Weekly Data Export')).toBeInTheDocument()
  })

  it('shows schedule details', () => {
    renderWithProviders(<ScheduledExports {...mockScheduleProps} />)
    
    // Check daily schedule details
    const dailySchedule = screen.getByTestId('schedule-schedule-1')
    expect(within(dailySchedule).getByText('Daily at 09:00')).toBeInTheDocument()
    expect(within(dailySchedule).getByText('PDF')).toBeInTheDocument()
    expect(within(dailySchedule).getByText('2 recipients')).toBeInTheDocument()
    
    // Check weekly schedule details
    const weeklySchedule = screen.getByTestId('schedule-schedule-2')
    expect(within(weeklySchedule).getByText('Weekly on Monday at 08:00')).toBeInTheDocument()
    expect(within(weeklySchedule).getByText('Excel')).toBeInTheDocument()
  })

  it('supports creating new schedule', async () => {
    const user = userEvent.setup()
    renderWithProviders(<ScheduledExports {...mockScheduleProps} />)
    
    const createButton = screen.getByText('New Schedule')
    await user.click(createButton)
    
    expect(screen.getByText('Create Export Schedule')).toBeInTheDocument()
    
    // Fill in schedule details
    const nameInput = screen.getByLabelText('Schedule Name')
    await user.type(nameInput, 'Monthly Report')
    
    const formatSelect = screen.getByLabelText('Export Format')
    await user.click(formatSelect)
    await user.click(screen.getByText('PDF'))
    
    const frequencySelect = screen.getByLabelText('Frequency')
    await user.click(frequencySelect)
    await user.click(screen.getByText('Monthly'))
    
    const saveButton = screen.getByText('Create Schedule')
    await user.click(saveButton)
    
    expect(mockScheduleProps.onScheduleCreate).toHaveBeenCalledWith(
      expect.objectContaining({
        name: 'Monthly Report',
        format: 'pdf',
        frequency: 'monthly'
      })
    )
  })

  it('supports editing existing schedule', async () => {
    const user = userEvent.setup()
    renderWithProviders(<ScheduledExports {...mockScheduleProps} />)
    
    const editButton = screen.getByTestId('edit-schedule-schedule-1')
    await user.click(editButton)
    
    expect(screen.getByText('Edit Export Schedule')).toBeInTheDocument()
    
    // Modify schedule
    const nameInput = screen.getByLabelText('Schedule Name')
    await user.clear(nameInput)
    await user.type(nameInput, 'Updated Daily Report')
    
    const saveButton = screen.getByText('Save Changes')
    await user.click(saveButton)
    
    expect(mockScheduleProps.onScheduleUpdate).toHaveBeenCalledWith(
      'schedule-1',
      expect.objectContaining({
        name: 'Updated Daily Report'
      })
    )
  })

  it('supports deleting schedule', async () => {
    const user = userEvent.setup()
    renderWithProviders(<ScheduledExports {...mockScheduleProps} />)
    
    const deleteButton = screen.getByTestId('delete-schedule-schedule-1')
    await user.click(deleteButton)
    
    expect(screen.getByText('Delete Schedule')).toBeInTheDocument()
    expect(screen.getByText('Are you sure you want to delete this export schedule?')).toBeInTheDocument()
    
    const confirmButton = screen.getByText('Delete')
    await user.click(confirmButton)
    
    expect(mockScheduleProps.onScheduleDelete).toHaveBeenCalledWith('schedule-1')
  })

  it('shows schedule execution history', async () => {
    const user = userEvent.setup()
    
    // Mock execution history
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        executions: [
          {
            id: 'exec-1',
            scheduledAt: '2024-01-07T09:00:00Z',
            completedAt: '2024-01-07T09:02:00Z',
            status: 'success',
            fileSize: 1024000
          },
          {
            id: 'exec-2',
            scheduledAt: '2024-01-06T09:00:00Z',
            completedAt: '2024-01-06T09:02:30Z',
            status: 'success',
            fileSize: 987000
          }
        ]
      })
    })
    
    renderWithProviders(<ScheduledExports {...mockScheduleProps} />)
    
    const historyButton = screen.getByTestId('history-schedule-1')
    await user.click(historyButton)
    
    await waitFor(() => {
      expect(screen.getByText('Export History')).toBeInTheDocument()
      expect(screen.getByText('Jan 7, 2024 09:00')).toBeInTheDocument()
      expect(screen.getByText('Success')).toBeInTheDocument()
    })
  })

  it('supports pausing/resuming schedules', async () => {
    const user = userEvent.setup()
    renderWithProviders(<ScheduledExports {...mockScheduleProps} />)
    
    const pauseButton = screen.getByTestId('pause-schedule-schedule-1')
    await user.click(pauseButton)
    
    expect(mockScheduleProps.onScheduleUpdate).toHaveBeenCalledWith(
      'schedule-1',
      expect.objectContaining({ status: 'paused' })
    )
  })

  it('validates schedule configuration', async () => {
    const user = userEvent.setup()
    renderWithProviders(<ScheduledExports {...mockScheduleProps} />)
    
    const createButton = screen.getByText('New Schedule')
    await user.click(createButton)
    
    // Try to save without required fields
    const saveButton = screen.getByText('Create Schedule')
    await user.click(saveButton)
    
    expect(screen.getByText('Schedule name is required')).toBeInTheDocument()
    expect(screen.getByText('Export format is required')).toBeInTheDocument()
  })

  it('shows next run times accurately', () => {
    renderWithProviders(<ScheduledExports {...mockScheduleProps} />)
    
    expect(screen.getByText(/Next run:/)).toBeInTheDocument()
    expect(screen.getByText(/Jan 8, 2024/)).toBeInTheDocument()
  })
})

describe('Export Error Handling', () => {
  it('handles network errors during export', async () => {
    const user = userEvent.setup()
    
    mockFetch.mockRejectedValueOnce(new Error('Network error'))
    
    renderWithProviders(
      <ExportManager dashboard={mockDashboard} open={true} onExportError={jest.fn()} />
    )
    
    const pdfOption = screen.getByLabelText('PDF')
    await user.click(pdfOption)
    
    const exportButton = screen.getByText('Start Export')
    await user.click(exportButton)
    
    await waitFor(() => {
      expect(screen.getByText('Network error occurred')).toBeInTheDocument()
      expect(screen.getByText('Try Again')).toBeInTheDocument()
    })
  })

  it('handles export timeout', async () => {
    const user = userEvent.setup()
    
    // Mock timeout scenario
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true, exportId: 'export-123' })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ status: 'processing' })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ status: 'timeout', error: 'Export timed out' })
      })
    
    renderWithProviders(
      <ExportManager dashboard={mockDashboard} open={true} onExportError={jest.fn()} />
    )
    
    const pdfOption = screen.getByLabelText('PDF')
    await user.click(pdfOption)
    
    const exportButton = screen.getByText('Start Export')
    await user.click(exportButton)
    
    await waitFor(() => {
      expect(screen.getByText('Export timed out')).toBeInTheDocument()
    })
  })

  it('handles insufficient permissions', async () => {
    const user = userEvent.setup()
    
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 403,
      json: async () => ({ error: 'Insufficient permissions' })
    })
    
    renderWithProviders(
      <ExportManager dashboard={mockDashboard} open={true} onExportError={jest.fn()} />
    )
    
    const pdfOption = screen.getByLabelText('PDF')
    await user.click(pdfOption)
    
    const exportButton = screen.getByText('Start Export')
    await user.click(exportButton)
    
    await waitFor(() => {
      expect(screen.getByText('Insufficient permissions')).toBeInTheDocument()
    })
  })
})

describe('Export Accessibility', () => {
  it('supports keyboard navigation', async () => {
    const user = userEvent.setup()
    renderWithProviders(<ExportManager dashboard={mockDashboard} open={true} />)
    
    // Tab through format options
    await user.tab()
    expect(document.activeElement).toHaveAttribute('type', 'radio')
    
    // Select format with keyboard
    await user.keyboard('{Enter}')
    
    // Tab to export button
    await user.tab()
    await user.tab()
    expect(document.activeElement).toHaveTextContent('Start Export')
  })

  it('provides proper ARIA labels', () => {
    renderWithProviders(<ExportManager dashboard={mockDashboard} open={true} />)
    
    expect(screen.getByRole('dialog')).toHaveAttribute('aria-labelledby', 'export-dialog-title')
    expect(screen.getByRole('radiogroup')).toHaveAttribute('aria-label', 'Export format selection')
  })

  it('announces export progress to screen readers', async () => {
    const user = userEvent.setup()
    
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true, exportId: 'export-123' })
    })
    
    renderWithProviders(<ExportManager dashboard={mockDashboard} open={true} />)
    
    const pdfOption = screen.getByLabelText('PDF')
    await user.click(pdfOption)
    
    const exportButton = screen.getByText('Start Export')
    await user.click(exportButton)
    
    await waitFor(() => {
      expect(screen.getByRole('status')).toHaveTextContent('Export in progress')
    })
  })
})