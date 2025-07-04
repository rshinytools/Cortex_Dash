# Pipelines API Documentation

## Overview
The Pipelines API orchestrates automated data processing workflows for clinical trial data. It manages the flow of data from source systems through transformations to final analytical datasets, ensuring data quality, compliance, and reproducibility throughout the clinical trial lifecycle.

## Business Purpose

### Why This API Exists
1. **Automation**: Eliminate manual data processing errors and reduce processing time
2. **Standardization**: Ensure consistent application of CDISC standards (SDTM/ADaM)
3. **Reproducibility**: Guarantee that data transformations can be re-executed with identical results
4. **Compliance**: Maintain audit trail of all data transformations for regulatory review
5. **Efficiency**: Process large volumes of clinical data in parallel

### Key Business Benefits
- **Time Savings**: Reduce data processing time from days to hours
- **Quality Improvement**: Automated validation catches errors early
- **Cost Reduction**: Less manual effort required for data preparation
- **Regulatory Readiness**: Complete documentation of data lineage
- **Scalability**: Handle multiple studies and data sources simultaneously

## API Endpoints

### 1. List Pipelines
```http
GET /api/v1/pipelines
```

**Purpose**: Retrieve all data pipelines with filtering and pagination support.

**Business Need**:
- Data managers need to monitor all active pipelines
- Study teams need to track their data processing status
- QC teams need to identify pipelines requiring review
- Administrators need to manage system resources

**Query Parameters**:
- `study_id`: Filter by study
- `status`: active, paused, completed, failed
- `type`: sdtm_mapping, adam_derivation, custom
- `owner`: Filter by pipeline creator
- `search`: Search in pipeline name or description

**Response Example**:
```json
{
  "items": [
    {
      "id": "pipe_8f7g6h5j4k3l2m1n",
      "name": "STUDY001 SDTM Mapping Pipeline",
      "description": "Maps raw EDC data to SDTM domains for Protocol STUDY001",
      "type": "sdtm_mapping",
      "study_id": "750e8400-e29b-41d4-a716-446655440001",
      "status": "active",
      "schedule": {
        "type": "cron",
        "expression": "0 2 * * *",
        "timezone": "UTC",
        "next_run": "2025-01-22T02:00:00Z"
      },
      "configuration": {
        "source_system": "EDC_System_A",
        "target_version": "SDTM 3.4",
        "validation_level": "strict",
        "error_handling": "quarantine"
      },
      "performance": {
        "avg_runtime_minutes": 45,
        "last_runtime_minutes": 42,
        "records_per_minute": 10000,
        "success_rate": 99.8
      },
      "last_execution": {
        "id": "exec_123456",
        "status": "completed",
        "started_at": "2025-01-21T02:00:00Z",
        "completed_at": "2025-01-21T02:42:00Z",
        "records_processed": 420000,
        "errors": 0,
        "warnings": 12
      }
    }
  ],
  "total": 67,
  "page": 1,
  "size": 20
}
```

### 2. Create Pipeline
```http
POST /api/v1/pipelines
```

**Purpose**: Create a new automated data processing pipeline.

**Business Need**:
- Set up data flow for new study
- Create custom transformations for specific analyses
- Automate recurring data preparation tasks
- Establish data quality checks

