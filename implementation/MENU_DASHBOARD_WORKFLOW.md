# Menu & Dashboard Template Workflow

## Overview

This document describes the complete workflow for creating and using menu and dashboard templates in the Clinical Dashboard platform.

## Phase 1: Template Creation (System Admin)

### 1.1 Create Menu Templates
- **Purpose**: Define reusable navigation structures
- **Location**: Admin Panel → Menu Templates
- **Example**: "Phase 3 Oncology Standard Menu"
  ```
  📁 Overview
  📁 Safety Monitoring
    ├── Adverse Events
    ├── Serious Adverse Events
    └── Lab Abnormalities
  📁 Efficacy
    ├── Primary Endpoints
    └── Secondary Endpoints
  📁 Patient Management
    ├── Enrollment Status
    └── Visit Compliance
  ```
- **Key Features**:
  - Hierarchical structure (groups and items)
  - Role-based visibility per menu item
  - Icons for visual clarity
  - No dashboard assignments yet (just structure)

### 1.2 Create Widget Library
- **Purpose**: Build reusable visualization components
- **Location**: Admin Panel → Widget Library
- **Widget Types**:
  - Metric Cards (KPIs)
  - Line Charts (Trends)
  - Bar Charts (Comparisons)
  - Tables (Detailed Data)
  - Enrollment Maps (Geographic)
  - Patient Flow (Sankey)
  - Custom Widgets

### 1.3 Create Dashboard Templates
- **Purpose**: Design reusable dashboard layouts
- **Location**: Admin Panel → Dashboard Templates
- **Process**:
  1. Create new dashboard template
  2. Use drag-and-drop designer
  3. Add widgets from library
  4. Configure widget properties
  5. Set responsive grid layout
- **Example**: "Safety Overview Dashboard"
  - AE Summary metric card
  - AE trends line chart
  - SAE table
  - Lab abnormalities heatmap

## Phase 2: Study Configuration (Study Manager)

### 2.1 Study Creation
1. **Basic Information**
   - Study name, protocol, phase
   - Therapeutic area, indication
   - Start/end dates

2. **Select Menu Template**
   - Choose from available menu templates
   - Preview menu structure
   - Confirm selection

3. **Dashboard Assignment**
   - For each menu item:
     - Select appropriate dashboard template
     - Or create custom dashboard
   - Example mapping:
     ```
     Menu Item              → Dashboard Template
     Overview               → Executive Summary Dashboard
     Adverse Events         → AE Monitoring Dashboard
     Lab Abnormalities      → Lab Results Dashboard
     Primary Endpoints      → Efficacy Dashboard
     ```

4. **Widget Configuration**
   - For each dashboard:
     - Map widget data sources
     - Configure filters
     - Set refresh intervals
     - Define calculations

5. **Data Source Setup**
   - Configure data connections
   - Map fields to widgets
   - Set up data pipelines

## Phase 3: Runtime Experience (End Users)

### 3.1 User Access
- Login → Select Study → View Dashboard
- Navigation sidebar shows configured menu
- Role-based menu visibility applied

### 3.2 Dashboard Interaction
- Click menu item → Load associated dashboard
- Widgets display real-time data
- Interactive filters and drill-downs
- Export capabilities

## Benefits of This Approach

### 1. Reusability
- Menu templates can be used across similar studies
- Dashboard templates save design time
- Widgets are shared components

### 2. Standardization
- Consistent navigation patterns
- Uniform dashboard layouts
- Best practices encoded in templates

### 3. Flexibility
- Templates are starting points
- Can customize per study
- Mix template and custom dashboards

### 4. Efficiency
- Faster study setup
- Reduced configuration errors
- Clear separation of concerns

## Technical Implementation

### Backend Models
```python
# Menu Template - Just structure
MenuTemplate:
  - code: str
  - name: str
  - menu_structure: List[MenuItem]
  
# Dashboard Template - Widget layouts
DashboardTemplate:
  - code: str
  - name: str
  - layout: List[WidgetConfig]
  
# Study Configuration - Links everything
StudyDashboard:
  - study_id: UUID
  - menu_template_id: UUID
  - dashboard_assignments: Dict[menu_item_id, dashboard_id]
```

### Frontend Flow
1. Menu designer creates structure
2. Dashboard designer creates layouts
3. Study config wizard links them
4. Runtime renders based on config

## Best Practices

1. **Menu Design**
   - Keep hierarchy shallow (max 3 levels)
   - Use clear, consistent naming
   - Group related items
   - Consider user workflows

2. **Dashboard Design**
   - Focus on key metrics
   - Use appropriate visualizations
   - Maintain visual hierarchy
   - Design for different screen sizes

3. **Template Management**
   - Version control templates
   - Document template purposes
   - Regular review and updates
   - Gather user feedback

## Future Enhancements

1. **Template Marketplace**
   - Share templates across organizations
   - Industry-standard templates
   - Template ratings and reviews

2. **AI-Assisted Configuration**
   - Suggest menu structures based on study type
   - Recommend dashboard layouts
   - Auto-map data fields

3. **Advanced Customization**
   - Custom widget development
   - Dynamic menu generation
   - Conditional dashboard elements