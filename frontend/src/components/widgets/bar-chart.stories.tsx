import type { Meta, StoryObj } from '@storybook/react';
import { action } from '@storybook/addon-actions';
import { BarChart } from './bar-chart';

const meta: Meta<typeof BarChart> = {
  title: 'Widgets/BarChart',
  component: BarChart,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'A versatile bar chart widget for displaying categorical data comparisons. Supports both vertical and horizontal orientations, multiple series, stacking, and various styling options.',
      },
    },
  },
  tags: ['autodocs'],
  argTypes: {
    title: {
      control: 'text',
      description: 'Chart title',
    },
    description: {
      control: 'text',
      description: 'Chart description',
    },
    configuration: {
      description: 'Bar chart configuration object',
    },
    data: {
      description: 'Chart data array',
    },
    loading: {
      control: 'boolean',
      description: 'Loading state',
    },
    error: {
      control: 'text',
      description: 'Error message',
    },
    className: {
      control: 'text',
      description: 'Additional CSS classes',
    },
  },
};

export default meta;
type Story = StoryObj<typeof meta>;

// Sample data for different scenarios
const enrollmentData = [
  { site: 'Site A', enrolled: 45, target: 50, screened: 67 },
  { site: 'Site B', enrolled: 38, target: 40, screened: 52 },
  { site: 'Site C', enrolled: 52, target: 55, screened: 78 },
  { site: 'Site D', enrolled: 29, target: 35, screened: 41 },
  { site: 'Site E', enrolled: 41, target: 45, screened: 59 },
];

const adverseEventsData = [
  { severity: 'Mild', week1: 12, week2: 15, week3: 18, week4: 22 },
  { severity: 'Moderate', week1: 5, week2: 8, week3: 12, week4: 15 },
  { severity: 'Severe', week1: 2, week2: 3, week3: 5, week4: 7 },
];

const demographicsData = [
  { ageGroup: '18-30', male: 45, female: 52 },
  { ageGroup: '31-45', male: 38, female: 41 },
  { ageGroup: '46-60', male: 29, female: 35 },
  { ageGroup: '61-75', male: 22, female: 28 },
  { ageGroup: '76+', male: 8, female: 12 },
];

const drugComplianceData = [
  { treatment: 'Placebo', compliant: 85.5, partialCompliant: 12.3, nonCompliant: 2.2 },
  { treatment: 'Drug A 10mg', compliant: 78.2, partialCompliant: 18.1, nonCompliant: 3.7 },
  { treatment: 'Drug A 20mg', compliant: 72.4, partialCompliant: 22.1, nonCompliant: 5.5 },
];

const labValuesData = [
  { parameter: 'Hemoglobin', baseline: 12.5, week4: 13.1, week8: 13.8 },
  { parameter: 'Platelets', baseline: 285, week4: 295, week8: 310 },
  { parameter: 'WBC Count', baseline: 6.8, week4: 7.2, week8: 7.5 },
  { parameter: 'Creatinine', baseline: 1.1, week4: 1.0, week8: 0.9 },
];

// Default vertical bar chart
export const Default: Story = {
  args: {
    title: 'Subject Enrollment by Site',
    description: 'Current enrollment progress compared to targets',
    configuration: {
      xAxisField: 'site',
      yAxisFields: [
        { field: 'enrolled', label: 'Enrolled', color: '#3b82f6' },
        { field: 'target', label: 'Target', color: '#10b981' },
      ],
      xAxisLabel: 'Study Sites',
      yAxisLabel: 'Number of Subjects',
      showGrid: true,
      showLegend: true,
      showTooltip: true,
      showValues: false,
      valueFormat: 'number',
      decimals: 0,
    },
    data: enrollmentData,
    loading: false,
    error: undefined,
  },
};

// Horizontal bar chart
export const Horizontal: Story = {
  args: {
    title: 'Enrollment Progress by Site',
    description: 'Horizontal view of enrollment data',
    configuration: {
      xAxisField: 'site',
      yAxisFields: [
        { field: 'enrolled', label: 'Enrolled Subjects', color: '#8b5cf6' },
      ],
      orientation: 'horizontal',
      xAxisLabel: 'Number of Subjects',
      yAxisLabel: 'Sites',
      showGrid: true,
      showLegend: false,
      showTooltip: true,
      showValues: true,
      valueFormat: 'number',
      decimals: 0,
      sortBy: 'value',
      sortOrder: 'desc',
    },
    data: enrollmentData,
    loading: false,
    error: undefined,
  },
};

