# Clinical Dashboard Platform - User Manual

## Table of Contents

1. [Study Management](#study-management)
   - [Creating a Study](#creating-a-study)
   - [Study Initialization](#study-initialization)
   - [Study Configuration](#study-configuration)
   - [Managing Study Data](#managing-study-data)
2. [Dashboard Designer](#dashboard-designer)
   - [Overview](#overview)
   - [Creating a Dashboard](#creating-a-dashboard)
   - [Editing Dashboards](#editing-dashboards)
   - [Widget Types](#widget-types)
   - [Widget Configuration](#widget-configuration)
   - [Responsive Design](#responsive-design)

## Study Management

### Creating a Study

Studies are the core organizational unit in the Clinical Dashboard Platform. Each study represents a clinical trial with its own data, dashboards, and configuration.

#### Prerequisites
- Organization Admin or System Admin role
- Organization must exist in the system

#### Steps to Create a Study
1. Navigate to **Studies** in the main navigation
2. Click **Create New Study** button
3. Fill in the required information:
   - **Study Name**: Descriptive name for the study
   - **Study Code**: Short identifier (e.g., "COV-VAC-P3")
   - **Protocol Number**: Unique protocol identifier
   - **Phase**: Select the clinical trial phase
   - **Therapeutic Area**: Disease or condition area
   - **Description**: Detailed description of the study
4. Click **Create Study**
5. You'll be redirected to the study initialization wizard

### Study Initialization

After creating a study, it needs to be initialized before data can be loaded and dashboards configured.

#### What Happens During Initialization
The initialization process sets up:
- Default folder structure for study data
- Pipeline configuration for data processing
- Dashboard templates (if selected)
- Data source configurations
- Compliance settings (21 CFR Part 11, GDPR, HIPAA)
- Default dashboard configuration

#### Using the Initialization Wizard
1. After creating a study, you're automatically directed to the initialization wizard
2. **Step 1: Select Dashboard Template**
   - Choose from available templates (Safety, Efficacy, Enrollment, etc.)
   - Or skip to configure manually later
3. **Step 2: Configure Data Sources** (Optional)
   - Set up connections to data sources
   - Configure folder paths for data uploads
4. **Step 3: Review and Activate**
   - Review all settings
   - Click **Complete Setup** to initialize the study

#### Manual Initialization via API
For programmatic initialization, use the POST endpoint:
```
POST /api/v1/studies/{study_id}/initialize
```

Request body:
```json
{
  "dashboard_template_id": "uuid-of-template",
  "data_source_config": {
    "primary": {
      "type": "folder",
      "path": "/custom/path"
    }
  },
  "pipeline_config": {
    "frequency": "daily",
    "start_time": "02:00"
  },
  "auto_configure": true
}
```

### Study Configuration

After initialization, you can further configure your study settings.

#### Accessing Study Configuration
1. Navigate to **Studies**
2. Click on your study name
3. Click **Settings** or **Configure** button

#### Configuration Options
- **General Settings**
  - Study dates and timeline
  - Status management (Active, Paused, Completed)
  - Data retention policies
- **Dashboard Configuration**
  - Apply or change dashboard templates
  - Configure field mappings
  - Customize widget settings
- **Pipeline Settings**
  - Data refresh frequency
  - Processing stages
  - Error handling
- **Compliance Settings**
  - Audit trail configuration
  - Electronic signature requirements
  - Data integrity rules

### Managing Study Data

#### Data Sources
Studies can receive data from multiple sources:
- **Folder Upload**: Manual file uploads to designated folders
- **API Integration**: Direct API connections to EDC systems
- **SFTP**: Automated file transfers from external systems

#### Data Organization
Study data is organized in a standardized folder structure:
```
/data/studies/{org_id}/{study_id}/
├── source_data/        # Raw data files
├── processed_data/     # Transformed data
├── exports/           # Generated reports
└── archives/          # Historical data
```

#### Monitoring Data Flow
1. Go to **Studies > [Your Study] > Data Sources**
2. View status of each data source
3. Check last update times
4. Monitor for errors or warnings

## Dashboard Designer

### Overview

The Dashboard Designer is a powerful drag-and-drop interface for creating custom dashboards for your clinical studies. Built with React Grid Layout, it provides an intuitive way to design and configure dashboards without writing code.

### Accessing the Dashboard Designer

1. Navigate to **Admin > Dashboards** in the sidebar (System Admin only)
2. You'll see a list of all dashboard templates
3. Click **Create Dashboard** to start designing a new dashboard

### Creating a Dashboard

#### Step 1: Dashboard Information
1. Click **Create Dashboard** button
2. Fill in the dashboard details:
   - **Name**: Give your dashboard a descriptive name
   - **Description**: Explain the purpose of this dashboard
   - **Category**: Select from Safety, Efficacy, Enrollment, Operations, or Custom
   - **Starting Template**: Choose a template or start with a blank dashboard
3. Click **Next: Design Dashboard**

#### Step 2: Design Your Dashboard
1. **Widget Palette** (Left Sidebar)
   - Browse available widgets by category
   - Search for specific widgets
   - Drag widgets to the canvas to add them

2. **Design Canvas** (Center)
   - Drop widgets onto the grid
   - Resize widgets by dragging the corners
   - Move widgets by dragging the handle
   - Click a widget to select it for configuration

3. **Property Panel** (Right Sidebar - appears when widget is selected)
   - Configure widget-specific settings
   - Set data sources
   - Adjust display options
   - Set size constraints

4. **Toolbar Features**
   - **Undo/Redo**: Revert or replay changes
   - **Grid Toggle**: Show/hide alignment grid
   - **Device Preview**: Test responsive layouts (Desktop/Tablet/Mobile)
   - **Preview Mode**: See how the dashboard will look to end users

#### Step 3: Save Your Dashboard
1. Click **Save Dashboard** when you're satisfied with the design
2. The dashboard will be saved and available for use in studies

### Editing Dashboards

1. From the dashboard list, click the menu icon (⋮) next to any dashboard
2. Select **Edit** to open the dashboard in the designer
3. Make your changes
4. Click **Save Changes** to update the dashboard

### Widget Types

#### Metrics Widgets
- **Metric Card**: Display single KPIs with optional trend indicators
- **Progress Bar**: Show progress towards goals

#### Chart Widgets
- **Line Chart**: Time series and trend visualization
- **Bar Chart**: Compare values across categories
- **Pie Chart**: Show proportions and percentages
- **Scatter Plot**: Visualize correlations between variables
- **Heatmap**: Display data density and patterns

#### Data Widgets
- **Data Table**: Display tabular data with sorting and filtering

#### Geographic Widgets
- **Geographic Map**: Visualize data on a map

#### Content Widgets
- **Text Widget**: Add custom text, descriptions, or instructions

### Widget Configuration

Each widget type has specific configuration options:

#### Common Settings
- **Title**: Widget header text
- **Data Source**: Select the data to display
- **Size**: Adjust width and height in grid units

#### Metric Card Settings
- **Unit**: Display unit (e.g., patients, %)
- **Show Trend**: Enable trend indicator
- **Trend Period**: Time range for trend calculation

#### Chart Settings
- **X/Y Axis Labels**: Customize axis labels
- **Show Legend**: Toggle legend visibility
- **Show Grid**: Toggle grid lines

#### Table Settings
- **Rows per Page**: Set pagination size
- **Enable Sorting**: Allow column sorting
- **Enable Filtering**: Add filter controls

### Responsive Design

The dashboard designer supports responsive layouts:

1. **Breakpoints**
   - Desktop (lg): 1200px and above
   - Tablet (md): 996px - 1199px
   - Mobile (sm): 768px - 995px
   - Small Mobile (xs): Below 768px

2. **Testing Responsive Layouts**
   - Use the device buttons in the toolbar
   - Preview how your dashboard adapts to different screen sizes
   - Widgets automatically reflow based on available space

### Best Practices

1. **Layout Design**
   - Place most important metrics at the top
   - Group related widgets together
   - Leave some whitespace for better readability

2. **Widget Selection**
   - Choose appropriate visualizations for your data
   - Don't overcrowd the dashboard
   - Consider the end user's needs

3. **Performance**
   - Limit the number of data-heavy widgets
   - Use appropriate refresh intervals
   - Test with realistic data volumes

4. **Accessibility**
   - Use clear, descriptive titles
   - Ensure sufficient color contrast
   - Provide text alternatives for visual data

### Troubleshooting

**Widgets won't drag**: Ensure you're in design mode (not preview mode)

**Can't resize widgets**: Click the widget first to select it, then drag the corners

**Changes not saving**: Check for validation errors in widget configuration

**Dashboard looks different in preview**: Some styling is only applied in preview/production mode

---

For technical support, contact your system administrator.