# Menu Navigation Implementation Summary

## Overview
This document summarizes the implementation of menu navigation in study dashboards, allowing users to see a left sidebar menu when viewing actual study dashboards (not just in admin preview).

## What Was Implemented

### 1. Frontend Changes

#### Studies API Enhancement (`/frontend/src/lib/api/studies.ts`)
- Added `StudyMenuResponse` interface to define menu structure
- Added `getStudyMenu()` function to fetch menu structure for a study
- API endpoint: `GET /runtime/{studyId}/menus`

#### Study Dashboard Page (`/frontend/src/app/studies/[studyId]/dashboard/page.tsx`)
- **Added Left Sidebar Navigation**:
  - Collapsible sidebar (264px expanded, 64px collapsed)
  - Displays menu items from the dashboard template
  - Dynamic icon mapping based on menu item icon field
  - Supports both flat menu items and grouped items
  - Selected menu item highlighting
  - Loading state while menu is being fetched

- **Visual Enhancements**:
  - Sidebar styled with slate colors for better contrast
  - Study code displayed in sidebar header
  - Improved button styling and spacing
  - Responsive design with collapse/expand functionality

- **Icon Support**:
  - Created `getMenuIcon()` function to map icon names to Lucide React components
  - Supports icons: LayoutDashboard, Shield, FlaskConical, Activity, BarChart3, etc.

### 2. Backend Changes

#### Runtime Dashboard Endpoint (`/backend/app/api/v1/endpoints/runtime/dashboards.py`)
- Fixed `GET /{study_id}/menus` endpoint to:
  - Fetch menu structure from dashboard template instead of non-existent menu_template_id
  - Extract menu from `template_structure.menu_structure` or `template_structure.menu`
  - Return default menu if no menu structure is found
  - Filter menu items based on user permissions

## How It Works

1. **Menu Storage**: Menus are stored as part of the dashboard template's `template_structure` field
2. **Menu Retrieval**: When a user visits a study dashboard:
   - Frontend calls `GET /runtime/{studyId}/menus`
   - Backend fetches the study's active dashboard configuration
   - Extracts menu structure from the dashboard template
   - Filters menu items based on user permissions
   - Returns the menu structure

3. **Menu Display**: 
   - Left sidebar shows the menu navigation
   - Users can click menu items to switch between different dashboard views
   - Sidebar can be collapsed to save screen space

## Menu Structure Example

```json
{
  "menu_structure": {
    "items": [
      {
        "id": "overview",
        "type": "dashboard",
        "label": "Study Overview",
        "icon": "LayoutDashboard",
        "order": 1
      },
      {
        "id": "safety-group",
        "type": "group",
        "label": "Safety Monitoring",
        "order": 2,
        "children": [
          {
            "id": "adverse-events",
            "type": "dashboard",
            "label": "Adverse Events",
            "icon": "Shield"
          },
          {
            "id": "lab-data",
            "type": "dashboard",
            "label": "Lab Data",
            "icon": "FlaskConical"
          }
        ]
      }
    ]
  }
}
```

## Testing

A test script was created (`test_study_menu.py`) to verify the functionality:
- Creates a dashboard template with embedded menu structure
- Retrieves the menu for a study
- Validates the menu structure is returned correctly

## Future Enhancements

1. **Dashboard Switching**: Currently, clicking menu items updates the selected state but doesn't load different dashboards. This needs to be implemented.
2. **Permission-based Visibility**: The backend supports filtering menu items by permissions, but frontend needs to handle this properly.
3. **Menu Customization**: Allow study managers to customize menus per study.
4. **Icons Library**: Expand the icon mapping to support more icons.

## Files Modified

- `/frontend/src/lib/api/studies.ts` - Added menu API functions
- `/frontend/src/app/studies/[studyId]/dashboard/page.tsx` - Added sidebar navigation
- `/backend/app/api/v1/endpoints/runtime/dashboards.py` - Fixed menu endpoint logic

## Related Components

- Dashboard templates store menu structures in their `template_structure` field
- Menu templates created in admin are saved as dashboard templates with category='custom'
- The same menu structure can be used in both admin preview and actual study dashboards