// Stacked bar chart
export const Stacked: Story = {
  args: {
    title: 'Adverse Events by Severity Over Time',
    description: 'Stacked view of AE distribution',
    configuration: {
      xAxisField: 'severity',
      yAxisFields: [
        { field: 'week1', label: 'Week 1', color: '#3b82f6', stackId: 'stack' },
        { field: 'week2', label: 'Week 2', color: '#10b981', stackId: 'stack' },
        { field: 'week3', label: 'Week 3', color: '#f59e0b', stackId: 'stack' },
        { field: 'week4', label: 'Week 4', color: '#ef4444', stackId: 'stack' },
      ],
      xAxisLabel: 'Severity Level',
      yAxisLabel: 'Number of Events',
      showGrid: true,
      showLegend: true,
      showTooltip: true,
      showValues: false,
      valueFormat: 'number',
      decimals: 0,
    },
    data: adverseEventsData,
    loading: false,
    error: undefined,
  },
};

// Grouped bar chart
export const Grouped: Story = {
  args: {
    title: 'Demographics by Age Group',
    description: 'Male vs Female distribution across age groups',
    configuration: {
      xAxisField: 'ageGroup',
      yAxisFields: [
        { field: 'male', label: 'Male', color: '#3b82f6' },
        { field: 'female', label: 'Female', color: '#ec4899' },
      ],
      xAxisLabel: 'Age Group',
      yAxisLabel: 'Number of Subjects',
      showGrid: true,
      showLegend: true,
      showTooltip: true,
      showValues: true,
      valueFormat: 'number',
      decimals: 0,
      barSize: 40,
      barGap: 4,
      categoryGap: 20,
    },
    data: demographicsData,
    loading: false,
    error: undefined,
  },
};

// Percentage format
export const Percentage: Story = {
  args: {
    title: 'Drug Compliance Rates',
    description: 'Compliance percentages by treatment group',
    configuration: {
      xAxisField: 'treatment',
      yAxisFields: [
        { field: 'compliant', label: 'Compliant', color: '#10b981', stackId: 'compliance' },
        { field: 'partialCompliant', label: 'Partial', color: '#f59e0b', stackId: 'compliance' },
        { field: 'nonCompliant', label: 'Non-compliant', color: '#ef4444', stackId: 'compliance' },
      ],
      xAxisLabel: 'Treatment Group',
      yAxisLabel: 'Compliance Rate',
      showGrid: true,
      showLegend: true,
      showTooltip: true,
      showValues: false,
      valueFormat: 'percentage',
      decimals: 1,
    },
    data: drugComplianceData.map(item => ({
      ...item,
      compliant: item.compliant / 100,
      partialCompliant: item.partialCompliant / 100,
      nonCompliant: item.nonCompliant / 100,
    })),
    loading: false,
    error: undefined,
  },
};

// With reference lines
export const WithReferenceLines: Story = {
  args: {
    title: 'Laboratory Values Over Time',
    description: 'Lab parameters with normal range indicators',
    configuration: {
      xAxisField: 'parameter',
      yAxisFields: [
        { field: 'baseline', label: 'Baseline', color: '#6b7280' },
        { field: 'week4', label: 'Week 4', color: '#3b82f6' },
        { field: 'week8', label: 'Week 8', color: '#10b981' },
      ],
      xAxisLabel: 'Lab Parameter',
      yAxisLabel: 'Value',
      showGrid: true,
      showLegend: true,
      showTooltip: true,
      showValues: false,
      valueFormat: 'number',
      decimals: 1,
      referenceLines: [
        { y: 12, label: 'Normal Hgb Min', color: '#ef4444', strokeDasharray: '5 5' },
        { y: 16, label: 'Normal Hgb Max', color: '#ef4444', strokeDasharray: '5 5' },
      ],
    },
    data: labValuesData,
    loading: false,
    error: undefined,
  },
};

// Large numbers format
export const LargeNumbers: Story = {
  args: {
    title: 'Sample Collection by Site',
    description: 'Total samples collected per site',
    configuration: {
      xAxisField: 'site',
      yAxisFields: [
        { field: 'samples', label: 'Total Samples', color: '#8b5cf6' },
      ],
      xAxisLabel: 'Study Sites',
      yAxisLabel: 'Number of Samples',
      showGrid: true,
      showLegend: false,
      showTooltip: true,
      showValues: true,
      valueFormat: 'number',
      decimals: 0,
      sortBy: 'value',
      sortOrder: 'desc',
    },
    data: [
      { site: 'Site A', samples: 12456 },
      { site: 'Site B', samples: 9823 },
      { site: 'Site C', samples: 15672 },
      { site: 'Site D', samples: 7891 },
      { site: 'Site E', samples: 11234 },
    ],
    loading: false,
    error: undefined,
  },
};

