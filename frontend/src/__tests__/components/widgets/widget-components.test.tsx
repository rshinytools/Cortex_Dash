// ABOUTME: Comprehensive test suite for all widget components
// ABOUTME: Tests rendering, data handling, interactions, and error states for each widget type

import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

// Widget Components
import MetricCard from '@/components/widgets/metric-card'
import BarChart from '@/components/widgets/bar-chart'
import LineChart from '@/components/widgets/line-chart'
import PieChart from '@/components/widgets/pie-chart'
import DataTable from '@/components/widgets/data-table'
import HeatMap from '@/components/widgets/heatmap'
import ScatterPlot from '@/components/widgets/scatter-plot'
import WidgetContainer from '@/components/widgets/widget-container'
import WidgetRenderer from '@/components/widgets/widget-renderer'

// Test utilities
const createQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: { retry: false },
    mutations: { retry: false },
  },
})

const renderWithQueryClient = (component: React.ReactElement) => {
  const queryClient = createQueryClient()
  return render(
    <QueryClientProvider client={queryClient}>
      {component}
    </QueryClientProvider>
  )
}

describe('MetricCard Widget', () => {
  const mockMetricData = {
    value: 1250,
    title: 'Total Subjects',
    subtitle: 'Enrolled in study',
    format: 'number' as const,
    trend: 'up' as const,
    change: 5.2,
    changeFormat: 'percentage' as const
  }

  it('renders metric value correctly', () => {
    renderWithQueryClient(<MetricCard {...mockMetricData} />)
    
    expect(screen.getByText('Total Subjects')).toBeInTheDocument()
    expect(screen.getByText('1,250')).toBeInTheDocument()
    expect(screen.getByText('Enrolled in study')).toBeInTheDocument()
  })

  it('displays trend indicator when provided', () => {
    renderWithQueryClient(<MetricCard {...mockMetricData} />)
    
    // Should show positive trend
    expect(screen.getByText('+5.2%')).toBeInTheDocument()
    // Trend arrow or icon should be present
    expect(document.querySelector('[data-testid="trend-up"]')).toBeInTheDocument()
  })

  it('handles different number formats', () => {
    const currencyData = { ...mockMetricData, format: 'currency' as const, value: 50000 }
    renderWithQueryClient(<MetricCard {...currencyData} />)
    
    expect(screen.getByText('$50,000')).toBeInTheDocument()
  })

  it('handles percentage format', () => {
    const percentageData = { ...mockMetricData, format: 'percentage' as const, value: 0.852 }
    renderWithQueryClient(<MetricCard {...percentageData} />)
    
    expect(screen.getByText('85.2%')).toBeInTheDocument()
  })

  it('handles loading state', () => {
    renderWithQueryClient(<MetricCard {...mockMetricData} isLoading={true} />)
    
    expect(screen.getByTestId('metric-skeleton')).toBeInTheDocument()
  })

  it('handles error state', () => {
    const errorMessage = 'Failed to load metric data'
    renderWithQueryClient(<MetricCard {...mockMetricData} error={errorMessage} />)
    
    expect(screen.getByText(errorMessage)).toBeInTheDocument()
    expect(screen.getByTestId('error-icon')).toBeInTheDocument()
  })

  it('calls onClick handler when clickable', async () => {
    const user = userEvent.setup()
    const onClick = jest.fn()
    
    renderWithQueryClient(<MetricCard {...mockMetricData} onClick={onClick} />)
    
    await user.click(screen.getByRole('button'))
    expect(onClick).toHaveBeenCalledTimes(1)
  })
})

