import type { Meta, StoryObj } from '@storybook/react';
import { action } from '@storybook/addon-actions';
import { DataTable } from './data-table';

const meta: Meta<typeof DataTable> = {
  title: 'Widgets/DataTable',
  component: DataTable,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'A comprehensive data table widget with sorting, filtering, pagination, and export capabilities. Built with TanStack Table for high performance with large datasets.',
      },
    },
  },
  tags: ['autodocs'],
  argTypes: {
    title: {
      control: 'text',
      description: 'Table title',
    },
    description: {
      control: 'text',
      description: 'Table description',
    },
    configuration: {
      description: 'Data table configuration object',
    },
    data: {
      description: 'Table data array',
    },
    loading: {
      control: 'boolean',
      description: 'Loading state',
    },
    error: {
      control: 'text',
      description: 'Error message',
    },
    onExport: {
      action: 'export-requested',
      description: 'Export callback function',
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
const subjectData = [
  { 
    subjectId: 'S001', 
    site: 'Site A', 
    age: 45, 
    gender: 'Female', 
    enrollmentDate: '2024-01-15',
    status: 'Active',
    visitCount: 3,
    compliance: 0.95,
    lastVisit: '2024-03-10'
  },
  { 
    subjectId: 'S002', 
    site: 'Site A', 
    age: 62, 
    gender: 'Male', 
    enrollmentDate: '2024-01-18',
    status: 'Completed',
    visitCount: 8,
    compliance: 1.0,
    lastVisit: '2024-04-15'
  },
  { 
    subjectId: 'S003', 
    site: 'Site B', 
    age: 38, 
    gender: 'Female', 
    enrollmentDate: '2024-01-22',
    status: 'Active',
    visitCount: 4,
    compliance: 0.88,
    lastVisit: '2024-03-22'
  },
  { 
    subjectId: 'S004', 
    site: 'Site B', 
    age: 29, 
    gender: 'Male', 
    enrollmentDate: '2024-02-01',
    status: 'Withdrawn',
    visitCount: 2,
    compliance: 0.67,
    lastVisit: '2024-02-28'
  },
  { 
    subjectId: 'S005', 
    site: 'Site C', 
    age: 54, 
    gender: 'Female', 
    enrollmentDate: '2024-02-05',
    status: 'Active',
    visitCount: 3,
    compliance: 0.92,
    lastVisit: '2024-03-15'
  },
];

const adverseEventData = [
  {
    eventId: 'AE001',
    subjectId: 'S001',
    term: 'Headache',
    severity: 'Mild',
    serious: false,
    startDate: '2024-02-10',
    endDate: '2024-02-12',
    outcome: 'Recovered',
    relationship: 'Possible'
  },
  {
    eventId: 'AE002',
    subjectId: 'S002',
    term: 'Nausea',
    severity: 'Moderate',
    serious: false,
    startDate: '2024-02-15',
    endDate: '2024-02-18',
    outcome: 'Recovered',
    relationship: 'Probable'
  },
  {
    eventId: 'AE003',
    subjectId: 'S003',
    term: 'Fatigue',
    severity: 'Mild',
    serious: false,
    startDate: '2024-02-20',
    endDate: null,
    outcome: 'Ongoing',
    relationship: 'Possible'
  },
  {
    eventId: 'AE004',
    subjectId: 'S001',
    term: 'Dizziness',
    severity: 'Moderate',
    serious: false,
    startDate: '2024-03-01',
    endDate: '2024-03-05',
    outcome: 'Recovered',
    relationship: 'Unlikely'
  },
];

const labResultsData = [
  {
    subjectId: 'S001',
    visitDate: '2024-02-15',
    hemoglobin: 12.5,
    hematocrit: 37.8,
    platelets: 285000,
    wbc: 6800,
    creatinine: 0.9,
    alt: 22,
    ast: 28
  },
  {
    subjectId: 'S002',
    visitDate: '2024-02-18',
    hemoglobin: 14.2,
    hematocrit: 42.1,
    platelets: 312000,
    wbc: 7200,
    creatinine: 1.1,
    alt: 18,
    ast: 24
  },
  {
    subjectId: 'S003',
    visitDate: '2024-02-22',
    hemoglobin: 11.8,
    hematocrit: 35.6,
    platelets: 267000,
    wbc: 5900,
    creatinine: 0.8,
    alt: 31,
    ast: 35
  },
];

const siteMetricsData = [
  {
    siteId: 'Site A',
    siteName: 'University Medical Center',
    country: 'USA',
    enrolledSubjects: 45,
    targetEnrollment: 50,
    screenFailures: 12,
    completionRate: 0.78,
    avgVisitDuration: 2.5,
    lastVisit: '2024-03-20'
  },
  {
    siteId: 'Site B',
    siteName: 'Regional Hospital',
    country: 'Canada',
    enrolledSubjects: 38,
    targetEnrollment: 40,
    screenFailures: 8,
    completionRate: 0.85,
    avgVisitDuration: 2.1,
    lastVisit: '2024-03-22'
  },
  {
    siteId: 'Site C',
    siteName: 'City Clinic',
    country: 'UK',
    enrolledSubjects: 52,
    targetEnrollment: 55,
    screenFailures: 15,
    completionRate: 0.73,
    avgVisitDuration: 2.8,
    lastVisit: '2024-03-18'
  },
];

// Default subject listing
export const Default: Story = {
  args: {
    title: 'Study Subjects',
    description: 'List of all enrolled subjects with key information',
    configuration: {
      columns: [
        { field: 'subjectId', header: 'Subject ID', type: 'text', sortable: true, filterable: true },
        { field: 'site', header: 'Site', type: 'text', sortable: true, filterable: true },
        { field: 'age', header: 'Age', type: 'number', sortable: true, align: 'center' },
        { field: 'gender', header: 'Gender', type: 'text', sortable: true, filterable: true },
        { field: 'enrollmentDate', header: 'Enrollment', type: 'date', sortable: true },
        { field: 'status', header: 'Status', type: 'text', sortable: true, filterable: true },
        { field: 'visitCount', header: 'Visits', type: 'number', sortable: true, align: 'center' },
        { field: 'compliance', header: 'Compliance', type: 'number', format: 'percentage', sortable: true, align: 'right' },
      ],
      pageSize: 10,
      showPagination: true,
      showSearch: true,
      showExport: true,
      striped: true,
      compact: false,
    },
    data: subjectData,
    loading: false,
    error: undefined,
    onExport: action('export-requested'),
  },
};

// Adverse events table
export const AdverseEvents: Story = {
  args: {
    title: 'Adverse Events',
    description: 'All reported adverse events during the study',
    configuration: {
      columns: [
        { field: 'eventId', header: 'Event ID', type: 'text', sortable: true, width: 100 },
        { field: 'subjectId', header: 'Subject', type: 'text', sortable: true, filterable: true },
        { field: 'term', header: 'Medical Term', type: 'text', sortable: true, filterable: true },
        { field: 'severity', header: 'Severity', type: 'text', sortable: true, filterable: true },
        { field: 'serious', header: 'Serious', type: 'boolean', sortable: true, filterable: true },
        { field: 'startDate', header: 'Start Date', type: 'date', sortable: true },
        { field: 'endDate', header: 'End Date', type: 'date', sortable: true },
        { field: 'outcome', header: 'Outcome', type: 'text', sortable: true, filterable: true },
        { field: 'relationship', header: 'Relationship', type: 'text', sortable: true, filterable: true },
      ],
      pageSize: 5,
      showPagination: true,
      showSearch: true,
      showExport: true,
      striped: false,
      compact: true,
    },
    data: adverseEventData,
    loading: false,
    error: undefined,
    onExport: action('export-ae-data'),
  },
};

// Laboratory results
export const LabResults: Story = {
  args: {
    title: 'Laboratory Results',
    description: 'Recent lab values for all subjects',
    configuration: {
      columns: [
        { field: 'subjectId', header: 'Subject ID', type: 'text', sortable: true },
        { field: 'visitDate', header: 'Visit Date', type: 'date', sortable: true },
        { field: 'hemoglobin', header: 'Hgb (g/dL)', type: 'number', sortable: true, align: 'right' },
        { field: 'hematocrit', header: 'Hct (%)', type: 'number', sortable: true, align: 'right' },
        { field: 'platelets', header: 'Platelets', type: 'number', sortable: true, align: 'right' },
        { field: 'wbc', header: 'WBC', type: 'number', sortable: true, align: 'right' },
        { field: 'creatinine', header: 'Creat (mg/dL)', type: 'number', sortable: true, align: 'right' },
        { field: 'alt', header: 'ALT (U/L)', type: 'number', sortable: true, align: 'right' },
        { field: 'ast', header: 'AST (U/L)', type: 'number', sortable: true, align: 'right' },
      ],
      pageSize: 10,
      showPagination: true,
      showSearch: true,
      showExport: true,
      striped: true,
      compact: false,
      maxHeight: 400,
    },
    data: labResultsData,
    loading: false,
    error: undefined,
    onExport: action('export-lab-data'),
  },
};

// Site metrics with currency format
export const SiteMetrics: Story = {
  args: {
    title: 'Site Performance Metrics',
    description: 'Key performance indicators by study site',
    configuration: {
      columns: [
        { field: 'siteId', header: 'Site ID', type: 'text', sortable: true, width: 80 },
        { field: 'siteName', header: 'Site Name', type: 'text', sortable: true, filterable: true, width: 200 },
        { field: 'country', header: 'Country', type: 'text', sortable: true, filterable: true },
        { field: 'enrolledSubjects', header: 'Enrolled', type: 'number', sortable: true, align: 'center' },
        { field: 'targetEnrollment', header: 'Target', type: 'number', sortable: true, align: 'center' },
        { field: 'screenFailures', header: 'Screen Failures', type: 'number', sortable: true, align: 'center' },
        { field: 'completionRate', header: 'Completion Rate', type: 'number', format: 'percentage', sortable: true, align: 'right' },
        { field: 'avgVisitDuration', header: 'Avg Visit (hrs)', type: 'number', sortable: true, align: 'right' },
        { field: 'lastVisit', header: 'Last Visit', type: 'date', sortable: true },
      ],
      pageSize: 5,
      showPagination: true,
      showSearch: true,
      showExport: true,
      striped: false,
      compact: false,
    },
    data: siteMetricsData,
    loading: false,
    error: undefined,
    onExport: action('export-site-metrics'),
  },
};

// Compact table without pagination
export const Compact: Story = {
  args: {
    title: 'Recent Subjects',
    description: 'Latest enrolled subjects',
    configuration: {
      columns: [
        { field: 'subjectId', header: 'ID', type: 'text', width: 80 },
        { field: 'site', header: 'Site', type: 'text', width: 80 },
        { field: 'enrollmentDate', header: 'Enrolled', type: 'date', width: 100 },
        { field: 'status', header: 'Status', type: 'text', width: 100 },
      ],
      pageSize: 5,
      showPagination: false,
      showSearch: false,
      showExport: false,
      striped: true,
      compact: true,
    },
    data: subjectData.slice(0, 5),
    loading: false,
    error: undefined,
  },
};

// No search or export
export const SimpleTable: Story = {
  args: {
    title: 'Simple Data View',
    description: 'Basic table without advanced features',
    configuration: {
      columns: [
        { field: 'subjectId', header: 'Subject ID', type: 'text', sortable: true },
        { field: 'age', header: 'Age', type: 'number', sortable: true, align: 'center' },
        { field: 'gender', header: 'Gender', type: 'text', sortable: true },
        { field: 'status', header: 'Status', type: 'text', sortable: true },
      ],
      pageSize: 3,
      showPagination: true,
      showSearch: false,
      showExport: false,
      striped: false,
      compact: false,
    },
    data: subjectData.slice(0, 3),
    loading: false,
    error: undefined,
  },
};

// Large dataset simulation
export const LargeDataset: Story = {
  args: {
    title: 'Large Subject Database',
    description: 'Performance test with many subjects',
    configuration: {
      columns: [
        { field: 'subjectId', header: 'Subject ID', type: 'text', sortable: true, filterable: true },
        { field: 'site', header: 'Site', type: 'text', sortable: true, filterable: true },
        { field: 'age', header: 'Age', type: 'number', sortable: true, align: 'center' },
        { field: 'gender', header: 'Gender', type: 'text', sortable: true, filterable: true },
        { field: 'status', header: 'Status', type: 'text', sortable: true, filterable: true },
        { field: 'compliance', header: 'Compliance', type: 'number', format: 'percentage', sortable: true, align: 'right' },
      ],
      pageSize: 20,
      showPagination: true,
      showSearch: true,
      showExport: true,
      striped: true,
      compact: true,
    },
    data: Array.from({ length: 100 }, (_, i) => ({
      subjectId: `S${String(i + 1).padStart(3, '0')}`,
      site: `Site ${String.fromCharCode(65 + (i % 5))}`,
      age: Math.floor(Math.random() * 50) + 20,
      gender: Math.random() > 0.5 ? 'Male' : 'Female',
      status: ['Active', 'Completed', 'Withdrawn'][Math.floor(Math.random() * 3)],
      compliance: Math.random() * 0.3 + 0.7, // 70-100%
    })),
    loading: false,
    error: undefined,
    onExport: action('export-large-dataset'),
  },
};

// Loading state
export const Loading: Story = {
  args: {
    title: 'Loading Subject Data...',
    description: 'Please wait while data is being fetched',
    configuration: {
      columns: [
        { field: 'subjectId', header: 'Subject ID', type: 'text' },
        { field: 'site', header: 'Site', type: 'text' },
        { field: 'status', header: 'Status', type: 'text' },
      ],
      showPagination: true,
      showSearch: true,
      showExport: true,
    },
    data: [],
    loading: true,
    error: undefined,
  },
};

// Error state
export const Error: Story = {
  args: {
    title: 'Subject Data',
    description: 'Unable to load subject information',
    configuration: {
      columns: [
        { field: 'subjectId', header: 'Subject ID', type: 'text' },
        { field: 'site', header: 'Site', type: 'text' },
        { field: 'status', header: 'Status', type: 'text' },
      ],
      showPagination: true,
      showSearch: true,
      showExport: true,
    },
    data: [],
    loading: false,
    error: 'Failed to connect to the database. Please check your connection and try again.',
  },
};

// Empty data
export const Empty: Story = {
  args: {
    title: 'No Subjects Found',
    description: 'No subjects match the current criteria',
    configuration: {
      columns: [
        { field: 'subjectId', header: 'Subject ID', type: 'text' },
        { field: 'site', header: 'Site', type: 'text' },
        { field: 'status', header: 'Status', type: 'text' },
      ],
      showPagination: true,
      showSearch: true,
      showExport: true,
    },
    data: [],
    loading: false,
    error: undefined,
  },
};

// Single row
export const SingleRow: Story = {
  args: {
    title: 'Single Subject Details',
    description: 'Detailed view of one subject',
    configuration: {
      columns: [
        { field: 'subjectId', header: 'Subject ID', type: 'text' },
        { field: 'site', header: 'Site', type: 'text' },
        { field: 'age', header: 'Age', type: 'number', align: 'center' },
        { field: 'gender', header: 'Gender', type: 'text' },
        { field: 'enrollmentDate', header: 'Enrollment Date', type: 'date' },
        { field: 'status', header: 'Status', type: 'text' },
        { field: 'compliance', header: 'Compliance', type: 'number', format: 'percentage', align: 'right' },
      ],
      showPagination: false,
      showSearch: false,
      showExport: true,
    },
    data: [subjectData[0]],
    loading: false,
    error: undefined,
    onExport: action('export-single-subject'),
  },
};

// Custom width columns
export const CustomWidths: Story = {
  args: {
    title: 'Custom Column Widths',
    description: 'Table with specific column width allocations',
    configuration: {
      columns: [
        { field: 'subjectId', header: 'ID', type: 'text', width: 80, sortable: true },
        { field: 'site', header: 'Site', type: 'text', width: 100, sortable: true },
        { field: 'age', header: 'Age', type: 'number', width: 60, align: 'center', sortable: true },
        { field: 'gender', header: 'Gender', type: 'text', width: 80, sortable: true },
        { field: 'enrollmentDate', header: 'Enrollment Date', type: 'date', width: 120, sortable: true },
        { field: 'status', header: 'Status', type: 'text', width: 100, sortable: true },
        { field: 'compliance', header: 'Compliance %', type: 'number', format: 'percentage', width: 120, align: 'right', sortable: true },
      ],
      pageSize: 5,
      showPagination: true,
      showSearch: true,
      showExport: true,
      striped: true,
      compact: false,
    },
    data: subjectData,
    loading: false,
    error: undefined,
    onExport: action('export-custom-widths'),
  },
};

// Responsive mobile view
export const Mobile: Story = {
  args: {
    title: 'Subjects',
    description: 'Mobile-optimized view',
    configuration: {
      columns: [
        { field: 'subjectId', header: 'ID', type: 'text', width: 70 },
        { field: 'site', header: 'Site', type: 'text', width: 80 },
        { field: 'status', header: 'Status', type: 'text', width: 90 },
      ],
      pageSize: 5,
      showPagination: true,
      showSearch: true,
      showExport: false,
      striped: true,
      compact: true,
    },
    data: subjectData,
    loading: false,
    error: undefined,
  },
  parameters: {
    viewport: {
      defaultViewport: 'mobile',
    },
  },
};