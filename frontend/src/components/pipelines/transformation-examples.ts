// ABOUTME: Transformation examples and templates for the data transformation UI
// ABOUTME: Provides ready-to-use code snippets for common clinical data transformations

export interface TransformationExample {
  id: string;
  name: string;
  description: string;
  category: 'basic' | 'analysis' | 'aggregation' | 'quality' | 'advanced';
  requiredDatasets: string[];
  outputDataset: string;
  code: string;
  explanation?: string;
}

export const transformationExamples: TransformationExample[] = [
  // Basic Transformations
  {
    id: 'age-groups',
    name: 'Age Categorization',
    description: 'Create age groups from continuous age values',
    category: 'basic',
    requiredDatasets: ['dm'],
    outputDataset: 'dm_categorized',
    code: `# Categorize subjects by age
df = dm.copy()

# Create age groups
df['age_group'] = pd.cut(df['AGE'], 
                         bins=[0, 18, 45, 65, 100], 
                         labels=['Pediatric', 'Young Adult', 'Middle Age', 'Elderly'])

# Create binary flags for special populations
df['elderly_flag'] = (df['AGE'] >= 65).astype(int)
df['pediatric_flag'] = (df['AGE'] < 18).astype(int)`,
    explanation: 'This creates categorical age groups and binary flags for analysis.'
  },
  
  {
    id: 'bmi-calculation',
    name: 'BMI Calculation',
    description: 'Calculate BMI and obesity categories',
    category: 'basic',
    requiredDatasets: ['dm'],
    outputDataset: 'dm_bmi',
    code: `# Calculate BMI from height and weight
df = dm.copy()

# Ensure numeric values
df['WEIGHT'] = pd.to_numeric(df['WEIGHT'], errors='coerce')
df['HEIGHT'] = pd.to_numeric(df['HEIGHT'], errors='coerce')

# Calculate BMI (weight in kg, height in cm)
df['BMI'] = df['WEIGHT'] / (df['HEIGHT'] / 100) ** 2

# Categorize BMI
df['BMI_category'] = pd.cut(df['BMI'], 
                            bins=[0, 18.5, 25, 30, 100], 
                            labels=['Underweight', 'Normal', 'Overweight', 'Obese'])

# Round BMI to 1 decimal place
df['BMI'] = df['BMI'].round(1)`,
    explanation: 'Calculates BMI and assigns WHO categories for body weight classification.'
  },

  // Analysis Datasets
  {
    id: 'adsl-basic',
    name: 'Basic ADSL Creation',
    description: 'Create a basic subject-level analysis dataset',
    category: 'analysis',
    requiredDatasets: ['dm', 'ae'],
    outputDataset: 'adsl',
    code: `# Create ADSL (Subject-Level Analysis Dataset)
adsl = dm.copy()

# Add safety population flag (all subjects who received treatment)
adsl['SAFFL'] = 'Y'

# Add ITT population flag (all randomized subjects)
adsl['ITTFL'] = 'Y'

# Add adverse event flags from AE data
ae_subjects = ae['USUBJID'].unique()
adsl['AEFL'] = adsl['USUBJID'].isin(ae_subjects).map({True: 'Y', False: 'N'})

# Serious adverse events
sae_subjects = ae[ae['AESER'] == 'Y']['USUBJID'].unique()
adsl['SAEFL'] = adsl['USUBJID'].isin(sae_subjects).map({True: 'Y', False: 'N'})

# Study completion flag (example logic)
adsl['COMPFL'] = 'Y'  # Would be based on disposition data

# Calculate age at enrollment
adsl['AGE'] = pd.to_numeric(adsl['AGE'], errors='coerce')

df = adsl`,
    explanation: 'Creates a subject-level dataset with standard analysis flags.'
  },

  {
    id: 'adae-basic',
    name: 'Basic ADAE Creation',
    description: 'Create adverse event analysis dataset',
    category: 'analysis',
    requiredDatasets: ['ae', 'dm'],
    outputDataset: 'adae',
    code: `# Create ADAE (Adverse Event Analysis Dataset)
adae = ae.copy()

# Merge with demographics for baseline characteristics
adae = pd.merge(adae, dm[['USUBJID', 'AGE', 'SEX', 'RACE', 'COUNTRY']], 
                on='USUBJID', how='left')

# Convert dates
adae['AESTDT'] = pd.to_datetime(adae['AESTDTC'], errors='coerce')
adae['AEENDT'] = pd.to_datetime(adae['AEENDTC'], errors='coerce')

# Calculate duration
adae['AEDUR'] = (adae['AEENDT'] - adae['AESTDT']).dt.days + 1

# Standardize severity to numeric
severity_map = {'MILD': 1, 'MODERATE': 2, 'SEVERE': 3}
adae['AESEVN'] = adae['AESEV'].map(severity_map)

# Treatment emergent flag (simplified - would normally check against first dose)
adae['TRTEMFL'] = 'Y'

# Analysis flags
adae['ANL01FL'] = 'Y'  # Include in primary analysis

df = adae`,
    explanation: 'Creates an analysis-ready adverse event dataset with derived variables.'
  },

  // Aggregations
  {
    id: 'ae-summary',
    name: 'AE Summary by Severity',
    description: 'Summarize adverse events by severity and body system',
    category: 'aggregation',
    requiredDatasets: ['ae'],
    outputDataset: 'ae_summary',
    code: `# Summarize adverse events
# Count by severity
severity_counts = ae.groupby(['AESEV']).size().reset_index(name='count')
severity_counts['percentage'] = (severity_counts['count'] / len(ae)) * 100

# Count by preferred term (top 10)
top_ae = ae['AEDECOD'].value_counts().head(10).reset_index()
top_ae.columns = ['AEDECOD', 'count']

# Count by subject and severity
subj_severity = ae.groupby(['USUBJID', 'AESEV']).size().reset_index(name='ae_count')

# Pivot to wide format
df = subj_severity.pivot(index='USUBJID', columns='AESEV', values='ae_count').fillna(0)
df = df.reset_index()

# Add total AE count
df['TOTAL_AE'] = df.select_dtypes(include='number').sum(axis=1)`,
    explanation: 'Creates summary statistics for adverse events analysis.'
  },

  {
    id: 'lab-summary',
    name: 'Laboratory Summary Statistics',
    description: 'Calculate summary statistics for lab parameters',
    category: 'aggregation',
    requiredDatasets: ['lb'],
    outputDataset: 'lb_summary',
    code: `# Summarize laboratory results by visit and test
# Convert to numeric
lb['LBSTRESN'] = pd.to_numeric(lb['LBORRES'], errors='coerce')

# Calculate summary statistics
summary = lb.groupby(['VISIT', 'LBTESTCD', 'LBTEST'])['LBSTRESN'].agg([
    'count',
    'mean',
    'std',
    'min',
    'max',
    ('q1', lambda x: x.quantile(0.25)),
    ('median', lambda x: x.quantile(0.5)),
    ('q3', lambda x: x.quantile(0.75))
]).reset_index()

# Round numeric columns
numeric_cols = ['mean', 'std', 'min', 'max', 'q1', 'median', 'q3']
summary[numeric_cols] = summary[numeric_cols].round(2)

# Add abnormal value counts
abnormal = lb[lb['LBNRIND'].isin(['HIGH', 'LOW', 'ABNORMAL'])]
abnormal_counts = abnormal.groupby(['VISIT', 'LBTESTCD']).size().reset_index(name='n_abnormal')

df = pd.merge(summary, abnormal_counts, on=['VISIT', 'LBTESTCD'], how='left')
df['n_abnormal'] = df['n_abnormal'].fillna(0).astype(int)`,
    explanation: 'Generates comprehensive summary statistics for laboratory data.'
  },

  // Data Quality
  {
    id: 'missing-data',
    name: 'Missing Data Report',
    description: 'Identify missing values across key variables',
    category: 'quality',
    requiredDatasets: ['dm'],
    outputDataset: 'dm_missing',
    code: `# Create missing data report
df = dm.copy()

# Count missing values per column
missing_counts = df.isnull().sum().reset_index()
missing_counts.columns = ['variable', 'missing_count']
missing_counts['total_count'] = len(df)
missing_counts['missing_percent'] = (missing_counts['missing_count'] / missing_counts['total_count']) * 100

# Add completeness flag for each subject
required_vars = ['AGE', 'SEX', 'RACE', 'COUNTRY']
df['n_missing'] = df[required_vars].isnull().sum(axis=1)
df['complete_flag'] = (df['n_missing'] == 0).map({True: 'Y', False: 'N'})

# Create summary
summary = pd.DataFrame({
    'total_subjects': [len(df)],
    'complete_subjects': [len(df[df['complete_flag'] == 'Y'])],
    'incomplete_subjects': [len(df[df['complete_flag'] == 'N'])],
    'completeness_rate': [(len(df[df['complete_flag'] == 'Y']) / len(df)) * 100]
})

# Keep subject-level data
df = df[['USUBJID', 'n_missing', 'complete_flag']]`,
    explanation: 'Identifies data completeness issues for quality control.'
  },

  {
    id: 'outlier-detection',
    name: 'Outlier Detection',
    description: 'Identify potential outliers in continuous variables',
    category: 'quality',
    requiredDatasets: ['vs'],
    outputDataset: 'vs_outliers',
    code: `# Detect outliers in vital signs
vs_numeric = vs.copy()
vs_numeric['VSORRES'] = pd.to_numeric(vs_numeric['VSORRES'], errors='coerce')

# Calculate outliers by test using IQR method
outliers = []

for test in vs_numeric['VSTESTCD'].unique():
    test_data = vs_numeric[vs_numeric['VSTESTCD'] == test]['VSORRES'].dropna()
    
    if len(test_data) > 0:
        q1 = test_data.quantile(0.25)
        q3 = test_data.quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        # Flag outliers
        test_outliers = vs_numeric[
            (vs_numeric['VSTESTCD'] == test) & 
            ((vs_numeric['VSORRES'] < lower_bound) | (vs_numeric['VSORRES'] > upper_bound))
        ].copy()
        
        test_outliers['outlier_type'] = test_outliers.apply(
            lambda x: 'LOW' if x['VSORRES'] < lower_bound else 'HIGH', axis=1
        )
        test_outliers['lower_bound'] = lower_bound
        test_outliers['upper_bound'] = upper_bound
        
        outliers.append(test_outliers)

# Combine all outliers
df = pd.concat(outliers, ignore_index=True) if outliers else pd.DataFrame()

# Add summary columns
if not df.empty:
    df['deviation'] = df.apply(
        lambda x: abs(x['VSORRES'] - x['lower_bound']) if x['outlier_type'] == 'LOW' 
        else abs(x['VSORRES'] - x['upper_bound']), axis=1
    )`,
    explanation: 'Identifies statistical outliers using the IQR method.'
  },

  // Advanced Transformations
  {
    id: 'time-to-event',
    name: 'Time to First AE',
    description: 'Calculate time to first adverse event',
    category: 'advanced',
    requiredDatasets: ['ae', 'dm'],
    outputDataset: 'tte_ae',
    code: `# Calculate time to first adverse event
# Get first AE date per subject
first_ae = ae.copy()
first_ae['AESTDT'] = pd.to_datetime(first_ae['AESTDTC'], errors='coerce')
first_ae = first_ae.groupby('USUBJID')['AESTDT'].min().reset_index()
first_ae.columns = ['USUBJID', 'first_ae_date']

# Merge with demographics
tte = dm[['USUBJID']].copy()
tte = pd.merge(tte, first_ae, on='USUBJID', how='left')

# Calculate days to event (would normally use randomization date)
# Using a placeholder start date for this example
study_start = pd.to_datetime('2024-01-01')
tte['days_to_ae'] = (tte['first_ae_date'] - study_start).dt.days

# Add censoring information
tte['event_flag'] = tte['first_ae_date'].notna().astype(int)
tte['censor_date'] = pd.to_datetime('2024-12-31')  # Study end date
tte['analysis_date'] = tte['first_ae_date'].fillna(tte['censor_date'])
tte['time_to_event'] = (tte['analysis_date'] - study_start).dt.days

# Categorize time to event
tte['tte_category'] = pd.cut(tte['time_to_event'], 
                             bins=[0, 30, 90, 180, 365, 1000],
                             labels=['<30 days', '30-90 days', '90-180 days', 
                                    '180-365 days', '>365 days'])

df = tte`,
    explanation: 'Calculates time-to-event variables for survival analysis.'
  },

  {
    id: 'exposure-summary',
    name: 'Drug Exposure Summary',
    description: 'Calculate drug exposure metrics',
    category: 'advanced',
    requiredDatasets: ['ex'],
    outputDataset: 'ex_summary',
    code: `# Calculate exposure summary metrics
ex_summary = ex.copy()

# Convert dates
ex_summary['EXSTDT'] = pd.to_datetime(ex_summary['EXSTDTC'], errors='coerce')
ex_summary['EXENDT'] = pd.to_datetime(ex_summary['EXENDTC'], errors='coerce')

# Calculate duration for each record
ex_summary['duration_days'] = (ex_summary['EXENDT'] - ex_summary['EXSTDT']).dt.days + 1

# Subject-level summary
subj_summary = ex_summary.groupby('USUBJID').agg({
    'EXSTDT': 'min',  # First dose date
    'EXENDT': 'max',  # Last dose date
    'duration_days': 'sum',  # Total exposure days
    'EXDOSE': ['count', 'sum', 'mean']  # Dose statistics
}).reset_index()

# Flatten column names
subj_summary.columns = ['USUBJID', 'first_dose_date', 'last_dose_date', 
                        'total_days', 'n_doses', 'total_dose', 'avg_dose']

# Calculate overall treatment duration
subj_summary['treatment_duration'] = (
    subj_summary['last_dose_date'] - subj_summary['first_dose_date']
).dt.days + 1

# Calculate compliance (doses given / expected doses)
# Assuming daily dosing
subj_summary['expected_doses'] = subj_summary['treatment_duration']
subj_summary['compliance_pct'] = (
    subj_summary['n_doses'] / subj_summary['expected_doses'] * 100
).round(1)

# Categorize compliance
subj_summary['compliance_cat'] = pd.cut(
    subj_summary['compliance_pct'],
    bins=[0, 80, 95, 100, 200],
    labels=['Poor (<80%)', 'Moderate (80-95%)', 'Good (95-100%)', 'Over-compliant']
)

df = subj_summary`,
    explanation: 'Creates comprehensive drug exposure summary with compliance metrics.'
  },

  {
    id: 'change-from-baseline',
    name: 'Change from Baseline',
    description: 'Calculate change from baseline for lab values',
    category: 'advanced',
    requiredDatasets: ['lb'],
    outputDataset: 'lb_change',
    code: `# Calculate change from baseline for laboratory values
lb_change = lb.copy()

# Convert to numeric
lb_change['LBSTRESN'] = pd.to_numeric(lb_change['LBORRES'], errors='coerce')

# Get baseline values
baseline = lb_change[lb_change['VISIT'] == 'BASELINE'][
    ['USUBJID', 'LBTESTCD', 'LBSTRESN']
].copy()
baseline.columns = ['USUBJID', 'LBTESTCD', 'BASE']

# Merge baseline with all visits
df = pd.merge(lb_change, baseline, on=['USUBJID', 'LBTESTCD'], how='left')

# Calculate changes
df['CHG'] = df['LBSTRESN'] - df['BASE']
df['PCHG'] = (df['CHG'] / df['BASE']) * 100

# Round to reasonable precision
df['CHG'] = df['CHG'].round(2)
df['PCHG'] = df['PCHG'].round(1)

# Flag clinically significant changes (>20% from baseline)
df['clin_sig_flag'] = (abs(df['PCHG']) > 20).map({True: 'Y', False: 'N', pd.NA: ''})

# Categorize direction and magnitude of change
def categorize_change(pchg):
    if pd.isna(pchg):
        return 'No Baseline'
    elif pchg <= -20:
        return 'Large Decrease'
    elif pchg <= -10:
        return 'Moderate Decrease' 
    elif pchg <= -5:
        return 'Small Decrease'
    elif pchg <= 5:
        return 'No Change'
    elif pchg <= 10:
        return 'Small Increase'
    elif pchg <= 20:
        return 'Moderate Increase'
    else:
        return 'Large Increase'

df['change_category'] = df['PCHG'].apply(categorize_change)`,
    explanation: 'Calculates absolute and percentage changes from baseline with clinical flags.'
  }
];

/**
 * Get examples by category
 */
export function getExamplesByCategory(category: TransformationExample['category']): TransformationExample[] {
  return transformationExamples.filter(example => example.category === category);
}

/**
 * Get example by ID
 */
export function getExampleById(id: string): TransformationExample | undefined {
  return transformationExamples.find(example => example.id === id);
}

/**
 * Get examples that can be run with available datasets
 */
export function getApplicableExamples(availableDatasets: string[]): TransformationExample[] {
  return transformationExamples.filter(example => 
    example.requiredDatasets.every(req => availableDatasets.includes(req))
  );
}

/**
 * Example categories with descriptions
 */
export const exampleCategories = {
  basic: {
    name: 'Basic Transformations',
    description: 'Simple calculations and data type conversions'
  },
  analysis: {
    name: 'Analysis Datasets',
    description: 'Create standard analysis datasets (ADSL, ADAE, etc.)'
  },
  aggregation: {
    name: 'Aggregations',
    description: 'Summary statistics and data aggregation'
  },
  quality: {
    name: 'Data Quality',
    description: 'Data validation and quality checks'
  },
  advanced: {
    name: 'Advanced',
    description: 'Complex transformations and derived variables'
  }
};