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
 * Bar Chart Widget Data Contract
 * Displays categorical data with bars for comparison
 */
export const barChartDataContract: DataContract = {
  requiredFields: [
    {
      name: 'category',
      type: 'string',
      description: 'Category name for x-axis',
      commonPatterns: ['category', 'name', 'group', 'site', 'treatment'],
    },
    {
      name: 'value',
      type: 'number',
      description: 'Numeric value for bar height',
      commonPatterns: ['value', 'count', 'total', 'sum', 'average'],
    },
  ],
  optionalFields: [
    {
      name: 'series',
      type: 'string',
      description: 'Series identifier for grouped bars',
      commonPatterns: ['series', 'group', 'type', 'arm'],
    },
    {
      name: 'sortOrder',
      type: 'number',
      description: 'Custom sort order for categories',
      commonPatterns: ['sort_order', 'order', 'sequence'],
    },
  ],
  dataSources: {
    primary: {
      datasetType: 'aggregated',
      refreshRate: 3600,
    },
  },
  mappingSuggestions: {
    siteEnrollment: {
      category: 'SITEID',
      value: 'ENROLLED_COUNT',
    },
    adverseEventsByType: {
      category: 'AEDECOD',
      value: 'AE_COUNT',
      series: 'AESEV',
    },
  },
};

/**
 * Scatter Plot Widget Data Contract
 * Displays correlation between two numeric variables
 */
export const scatterPlotDataContract: DataContract = {
  requiredFields: [
    {
      name: 'xValue',
      type: 'number',
      description: 'X-axis numeric value',
      commonPatterns: ['x_value', 'baseline', 'age', 'dose'],
    },
    {
      name: 'yValue',
      type: 'number',
      description: 'Y-axis numeric value',
      commonPatterns: ['y_value', 'outcome', 'response', 'result'],
    },
  ],
  optionalFields: [
    {
      name: 'id',
      type: 'string',
      description: 'Unique identifier for each point',
      sdtmMapping: 'USUBJID',
      commonPatterns: ['id', 'subject_id', 'patient_id'],
    },
    {
      name: 'group',
      type: 'string',
      description: 'Grouping variable for color coding',
      sdtmMapping: 'ARM',
      commonPatterns: ['group', 'category', 'treatment_arm', 'cohort'],
    },
    {
      name: 'size',
      type: 'number',
      description: 'Size variable for bubble plots',
      commonPatterns: ['size', 'weight', 'count', 'duration'],
    },
    {
      name: 'label',
      type: 'string',
      description: 'Label for tooltip display',
      commonPatterns: ['label', 'name', 'description'],
    },
  ],
  dataSources: {
    primary: {
      datasetType: 'analysis',
      refreshRate: 3600,
    },
  },
  mappingSuggestions: {
    efficacyCorrelation: {
      xValue: 'BASELINE_VALUE',
      yValue: 'CHANGE_FROM_BASELINE',
      group: 'TRT01A',
      id: 'USUBJID',
    },
    doseResponse: {
      xValue: 'DOSE',
      yValue: 'AVAL',
      group: 'PARAM',
    },
  },
};

/**
 * Heatmap Widget Data Contract
 * Displays matrix data with color intensity
 */
export const heatmapDataContract: DataContract = {
  requiredFields: [
    {
      name: 'xCategory',
      type: 'string',
      description: 'X-axis category',
      commonPatterns: ['x_category', 'column', 'visit', 'timepoint'],
    },
    {
      name: 'yCategory',
      type: 'string',
      description: 'Y-axis category',
      commonPatterns: ['y_category', 'row', 'parameter', 'test'],
    },
    {
      name: 'value',
      type: 'number',
      description: 'Cell value for color intensity',
      commonPatterns: ['value', 'correlation', 'frequency', 'score'],
    },
  ],
  optionalFields: [
    {
      name: 'label',
      type: 'string',
      description: 'Display label for cell',
      commonPatterns: ['label', 'formatted_value', 'display_value'],
    },
    {
      name: 'tooltip',
      type: 'string',
      description: 'Tooltip text for additional info',
      commonPatterns: ['tooltip', 'description', 'details'],
    },
  ],
  dataSources: {
    primary: {
      datasetType: 'matrix',
      refreshRate: 86400,
    },
  },
  mappingSuggestions: {
    correlationMatrix: {
      xCategory: 'PARAM1',
      yCategory: 'PARAM2',
      value: 'CORRELATION',
    },
    visitCompletion: {
      xCategory: 'VISIT',
      yCategory: 'SITEID',
      value: 'COMPLETION_RATE',
    },
  },
};

/**
 * KPI Comparison Widget Data Contract
 * Compares key performance indicators across periods or groups
 */
