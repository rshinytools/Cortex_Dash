// ABOUTME: Mock data for transformation-related tests
// ABOUTME: Provides consistent test data for transformation components

export const mockStudy = {
  id: 'test-study-id',
  name: 'Test Study',
  protocol_number: 'TEST-001',
  phase: 'Phase III',
  therapeutic_area: 'Oncology',
  indication: 'Test Indication',
  sponsor_name: 'Test Sponsor',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z'
};

export const mockTransformations = [
  {
    id: 'trans-1',
    study_id: 'test-study-id',
    name: 'Demographics Analysis',
    description: 'Transform demographics data for analysis',
    script_content: "df['age_group'] = pd.cut(df['AGE'], bins=[0, 18, 65, 100])",
    input_datasets: ['dm'],
    output_dataset: 'dm_analysis',
    status: 'completed',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    created_by: 'user-1',
    last_run_at: '2024-01-02T00:00:00Z',
    last_run_duration_seconds: 45,
    last_run_records_processed: 1500
  },
  {
    id: 'trans-2',
    study_id: 'test-study-id',
    name: 'Adverse Events Summary',
    description: 'Summarize AE data by severity',
    script_content: "df_summary = df.groupby(['USUBJID', 'AESEV']).size().reset_index(name='count')",
    input_datasets: ['ae'],
    output_dataset: 'ae_summary',
    status: 'draft',
    created_at: '2024-01-02T00:00:00Z',
    updated_at: '2024-01-02T00:00:00Z',
    created_by: 'user-1'
  },
  {
    id: 'trans-3',
    study_id: 'test-study-id',
    name: 'Combined Analysis',
    description: 'Merge demographics with adverse events',
    script_content: "df = pd.merge(dm, ae, on='USUBJID', how='left')",
    input_datasets: ['dm', 'ae'],
    output_dataset: 'combined_analysis',
    status: 'running',
    created_at: '2024-01-03T00:00:00Z',
    updated_at: '2024-01-03T00:00:00Z',
    created_by: 'user-1',
    current_task_id: 'task-123'
  }
];

export const mockDatasets = [
  {
    name: 'dm',
    display_name: 'Demographics',
    description: 'Subject demographics data',
    record_count: 500,
    columns: ['USUBJID', 'AGE', 'SEX', 'RACE', 'COUNTRY'],
    last_updated: '2024-01-01T00:00:00Z'
  },
  {
    name: 'ae',
    display_name: 'Adverse Events',
    description: 'Adverse events data',
    record_count: 3200,
    columns: ['USUBJID', 'AETERM', 'AESEV', 'AESTDTC', 'AEENDTC'],
    last_updated: '2024-01-01T00:00:00Z'
  },
  {
    name: 'lb',
    display_name: 'Laboratory',
    description: 'Laboratory test results',
    record_count: 15000,
    columns: ['USUBJID', 'LBTESTCD', 'LBTEST', 'LBORRES', 'LBORRESU'],
    last_updated: '2024-01-01T00:00:00Z'
  },
  {
    name: 'vs',
    display_name: 'Vital Signs',
    description: 'Vital signs measurements',
    record_count: 8000,
    columns: ['USUBJID', 'VSTESTCD', 'VSTEST', 'VSORRES', 'VSORRESU'],
    last_updated: '2024-01-01T00:00:00Z'
  }
];

export const mockTransformationExecution = {
  pending: {
    state: 'PENDING',
    current: 0,
    total: 100,
    status: 'Waiting to start...'
  },
  progress: {
    state: 'PROGRESS',
    current: 50,
    total: 100,
    status: 'Processing records...'
  },
  success: {
    state: 'SUCCESS',
    current: 100,
    total: 100,
    status: 'Transformation completed successfully',
    result: {
      records_processed: 1500,
      duration_seconds: 45,
      output_path: '/data/studies/test-study-id/transformed/2024-01-01/dm_analysis.parquet'
    }
  },
  failure: {
    state: 'FAILURE',
    current: 75,
    total: 100,
    status: 'Transformation failed',
    error: 'KeyError: Column "INVALID_COL" not found in dataset'
  }
};

export const mockValidationResults = {
  valid: {
    is_valid: true,
    sample_output: {
      columns: ['USUBJID', 'AGE', 'age_group'],
      rows: 100,
      preview: [
        { USUBJID: '001', AGE: 45, age_group: 'Adult' },
        { USUBJID: '002', AGE: 72, age_group: 'Elderly' },
        { USUBJID: '003', AGE: 16, age_group: 'Pediatric' }
      ]
    },
    warnings: []
  },
  invalid: {
    is_valid: false,
    error: 'NameError: name "undefined_variable" is not defined',
    line_number: 3,
    warnings: []
  },
  securityViolation: {
    is_valid: false,
    error: 'Security violation: import statements are not allowed',
    line_number: 1,
    warnings: []
  }
};

export const mockTransformationScripts = {
  demographics: `# Transform demographics data
# Create age groups
df['age_group'] = pd.cut(df['AGE'], 
                         bins=[0, 18, 65, 100], 
                         labels=['Pediatric', 'Adult', 'Elderly'])

# Create BMI calculation
df['BMI'] = df['WEIGHT'] / (df['HEIGHT'] / 100) ** 2

# Flag high-risk subjects
df['high_risk'] = (df['AGE'] > 65) | (df['BMI'] > 30)`,

  adverseEvents: `# Summarize adverse events
# Count AEs by severity
ae_summary = df.groupby(['USUBJID', 'AESEV']).size().reset_index(name='ae_count')

# Identify serious adverse events
df['is_serious'] = df['AESER'] == 'Y'

# Calculate days from first dose to AE
df['days_to_ae'] = (pd.to_datetime(df['AESTDTC']) - pd.to_datetime(df['TRTSTDTC'])).dt.days`,

  labResults: `# Process laboratory results
# Convert to numeric
df['result_numeric'] = pd.to_numeric(df['LBORRES'], errors='coerce')

# Flag abnormal results
df['abnormal'] = df['LBNRIND'].isin(['HIGH', 'LOW', 'ABNORMAL'])

# Calculate change from baseline
baseline = df[df['VISIT'] == 'BASELINE'][['USUBJID', 'LBTESTCD', 'result_numeric']]
baseline.columns = ['USUBJID', 'LBTESTCD', 'baseline_value']
df = pd.merge(df, baseline, on=['USUBJID', 'LBTESTCD'], how='left')
df['change_from_baseline'] = df['result_numeric'] - df['baseline_value']`
};

export const mockApiErrors = {
  unauthorized: {
    response: {
      status: 401,
      data: { detail: 'Not authenticated' }
    }
  },
  forbidden: {
    response: {
      status: 403,
      data: { detail: 'Not enough permissions' }
    }
  },
  notFound: {
    response: {
      status: 404,
      data: { detail: 'Transformation not found' }
    }
  },
  validation: {
    response: {
      status: 422,
      data: {
        detail: [
          {
            loc: ['body', 'script_content'],
            msg: 'Script cannot be empty',
            type: 'value_error'
          }
        ]
      }
    }
  },
  serverError: {
    response: {
      status: 500,
      data: { detail: 'Internal server error' }
    }
  }
};