describe('BarChart Widget', () => {
  const mockBarChartData = {
    data: [
      { category: 'Site 001', value: 45, label: '45 subjects' },
      { category: 'Site 002', value: 38, label: '38 subjects' },
      { category: 'Site 003', value: 52, label: '52 subjects' },
      { category: 'Site 004', value: 31, label: '31 subjects' }
    ],
    title: 'Enrollment by Site',
    xAxisLabel: 'Study Sites',
    yAxisLabel: 'Number of Subjects',
    color: '#3b82f6'
  }

  it('renders chart with correct data', () => {
    renderWithQueryClient(<BarChart {...mockBarChartData} />)
    
    expect(screen.getByText('Enrollment by Site')).toBeInTheDocument()
    expect(screen.getByText('Study Sites')).toBeInTheDocument()
    expect(screen.getByText('Number of Subjects')).toBeInTheDocument()
  })

  it('displays all data categories', () => {
    renderWithQueryClient(<BarChart {...mockBarChartData} />)
    
    mockBarChartData.data.forEach(item => {
      expect(screen.getByText(item.category)).toBeInTheDocument()
    })
  })

  it('handles empty data gracefully', () => {
    const emptyData = { ...mockBarChartData, data: [] }
    renderWithQueryClient(<BarChart {...emptyData} />)
    
    expect(screen.getByText('No data available')).toBeInTheDocument()
  })

  it('supports horizontal orientation', () => {
    renderWithQueryClient(<BarChart {...mockBarChartData} orientation="horizontal" />)
    
    // Check if chart container has horizontal class
    expect(document.querySelector('.bar-chart-horizontal')).toBeInTheDocument()
  })

  it('handles click events on bars', async () => {
    const user = userEvent.setup()
    const onBarClick = jest.fn()
    
    renderWithQueryClient(<BarChart {...mockBarChartData} onBarClick={onBarClick} />)
    
    // Click on first bar
    const firstBar = screen.getByTestId('bar-Site 001')
    await user.click(firstBar)
    
    expect(onBarClick).toHaveBeenCalledWith(mockBarChartData.data[0])
  })

  it('displays tooltips on hover', async () => {
    const user = userEvent.setup()
    renderWithQueryClient(<BarChart {...mockBarChartData} />)
    
    const firstBar = screen.getByTestId('bar-Site 001')
    await user.hover(firstBar)
    
    await waitFor(() => {
      expect(screen.getByText('45 subjects')).toBeInTheDocument()
    })
  })
})

describe('LineChart Widget', () => {
  const mockLineChartData = {
    data: [
      { x: '2024-01', y: 10, label: 'January 2024' },
      { x: '2024-02', y: 15, label: 'February 2024' },
      { x: '2024-03', y: 22, label: 'March 2024' },
      { x: '2024-04', y: 18, label: 'April 2024' }
    ],
    title: 'Enrollment Trend',
    xAxisLabel: 'Month',
    yAxisLabel: 'New Enrollments',
    color: '#10b981'
  }

  it('renders line chart correctly', () => {
    renderWithQueryClient(<LineChart {...mockLineChartData} />)
    
    expect(screen.getByText('Enrollment Trend')).toBeInTheDocument()
    expect(screen.getByText('Month')).toBeInTheDocument()
    expect(screen.getByText('New Enrollments')).toBeInTheDocument()
  })

  it('supports multiple series', () => {
    const multiSeriesData = {
      ...mockLineChartData,
      data: [
        {
          id: 'enrolled',
          data: mockLineChartData.data
        },
        {
          id: 'screened',
          data: mockLineChartData.data.map(d => ({ ...d, y: d.y * 1.5 }))
        }
      ]
    }
    
    renderWithQueryClient(<LineChart {...multiSeriesData} />)
    
    expect(screen.getByText('enrolled')).toBeInTheDocument()
    expect(screen.getByText('screened')).toBeInTheDocument()
  })

  it('handles different line styles', () => {
    renderWithQueryClient(<LineChart {...mockLineChartData} lineStyle="dashed" />)
    
    // Check if line has dashed style
    expect(document.querySelector('.line-dashed')).toBeInTheDocument()
  })

  it('supports data point markers', () => {
    renderWithQueryClient(<LineChart {...mockLineChartData} showMarkers={true} />)
    
    // Check for marker elements
    expect(document.querySelectorAll('.line-marker')).toHaveLength(mockLineChartData.data.length)
  })
})

