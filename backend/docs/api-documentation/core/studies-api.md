# Studies API Documentation

## Overview
The Studies API manages clinical trials and research studies within the platform. It provides comprehensive functionality for study setup, configuration, participant management, and protocol tracking while ensuring compliance with clinical trial regulations.

## Business Purpose

### Why This API Exists
1. **Clinical Trial Management**: Central hub for managing all aspects of clinical studies
2. **Protocol Compliance**: Ensures studies follow approved protocols and regulations
3. **Multi-site Coordination**: Enables coordination across multiple study sites
4. **Data Standardization**: Enforces CDISC standards (SDTM, ADaM) for data collection
5. **Regulatory Requirements**: Meets FDA, EMA, and other regulatory body requirements

### Key Business Benefits
- **Streamlined Study Setup**: Rapid study initialization with templates
- **Protocol Adherence**: Automated checks for protocol compliance
- **Real-time Monitoring**: Live study progress tracking
- **Cost Management**: Budget tracking per study
- **Risk Mitigation**: Early identification of study issues

## API Endpoints

### 1. List Studies
```http
GET /api/v1/studies
```

**Purpose**: Retrieve studies accessible to the current user with filtering and pagination.

**Business Need**:
- Study coordinators need to see all their active studies
- Monitors need to track study progress
- Executives need study portfolio overview
- Data managers need to identify studies requiring attention

**Query Parameters**:
- `org_id`: Filter by organization
- `status`: Filter by study status (planning, active, completed, terminated)
- `phase`: Filter by clinical phase (I, II, III, IV)
- `therapeutic_area`: Filter by therapeutic area
- `search`: Search in study name or protocol number

**Response Example**:
```json
{
  "items": [
    {
      "id": "750e8400-e29b-41d4-a716-446655440001",
      "protocol_number": "PRO-2024-001",
      "name": "A Phase III Study of Drug X in Diabetes",
      "short_name": "DIABETES-X-P3",
      "phase": "III",
      "status": "active",
      "therapeutic_area": "Endocrinology",
      "indication": "Type 2 Diabetes Mellitus",
      "org_id": "550e8400-e29b-41d4-a716-446655440000",
      "sponsor": "Pharma Corp International",
      "start_date": "2024-03-01",
      "estimated_completion": "2026-09-01",
      "enrollment": {
        "target": 500,
        "actual": 342,
        "percentage": 68.4
      },
      "sites": {
        "planned": 25,
        "activated": 22,
        "enrolling": 20
      },
      "configuration": {
        "data_standards": "CDISC SDTM 3.4",
        "ePRO_enabled": true,
        "central_lab": true,
        "adaptive_design": false
      }
    }
  ],
  "total": 45,
  "page": 1,
  "size": 20
}
```

### 2. Create Study
```http
POST /api/v1/studies
```

**Purpose**: Initialize a new clinical study with all required regulatory information.

**Business Need**:
- Protocol approved, need to operationalize study
- Set up study infrastructure before first patient in
- Define study parameters for all sites
- Establish data collection standards

**Request Body**:
```json
{
  "protocol_number": "PRO-2024-002",
  "name": "A Randomized, Double-Blind, Placebo-Controlled Study of Drug Y",
  "short_name": "DRUG-Y-P2",
  "phase": "II",
  "study_type": "Interventional",
  "therapeutic_area": "Oncology",
  "indication": "Non-Small Cell Lung Cancer",
  "design": {
    "allocation": "Randomized",
    "intervention_model": "Parallel Assignment",
    "masking": "Double (Participant, Investigator)",
    "primary_purpose": "Treatment"
  },
  "enrollment_target": 200,
  "duration": {
    "screening_days": 28,
    "treatment_weeks": 24,
    "followup_weeks": 52
  },
  "inclusion_criteria": [
    "Age 18-75 years",
    "Confirmed NSCLC diagnosis",
    "ECOG performance status 0-1"
  ],
  "exclusion_criteria": [
    "Prior systemic therapy for NSCLC",
    "Active brain metastases",
    "Severe renal impairment"
  ],
  "endpoints": {
    "primary": "Progression-free survival at 6 months",
    "secondary": [
      "Overall response rate",
      "Overall survival",
      "Quality of life scores"
    ]
  },
  "configuration": {
    "data_standards": "CDISC SDTM 3.4",
    "lab_vendor": "Central Lab Corp",
    "imaging_vendor": "Imaging CRO Inc",
    "randomization_system": "IWRS Pro",
    "eCRF_system": "ClinicalOne"
  }
}
```

