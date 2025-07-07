import type { Meta, StoryObj } from '@storybook/react';
import { action } from '@storybook/addon-actions';
import { PieChart } from './pie-chart';

const meta: Meta<typeof PieChart> = {
  title: 'Widgets/PieChart',
  component: PieChart,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'A versatile pie chart widget for displaying categorical data distributions. Supports both pie and donut chart styles with customizable colors, labels, and interactivity.',
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
      description: 'Pie chart configuration object',
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
const genderDistribution = [
  { gender: 'Male', count: 68, percentage: 0.52 },
  { gender: 'Female', count: 62, percentage: 0.48 },
];

const ageGroupDistribution = [
  { ageGroup: '18-30', subjects: 25 },
  { ageGroup: '31-45', subjects: 45 },
  { ageGroup: '46-60', subjects: 38 },
  { ageGroup: '61-75', subjects: 22 },
  { ageGroup: '76+', subjects: 8 },
];

const siteEnrollment = [
  { site: 'Site A', enrolled: 45 },
  { site: 'Site B', enrolled: 38 },
  { site: 'Site C', enrolled: 52 },
  { site: 'Site D', enrolled: 29 },
  { site: 'Site E', enrolled: 36 },
];

const adverseEventSeverity = [
  { severity: 'Mild', events: 125 },
  { severity: 'Moderate', events: 48 },
  { severity: 'Severe', events: 15 },
  { severity: 'Life-threatening', events: 3 },
];

const subjectStatus = [
  { status: 'Active', count: 145 },
  { status: 'Completed', count: 78 },
  { status: 'Withdrawn', count: 23 },
  { status: 'Screen Failed', count: 41 },
];

const treatmentAllocation = [
  { treatment: 'Placebo', subjects: 52 },
  { treatment: 'Drug A 10mg', subjects: 48 },
  { treatment: 'Drug A 20mg', subjects: 50 },
];

const visitCompliance = [
  { compliance: 'Compliant', subjects: 156 },
  { compliance: 'Partially Compliant', subjects: 38 },
  { compliance: 'Non-Compliant', subjects: 12 },
];

// Default pie chart - gender distribution
export const Default: Story = {
  args: {
    title: 'Gender Distribution',
    description: 'Distribution of subjects by gender',
    configuration: {
      dataField: 'gender',
      labelField: 'gender',
      valueField: 'count',
      showLegend: true,
      showTooltip: true,
      showLabels: false,
      showPercentage: true,
      valueFormat: 'number',
      decimals: 0,
      activeOnHover: true,
      legendPosition: 'bottom',
    },
    data: genderDistribution,
    loading: false,
    error: undefined,
  },
};

// Donut chart with inner radius
export const DonutChart: Story = {
  args: {
    title: 'Age Group Distribution',
    description: 'Subject distribution across age groups',
    configuration: {
      dataField: 'ageGroup',
      labelField: 'ageGroup',
      valueField: 'subjects',
      showLegend: true,
      showTooltip: true,
      showLabels: false,
      showPercentage: true,
      innerRadius: 60,
      valueFormat: 'number',
      decimals: 0,
      activeOnHover: true,
      legendPosition: 'right',
    },
    data: ageGroupDistribution,
    loading: false,
    error: undefined,
  },
};

// With custom colors
export const CustomColors: Story = {
  args: {
    title: 'Site Enrollment',
    description: 'Number of subjects enrolled per site',
    configuration: {
      dataField: 'site',
      labelField: 'site',
      valueField: 'enrolled',
      showLegend: true,
      showTooltip: true,
      showLabels: true,
      showPercentage: false,
      valueFormat: 'number',
      decimals: 0,
      activeOnHover: false,
      colors: ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57'],
      legendPosition: 'bottom',
    },
    data: siteEnrollment,
    loading: false,
    error: undefined,
  },
};

// Safety data - AE severity
export const SafetyData: Story = {
  args: {
    title: 'Adverse Event Severity',
    description: 'Distribution of adverse events by severity level',
    configuration: {
      dataField: 'severity',
      labelField: 'severity',
      valueField: 'events',
      showLegend: true,
      showTooltip: true,
      showLabels: false,
      showPercentage: true,
      valueFormat: 'number',
      decimals: 0,
      activeOnHover: true,
      colors: ['#10B981', '#F59E0B', '#EF4444', '#991B1B'],
      legendPosition: 'bottom',
    },
    data: adverseEventSeverity,
    loading: false,
    error: undefined,
  },
};

// Subject status overview
export const SubjectStatus: Story = {
  args: {
    title: 'Subject Status Overview',
    description: 'Current status of all subjects in the study',
    configuration: {
      dataField: 'status',
      labelField: 'status',
      valueField: 'count',
      showLegend: true,
      showTooltip: true,
      showLabels: true,
      showPercentage: false,
      innerRadius: 40,
      valueFormat: 'number',
      decimals: 0,
      activeOnHover: true,
      colors: ['#3B82F6', '#10B981', '#F59E0B', '#EF4444'],
      legendPosition: 'right',
    },
    data: subjectStatus,
    loading: false,
    error: undefined,
  },
};

// Treatment allocation
export const TreatmentAllocation: Story = {
  args: {
    title: 'Treatment Group Allocation',
    description: 'Randomization distribution across treatment arms',
    configuration: {
      dataField: 'treatment',
      labelField: 'treatment',
      valueField: 'subjects',
      showLegend: true,
      showTooltip: true,
      showLabels: true,
      showPercentage: true,
      valueFormat: 'number',
      decimals: 0,
      activeOnHover: false,
      colors: ['#6B7280', '#8B5CF6', '#EC4899'],
      startAngle: 0,
      endAngle: 360,
      legendPosition: 'bottom',
    },
    data: treatmentAllocation,
    loading: false,
    error: undefined,
  },
};

// Half pie chart
export const HalfPie: Story = {
  args: {
    title: 'Visit Compliance Rate',
    description: 'Subject compliance with scheduled visits',
    configuration: {
      dataField: 'compliance',
      labelField: 'compliance',
      valueField: 'subjects',
      showLegend: true,
      showTooltip: true,
      showLabels: false,
      showPercentage: true,
      startAngle: 180,
      endAngle: 0,
      valueFormat: 'number',
      decimals: 0,
      activeOnHover: true,
      colors: ['#10B981', '#F59E0B', '#EF4444'],
      legendPosition: 'bottom',
    },
    data: visitCompliance,
    loading: false,
    error: undefined,
  },
};

// Small pie chart without legend
export const Small: Story = {
  args: {
    title: 'Gender Split',
    description: undefined,
    configuration: {
      dataField: 'gender',
      labelField: 'gender',
      valueField: 'count',
      showLegend: false,
      showTooltip: true,
      showLabels: true,
      showPercentage: true,
      valueFormat: 'number',
      decimals: 0,
      activeOnHover: false,
    },
    data: genderDistribution,
    loading: false,
    error: undefined,
  },
  parameters: {
    viewport: {
      defaultViewport: 'mobile',
    },
  },
};

// Single segment
export const SingleSegment: Story = {
  args: {
    title: 'Study Completion Rate',
    description: '100% of enrolled subjects completed the study',
    configuration: {
      dataField: 'category',
      labelField: 'category',
      valueField: 'percentage',
      showLegend: false,
      showTooltip: true,
      showLabels: true,
      showPercentage: false,
      valueFormat: 'percentage',
      decimals: 0,
      activeOnHover: false,
      colors: ['#10B981'],
    },
    data: [
      { category: 'Completed', percentage: 1.0 },
    ],
    loading: false,
    error: undefined,
  },
};

// Many segments
export const ManySegments: Story = {
  args: {
    title: 'Global Site Distribution',
    description: 'Enrollment across all participating sites',
    configuration: {
      dataField: 'site',
      labelField: 'site',
      valueField: 'subjects',
      showLegend: true,
      showTooltip: true,
      showLabels: false,
      showPercentage: false,
      innerRadius: 50,
      valueFormat: 'number',
      decimals: 0,
      activeOnHover: true,
      legendPosition: 'right',
    },
    data: Array.from({ length: 12 }, (_, i) => ({
      site: `Site ${String.fromCharCode(65 + i)}`,
      subjects: Math.floor(Math.random() * 30) + 10,
    })),
    loading: false,
    error: undefined,
  },
};

// Percentage format
export const PercentageFormat: Story = {
  args: {
    title: 'Protocol Deviation Rates',
    description: 'Percentage of subjects with protocol deviations',
    configuration: {
      dataField: 'category',
      labelField: 'category',
      valueField: 'rate',
      showLegend: true,
      showTooltip: true,
      showLabels: true,
      showPercentage: false,
      valueFormat: 'percentage',
      decimals: 1,
      activeOnHover: true,
      colors: ['#10B981', '#F59E0B'],
      legendPosition: 'bottom',
    },
    data: [
      { category: 'No Deviations', rate: 0.847 },
      { category: 'With Deviations', rate: 0.153 },
    ],
    loading: false,
    error: undefined,
  },
};

// Legend positions
export const LegendTop: Story = {
  args: {
    title: 'Enrollment by Country',
    description: 'Subject distribution across countries',
    configuration: {
      dataField: 'country',
      labelField: 'country',
      valueField: 'subjects',
      showLegend: true,
      showTooltip: true,
      showLabels: false,
      showPercentage: true,
      valueFormat: 'number',
      decimals: 0,
      activeOnHover: false,
      legendPosition: 'top',
      colors: ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'],
    },
    data: [
      { country: 'USA', subjects: 85 },
      { country: 'Canada', subjects: 42 },
      { country: 'UK', subjects: 38 },
      { country: 'Germany', subjects: 31 },
      { country: 'France', subjects: 24 },
    ],
    loading: false,
    error: undefined,
  },
};

// No tooltip or legend
export const Minimal: Story = {
  args: {
    title: 'Simple Distribution',
    description: 'Minimal pie chart with just labels',
    configuration: {
      dataField: 'category',
      labelField: 'category',
      valueField: 'value',
      showLegend: false,
      showTooltip: false,
      showLabels: true,
      showPercentage: true,
      valueFormat: 'number',
      decimals: 0,
      activeOnHover: false,
    },
    data: [
      { category: 'A', value: 45 },
      { category: 'B', value: 35 },
      { category: 'C', value: 20 },
    ],
    loading: false,
    error: undefined,
  },
};

// Loading state
export const Loading: Story = {
  args: {
    title: 'Loading Chart Data...',
    description: 'Please wait while data is being fetched',
    configuration: {
      dataField: 'category',
      labelField: 'category',
      valueField: 'value',
      showLegend: true,
      showTooltip: true,
    },
    data: [],
    loading: true,
    error: undefined,
  },
};

// Error state
export const Error: Story = {
  args: {
    title: 'Distribution Chart',
    description: 'Unable to load chart data',
    configuration: {
      dataField: 'category',
      labelField: 'category',
      valueField: 'value',
      showLegend: true,
      showTooltip: true,
    },
    data: [],
    loading: false,
    error: 'Failed to fetch distribution data from the server',
  },
};

// Empty data
export const Empty: Story = {
  args: {
    title: 'No Data Available',
    description: 'No data matches the current filters',
    configuration: {
      dataField: 'category',
      labelField: 'category',
      valueField: 'value',
      showLegend: true,
      showTooltip: true,
    },
    data: [],
    loading: false,
    error: undefined,
  },
};

// Interactive with hover effects
export const Interactive: Story = {
  args: {
    title: 'Interactive Chart',
    description: 'Hover over segments to see effects',
    configuration: {
      dataField: 'department',
      labelField: 'department',
      valueField: 'budget',
      showLegend: true,
      showTooltip: true,
      showLabels: false,
      showPercentage: true,
      innerRadius: 40,
      valueFormat: 'currency',
      decimals: 0,
      activeOnHover: true,
      colors: ['#3B82F6', '#10B981', '#F59E0B', '#EF4444'],
      legendPosition: 'right',
    },
    data: [
      { department: 'Clinical Operations', budget: 1250000 },
      { department: 'Data Management', budget: 850000 },
      { department: 'Regulatory Affairs', budget: 420000 },
      { department: 'Site Management', budget: 680000 },
    ],
    loading: false,
    error: undefined,
  },
};

// Custom angle range
export const CustomAngles: Story = {
  args: {
    title: 'Protocol Compliance Score',
    description: 'Overall compliance across all sites',
    configuration: {
      dataField: 'metric',
      labelField: 'metric',
      valueField: 'score',
      showLegend: false,
      showTooltip: true,
      showLabels: true,
      showPercentage: false,
      startAngle: 90,
      endAngle: -90,
      innerRadius: 60,
      valueFormat: 'percentage',
      decimals: 1,
      activeOnHover: false,
      colors: ['#10B981', '#F59E0B'],
    },
    data: [
      { metric: 'Compliant', score: 0.892 },
      { metric: 'Non-Compliant', score: 0.108 },
    ],
    loading: false,
    error: undefined,
  },
};