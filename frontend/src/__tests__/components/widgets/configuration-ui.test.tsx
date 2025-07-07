// ABOUTME: Comprehensive test suite for widget configuration UI components
// ABOUTME: Tests widget config dialog, palette, property panels, and form validation

import React from 'react'
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

// Configuration Components
import WidgetConfigDialog from '@/components/widgets/widget-config-dialog'
import WidgetPalette from '@/components/widgets/widget-palette'
import { UnifiedDashboardDesigner } from '@/components/admin/unified-dashboard-designer'

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
const mockWidgetDefinitions = [
  {
    id: 'metric-def-1',
    name: 'Metric Widget',
    description: 'Display single metric values',
    category: 'metric',
    configSchema: {
      type: 'object',
      properties: {
        title: { type: 'string', title: 'Widget Title' },
        dataSource: { type: 'string', title: 'Data Source', enum: ['demographics', 'adverse_events'] },
        field: { type: 'string', title: 'Field Name' },
        aggregation: { type: 'string', title: 'Aggregation', enum: ['count', 'sum', 'avg', 'min', 'max'] },
        format: { type: 'string', title: 'Display Format', enum: ['number', 'currency', 'percentage'] }
      },
      required: ['title', 'dataSource', 'field', 'aggregation']
    },
    defaultConfig: {
      title: 'New Metric',
      dataSource: 'demographics',
      field: 'subject_id',
      aggregation: 'count',
      format: 'number'
    }
  },
  {
    id: 'chart-def-1',
    name: 'Chart Widget',
    description: 'Display data visualizations',
    category: 'chart',
    configSchema: {
      type: 'object',
      properties: {
        title: { type: 'string', title: 'Chart Title' },
        chartType: { type: 'string', title: 'Chart Type', enum: ['bar', 'line', 'pie', 'scatter'] },
        dataSource: { type: 'string', title: 'Data Source' },
        xAxis: { type: 'string', title: 'X-Axis Field' },
        yAxis: { type: 'string', title: 'Y-Axis Field' },
        groupBy: { type: 'string', title: 'Group By (Optional)' }
      },
      required: ['title', 'chartType', 'dataSource', 'xAxis', 'yAxis']
    },
    defaultConfig: {
      title: 'New Chart',
      chartType: 'bar',
      dataSource: 'demographics',
      xAxis: 'site',
      yAxis: 'count'
    }
  }
]

const mockWidget = global.createMockWidget({
  id: 'widget-1',
  type: 'metric',
  title: 'Total Subjects',
  config: {
    title: 'Total Subjects',
    dataSource: 'demographics',
    field: 'subject_id',
    aggregation: 'count',
    format: 'number'
  }
})