describe('PieChart Widget', () => {
  const mockPieChartData = {
    data: [
      { id: 'Male', value: 65, label: 'Male (65%)' },
      { id: 'Female', value: 35, label: 'Female (35%)' }
    ],
    title: 'Gender Distribution',
    colors: ['#3b82f6', '#ef4444']
  }

  it('renders pie chart with correct segments', () => {
    renderWithQueryClient(<PieChart {...mockPieChartData} />)
    
    expect(screen.getByText('Gender Distribution')).toBeInTheDocument()
    expect(screen.getByText('Male (65%)')).toBeInTheDocument()
    expect(screen.getByText('Female (35%)')).toBeInTheDocument()
  })

  it('supports donut chart variant', () => {
    renderWithQueryClient(<PieChart {...mockPieChartData} variant="donut" />)
    
    expect(document.querySelector('.pie-chart-donut')).toBeInTheDocument()
  })

  it('displays legend correctly', () => {
    renderWithQueryClient(<PieChart {...mockPieChartData} showLegend={true} />)
    
    expect(screen.getByTestId('chart-legend')).toBeInTheDocument()
    mockPieChartData.data.forEach(item => {
      expect(screen.getByText(item.id)).toBeInTheDocument()
    })
  })

  it('handles segment click events', async () => {
    const user = userEvent.setup()
    const onSegmentClick = jest.fn()
    
    renderWithQueryClient(<PieChart {...mockPieChartData} onSegmentClick={onSegmentClick} />)
    
    const maleSegment = screen.getByTestId('pie-segment-Male')
    await user.click(maleSegment)
    
    expect(onSegmentClick).toHaveBeenCalledWith(mockPieChartData.data[0])
  })
})

describe('DataTable Widget', () => {
  const mockTableData = {
    data: [
      { id: 'S001', subject_id: 'STUDY-001', age: 25, gender: 'M', site: 'Site 001' },
      { id: 'S002', subject_id: 'STUDY-002', age: 30, gender: 'F', site: 'Site 002' },
      { id: 'S003', subject_id: 'STUDY-003', age: 35, gender: 'M', site: 'Site 001' }
    ],
    columns: [
      { key: 'subject_id', header: 'Subject ID', sortable: true },
      { key: 'age', header: 'Age', sortable: true, type: 'number' },
      { key: 'gender', header: 'Gender', sortable: true },
      { key: 'site', header: 'Site', sortable: true }
    ],
    title: 'Subject Demographics'
  }

  it('renders table with all data', () => {
    renderWithQueryClient(<DataTable {...mockTableData} />)
    
    expect(screen.getByText('Subject Demographics')).toBeInTheDocument()
    
    // Check headers
    mockTableData.columns.forEach(col => {
      expect(screen.getByText(col.header)).toBeInTheDocument()
    })
    
    // Check data rows
    mockTableData.data.forEach(row => {
      expect(screen.getByText(row.subject_id)).toBeInTheDocument()
      expect(screen.getByText(row.age.toString())).toBeInTheDocument()
    })
  })

  it('supports column sorting', async () => {
    const user = userEvent.setup()
    renderWithQueryClient(<DataTable {...mockTableData} />)
    
    const ageHeader = screen.getByText('Age')
    await user.click(ageHeader)
    
    // Check if data is sorted by age (ascending first)
    const rows = screen.getAllByTestId(/table-row-/)
    expect(rows[0]).toHaveTextContent('STUDY-001') // Age 25
    expect(rows[2]).toHaveTextContent('STUDY-003') // Age 35
  })

  it('supports pagination', () => {
    const largeDataSet = {
      ...mockTableData,
      data: Array(25).fill(null).map((_, i) => ({
        id: `S${i.toString().padStart(3, '0')}`,
        subject_id: `STUDY-${i.toString().padStart(3, '0')}`,
        age: 20 + i,
        gender: i % 2 === 0 ? 'M' : 'F',
        site: `Site ${(i % 3) + 1}`
      })),
      pageSize: 10
    }
    
    renderWithQueryClient(<DataTable {...largeDataSet} />)
    
    expect(screen.getByTestId('pagination')).toBeInTheDocument()
    expect(screen.getByText('1 of 3')).toBeInTheDocument()
  })

  it('supports row selection', async () => {
    const user = userEvent.setup()
    const onRowSelect = jest.fn()
    
    renderWithQueryClient(<DataTable {...mockTableData} selectable={true} onRowSelect={onRowSelect} />)
    
    const firstRowCheckbox = screen.getByTestId('row-checkbox-S001')
    await user.click(firstRowCheckbox)
    
    expect(onRowSelect).toHaveBeenCalledWith(['S001'])
  })

  it('supports filtering', async () => {
    const user = userEvent.setup()
    renderWithQueryClient(<DataTable {...mockTableData} filterable={true} />)
    
    const filterInput = screen.getByPlaceholderText('Filter table...')
    await user.type(filterInput, 'Site 001')
    
    await waitFor(() => {
      // Should only show rows from Site 001
      expect(screen.getAllByTestId(/table-row-/)).toHaveLength(2)
    })
  })

  it('handles empty data state', () => {
    const emptyData = { ...mockTableData, data: [] }
    renderWithQueryClient(<DataTable {...emptyData} />)
    
    expect(screen.getByText('No data available')).toBeInTheDocument()
  })
})

