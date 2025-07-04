# Data Sources API Documentation

## Overview
The Data Sources API manages connections to external clinical data systems, enabling secure and compliant data ingestion from various sources including EDC systems, laboratory systems, imaging platforms, and third-party data providers. It handles authentication, data retrieval scheduling, and connection monitoring.

## Business Purpose

### Why This API Exists
1. **System Integration**: Connect to diverse clinical data sources without custom coding
2. **Data Centralization**: Aggregate data from multiple systems into a unified platform
3. **Security Management**: Centralize credential management and access control
4. **Compliance**: Ensure data transfer meets regulatory requirements
5. **Automation**: Schedule and automate data retrieval from external systems

### Key Business Benefits
- **Reduced Integration Time**: Pre-built connectors for common clinical systems
- **Improved Data Quality**: Automated validation during data transfer
- **Enhanced Security**: Centralized credential management with encryption
- **Real-time Monitoring**: Track data flow and identify issues early
- **Cost Efficiency**: Reduce manual data transfer efforts

## API Endpoints

### 1. List Data Sources
```http
GET /api/v1/data-sources
```

**Purpose**: Retrieve all configured data sources with their current status.

**Business Need**:
- Monitor all active data connections
- Identify failing connections requiring attention
- Plan data integration workflows
- Audit external system access

**Response Example**:
```json
{
  "items": [
    {
      "id": "ds_edc_primary",
      "name": "Primary EDC System",
      "type": "oracle_clinical",
      "category": "edc",
      "study_id": "750e8400-e29b-41d4-a716-446655440001",
      "status": "active",
      "connection_status": {
        "state": "connected",
        "last_successful_connection": "2025-01-21T14:00:00Z",
        "last_sync": "2025-01-21T14:00:00Z",
        "next_scheduled_sync": "2025-01-21T20:00:00Z"
      },
      "configuration": {
        "host": "edc.clinicaltrials.com",
        "port": 443,
        "protocol": "https",
        "api_version": "21.3",
        "authentication_method": "oauth2"
      },
      "data_statistics": {
        "total_records_synced": 1250000,
        "last_sync_records": 5420,
        "average_sync_duration_minutes": 12,
        "data_lag_hours": 6
      },
      "quality_metrics": {
        "success_rate": 99.8,
        "validation_pass_rate": 98.5,
        "average_records_per_minute": 450
      }
    }
  ],
  "total": 23,
  "page": 1,
  "size": 20
}
```

### 2. Create Data Source
```http
POST /api/v1/data-sources
```

**Purpose**: Configure a new external data source connection.

**Business Need**:
- Connect new clinical systems
- Add laboratory data feeds
- Integrate imaging systems
- Set up partner data transfers

**Request Body**:
```json
{
  "name": "Central Laboratory System",
  "type": "lab_system",
  "category": "laboratory",
  "study_id": "750e8400-e29b-41d4-a716-446655440001",
  "connection_config": {
    "type": "sftp",
    "host": "lab.centrallab.com",
    "port": 22,
    "directory": "/clinical_trials/STUDY001/",
    "file_pattern": "*.csv",
    "authentication": {
      "method": "ssh_key",
      "username": "study001_user",
      "ssh_key_id": "key_123456"
    }
  },
  "data_config": {
    "format": "csv",
    "delimiter": ",",
    "encoding": "UTF-8",
    "has_header": true,
    "date_format": "YYYY-MM-DD",
    "mapping_template": "lab_standard_v2"
  },
  "schedule": {
    "type": "cron",
    "expression": "0 */6 * * *",
    "timezone": "UTC"
  },
  "validation_rules": [
    {
      "field": "subject_id",
      "rule": "required",
      "format": "^[A-Z]{3}-\\d{4}$"
    },
    {
      "field": "lab_value",
      "rule": "numeric_range",
      "min": 0,
      "max": 1000
    }
  ],
  "error_handling": {
    "strategy": "quarantine",
    "notification_threshold": 5,
    "retry_attempts": 3,
    "retry_delay_minutes": 15
  }
}
```

### 3. Get Data Source Details
```http
GET /api/v1/data-sources/{source_id}
```

**Purpose**: Retrieve detailed configuration and status of a specific data source.

**Business Need**:
- Troubleshoot connection issues
- Review configuration settings
- Audit data source access
- Monitor performance metrics

### 4. Update Data Source
```http
PUT /api/v1/data-sources/{source_id}
```

**Purpose**: Modify data source configuration or credentials.

**Business Need**:
- Update credentials after rotation
- Modify sync schedules
- Change validation rules
- Update connection parameters

**Security Note**: Credential updates require elevated permissions and are logged for audit.

### 5. Delete Data Source
```http
DELETE /api/v1/data-sources/{source_id}
```

**Purpose**: Deactivate data source connection.

**Business Need**:
- End of study data collection
- Decommission old systems
- Security incident response
- System migration

### 6. Test Connection
```http
POST /api/v1/data-sources/{source_id}/test
```

**Purpose**: Verify data source connectivity and credentials.

**Business Need**:
- Validate configuration before activation
- Troubleshoot connection issues
- Verify after credential updates
- Pre-sync validation

**Response Example**:
```json
{
  "status": "success",
  "connection_test": {
    "connectivity": "passed",
    "authentication": "passed",
    "permissions": "passed",
    "data_access": "passed"
  },
  "response_time_ms": 234,
  "test_timestamp": "2025-01-21T15:30:00Z",
  "sample_data": {
    "available": true,
    "record_count": 10,
    "fields_detected": ["subject_id", "visit_date", "lab_test", "result"]
  },
  "warnings": [
    "SSL certificate expires in 30 days"
  ]
}
```