// Limited bars with sorting
export const TopSites: Story = {
  args: {
    title: 'Top 3 Performing Sites',
    description: 'Sites with highest enrollment rates',
    configuration: {
      xAxisField: 'site',
      yAxisFields: [
        { field: 'enrolled', label: 'Enrolled', color: '#10b981' },
      ],
      xAxisLabel: 'Study Sites',
      yAxisLabel: 'Enrolled Subjects',
      showGrid: true,
      showLegend: false,
      showTooltip: true,
      showValues: true,
      valueFormat: 'number',
      decimals: 0,
      sortBy: 'value',
      sortOrder: 'desc',
      maxBars: 3,
    },
    data: enrollmentData,
    loading: false,
    error: undefined,
  },
};

// Small size
export const Small: Story = {
  args: {
    ...Default.args,
    title: 'Enrollment',
    description: undefined,
    configuration: {
      ...Default.args?.configuration,
      showLegend: false,
      showValues: false,
    },
  },
  parameters: {
    viewport: {
      defaultViewport: 'mobile',
    },
  },
};

// Loading state
export const Loading: Story = {
  args: {
    title: 'Loading Chart Data...',
    description: 'Please wait while data is being fetched',
    configuration: {
      xAxisField: 'site',
      yAxisFields: [
        { field: 'enrolled', label: 'Enrolled', color: '#3b82f6' },
      ],
    },
    data: [],
    loading: true,
    error: undefined,
  },
};

// Error state
export const Error: Story = {
  args: {
    title: 'Enrollment Data',
    description: 'Unable to load chart data',
    configuration: {
      xAxisField: 'site',
      yAxisFields: [
        { field: 'enrolled', label: 'Enrolled', color: '#3b82f6' },
      ],
    },
    data: [],
    loading: false,
    error: 'Failed to fetch enrollment data from the server',
  },
};

// Empty data
export const Empty: Story = {
  args: {
    title: 'No Enrollment Data',
    description: 'No data available for the selected period',
    configuration: {
      xAxisField: 'site',
      yAxisFields: [
        { field: 'enrolled', label: 'Enrolled', color: '#3b82f6' },
      ],
    },
    data: [],
    loading: false,
    error: undefined,
  },
};

// Single bar
export const SingleBar: Story = {
  args: {
    title: 'Total Study Enrollment',
    description: 'Overall enrollment across all sites',
    configuration: {
      xAxisField: 'category',
      yAxisFields: [
        { field: 'total', label: 'Total Enrolled', color: '#3b82f6' },
      ],
      showGrid: false,
      showLegend: false,
      showTooltip: true,
      showValues: true,
      valueFormat: 'number',
      decimals: 0,
    },
    data: [
      { category: 'Study XYZ-123', total: 205 },
    ],
    loading: false,
    error: undefined,
  },
};

// Many bars (scrollable)
export const ManyBars: Story = {
  args: {
    title: 'Global Site Performance',
    description: 'Enrollment data from all study sites',
    configuration: {
      xAxisField: 'site',
      yAxisFields: [
        { field: 'enrolled', label: 'Enrolled', color: '#3b82f6' },
      ],
      xAxisLabel: 'Study Sites',
      yAxisLabel: 'Enrolled Subjects',
      showGrid: true,
      showLegend: false,
      showTooltip: true,
      showValues: false,
      valueFormat: 'number',
      decimals: 0,
    },
    data: Array.from({ length: 25 }, (_, i) => ({
      site: `Site ${String.fromCharCode(65 + i)}`,
      enrolled: Math.floor(Math.random() * 50) + 10,
    })),
    loading: false,
    error: undefined,
  },
};

// Custom styling
export const CustomStyling: Story = {
  args: {
    title: 'Custom Styled Chart',
    description: 'Chart with custom bar sizing and spacing',
    configuration: {
      xAxisField: 'month',
      yAxisFields: [
        { field: 'visits', label: 'Site Visits', color: '#8b5cf6' },
      ],
      xAxisLabel: 'Month',
      yAxisLabel: 'Number of Visits',
      showGrid: true,
      showLegend: false,
      showTooltip: true,
      showValues: true,
      valueFormat: 'number',
      decimals: 0,
      barSize: 60,
      barGap: 8,
      categoryGap: 30,
    },
    data: [
      { month: 'Jan', visits: 145 },
      { month: 'Feb', visits: 167 },
      { month: 'Mar', visits: 189 },
      { month: 'Apr', visits: 203 },
      { month: 'May', visits: 178 },
    ],
    loading: false,
    error: undefined,
  },
};