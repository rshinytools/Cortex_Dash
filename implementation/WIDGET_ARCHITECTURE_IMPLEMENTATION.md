# Widget Architecture Implementation Plan

## Executive Summary

This document outlines the phased implementation of a comprehensive widget architecture for the Cortex Clinical Dashboard platform. The architecture enables flexible data mapping between EDC source data and dynamic dashboard widgets, supporting both manual uploads and API integrations (Medidata Rave, Veeva Vault).

## Core Architecture Principles

1. **Data Source Agnostic**: Widgets work with any EDC data structure
2. **Semantic Mapping**: Map data by meaning, not column names
3. **Reusable Templates**: Dashboard templates work across different studies
4. **Smart Caching**: Configurable TTL with intelligent invalidation
5. **Complex Calculations**: Support for derived fields and custom SQL

---

## Phase 1: Foundation Layer (4-6 weeks)

### Objective
Establish core data models, basic widget definitions, and foundational infrastructure.

### 1.1 Database Schema Updates
- [ ] Create widget_definitions table with enhanced schema
- [ ] Add data_contract column (JSONB) to widget_definitions
- [ ] Create study_data_mappings table
- [ ] Create widget_mapping_templates table
- [ ] Add dataset_metadata table for uploaded files
- [ ] Create data_cache table for query results
- [ ] Add widget_calculations table for derived fields
- [ ] Update dashboard_templates to support widget placeholders

### 1.2 Backend Models & API
- [ ] Update WidgetDefinition model with data contract
- [ ] Create StudyDataMapping model
- [ ] Create DatasetMetadata model
- [ ] Create WidgetMappingTemplate model
- [ ] Implement /api/v1/widgets/definitions CRUD endpoints
- [ ] Implement /api/v1/study/{id}/mappings endpoints
- [ ] Create /api/v1/datasets/metadata extraction endpoint
- [ ] Add /api/v1/mapping-templates CRUD endpoints

### 1.3 Core Widget Types (5 widgets)
- [ ] **KPI Metric Card**
  - [ ] Define data contract
  - [ ] Create configuration schema
  - [ ] Implement aggregation logic
  - [ ] Add comparison calculations
- [ ] **Time Series Chart**
  - [ ] Define temporal data requirements
  - [ ] Support multiple aggregation periods
  - [ ] Implement trend calculations
  - [ ] Add forecast capabilities
- [ ] **Distribution Chart**
  - [ ] Define categorical data requirements
  - [ ] Support multiple chart types (pie, bar, histogram)
  - [ ] Add statistical calculations
  - [ ] Implement drill-down logic
- [ ] **Data Table**
  - [ ] Define flexible column mapping
  - [ ] Add sorting/filtering logic
  - [ ] Support computed columns
  - [ ] Implement export functionality
- [ ] **Subject Timeline**
  - [ ] Define event-based data structure
  - [ ] Support point and range events
  - [ ] Add timeline calculations
  - [ ] Implement multiple view modes

### 1.4 Frontend Components
- [ ] Create WidgetDefinitionForm with data contract builder
- [ ] Build DataMappingInterface component
- [ ] Implement WidgetPreview component
- [ ] Create MappingTemplateSelector
- [ ] Add DatasetMetadataViewer
- [ ] Build CalculationBuilder UI

---

## Phase 2: Data Mapping Engine (4-5 weeks)

### Objective
Implement intelligent data mapping with metadata extraction and validation.

### 2.1 Metadata Extraction
- [ ] Create CSV parser with column analysis
- [ ] Implement Excel/XLSX parser
- [ ] Add SAS7BDAT file support
- [ ] Build data type detection logic
- [ ] Implement pattern recognition for common fields
- [ ] Add data quality analysis (nulls, uniqueness)
- [ ] Create granularity detection (subject/visit/event level)

### 2.2 Mapping Interface
- [ ] Build visual field mapping UI
- [ ] Add drag-and-drop field connections
- [ ] Implement mapping validation
- [ ] Create field type compatibility checks
- [ ] Add mapping preview with sample data
- [ ] Build mapping template save/load
- [ ] Implement bulk mapping operations

### 2.3 Query Generation Engine
- [ ] Create SQL query builder from mappings
- [ ] Implement JOIN logic for multiple datasets
- [ ] Add WHERE clause generation from filters
- [ ] Build GROUP BY logic from widget requirements
- [ ] Create aggregation function mapping
- [ ] Add subquery support for complex calculations
- [ ] Implement query optimization logic

### 2.4 Validation Framework
- [ ] Create data type validators
- [ ] Add required field checks
- [ ] Implement relationship validation for JOINs
- [ ] Build data quality rules engine
- [ ] Add custom validation rule support
- [ ] Create validation report generator
- [ ] Implement fix suggestions

---