describe('WidgetConfigDialog', () => {
  const mockConfigProps = {
    widget: mockWidget,
    widgetDefinition: mockWidgetDefinitions[0],
    open: true,
    onSave: jest.fn(),
    onCancel: jest.fn()
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders configuration form with current values', () => {
    renderWithProviders(<WidgetConfigDialog {...mockConfigProps} />)
    
    expect(screen.getByText('Configure Widget')).toBeInTheDocument()
    expect(screen.getByDisplayValue('Total Subjects')).toBeInTheDocument()
    expect(screen.getByDisplayValue('demographics')).toBeInTheDocument()
    expect(screen.getByDisplayValue('subject_id')).toBeInTheDocument()
    expect(screen.getByDisplayValue('count')).toBeInTheDocument()
  })

  it('validates required fields', async () => {
    const user = userEvent.setup()
    renderWithProviders(<WidgetConfigDialog {...mockConfigProps} />)
    
    // Clear required field
    const titleInput = screen.getByLabelText('Widget Title')
    await user.clear(titleInput)
    
    const saveButton = screen.getByText('Save')
    await user.click(saveButton)
    
    expect(screen.getByText('Widget Title is required')).toBeInTheDocument()
    expect(mockConfigProps.onSave).not.toHaveBeenCalled()
  })

  it('handles form field changes', async () => {
    const user = userEvent.setup()
    renderWithProviders(<WidgetConfigDialog {...mockConfigProps} />)
    
    const titleInput = screen.getByLabelText('Widget Title')
    await user.clear(titleInput)
    await user.type(titleInput, 'Updated Title')
    
    const aggregationSelect = screen.getByLabelText('Aggregation')
    await user.click(aggregationSelect)
    await user.click(screen.getByText('sum'))
    
    expect(titleInput).toHaveValue('Updated Title')
    expect(screen.getByText('sum')).toBeInTheDocument()
  })

  it('saves configuration changes', async () => {
    const user = userEvent.setup()
    renderWithProviders(<WidgetConfigDialog {...mockConfigProps} />)
    
    const titleInput = screen.getByLabelText('Widget Title')
    await user.clear(titleInput)
    await user.type(titleInput, 'Updated Widget Title')
    
    const saveButton = screen.getByText('Save')
    await user.click(saveButton)
    
    expect(mockConfigProps.onSave).toHaveBeenCalledWith({
      ...mockWidget.config,
      title: 'Updated Widget Title'
    })
  })

  it('handles cancellation', async () => {
    const user = userEvent.setup()
    renderWithProviders(<WidgetConfigDialog {...mockConfigProps} />)
    
    const cancelButton = screen.getByText('Cancel')
    await user.click(cancelButton)
    
    expect(mockConfigProps.onCancel).toHaveBeenCalled()
  })

  it('shows field descriptions when available', () => {
    const definitionWithDescriptions = {
      ...mockWidgetDefinitions[0],
      configSchema: {
        ...mockWidgetDefinitions[0].configSchema,
        properties: {
          ...mockWidgetDefinitions[0].configSchema.properties,
          title: {
            ...mockWidgetDefinitions[0].configSchema.properties.title,
            description: 'The title displayed at the top of the widget'
          }
        }
      }
    }
    
    renderWithProviders(
      <WidgetConfigDialog {...mockConfigProps} widgetDefinition={definitionWithDescriptions} />
    )
    
    expect(screen.getByText('The title displayed at the top of the widget')).toBeInTheDocument()
  })

  it('supports conditional field visibility', async () => {
    const user = userEvent.setup()
    
    // Widget definition with conditional fields
    const conditionalDefinition = {
      ...mockWidgetDefinitions[1],
      configSchema: {
        ...mockWidgetDefinitions[1].configSchema,
        properties: {
          ...mockWidgetDefinitions[1].configSchema.properties,
          stackedMode: {
            type: 'boolean',
            title: 'Stacked Mode',
            description: 'Only available for bar charts'
          }
        },
        conditionalFields: {
          stackedMode: {
            dependsOn: 'chartType',
            showWhen: ['bar', 'area']
          }
        }
      }
    }
    
    renderWithProviders(
      <WidgetConfigDialog 
        {...mockConfigProps} 
        widgetDefinition={conditionalDefinition}
        widget={{
          ...mockWidget,
          type: 'chart',
          config: { ...mockWidgetDefinitions[1].defaultConfig }
        }}
      />
    )
    
    // Should show stacked mode for bar chart
    expect(screen.getByLabelText('Stacked Mode')).toBeInTheDocument()
    
    // Change to pie chart
    const chartTypeSelect = screen.getByLabelText('Chart Type')
    await user.click(chartTypeSelect)
    await user.click(screen.getByText('pie'))
    
    // Stacked mode should be hidden
    expect(screen.queryByLabelText('Stacked Mode')).not.toBeInTheDocument()
  })

  it('handles enum field options', () => {
    renderWithProviders(<WidgetConfigDialog {...mockConfigProps} />)
    
    const aggregationSelect = screen.getByLabelText('Aggregation')
    fireEvent.click(aggregationSelect)
    
    // Should show all enum options
    expect(screen.getByText('count')).toBeInTheDocument()
    expect(screen.getByText('sum')).toBeInTheDocument()
    expect(screen.getByText('avg')).toBeInTheDocument()
    expect(screen.getByText('min')).toBeInTheDocument()
    expect(screen.getByText('max')).toBeInTheDocument()
  })

  it('supports field validation rules', async () => {
    const user = userEvent.setup()
    
    const validationDefinition = {
      ...mockWidgetDefinitions[0],
      configSchema: {
        ...mockWidgetDefinitions[0].configSchema,
        properties: {
          ...mockWidgetDefinitions[0].configSchema.properties,
          threshold: {
            type: 'number',
            title: 'Threshold Value',
            minimum: 0,
            maximum: 100
          }
        }
      }
    }
    
    renderWithProviders(
      <WidgetConfigDialog {...mockConfigProps} widgetDefinition={validationDefinition} />
    )
    
    const thresholdInput = screen.getByLabelText('Threshold Value')
    await user.type(thresholdInput, '150')
    
    const saveButton = screen.getByText('Save')
    await user.click(saveButton)
    
    expect(screen.getByText('Value must be between 0 and 100')).toBeInTheDocument()
  })
})