### 3. Get Study Details
```http
GET /api/v1/studies/{study_id}
```

**Purpose**: Retrieve comprehensive study information including protocol details, enrollment status, and configuration.

**Business Need**:
- Study teams need complete study information
- Monitors need to review study setup
- Auditors need to verify study configuration
- Regulators need to inspect study details

### 4. Update Study
```http
PUT /api/v1/studies/{study_id}
```

**Purpose**: Update study information following protocol amendments or operational changes.

**Business Need**:
- Protocol amendments require study updates
- Enrollment target adjustments
- Timeline modifications
- Site additions or closures
- Configuration changes

**Validation Rules**:
- Cannot change protocol number after first patient enrolled
- Status changes follow valid transitions
- Protocol amendments require version tracking
- Critical changes require electronic signatures

### 5. Delete Study
```http
DELETE /api/v1/studies/{study_id}
```

**Purpose**: Archive study (soft delete only).

**Business Need**:
- Study termination
- Cancelled studies
- Compliance with data retention policies

**Note**: Studies are never hard deleted. Data retained per regulatory requirements (typically 15-25 years).

### 6. Get Study Users
```http
GET /api/v1/studies/{study_id}/users
```

**Purpose**: List all users with access to the study and their roles.

**Business Need**:
- Access control management
- Study team directory
- Communication planning
- Training tracking
- Audit of study access

**Response Includes**:
- User details
- Study role (PI, Sub-I, CRC, Monitor, Data Manager)
- Site affiliation
- Access permissions
- Training status
- Last access date

### 7. Add User to Study
```http
POST /api/v1/studies/{study_id}/users
```

**Purpose**: Grant user access to study with specific role and permissions.

**Business Need**:
- Onboard new study team members
- Assign site personnel
- Grant monitor access
- Add data reviewers

**Requirements**:
- User must complete required training
- Role-appropriate credentials verified
- Site authorization (if site-specific)
- Delegation log updated

### 8. Get Study Configuration
```http
GET /api/v1/studies/{study_id}/configuration
```

**Purpose**: Retrieve study configuration including dashboard widgets, data sources, and pipeline settings.

**Business Need**:
- View current study setup
- Dashboard customization settings
- Data pipeline configuration
- Integration settings review

**Response Example**:
```json
{
  "config": {
    "display_settings": {
      "theme": "clinical-blue",
      "logo_position": "top-left",
      "show_protocol_number": true
    },
    "data_standards": {
      "sdtm_version": "3.4",
      "adam_version": "1.3",
      "terminology_version": "2023-09-29"
    }
  },
  "pipeline_config": {
    "refresh_schedule": "0 2 * * *",
    "data_sources": ["rave", "central-lab", "imaging"],
    "transformation_steps": ["sdtm", "adam", "custom"],
    "validation_enabled": true
  },
  "dashboard_config": {
    "default_view": "enrollment-overview",
    "widgets": [
      {
        "id": "enrollment-chart",
        "type": "line-chart",
        "position": {"x": 0, "y": 0, "w": 6, "h": 4},
        "data_source": "enrollment_metrics"
      }
    ],
    "refresh_interval": 300
  },
  "updated_at": "2024-03-15T10:30:00Z"
}
```

### 9. Update Study Configuration
```http
PUT /api/v1/studies/{study_id}/configuration
```

**Purpose**: Update study configuration including dashboard widgets, data sources, and pipeline settings.

**Business Need**:
- Customize study dashboards
- Configure data pipeline settings
- Update integration parameters
- Modify display preferences

**Request Body**:
```json
{
  "config": {
    "display_settings": {
      "theme": "clinical-dark",
      "show_enrollment_target": true
    }
  },
  "pipeline_config": {
    "refresh_schedule": "0 */6 * * *",
    "notification_email": "study-team@example.com"
  },
  "dashboard_config": {
    "widgets": [
      {
        "id": "safety-metrics",
        "type": "metric-card",
        "position": {"x": 6, "y": 0, "w": 3, "h": 2},
        "data_source": "adverse_events",
        "config": {
          "metric": "serious_ae_count",
          "threshold": 5,
          "alert_on_exceed": true
        }
      }
    ]
  }
}
```

**Validation Rules**:
- Widget positions must not overlap
- Data sources must exist and be accessible
- Refresh schedules must be valid cron expressions
- Configuration changes are audited

### 10. Activate Study
```http
POST /api/v1/studies/{study_id}/activate
```

