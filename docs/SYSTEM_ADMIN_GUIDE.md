# System Administrator Guide - Cortex Clinical Dashboard Platform

## Table of Contents

1. [Introduction](#introduction)
2. [Platform Overview](#platform-overview)
3. [Complete Setup Workflow](#complete-setup-workflow)
   - [Phase 1: Initial System Setup](#phase-1-initial-system-setup)
   - [Phase 2: Create Dashboard Template](#phase-2-create-dashboard-template)
   - [Phase 3: Create Study](#phase-3-create-study)
   - [Phase 4: Study Initialization](#phase-4-study-initialization)
   - [Phase 5: Data Setup & Pipeline](#phase-5-data-setup--pipeline)
   - [Phase 6: Verification & Go-Live](#phase-6-verification--go-live)
4. [Best Practices](#best-practices)
5. [Troubleshooting](#troubleshooting)
6. [Appendix](#appendix)

---

## Introduction

This guide provides step-by-step instructions for System Administrators to set up and configure the Cortex Clinical Dashboard Platform for new clients and studies. The example workflow demonstrates setting up a client called "SAGAR" with a study "DEMO101".

### Prerequisites
- System Administrator access (system_admin role)
- Access to client's data specifications
- Understanding of clinical trial data structures (CDISC SDTM/ADaM)

### Time Estimate
- Complete setup: 30-45 minutes
- Template creation: 15-20 minutes
- Study initialization: 10-15 minutes

---

## Platform Overview

### Architecture
The platform follows a template-based approach:
1. **Dashboard Templates** - Reusable dashboard configurations including menus and widgets
2. **Studies** - Individual clinical trials that use dashboard templates
3. **Organizations** - Client companies that own studies
4. **Data Pipeline** - Automated data ingestion and processing

### Key Concepts
- **Unified Templates**: Menu structure + dashboard layouts + widgets in one template
- **Data Contracts**: Widgets declare their data requirements
- **Field Mapping**: Map study-specific fields to template requirements
- **Role-Based Access**: Control who sees what at menu and widget level

---

## Complete Setup Workflow

### Example Scenario
**Client**: SAGAR  
**Study**: DEMO101  
**Requirements**: 
- 3 main menus: Overview, Adverse Events (with 2 submenus), Lab Data
- 15 total widgets across all dashboards
- Safety-focused monitoring

---

## Phase 1: Initial System Setup

### Step 1.1: Create Organization

**Navigation**: `/organizations` → "New Organization"

**Form Details**:
```yaml
Organization Name: SAGAR
Subdomain: sagar
Contact Email: admin@sagar.com
Settings:
  timezone: "America/New_York"
  date_format: "MM/DD/YYYY"
  fiscal_year_start: "January"
```

**Visual Interface**:
```
┌─────────────────────────────────────┐
│       Create New Organization       │
├─────────────────────────────────────┤
│ Name:     [SAGAR                ]   │
│ Subdomain:[sagar                ]   │
│ Email:    [admin@sagar.com      ]   │
│                                     │
│ Advanced Settings:                  │
│ Timezone: [America/New_York ▼  ]   │
│ Date Format: [MM/DD/YYYY ▼     ]   │
│                                     │
│         [Cancel] [Create]           │
└─────────────────────────────────────┘
```

### Step 1.2: Create Organization Admin

**Navigation**: `/admin/users` → "New User"

**Form Details**:
```yaml
Full Name: John Smith
Email: john.smith@sagar.com
Role: org_admin
Organization: SAGAR
Temporary Password: Welcome123!
Force Password Change: Yes
Send Welcome Email: Yes
```

**Access Permissions for org_admin**:
- Manage users within organization
- View all studies in organization
- Cannot create/modify dashboard templates
- Cannot access system settings

---

## Phase 2: Create Dashboard Template

### Step 2.1: Navigate to Template Designer

**Navigation**: `/admin/dashboard-templates` → "New Template"

### Step 2.2: Configure Template Metadata

**Template Information**:
```yaml
Template Name: SAGAR Clinical Safety Dashboard
Description: Comprehensive safety monitoring dashboard for SAGAR clinical trials
Category: Safety Monitoring
Tags: 
  - safety
  - adverse-events
  - laboratory
  - phase-2
  - oncology
Version: 1.0
Status: Active
```

### Step 2.3: Design Menu Structure

**Menu Hierarchy**:
```
📊 Overview
📋 Adverse Events
   ├─ AE Listing
   └─ AE Summary
🧪 Lab Data
```

**Visual Designer - Menu Panel**:
```
┌─────────────────────────────┐
│ MENU STRUCTURE              │
├─────────────────────────────┤
│ 📊 Overview                 │
│ 📋 Adverse Events ▼         │
│   ├─ AE Listing             │
│   └─ AE Summary             │
│ 🧪 Lab Data                 │
│                             │
│ [+ Add Menu Item]           │
│                             │
│ Menu Item Settings:         │
│ Name: [Overview        ]    │
│ Icon: [📊 Dashboard ▼  ]    │
│ Type: [Dashboard Page ▼]    │
│ Visible to Roles:           │
│ ☑ All Roles                │
└─────────────────────────────┘
```

### Step 2.4: Design Dashboard Layouts

#### Overview Dashboard Configuration

**Layout Grid**: 12 columns x 12 rows

**Widget Placement**:
```
┌─────────────────────────────────────────────────────────────┐
│                        Overview Dashboard                    │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│ │ Enrollment  │ │   Safety    │ │ Completion  │           │
│ │   Metrics   │ │    Score    │ │    Rate     │           │
│ │  (0,0,4,2)  │ │  (4,0,4,2)  │ │  (8,0,4,2)  │           │
│ └─────────────┘ └─────────────┘ └─────────────┘           │
│                                                             │
│ ┌───────────────────────────────────────────────┐         │
│ │          Enrollment Timeline                   │         │
│ │          Line Chart Widget                     │         │
│ │              (0,2,12,4)                        │         │
│ └───────────────────────────────────────────────┘         │
│                                                             │
│ ┌───────────────────────────────────────────────┐         │
│ │          Site Enrollment Map                   │         │
│ │          Geographic Widget                     │         │
│ │              (0,6,12,6)                        │         │
│ └───────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

**Widget Configurations**:

1. **Enrollment Metrics Widget**
```yaml
Type: metric-card
Position: {x: 0, y: 0, width: 4, height: 2}
Configuration:
  title: "Total Enrollment"
  data_source: "demographics"
  calculation:
    type: "count"
    field: "subject_id"
    distinct: true
  display:
    format: "number"
    show_trend: true
    trend_period: "last_30_days"
  thresholds:
    target: 150
    warning: 120
    critical: 100
```

2. **Safety Score Widget**
```yaml
Type: metric-card
Position: {x: 4, y: 0, width: 4, height: 2}
Configuration:
  title: "Safety Score"
  data_source: "calculated"
  calculation:
    formula: "100 - (serious_ae_count / total_subjects * 100)"
  display:
    format: "percentage"
    decimals: 1
    color_scheme: "reverse" # Higher is better
```

3. **Enrollment Timeline Widget**
```yaml
Type: line-chart
Position: {x: 0, y: 2, width: 12, height: 4}
Configuration:
  title: "Enrollment Over Time"
  data_source: "demographics"
  x_axis:
    field: "enrollment_date"
    type: "date"
    format: "MMM YYYY"
  y_axis:
    field: "subject_id"
    type: "cumulative_count"
  series:
    - name: "Actual"
      color: "#2563eb"
    - name: "Target"
      type: "projection"
      color: "#dc2626"
      dashed: true
```

#### AE Listing Dashboard Configuration

**Widget Placement**:
```
┌─────────────────────────────────────────────────────────────┐
│                     AE Listing Dashboard                     │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────────────┐ ┌─────────────────────┐           │
│ │  AE by Severity     │ │    Recent AEs      │           │
│ │   Bar Chart         │ │   Metric Card      │           │
│ │    (0,0,6,3)        │ │    (6,0,6,3)       │           │
│ └─────────────────────┘ └─────────────────────┘           │
│                                                             │
│ ┌───────────────────────────────────────────────┐         │
│ │         Adverse Events Detail Table            │         │
│ │                                                │         │
│ │  Subject | AE Term | Severity | Start | Status │         │
│ │  --------|---------|----------|-------|------- │         │
│ │  001     | Nausea  | Mild     | 01/15 | Ongng  │         │
│ │  002     | Fatigue | Moderate | 01/18 | Resol  │         │
│ │                 (0,3,12,6)                     │         │
│ └───────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

**AE Detail Table Configuration**:
```yaml
Type: data-table
Position: {x: 0, y: 3, width: 12, height: 6}
Configuration:
  title: "Adverse Events Details"
  data_source: "adverse_events"
  columns:
    - field: "subject_id"
      label: "Subject ID"
      width: 100
      sortable: true
    - field: "ae_term"
      label: "AE Term"
      width: 200
      sortable: true
      filterable: true
    - field: "severity"
      label: "Severity"
      width: 100
      sortable: true
      filterable: true
      color_coding:
        mild: "#22c55e"
        moderate: "#f59e0b"
        severe: "#ef4444"
    - field: "start_date"
      label: "Start Date"
      width: 100
      format: "MM/DD/YYYY"
    - field: "status"
      label: "Status"
      width: 100
  features:
    - pagination
    - export_csv
    - column_resize
    - row_selection
  filters:
    default:
      - field: "status"
        operator: "equals"
        value: "ongoing"
```

#### AE Summary Dashboard Configuration

**Widgets**:
1. AE by System Organ Class (Pie Chart)
2. AE Trends Over Time (Line Chart)
3. Top 10 Most Frequent AEs (Horizontal Bar Chart)
4. Serious AE Summary (Metric Card)

#### Lab Data Dashboard Configuration

**Widgets**:
1. Lab Abnormalities Count (Metric Card)
2. Lab Values Heatmap (Heatmap)
3. Lab Parameters Trends (Multi-line Chart)
4. Lab Results Table (Data Table)

### Step 2.5: Define Data Requirements

**Consolidated Data Contract**:
```yaml
Required Datasets:
  demographics:
    source: "DM"
    required_fields:
      - field: "USUBJID"
        maps_to: "subject_id"
        type: "string"
      - field: "ARM"
        maps_to: "treatment_arm"
        type: "string"
      - field: "RFSTDTC"
        maps_to: "enrollment_date"
        type: "date"
    optional_fields:
      - field: "RFENDTC"
        maps_to: "completion_date"
        type: "date"

  adverse_events:
    source: "AE"
    required_fields:
      - field: "USUBJID"
        maps_to: "subject_id"
        type: "string"
      - field: "AETERM"
        maps_to: "ae_term"
        type: "string"
      - field: "AESEV"
        maps_to: "severity"
        type: "string"
        valid_values: ["MILD", "MODERATE", "SEVERE"]
      - field: "AESTDTC"
        maps_to: "start_date"
        type: "date"

  laboratory:
    source: "LB"
    required_fields:
      - field: "USUBJID"
        maps_to: "subject_id"
        type: "string"
      - field: "LBTEST"
        maps_to: "lab_test"
        type: "string"
      - field: "LBSTRESN"
        maps_to: "lab_value"
        type: "numeric"
      - field: "VISITNUM"
        maps_to: "visit_number"
        type: "numeric"
```

### Step 2.6: Save and Validate Template

**Actions**:
1. Click "Validate Template" - Checks for:
   - All widgets have required configurations
   - Data requirements are complete
   - No circular menu references
   - Valid role assignments

2. Click "Preview Template" - Shows live preview

3. Click "Save Template"
   - Status: "SAGAR Clinical Safety Dashboard created successfully"
   - Template ID: `sagar-safety-dashboard-v1`

---

## Phase 3: Create Study

### Step 3.1: Navigate to Study Creation

**Navigation**: `/studies` → "New Study"

### Step 3.2: Enter Study Information

**Basic Information Tab**:
```yaml
Study Name: DEMO101
Protocol Number: SAGAR-DEMO-101
Phase: Phase 2
Status: Active
Therapeutic Area: Oncology
Indication: Non-Small Cell Lung Cancer
Sponsor: SAGAR Pharmaceuticals
```

**Timeline Tab**:
```yaml
First Patient In: 2024-01-15
Last Patient In: 2024-06-30
Last Patient Out: 2025-06-30
Database Lock: 2025-08-31
```

**Enrollment Tab**:
```yaml
Planned Enrollment: 150
Sites: 12
Countries: 
  - United States (8 sites)
  - Canada (4 sites)
```

**Organization Assignment**:
```yaml
Organization: SAGAR
Study Manager: John Smith (john.smith@sagar.com)
```

### Step 3.3: Save Study

**Result**:
- Study ID: `demo101`
- Status: Created (Pending Initialization)
- Next Step: Initialize Dashboard

---

## Phase 4: Study Initialization

### Step 4.1: Start Initialization Wizard

**Navigation**: `/studies/DEMO101/initialize`

**Initialization Wizard Overview**:
```
┌─────────────────────────────────────────────────────┐
│           Study Initialization Wizard               │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Step 1: Select Dashboard Template      ━━━━━━     │
│  Step 2: Map Data Fields               ░░░░░░     │
│  Step 3: Review & Activate             ░░░░░░     │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Step 4.2: Select Dashboard Template

**Template Selection Screen**:
```
┌─────────────────────────────────────────────────────────────┐
│             Select Dashboard Template                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Filter by: [All Categories ▼] [All Tags ▼]                 │
│                                                             │
│ ┌────────────────────────────┐ ┌────────────────────────┐  │
│ │ 🔒 SAGAR Clinical Safety   │ │ 📊 Oncology Standard   │  │
│ │    Dashboard               │ │                        │  │
│ │                            │ │                        │  │
│ │ ✓ Custom for SAGAR        │ │ • Generic template     │  │
│ │ ✓ Safety focused          │ │ • Full suite           │  │
│ │ ✓ 4 dashboards            │ │ • 8 dashboards         │  │
│ │ ✓ 15 widgets              │ │ • 32 widgets           │  │
│ │                            │ │                        │  │
│ │ Requirements:              │ │ Requirements:          │  │
│ │ • DM, AE, LB datasets     │ │ • DM, AE, LB, VS, EX   │  │
│ │                            │ │                        │  │
│ │      [Preview] [Select ✓]  │ │      [Preview] [Select]│  │
│ └────────────────────────────┘ └────────────────────────┘  │
│                                                             │
│                              [Back] [Next: Map Data]        │
└─────────────────────────────────────────────────────────────┘
```

**Action**: Select "SAGAR Clinical Safety Dashboard"

### Step 4.3: Map Data Fields

**Data Mapping Interface**:
```
┌────────────────────────────────────────────────────────────────┐
│                    Data Field Mapping                           │
├────────────────────────────────────────────────────────────────┤
│ Auto-Mapping: 12 of 12 fields mapped automatically ✅          │
│                                                                │
│ [🔄 Re-scan] [📋 Import Mapping] [💾 Export Mapping]           │
│                                                                │
│ DEMOGRAPHICS (DM) - Source: /data/DEMO101/dm.sas7bdat          │
│ ┌──────────────────────┬─────────────────────┬──────────┐    │
│ │ Template Field       │ Your Data Field     │ Status   │    │
│ ├──────────────────────┼─────────────────────┼──────────┤    │
│ │ subject_id           │ USUBJID ✓           │ ✅ Auto   │    │
│ │ enrollment_date      │ RFSTDTC ✓           │ ✅ Auto   │    │
│ │ treatment_arm        │ ARM ✓               │ ✅ Auto   │    │
│ │ completion_date      │ RFENDTC ✓           │ ✅ Auto   │    │
│ └──────────────────────┴─────────────────────┴──────────┘    │
│                                                                │
│ ADVERSE EVENTS (AE) - Source: /data/DEMO101/ae.sas7bdat       │
│ ┌──────────────────────┬─────────────────────┬──────────┐    │
│ │ Template Field       │ Your Data Field     │ Status   │    │
│ ├──────────────────────┼─────────────────────┼──────────┤    │
│ │ subject_id           │ USUBJID ✓           │ ✅ Auto   │    │
│ │ ae_term              │ AETERM ✓            │ ✅ Auto   │    │
│ │ severity             │ AESEV ✓             │ ✅ Auto   │    │
│ │ start_date           │ AESTDTC ✓           │ ✅ Auto   │    │
│ │ serious_flag         │ AESER ✓             │ ✅ Auto   │    │
│ └──────────────────────┴─────────────────────┴──────────┘    │
│                                                                │
│ LABORATORY (LB) - Source: /data/DEMO101/lb.sas7bdat           │
│ ┌──────────────────────┬─────────────────────┬──────────┐    │
│ │ Template Field       │ Your Data Field     │ Status   │    │
│ ├──────────────────────┼─────────────────────┼──────────┤    │
│ │ subject_id           │ USUBJID ✓           │ ✅ Auto   │    │
│ │ lab_test             │ LBTEST ✓            │ ✅ Auto   │    │
│ │ lab_value            │ LBSTRESN ✓          │ ✅ Auto   │    │
│ │ visit_number         │ VISITNUM ✓          │ ✅ Auto   │    │
│ └──────────────────────┴─────────────────────┴──────────┘    │
│                                                                │
│ ✅ All required fields mapped successfully!                    │
│                                                                │
│                    [Back] [Next: Review & Activate]            │
└────────────────────────────────────────────────────────────────┘
```

**Manual Mapping (if needed)**:
- Click dropdown next to unmapped field
- Select from available columns
- System shows data type compatibility

### Step 4.4: Review and Activate

**Review Configuration Screen**:
```
┌─────────────────────────────────────────────────────────────┐
│                 Review Study Configuration                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Study Information:                                          │
│ ┌───────────────────────────────────────────────────────┐  │
│ │ Study: DEMO101 (SAGAR-DEMO-101)                       │  │
│ │ Organization: SAGAR                                    │  │
│ │ Template: SAGAR Clinical Safety Dashboard              │  │
│ │ Status: Ready to Activate                              │  │
│ └───────────────────────────────────────────────────────┘  │
│                                                             │
│ Dashboard Structure:                                         │
│ ┌───────────────────────────────────────────────────────┐  │
│ │ 📊 Overview                    4 widgets               │  │
│ │ 📋 Adverse Events                                      │  │
│ │    ├─ AE Listing              3 widgets               │  │
│ │    └─ AE Summary              4 widgets               │  │
│ │ 🧪 Lab Data                    4 widgets               │  │
│ │                                                        │  │
│ │ Total: 4 dashboards, 15 widgets                        │  │
│ └───────────────────────────────────────────────────────┘  │
│                                                             │
│ Data Configuration:                                         │
│ ┌───────────────────────────────────────────────────────┐  │
│ │ Demographics (DM): 4 fields mapped ✅                  │  │
│ │ Adverse Events (AE): 5 fields mapped ✅                │  │
│ │ Laboratory (LB): 4 fields mapped ✅                    │  │
│ │                                                        │  │
│ │ Data Pipeline: Not configured (configure after)        │  │
│ └───────────────────────────────────────────────────────┘  │
│                                                             │
│ Pre-Activation Checklist:                                   │
│ ☑ Dashboard template selected                               │
│ ☑ All required fields mapped                                │
│ ☑ User permissions configured                               │
│ ☐ Data pipeline configured (optional)                       │
│                                                             │
│ ⚠️ Activating will make the dashboard available to users    │
│                                                             │
│           [Back] [Save Draft] [🚀 Activate Study]           │
└─────────────────────────────────────────────────────────────┘
```

**Action**: Click "Activate Study"

**Result**:
- Status: Study Activated Successfully
- Dashboard URL: `/studies/DEMO101/dashboard`
- Next Step: Configure Data Pipeline

---

## Phase 5: Data Setup & Pipeline

### Step 5.1: Configure Data Source

**Navigation**: `/studies/DEMO101/data-sources` → "Add Data Source"

**Data Source Configuration**:
```yaml
Type: SFTP
Name: SAGAR EDC Daily Export
Description: Automated daily export from Medidata Rave

Connection Details:
  Host: sftp.sagar-clinical.com
  Port: 22
  Username: demo101_user
  Password: [Encrypted]
  Base Path: /exports/DEMO101/
  
File Configuration:
  File Pattern: "*.sas7bdat"
  Date Pattern: "YYYYMMDD"
  Expected Files:
    - dm.sas7bdat
    - ae.sas7bdat
    - lb.sas7bdat
    
Schedule:
  Frequency: Daily
  Time: 02:00 EST
  Retry: 3 times, 30 min interval
  
Processing:
  Validation: Yes
  Duplicate Check: Yes
  Archive After: 30 days
```

### Step 5.2: Test Connection

**Test Results**:
```
┌─────────────────────────────────────────┐
│         Connection Test Results         │
├─────────────────────────────────────────┤
│ ✅ Connection successful                │
│ ✅ Authentication successful            │
│ ✅ Path accessible                      │
│ ✅ Files found:                         │
│    • dm_20240715.sas7bdat (2.1 MB)    │
│    • ae_20240715.sas7bdat (4.5 MB)    │
│    • lb_20240715.sas7bdat (8.3 MB)    │
│                                         │
│         [Close] [Configure Pipeline]    │
└─────────────────────────────────────────┘
```

### Step 5.3: Run Initial Data Load

**Manual Import Process**:
```
┌─────────────────────────────────────────────────┐
│           Initial Data Import                    │
├─────────────────────────────────────────────────┤
│                                                 │
│ Selected Files:                                 │
│ ☑ dm_20240715.sas7bdat                        │
│ ☑ ae_20240715.sas7bdat                        │
│ ☑ lb_20240715.sas7bdat                        │
│                                                 │
│ Import Options:                                 │
│ ☑ Validate data quality                        │
│ ☑ Generate import report                       │
│ ☐ Send notification on completion              │
│                                                 │
│              [Cancel] [Start Import]            │
└─────────────────────────────────────────────────┘
```

**Import Progress**:
```
┌─────────────────────────────────────────────────┐
│              Import Progress                     │
├─────────────────────────────────────────────────┤
│                                                 │
│ Demographics (DM):                              │
│ [████████████████████] 100% - 87 records       │
│ ✅ Validation passed                            │
│                                                 │
│ Adverse Events (AE):                            │
│ [████████████████████] 100% - 342 records      │
│ ✅ Validation passed                            │
│                                                 │
│ Laboratory (LB):                                │
│ [████████████████████] 100% - 1,245 records    │
│ ⚠️ 3 records with missing VISITNUM             │
│                                                 │
│ Overall Status: Completed with warnings         │
│                                                 │
│         [View Report] [Close]                   │
└─────────────────────────────────────────────────┘
```

### Step 5.4: Configure Automated Pipeline

**Pipeline Rules**:
```yaml
Processing Rules:
  - Name: "Missing Visit Number"
    Condition: "LB.VISITNUM is NULL"
    Action: "Set to 99 (Unscheduled)"
    
  - Name: "Future Dates"
    Condition: "Any date > Today"
    Action: "Flag for review"
    
  - Name: "Duplicate Records"
    Condition: "Same USUBJID + VISITNUM + Test"
    Action: "Keep latest, archive others"

Notifications:
  On Success:
    - Email: data-team@sagar.com
    - Dashboard: Show green status
    
  On Error:
    - Email: admin@sagar.com, data-team@sagar.com
    - Dashboard: Show red alert
    - Action: Pause subsequent runs
```

---

## Phase 6: Verification & Go-Live

### Step 6.1: Verify Dashboard Access

**Test User Access**:
1. Login as different user roles
2. Verify menu visibility based on permissions
3. Check widget data display
4. Test filters and interactions

**Access Matrix**:
```
┌─────────────────┬────────┬────────┬────────┬────────┐
│ Menu/Feature    │ Viewer │ Analyst│ Manager│ Admin  │
├─────────────────┼────────┼────────┼────────┼────────┤
│ Overview        │   ✅    │   ✅    │   ✅    │   ✅    │
│ AE Listing      │   ✅    │   ✅    │   ✅    │   ✅    │
│ AE Summary      │   ❌    │   ✅    │   ✅    │   ✅    │
│ Lab Data        │   ❌    │   ✅    │   ✅    │   ✅    │
│ Export Data     │   ❌    │   ✅    │   ✅    │   ✅    │
│ Configure       │   ❌    │   ❌    │   ❌    │   ✅    │
└─────────────────┴────────┴────────┴────────┴────────┘
```

### Step 6.2: Final Dashboard View

**End User Experience**:
```
┌─────────────────────────────────────────────────────────────────┐
│ DEMO101 - Clinical Safety Dashboard              John Smith 👤  │
├───────────────────┬─────────────────────────────────────────────┤
│                   │  ┌─────────┐ ┌─────────┐ ┌─────────┐     │
│ 📊 Overview       │  │   87    │ │  94.2   │ │  78.5%  │     │
│                   │  │Enrolled │ │ Safety  │ │Complete │     │
│ 📋 Adverse Events ▼│  │ ↑12%    │ │  Score  │ │         │     │
│   ├─ AE Listing   │  └─────────┘ └─────────┘ └─────────┘     │
│   └─ AE Summary   │                                           │
│                   │  Enrollment Timeline                       │
│ 🧪 Lab Data       │  [═══════════════════════════════]        │
│                   │   Jan  Feb  Mar  Apr  May  Jun  Jul       │
│                   │                                           │
│ ─────────────     │  ┌─── Site Enrollment Map ─────────┐      │
│                   │  │                                 │      │
│ 🔔 Notifications  │  │    [US Map with site dots]     │      │
│ ⚙️ Settings       │  │                                 │      │
│ 📤 Export         │  └─────────────────────────────────┘      │
│                   │                                           │
│ Last Updated:     │  Data Quality: ████████░░ 87%              │
│ 07/15 02:35 AM    │                                           │
└───────────────────┴─────────────────────────────────────────────┘
```

### Step 6.3: Documentation and Training

**Create Study-Specific Documentation**:
1. Dashboard User Guide
2. Data Dictionary
3. Calculation Definitions
4. FAQ Document

**Training Sessions**:
- End Users: 30-minute dashboard navigation
- Data Managers: 45-minute data pipeline overview
- Study Managers: 60-minute full platform training

---

## Best Practices

### Template Design
1. **Start Generic**: Create templates that can work for multiple studies
2. **Think Modular**: Design widgets that can be reused
3. **Plan for Growth**: Leave space for additional widgets
4. **Document Logic**: Include calculation formulas in widget descriptions

### Data Management
1. **Validate Early**: Set up data validation rules before import
2. **Archive Regularly**: Keep only recent data in active tables
3. **Monitor Quality**: Set up automated data quality checks
4. **Version Control**: Track changes to mappings and calculations

### Performance
1. **Optimize Queries**: Index frequently filtered fields
2. **Cache Appropriately**: Set refresh intervals based on data update frequency
3. **Limit Real-time**: Use scheduled calculations for complex metrics
4. **Monitor Usage**: Track slow queries and optimize

### Security
1. **Least Privilege**: Give users minimum required access
2. **Audit Everything**: Enable audit logs for all data access
3. **Encrypt Sensitive**: Use field-level encryption for PII
4. **Regular Reviews**: Quarterly access reviews

---

## Troubleshooting

### Common Issues

#### Issue: Widgets show "No Data"
**Causes**:
- Field mapping incorrect
- Data not yet loaded
- Filter excluding all records
- User lacks permission

**Solution**:
1. Check field mappings in study configuration
2. Verify data import completed successfully
3. Review widget filters
4. Check user role permissions

#### Issue: Dashboard loads slowly
**Causes**:
- Too many widgets on one dashboard
- Complex calculations
- Large datasets without filters
- Network latency

**Solution**:
1. Split dashboard into multiple pages
2. Pre-calculate complex metrics
3. Add default filters
4. Enable caching

#### Issue: Data import fails
**Causes**:
- Connection timeout
- File format changed
- Validation rules too strict
- Disk space full

**Solution**:
1. Check connection settings
2. Verify file structure matches expected
3. Review validation rules
4. Check system resources

---

## Appendix

### A. Glossary

| Term | Definition |
|------|------------|
| Dashboard Template | Reusable configuration of menus, dashboards, and widgets |
| Data Contract | Widget's declaration of required data fields |
| Field Mapping | Linking study data fields to template requirements |
| Widget | Individual visualization component (chart, table, etc.) |
| Pipeline | Automated data import and processing workflow |

### B. CDISC Field Mappings

**Standard Demographics (DM) Mappings**:
- USUBJID → subject_id
- SITEID → site_id
- ARM/ACTARM → treatment_arm
- RFSTDTC → enrollment_date
- RFENDTC → completion_date

**Standard Adverse Events (AE) Mappings**:
- AETERM → ae_term
- AESEV → severity
- AESTDTC → start_date
- AEENDTC → end_date
- AESER → serious_flag

### C. Widget Types Reference

| Widget Type | Best For | Data Requirements |
|-------------|----------|-------------------|
| Metric Card | KPIs, single values | 1 numeric field |
| Line Chart | Trends over time | Date + value fields |
| Bar Chart | Comparisons | Category + value |
| Pie Chart | Proportions | Category + value |
| Data Table | Detailed records | Multiple fields |
| Heatmap | Patterns | 2 dimensions + value |
| Geographic | Location data | Coordinates/regions |

### D. Keyboard Shortcuts

| Action | Windows/Linux | Mac |
|--------|---------------|-----|
| Save | Ctrl+S | Cmd+S |
| Preview | Ctrl+P | Cmd+P |
| Duplicate | Ctrl+D | Cmd+D |
| Delete | Delete | Delete |
| Undo | Ctrl+Z | Cmd+Z |
| Redo | Ctrl+Y | Cmd+Shift+Z |

### E. Support Resources

**Documentation**:
- Platform User Guide: `/docs/user-guide`
- API Reference: `/docs/api`
- Video Tutorials: `/docs/videos`

**Support Channels**:
- Email: support@cortexdashboard.com
- Phone: 1-800-CORTEX-1
- Chat: Available in platform
- Training: training@cortexdashboard.com

---

*Last Updated: January 2024*  
*Version: 1.0*  
*Document ID: SYSADMIN-GUIDE-001*