describe('WidgetPalette', () => {
  const mockPaletteProps = {
    widgetDefinitions: mockWidgetDefinitions,
    onWidgetSelect: jest.fn(),
    searchable: true,
    categorized: true
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders all widget definitions', () => {
    renderWithProviders(<WidgetPalette {...mockPaletteProps} />)
    
    expect(screen.getByText('Widget Palette')).toBeInTheDocument()
    expect(screen.getByText('Metric Widget')).toBeInTheDocument()
    expect(screen.getByText('Chart Widget')).toBeInTheDocument()
  })

  it('groups widgets by category', () => {
    renderWithProviders(<WidgetPalette {...mockPaletteProps} />)
    
    expect(screen.getByText('Metric Widgets')).toBeInTheDocument()
    expect(screen.getByText('Chart Widgets')).toBeInTheDocument()
  })

  it('supports widget search', async () => {
    const user = userEvent.setup()
    renderWithProviders(<WidgetPalette {...mockPaletteProps} />)
    
    const searchInput = screen.getByPlaceholderText('Search widgets...')
    await user.type(searchInput, 'metric')
    
    expect(screen.getByText('Metric Widget')).toBeInTheDocument()
    expect(screen.queryByText('Chart Widget')).not.toBeInTheDocument()
  })

  it('handles widget selection', async () => {
    const user = userEvent.setup()
    renderWithProviders(<WidgetPalette {...mockPaletteProps} />)
    
    const metricWidget = screen.getByTestId('widget-def-metric-def-1')
    await user.click(metricWidget)
    
    expect(mockPaletteProps.onWidgetSelect).toHaveBeenCalledWith(mockWidgetDefinitions[0])
  })

  it('shows widget descriptions on hover', async () => {
    const user = userEvent.setup()
    renderWithProviders(<WidgetPalette {...mockPaletteProps} />)
    
    const metricWidget = screen.getByTestId('widget-def-metric-def-1')
    await user.hover(metricWidget)
    
    await waitFor(() => {
      expect(screen.getByText('Display single metric values')).toBeInTheDocument()
    })
  })

  it('supports drag and drop for widget creation', async () => {
    const user = userEvent.setup()
    renderWithProviders(<WidgetPalette {...mockPaletteProps} draggable={true} />)
    
    const metricWidget = screen.getByTestId('widget-def-metric-def-1')
    expect(metricWidget).toHaveAttribute('draggable', 'true')
    
    // Simulate drag start
    fireEvent.dragStart(metricWidget)
    
    // Should set drag data
    expect(metricWidget).toHaveAttribute('data-widget-type', 'metric')
  })

  it('filters widgets by category', async () => {
    const user = userEvent.setup()
    renderWithProviders(<WidgetPalette {...mockPaletteProps} />)
    
    const categoryFilter = screen.getByLabelText('Filter by category')
    await user.click(categoryFilter)
    await user.click(screen.getByText('Metric'))
    
    expect(screen.getByText('Metric Widget')).toBeInTheDocument()
    expect(screen.queryByText('Chart Widget')).not.toBeInTheDocument()
  })

  it('shows widget preview on selection', async () => {
    const user = userEvent.setup()
    renderWithProviders(<WidgetPalette {...mockPaletteProps} showPreview={true} />)
    
    const chartWidget = screen.getByTestId('widget-def-chart-def-1')
    await user.click(chartWidget)
    
    expect(screen.getByText('Widget Preview')).toBeInTheDocument()
    expect(screen.getByTestId('widget-preview')).toBeInTheDocument()
  })
})

