# Dashboard Template Fixes Implementation Plan

## Overview
This document tracks the implementation of fixes for the dashboard template system where templates show "0 dashboards 0 widgets" despite having content.

## Root Cause Analysis
1. Dashboard template API endpoint doesn't include nested dashboard and widget data
2. Frontend expects nested data but receives only template metadata
3. Study initialization has race conditions when fetching data
4. Missing data source configuration step in the wizard

## Implementation Checklist

### Phase 1: Backend API Fixes

#### [x] 1.1 Fix Dashboard Template API Response
- **File**: `backend/app/api/v1/endpoints/runtime/dashboard_templates.py`
- **Task**: Modify GET endpoint to include nested dashboards and widgets
- **Details**:
  - Add relationship loading for dashboards
  - Add relationship loading for widgets within dashboards
  - Ensure proper JSON serialization of nested data
- **Test**: Verify API returns complete nested structure

#### [x] 1.2 Add Dashboard Count Properties
- **File**: `backend/app/models/dashboard.py`
- **Task**: Add computed properties for dashboard and widget counts
- **Details**:
  - Add `dashboard_count` property to DashboardTemplate
  - Add `widget_count` property to DashboardTemplate
  - Use SQLAlchemy hybrid properties for efficiency
- **Test**: Verify counts are accurate in API responses

#### [x] 1.3 Fix Study Details API
- **File**: `backend/app/api/v1/endpoints/studies.py`
- **Task**: Ensure study details endpoint handles missing data gracefully
- **Details**:
  - Add proper 404 handling
  - Return partial data when study is being initialized
  - Add initialization status field
- **Test**: No 404 errors during study creation flow

### Phase 2: Frontend Display Fixes

#### [x] 2.1 Update Dashboard Template Card Display
- **File**: `frontend/src/app/studies/[studyId]/initialize/steps/dashboard-step.tsx`
- **Task**: Display correct dashboard and widget counts
- **Details**:
  - Use nested data from API response
  - Calculate counts from dashboards array
  - Show loading state while fetching
- **Test**: Template cards show correct counts

#### [x] 2.2 Add Loading States
- **File**: `frontend/src/app/studies/[studyId]/initialize/steps/dashboard-step.tsx`
- **Task**: Add proper loading and error states
- **Details**:
  - Show skeleton loaders while fetching
  - Handle API errors gracefully
  - Add retry mechanism for failed requests
- **Test**: Smooth loading experience without errors

#### [x] 2.3 Fix Study Navigation
- **File**: `frontend/src/app/studies/[studyId]/dashboard/page.tsx`
- **Task**: Handle study not found errors
- **Details**:
  - Check if study exists before rendering
  - Show appropriate error message
  - Add redirect to study list if not found
- **Test**: No 404 errors when navigating to study

### Phase 3: Data Source Configuration

#### [x] 3.1 Add Data Source Step to Wizard
- **File**: `frontend/src/app/studies/[studyId]/initialize/page.tsx`
- **Task**: Add data source configuration as step 2
- **Details**:
  - Insert between dashboard selection and field mapping
  - Create new DataSourceStep component
  - Update step navigation logic
- **Test**: Wizard shows data source step

#### [ ] 3.2 Create Data Source Configuration UI
- **File**: `frontend/src/app/studies/[studyId]/initialize/steps/data-source-step.tsx` (new)
- **Task**: Create UI for configuring data sources
- **Details**:
  - Support multiple data source types (SFTP, API, Manual)
  - Add connection testing
  - Save configuration to backend
- **Test**: Can configure and test data sources

#### [ ] 3.3 Update Field Mapping Step
- **File**: `frontend/src/app/studies/[studyId]/initialize/steps/data-mapping-step.tsx`
- **Task**: Use configured data sources for field mapping
- **Details**:
  - Load data sources from previous step
  - Show available fields from each source
  - Improve mapping UI/UX
- **Test**: Field mapping uses actual data sources

### Phase 4: Study Initialization Flow

#### [ ] 4.1 Add Study Status Tracking
- **File**: `backend/app/models/study.py`
- **Task**: Add initialization status field
- **Details**:
  - Add status enum (draft, initializing, active, etc.)
  - Track initialization progress
  - Update status on completion
- **Test**: Status updates correctly through flow

#### [ ] 4.2 Improve Initialization API
- **File**: `backend/app/api/v1/endpoints/studies.py`
- **Task**: Add initialization completion endpoint
- **Details**:
  - Validate all required fields configured
  - Transition study to active status
  - Return any validation errors
- **Test**: Study becomes active after initialization

#### [ ] 4.3 Add Progress Indicators
- **File**: `frontend/src/app/studies/[studyId]/initialize/page.tsx`
- **Task**: Show initialization progress
- **Details**:
  - Add progress bar component
  - Show completion percentage
  - Highlight incomplete steps
- **Test**: Clear progress indication

### Phase 5: Testing and Validation

#### [ ] 5.1 End-to-End Testing
- Create automated test for complete flow
- Test with multiple dashboard templates
- Verify data persistence

#### [ ] 5.2 Error Handling
- Test all error scenarios
- Ensure graceful degradation
- Add user-friendly error messages

#### [ ] 5.3 Performance Testing
- Test with large numbers of widgets
- Optimize API queries if needed
- Add caching where appropriate

## Success Criteria
- [ ] Dashboard templates show correct dashboard and widget counts
- [ ] No 404 errors during study creation flow
- [ ] Data source configuration is intuitive and functional
- [ ] Field mapping uses actual data from configured sources
- [ ] Study initialization completes successfully
- [ ] All tests pass

## Notes
- Prioritize Phase 1 and 2 for immediate fix
- Phase 3 and 4 enhance the overall experience
- Consider adding more detailed documentation after implementation