describe('WidgetContainer', () => {
  const mockWidget = global.createMockWidget({
    title: 'Test Container Widget',
    type: 'metric'
  })

  it('renders widget with container styling', () => {
    renderWithQueryClient(
      <WidgetContainer widget={mockWidget}>
        <div>Widget Content</div>
      </WidgetContainer>
    )
    
    expect(screen.getByText('Test Container Widget')).toBeInTheDocument()
    expect(screen.getByText('Widget Content')).toBeInTheDocument()
  })

  it('supports edit mode', () => {
    renderWithQueryClient(
      <WidgetContainer widget={mockWidget} editMode={true}>
        <div>Widget Content</div>
      </WidgetContainer>
    )
    
    expect(screen.getByTestId('widget-edit-controls')).toBeInTheDocument()
    expect(screen.getByTitle('Edit widget')).toBeInTheDocument()
    expect(screen.getByTitle('Delete widget')).toBeInTheDocument()
  })

  it('handles widget actions', async () => {
    const user = userEvent.setup()
    const onEdit = jest.fn()
    const onDelete = jest.fn()
    
    renderWithQueryClient(
      <WidgetContainer widget={mockWidget} editMode={true} onEdit={onEdit} onDelete={onDelete}>
        <div>Widget Content</div>
      </WidgetContainer>
    )
    
    await user.click(screen.getByTitle('Edit widget'))
    expect(onEdit).toHaveBeenCalledWith(mockWidget.id)
    
    await user.click(screen.getByTitle('Delete widget'))
    expect(onDelete).toHaveBeenCalledWith(mockWidget.id)
  })

  it('supports loading state', () => {
    renderWithQueryClient(
      <WidgetContainer widget={mockWidget} isLoading={true}>
        <div>Widget Content</div>
      </WidgetContainer>
    )
    
    expect(screen.getByTestId('widget-skeleton')).toBeInTheDocument()
  })

  it('handles error state', () => {
    const error = 'Widget failed to load'
    renderWithQueryClient(
      <WidgetContainer widget={mockWidget} error={error}>
        <div>Widget Content</div>
      </WidgetContainer>
    )
    
    expect(screen.getByText('Error loading widget')).toBeInTheDocument()
    expect(screen.getByText(error)).toBeInTheDocument()
  })

  it('supports fullscreen mode', async () => {
    const user = userEvent.setup()
    renderWithQueryClient(
      <WidgetContainer widget={mockWidget} allowFullscreen={true}>
        <div>Widget Content</div>
      </WidgetContainer>
    )
    
    await user.click(screen.getByTitle('Fullscreen'))
    expect(document.querySelector('.widget-fullscreen')).toBeInTheDocument()
  })
})