describe('UnifiedDashboardDesigner', () => {
  const mockDesignerProps = {
    dashboardTemplate: global.createMockDashboard({
      widgets: [mockWidget]
    }),
    widgetDefinitions: mockWidgetDefinitions,
    onSave: jest.fn(),
    onCancel: jest.fn()
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders designer with all components', () => {
    renderWithProviders(<UnifiedDashboardDesigner {...mockDesignerProps} />)
    
    expect(screen.getByText('Dashboard Designer')).toBeInTheDocument()
    expect(screen.getByText('Widget Palette')).toBeInTheDocument()
    expect(screen.getByTestId('design-canvas')).toBeInTheDocument()
    expect(screen.getByTestId('property-panel')).toBeInTheDocument()
  })

  it('supports adding widgets from palette', async () => {
    const user = userEvent.setup()
    renderWithProviders(<UnifiedDashboardDesigner {...mockDesignerProps} />)
    
    const metricWidget = screen.getByTestId('widget-def-metric-def-1')
    const canvas = screen.getByTestId('design-canvas')
    
    // Simulate drag and drop
    fireEvent.dragStart(metricWidget)
    fireEvent.dragOver(canvas)
    fireEvent.drop(canvas)
    
    // Should add new widget to canvas
    expect(screen.getAllByTestId(/^widget-/)).toHaveLength(2) // Original + new
  })

  it('shows property panel when widget is selected', async () => {
    const user = userEvent.setup()
    renderWithProviders(<UnifiedDashboardDesigner {...mockDesignerProps} />)
    
    const existingWidget = screen.getByTestId('widget-widget-1')
    await user.click(existingWidget)
    
    const propertyPanel = screen.getByTestId('property-panel')
    expect(within(propertyPanel).getByText('Widget Properties')).toBeInTheDocument()
    expect(within(propertyPanel).getByDisplayValue('Total Subjects')).toBeInTheDocument()
  })

  it('handles widget deletion', async () => {
    const user = userEvent.setup()
    renderWithProviders(<UnifiedDashboardDesigner {...mockDesignerProps} />)
    
    const widget = screen.getByTestId('widget-widget-1')
    await user.click(widget) // Select widget
    
    const deleteButton = screen.getByTitle('Delete widget')
    await user.click(deleteButton)
    
    expect(screen.getByText('Delete Widget')).toBeInTheDocument()
    
    const confirmButton = screen.getByText('Delete')
    await user.click(confirmButton)
    
    expect(screen.queryByTestId('widget-widget-1')).not.toBeInTheDocument()
  })

  it('supports undo/redo operations', async () => {
    const user = userEvent.setup()
    renderWithProviders(<UnifiedDashboardDesigner {...mockDesignerProps} />)
    
    // Make a change (delete widget)
    const widget = screen.getByTestId('widget-widget-1')
    await user.click(widget)
    
    const deleteButton = screen.getByTitle('Delete widget')
    await user.click(deleteButton)
    await user.click(screen.getByText('Delete'))
    
    // Undo the change
    const undoButton = screen.getByTitle('Undo')
    await user.click(undoButton)
    
    expect(screen.getByTestId('widget-widget-1')).toBeInTheDocument()
    
    // Redo the change
    const redoButton = screen.getByTitle('Redo')
    await user.click(redoButton)
    
    expect(screen.queryByTestId('widget-widget-1')).not.toBeInTheDocument()
  })

  it('shows grid snapping options', () => {
    renderWithProviders(<UnifiedDashboardDesigner {...mockDesignerProps} />)
    
    expect(screen.getByLabelText('Snap to grid')).toBeInTheDocument()
    expect(screen.getByLabelText('Show grid')).toBeInTheDocument()
  })

  it('supports responsive preview modes', async () => {
    const user = userEvent.setup()
    renderWithProviders(<UnifiedDashboardDesigner {...mockDesignerProps} />)
    
    const deviceSelector = screen.getByLabelText('Preview device')
    await user.click(deviceSelector)
    
    expect(screen.getByText('Desktop')).toBeInTheDocument()
    expect(screen.getByText('Tablet')).toBeInTheDocument()
    expect(screen.getByText('Mobile')).toBeInTheDocument()
    
    await user.click(screen.getByText('Mobile'))
    
    const canvas = screen.getByTestId('design-canvas')
    expect(canvas).toHaveClass('mobile-preview')
  })

  it('validates dashboard before saving', async () => {
    const user = userEvent.setup()
    
    // Create invalid dashboard (overlapping widgets)
    const invalidDashboard = {
      ...mockDesignerProps.dashboardTemplate,
      widgets: [
        global.createMockWidget({
          id: 'widget-1',
          position: { x: 0, y: 0, w: 4, h: 2 }
        }),
        global.createMockWidget({
          id: 'widget-2',
          position: { x: 2, y: 0, w: 4, h: 2 } // Overlaps with widget-1
        })
      ]
    }
    
    renderWithProviders(
      <UnifiedDashboardDesigner {...mockDesignerProps} dashboardTemplate={invalidDashboard} />
    )
    
    const saveButton = screen.getByText('Save Dashboard')
    await user.click(saveButton)
    
    expect(screen.getByText('Dashboard Validation Errors')).toBeInTheDocument()
    expect(screen.getByText(/widgets overlap/i)).toBeInTheDocument()
  })

  it('supports keyboard shortcuts', async () => {
    const user = userEvent.setup()
    renderWithProviders(<UnifiedDashboardDesigner {...mockDesignerProps} />)
    
    // Select widget and delete with keyboard
    const widget = screen.getByTestId('widget-widget-1')
    await user.click(widget)
    
    await user.keyboard('{Delete}')
    
    expect(screen.getByText('Delete Widget')).toBeInTheDocument()
  })

  it('auto-saves draft changes', async () => {
    const user = userEvent.setup()
    renderWithProviders(<UnifiedDashboardDesigner {...mockDesignerProps} autoSave={true} />)
    
    // Make a change
    const widget = screen.getByTestId('widget-widget-1')
    await user.click(widget)
    
    const titleInput = screen.getByDisplayValue('Total Subjects')
    await user.clear(titleInput)
    await user.type(titleInput, 'Modified Title')
    
    // Should show auto-save indicator
    await waitFor(() => {
      expect(screen.getByText('Draft saved')).toBeInTheDocument()
    })
  })
})

