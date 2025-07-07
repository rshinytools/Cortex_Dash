import type { Meta, StoryObj } from '@storybook/react';
import { action } from '@storybook/addon-actions';
import { PatientTimeline } from './patient-timeline';

const meta: Meta<typeof PatientTimeline> = {
  title: 'Widgets/PatientTimeline',
  component: PatientTimeline,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'A comprehensive patient timeline widget for visualizing clinical events chronologically. Supports multiple display modes including vertical timelines, horizontal timelines, and grouped patient views with customizable event types and styling.',
      },
    },
  },
  tags: ['autodocs'],
  argTypes: {
    title: {
      control: 'text',
      description: 'Timeline title',
    },
    description: {
      control: 'text',
      description: 'Timeline description',
    },
    configuration: {
      description: 'Patient timeline configuration object',
    },
    data: {
      description: 'Timeline events data array',
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

// Sample timeline data for different scenarios
const singlePatientEvents = [
  {
    date: '2024-01-15',
    eventType: 'visit',
    description: 'Screening Visit',
    category: 'Protocol Visit',
    severity: 1,
    patientId: 'P001'
  },
  {
    date: '2024-01-29',
    eventType: 'treatment',
    description: 'First dose of study drug',
    category: 'Treatment',
    severity: 1,
    patientId: 'P001'
  },
  {
    date: '2024-02-05',
    eventType: 'lab',
    description: 'Laboratory assessments - CBC, CMP',
    category: 'Laboratory',
    severity: 1,
    patientId: 'P001'
  },
  {
    date: '2024-02-12',
    eventType: 'ae',
    description: 'Mild headache, resolved with acetaminophen',
    category: 'Adverse Event',
    severity: 1,
    patientId: 'P001'
  },
  {
    date: '2024-02-19',
    eventType: 'visit',
    description: 'Week 2 Follow-up Visit',
    category: 'Protocol Visit',
    severity: 1,
    patientId: 'P001'
  },
  {
    date: '2024-02-26',
    eventType: 'vital',
    description: 'Vital signs assessment',
    category: 'Vital Signs',
    severity: 1,
    patientId: 'P001'
  },
  {
    date: '2024-03-05',
    eventType: 'assessment',
    description: 'Efficacy assessment - MADRS scale',
    category: 'Assessment',
    severity: 1,
    patientId: 'P001'
  },
  {
    date: '2024-03-12',
    eventType: 'ae',
    description: 'Moderate nausea, ongoing',
    category: 'Adverse Event',
    severity: 2,
    patientId: 'P001'
  },
  {
    date: '2024-03-19',
    eventType: 'visit',
    description: 'Week 6 Follow-up Visit',
    category: 'Protocol Visit',
    severity: 1,
    patientId: 'P001'
  },
  {
    date: '2024-03-26',
    eventType: 'lab',
    description: 'Safety laboratory assessments',
    category: 'Laboratory',
    severity: 1,
    patientId: 'P001'
  }
];

const multiPatientEvents = [
  // Patient P001 events
  {
    date: '2024-01-15',
    eventType: 'visit',
    description: 'Screening Visit',
    category: 'Protocol Visit',
    severity: 1,
    patientId: 'P001'
  },
  {
    date: '2024-01-29',
    eventType: 'treatment',
    description: 'First dose - Drug A 10mg',
    category: 'Treatment',
    severity: 1,
    patientId: 'P001'
  },
  {
    date: '2024-02-12',
    eventType: 'ae',
    description: 'Mild headache',
    category: 'Adverse Event',
    severity: 1,
    patientId: 'P001'
  },
  
  // Patient P002 events
  {
    date: '2024-01-18',
    eventType: 'visit',
    description: 'Screening Visit',
    category: 'Protocol Visit',
    severity: 1,
    patientId: 'P002'
  },
  {
    date: '2024-02-01',
    eventType: 'treatment',
    description: 'First dose - Placebo',
    category: 'Treatment',
    severity: 1,
    patientId: 'P002'
  },
  {
    date: '2024-02-15',
    eventType: 'ae',
    description: 'Severe dizziness - hospitalization required',
    category: 'Serious Adverse Event',
    severity: 4,
    patientId: 'P002'
  },
  
  // Patient P003 events
  {
    date: '2024-01-22',
    eventType: 'visit',
    description: 'Screening Visit',
    category: 'Protocol Visit',
    severity: 1,
    patientId: 'P003'
  },
  {
    date: '2024-02-05',
    eventType: 'treatment',
    description: 'First dose - Drug A 20mg',
    category: 'Treatment',
    severity: 1,
    patientId: 'P003'
  },
  {
    date: '2024-02-19',
    eventType: 'ae',
    description: 'Moderate fatigue',
    category: 'Adverse Event',
    severity: 2,
    patientId: 'P003'
  },
  {
    date: '2024-03-05',
    eventType: 'assessment',
    description: 'Primary efficacy endpoint',
    category: 'Assessment',
    severity: 1,
    patientId: 'P003'
  }
];

const safetyTimelineData = [
  {
    date: '2024-01-15',
    eventType: 'ae',
    description: 'Headache - mild, resolved',
    category: 'Nervous System',
    severity: 1,
    patientId: 'P001'
  },
  {
    date: '2024-01-18',
    eventType: 'ae',
    description: 'Nausea - moderate, ongoing',
    category: 'Gastrointestinal',
    severity: 2,
    patientId: 'P002'
  },
  {
    date: '2024-01-22',
    eventType: 'ae',
    description: 'Fatigue - mild, resolved',
    category: 'General',
    severity: 1,
    patientId: 'P003'
  },
  {
    date: '2024-02-01',
    eventType: 'ae',
    description: 'Dizziness - severe, hospitalization',
    category: 'Nervous System',
    severity: 4,
    patientId: 'P002'
  },
  {
    date: '2024-02-05',
    eventType: 'ae',
    description: 'Rash - moderate, treatment discontinued',
    category: 'Skin',
    severity: 3,
    patientId: 'P004'
  },
  {
    date: '2024-02-12',
    eventType: 'ae',
    description: 'Insomnia - mild, ongoing',
    category: 'Psychiatric',
    severity: 1,
    patientId: 'P001'
  },
  {
    date: '2024-02-15',
    eventType: 'ae',
    description: 'Chest pain - severe, cardiac evaluation',
    category: 'Cardiovascular',
    severity: 4,
    patientId: 'P005'
  }
];

const efficacyTimelineData = [
  {
    date: '2024-01-15',
    eventType: 'assessment',
    description: 'Baseline MADRS Score: 32',
    category: 'Primary Efficacy',
    severity: 1,
    patientId: 'P001'
  },
  {
    date: '2024-02-12',
    eventType: 'assessment',
    description: 'Week 4 MADRS Score: 28 (-12.5%)',
    category: 'Primary Efficacy',
    severity: 1,
    patientId: 'P001'
  },
  {
    date: '2024-03-12',
    eventType: 'assessment',
    description: 'Week 8 MADRS Score: 22 (-31.3%)',
    category: 'Primary Efficacy',
    severity: 1,
    patientId: 'P001'
  },
  {
    date: '2024-04-09',
    eventType: 'assessment',
    description: 'Week 12 MADRS Score: 18 (-43.8%)',
    category: 'Primary Efficacy',
    severity: 1,
    patientId: 'P001'
  },
  {
    date: '2024-01-18',
    eventType: 'assessment',
    description: 'Baseline CGI-S Score: 5',
    category: 'Secondary Efficacy',
    severity: 1,
    patientId: 'P001'
  },
  {
    date: '2024-02-15',
    eventType: 'assessment',
    description: 'Week 4 CGI-S Score: 4',
    category: 'Secondary Efficacy',
    severity: 1,
    patientId: 'P001'
  },
  {
    date: '2024-03-15',
    eventType: 'assessment',
    description: 'Week 8 CGI-S Score: 3',
    category: 'Secondary Efficacy',
    severity: 1,
    patientId: 'P001'
  }
];

// Default single patient timeline
export const Default: Story = {
  args: {
    title: 'Patient Timeline',
    description: 'Clinical events for Patient P001',
    configuration: {
      dateField: 'date',
      eventTypeField: 'eventType',
      eventDescriptionField: 'description',
      categoryField: 'category',
      displayType: 'vertical',
      showEventDetails: true,
      showLegend: true,
      sortOrder: 'asc',
      dateFormat: 'MMM dd, yyyy',
    },
    data: singlePatientEvents,
    loading: false,
    error: undefined,
  },
};

// Multiple patients grouped
export const MultiplePatients: Story = {
  args: {
    title: 'Multi-Patient Timeline',
    description: 'Clinical events grouped by patient',
    configuration: {
      dateField: 'date',
      eventTypeField: 'eventType',
      eventDescriptionField: 'description',
      patientIdField: 'patientId',
      categoryField: 'category',
      severityField: 'severity',
      displayType: 'vertical',
      groupByPatient: true,
      showEventDetails: true,
      showLegend: true,
      sortOrder: 'asc',
      highlightSevere: true,
      severityThreshold: 3,
      maxEventsPerPatient: 5,
    },
    data: multiPatientEvents,
    loading: false,
    error: undefined,
  },
};

// Horizontal timeline view
export const HorizontalTimeline: Story = {
  args: {
    title: 'Study Timeline - Horizontal View',
    description: 'Events displayed in horizontal timeline format',
    configuration: {
      dateField: 'date',
      eventTypeField: 'eventType',
      eventDescriptionField: 'description',
      displayType: 'horizontal',
      showLegend: true,
      sortOrder: 'asc',
    },
    data: singlePatientEvents.slice(0, 6), // Limit for better horizontal display
    loading: false,
    error: undefined,
  },
};

// Safety-focused timeline
export const SafetyTimeline: Story = {
  args: {
    title: 'Safety Timeline',
    description: 'Adverse events with severity highlighting',
    configuration: {
      dateField: 'date',
      eventTypeField: 'eventType',
      eventDescriptionField: 'description',
      patientIdField: 'patientId',
      categoryField: 'category',
      severityField: 'severity',
      displayType: 'vertical',
      groupByPatient: true,
      showEventDetails: true,
      showLegend: true,
      sortOrder: 'asc',
      highlightSevere: true,
      severityThreshold: 3,
      eventTypes: {
        ae: { label: 'Adverse Event', color: '#ef4444', icon: 'alert' },
      },
    },
    data: safetyTimelineData,
    loading: false,
    error: undefined,
  },
};

// Efficacy assessments timeline
export const EfficacyTimeline: Story = {
  args: {
    title: 'Efficacy Assessment Timeline',
    description: 'Patient response measurements over time',
    configuration: {
      dateField: 'date',
      eventTypeField: 'eventType',
      eventDescriptionField: 'description',
      categoryField: 'category',
      displayType: 'vertical',
      showEventDetails: true,
      showLegend: true,
      sortOrder: 'asc',
      eventTypes: {
        assessment: { label: 'Assessment', color: '#8b5cf6', icon: 'file' },
      },
    },
    data: efficacyTimelineData,
    loading: false,
    error: undefined,
  },
};

// Compact mode timeline
export const CompactMode: Story = {
  args: {
    title: 'Compact Timeline',
    description: 'Space-efficient timeline view',
    configuration: {
      dateField: 'date',
      eventTypeField: 'eventType',
      eventDescriptionField: 'description',
      displayType: 'vertical',
      compactMode: true,
      showEventDetails: true,
      showLegend: false,
      sortOrder: 'asc',
    },
    data: singlePatientEvents,
    loading: false,
    error: undefined,
  },
};

// Custom event types and colors
export const CustomEventTypes: Story = {
  args: {
    title: 'Custom Event Timeline',
    description: 'Timeline with custom event types and styling',
    configuration: {
      dateField: 'date',
      eventTypeField: 'eventType',
      eventDescriptionField: 'description',
      displayType: 'vertical',
      showEventDetails: true,
      showLegend: true,
      sortOrder: 'asc',
      eventTypes: {
        visit: { label: 'Clinical Visit', color: '#3b82f6', icon: 'calendar' },
        treatment: { label: 'Drug Administration', color: '#10b981', icon: 'pill' },
        ae: { label: 'Safety Event', color: '#f59e0b', icon: 'alert' },
        lab: { label: 'Laboratory Test', color: '#8b5cf6', icon: 'activity' },
        assessment: { label: 'Efficacy Assessment', color: '#ec4899', icon: 'file' },
        vital: { label: 'Vital Signs', color: '#14b8a6', icon: 'heart' },
      },
    },
    data: singlePatientEvents,
    loading: false,
    error: undefined,
  },
};

// Reverse chronological order
export const ReverseChronological: Story = {
  args: {
    title: 'Recent Events First',
    description: 'Timeline with most recent events at the top',
    configuration: {
      dateField: 'date',
      eventTypeField: 'eventType',
      eventDescriptionField: 'description',
      categoryField: 'category',
      displayType: 'vertical',
      showEventDetails: true,
      showLegend: true,
      sortOrder: 'desc',
    },
    data: singlePatientEvents,
    loading: false,
    error: undefined,
  },
};

// Limited events per patient
export const LimitedEvents: Story = {
  args: {
    title: 'Recent Events Only',
    description: 'Shows only the most recent 3 events per patient',
    configuration: {
      dateField: 'date',
      eventTypeField: 'eventType',
      eventDescriptionField: 'description',
      patientIdField: 'patientId',
      displayType: 'vertical',
      groupByPatient: true,
      showEventDetails: true,
      showLegend: true,
      sortOrder: 'desc',
      maxEventsPerPatient: 3,
    },
    data: multiPatientEvents,
    loading: false,
    error: undefined,
  },
};

// No event details (titles only)
export const TitlesOnly: Story = {
  args: {
    title: 'Event Titles Only',
    description: 'Simplified timeline showing just event types and dates',
    configuration: {
      dateField: 'date',
      eventTypeField: 'eventType',
      displayType: 'vertical',
      showEventDetails: false,
      showLegend: true,
      sortOrder: 'asc',
    },
    data: singlePatientEvents,
    loading: false,
    error: undefined,
  },
};

// Custom date format
export const CustomDateFormat: Story = {
  args: {
    title: 'Custom Date Format',
    description: 'Timeline with abbreviated date format',
    configuration: {
      dateField: 'date',
      eventTypeField: 'eventType',
      eventDescriptionField: 'description',
      displayType: 'vertical',
      showEventDetails: true,
      showLegend: true,
      sortOrder: 'asc',
      dateFormat: 'MM/dd/yy',
    },
    data: singlePatientEvents,
    loading: false,
    error: undefined,
  },
};

// Mobile responsive view
export const Mobile: Story = {
  args: {
    title: 'Mobile Timeline',
    description: 'Optimized for mobile devices',
    configuration: {
      dateField: 'date',
      eventTypeField: 'eventType',
      eventDescriptionField: 'description',
      displayType: 'vertical',
      compactMode: true,
      showEventDetails: true,
      showLegend: false,
      sortOrder: 'asc',
      dateFormat: 'MM/dd',
    },
    data: singlePatientEvents.slice(0, 5),
    loading: false,
    error: undefined,
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
    title: 'Loading Timeline...',
    description: 'Please wait while events are being retrieved',
    configuration: {
      dateField: 'date',
      eventTypeField: 'eventType',
      eventDescriptionField: 'description',
      displayType: 'vertical',
      showLegend: true,
    },
    data: [],
    loading: true,
    error: undefined,
  },
};

// Error state
export const Error: Story = {
  args: {
    title: 'Patient Timeline',
    description: 'Unable to load timeline data',
    configuration: {
      dateField: 'date',
      eventTypeField: 'eventType',
      eventDescriptionField: 'description',
      displayType: 'vertical',
      showLegend: true,
    },
    data: [],
    loading: false,
    error: 'Failed to retrieve patient timeline data from the clinical database. Please check your connection and try again.',
  },
};

// Empty timeline
export const Empty: Story = {
  args: {
    title: 'No Events Found',
    description: 'No clinical events match the current criteria',
    configuration: {
      dateField: 'date',
      eventTypeField: 'eventType',
      eventDescriptionField: 'description',
      displayType: 'vertical',
      showLegend: true,
    },
    data: [],
    loading: false,
    error: undefined,
  },
};

// Single event
export const SingleEvent: Story = {
  args: {
    title: 'Single Event Timeline',
    description: 'Timeline with just one recorded event',
    configuration: {
      dateField: 'date',
      eventTypeField: 'eventType',
      eventDescriptionField: 'description',
      categoryField: 'category',
      displayType: 'vertical',
      showEventDetails: true,
      showLegend: true,
      sortOrder: 'asc',
    },
    data: [singlePatientEvents[0]],
    loading: false,
    error: undefined,
  },
};

// Complex multi-patient study
export const ComplexStudy: Story = {
  args: {
    title: 'Complex Study Timeline',
    description: 'Multiple patients with diverse event types',
    configuration: {
      dateField: 'date',
      eventTypeField: 'eventType',
      eventDescriptionField: 'description',
      patientIdField: 'patientId',
      categoryField: 'category',
      severityField: 'severity',
      displayType: 'vertical',
      groupByPatient: true,
      showEventDetails: true,
      showLegend: true,
      sortOrder: 'asc',
      highlightSevere: true,
      severityThreshold: 3,
      eventTypes: {
        visit: { label: 'Protocol Visit', color: '#3b82f6', icon: 'calendar' },
        treatment: { label: 'Treatment', color: '#10b981', icon: 'pill' },
        ae: { label: 'Adverse Event', color: '#f59e0b', icon: 'alert' },
        lab: { label: 'Laboratory', color: '#8b5cf6', icon: 'activity' },
        assessment: { label: 'Assessment', color: '#ec4899', icon: 'file' },
        vital: { label: 'Vitals', color: '#14b8a6', icon: 'heart' },
      },
    },
    data: [
      ...multiPatientEvents,
      ...safetyTimelineData.slice(0, 3),
      ...efficacyTimelineData.slice(0, 3),
    ],
    loading: false,
    error: undefined,
  },
};