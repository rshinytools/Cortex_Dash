# Visual Filter Builder Specification

## Overview
A visual interface for building complex filter expressions for widget data queries.

## User Interface Design

### Basic Filter Structure
```
┌─ Filter Group (AND) ─────────────────────────────────────┐
│ ┌─ Condition 1 ────────────────────────────────────────┐ │
│ │ [AETERM ▼] [is not null ▼]                    [✕]   │ │
│ └──────────────────────────────────────────────────────┘ │
│                                                           │
│ ┌─ Condition 2 ────────────────────────────────────────┐ │
│ │ [AESEV ▼] [equals ▼] [SEVERE          ]       [✕]   │ │
│ └──────────────────────────────────────────────────────┘ │
│                                                           │
│ [+ Add Condition] [+ Add OR Group]                       │
└───────────────────────────────────────────────────────────┘
```

### Complex Filter with OR Logic
```
┌─ Filter Expression ──────────────────────────────────────┐
│ ┌─ Group 1 (AND) ───────────────────────────────────┐   │
│ │ [AETERM ▼] [is not null ▼]                        │   │
│ │ [AESEV ▼] [equals ▼] [SEVERE]                     │   │
│ └────────────────────────────────────────────────────┘   │
│                                                           │
│                        OR                                 │
│                                                           │
│ ┌─ Group 2 (AND) ───────────────────────────────────┐   │
│ │ [AESER ▼] [equals ▼] [Y]                          │   │
│ └────────────────────────────────────────────────────┘   │
│                                                           │
│ [+ Add OR Group]                                         │
└───────────────────────────────────────────────────────────┘
```

## Components

### 1. Column Selector
- Dropdown populated with all columns from selected dataset
- Shows column name and type (string, number, date)
- Search/filter capability for datasets with many columns

### 2. Operator Selector
Based on column data type:

**String columns:**
- equals
- not equals
- contains
- does not contain
- starts with
- ends with
- is null
- is not null
- in list
- not in list

**Numeric columns:**
- equals
- not equals
- greater than (>)
- less than (<)
- greater than or equal (>=)
- less than or equal (<=)
- between
- is null
- is not null

**Date columns:**
- equals
- not equals
- before
- after
- between
- is null
- is not null
- in last N days
- in next N days

### 3. Value Input
Dynamic based on operator:
- Text input for single values
- Date picker for date values
- Number input for numeric values
- Multi-select for "in list" operators
- Two inputs for "between" operator
- No input for null checks

## Filter Expression Output

### Internal Representation
```javascript
{
  "logic": "OR",
  "groups": [
    {
      "logic": "AND",
      "conditions": [
        {
          "column": "AETERM",
          "operator": "NOT_NULL",
          "value": null
        },
        {
          "column": "AESEV",
          "operator": "EQUALS",
          "value": "SEVERE"
        }
      ]
    },
    {
      "logic": "AND",
      "conditions": [
        {
          "column": "AESER",
          "operator": "EQUALS",
          "value": "Y"
        }
      ]
    }
  ]
}
```

### SQL Generation
The above would generate:
```sql
WHERE (AETERM IS NOT NULL AND AESEV = 'SEVERE') OR (AESER = 'Y')
```

## User Interactions

### Adding Conditions
1. Click "+ Add Condition" within a group
2. New condition row appears with default values
3. Select column → operator updates based on type → value input appears

### Adding OR Groups
1. Click "+ Add OR Group"
2. New AND group appears with OR separator
3. Add conditions within the new group

### Removing Elements
- Click [✕] on any condition to remove it
- Click [✕] on group header to remove entire group
- Confirm if group has multiple conditions

### Validation
- Highlight incomplete conditions in red
- Show warning if no conditions defined
- Validate value format matches column type
- Prevent saving invalid filters

## Advanced Features

### 1. Filter Templates
Save commonly used filters:
```
┌─ Saved Filters ─────────────────────────────────────────┐
│ ⭐ Serious AEs - Apply this filter                       │
│ ⭐ Recent Events (Last 30 days) - Apply                  │
│ ⭐ Active Subjects Only - Apply                          │
└──────────────────────────────────────────────────────────┘
```

### 2. Expression Preview
Show the filter in plain English:
```
Preview: Show records where (Adverse Event Term is not empty 
AND Severity equals "SEVERE") OR (Serious AE equals "Y")
```

### 3. Quick Filters
Common one-click filters:
- [Exclude NULL values]
- [This month only]
- [Active records only]

### 4. Test Filter
Before saving:
```
[Test Filter] → "This filter would return 234 records"
```

## Implementation Notes

### React Component Structure
```typescript
<FilterBuilder
  dataset="AE"
  columns={columnList}
  value={filterConfig}
  onChange={setFilterConfig}
  onTest={handleTestFilter}
/>
```

### State Management
```typescript
interface FilterConfig {
  logic: 'AND' | 'OR';
  groups: FilterGroup[];
}

interface FilterGroup {
  logic: 'AND' | 'OR';
  conditions: FilterCondition[];
}

interface FilterCondition {
  column: string;
  operator: FilterOperator;
  value: any;
}
```

### Parquet Query Translation
Convert filter config to PyArrow filter expressions for efficient parquet querying.

## Error Handling

1. **Invalid column**: "Column 'AETERM' not found in dataset"
2. **Type mismatch**: "Cannot use 'greater than' with text column"
3. **Invalid value**: "Date must be in YYYY-MM-DD format"
4. **Empty filter**: "At least one condition is required"

## Accessibility
- Keyboard navigation support
- Screen reader friendly labels
- Clear focus indicators
- Tooltips for all controls