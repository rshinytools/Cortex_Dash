// ABOUTME: Data contracts for all widget types defining their field requirements
// ABOUTME: Each widget declares what data it needs and provides CDISC mapping suggestions

import { DataContract } from '@/types/widget';

/**
 * Metric Card Widget Data Contract
 * Displays a single metric value with optional trend and comparison
 */
export const metricCardDataContract: DataContract = {
  requiredFields: [
    {
      name: 'value',
      type: 'number',
      description: 'The primary metric value to display',
      commonPatterns: ['value', 'result', 'count', 'total', 'sum'],
    },
  ],
  optionalFields: [
    {
      name: 'previousValue',
      type: 'number',
      description: 'Previous value for comparison (e.g., previous period)',
      commonPatterns: ['previous_value', 'last_value', 'prior_value'],
    },
    {
      name: 'trend',
      type: 'number',
      description: 'Trend percentage change from previous value',
      commonPatterns: ['trend', 'change', 'delta', 'percent_change'],
    },
    {
      name: 'trendDirection',
      type: 'string',
      description: 'Direction of trend (up/down/neutral)',
      commonPatterns: ['trend_direction', 'direction', 'trend_indicator'],
      validation: {
        enum: ['up', 'down', 'neutral'],
      },
    },
    {
      name: 'timestamp',
      type: 'datetime',
      description: 'When this metric was calculated',
      commonPatterns: ['timestamp', 'date', 'datetime', 'calculated_at'],
    },
  ],
  calculatedFields: [
    {
      name: 'trend',
      type: 'number',
      description: 'Calculate trend if not provided',
      calculation: '((value - previousValue) / previousValue) * 100',
      dependsOn: ['value', 'previousValue'],
    },
  ],
  dataSources: {
    primary: {
      datasetType: 'aggregated',
      refreshRate: 3600, // 1 hour
    },
  },
  mappingSuggestions: {
    enrollment: {
      value: 'ENROLLED_COUNT',
      previousValue: 'PREV_ENROLLED_COUNT',
    },
    safety: {
      value: 'AE_COUNT',
      previousValue: 'PREV_AE_COUNT',
    },
    efficacy: {
      value: 'RESPONSE_RATE',
      previousValue: 'PREV_RESPONSE_RATE',
    },
  },
};

/**
 * Line Chart Widget Data Contract
 * Displays time series data with multiple series support
 */
export const lineChartDataContract: DataContract = {
  requiredFields: [
    {
      name: 'date',
      type: 'date',
      description: 'Date/time for x-axis',
      sdtmMapping: 'VISITDT',
      adamMapping: 'ADT',
      commonPatterns: ['date', 'datetime', 'visit_date', 'assessment_date'],
    },
    {
      name: 'value',
      type: 'number',
      description: 'Value for y-axis',
      adamMapping: 'AVAL',
      commonPatterns: ['value', 'result', 'measurement', 'score'],
    },
  ],
  optionalFields: [
    {
      name: 'series',
      type: 'string',
      description: 'Series/group identifier for multiple lines',
      sdtmMapping: 'ARM',
      adamMapping: 'TRT01A',
      commonPatterns: ['series', 'group', 'category', 'treatment_arm'],
    },
    {
      name: 'lowerBound',
      type: 'number',
      description: 'Lower confidence interval or error bound',
      commonPatterns: ['lower_bound', 'ci_lower', 'error_lower'],
    },
    {
      name: 'upperBound',
      type: 'number',
      description: 'Upper confidence interval or error bound',
      commonPatterns: ['upper_bound', 'ci_upper', 'error_upper'],
    },
    {
      name: 'label',
      type: 'string',
      description: 'Label for data point',
      commonPatterns: ['label', 'name', 'description'],
    },
  ],
  dataSources: {
    primary: {
      datasetType: 'timeseries',
      refreshRate: 3600,
    },
  },
  mappingSuggestions: {
    efficacy: {
      date: 'VISITDT',
      value: 'AVAL',
      series: 'TRT01A',
    },
    laboratory: {
      date: 'ADT',
      value: 'AVAL',
      series: 'PARAM',
    },
    vitals: {
      date: 'VSDTC',
      value: 'VSSTRESN',
      series: 'VSTEST',
    },
  },
};

/**
 * Table Widget Data Contract
 * Displays tabular data with configurable columns
 */
