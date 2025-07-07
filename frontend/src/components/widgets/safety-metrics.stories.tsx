import type { Meta, StoryObj } from '@storybook/react';
import { action } from '@storybook/addon-actions';
import { SafetyMetrics } from './safety-metrics';

const meta: Meta<typeof SafetyMetrics> = {
  title: 'Widgets/SafetyMetrics',
  component: SafetyMetrics,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'A specialized safety metrics widget for clinical trial adverse event monitoring. Provides multiple visualization modes for AE data including summary statistics, severity breakdowns, system organ class distributions, and timeline analysis.',
      },
    },
  },
  tags: ['autodocs'],
  argTypes: {
    title: {
      control: 'text',
      description: 'Widget title',
    },
    description: {
      control: 'text',
      description: 'Widget description',
    },
    configuration: {
      description: 'Safety metrics configuration object',
    },
    data: {
      description: 'Safety data object',
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

// Sample safety data for different scenarios
const comprehensiveSafetyData = {
  totalAEs: 324,
  totalSAEs: 18,
  totalSubjectsWithAE: 156,
  totalSubjects: 200,
  aesBySeverity: [
    { severity: 'mild', count: 198, percentage: 61.1 },
    { severity: 'moderate', count: 108, percentage: 33.3 },
    { severity: 'severe', count: 16, percentage: 4.9 },
    { severity: 'lifeThreatening', count: 2, percentage: 0.6 },
  ],
  aesBySystem: [
    { system: 'Gastrointestinal', count: 89, percentage: 27.5 },
    { system: 'Nervous System', count: 67, percentage: 20.7 },
    { system: 'Skin & Subcutaneous', count: 45, percentage: 13.9 },
    { system: 'Respiratory', count: 38, percentage: 11.7 },
    { system: 'Musculoskeletal', count: 32, percentage: 9.9 },
    { system: 'Cardiovascular', count: 28, percentage: 8.6 },
    { system: 'Psychiatric', count: 15, percentage: 4.6 },
    { system: 'Renal & Urinary', count: 10, percentage: 3.1 },
  ],
  saeTimeline: [
    { date: '2024-01-15', count: 2, cumulative: 2 },
    { date: '2024-02-01', count: 1, cumulative: 3 },
    { date: '2024-02-15', count: 3, cumulative: 6 },
    { date: '2024-03-01', count: 2, cumulative: 8 },
    { date: '2024-03-15', count: 1, cumulative: 9 },
    { date: '2024-04-01', count: 4, cumulative: 13 },
    { date: '2024-04-15', count: 2, cumulative: 15 },
    { date: '2024-05-01', count: 1, cumulative: 16 },
    { date: '2024-05-15', count: 2, cumulative: 18 },
  ],
  trends: {
    aeRate: 78.0,
    saeRate: 9.0,
    rateChange: -2.3,
  },
};

const earlySafetyData = {
  totalAEs: 45,
  totalSAEs: 2,
  totalSubjectsWithAE: 28,
  totalSubjects: 50,
  aesBySeverity: [
    { severity: 'mild', count: 32, percentage: 71.1 },
    { severity: 'moderate', count: 11, percentage: 24.4 },
    { severity: 'severe', count: 2, percentage: 4.4 },
  ],
  aesBySystem: [
    { system: 'Gastrointestinal', count: 18, percentage: 40.0 },
    { system: 'Nervous System', count: 12, percentage: 26.7 },
    { system: 'Skin & Subcutaneous', count: 8, percentage: 17.8 },
    { system: 'Respiratory', count: 7, percentage: 15.6 },
  ],
  saeTimeline: [
    { date: '2024-01-15', count: 1, cumulative: 1 },
    { date: '2024-02-15', count: 1, cumulative: 2 },
  ],
  trends: {
    aeRate: 56.0,
    saeRate: 4.0,
    rateChange: 0.0,
  },
};

const highRiskSafetyData = {
  totalAEs: 567,
  totalSAEs: 45,
  totalSubjectsWithAE: 189,
  totalSubjects: 200,
  aesBySeverity: [
    { severity: 'mild', count: 245, percentage: 43.2 },
    { severity: 'moderate', count: 198, percentage: 34.9 },
    { severity: 'severe', count: 89, percentage: 15.7 },
    { severity: 'lifeThreatening', count: 35, percentage: 6.2 },
  ],
  aesBySystem: [
    { system: 'Cardiovascular', count: 124, percentage: 21.9 },
    { system: 'Nervous System', count: 98, percentage: 17.3 },
    { system: 'Gastrointestinal', count: 87, percentage: 15.3 },
    { system: 'Respiratory', count: 76, percentage: 13.4 },
    { system: 'Renal & Urinary', count: 54, percentage: 9.5 },
    { system: 'Hepatic', count: 42, percentage: 7.4 },
    { system: 'Hematologic', count: 38, percentage: 6.7 },
    { system: 'Metabolic', count: 32, percentage: 5.6 },
    { system: 'Immune System', count: 16, percentage: 2.8 },
  ],
  saeTimeline: [
    { date: '2024-01-15', count: 3, cumulative: 3 },
    { date: '2024-02-01', count: 5, cumulative: 8 },
    { date: '2024-02-15', count: 7, cumulative: 15 },
    { date: '2024-03-01', count: 6, cumulative: 21 },
    { date: '2024-03-15', count: 4, cumulative: 25 },
    { date: '2024-04-01', count: 8, cumulative: 33 },
    { date: '2024-04-15', count: 5, cumulative: 38 },
    { date: '2024-05-01', count: 4, cumulative: 42 },
    { date: '2024-05-15', count: 3, cumulative: 45 },
  ],
  trends: {
    aeRate: 94.5,
    saeRate: 22.5,
    rateChange: 15.2,
  },
};

// Default safety summary view
export const Default: Story = {
  args: {
    title: 'Safety Overview',
    description: 'Summary of adverse events in the study',
    configuration: {
      displayType: 'summary',
      showTrends: true,
      showRelatedOnly: false,
    },
    data: comprehensiveSafetyData,
    loading: false,
    error: undefined,
  },
};

// AE by severity pie chart
export const AEBySeverity: Story = {
  args: {
    title: 'Adverse Events by Severity',
    description: 'Distribution of AEs across severity levels',
    configuration: {
      displayType: 'ae-by-severity',
      showTrends: false,
      showRelatedOnly: false,
      severityColors: {
        mild: '#10b981',
        moderate: '#f59e0b', 
        severe: '#ef4444',
        lifeThreatening: '#7c3aed',
      },
    },
    data: comprehensiveSafetyData,
    loading: false,
    error: undefined,
  },
};

// AE by system organ class
export const AEBySystem: Story = {
  args: {
    title: 'Adverse Events by System',
    description: 'AE distribution across organ systems',
    configuration: {
      displayType: 'ae-by-system',
      showTrends: false,
      showRelatedOnly: false,
    },
    data: comprehensiveSafetyData,
    loading: false,
    error: undefined,
  },
};

// SAE timeline
export const SAETimeline: Story = {
  args: {
    title: 'Serious Adverse Events Timeline',
    description: 'SAE occurrence over time with cumulative count',
    configuration: {
      displayType: 'sae-timeline',
      showTrends: false,
      showRelatedOnly: false,
    },
    data: comprehensiveSafetyData,
    loading: false,
    error: undefined,
  },
};

// Early study phase with minimal AEs
export const EarlyPhase: Story = {
  args: {
    title: 'Early Phase Safety Data',
    description: 'Safety profile in the initial 50 subjects',
    configuration: {
      displayType: 'summary',
      showTrends: true,
      showRelatedOnly: false,
    },
    data: earlySafetyData,
    loading: false,
    error: undefined,
  },
};

// High-risk profile with many SAEs
export const HighRiskProfile: Story = {
  args: {
    title: 'High-Risk Safety Profile',
    description: 'Study with elevated SAE rates requiring monitoring',
    configuration: {
      displayType: 'summary',
      showTrends: true,
      showRelatedOnly: false,
    },
    data: highRiskSafetyData,
    loading: false,
    error: undefined,
  },
};

// Severity distribution for high-risk study
export const HighRiskSeverity: Story = {
  args: {
    title: 'High-Risk AE Severity Distribution',
    description: 'Concerning severity profile with many severe events',
    configuration: {
      displayType: 'ae-by-severity',
      showTrends: false,
      showRelatedOnly: false,
      severityColors: {
        mild: '#10b981',
        moderate: '#f59e0b',
        severe: '#ef4444',
        lifeThreatening: '#7c3aed',
      },
    },
    data: highRiskSafetyData,
    loading: false,
    error: undefined,
  },
};

// System distribution for high-risk study
export const HighRiskSystemDistribution: Story = {
  args: {
    title: 'High-Risk System Distribution',
    description: 'AE distribution showing cardiovascular signals',
    configuration: {
      displayType: 'ae-by-system',
      showTrends: false,
      showRelatedOnly: false,
    },
    data: highRiskSafetyData,
    loading: false,
    error: undefined,
  },
};

// Escalating SAE timeline
export const EscalatingSAETimeline: Story = {
  args: {
    title: 'Escalating SAE Pattern',
    description: 'Timeline showing concerning SAE rate increase',
    configuration: {
      displayType: 'sae-timeline',
      showTrends: false,
      showRelatedOnly: false,
    },
    data: highRiskSafetyData,
    loading: false,
    error: undefined,
  },
};

// Custom severity colors
export const CustomSeverityColors: Story = {
  args: {
    title: 'Custom Color Scheme',
    description: 'AE severity with custom color palette',
    configuration: {
      displayType: 'ae-by-severity',
      showTrends: false,
      showRelatedOnly: false,
      severityColors: {
        mild: '#22d3ee',      // cyan
        moderate: '#fb923c',   // orange
        severe: '#f87171',     // red
        lifeThreatening: '#a78bfa', // purple
      },
    },
    data: comprehensiveSafetyData,
    loading: false,
    error: undefined,
  },
};

// Clean study with minimal AEs
export const CleanSafetyProfile: Story = {
  args: {
    title: 'Clean Safety Profile',
    description: 'Study with very low AE rates',
    configuration: {
      displayType: 'summary',
      showTrends: true,
      showRelatedOnly: false,
    },
    data: {
      totalAEs: 23,
      totalSAEs: 0,
      totalSubjectsWithAE: 18,
      totalSubjects: 150,
      aesBySeverity: [
        { severity: 'mild', count: 20, percentage: 87.0 },
        { severity: 'moderate', count: 3, percentage: 13.0 },
      ],
      trends: {
        aeRate: 12.0,
        saeRate: 0.0,
        rateChange: -1.5,
      },
    },
    loading: false,
    error: undefined,
  },
};

// Loading state
export const Loading: Story = {
  args: {
    title: 'Loading Safety Data...',
    description: 'Please wait while safety information is being retrieved',
    configuration: {
      displayType: 'summary',
      showTrends: true,
      showRelatedOnly: false,
    },
    data: undefined,
    loading: true,
    error: undefined,
  },
};

// Error state
export const Error: Story = {
  args: {
    title: 'Safety Metrics',
    description: 'Unable to load safety data',
    configuration: {
      displayType: 'summary',
      showTrends: true,
      showRelatedOnly: false,
    },
    data: undefined,
    loading: false,
    error: 'Failed to retrieve safety data from the clinical database. Please check your connection and try again.',
  },
};

// No data available
export const NoData: Story = {
  args: {
    title: 'No Safety Data',
    description: 'No adverse events reported yet',
    configuration: {
      displayType: 'summary',
      showTrends: false,
      showRelatedOnly: false,
    },
    data: {
      totalAEs: 0,
      totalSAEs: 0,
      totalSubjectsWithAE: 0,
      totalSubjects: 0,
    },
    loading: false,
    error: undefined,
  },
};

// Small widget size
export const Compact: Story = {
  args: {
    title: 'Safety Summary',
    description: undefined,
    configuration: {
      displayType: 'summary',
      showTrends: false,
      showRelatedOnly: false,
    },
    data: {
      totalAEs: 156,
      totalSAEs: 8,
      totalSubjectsWithAE: 89,
      totalSubjects: 120,
      aesBySeverity: [
        { severity: 'mild', count: 98, percentage: 62.8 },
        { severity: 'moderate', count: 45, percentage: 28.8 },
        { severity: 'severe', count: 13, percentage: 8.3 },
      ],
    },
    loading: false,
    error: undefined,
  },
  parameters: {
    viewport: {
      defaultViewport: 'mobile',
    },
  },
};

// Related events only
export const RelatedEventsOnly: Story = {
  args: {
    title: 'Drug-Related Safety Events',
    description: 'AEs with possible/probable/definite relationship to study drug',
    configuration: {
      displayType: 'summary',
      showTrends: true,
      showRelatedOnly: true,
    },
    data: {
      totalAEs: 89,
      totalSAEs: 5,
      totalSubjectsWithAE: 67,
      totalSubjects: 200,
      aesBySeverity: [
        { severity: 'mild', count: 52, percentage: 58.4 },
        { severity: 'moderate', count: 28, percentage: 31.5 },
        { severity: 'severe', count: 9, percentage: 10.1 },
      ],
      trends: {
        aeRate: 33.5,
        saeRate: 2.5,
        rateChange: 1.8,
      },
    },
    loading: false,
    error: undefined,
  },
};

// Large study with comprehensive data
export const LargeStudyData: Story = {
  args: {
    title: 'Large Phase III Study Safety',
    description: 'Comprehensive safety data from 1000+ subject study',
    configuration: {
      displayType: 'summary',
      showTrends: true,
      showRelatedOnly: false,
    },
    data: {
      totalAEs: 2847,
      totalSAEs: 156,
      totalSubjectsWithAE: 856,
      totalSubjects: 1024,
      aesBySeverity: [
        { severity: 'mild', count: 1698, percentage: 59.6 },
        { severity: 'moderate', count: 854, percentage: 30.0 },
        { severity: 'severe', count: 234, percentage: 8.2 },
        { severity: 'lifeThreatening', count: 61, percentage: 2.1 },
      ],
      trends: {
        aeRate: 83.6,
        saeRate: 15.2,
        rateChange: -0.8,
      },
    },
    loading: false,
    error: undefined,
  },
};