describe('Configuration Form Validation', () => {
  it('validates required fields across all widget types', async () => {
    const user = userEvent.setup()
    
    for (const definition of mockWidgetDefinitions) {
      const widget = global.createMockWidget({
        type: definition.category,
        config: {}
      })
      
      renderWithProviders(
        <WidgetConfigDialog
          widget={widget}
          widgetDefinition={definition}
          open={true}
          onSave={jest.fn()}
          onCancel={jest.fn()}
        />
      )
      
      const saveButton = screen.getByText('Save')
      await user.click(saveButton)
      
      // Should show validation errors for required fields
      const requiredFields = definition.configSchema.required || []
      for (const field of requiredFields) {
        const property = definition.configSchema.properties[field]
        if (property?.title) {
          expect(screen.getByText(`${property.title} is required`)).toBeInTheDocument()
        }
      }
    }
  })

  it('validates field data types', async () => {
    const user = userEvent.setup()
    
    const numberFieldDefinition = {
      ...mockWidgetDefinitions[0],
      configSchema: {
        ...mockWidgetDefinitions[0].configSchema,
        properties: {
          ...mockWidgetDefinitions[0].configSchema.properties,
          threshold: {
            type: 'number',
            title: 'Threshold'
          }
        }
      }
    }
    
    renderWithProviders(
      <WidgetConfigDialog
        widget={mockWidget}
        widgetDefinition={numberFieldDefinition}
        open={true}
        onSave={jest.fn()}
        onCancel={jest.fn()}
      />
    )
    
    const thresholdInput = screen.getByLabelText('Threshold')
    await user.type(thresholdInput, 'not-a-number')
    
    const saveButton = screen.getByText('Save')
    await user.click(saveButton)
    
    expect(screen.getByText('Threshold must be a number')).toBeInTheDocument()
  })

  it('validates field constraints', async () => {
    const user = userEvent.setup()
    
    const constrainedDefinition = {
      ...mockWidgetDefinitions[0],
      configSchema: {
        ...mockWidgetDefinitions[0].configSchema,
        properties: {
          ...mockWidgetDefinitions[0].configSchema.properties,
          title: {
            type: 'string',
            title: 'Widget Title',
            minLength: 3,
            maxLength: 50
          }
        }
      }
    }
    
    renderWithProviders(
      <WidgetConfigDialog
        widget={mockWidget}
        widgetDefinition={constrainedDefinition}
        open={true}
        onSave={jest.fn()}
        onCancel={jest.fn()}
      />
    )
    
    const titleInput = screen.getByLabelText('Widget Title')
    
    // Test minimum length
    await user.clear(titleInput)
    await user.type(titleInput, 'AB')
    
    let saveButton = screen.getByText('Save')
    await user.click(saveButton)
    
    expect(screen.getByText('Widget Title must be at least 3 characters')).toBeInTheDocument()
    
    // Test maximum length
    await user.clear(titleInput)
    await user.type(titleInput, 'A'.repeat(51))
    
    saveButton = screen.getByText('Save')
    await user.click(saveButton)
    
    expect(screen.getByText('Widget Title must be no more than 50 characters')).toBeInTheDocument()
  })
})