### 7. Sync Data
```http
POST /api/v1/data-sources/{source_id}/sync
```

**Purpose**: Manually trigger data synchronization.

**Business Need**:
- On-demand data updates
- Emergency data retrieval
- Testing data flow
- Recovery after failures

**Request Body**:
```json
{
  "sync_mode": "incremental",
  "date_range": {
    "start": "2025-01-20",
    "end": "2025-01-21"
  },
  "options": {
    "force_full_validation": true,
    "skip_duplicates": true,
    "priority": "high"
  }
}
```

## Supported Data Source Types

### Clinical Systems
```json
{
  "edc_systems": [
    "Oracle Clinical",
    "Medidata Rave",
    "Veeva Vault",
    "REDCap",
    "OpenClinica"
  ],
  "connectivity": [
    "REST API",
    "SOAP Web Services",
    "Direct Database",
    "File Export"
  ]
}
```

### Laboratory Systems
```json
{
  "lab_systems": [
    "LabCorp",
    "Quest Diagnostics",
    "Covance",
    "Local Hospital Labs"
  ],
  "formats": [
    "HL7",
    "CSV/TSV",
    "XML",
    "Custom Formats"
  ]
}
```

### Imaging Systems
```json
{
  "imaging_platforms": [
    "PACS Systems",
    "Cloud Imaging",
    "DICOM Servers"
  ],
  "protocols": [
    "DICOM",
    "DICOMweb",
    "FHIR Imaging"
  ]
}
```

### Other Sources
- Electronic Patient Reported Outcomes (ePRO)
- Wearable Device Data
- External Partner Systems
- Public Health Databases

## Security & Compliance

### Credential Management
- **Encryption**: All credentials encrypted at rest (AES-256)
- **Key Rotation**: Automated credential rotation support
- **Access Control**: Role-based access to credentials
- **Audit Trail**: All credential access logged

### Data Transfer Security
- **TLS/SSL**: Minimum TLS 1.2 for all connections
- **VPN Support**: Site-to-site VPN connections
- **IP Whitelisting**: Source IP restrictions
- **Data Encryption**: In-transit encryption mandatory

### Compliance Features
- **21 CFR Part 11**: Complete audit trail of data transfers
- **HIPAA**: PHI handling compliance
- **GDPR**: Data minimization and purpose limitation
- **Chain of Custody**: Full data lineage tracking

## Connection Monitoring

### Health Checks
```json
{
  "monitoring_intervals": {
    "critical_sources": "5 minutes",
    "standard_sources": "30 minutes",
    "low_priority": "hourly"
  },
  "health_metrics": [
    "connectivity",
    "authentication_validity",
    "response_time",
    "error_rate"
  ]
}
```

### Alerting Rules
- Connection failures
- Authentication errors
- Data validation failures > threshold
- Sync delays > SLA
- Unusual data volumes

## Data Quality Assurance

### Validation Layers
1. **Format Validation**: File structure and encoding
2. **Schema Validation**: Required fields and data types
3. **Business Rules**: Clinical data constraints
4. **Referential Integrity**: Cross-reference checks
5. **Duplicate Detection**: Prevent duplicate records

### Quality Metrics
- Validation pass rate
- Error distribution by type
- Data completeness scores
- Timeliness metrics
- Consistency checks

## Performance Optimization

### Sync Strategies
1. **Full Sync**: Complete data refresh
2. **Incremental**: Only new/modified records
3. **Delta**: Changed records with audit trail
4. **Real-time**: Streaming for critical data

### Resource Management
- Connection pooling
- Bandwidth throttling
- Concurrent sync limits
- Priority queue management
- Automatic retry with backoff

## Integration Architecture

### Data Flow
```
External System → Data Source API → Validation → Transformation → Storage
                          ↓
                    Monitoring & Alerts
```

### Error Handling
- Transient error retry
- Permanent error quarantine
- Partial success handling
- Rollback capabilities
- Manual intervention workflows

## Troubleshooting

### Common Issues
1. **Authentication Failures**
   - Expired credentials
   - Permission changes
   - Password policy violations

2. **Connectivity Issues**
   - Firewall blocks
   - Network timeouts
   - SSL certificate problems

3. **Data Quality Problems**
   - Format changes
   - Missing required fields
   - Invalid values

### Diagnostic Tools
- Connection test endpoint
- Detailed error logs
- Network trace capabilities
- Sample data preview
- Validation report generation

## Best Practices

### Configuration
1. Use strong authentication methods
2. Implement least-privilege access
3. Regular credential rotation
4. Monitor connection health
5. Document data mappings

### Operations
1. Schedule syncs during off-peak hours
2. Implement gradual rollout for new sources
3. Regular validation rule reviews
4. Maintain source system contacts
5. Plan for source system maintenance

## Change Log

### Version 1.0 (January 2025)
- Initial implementation
- Support for major EDC systems
- Basic laboratory connections
- SFTP and API connectivity

### Planned Enhancements
- Real-time streaming support
- AI-powered data mapping
- Automated schema detection
- Self-healing connections
- Advanced throttling controls

---

*Last Updated: January 2025*  
*API Version: 1.0*  
*Compliance: 21 CFR Part 11, HIPAA, GDPR*