**Request Body**:
```json
{
  "name": "STUDY002 ADaM Dataset Generation",
  "description": "Generate ADaM datasets from SDTM for primary efficacy analysis",
  "type": "adam_derivation",
  "study_id": "750e8400-e29b-41d4-a716-446655440002",
  "steps": [
    {
      "name": "Load SDTM Datasets",
      "type": "data_source",
      "config": {
        "source_type": "sdtm_library",
        "datasets": ["DM", "AE", "LB", "VS", "EX"]
      }
    },
    {
      "name": "Create ADSL",
      "type": "transformation",
      "config": {
        "script": "transformations/create_adsl.sas",
        "inputs": ["DM", "EX"],
        "output": "ADSL",
        "parameters": {
          "cutoff_date": "2025-01-15",
          "population_flags": ["ITT", "PP", "SAFETY"]
        }
      }
    },
    {
      "name": "Create ADAE",
      "type": "transformation",
      "config": {
        "script": "transformations/create_adae.sas",
        "inputs": ["AE", "ADSL"],
        "output": "ADAE",
        "parameters": {
          "coding_dictionary": "MedDRA 27.0"
        }
      }
    },
    {
      "name": "Validate ADaM",
      "type": "validation",
      "config": {
        "validator": "pinnacle21",
        "standard": "ADaM 2.1",
        "severity_threshold": "warning"
      }
    },
    {
      "name": "Export to Analysis Environment",
      "type": "data_sink",
      "config": {
        "destination": "analysis_repository",
        "format": "sas7bdat",
        "compression": true
      }
    }
  ],
  "schedule": {
    "type": "manual",
    "auto_retry": true,
    "max_retries": 3
  },
  "notifications": {
    "on_success": ["data.manager@sponsor.com"],
    "on_failure": ["data.manager@sponsor.com", "it.support@sponsor.com"],
    "on_warning": ["data.manager@sponsor.com"]
  },
  "quality_checks": {
    "pre_execution": [
      "verify_source_data_completeness",
      "check_sdtm_compliance"
    ],
    "post_execution": [
      "validate_record_counts",
      "check_derived_variables"
    ]
  }
}
```

### 3. Get Pipeline Details
```http
GET /api/v1/pipelines/{pipeline_id}
```

**Purpose**: Retrieve comprehensive pipeline configuration and execution history.

**Business Need**:
- Review pipeline configuration before execution
- Debug failed pipeline runs
- Audit data transformation logic
- Optimize pipeline performance

### 4. Update Pipeline
```http
PUT /api/v1/pipelines/{pipeline_id}
```

**Purpose**: Modify pipeline configuration or steps.

**Business Need**:
- Add new transformation steps
- Update scheduling
- Modify data sources
- Change validation rules
- Update notification recipients

**Validation Rules**:
- Cannot modify running pipeline
- Changes require testing before activation
- Version control maintains history
- Critical changes require approval

### 5. Delete Pipeline
```http
DELETE /api/v1/pipelines/{pipeline_id}
```

**Purpose**: Deactivate pipeline (soft delete).

**Business Need**:
- Study completion
- Replace with updated version
- Temporary suspension
- Resource management

### 6. Execute Pipeline
```http
POST /api/v1/pipelines/{pipeline_id}/execute
```

**Purpose**: Manually trigger pipeline execution.

**Business Need**:
- On-demand data processing
- Reprocess after data corrections
- Testing and validation
- Emergency data updates

**Request Body**:
```json
{
  "execution_mode": "full",
  "parameters": {
    "cutoff_date": "2025-01-21",
    "force_reprocess": false,
    "skip_validation": false
  },
  "notification_override": {
    "additional_recipients": ["clinical.lead@sponsor.com"]
  }
}
```

### 7. Get Pipeline History
```http
GET /api/v1/pipelines/{pipeline_id}/history
```

**Purpose**: Retrieve execution history with detailed metrics.

**Business Need**:
- Monitor pipeline reliability
- Identify performance trends
- Troubleshoot recurring issues
- Audit data processing

**Response Includes**:
- Execution timestamps
- Duration and performance metrics
- Record counts
- Error and warning details
- Resource utilization
- Data lineage information

## Pipeline Components

### Step Types

#### 1. Data Source
```json
{
  "type": "data_source",
  "supported_sources": [
    "EDC Systems",
    "Laboratory Systems",
    "ePRO/eCOA",
    "External Data Transfers",
    "Previous Pipeline Output"
  ]
}
```

#### 2. Transformation
```json
{
  "type": "transformation",
  "supported_engines": [
    "SAS Programs",
    "Python Scripts",
    "R Scripts",
    "SQL Queries",
    "Built-in Transformations"
  ]
}
```

#### 3. Validation
```json
{
  "type": "validation",
  "validators": [
    "Pinnacle 21",
    "Custom Rules",
    "Data Integrity Checks",
    "Business Logic Validation"
  ]
}
```

#### 4. Data Sink
```json
{
  "type": "data_sink",
  "destinations": [
    "Data Warehouse",
    "Analysis Datasets",
    "Export Files",
    "Reporting Systems"
  ]
}
```

## Execution Engine