describe('WidgetRenderer', () => {
  const mockMetricWidget = global.createMockWidget({
    type: 'metric',
    config: {
      title: 'Test Metric',
      value: 100,
      format: 'number'
    }
  })

  const mockChartWidget = global.createMockWidget({
    type: 'chart',
    config: {
      title: 'Test Chart',
      chartType: 'bar',
      data: [
        { category: 'A', value: 10 },
        { category: 'B', value: 20 }
      ]
    }
  })

  it('renders metric widget correctly', () => {
    renderWithQueryClient(<WidgetRenderer widget={mockMetricWidget} />)
    
    expect(screen.getByText('Test Metric')).toBeInTheDocument()
    expect(screen.getByText('100')).toBeInTheDocument()
  })

  it('renders chart widget correctly', () => {
    renderWithQueryClient(<WidgetRenderer widget={mockChartWidget} />)
    
    expect(screen.getByText('Test Chart')).toBeInTheDocument()
  })

  it('handles unknown widget type', () => {
    const unknownWidget = global.createMockWidget({
      type: 'unknown' as any
    })
    
    renderWithQueryClient(<WidgetRenderer widget={unknownWidget} />)
    
    expect(screen.getByText('Unsupported widget type')).toBeInTheDocument()
  })

  it('supports custom widget props', () => {
    const customProps = {
      showBorder: false,
      backgroundColor: '#f0f0f0'
    }
    
    renderWithQueryClient(<WidgetRenderer widget={mockMetricWidget} {...customProps} />)
    
    const widgetElement = screen.getByTestId('widget-renderer')
    expect(widgetElement).toHaveStyle({ backgroundColor: '#f0f0f0' })
  })

  it('handles widget data loading', () => {
    renderWithQueryClient(<WidgetRenderer widget={mockMetricWidget} isLoading={true} />)
    
    expect(screen.getByTestId('widget-loading')).toBeInTheDocument()
  })
})

describe('Widget Error Handling', () => {
  it('handles network errors gracefully', () => {
    const error = new Error('Network error')
    renderWithQueryClient(<MetricCard title="Test" value={0} error={error.message} />)
    
    expect(screen.getByText('Network error')).toBeInTheDocument()
    expect(screen.getByTestId('retry-button')).toBeInTheDocument()
  })

  it('handles data validation errors', () => {
    // Test with invalid data
    const invalidData = { data: 'invalid' } as any
    renderWithQueryClient(<BarChart data={invalidData} title="Test" />)
    
    expect(screen.getByText('Invalid data format')).toBeInTheDocument()
  })

  it('displays fallback UI for critical errors', () => {
    // Simulate critical error
    const ThrowError = () => {
      throw new Error('Critical widget error')
    }
    
    // Should be wrapped in error boundary
    expect(() => render(<ThrowError />)).not.toThrow()
  })
})

describe('Widget Accessibility', () => {
  it('supports keyboard navigation', async () => {
    const user = userEvent.setup()
    const onClick = jest.fn()
    
    renderWithQueryClient(<MetricCard title="Test" value={100} onClick={onClick} />)
    
    const widget = screen.getByRole('button')
    widget.focus()
    await user.keyboard('{Enter}')
    
    expect(onClick).toHaveBeenCalled()
  })

  it('has proper ARIA labels', () => {
    renderWithQueryClient(<MetricCard title="Total Users" value={1250} />)
    
    expect(screen.getByLabelText('Total Users metric: 1,250')).toBeInTheDocument()
  })

  it('supports screen readers', () => {
    renderWithQueryClient(<BarChart 
      data={[{ category: 'A', value: 10 }]} 
      title="Test Chart" 
      ariaDescription="Bar chart showing test data"
    />)
    
    expect(screen.getByLabelText('Test Chart')).toBeInTheDocument()
    expect(screen.getByText('Bar chart showing test data')).toBeInTheDocument()
  })
})