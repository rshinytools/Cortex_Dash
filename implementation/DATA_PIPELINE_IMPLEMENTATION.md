# Data Pipeline Implementation Plan
## Clinical Dashboard Data Flow Architecture

---

## 🎯 **Executive Summary**

This document outlines a pragmatic, phased approach to implementing a working data pipeline for the Clinical Dashboard. We prioritize getting a simple solution working first, then adding complexity as needed.

**Core Principle**: Make it work, make it right, make it fast (in that order).

---

## 🚨 **Critical Issues to Address**

### **Current State Problems:**
1. **Widgets exist but don't show data** - UI is there but no data connection
2. **Metadata extraction happens but isn't stored** - Information is lost
3. **Mappings aren't persisted** - User work is wasted
4. **No data validation** - Bad data can break everything
5. **Over-complex architecture** - Too many moving parts that don't connect

### **Proposed Solutions:**
1. **PostgreSQL first, Parquet later** - Simpler, works immediately
2. **Auto-detect CDISC standards** - Reduce manual mapping by 90%
3. **Progressive complexity** - Start simple, add features as needed
4. **Validation at every step** - Fail fast with clear errors

---

## 📋 **Phase 0: Foundation Fixes** (3 days)
*Fix what's broken before adding new features*

### Objectives:
- Fix file path structure to be organization-based
- Ensure basic upload/conversion works
- Store metadata properly

### Tasks:
- [ ] Update all file paths to `/data/{org_id}/studies/{study_id}/`
- [ ] Fix `FileConversionService` to use new paths
- [ ] Create `dataset_metadata` table migration
- [ ] Update `StudyInitializationService` to save metadata
- [ ] Add basic error handling and logging
- [ ] Test with real clinical data files

### Success Criteria:
- Files upload to correct organization folder
- Metadata is stored in database
- Can query metadata via API

### Code Changes:
```python
# backend/app/services/file_conversion_service.py
def get_study_data_path(org_id: UUID, study_id: UUID, data_type: str = "source_data"):
    """Get the correct path for study data"""
    return Path(f"/data/{org_id}/studies/{study_id}/{data_type}/{get_timestamp_folder()}")
```

---

## 📋 **Phase 1: Simple PostgreSQL Storage** (1 week)
*Get data flowing end-to-end with PostgreSQL*

### Objectives:
- Store uploaded data in PostgreSQL tables
- Auto-detect CDISC structure
- Show data in ONE widget (KPI Card)

### Tasks:
- [ ] Create `study_datasets` table to store actual data
- [ ] Build CDISC detector service
- [ ] Implement CSV → PostgreSQL importer
- [ ] Create simple query builder for KPI widget
- [ ] Connect KPI widget to PostgreSQL data
- [ ] Add data preview in upload step

### Database Schema:
```sql
-- Store uploaded data in PostgreSQL (simple approach)
CREATE TABLE study_datasets (
    id UUID PRIMARY KEY,
    org_id UUID NOT NULL,
    study_id UUID NOT NULL,
    dataset_name VARCHAR(100),  -- "demographics", "adverse_events"
    row_data JSONB,             -- Actual data rows
    created_at TIMESTAMP,
    version INTEGER DEFAULT 1,
    UNIQUE(study_id, dataset_name, version)
);

-- Index for fast queries
CREATE INDEX idx_study_datasets_data ON study_datasets USING GIN (row_data);
```

### Success Criteria:
- Upload CSV → Store in PostgreSQL → Display in KPI widget
- Auto-detection works for standard CDISC files
- User can see actual data immediately

---

## 📋 **Phase 2: Smart Field Mapping** (1 week)
*Make mapping intelligent and user-friendly*

### Objectives:
- Auto-map 90% of fields using CDISC patterns
- Simple UI for reviewing/adjusting mappings
- Save and reuse mapping templates

### Tasks:
- [ ] Enhance CDISC pattern matching
- [ ] Build mapping preview UI with sample data
- [ ] Implement mapping templates
- [ ] Add mapping validation
- [ ] Create "mapping confidence score"
- [ ] Test with various CDISC datasets

### Smart Mapping Logic:
```python
class SmartMapper:
    def auto_map_fields(self, dataset_columns: List[str]) -> Dict[str, float]:
        """
        Returns mapping suggestions with confidence scores
        Example: {"USUBJID": {"maps_to": "subject_id", "confidence": 0.95}}
        """
        # Check exact matches first
        # Then check patterns
        # Then check semantic similarity
```

### Success Criteria:
- 90% of CDISC fields map automatically
- User can approve mappings in <1 minute
- Mapping templates reduce future work

---

## 📋 **Phase 3: Multi-Dataset Queries** (1 week)
*Enable widgets to query across multiple datasets*

### Objectives:
- Join demographics with lab data
- Enable time-series analysis
- Support derived calculations

### Tasks:
- [ ] Implement dataset joining logic
- [ ] Add time-series aggregations
- [ ] Build calculation engine
- [ ] Create data lineage tracking
- [ ] Add query performance monitoring
- [ ] Test with complex clinical queries

### Example Complex Query:
```sql
-- Get lab values with demographics
SELECT 
    d.subject_id,
    d.age,
    d.sex,
    l.test_name,
    l.value,
    l.visit_date
FROM demographics d
JOIN lab_results l ON d.subject_id = l.subject_id
WHERE l.test_name = 'ALT'
  AND l.value > normal_range_upper
```

