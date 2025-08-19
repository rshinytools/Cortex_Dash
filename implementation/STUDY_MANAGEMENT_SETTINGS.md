# Study Management Settings - Implementation Plan

## Executive Summary
This document outlines the phased implementation approach for creating a unified Study Management Center that allows system administrators to edit and manage studies after initialization. The system reuses existing initialization workflow components in a tabbed interface.

**Core Principle**: Reuse the initialization wizard components with edit mode capabilities.

---

## 🎯 Project Goals

### Primary Objectives
1. Create a single management interface at `/studies/[id]/manage`
2. Enable system admins to update study configurations post-initialization
3. Reuse existing initialization components (70% code reuse)
4. Support data versioning and source switching
5. Handle new widget mapping requirements

### Success Criteria
- [ ] System admins can update study information
- [ ] System admins can upload new data (replace/append)
- [ ] System admins can switch between manual/API data sources
- [ ] System admins can map newly added widgets
- [ ] System admins can change dashboard templates

---

## 📋 Pre-Implementation Checklist

### Cleanup Tasks (Do First)
- [ ] Remove `/studies/[id]/settings` route and files
- [ ] Remove `/studies/[id]/edit` route and files
- [ ] Remove `/studies/[id]/pipeline` route and files
- [ ] Remove `/studies/[id]/data-sources/upload` route and files
- [ ] Clean up any imports/references to removed routes
- [ ] Update navigation links that point to removed routes

### Dependencies Verification
- [ ] Verify initialization wizard components are working
- [ ] Confirm RBAC system admin check is functioning
- [ ] Ensure data versioning folder structure is in place
- [ ] Check that study update API endpoints exist
- [ ] Verify file upload service is operational

---

## 📅 Phase 1: Foundation Setup (Week 1)

### Objective
Create the basic management page structure with tab navigation and admin authentication.

### Tasks

#### 1.1 Create Management Route Structure
- [ ] Create `/app/studies/[studyId]/manage/` folder
- [ ] Create `page.tsx` with basic structure
- [ ] Add system admin authentication check
- [ ] Implement redirect for non-admin users
- [ ] Add loading state while checking permissions

#### 1.2 Setup Tab Navigation
- [ ] Import and setup Tabs component from shadcn/ui
- [ ] Create four tabs: Info, Data Source, Mappings, Template
- [ ] Add tab state management
- [ ] Style tabs to match existing UI
- [ ] Add tab descriptions/help text

#### 1.3 Create Tab Container Components
- [ ] Create `/manage/components/` folder
- [ ] Create `study-info-tab.tsx` (empty shell)
- [ ] Create `data-source-tab.tsx` (empty shell)
- [ ] Create `mappings-tab.tsx` (empty shell)
- [ ] Create `template-tab.tsx` (empty shell)

#### 1.4 Add Management Link to Dashboard
- [ ] Add "Manage Study" button to study dashboard (admin only)
- [ ] Update study list page with manage action (admin only)
- [ ] Add breadcrumb navigation
- [ ] Create proper back navigation

### Deliverables
- Working `/studies/[id]/manage` route
- Tab navigation functional
- Admin-only access enforced
- Basic page structure in place

---

## 📅 Phase 2: Component Adaptation (Week 2)

### Objective
Adapt existing initialization components to work in edit mode with pre-populated data.

### Tasks

#### 2.1 Update Initialization Components for Dual Mode
- [ ] Add `mode: 'create' | 'edit'` prop to `BasicInfoStep`
- [ ] Add `initialData` prop to `BasicInfoStep`
- [ ] Add `onSave` callback to `BasicInfoStep`
- [ ] Repeat for `TemplateSelectionStep`
- [ ] Repeat for `DataUploadStep`
- [ ] Repeat for `FieldMappingStep`

#### 2.2 Implement Pre-population Logic
- [ ] Load existing study data in management page
- [ ] Pass study data to BasicInfoStep
- [ ] Pre-populate form fields
- [ ] Handle null/undefined values gracefully
- [ ] Add dirty state tracking

#### 2.3 Create Save Handlers
- [ ] Implement updateStudyInfo function
- [ ] Add success/error toast notifications
- [ ] Handle validation errors
- [ ] Add loading states during save
- [ ] Implement optimistic updates

#### 2.4 Wire Up Components to Tabs
- [ ] Connect BasicInfoStep to study-info-tab
- [ ] Connect TemplateSelectionStep to template-tab
- [ ] Connect DataUploadStep to data-source-tab
- [ ] Connect FieldMappingStep to mappings-tab
- [ ] Test data flow between parent and children

### Deliverables
- All initialization components work in edit mode
- Forms pre-populate with existing data
- Save functionality works per tab
- Proper error handling and feedback