## Phase 3: Calculation Engine (3-4 weeks)

### Objective
Build comprehensive calculation capabilities with custom expressions.

### 3.1 Expression Parser
- [ ] Implement SQL expression parser
- [ ] Add field reference resolver
- [ ] Create function call parser
- [ ] Build operator precedence logic
- [ ] Add parenthesis handling
- [ ] Implement type checking
- [ ] Create syntax validation

### 3.2 Function Library
- [ ] **Basic Math Functions**
  - [ ] Arithmetic operations (+, -, *, /, %)
  - [ ] ROUND, CEIL, FLOOR, ABS
  - [ ] POWER, SQRT, LOG
- [ ] **Statistical Functions**
  - [ ] MEAN, MEDIAN, MODE
  - [ ] STDDEV, VARIANCE
  - [ ] PERCENTILE, QUARTILE
  - [ ] MIN, MAX, RANGE
- [ ] **Date Functions**
  - [ ] DATE_DIFF, DATE_ADD
  - [ ] DATE_TRUNC, DATE_FORMAT
  - [ ] AGE calculation
  - [ ] BUSINESS_DAYS
- [ ] **String Functions**
  - [ ] CONCAT, SUBSTRING
  - [ ] UPPER, LOWER, TRIM
  - [ ] REPLACE, REGEX_EXTRACT
- [ ] **Clinical Functions**
  - [ ] BMI, BSA, eGFR
  - [ ] CTCAE grade mapping
  - [ ] Study day calculation
  - [ ] Visit window checking

### 3.3 Calculation Builder UI
- [ ] Create visual formula builder
- [ ] Add function autocomplete
- [ ] Implement field picker
- [ ] Build expression validator
- [ ] Add calculation preview
- [ ] Create calculation templates
- [ ] Implement calculation testing

### 3.4 Performance Optimization
- [ ] Implement calculation caching
- [ ] Add incremental computation
- [ ] Create calculation dependency graph
- [ ] Build parallel execution for independent calcs
- [ ] Add calculation profiling
- [ ] Implement optimization suggestions

---

## Phase 4: Caching & Performance (2-3 weeks)

### Objective
Implement intelligent caching with configurable TTL and invalidation strategies.

### 4.1 Cache Infrastructure
- [ ] Implement Redis cache layer
- [ ] Create cache key generation logic
- [ ] Add TTL configuration per widget
- [ ] Build cache invalidation triggers
- [ ] Implement cache warming on data upload
- [ ] Add cache statistics tracking
- [ ] Create cache management API

### 4.2 Query Optimization
- [ ] Implement query result caching
- [ ] Add query plan analysis
- [ ] Create index recommendations
- [ ] Build query batching for multiple widgets
- [ ] Add materialized view support
- [ ] Implement incremental refresh
- [ ] Create query performance monitoring

### 4.3 Data Partitioning
- [ ] Implement time-based partitioning
- [ ] Add study-based data isolation
- [ ] Create partition pruning logic
- [ ] Build parallel query execution
- [ ] Add partition maintenance jobs
- [ ] Implement archival strategy

### 4.4 Performance Monitoring
- [ ] Add query execution tracking
- [ ] Create performance dashboards
- [ ] Implement slow query logging
- [ ] Build resource usage monitoring
- [ ] Add alert thresholds
- [ ] Create optimization reports

---

## Phase 5: API Integrations (3-4 weeks)

### Objective
Integrate with external EDC systems for automated data synchronization.

### 5.1 Medidata Rave Integration
- [ ] Implement OAuth authentication
- [ ] Create Rave API client
- [ ] Build dataset listing endpoint
- [ ] Add incremental data sync
- [ ] Implement error handling and retry
- [ ] Create sync status monitoring
- [ ] Add field mapping auto-detection

### 5.2 Veeva Vault Integration
- [ ] Implement Vault authentication
- [ ] Create Vault API client
- [ ] Build study data extraction
- [ ] Add query API support
- [ ] Implement change detection
- [ ] Create sync scheduling
- [ ] Add connection testing

### 5.3 Generic API Framework
- [ ] Create pluggable connector interface
- [ ] Build authentication manager
- [ ] Implement rate limiting
- [ ] Add request/response logging
- [ ] Create error recovery logic
- [ ] Build connection pool management
- [ ] Add API health monitoring

### 5.4 Sync Management
- [ ] Create sync scheduler (Celery)
- [ ] Build sync status dashboard
- [ ] Implement conflict resolution
- [ ] Add sync history tracking
- [ ] Create sync notifications
- [ ] Build manual sync triggers
- [ ] Add sync validation

---

## Phase 6: Advanced Features (4-5 weeks)

### Objective
Add enterprise features and advanced capabilities.