---

## 📋 **Phase 4: Performance Optimization** (1 week)
*Make it fast for large datasets*

### Objectives:
- Add caching layer
- Implement Parquet for large files (>100k rows)
- Background processing for heavy operations

### Tasks:
- [ ] Implement Redis caching
- [ ] Add Parquet storage option
- [ ] Create background job queue
- [ ] Build incremental update system
- [ ] Add query optimization
- [ ] Performance testing with large datasets

### Decision Tree:
```
IF rows < 10,000 → PostgreSQL only
IF rows < 100,000 → PostgreSQL + Redis cache  
IF rows > 100,000 → Parquet + DuckDB
```

---

## 📋 **Phase 5: Advanced Features** (2 weeks)
*Add enterprise features*

### Objectives:
- Real-time data updates
- Advanced visualizations
- Export capabilities
- API integrations

### Tasks:
- [ ] WebSocket for real-time updates
- [ ] Connect remaining 4 widgets
- [ ] Build export system
- [ ] Add Medidata Rave integration
- [ ] Implement data quality checks
- [ ] Create automated reports

---

## 🎯 **Success Metrics**

### Phase 0-1 (MVP):
- **Upload to Display**: <30 seconds
- **Auto-mapping accuracy**: >90% for CDISC
- **User satisfaction**: Can see their data immediately

### Phase 2-3 (Enhanced):
- **Complex queries**: <2 seconds
- **Multiple datasets**: Seamless joining
- **Reduced manual work**: 80% less mapping effort

### Phase 4-5 (Optimized):
- **Large datasets**: Handle 1M+ rows
- **Real-time updates**: <100ms latency
- **Enterprise ready**: Full audit trail, validations

---

## ⚠️ **Risk Mitigation**

### Technical Risks:
1. **Risk**: Parquet complexity
   - **Mitigation**: PostgreSQL first, Parquet only when needed

2. **Risk**: Manual mapping burden
   - **Mitigation**: Invest heavily in auto-detection

3. **Risk**: Performance issues
   - **Mitigation**: Start with small data, optimize later

### User Experience Risks:
1. **Risk**: Too complex for users
   - **Mitigation**: Progressive disclosure, smart defaults

2. **Risk**: Data quality issues
   - **Mitigation**: Validation at every step, clear error messages

---

## 🚀 **Quick Wins** (Do These First!)

1. **Fix file paths** (2 hours)
2. **Store metadata** (4 hours)  
3. **Show data in KPI widget** (1 day)
4. **Add data preview** (4 hours)
5. **Auto-detect CDISC** (1 day)

These quick wins will:
- Show immediate progress
- Build confidence
- Provide working features for testing

---

## 📝 **Implementation Notes**

### What to AVOID:
- Don't over-engineer early
- Don't add features without user feedback
- Don't optimize prematurely
- Don't build complex UI before simple works

### What to FOCUS on:
- Get data flowing end-to-end ASAP
- Make the happy path work perfectly
- Fail fast with clear errors
- Test with real clinical data

### Architecture Decisions:
1. **PostgreSQL vs Parquet**: Start with PostgreSQL, add Parquet in Phase 4
2. **Sync vs Async**: Sync for small operations, async for large
3. **Caching**: Add only after measuring performance
4. **Complexity**: Hide it from users, expose via "Advanced" options

---

## 📅 **Realistic Timeline**

### Month 1:
- Week 1: Phase 0 (Foundation)
- Week 2: Phase 1 (PostgreSQL Storage)
- Week 3: Phase 2 (Smart Mapping)
- Week 4: Phase 3 (Multi-Dataset)

### Month 2:
- Week 1: Phase 4 (Optimization)
- Week 2-3: Phase 5 (Advanced Features)
- Week 4: Testing, Bug Fixes, Polish

### Total: 8 weeks to production-ready

---

## ✅ **Definition of Done**

Each phase is complete when:
1. All tasks checked off
2. Tests written and passing
3. Documentation updated
4. Code reviewed and merged
5. Deployed to staging
6. User acceptance tested

---

## 🔄 **Feedback Loops**

After each phase:
1. Demo to stakeholders
2. Gather user feedback
3. Adjust next phase based on learnings
4. Document what worked/didn't work

---

## 💡 **Alternative Approaches**

If the above doesn't work:

### Plan B: Direct Parquet Queries
- Skip PostgreSQL entirely
- Use DuckDB to query Parquet directly
- Simpler architecture but less flexible

### Plan C: Commercial Solution
- Use Apache Superset for dashboards
- Focus on data preparation only
- Faster to market but less control

### Plan D: Hybrid Approach
- Use PostgreSQL for metadata
- Use Parquet for data
- Query both as needed

---

## 📊 **Measuring Success**

### Technical Metrics:
- Query performance (<2s for 95% of queries)
- Upload success rate (>99%)
- Auto-mapping accuracy (>90%)
- System uptime (>99.9%)

### Business Metrics:
- Time to first insight (<5 minutes from upload)
- User engagement (daily active users)
- Data quality scores (>95% valid)
- Customer satisfaction (NPS >50)

---

## 🎬 **Getting Started**

1. **Today**: Review this plan, adjust as needed
2. **Tomorrow**: Start Phase 0 - fix file paths
3. **This Week**: Complete Phase 0, start Phase 1
4. **Next Week**: Have working KPI widget with real data

Remember: **Perfect is the enemy of good. Ship something that works, then iterate.**