---

## 📅 Phase 3: Data Management Features (Week 3)

### Objective
Implement data versioning, source switching, and upload modes.

### Tasks

#### 3.1 Data Version History
- [ ] Create version history component
- [ ] Fetch list of data versions from backend
- [ ] Display versions with timestamps
- [ ] Add "Current" indicator
- [ ] Implement version preview modal
- [ ] Add rollback functionality
- [ ] Add confirmation dialogs for rollback

#### 3.2 Upload Mode Selection
- [ ] Add Replace/Append radio buttons
- [ ] Update upload handler for replace mode
- [ ] Update upload handler for append mode
- [ ] Create new version folder on upload
- [ ] Update current version pointer
- [ ] Add upload progress indicator

#### 3.3 Data Source Switching
- [ ] Add source type selector (Manual/API)
- [ ] Create API configuration form
- [ ] Add API connection testing
- [ ] Implement credential storage (encrypted)
- [ ] Handle source type transitions
- [ ] Update data fetch logic based on source

#### 3.4 API Integration Setup
- [ ] Create Medidata Rave connector
- [ ] Create Veeva Vault connector
- [ ] Create REDCap connector
- [ ] Add custom API option
- [ ] Implement authentication flows
- [ ] Add error handling for API failures

### Deliverables
- Data versioning fully functional
- Replace/Append modes working
- API integration configured
- Source switching operational

---

## 📅 Phase 4: Mapping Enhancements (Week 4)

### Objective
Add new widget detection, mapping status indicators, and bulk operations.

### Tasks

#### 4.1 New Widget Detection
- [ ] Create widget comparison service
- [ ] Compare template widgets vs mapped widgets
- [ ] Identify unmapped widgets
- [ ] Add "New" badge to unmapped widgets
- [ ] Create unmapped widget notification
- [ ] Auto-scroll to unmapped widgets

#### 4.2 Mapping Status Indicators
- [ ] Add status icons (✅ ⚠️ ❌)
- [ ] Create mapping completeness calculation
- [ ] Add progress bar for overall mapping
- [ ] Highlight required vs optional fields
- [ ] Add validation messages
- [ ] Create mapping summary card

#### 4.3 Enhanced Mapping Interface
- [ ] Add "Only show unmapped" filter
- [ ] Implement auto-mapping suggestions
- [ ] Add bulk mapping operations
- [ ] Create mapping templates
- [ ] Add field search/filter
- [ ] Implement mapping preview

#### 4.4 Mapping Validation
- [ ] Add real-time validation
- [ ] Check data type compatibility
- [ ] Validate required fields
- [ ] Add warning for potential issues
- [ ] Create validation report
- [ ] Block save if critical errors

### Deliverables
- New widgets automatically detected
- Clear mapping status visibility
- Improved mapping workflow
- Comprehensive validation

---

## 📅 Phase 5: Template Management (Week 5)

### Objective
Enable template switching with proper migration and mapping preservation.

### Tasks

#### 5.1 Template Change Flow
- [ ] Add template change confirmation
- [ ] Create backup of current configuration
- [ ] Implement template compatibility check
- [ ] Show template differences
- [ ] Handle widget migration
- [ ] Update dashboard layout

#### 5.2 Mapping Migration
- [ ] Identify common widgets between templates
- [ ] Preserve existing mappings where possible
- [ ] Flag widgets that need remapping
- [ ] Auto-map similar widgets
- [ ] Create mapping migration report
- [ ] Handle orphaned mappings

#### 5.3 Template Preview
- [ ] Add template preview in management
- [ ] Show before/after comparison
- [ ] Display affected widgets
- [ ] Estimate remapping effort
- [ ] Show data compatibility
- [ ] Add rollback option

### Deliverables
- Template switching functional
- Mapping preservation working
- Clear migration workflow
- Rollback capability

---

## 📅 Phase 6: Scheduling & Automation (Week 6)

### Objective
Implement scheduled data pulls and automated workflows.

### Tasks

#### 6.1 Schedule Configuration
- [ ] Create schedule UI component
- [ ] Add frequency options (daily/weekly/monthly)
- [ ] Add time picker
- [ ] Add timezone handling
- [ ] Create schedule preview
- [ ] Add enable/disable toggle

#### 6.2 Backend Scheduling
- [ ] Setup Celery beat for scheduling
- [ ] Create scheduled task definitions
- [ ] Implement task execution
- [ ] Add task monitoring
- [ ] Handle failed tasks
- [ ] Add retry logic

