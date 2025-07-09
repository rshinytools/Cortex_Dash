# Core Workflow Implementation Document

## Overview
This document tracks the implementation of core functionality needed to achieve a working end-to-end workflow for the Clinical Dashboard Platform. The goal is to enable the complete workflow from admin configuration to end-user dashboard access.

## Target Workflow
1. System admin creates menu templates and dashboard templates
2. Admin creates organization and study
3. Study initialization with template selection and data mapping
4. End users access fully functional dashboards with navigation and filters

---

## Phase 1: Menu Navigation & Widget Layout Switching ⭐ CRITICAL

### Overview
Enable menu items to switch between different widget layouts within the same dashboard context. Currently, clicking menu items only highlights them but doesn't change the displayed widgets.

### Implementation Tasks

#### 1.1 Backend: Store Widget Layouts per Menu Item
- [x] **Update Dashboard Template Model**
  - [x] Modify `template_structure` to support layouts per menu item
  - [x] Structure: `template_structure.dashboards[].id = menu_item_id, layout = widgets`
  - [x] Migration to update existing templates (not needed - existing structure works)
  - [x] Test: Verify templates can store multiple layouts

- [x] **Update Study Dashboard Model**
  - [x] Add field to store active menu layouts (uses template structure)
  - [x] Copy menu layouts from template during initialization
  - [ ] Test: Verify study dashboards inherit layouts

#### 1.2 Frontend: Menu-Based Layout Switching
- [x] **Update Study Dashboard Page**
  - [x] Load menu layouts from dashboard configuration
  - [x] State management for current menu item
  - [x] Switch widget sets when menu clicked
  - [ ] Test: Menu navigation changes displayed widgets

- [x] **Widget Layout Storage**
  - [x] Store layouts in format: `{ [menuItemId]: WidgetLayout[] }`
  - [x] Default layout for unmapped menu items
  - [ ] Test: Layouts persist after page refresh

#### 1.3 API Updates
- [x] **Dashboard Configuration Endpoint**
  - [x] Return menu layouts in dashboard config
  - [x] Include widget configurations per menu item
  - [x] Test: API returns complete layout data

### Test Scenarios
- [ ] Create dashboard with 3 menu items (Overview, Safety, Demographics)
- [ ] Assign different widgets to each menu item
- [ ] Verify clicking menu items shows different widgets
- [ ] Verify layouts persist after refresh

---

## Phase 2: Study Dashboard Configuration ⭐ CRITICAL

### Overview
Replace hardcoded mock widgets with actual dashboard template configuration. When a study is initialized, it should use the selected template's widgets and layouts.

### Implementation Tasks

#### 2.1 Backend: Template to Study Configuration
- [x] **Study Initialization Updates**
  - [x] Copy complete widget layouts from template
  - [x] Apply study-specific customizations
  - [x] Store menu-widget mappings
  - [x] Test: Initialized study has template widgets

- [x] **Runtime Dashboard API**
  - [x] Load actual widget configurations
  - [x] Return study-specific dashboard config
  - [x] Include menu structure and layouts
  - [x] Test: API returns template-based config

#### 2.2 Frontend: Load Real Configuration
- [x] **Remove Hardcoded Widgets**
  - [x] Delete mock dashboard configuration
  - [x] Load configuration from API
  - [x] Handle loading states
  - [ ] Test: Dashboard shows template widgets

- [x] **Dynamic Widget Rendering**
  - [x] Render widgets based on configuration
  - [x] Support all widget types from template
  - [x] Handle missing widget types gracefully
  - [ ] Test: All template widgets render correctly

### Test Scenarios
- [ ] Initialize study with safety-focused template
- [ ] Verify dashboard shows safety widgets
- [ ] Initialize another study with operational template
- [ ] Verify different widget set loads

---

## Phase 3: Widget Data Connection ⭐ IMPORTANT

### Overview
Connect the widget data executor to runtime APIs. Replace mock data with real data queries based on widget configuration.

### Implementation Tasks