### Processing Modes
1. **Full Processing**: Complete reprocessing of all data
2. **Incremental**: Process only new/changed records
3. **Delta**: Process specific date ranges
4. **Replay**: Re-execute from specific point

### Error Handling
```json
{
  "strategies": {
    "continue": "Log error and continue processing",
    "quarantine": "Move error records to quarantine",
    "halt": "Stop pipeline execution",
    "rollback": "Revert all changes"
  }
}
```

### Performance Optimization
- **Parallel Processing**: Multiple steps run concurrently
- **Resource Allocation**: Dynamic compute resource assignment
- **Caching**: Intermediate results cached
- **Checkpointing**: Resume from failure point

## Compliance Features

### 21 CFR Part 11
- **Audit Trail**: Every execution logged with full details
- **Version Control**: All pipeline changes tracked
- **Electronic Signatures**: Required for validated pipelines
- **Access Control**: Role-based pipeline management

### Data Integrity
- **Checksums**: Input/output data verification
- **Lineage Tracking**: Complete data transformation path
- **Reproducibility**: Identical results guaranteed
- **Validation Reports**: Automated compliance checking

### CDISC Compliance
- **SDTM Mapping**: Built-in SDTM 3.4 compliance
- **ADaM Derivation**: ADaM 2.1 standard support
- **Define-XML**: Automatic generation
- **Controlled Terminology**: CDISC CT validation

## Monitoring & Alerting

### Real-time Monitoring
```json
{
  "metrics": {
    "execution_status": "Running step 3 of 5",
    "progress_percentage": 60,
    "records_processed": 250000,
    "estimated_completion": "2025-01-21T03:15:00Z",
    "resource_usage": {
      "cpu_percent": 75,
      "memory_gb": 12.5,
      "disk_io_mbps": 150
    }
  }
}
```

### Alert Conditions
- Pipeline failure
- Execution time exceeds threshold
- Error rate above limit
- Resource constraints
- Data quality issues

### Notification Channels
- Email notifications
- SMS alerts
- Webhook integration
- Dashboard updates
- Incident management system

## Security Considerations

### Access Control
- **Pipeline Creation**: Data Manager role required
- **Execution**: Study team member
- **Configuration**: Pipeline owner or admin
- **Viewing**: Read access to study

### Data Security
- **Encryption**: Data encrypted in transit and at rest
- **Isolation**: Pipeline execution in isolated environment
- **Credentials**: Secure credential storage
- **Network**: VPN/private network requirements

## Integration Points

### Source Systems
1. **EDC Systems**: RESTful APIs, SFTP
2. **Laboratory**: HL7, custom formats
3. **Imaging**: DICOM gateways
4. **External Partners**: Secure file transfer

### Downstream Systems
1. **Statistical Analysis**: SAS, R environments
2. **Reporting**: Business intelligence tools
3. **Data Warehouse**: Clinical data repository
4. **Regulatory Submission**: eCTD packages

## Error Handling

### Pipeline Error Codes
- `PIP001`: Pipeline not found
- `PIP002`: Invalid configuration
- `PIP003`: Source system unavailable
- `PIP004`: Transformation error
- `PIP005`: Validation failure
- `PIP006`: Insufficient resources
- `PIP007`: Schedule conflict
- `PIP008`: Permission denied

### Recovery Procedures
1. Automatic retry with backoff
2. Partial result preservation
3. Manual intervention options
4. Rollback capabilities
5. Alternative processing paths

## Best Practices

### Pipeline Design
1. Modular step design for reusability
2. Comprehensive error handling
3. Performance optimization
4. Clear documentation
5. Version control integration

### Operations
1. Regular performance reviews
2. Proactive monitoring
3. Scheduled maintenance windows
4. Disaster recovery planning
5. Continuous improvement

## Change Log

### Version 1.0 (January 2025)
- Initial implementation
- Core pipeline functionality
- SDTM/ADaM support
- Basic scheduling

### Planned Enhancements
- Machine learning optimizations
- Real-time streaming support
- Advanced orchestration
- Self-healing pipelines
- Cost optimization features

---

*Last Updated: January 2025*  
*API Version: 1.0*  
*Compliance: 21 CFR Part 11, CDISC Standards*