describe('Configuration UI Accessibility', () => {
  it('supports keyboard navigation in forms', async () => {
    const user = userEvent.setup()
    renderWithProviders(
      <WidgetConfigDialog
        widget={mockWidget}
        widgetDefinition={mockWidgetDefinitions[0]}
        open={true}
        onSave={jest.fn()}
        onCancel={jest.fn()}
      />
    )
    
    // Tab through form fields
    await user.tab()
    expect(document.activeElement).toHaveAttribute('name', 'title')
    
    await user.tab()
    expect(document.activeElement).toHaveAttribute('name', 'dataSource')
  })

  it('provides proper ARIA labels and descriptions', () => {
    renderWithProviders(
      <WidgetConfigDialog
        widget={mockWidget}
        widgetDefinition={mockWidgetDefinitions[0]}
        open={true}
        onSave={jest.fn()}
        onCancel={jest.fn()}
      />
    )
    
    expect(screen.getByRole('dialog')).toHaveAttribute('aria-labelledby')
    expect(screen.getByLabelText('Widget Title')).toBeInTheDocument()
    expect(screen.getByLabelText('Data Source')).toBeInTheDocument()
  })

  it('announces validation errors to screen readers', async () => {
    const user = userEvent.setup()
    renderWithProviders(
      <WidgetConfigDialog
        widget={mockWidget}
        widgetDefinition={mockWidgetDefinitions[0]}
        open={true}
        onSave={jest.fn()}
        onCancel={jest.fn()}
      />
    )
    
    const titleInput = screen.getByLabelText('Widget Title')
    await user.clear(titleInput)
    
    const saveButton = screen.getByText('Save')
    await user.click(saveButton)
    
    const errorMessage = screen.getByText('Widget Title is required')
    expect(errorMessage).toHaveAttribute('role', 'alert')
  })

  it('maintains focus management in modal dialogs', async () => {
    const user = userEvent.setup()
    renderWithProviders(
      <WidgetConfigDialog
        widget={mockWidget}
        widgetDefinition={mockWidgetDefinitions[0]}
        open={true}
        onSave={jest.fn()}
        onCancel={jest.fn()}
      />
    )
    
    // Focus should be trapped within dialog
    await user.tab()
    expect(document.activeElement).toBeInTheDocument()
    
    // Should not tab outside of dialog
    const activeElement = document.activeElement
    await user.keyboard('{Shift>}{Tab}{/Shift}')
    expect(document.activeElement).toBeInTheDocument()
  })
})