**Purpose**: Activate a study for data collection and monitoring.

**Business Need**:
- Study ready to start enrollment
- All setup complete
- Regulatory approvals obtained

### 11. Deactivate Study
```http
POST /api/v1/studies/{study_id}/deactivate
```

**Purpose**: Temporarily deactivate a study while preserving all data.

**Business Need**:
- Study on hold
- Enrollment pause
- Regulatory review

## Compliance Features

### Good Clinical Practice (GCP) Compliance
- **Protocol Adherence**: All study parameters match approved protocol
- **Version Control**: Protocol amendments tracked with full history
- **Delegation Log**: Automated tracking of study role assignments
- **Training Records**: Integrated with training management system

### 21 CFR Part 11 Compliance
- **Audit Trail**: Complete history of all study changes
- **Electronic Signatures**: Required for critical study updates
- **Access Control**: Role-based permissions per study
- **Data Integrity**: Validation of all study parameters

### ICH E6(R2) Compliance
- **Risk-Based Monitoring**: Risk indicators tracked
- **Essential Documents**: Links to eTMF system
- **Protocol Deviations**: Tracking and reporting system
- **Quality Management**: Integrated quality metrics

## Data Standards

### CDISC Compliance
- **SDTM**: Study configuration defines SDTM mapping
- **ADaM**: Analysis dataset specifications
- **Define-XML**: Metadata generation support
- **Controlled Terminology**: CDISC CT validation

### Study Data Flow
```
Protocol → Study Configuration → Data Collection → SDTM → ADaM → Analysis
```

## Security Considerations

### Access Control Hierarchy
1. **Organization Admin**: Full access to all organization studies
2. **Study Director**: Full access to specific study
3. **Principal Investigator**: Site-specific full access
4. **Study Coordinator**: Operational access
5. **Monitor**: Read access with specific monitoring permissions
6. **Data Manager**: Data access without PHI

### Data Protection
- **Blinding**: Maintains treatment assignment blinding
- **PHI Protection**: Personal data encrypted and access-controlled
- **Site Isolation**: Multi-site studies maintain site data separation
- **Export Control**: Data export requires special permissions

## Performance Considerations

### Scalability
- Supports studies with 1000+ sites
- Handles 100,000+ subjects per study
- Real-time enrollment tracking
- Efficient query across millions of data points

### Caching Strategy
- Study list cached per user (5 minutes)
- Study details cached (15 minutes)
- Enrollment statistics cached (1 hour)
- Cache invalidated on updates

## Integration Points

### Clinical Systems
1. **CTMS**: Clinical Trial Management System integration
2. **EDC**: Electronic Data Capture system
3. **IWRS/RTSM**: Randomization system
4. **eTMF**: Electronic Trial Master File
5. **Safety Database**: Adverse event reporting

### Internal APIs
1. **Organizations API**: Study belongs to organization
2. **Sites API**: Study conducted at sites
3. **Users API**: Study team management
4. **Data Pipeline API**: Study data processing
5. **Reports API**: Study progress reports

## Monitoring & Alerts

### Key Metrics
- Enrollment rate vs. target
- Site activation timeline
- Protocol deviation rate
- Data entry lag time
- Query resolution time

### Automated Alerts
- Enrollment below projected rate
- Site not screening for 30 days
- High protocol deviation rate
- Approaching study milestones
- Budget utilization warnings

## Error Handling

### Study-Specific Error Codes
- `STU001`: Study not found
- `STU002`: Protocol number already exists
- `STU003`: Invalid study phase
- `STU004`: Cannot modify locked study
- `STU005`: User lacks study access
- `STU006`: Invalid protocol amendment
- `STU007`: Study has active subjects (cannot terminate)

## Best Practices

### Study Setup
1. Use study templates for common protocols
2. Validate all regulatory requirements before activation
3. Ensure all systems integrated before first patient in
4. Complete user training before granting access

### Ongoing Management
1. Regular review of study metrics
2. Proactive monitoring of enrollment
3. Timely protocol amendment implementation
4. Continuous data quality monitoring

## Change Log

### Version 1.0 (January 2025)
- Initial implementation
- Full CDISC compliance
- Multi-site support
- GCP compliance features

### Planned Enhancements
- Machine learning for enrollment prediction
- Automated protocol deviation detection
- Risk-based monitoring algorithms
- Natural language protocol parsing

---

*Last Updated: January 2025*  
*API Version: 1.0*  
*Compliance: 21 CFR Part 11, ICH-GCP, CDISC Standards*