export const tableDataContract: DataContract = {
  requiredFields: [
    {
      name: 'id',
      type: 'string',
      description: 'Unique identifier for each row',
      sdtmMapping: 'USUBJID',
      commonPatterns: ['id', 'subject_id', 'patient_id', 'record_id'],
    },
  ],
  optionalFields: [
    // Columns are dynamically configured, so we define common ones
    {
      name: 'subject',
      type: 'string',
      description: 'Subject identifier',
      sdtmMapping: 'USUBJID',
      commonPatterns: ['subject', 'subject_id', 'patient_id'],
    },
    {
      name: 'site',
      type: 'string',
      description: 'Site identifier',
      sdtmMapping: 'SITEID',
      commonPatterns: ['site', 'site_id', 'center', 'location'],
    },
    {
      name: 'status',
      type: 'string',
      description: 'Current status',
      commonPatterns: ['status', 'state', 'disposition'],
    },
    {
      name: 'date',
      type: 'date',
      description: 'Relevant date',
      commonPatterns: ['date', 'datetime', 'visit_date'],
    },
  ],
  dataSources: {
    primary: {
      datasetType: 'tabular',
      refreshRate: 3600,
    },
  },
  mappingSuggestions: {
    subjectListing: {
      id: 'USUBJID',
      subject: 'USUBJID',
      site: 'SITEID',
      status: 'DSDECOD',
    },
    adverseEvents: {
      id: 'AESEQ',
      subject: 'USUBJID',
      site: 'SITEID',
      date: 'AESTDTC',
    },
  },
};

/**
 * Enrollment Map Widget Data Contract
 * Displays geographic enrollment data
 */
export const enrollmentMapDataContract: DataContract = {
  requiredFields: [
    {
      name: 'siteId',
      type: 'string',
      description: 'Site identifier',
      sdtmMapping: 'SITEID',
      commonPatterns: ['site_id', 'site', 'center_id', 'location_id'],
    },
    {
      name: 'latitude',
      type: 'number',
      description: 'Site latitude coordinate',
      commonPatterns: ['latitude', 'lat', 'site_latitude'],
      validation: {
        min: -90,
        max: 90,
      },
    },
    {
      name: 'longitude',
      type: 'number',
      description: 'Site longitude coordinate',
      commonPatterns: ['longitude', 'lng', 'lon', 'site_longitude'],
      validation: {
        min: -180,
        max: 180,
      },
    },
    {
      name: 'enrollmentCount',
      type: 'number',
      description: 'Number of subjects enrolled at site',
      commonPatterns: ['enrollment_count', 'enrolled', 'subject_count', 'patient_count'],
      defaultValue: 0,
    },
  ],
  optionalFields: [
    {
      name: 'siteName',
      type: 'string',
      description: 'Human-readable site name',
      commonPatterns: ['site_name', 'center_name', 'location_name'],
    },
    {
      name: 'country',
      type: 'string',
      description: 'Country code or name',
      sdtmMapping: 'COUNTRY',
      commonPatterns: ['country', 'country_code', 'nation'],
    },
    {
      name: 'city',
      type: 'string',
      description: 'City name',
      commonPatterns: ['city', 'town', 'location'],
    },
    {
      name: 'targetEnrollment',
      type: 'number',
      description: 'Target enrollment for the site',
      commonPatterns: ['target_enrollment', 'planned_enrollment', 'enrollment_goal'],
    },
    {
      name: 'status',
      type: 'string',
      description: 'Site status (active, completed, etc.)',
      commonPatterns: ['status', 'site_status', 'state'],
    },
    {
      name: 'lastEnrollmentDate',
      type: 'date',
      description: 'Date of last enrollment at site',
      commonPatterns: ['last_enrollment', 'latest_enrollment', 'recent_enrollment'],
    },
  ],
  calculatedFields: [
    {
      name: 'enrollmentPercentage',
      type: 'number',
      description: 'Percentage of target enrollment achieved',
      calculation: '(enrollmentCount / targetEnrollment) * 100',
      dependsOn: ['enrollmentCount', 'targetEnrollment'],
    },
  ],
  dataSources: {
    primary: {
      datasetType: 'site_summary',
      refreshRate: 86400, // 24 hours
    },
    secondary: [
      {
        datasetType: 'ADSL',
        joinOn: 'siteId',
      },
    ],
  },
  mappingSuggestions: {
    standard: {
      siteId: 'SITEID',
      country: 'COUNTRY',
      enrollmentCount: 'ENROLLED_COUNT',
    },
  },
};

/**
 * Export all data contracts
 */
export const widgetDataContracts = {
  metric_card: metricCardDataContract,
  line_chart: lineChartDataContract,
  table: tableDataContract,
  enrollment_map: enrollmentMapDataContract,
};

/**
 * Get data contract for a widget type
 */
export function getWidgetDataContract(widgetType: string): DataContract | undefined {
  return widgetDataContracts[widgetType as keyof typeof widgetDataContracts];
}