#### 6.3 Automation Features
- [ ] Add auto-mapping for known patterns
- [ ] Create mapping rules engine
- [ ] Add data validation rules
- [ ] Implement alert conditions
- [ ] Add email notifications
- [ ] Create automation logs

### Deliverables
- Scheduling UI complete
- Automated data pulls working
- Notification system active
- Automation logs available

---

## 📅 Phase 7: Polish & Optimization (Week 7)

### Objective
Refine UI/UX, optimize performance, and add quality-of-life features.

### Tasks

#### 7.1 UI/UX Improvements
- [ ] Add keyboard shortcuts
- [ ] Implement unsaved changes warning
- [ ] Add contextual help
- [ ] Create guided tours
- [ ] Improve error messages
- [ ] Add loading skeletons

#### 7.2 Performance Optimization
- [ ] Implement lazy loading for tabs
- [ ] Add data caching
- [ ] Optimize API calls
- [ ] Add pagination for large datasets
- [ ] Implement virtual scrolling
- [ ] Add request debouncing

#### 7.3 Additional Features
- [ ] Add activity log
- [ ] Create audit trail viewer
- [ ] Add export configuration
- [ ] Implement configuration templates
- [ ] Add bulk study management
- [ ] Create management dashboard

### Deliverables
- Polished user interface
- Optimized performance
- Enhanced feature set
- Production-ready system

---

## 📅 Phase 8: Testing & Documentation (Week 8)

### Objective
Ensure system reliability and create comprehensive documentation.

### Tasks

#### 8.1 Testing
- [ ] Unit tests for all components
- [ ] Integration tests for workflows
- [ ] E2E tests for critical paths
- [ ] Load testing for large datasets
- [ ] Security testing for admin features
- [ ] Cross-browser testing

#### 8.2 Bug Fixes
- [ ] Fix issues from testing
- [ ] Handle edge cases
- [ ] Improve error handling
- [ ] Add fallback states
- [ ] Fix UI inconsistencies
- [ ] Resolve performance issues

#### 8.3 Documentation
- [ ] Create user guide
- [ ] Write API documentation
- [ ] Document component props
- [ ] Create troubleshooting guide
- [ ] Add inline code comments
- [ ] Update README files

### Deliverables
- All tests passing
- Bugs resolved
- Complete documentation
- Deployment ready

---

## 🚀 Quick Wins (Can Do Immediately)

These tasks can be done in parallel with main development:

- [ ] Add "Coming Soon" management page
- [ ] Remove broken route files
- [ ] Add management button (disabled)
- [ ] Create page structure
- [ ] Setup component shells
- [ ] Add navigation breadcrumbs
- [ ] Create loading states
- [ ] Add error boundaries

---

## 📊 Success Metrics

### Functional Metrics
- [ ] All 4 management functions working
- [ ] Zero critical bugs
- [ ] < 3 second page load time
- [ ] 100% admin-only access enforced

### Code Quality Metrics
- [ ] 70% code reuse achieved
- [ ] 80% test coverage
- [ ] No duplicate code
- [ ] All components documented

### User Experience Metrics
- [ ] Average task completion < 2 minutes
- [ ] Zero confusion points in UI
- [ ] All actions have feedback
- [ ] All errors have recovery paths

---

## 🚨 Risk Mitigation

### Identified Risks
1. **Risk**: Breaking existing initialization flow
   - **Mitigation**: Careful component modification with fallbacks

2. **Risk**: Data corruption during version switching
   - **Mitigation**: Always create new versions, never modify existing

3. **Risk**: API integration failures
   - **Mitigation**: Fallback to manual upload, comprehensive error handling

4. **Risk**: Performance issues with large datasets
   - **Mitigation**: Pagination, lazy loading, virtual scrolling

5. **Risk**: Security vulnerabilities in admin features
   - **Mitigation**: Strict RBAC enforcement, audit logging

---

## 📝 Notes

### Implementation Guidelines
- Always check for system admin role before allowing access
- Create new data version folders, never modify existing
- Preserve existing functionality while adding new features
- Test with real study data throughout development
- Keep UI consistent with existing design patterns

### Future Enhancements (Not in Current Scope)
- Bulk study operations
- Study templates/cloning
- Advanced automation rules
- Machine learning for auto-mapping
- Real-time collaboration features
- Mobile-responsive management

---

## ✅ Final Checklist Before Launch

- [ ] All phases completed
- [ ] Security review passed
- [ ] Performance benchmarks met
- [ ] Documentation complete
- [ ] User training prepared
- [ ] Rollback plan ready
- [ ] Monitoring configured
- [ ] Support team briefed

---

*Document Version: 1.0*  
*Created: [Current Date]*  
*Last Updated: [Current Date]*  
*Owner: System Admin Team*