### 6.1 Multi-Dataset JOINs
- [ ] Implement JOIN builder UI
- [ ] Add JOIN type selection (INNER, LEFT, RIGHT)
- [ ] Create key matching logic
- [ ] Build JOIN validation
- [ ] Add complex JOIN conditions
- [ ] Implement JOIN optimization
- [ ] Create JOIN preview

### 6.2 Custom SQL Support
- [ ] Create SQL editor with syntax highlighting
- [ ] Add SQL validation and sanitization
- [ ] Implement parameter binding
- [ ] Build SQL template library
- [ ] Add SQL execution sandbox
- [ ] Create SQL performance analysis
- [ ] Implement SQL version control

### 6.3 Advanced Visualizations
- [ ] Add Gantt charts for timelines
- [ ] Implement heatmaps for correlations
- [ ] Create Sankey diagrams for flow
- [ ] Add geographical maps for sites
- [ ] Build waterfall charts for changes
- [ ] Implement box plots for distributions
- [ ] Create combination charts

### 6.4 Data Quality Framework
- [ ] Create quality rule builder
- [ ] Add anomaly detection
- [ ] Implement completeness checks
- [ ] Build consistency validation
- [ ] Add trend analysis
- [ ] Create quality scorecards
- [ ] Implement quality alerts

### 6.5 Export & Reporting
- [ ] Add PowerPoint export with charts
- [ ] Create Excel export with formatting
- [ ] Build PDF report generator
- [ ] Implement scheduled reports
- [ ] Add report templates
- [ ] Create report distribution
- [ ] Build report API

---

## Phase 7: Testing & Optimization (2-3 weeks)

### Objective
Comprehensive testing and performance optimization.

### 7.1 Unit Testing
- [ ] Widget definition tests
- [ ] Mapping logic tests
- [ ] Calculation engine tests
- [ ] Query generation tests
- [ ] Cache logic tests
- [ ] API integration tests
- [ ] Validation framework tests

### 7.2 Integration Testing
- [ ] End-to-end data flow tests
- [ ] Multi-dataset JOIN tests
- [ ] Complex calculation tests
- [ ] Cache invalidation tests
- [ ] API sync tests
- [ ] Performance benchmark tests
- [ ] Security penetration tests

### 7.3 Performance Testing
- [ ] Load testing with large datasets
- [ ] Concurrent user testing
- [ ] Cache performance testing
- [ ] Query optimization testing
- [ ] Memory usage profiling
- [ ] Network latency testing
- [ ] Database connection pooling

### 7.4 User Acceptance Testing
- [ ] Widget creation workflow
- [ ] Data mapping usability
- [ ] Calculation builder testing
- [ ] Dashboard performance testing
- [ ] Export functionality testing
- [ ] API integration testing
- [ ] Documentation review

---

## Phase 8: Documentation & Training (2 weeks)

### Objective
Create comprehensive documentation and training materials.

### 8.1 Technical Documentation
- [ ] API documentation with examples
- [ ] Database schema documentation
- [ ] Architecture diagrams
- [ ] Deployment guides
- [ ] Configuration reference
- [ ] Troubleshooting guides
- [ ] Performance tuning guide

### 8.2 User Documentation
- [ ] Widget creation guide
- [ ] Data mapping tutorial
- [ ] Calculation builder guide
- [ ] Dashboard design best practices
- [ ] Import/export procedures
- [ ] FAQ compilation
- [ ] Video tutorials

### 8.3 Developer Documentation
- [ ] Custom widget development
- [ ] API integration guide
- [ ] Plugin development
- [ ] Testing procedures
- [ ] Code contribution guidelines
- [ ] Security best practices
- [ ] Performance optimization

---

## Implementation Timeline

```
Phase 1: Foundation Layer          [Weeks 1-6]   ████████████
Phase 2: Data Mapping Engine       [Weeks 5-10]      ██████████
Phase 3: Calculation Engine        [Weeks 9-13]          ████████
Phase 4: Caching & Performance     [Weeks 12-15]           ██████
Phase 5: API Integrations          [Weeks 14-18]             ████████
Phase 6: Advanced Features         [Weeks 17-22]                ██████████
Phase 7: Testing & Optimization    [Weeks 21-24]                      ██████
Phase 8: Documentation & Training  [Weeks 23-25]                        ████
```

Total Duration: **25 weeks** (with overlapping phases)

---

## Success Metrics

### Technical Metrics
- Widget load time < 2 seconds
- Dashboard refresh < 5 seconds
- Cache hit rate > 80%
- Query optimization > 50% improvement
- API sync reliability > 99.9%
- Zero data loss during sync

### User Experience Metrics
- Mapping time < 10 minutes per study
- Widget configuration < 5 minutes
- Calculation creation < 3 minutes
- Export generation < 30 seconds
- User satisfaction > 90%

