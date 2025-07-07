import type { Meta, StoryObj } from '@storybook/react';
import { action } from '@storybook/addon-actions';
import { MetricCard } from './metric-card';

const meta: Meta<typeof MetricCard> = {
  title: 'Widgets/MetricCard',
  component: MetricCard,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'A metric card widget that displays a single metric value with optional trend indicators and comparison data.',
      },
    },
  },
  tags: ['autodocs'],
  argTypes: {
    title: {
      control: 'text',
      description: 'The title displayed at the top of the metric card',
    },
    value: {
      control: 'number',
      description: 'The main metric value to display',
    },
    unit: {
      control: 'text',
      description: 'The unit of measurement for the metric',
    },
    trend: {
      control: 'select',
      options: ['up', 'down', 'stable'],
      description: 'The trend direction of the metric',
    },
    trendValue: {
      control: 'number',
      description: 'The numerical trend value (percentage change)',
    },
    showTrend: {
      control: 'boolean',
      description: 'Whether to display the trend indicator',
    },
    color: {
      control: 'select',
      options: ['default', 'success', 'warning', 'error', 'info'],
      description: 'The color theme of the metric card',
    },
    size: {
      control: 'select',
      options: ['small', 'medium', 'large'],
      description: 'The size of the metric card',
    },
    isLoading: {
      control: 'boolean',
      description: 'Whether the metric card is in a loading state',
    },
    onClick: {
      action: 'clicked',
      description: 'Callback fired when the metric card is clicked',
    },
  },
};

export default meta;
type Story = StoryObj<typeof meta>;

// Default metric card
export const Default: Story = {
  args: {
    title: 'Total Enrolled Subjects',
    value: 156,
    unit: 'subjects',
    trend: 'up',
    trendValue: 12.5,
    showTrend: true,
    color: 'default',
    size: 'medium',
    isLoading: false,
    onClick: action('metric-card-clicked'),
  },
};

// Loading state
export const Loading: Story = {
  args: {
    ...Default.args,
    isLoading: true,
  },
};

// No trend data
export const WithoutTrend: Story = {
  args: {
    ...Default.args,
    showTrend: false,
    trendValue: undefined,
  },
};

// Negative trend
export const DownwardTrend: Story = {
  args: {
    ...Default.args,
    title: 'Screen Failures',
    value: 23,
    trend: 'down',
    trendValue: -8.3,
    color: 'success',
  },
};

// Warning state
export const Warning: Story = {
  args: {
    ...Default.args,
    title: 'Data Quality Score',
    value: 72,
    unit: '%',
    trend: 'down',
    trendValue: -5.2,
    color: 'warning',
  },
};

// Error state
export const Error: Story = {
  args: {
    ...Default.args,
    title: 'System Uptime',
    value: 94.2,
    unit: '%',
    trend: 'down',
    trendValue: -2.1,
    color: 'error',
  },
};

// Large size
export const Large: Story = {
  args: {
    ...Default.args,
    size: 'large',
    value: 1234,
  },
};

// Small size
export const Small: Story = {
  args: {
    ...Default.args,
    size: 'small',
    title: 'AEs',
    value: 47,
  },
};

// High numbers
export const HighNumbers: Story = {
  args: {
    ...Default.args,
    title: 'Total Lab Results',
    value: 125678,
    unit: 'results',
    trend: 'up',
    trendValue: 23.4,
  },
};

// Decimal values
export const DecimalValues: Story = {
  args: {
    ...Default.args,
    title: 'Average Age',
    value: 64.7,
    unit: 'years',
    trend: 'stable',
    trendValue: 0.2,
  },
};

// Percentage values
export const Percentage: Story = {
  args: {
    ...Default.args,
    title: 'Completion Rate',
    value: 87.5,
    unit: '%',
    trend: 'up',
    trendValue: 3.1,
    color: 'success',
  },
};

// Interactive example
export const Interactive: Story = {
  args: {
    ...Default.args,
    title: 'Click Me!',
  },
  play: async ({ canvasElement, args }) => {
    // This story demonstrates interaction testing
    const canvas = canvasElement;
    const metricCard = canvas.querySelector('[data-testid="metric-card"]');
    if (metricCard) {
      // Simulate click
      metricCard.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    }
  },
};