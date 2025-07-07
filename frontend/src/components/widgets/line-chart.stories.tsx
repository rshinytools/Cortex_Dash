import type { Meta, StoryObj } from '@storybook/react';
import { action } from '@storybook/addon-actions';
import { LineChart } from './line-chart';

const meta: Meta<typeof LineChart> = {
  title: 'Widgets/LineChart',
  component: LineChart,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'A line chart widget for displaying time-series data and trends. Supports multiple data series, interactive tooltips, and various styling options.',
      },
    },
  },
  tags: ['autodocs'],
  argTypes: {
    data: {
      description: 'Chart data with labels and datasets',
    },
    title: {
      control: 'text',
      description: 'Chart title',
    },
    height: {
      control: 'number',
      description: 'Chart height in pixels',
    },
    showLegend: {
      control: 'boolean',
      description: 'Whether to show the legend',
    },
    showGrid: {
      control: 'boolean',
      description: 'Whether to show grid lines',
    },
    showTooltip: {
      control: 'boolean',
      description: 'Whether to show tooltips on hover',
    },
    interactive: {
      control: 'boolean',
      description: 'Whether the chart is interactive',
    },
    colorScheme: {
      control: 'select',
      options: ['default', 'clinical', 'safety', 'efficacy'],
      description: 'Color scheme for the chart',
    },
    onDataPointClick: {
      action: 'data-point-clicked',
      description: 'Callback fired when a data point is clicked',
    },
  },
};

export default meta;
type Story = StoryObj<typeof meta>;

// Sample data for stories
const enrollmentData = {
  labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
  datasets: [
    {
      label: 'Enrolled',
      data: [12, 19, 24, 32, 45, 58],
      borderColor: '#3B82F6',
      backgroundColor: 'rgba(59, 130, 246, 0.1)',
      tension: 0.4,
    },
    {
      label: 'Target',
      data: [15, 25, 35, 45, 55, 65],
      borderColor: '#10B981',
      backgroundColor: 'rgba(16, 185, 129, 0.1)',
      borderDash: [5, 5],
      tension: 0.4,
    },
  ],
};

const safetyData = {
  labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5', 'Week 6'],
  datasets: [
    {
      label: 'Mild AEs',
      data: [5, 8, 12, 10, 15, 18],
      borderColor: '#F59E0B',
      backgroundColor: 'rgba(245, 158, 11, 0.1)',
    },
    {
      label: 'Moderate AEs',
      data: [2, 3, 5, 4, 6, 8],
      borderColor: '#EF4444',
      backgroundColor: 'rgba(239, 68, 68, 0.1)',
    },
    {
      label: 'Severe AEs',
      data: [0, 1, 1, 2, 1, 3],
      borderColor: '#991B1B',
      backgroundColor: 'rgba(153, 27, 27, 0.1)',
    },
  ],
};

const biomarkerData = {
  labels: ['Baseline', '4 weeks', '8 weeks', '12 weeks', '16 weeks', '20 weeks'],
  datasets: [
    {
      label: 'Placebo',
      data: [100, 98, 102, 99, 101, 103],
      borderColor: '#6B7280',
      backgroundColor: 'rgba(107, 114, 128, 0.1)',
    },
    {
      label: 'Drug A 10mg',
      data: [100, 85, 72, 68, 65, 62],
      borderColor: '#8B5CF6',
      backgroundColor: 'rgba(139, 92, 246, 0.1)',
    },
    {
      label: 'Drug A 20mg',
      data: [100, 78, 58, 45, 38, 32],
      borderColor: '#EC4899',
      backgroundColor: 'rgba(236, 72, 153, 0.1)',
    },
  ],
};

// Default line chart
export const Default: Story = {
  args: {
    title: 'Subject Enrollment Trend',
    data: enrollmentData,
    height: 400,
    showLegend: true,
    showGrid: true,
    showTooltip: true,
    interactive: true,
    colorScheme: 'default',
    onDataPointClick: action('data-point-clicked'),
  },
};

// Safety monitoring chart
export const SafetyMonitoring: Story = {
  args: {
    title: 'Adverse Events Over Time',
    data: safetyData,
    height: 350,
    showLegend: true,
    showGrid: true,
    showTooltip: true,
    interactive: true,
    colorScheme: 'safety',
    onDataPointClick: action('safety-data-clicked'),
  },
};

// Biomarker efficacy chart
export const BiomarkerEfficacy: Story = {
  args: {
    title: 'Biomarker Response by Treatment Group',
    data: biomarkerData,
    height: 400,
    showLegend: true,
    showGrid: true,
    showTooltip: true,
    interactive: true,
    colorScheme: 'efficacy',
    onDataPointClick: action('biomarker-clicked'),
  },
};

// Minimal chart without legend or grid
export const Minimal: Story = {
  args: {
    title: 'Simple Trend',
    data: {
      labels: ['Q1', 'Q2', 'Q3', 'Q4'],
      datasets: [
        {
          label: 'Value',
          data: [45, 52, 48, 61],
          borderColor: '#3B82F6',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
        },
      ],
    },
    height: 250,
    showLegend: false,
    showGrid: false,
    showTooltip: true,
    interactive: false,
    colorScheme: 'default',
  },
};

// Small chart
export const Small: Story = {
  args: {
    ...Default.args,
    height: 200,
    showLegend: false,
  },
};

// Large chart
export const Large: Story = {
  args: {
    ...Default.args,
    height: 600,
  },
};

// Loading state
export const Loading: Story = {
  args: {
    title: 'Loading Chart Data...',
    data: { labels: [], datasets: [] },
    height: 400,
    showLegend: true,
    showGrid: true,
    showTooltip: true,
    interactive: false,
    isLoading: true,
  },
};

// Empty state
export const Empty: Story = {
  args: {
    title: 'No Data Available',
    data: { labels: [], datasets: [] },
    height: 400,
    showLegend: true,
    showGrid: true,
    showTooltip: true,
    interactive: false,
    isEmpty: true,
  },
};

// Single data point
export const SinglePoint: Story = {
  args: {
    title: 'Single Data Point',
    data: {
      labels: ['Today'],
      datasets: [
        {
          label: 'Current Value',
          data: [42],
          borderColor: '#3B82F6',
          backgroundColor: 'rgba(59, 130, 246, 0.5)',
          pointRadius: 8,
        },
      ],
    },
    height: 300,
    showLegend: false,
    showGrid: true,
    showTooltip: true,
    interactive: true,
  },
};

// Many data points
export const ManyDataPoints: Story = {
  args: {
    title: 'Daily Enrollment (6 months)',
    data: {
      labels: Array.from({ length: 180 }, (_, i) => `Day ${i + 1}`),
      datasets: [
        {
          label: 'Daily Enrollment',
          data: Array.from({ length: 180 }, () => Math.floor(Math.random() * 10)),
          borderColor: '#3B82F6',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          pointRadius: 1,
        },
      ],
    },
    height: 400,
    showLegend: true,
    showGrid: true,
    showTooltip: true,
    interactive: true,
  },
};

// Responsive chart
export const Responsive: Story = {
  args: {
    ...Default.args,
    responsive: true,
  },
  parameters: {
    viewport: {
      defaultViewport: 'mobile',
    },
  },
};