#### 3.1 Backend: Wire Data Executor
- [ ] **Update Runtime Widget Data Endpoint**
  - [ ] Import and use `widget_data_executor`
  - [ ] Remove mock data generation
  - [ ] Apply study field mappings
  - [ ] Test: API returns executor-generated data

- [ ] **Field Mapping Integration**
  - [ ] Load study-specific field mappings
  - [ ] Apply mappings to widget queries
  - [ ] Handle missing mappings
  - [ ] Test: Mapped fields query correctly

#### 3.2 Data Source Configuration
- [ ] **Connect to Study Data Sources**
  - [ ] Use study's data directory
  - [ ] Auto-discover available datasets
  - [ ] Cache dataset schemas
  - [ ] Test: Widgets show study data

- [ ] **Error Handling**
  - [ ] Handle missing datasets gracefully
  - [ ] Provide meaningful error messages
  - [ ] Fallback to mock data if needed
  - [ ] Test: Errors don't break dashboard

### Test Scenarios
- [ ] Configure widget to show ADSL count
- [ ] Verify count matches actual data
- [ ] Configure chart with ADAE data
- [ ] Verify chart displays real values

---

## Phase 4: Global Filter System ⭐ IMPORTANT

### Overview
Implement flexible global and local filtering system that adapts to each study's data structure.

### Implementation Tasks

#### 4.1 Filter Configuration
- [ ] **Template-Level Filter Definition**
  - [ ] Add `global_filters` to template structure
  - [ ] Support filter types: dropdown, multiselect, date range
  - [ ] Define target datasets and fields
  - [ ] Test: Templates store filter configs

- [ ] **Study-Level Filter Mapping**
  - [ ] UI for mapping template filters to study fields
  - [ ] Store mappings in study configuration
  - [ ] Support alternate field names
  - [ ] Test: Mappings persist and load

#### 4.2 Filter Components
- [ ] **Global Filter Bar Component**
  - [ ] Dynamic filter rendering based on config
  - [ ] Load filter options from data
  - [ ] State management for selected values
  - [ ] Test: Filters render and interact

- [ ] **Filter State Management**
  - [ ] Global filter context/store
  - [ ] Filter change propagation
  - [ ] URL state synchronization
  - [ ] Test: Filter state persists

#### 4.3 Filter Application
- [ ] **Widget Data Filtering**
  - [ ] Pass filters to data executor
  - [ ] Apply filters only to relevant datasets
  - [ ] Handle missing filter fields
  - [ ] Test: Data updates with filters

- [ ] **Cross-Widget Coordination**
  - [ ] All widgets receive filter updates
  - [ ] Loading states during filter changes
  - [ ] Cache filtered results
  - [ ] Test: All widgets filter together

### Advanced Filter Features
- [ ] **Filter Dependencies**
  - [ ] Country → Site → Subject cascading
  - [ ] Dynamic option updates
  - [ ] Test: Dependent filters update

- [ ] **Virtual Filters**
  - [ ] Age groups, derived categories
  - [ ] Custom SQL expressions
  - [ ] Test: Virtual filters apply correctly

- [ ] **Local Widget Filters**
  - [ ] Widget-specific filter UI
  - [ ] Combine with global filters
  - [ ] Test: Local and global filters work together

### Test Scenarios
- [ ] Add Site filter, verify all widgets filter
- [ ] Add Visit filter, verify only applicable widgets filter
- [ ] Test filter persistence across page navigation
- [ ] Test filter performance with large datasets

---

## Phase 5: UI Polish & Theming ⭐ IMPORTANT

### Overview
Match the dashboard UI to the reference screenshots with proper styling, dark theme, and layout.

### Implementation Tasks

#### 5.1 Dark Theme Implementation
- [ ] **Theme Configuration**
  - [ ] Create dark theme color palette
  - [ ] Update Tailwind configuration
  - [ ] Theme toggle functionality
  - [ ] Test: Theme applies consistently

- [ ] **Component Styling**
  - [ ] Update all components for dark theme
  - [ ] Ensure contrast accessibility
  - [ ] Fix any theme-specific issues
  - [ ] Test: All components look good in dark