### Business Metrics
- Study setup time reduced by 70%
- Template reuse rate > 80%
- Support tickets reduced by 50%
- User adoption rate > 90%
- Time to insights reduced by 60%

---

## Risk Mitigation

### Technical Risks
- **Performance degradation**: Implement progressive loading and pagination
- **Data inconsistency**: Add validation and reconciliation processes
- **API changes**: Version lock and adapter pattern
- **Security vulnerabilities**: Regular security audits and updates

### Operational Risks
- **User adoption**: Phased rollout with training
- **Data quality issues**: Automated quality checks
- **System downtime**: High availability architecture
- **Resource constraints**: Cloud scaling capabilities

---

## Dependencies

### External Dependencies
- PostgreSQL 15+
- Redis 7+
- Docker & Kubernetes
- EDC API access credentials
- SSL certificates

### Internal Dependencies
- User authentication system
- Audit logging framework
- Notification service
- File storage system
- Background job processor (Celery)

---

## Next Steps

1. **Week 1**: Review and approve implementation plan
2. **Week 2**: Set up development environment and CI/CD
3. **Week 3**: Begin Phase 1 implementation
4. **Week 4**: Weekly progress reviews and adjustments
5. **Ongoing**: Daily standups and bi-weekly demos

---

## Appendix A: Database Schema Changes

```sql
-- Widget Definitions with Data Contract
ALTER TABLE widget_definitions ADD COLUMN data_contract JSONB;
ALTER TABLE widget_definitions ADD COLUMN cache_ttl INTEGER DEFAULT 3600;
ALTER TABLE widget_definitions ADD COLUMN query_template TEXT;

-- Study Data Mappings
CREATE TABLE study_data_mappings (
    id UUID PRIMARY KEY,
    study_id UUID REFERENCES studies(id),
    widget_id UUID REFERENCES widget_definitions(id),
    dataset_id UUID REFERENCES dataset_metadata(id),
    field_mappings JSONB NOT NULL,
    transformations JSONB,
    join_config JSONB,
    cache_override INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Dataset Metadata
CREATE TABLE dataset_metadata (
    id UUID PRIMARY KEY,
    study_id UUID REFERENCES studies(id),
    filename VARCHAR(255),
    file_type VARCHAR(50),
    row_count INTEGER,
    column_metadata JSONB,
    granularity VARCHAR(50),
    upload_date TIMESTAMP DEFAULT NOW(),
    last_updated TIMESTAMP DEFAULT NOW()
);

-- Mapping Templates
CREATE TABLE widget_mapping_templates (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    description TEXT,
    widget_type VARCHAR(100),
    field_patterns JSONB,
    default_mappings JSONB,
    created_by UUID REFERENCES users(id),
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Query Cache
CREATE TABLE query_cache (
    cache_key VARCHAR(255) PRIMARY KEY,
    study_id UUID REFERENCES studies(id),
    widget_id UUID REFERENCES widget_definitions(id),
    query_hash VARCHAR(64),
    result_data JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    hit_count INTEGER DEFAULT 0
);
```

---

## Appendix B: API Endpoints

### Widget Management
- `GET /api/v1/widgets` - List all widgets with filtering
- `POST /api/v1/widgets` - Create new widget definition
- `PUT /api/v1/widgets/{id}` - Update widget definition
- `GET /api/v1/widgets/{id}/contract` - Get data contract
- `POST /api/v1/widgets/{id}/validate` - Validate widget configuration

### Data Mapping
- `GET /api/v1/studies/{id}/mappings` - Get study mappings
- `POST /api/v1/studies/{id}/mappings` - Create mapping
- `PUT /api/v1/studies/{id}/mappings/{mapping_id}` - Update mapping
- `POST /api/v1/studies/{id}/mappings/validate` - Validate mappings
- `GET /api/v1/studies/{id}/mappings/preview` - Preview with sample data

### Dataset Management
- `POST /api/v1/datasets/upload` - Upload dataset
- `GET /api/v1/datasets/{id}/metadata` - Get metadata
- `POST /api/v1/datasets/{id}/analyze` - Analyze dataset
- `GET /api/v1/datasets/{id}/preview` - Preview data

### Calculation Engine
- `POST /api/v1/calculations/validate` - Validate expression
- `POST /api/v1/calculations/execute` - Execute calculation
- `GET /api/v1/calculations/functions` - List available functions
- `POST /api/v1/calculations/test` - Test with sample data

### Cache Management
- `GET /api/v1/cache/stats` - Get cache statistics
- `POST /api/v1/cache/invalidate` - Invalidate cache
- `POST /api/v1/cache/warm` - Warm cache
- `GET /api/v1/cache/config` - Get cache configuration

---

## Document Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-08-13 | System | Initial implementation plan |

---

**End of Document**