export const kpiComparisonDataContract: DataContract = {
  requiredFields: [
    {
      name: 'kpiValue',
      type: 'number',
      description: 'Current KPI value',
      commonPatterns: ['value', 'current', 'actual', 'result'],
    },
  ],
  optionalFields: [
    {
      name: 'groupName',
      type: 'string',
      description: 'Group or category name',
      commonPatterns: ['group', 'name', 'category', 'site'],
    },
    {
      name: 'previousValue',
      type: 'number',
      description: 'Previous period value for comparison',
      commonPatterns: ['previous', 'prior', 'last_period'],
    },
    {
      name: 'targetValue',
      type: 'number',
      description: 'Target or goal value',
      commonPatterns: ['target', 'goal', 'planned', 'expected'],
    },
    {
      name: 'benchmarkValue',
      type: 'number',
      description: 'Benchmark or reference value',
      commonPatterns: ['benchmark', 'reference', 'industry_average'],
    },
    {
      name: 'period',
      type: 'string',
      description: 'Time period identifier',
      commonPatterns: ['period', 'month', 'quarter', 'year'],
    },
  ],
  calculatedFields: [
    {
      name: 'changePercent',
      type: 'number',
      description: 'Percentage change from previous',
      calculation: '((kpiValue - previousValue) / previousValue) * 100',
      dependsOn: ['kpiValue', 'previousValue'],
    },
    {
      name: 'achievementPercent',
      type: 'number',
      description: 'Percentage of target achieved',
      calculation: '(kpiValue / targetValue) * 100',
      dependsOn: ['kpiValue', 'targetValue'],
    },
  ],
  dataSources: {
    primary: {
      datasetType: 'kpi_summary',
      refreshRate: 3600,
    },
  },
  mappingSuggestions: {
    enrollmentKPIs: {
      kpiValue: 'CURRENT_ENROLLED',
      previousValue: 'PREVIOUS_ENROLLED',
      targetValue: 'TARGET_ENROLLED',
      groupName: 'SITEID',
    },
    dataQualityKPIs: {
      kpiValue: 'QUERY_RATE',
      benchmarkValue: 'INDUSTRY_QUERY_RATE',
      groupName: 'FORM_NAME',
    },
  },
};

/**
 * Patient Timeline Widget Data Contract
 * Displays chronological events for patients
 */
export const patientTimelineDataContract: DataContract = {
  requiredFields: [
    {
      name: 'eventDate',
      type: 'date',
      description: 'Date/time of the event',
      sdtmMapping: 'DTC',
      commonPatterns: ['date', 'datetime', 'event_date', 'visit_date'],
    },
    {
      name: 'eventType',
      type: 'string',
      description: 'Type or category of event',
      commonPatterns: ['event_type', 'type', 'category', 'domain'],
    },
  ],
  optionalFields: [
    {
      name: 'patientId',
      type: 'string',
      description: 'Patient identifier',
      sdtmMapping: 'USUBJID',
      commonPatterns: ['patient_id', 'subject_id', 'usubjid'],
    },
    {
      name: 'eventDescription',
      type: 'string',
      description: 'Detailed description of the event',
      commonPatterns: ['description', 'event_description', 'details', 'term'],
    },
    {
      name: 'severity',
      type: 'string',
      description: 'Severity or grade of event',
      sdtmMapping: 'SEV',
      commonPatterns: ['severity', 'grade', 'intensity'],
    },
    {
      name: 'category',
      type: 'string',
      description: 'Sub-category or classification',
      commonPatterns: ['category', 'subcategory', 'class', 'system'],
    },
    {
      name: 'duration',
      type: 'number',
      description: 'Duration of event in days',
      commonPatterns: ['duration', 'days', 'length'],
    },
    {
      name: 'outcome',
      type: 'string',
      description: 'Event outcome or resolution',
      commonPatterns: ['outcome', 'resolution', 'status'],
    },
  ],
  dataSources: {
    primary: {
      datasetType: 'events',
      refreshRate: 3600,
    },
    secondary: [
      {
        datasetType: 'ADAE',
        joinOn: 'patientId',
      },
      {
        datasetType: 'ADCM',
        joinOn: 'patientId',
      },
    ],
  },
  mappingSuggestions: {
    adverseEvents: {
      eventDate: 'AESTDTC',
      eventType: 'AEDECOD',
      patientId: 'USUBJID',
      severity: 'AESEV',
      category: 'AESOC',
    },
    treatments: {
      eventDate: 'CMSTDTC',
      eventType: 'CMTRT',
      patientId: 'USUBJID',
      eventDescription: 'CMDECOD',
    },
    visits: {
      eventDate: 'SVSTDTC',
      eventType: 'VISIT',
      patientId: 'USUBJID',
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
  bar_chart: barChartDataContract,
  scatter_plot: scatterPlotDataContract,
  heatmap: heatmapDataContract,
  kpi_comparison: kpiComparisonDataContract,
  patient_timeline: patientTimelineDataContract,
};

/**
 * Get data contract for a widget type
 */
export function getWidgetDataContract(widgetType: string): DataContract | undefined {
  return widgetDataContracts[widgetType as keyof typeof widgetDataContracts];
}