#### 5.2 Widget Styling
- [ ] **Metric Cards**
  - [ ] Match reference screenshot styling
  - [ ] Add proper shadows and borders
  - [ ] Trend indicators and icons
  - [ ] Test: Metrics match reference

- [ ] **Charts & Tables**
  - [ ] Dark theme chart colors
  - [ ] Proper grid backgrounds
  - [ ] Table styling improvements
  - [ ] Test: Visualizations are readable

#### 5.3 Layout Improvements
- [ ] **Grid Spacing**
  - [ ] Match screenshot grid gaps
  - [ ] Consistent widget padding
  - [ ] Responsive breakpoints
  - [ ] Test: Layout matches reference

- [ ] **Navigation Styling**
  - [ ] Sidebar styling improvements
  - [ ] Active state indicators
  - [ ] Smooth transitions
  - [ ] Test: Navigation feels polished

### Test Scenarios
- [ ] Compare dashboard to reference screenshots
- [ ] Test in different screen sizes
- [ ] Verify dark theme consistency
- [ ] Check accessibility standards

---

## Testing & Validation

### End-to-End Test Workflow
1. **Admin Configuration**
   - [ ] Create menu template with Overview, Safety, Demographics
   - [ ] Create dashboard template using menu
   - [ ] Configure different widgets per menu item
   - [ ] Add global filters (Site, Treatment, Visit)

2. **Organization & Study Setup**
   - [ ] Create new organization "Test Pharma"
   - [ ] Create study "ABC-123"
   - [ ] Initialize with dashboard template
   - [ ] Map study fields to template fields

3. **End User Access**
   - [ ] Login as viewer/analyst
   - [ ] Access study dashboard
   - [ ] Verify menu navigation works
   - [ ] Verify widgets show data
   - [ ] Verify filters function

4. **Validation Checklist**
   - [ ] Menu items switch widget layouts ✓
   - [ ] Widgets display study-specific data ✓
   - [ ] Global filters affect all applicable widgets ✓
   - [ ] UI matches reference screenshots ✓
   - [ ] Performance is acceptable (<2s load) ✓

---

## Implementation Timeline

### Week 1
- Phase 1: Menu Navigation (2 days)
- Phase 2: Dashboard Configuration (2 days)
- Testing & Bug Fixes (1 day)

### Week 2
- Phase 3: Widget Data Connection (2 days)
- Phase 4: Filter System (3 days)

### Week 3
- Phase 5: UI Polish (2 days)
- End-to-End Testing (2 days)
- Documentation & Deployment (1 day)

---

## Technical Considerations

### Performance
- Widget data caching strategy
- Filter query optimization
- Lazy loading for large datasets
- Dashboard configuration caching

### Security
- Filter injection prevention
- Data access validation
- Widget-level permissions
- Audit trail for filter usage

### Scalability
- Support for 100+ widgets per dashboard
- Handle datasets with millions of rows
- Multiple concurrent users
- Real-time data updates

---

## Success Criteria

1. **Functional Requirements**
   - Admin can configure complete dashboards
   - Menu navigation switches widget views
   - Widgets display real study data
   - Filters work across all widgets
   - UI matches reference design

2. **Performance Requirements**
   - Dashboard loads in <2 seconds
   - Menu switches in <500ms
   - Filter updates in <1 second
   - Smooth UI interactions

3. **User Experience**
   - Intuitive navigation
   - Clear data visualization
   - Responsive design
   - Consistent theming

---

## Risk Mitigation

### Technical Risks
- **Data Volume**: Implement pagination and data sampling
- **Filter Complexity**: Start simple, add advanced features incrementally
- **Performance**: Add caching layers and optimize queries
- **Browser Compatibility**: Test across major browsers

### Process Risks
- **Scope Creep**: Stick to core features first
- **Testing Time**: Automate where possible
- **Integration Issues**: Test incrementally
- **User Adoption**: Provide clear documentation

---

## Next Steps

1. Review and approve implementation plan
2. Set up development environment
3. Begin Phase 1 implementation
4. Daily progress updates
5. Weekly stakeholder demos

This document will be updated as implementation progresses, with checkboxes marked upon completion and testing of each feature.