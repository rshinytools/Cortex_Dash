# Clinical Dashboard Platform - User Manual

## Table of Contents

1. [Authentication](#authentication)
   - [Login](#login)
   - [Password Recovery](#password-recovery)
   - [Resetting Your Password](#resetting-your-password)
2. [Study Management](#study-management)
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
3. [Unified Dashboard Designer](#unified-dashboard-designer)
   - [Overview](#unified-dashboard-overview)
   - [Creating Unified Templates](#creating-unified-templates)
   - [Menu Design](#menu-design)
   - [Dashboard Theming](#dashboard-theming)
   - [Save Options and Autosave](#save-options-and-autosave)
   - [Help System](#help-system)

## Authentication

### Login

To access the Clinical Dashboard Platform, you need to authenticate with your credentials.

1. Navigate to the login page at `/auth/login`
2. Enter your email address and password
3. Click **Sign In**
4. You'll be redirected to the dashboard upon successful authentication

### Password Recovery

If you've forgotten your password, you can request a password reset:

1. On the login page, click **Forgot password?**
2. Enter your registered email address
3. Click **Send reset instructions**
4. Check your email for password reset instructions
5. The email will contain a link valid for 24 hours

**Note**: If you don't receive the email within a few minutes, check your spam folder.

### Resetting Your Password

After receiving the password reset email:

1. Click the reset link in the email
2. You'll be redirected to the password reset page
3. Enter your new password (minimum 8 characters)
4. Confirm your new password
5. Click **Reset password**
6. You'll be redirected to the login page after successful reset

**Password Requirements**:
- At least 8 characters long
- Recommended: Include a mix of letters, numbers, and symbols for better security

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

### Dashboard Designer Features

#### Toolbar Controls

The dashboard designer includes a comprehensive toolbar with the following features:

##### Grid Snapping
- **Toggle Button**: Click the grid icon to enable/disable grid snapping
- When enabled, widgets will automatically snap to grid positions for perfect alignment
- Grid snapping makes it easier to create clean, organized layouts

##### Alignment Tools
Align multiple widgets with precision:
- **Align Left**: Align selected widgets to the leftmost edge
- **Align Center**: Center widgets horizontally
- **Align Right**: Align selected widgets to the rightmost edge
- **Align Top**: Align selected widgets to the topmost edge
- **Align Middle**: Center widgets vertically
- **Align Bottom**: Align selected widgets to the bottommost edge

**How to use alignment tools:**
1. Hold Ctrl/Cmd and click to select multiple widgets
2. Click the desired alignment button
3. Selected widgets will align based on your choice

##### Distribution Tools
Evenly distribute widgets in your layout:
- **Distribute Horizontally**: Space widgets evenly left to right
- **Distribute Vertically**: Space widgets evenly top to bottom

**Requirements:** Select at least 3 widgets to use distribution tools

##### Copy/Paste Functionality
- **Copy**: Select a widget and click the copy button or press Ctrl+C
- **Paste**: Click paste button or press Ctrl+V to duplicate the widget
- Pasted widgets appear with a slight offset from the original

##### Undo/Redo
- **Undo**: Revert the last action (Ctrl+Z)
- **Redo**: Restore an undone action (Ctrl+Y)
- The system maintains up to 50 actions in history

#### Keyboard Shortcuts

| Action | Windows/Linux | Mac |
|--------|---------------|-----|
| Copy Widget | Ctrl+C | Cmd+C |
| Paste Widget | Ctrl+V | Cmd+V |
| Undo | Ctrl+Z | Cmd+Z |
| Redo | Ctrl+Y | Cmd+Y |
| Delete Widget | Delete | Delete |
| Clear Selection | Escape | Escape |

#### Multi-Selection
- Hold Ctrl/Cmd while clicking widgets to select multiple items
- Selected widgets show a highlighted border
- Perform bulk operations on selected widgets
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
   - Use grid snapping for consistent alignment
   - Leverage alignment tools for professional layouts

2. **Widget Selection**
   - Choose appropriate visualizations for your data
   - Don't overcrowd the dashboard
   - Consider the end user's needs
   - Copy successful widget configurations for consistency

3. **Performance**
   - Limit the number of data-heavy widgets
   - Use appropriate refresh intervals
   - Test with realistic data volumes

4. **Accessibility**
   - Use clear, descriptive titles
   - Ensure sufficient color contrast
   - Provide text alternatives for visual data

5. **Efficient Design Workflow**
   - Use keyboard shortcuts to speed up your work
   - Take advantage of undo/redo for experimentation
   - Copy and modify existing widgets instead of creating from scratch
   - Use multi-select for bulk operations

### Troubleshooting

**Widgets won't drag**: Ensure you're in design mode (not preview mode)

**Can't resize widgets**: Click the widget first to select it, then drag the corners

**Changes not saving**: Check for validation errors in widget configuration

**Dashboard looks different in preview**: Some styling is only applied in preview/production mode

**Alignment tools disabled**: You need to select at least 2 widgets to use alignment tools

**Distribution tools disabled**: You need to select at least 3 widgets to distribute them

**Copy/Paste not working**: Ensure you have a widget selected before copying

**Undo not available**: The action history may be empty or you're at the beginning of the history

## Unified Dashboard Designer

### Overview {#unified-dashboard-overview}

The Unified Dashboard Designer is an advanced interface that allows you to create complete dashboard solutions by combining menu structures with multiple dashboards. This tool is perfect for creating comprehensive dashboard templates that can be applied to multiple studies.

### Accessing the Unified Dashboard Designer

1. Navigate to **Admin > Dashboard Templates** in the sidebar (System Admin only)
2. Click **Create New Template** to start designing
3. Or click **Edit** on an existing template to modify it

### Creating Unified Templates

#### Step 1: Template Metadata

When creating a new unified template, start by providing basic information:

1. **Template Name**: A descriptive name for your template
2. **Description**: Explain the purpose and use case
3. **Tags**: Add tags for easy searching (e.g., "safety", "phase3", "oncology")
4. **Category**: Select the primary category (Safety, Efficacy, Enrollment, etc.)

#### Step 2: Design the Navigation Menu

The left panel shows the menu designer where you create the navigation structure:

1. **Add Menu Items**:
   - Click **Add Item** to create a new menu entry
   - Choose the item type:
     - **Dashboard Page**: A page that displays widgets
     - **Group**: A folder to organize related items
     - **External Link**: Link to external resources

2. **Configure Menu Items**:
   - **Label**: The display name in the menu
   - **Icon**: Choose an icon for visual identification
   - **Type**: Switch between dashboard page, group, or link
   - **Visibility**: Control who can see this item

3. **Organize the Structure**:
   - Drag and drop items to reorder
   - Nest items under groups for organization
   - Create multi-level hierarchies

#### Step 3: Configure Dashboards

For each dashboard page in your menu:

1. Select the menu item from the left panel
2. The dashboard designer appears on the right
3. Add widgets from the widget palette
4. Configure each widget's data and display settings
5. Arrange widgets using the grid layout

#### Step 4: Preview and Save

1. Click **Preview** to see how the template will look
2. Review the complete navigation and dashboard flow
3. Click **Save Template** when satisfied

### Menu Design

The menu designer supports creating complex navigation structures:

#### Menu Item Types

1. **Dashboard Page**
   - Links to a dashboard with widgets
   - Can be nested under groups
   - Supports custom icons and labels

2. **Group**
   - Collapsible folder for organization
   - Can contain other groups or pages
   - Helps organize related dashboards

3. **External Link**
   - Opens external URLs in new tab
   - Useful for documentation or external tools
   - Shows an external link indicator

#### Best Practices for Menu Design

- Keep the hierarchy shallow (3 levels max)
- Use clear, descriptive labels
- Group related dashboards together
- Place frequently used items at the top
- Use consistent naming conventions

### Dashboard Theming

The unified designer includes a powerful theming system to customize the appearance of your dashboards.

#### Accessing Theme Settings

Click the **Theme** button in the header toolbar to open the theme editor.

#### Theme Options

1. **Preset Themes**
   - **Light**: Clean, bright theme for standard use
   - **Dark**: Dark mode for reduced eye strain
   - **Clinical**: Professional theme optimized for medical data

2. **Color Customization**
   - **Primary Color**: Main brand color for buttons and highlights
   - **Secondary Color**: Accent color for secondary elements
   - **Background**: Page background color
   - **Card**: Widget container background
   - **Text Colors**: Foreground and muted text colors
   - **Border**: Colors for lines and dividers

3. **Typography Settings**
   - **Font Family**: Choose from professional font options
   - **Base Font Size**: Adjust text size (12-18px)
   - **Line Height**: Control text spacing
   - **Heading Font**: Optional different font for headings

4. **Spacing and Layout**
   - **Border Radius**: Control corner roundness (0-16px)
   - **Widget Gap**: Space between widgets
   - **Container Padding**: Internal spacing

#### Theme Preview

Changes are reflected in real-time in the designer. Use the preview mode to see the full effect of your theme choices.

### Save Options and Autosave

The unified designer includes robust save functionality to protect your work:

#### Manual Save

- Click **Save Template** to manually save your work
- Provides immediate feedback on save success or failure
- Shows detailed error messages if save fails

#### Autosave Feature

Autosave is enabled by default and automatically saves your work every 30 seconds when changes are detected.

1. **Autosave Indicator**
   - Shows "Saved X minutes ago" when up to date
   - Shows "Unsaved changes" when edits are pending
   - Shows "Saving..." during save operations

2. **Configuring Autosave**
   - Click the Settings icon (⚙️) in the header
   - Toggle "Autosave" on/off
   - When disabled, only manual saves will occur

3. **Best Practices**
   - Keep autosave enabled for safety
   - Still save manually before major changes
   - Check the save indicator before leaving

#### Save Notifications

The new notification system provides clear feedback:

- **Success**: Green notification confirming save
- **Error**: Red notification with error details
- **Loading**: Blue notification during save
- **Info**: General information messages

Notifications appear in the bottom-right corner and auto-dismiss after 4 seconds (except loading notifications).

### Help System

The unified designer includes comprehensive help features:

#### Contextual Help Icons

Throughout the interface, you'll find help icons (?) that provide:
- Quick explanations of features
- Tips for effective use
- Links to detailed documentation

#### Help Panel

Click the help button (floating button in bottom-left) to access:

1. **Getting Started Guide**
   - Step-by-step walkthrough
   - Best practices for template creation

2. **Feature Documentation**
   - Menu Design
   - Widget Configuration
   - Theming System
   - Autosave Settings

3. **Troubleshooting**
   - Common issues and solutions
   - Performance tips

#### Keyboard Shortcuts

The help panel includes a complete list of keyboard shortcuts for power users.

### Export and Import

Templates can be exported and imported for sharing or backup:

#### Exporting Templates

1. Click **Export** in the header toolbar
2. A JSON file downloads with:
   - Complete menu structure
   - All dashboard configurations
   - Theme settings
   - Widget arrangements

#### Importing Templates

1. Click **Import** in the header toolbar
2. Select a previously exported JSON file
3. The template loads into the designer
4. Review and save to add to your system

### Best Practices for Unified Templates

1. **Planning**
   - Sketch the menu structure first
   - Identify common dashboard patterns
   - Consider the end-user workflow

2. **Consistency**
   - Use the same theme across all dashboards
   - Maintain consistent widget styles
   - Follow naming conventions

3. **Performance**
   - Limit widgets per dashboard (10-15 max)
   - Use appropriate data refresh rates
   - Test with realistic data volumes

4. **Maintenance**
   - Document template purpose and usage
   - Version templates for major changes
   - Test thoroughly before deployment

---

For technical support, contact your system administrator.