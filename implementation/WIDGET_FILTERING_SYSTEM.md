# Enterprise Widget Filtering System - Implementation Document

## Executive Summary

This document outlines the implementation plan for an enterprise-grade SQL-based filtering system for the Clinical Dashboard Platform. The system enables administrators to apply complex SQL WHERE clause filters at the widget-field mapping level, supporting AND/OR logic and multiple conditions.

**Target Completion:** 4 weeks  
**Priority:** High  
**Complexity:** Enterprise-level with full features from day one

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Technical Requirements](#technical-requirements)
3. [Implementation Phases](#implementation-phases)
4. [Phase 1: Core Infrastructure](#phase-1-core-infrastructure-week-1)
5. [Phase 2: Integration Layer](#phase-2-integration-layer-week-2)
6. [Phase 3: User Interface](#phase-3-user-interface-week-3)
7. [Phase 4: Testing & Optimization](#phase-4-testing--optimization-week-4)
8. [Post-Implementation](#post-implementation)
9. [Risk Mitigation](#risk-mitigation)
10. [Success Metrics](#success-metrics)

---

## System Overview

### Architecture Flow
```
User Input (SQL Filter) → Validation → Parser → Executor → Filtered Data → Widget Display
                           ↓            ↓         ↓
                        Schema      AST Tree   Pandas/SQL
                        Check      Generation   Query
```

### Supported Filter Types
- Simple equality: `AESER = 'Y'`
- Complex conditions: `AGE >= 18 AND AGE <= 65`
- AND/OR logic: `(AESER = 'Y' AND AETERM IS NOT NULL) OR AESIDAT IS NOT NULL`
- IN operators: `AESEV IN ('SEVERE', 'LIFE THREATENING')`
- String patterns: `AETERM LIKE '%HEADACHE%'`
- NULL checks: `DSTERM IS NOT NULL`

---

## Technical Requirements

### Functional Requirements
- ✅ Support full SQL WHERE clause syntax
- ✅ Real-time query execution (no pre-processing)
- ✅ Complex AND/OR nested conditions
- ✅ Integration with existing field mapping system
- ✅ Validation against dataset schemas
- ✅ Performance optimization for datasets up to 1M rows
- ✅ Filter management in both initialization and study management

### Non-Functional Requirements
- ✅ Query response time < 2 seconds for datasets under 1M rows
- ✅ 21 CFR Part 11 compliant audit trail
- ✅ Graceful error handling (fail open, not closed)
- ✅ Schema change resilience
- ✅ Concurrent filter execution support

---

## Implementation Phases

### Phase Overview
| Phase | Duration | Focus Area | Dependencies |
|-------|----------|------------|--------------|
| Phase 1 | Week 1 | Core Infrastructure | None |
| Phase 2 | Week 2 | Integration Layer | Phase 1 |
| Phase 3 | Week 3 | User Interface | Phase 1, 2 |
| Phase 4 | Week 4 | Testing & Optimization | Phase 1, 2, 3 |

---

## Phase 1: Core Infrastructure (Week 1)

### Objectives
Build the foundational filtering engine with parser, validator, and executor components.

### Database Schema Updates

#### Task 1.1: Update Database Schema
**File:** `backend/app/alembic/versions/add_widget_filtering_system.py`

```python
"""Add widget filtering system

Revision ID: widget_filtering_001
Revises: current_head
Create Date: 2024-01-20
"""

def upgrade():
    # Add filter storage to studies table
    op.add_column('studies',
        sa.Column('field_mapping_filters', sa.JSON, nullable=True, default={})
    )
    
    # Create filter validation cache
    op.create_table('filter_validation_cache',
        sa.Column('id', sa.UUID, primary_key=True),
        sa.Column('study_id', sa.UUID, sa.ForeignKey('studies.id')),
        sa.Column('widget_id', sa.String(255)),
        sa.Column('filter_expression', sa.Text),
        sa.Column('dataset_name', sa.String(255)),
        sa.Column('is_valid', sa.Boolean),
        sa.Column('validation_errors', sa.JSON),
        sa.Column('validated_columns', sa.JSON),
        sa.Column('created_at', sa.DateTime),
        sa.Column('last_validated', sa.DateTime)
    )
    
    # Create filter metrics table
    op.create_table('filter_metrics',
        sa.Column('id', sa.UUID, primary_key=True),
        sa.Column('study_id', sa.UUID),
        sa.Column('widget_id', sa.String(255)),
        sa.Column('filter_expression', sa.Text),
        sa.Column('execution_time_ms', sa.Integer),
        sa.Column('rows_before', sa.Integer),
        sa.Column('rows_after', sa.Integer),
        sa.Column('executed_at', sa.DateTime)
    )
```

**Checklist:**
- [ ] Create Alembic migration file
- [ ] Add field_mapping_filters column to studies table
- [ ] Create filter_validation_cache table
- [ ] Create filter_metrics table
- [ ] Run migration in development
- [ ] Test rollback capability

### Backend Services

#### Task 1.2: Filter Parser Service
**File:** `backend/app/services/filters/filter_parser.py`

```python
# ABOUTME: SQL WHERE clause parser for widget filters
# ABOUTME: Converts SQL expressions to pandas queries and validates syntax

import re
import sqlparse
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import pandas as pd

@dataclass
class ParsedFilter:
    """Parsed filter representation"""
    original: str
    ast: Dict
    pandas_query: str
    sql_where: str
    referenced_columns: List[str]
    is_valid: bool
    errors: List[str]

class FilterParser:
    """Parse and validate SQL WHERE clauses"""
    
    OPERATORS = {
        '=': '==',
        '!=': '!=',
        '<>': '!=',
        '>': '>',
        '<': '<',
        '>=': '>=',
        '<=': '<=',
    }
    
    def parse(self, expression: str) -> ParsedFilter:
        """Parse SQL WHERE clause"""
        # Implementation here
        pass
    
    def validate_syntax(self, expression: str) -> Tuple[bool, List[str]]:
        """Validate SQL syntax"""
        pass
    
    def extract_columns(self, expression: str) -> List[str]:
        """Extract referenced column names"""
        pass
    
    def to_pandas_query(self, ast: Dict) -> str:
        """Convert AST to pandas query string"""
        pass
    
    def to_parquet_filters(self, ast: Dict) -> List:
        """Convert to PyArrow filter format"""
        pass
```

**Checklist:**
- [ ] Create filter_parser.py file
- [ ] Implement SQL tokenizer/lexer
- [ ] Build AST generator
- [ ] Create pandas query converter
- [ ] Add PyArrow filter converter
- [ ] Handle NULL/NOT NULL operations
- [ ] Support IN/NOT IN operators
- [ ] Handle LIKE patterns
- [ ] Add SQL injection protection
- [ ] Write comprehensive unit tests

#### Task 1.3: Filter Validator Service
**File:** `backend/app/services/filters/filter_validator.py`

```python
# ABOUTME: Validates filters against dataset schemas
# ABOUTME: Ensures type compatibility and column existence

from typing import Dict, List, Optional
from dataclasses import dataclass
import pandas as pd

@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    column_types: Dict[str, str]
    missing_columns: List[str]
    type_mismatches: List[Dict]

class FilterValidator:
    """Validate filters against dataset schemas"""
    
    def validate(
        self,
        filter_expression: str,
        dataset_schema: Dict[str, str]
    ) -> ValidationResult:
        """Validate filter against schema"""
        pass
    
    def check_column_existence(
        self,
        columns: List[str],
        schema: Dict[str, str]
    ) -> List[str]:
        """Check if columns exist in schema"""
        pass
    
    def check_type_compatibility(
        self,
        filter_ast: Dict,
        schema: Dict[str, str]
    ) -> List[Dict]:
        """Check data type compatibility"""
        pass
    
    def suggest_fixes(
        self,
        validation_result: ValidationResult,
        schema: Dict[str, str]
    ) -> List[str]:
        """Suggest fixes for validation errors"""
        pass
```

**Checklist:**
- [ ] Create filter_validator.py file
- [ ] Implement column existence check
- [ ] Add type compatibility validation
- [ ] Create error message generator
- [ ] Add suggestion engine for fixes
- [ ] Handle case sensitivity issues
- [ ] Support schema versioning
- [ ] Write validation unit tests

#### Task 1.4: Filter Executor Service
**File:** `backend/app/services/filters/filter_executor.py`

```python
# ABOUTME: Executes filters on datasets with performance tracking
# ABOUTME: Handles both pandas and SQL execution strategies

import time
import pandas as pd
import pyarrow.parquet as pq
from pathlib import Path
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class FilterExecutor:
    """Execute filters on datasets"""
    
    def execute(
        self,
        df: pd.DataFrame,
        filter_expression: str,
        schema: Dict[str, str]
    ) -> Tuple[pd.DataFrame, Dict]:
        """Execute filter and return filtered data with metrics"""
        start_time = time.time()
        
        try:
            # Parse filter
            parser = FilterParser()
            parsed = parser.parse(filter_expression)
            
            # Validate
            validator = FilterValidator()
            validation = validator.validate(filter_expression, schema)
            
            if not validation.is_valid:
                raise ValueError(f"Invalid filter: {validation.errors}")
            
            # Execute based on dataset size
            original_count = len(df)
            
            if original_count < 10000:
                # Small dataset - use pandas query
                filtered_df = df.query(parsed.pandas_query)
            else:
                # Large dataset - optimize execution
                filtered_df = self._execute_optimized(df, parsed)
            
            # Calculate metrics
            metrics = {
                'execution_time_ms': int((time.time() - start_time) * 1000),
                'rows_before': original_count,
                'rows_after': len(filtered_df),
                'reduction_percentage': (1 - len(filtered_df) / original_count) * 100
            }
            
            return filtered_df, metrics
            
        except Exception as e:
            logger.error(f"Filter execution failed: {str(e)}")
            raise
    
    def _execute_optimized(self, df: pd.DataFrame, parsed: ParsedFilter) -> pd.DataFrame:
        """Optimized execution for large datasets"""
        pass
    
    def execute_on_parquet(
        self,
        file_path: Path,
        filter_expression: str
    ) -> pd.DataFrame:
        """Execute directly on Parquet file"""
        pass
```

**Checklist:**
- [ ] Create filter_executor.py file
- [ ] Implement pandas query execution
- [ ] Add PyArrow Parquet filter pushdown
- [ ] Create execution strategy selector
- [ ] Add performance metrics tracking
- [ ] Implement error recovery
- [ ] Add query result caching logic
- [ ] Create execution benchmarks
- [ ] Write integration tests

### Phase 1 Deliverables Checklist
- [ ] Database migration completed and tested
- [ ] Filter parser fully functional with all operators
- [ ] Validator catching all error cases
- [ ] Executor handling datasets up to 1M rows
- [ ] All unit tests passing
- [ ] Documentation for each service
- [ ] Performance benchmarks established

---

## Phase 2: Integration Layer (Week 2)

### Objectives
Integrate filtering system with existing widget execution and create API endpoints.

### Widget Executor Integration

#### Task 2.1: Update Widget Data Executor
**File:** `backend/app/services/widget_data_executor_real.py`

```python
# Modifications to existing file

async def _get_real_kpi_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
    """Get real KPI data from Parquet files with filtering"""
    try:
        # ... existing code ...
        
        # NEW: Load filter configuration
        filter_config = self._get_filter_config(widget_id)
        
        if filter_config and filter_config.get('expression'):
            # Apply filter
            filtered_df, metrics = await self._apply_widget_filter(
                df,
                filter_config['expression'],
                dataset_name
            )
            
            # Track metrics
            await self._track_filter_metrics(
                widget_id,
                filter_config['expression'],
                metrics
            )
            
            df = filtered_df
            
        # ... continue with aggregation ...
        
    except FilterExecutionError as e:
        logger.error(f"Filter failed, continuing without filter: {str(e)}")
        # Continue without filter rather than fail widget
        
def _get_filter_config(self, widget_id: str) -> Optional[Dict]:
    """Get filter configuration for widget"""
    filters = self.study.field_mapping_filters or {}
    return filters.get(widget_id)

async def _apply_widget_filter(
    self,
    df: pd.DataFrame,
    expression: str,
    dataset: str
) -> Tuple[pd.DataFrame, Dict]:
    """Apply filter with error handling"""
    executor = FilterExecutor()
    schema = self._get_dataset_schema(dataset)
    return executor.execute(df, expression, schema)
```

**Checklist:**
- [ ] Add filter loading logic
- [ ] Integrate FilterExecutor
- [ ] Add metrics tracking
- [ ] Implement graceful failure (continue without filter)
- [ ] Add filter caching mechanism
- [ ] Update logging for filter operations
- [ ] Test with existing widgets
- [ ] Verify performance impact

### API Endpoints

#### Task 2.2: Filter Management API
**File:** `backend/app/api/v1/endpoints/widget_filters.py`

```python
# ABOUTME: API endpoints for widget filter management
# ABOUTME: Provides validation, preview, and CRUD operations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from typing import Dict, Any
from uuid import UUID
from pydantic import BaseModel

router = APIRouter()

class FilterValidateRequest(BaseModel):
    expression: str
    dataset: str
    
class FilterUpdateRequest(BaseModel):
    expression: str
    enabled: bool = True

@router.post("/studies/{study_id}/widgets/{widget_id}/filter/validate")
async def validate_filter(
    study_id: UUID,
    widget_id: str,
    request: FilterValidateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Validate filter expression against dataset schema"""
    # Implementation
    pass

@router.post("/studies/{study_id}/widgets/{widget_id}/filter/preview")
async def preview_filter(
    study_id: UUID,
    widget_id: str,
    request: FilterValidateRequest,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Preview filtered data"""
    # Implementation
    pass

@router.put("/studies/{study_id}/widgets/{widget_id}/filter")
async def update_filter(
    study_id: UUID,
    widget_id: str,
    request: FilterUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update or create filter for widget"""
    # Implementation
    pass

@router.delete("/studies/{study_id}/widgets/{widget_id}/filter")
async def delete_filter(
    study_id: UUID,
    widget_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove filter from widget"""
    # Implementation
    pass

@router.get("/studies/{study_id}/filters")
async def get_all_filters(
    study_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all filters for a study"""
    # Implementation
    pass

@router.post("/studies/{study_id}/filters/validate-all")
async def validate_all_filters(
    study_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Validate all filters in study (useful after data update)"""
    # Implementation
    pass
```

**Checklist:**
- [ ] Create widget_filters.py endpoint file
- [ ] Implement validation endpoint
- [ ] Add preview endpoint with row limit
- [ ] Create CRUD operations
- [ ] Add batch validation endpoint
- [ ] Implement permission checks
- [ ] Add audit logging
- [ ] Create OpenAPI documentation
- [ ] Write API integration tests

#### Task 2.3: Update Study Wizard Endpoints
**File:** `backend/app/api/v1/endpoints/study_wizard.py`

```python
# Modifications to save filters during wizard

@router.post("/wizard/{study_id}/field-mappings")
async def save_field_mappings_with_filters(
    study_id: UUID,
    mappings: Dict[str, Any],
    filters: Dict[str, Dict[str, Any]],  # NEW
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Save field mappings with optional filters"""
    study = db.get(Study, study_id)
    
    # Save mappings (existing code)
    study.field_mappings = mappings
    
    # NEW: Save filters
    if filters:
        study.field_mapping_filters = filters
        
        # Validate all filters
        for widget_id, filter_config in filters.items():
            if filter_config.get('expression'):
                # Validate and cache
                validation_result = await validate_and_cache_filter(
                    study_id,
                    widget_id,
                    filter_config['expression']
                )
                
                if not validation_result.is_valid:
                    # Return validation errors
                    pass
    
    db.commit()
```

**Checklist:**
- [ ] Update field mapping save endpoint
- [ ] Add filter parameter to wizard
- [ ] Implement filter validation during save
- [ ] Update wizard completion logic
- [ ] Add filter to initialization process
- [ ] Test with existing wizard flow

### Phase 2 Deliverables Checklist
- [ ] Widget executor successfully applying filters
- [ ] All API endpoints functional
- [ ] Filter validation working correctly
- [ ] Preview functionality operational
- [ ] Metrics being tracked
- [ ] API documentation complete
- [ ] Integration tests passing

---

## Phase 3: User Interface (Week 3)

### Objectives
Build comprehensive UI for filter management in both study initialization and management interfaces.

### Study Initialization UI

#### Task 3.1: Update Field Mapping Component
**File:** `frontend/src/components/study/initialization-wizard/steps/field-mapping.tsx`

```typescript
// Add filter support to existing component

interface FieldMapping {
  dataset: string;
  column: string;
  confidence?: number;
  filter?: {  // NEW
    expression: string;
    isValid: boolean;
    validationMessage?: string;
  };
}

// Add filter input section
<div className="mt-4 space-y-2">
  <div className="flex items-center gap-2">
    <Label className="text-sm font-medium">
      Filter Condition
      <Badge variant="outline" className="ml-2">Optional</Badge>
    </Label>
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger>
          <Info className="h-4 w-4 text-muted-foreground" />
        </TooltipTrigger>
        <TooltipContent>
          <p>SQL WHERE clause syntax. Examples:</p>
          <code>AESER = 'Y'</code><br/>
          <code>AGE >= 18 AND AGE <= 65</code>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  </div>
  
  <div className="flex gap-2">
    <div className="flex-1 relative">
      <Textarea
        value={currentMapping?.filter?.expression || ''}
        onChange={(e) => handleFilterChange(requirement.widget_id, field, e.target.value)}
        placeholder="e.g., AESER = 'Y' AND AETERM IS NOT NULL"
        className={cn(
          "font-mono text-sm",
          filterValidation[`${requirement.widget_id}_${field}`]?.isValid === false && 
          "border-red-500"
        )}
        rows={2}
      />
      {isValidating && (
        <Loader2 className="absolute right-2 top-2 h-4 w-4 animate-spin" />
      )}
    </div>
    
    <div className="flex flex-col gap-2">
      <Button
        size="sm"
        variant="outline"
        onClick={() => validateFilter(requirement.widget_id, field)}
        disabled={!currentMapping?.filter?.expression}
      >
        <CheckCircle2 className="h-4 w-4 mr-1" />
        Validate
      </Button>
      
      <Button
        size="sm"
        variant="outline"
        onClick={() => previewFilter(requirement.widget_id, field)}
        disabled={!currentMapping?.filter?.isValid}
      >
        <Eye className="h-4 w-4 mr-1" />
        Preview
      </Button>
    </div>
  </div>
  
  {/* Validation feedback */}
  {filterValidation[`${requirement.widget_id}_${field}`] && (
    <Alert className={cn(
      "mt-2",
      filterValidation[`${requirement.widget_id}_${field}`].isValid 
        ? "border-green-500" 
        : "border-red-500"
    )}>
      <AlertDescription>
        {filterValidation[`${requirement.widget_id}_${field}`].message}
      </AlertDescription>
    </Alert>
  )}
  
  {/* Column reference helper */}
  <div className="text-xs text-muted-foreground">
    Available columns: {availableColumns.join(', ')}
  </div>
</div>
```

**Checklist:**
- [ ] Add filter input field to mapping component
- [ ] Implement SQL syntax highlighting
- [ ] Add validation button and feedback
- [ ] Create preview functionality
- [ ] Add column reference helper
- [ ] Implement real-time validation
- [ ] Add filter examples/templates
- [ ] Handle validation errors gracefully
- [ ] Update form submission to include filters

### Study Management UI

#### Task 3.2: Create Filter Management Tab
**File:** `frontend/src/app/studies/[studyId]/manage/components/filters-tab.tsx`

```typescript
// ABOUTME: Filter management interface for study administrators
// ABOUTME: Provides bulk filter editing and validation status

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { FilterEditor } from '@/components/filters/FilterEditor';
import { studiesApi } from '@/lib/api/studies';

interface FiltersTabProps {
  studyId: string;
  isReadOnly?: boolean;
}

export function FiltersTab({ studyId, isReadOnly }: FiltersTabProps) {
  const [filters, setFilters] = useState<Record<string, FilterConfig>>({});
  const [validationStatus, setValidationStatus] = useState<Record<string, ValidationResult>>({});
  const [isValidating, setIsValidating] = useState(false);
  
  // Load existing filters
  useEffect(() => {
    loadFilters();
  }, [studyId]);
  
  const loadFilters = async () => {
    const response = await studiesApi.getStudyFilters(studyId);
    setFilters(response.filters);
    setValidationStatus(response.validationStatus);
  };
  
  const validateAllFilters = async () => {
    setIsValidating(true);
    try {
      const result = await studiesApi.validateAllFilters(studyId);
      setValidationStatus(result.validationStatus);
      
      toast({
        title: 'Validation Complete',
        description: `${result.validCount} valid, ${result.invalidCount} invalid filters`,
      });
    } finally {
      setIsValidating(false);
    }
  };
  
  return (
    <div className="space-y-6">
      {/* Summary Card */}
      <Card>
        <CardHeader>
          <CardTitle>Filter Overview</CardTitle>
          <CardDescription>
            Manage data filters for all dashboard widgets
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="flex gap-4">
              <div>
                <p className="text-sm text-muted-foreground">Total Filters</p>
                <p className="text-2xl font-bold">{Object.keys(filters).length}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Valid</p>
                <p className="text-2xl font-bold text-green-600">
                  {Object.values(validationStatus).filter(v => v.isValid).length}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Invalid</p>
                <p className="text-2xl font-bold text-red-600">
                  {Object.values(validationStatus).filter(v => !v.isValid).length}
                </p>
              </div>
            </div>
            
            <Button 
              onClick={validateAllFilters}
              disabled={isValidating}
            >
              {isValidating ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Validating...
                </>
              ) : (
                <>
                  <CheckCircle2 className="mr-2 h-4 w-4" />
                  Validate All
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
      
      {/* Filter List */}
      <div className="space-y-4">
        {Object.entries(filters).map(([widgetId, filter]) => (
          <FilterEditor
            key={widgetId}
            widgetId={widgetId}
            filter={filter}
            validation={validationStatus[widgetId]}
            onUpdate={(newFilter) => updateFilter(widgetId, newFilter)}
            onDelete={() => deleteFilter(widgetId)}
            isReadOnly={isReadOnly}
          />
        ))}
      </div>
    </div>
  );
}
```

**Checklist:**
- [ ] Create filters-tab component
- [ ] Build filter overview dashboard
- [ ] Implement filter list/grid view
- [ ] Add bulk validation functionality
- [ ] Create filter editor component
- [ ] Add preview functionality
- [ ] Implement save/update operations
- [ ] Add delete confirmation
- [ ] Create filter templates dropdown

#### Task 3.3: Create Filter Editor Component
**File:** `frontend/src/components/filters/FilterEditor.tsx`

```typescript
// ABOUTME: Reusable filter editor with syntax highlighting and validation
// ABOUTME: Used in both initialization and management interfaces

import React, { useState, useEffect } from 'react';
import CodeMirror from '@uiw/react-codemirror';
import { sql } from '@codemirror/lang-sql';
import { oneDark } from '@codemirror/theme-one-dark';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

interface FilterEditorProps {
  widgetId: string;
  widgetTitle: string;
  datasetName: string;
  currentFilter?: string;
  onSave: (filter: string) => void;
  onValidate: (filter: string) => Promise<ValidationResult>;
  onPreview: (filter: string) => Promise<PreviewResult>;
}

export function FilterEditor({
  widgetId,
  widgetTitle,
  datasetName,
  currentFilter = '',
  onSave,
  onValidate,
  onPreview
}: FilterEditorProps) {
  const [filter, setFilter] = useState(currentFilter);
  const [validation, setValidation] = useState<ValidationResult | null>(null);
  const [preview, setPreview] = useState<PreviewResult | null>(null);
  const [isValidating, setIsValidating] = useState(false);
  const [isPreviewing, setIsPreviewing] = useState(false);
  
  // Debounced validation
  useEffect(() => {
    const timer = setTimeout(() => {
      if (filter) {
        handleValidate();
      }
    }, 500);
    
    return () => clearTimeout(timer);
  }, [filter]);
  
  const handleValidate = async () => {
    setIsValidating(true);
    try {
      const result = await onValidate(filter);
      setValidation(result);
    } finally {
      setIsValidating(false);
    }
  };
  
  const handlePreview = async () => {
    setIsPreviewing(true);
    try {
      const result = await onPreview(filter);
      setPreview(result);
    } finally {
      setIsPreviewing(false);
    }
  };
  
  return (
    <Card className="p-4">
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-medium">{widgetTitle}</h3>
            <p className="text-sm text-muted-foreground">Dataset: {datasetName}</p>
          </div>
          <Badge variant={validation?.isValid ? 'success' : 'destructive'}>
            {validation?.isValid ? 'Valid' : 'Invalid'}
          </Badge>
        </div>
        
        {/* SQL Editor */}
        <div className="border rounded-lg overflow-hidden">
          <CodeMirror
            value={filter}
            height="100px"
            theme={oneDark}
            extensions={[sql()]}
            onChange={(value) => setFilter(value)}
            placeholder="Enter SQL WHERE clause (e.g., AESER = 'Y')"
          />
        </div>
        
        {/* Validation Messages */}
        {validation && !validation.isValid && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              {validation.errors.join(', ')}
            </AlertDescription>
          </Alert>
        )}
        
        {/* Preview Results */}
        {preview && (
          <div className="bg-muted p-3 rounded-lg">
            <p className="text-sm">
              Filter Impact: {preview.rowsBefore} → {preview.rowsAfter} rows
              ({preview.reductionPercentage.toFixed(1)}% reduction)
            </p>
          </div>
        )}
        
        {/* Actions */}
        <div className="flex gap-2">
          <Button
            onClick={() => onSave(filter)}
            disabled={!validation?.isValid}
          >
            Save Filter
          </Button>
          <Button
            variant="outline"
            onClick={handlePreview}
            disabled={!validation?.isValid || isPreviewing}
          >
            {isPreviewing ? 'Loading...' : 'Preview'}
          </Button>
        </div>
      </div>
    </Card>
  );
}
```

**Checklist:**
- [ ] Create FilterEditor component
- [ ] Integrate CodeMirror for SQL syntax
- [ ] Add real-time validation feedback
- [ ] Implement preview functionality
- [ ] Add error display
- [ ] Create impact visualization
- [ ] Add filter templates dropdown
- [ ] Support dark/light themes
- [ ] Add keyboard shortcuts

### Frontend API Integration

#### Task 3.4: Update Studies API Client
**File:** `frontend/src/lib/api/studies.ts`

```typescript
// Add filter-related API methods

export const studiesApi = {
  // ... existing methods ...
  
  // Filter validation
  async validateFilter(
    studyId: string,
    widgetId: string,
    expression: string,
    dataset: string
  ) {
    const response = await apiClient.post(
      `/studies/${studyId}/widgets/${widgetId}/filter/validate`,
      { expression, dataset }
    );
    return response.data;
  },
  
  // Filter preview
  async previewFilter(
    studyId: string,
    widgetId: string,
    expression: string,
    dataset: string,
    limit: number = 100
  ) {
    const response = await apiClient.post(
      `/studies/${studyId}/widgets/${widgetId}/filter/preview`,
      { expression, dataset, limit }
    );
    return response.data;
  },
  
  // Update filter
  async updateWidgetFilter(
    studyId: string,
    widgetId: string,
    expression: string,
    enabled: boolean = true
  ) {
    const response = await apiClient.put(
      `/studies/${studyId}/widgets/${widgetId}/filter`,
      { expression, enabled }
    );
    return response.data;
  },
  
  // Get all filters
  async getStudyFilters(studyId: string) {
    const response = await apiClient.get(`/studies/${studyId}/filters`);
    return response.data;
  },
  
  // Validate all filters
  async validateAllFilters(studyId: string) {
    const response = await apiClient.post(`/studies/${studyId}/filters/validate-all`);
    return response.data;
  }
};
```

**Checklist:**
- [ ] Add validation API method
- [ ] Add preview API method
- [ ] Add CRUD operations
- [ ] Add batch operations
- [ ] Handle error responses
- [ ] Add TypeScript types
- [ ] Test API integration

### Phase 3 Deliverables Checklist
- [ ] Field mapping UI updated with filter support
- [ ] Filter management tab functional
- [ ] Filter editor component complete
- [ ] Syntax highlighting working
- [ ] Real-time validation operational
- [ ] Preview functionality working
- [ ] API integration complete
- [ ] UI responsive and accessible

---

## Phase 4: Testing & Optimization (Week 4)

### Objectives
Comprehensive testing, performance optimization, and production readiness.

### Testing Strategy

#### Task 4.1: Unit Tests
**File:** `backend/tests/services/filters/test_filter_parser.py`

```python
import pytest
from app.services.filters.filter_parser import FilterParser

class TestFilterParser:
    def test_simple_equality(self):
        parser = FilterParser()
        result = parser.parse("AESER = 'Y'")
        assert result.is_valid
        assert result.pandas_query == "AESER == 'Y'"
    
    def test_complex_and_or(self):
        parser = FilterParser()
        expr = "(AESER = 'Y' AND AETERM IS NOT NULL) OR AESIDAT IS NOT NULL"
        result = parser.parse(expr)
        assert result.is_valid
        assert len(result.referenced_columns) == 3
    
    def test_sql_injection_protection(self):
        parser = FilterParser()
        malicious = "AESER = 'Y'; DROP TABLE studies; --"
        result = parser.parse(malicious)
        assert not result.is_valid
        assert "SQL injection" in result.errors[0]
    
    # Add more test cases...
```

**Checklist:**
- [ ] Test all SQL operators
- [ ] Test nested conditions
- [ ] Test SQL injection attempts
- [ ] Test malformed expressions
- [ ] Test edge cases (empty, null)
- [ ] Test performance with complex filters
- [ ] Test column name variations
- [ ] Test data type handling

#### Task 4.2: Integration Tests
**File:** `backend/tests/api/test_widget_filters.py`

```python
import pytest
from fastapi.testclient import TestClient

class TestWidgetFilterAPI:
    def test_validate_filter_endpoint(self, client: TestClient, test_study):
        response = client.post(
            f"/api/v1/studies/{test_study.id}/widgets/widget1/filter/validate",
            json={"expression": "AESER = 'Y'", "dataset": "ae"}
        )
        assert response.status_code == 200
        assert response.json()["isValid"] == True
    
    def test_preview_filter_impact(self, client: TestClient, test_study):
        response = client.post(
            f"/api/v1/studies/{test_study.id}/widgets/widget1/filter/preview",
            json={"expression": "AESER = 'Y'", "dataset": "ae"}
        )
        assert response.status_code == 200
        assert "rowsBefore" in response.json()
        assert "rowsAfter" in response.json()
    
    # Add more test cases...
```

**Checklist:**
- [ ] Test all API endpoints
- [ ] Test permission checks
- [ ] Test validation errors
- [ ] Test concurrent requests
- [ ] Test large filter expressions
- [ ] Test filter updates
- [ ] Test audit logging

#### Task 4.3: End-to-End Tests
**File:** `frontend/tests/e2e/filter-management.spec.ts`

```typescript
import { test, expect } from '@playwright/test';

test.describe('Filter Management', () => {
  test('should add filter during study initialization', async ({ page }) => {
    // Navigate to field mapping step
    await page.goto('/studies/new/initialize');
    
    // Add mapping
    await page.selectOption('[data-testid="dataset-select"]', 'ae');
    await page.selectOption('[data-testid="column-select"]', 'AETERM');
    
    // Add filter
    await page.fill('[data-testid="filter-input"]', "AESER = 'Y'");
    await page.click('[data-testid="validate-button"]');
    
    // Check validation
    await expect(page.locator('[data-testid="validation-success"]')).toBeVisible();
    
    // Preview
    await page.click('[data-testid="preview-button"]');
    await expect(page.locator('[data-testid="preview-results"]')).toContainText('rows');
  });
  
  test('should edit filter in study management', async ({ page }) => {
    // Test filter editing flow
  });
});
```

**Checklist:**
- [ ] Test filter creation flow
- [ ] Test filter editing flow
- [ ] Test validation feedback
- [ ] Test preview functionality
- [ ] Test error handling
- [ ] Test filter deletion
- [ ] Test bulk operations

### Performance Optimization

#### Task 4.4: Performance Benchmarks
**File:** `backend/tests/performance/test_filter_performance.py`

```python
import pytest
import pandas as pd
import numpy as np
from app.services.filters.filter_executor import FilterExecutor

class TestFilterPerformance:
    @pytest.mark.benchmark
    def test_filter_performance_small_dataset(self, benchmark):
        # 1,000 rows
        df = pd.DataFrame({
            'AESER': np.random.choice(['Y', 'N'], 1000),
            'AETERM': np.random.choice(['HEADACHE', 'NAUSEA', None], 1000)
        })
        
        executor = FilterExecutor()
        result = benchmark(executor.execute, df, "AESER = 'Y'", {})
        assert result[1]['execution_time_ms'] < 100
    
    @pytest.mark.benchmark
    def test_filter_performance_large_dataset(self, benchmark):
        # 1,000,000 rows
        df = pd.DataFrame({
            'AESER': np.random.choice(['Y', 'N'], 1000000),
            'AETERM': np.random.choice(['HEADACHE', 'NAUSEA', None], 1000000)
        })
        
        executor = FilterExecutor()
        result = benchmark(executor.execute, df, "AESER = 'Y'", {})
        assert result[1]['execution_time_ms'] < 2000
```

**Checklist:**
- [ ] Benchmark small datasets (<10k rows)
- [ ] Benchmark medium datasets (10k-100k rows)
- [ ] Benchmark large datasets (100k-1M rows)
- [ ] Test complex filter performance
- [ ] Test concurrent filter execution
- [ ] Identify optimization opportunities
- [ ] Document performance baselines

#### Task 4.5: Optimization Implementation

**Optimizations to implement:**
1. **Query Optimization**
   - [ ] Use Parquet predicates pushdown
   - [ ] Implement query result caching
   - [ ] Optimize pandas query compilation

2. **Caching Strategy**
   - [ ] Cache parsed filter expressions
   - [ ] Cache validation results
   - [ ] Implement TTL for caches

3. **Execution Strategy**
   - [ ] Choose execution path based on dataset size
   - [ ] Parallelize filter execution for multiple widgets
   - [ ] Use indexed columns when available

### Documentation

#### Task 4.6: User Documentation
**File:** `docs/FILTER_USER_GUIDE.md`

Create comprehensive user guide covering:
- [ ] Filter syntax reference
- [ ] Common filter examples
- [ ] Performance best practices
- [ ] Troubleshooting guide
- [ ] FAQ section

#### Task 4.7: Technical Documentation
**File:** `docs/FILTER_TECHNICAL_SPEC.md`

Document technical implementation:
- [ ] Architecture overview
- [ ] API reference
- [ ] Database schema
- [ ] Performance characteristics
- [ ] Maintenance procedures

### Phase 4 Deliverables Checklist
- [ ] All unit tests passing (>90% coverage)
- [ ] Integration tests complete
- [ ] E2E tests automated
- [ ] Performance benchmarks met
- [ ] Optimizations implemented
- [ ] Documentation complete
- [ ] Security review passed
- [ ] Load testing complete

---

## Post-Implementation

### Monitoring & Maintenance

#### Monitoring Setup
- [ ] Add filter execution metrics to monitoring dashboard
- [ ] Set up alerts for filter failures
- [ ] Track filter performance trends
- [ ] Monitor validation cache hit rates

#### Maintenance Tasks
- [ ] Weekly validation of all filters
- [ ] Monthly performance review
- [ ] Quarterly filter optimization review
- [ ] Update filter templates based on usage

### Future Enhancements

1. **Filter Templates Library** (Month 2)
   - Pre-built filters for common scenarios
   - Organization-specific templates
   - Share filters across studies

2. **Visual Query Builder** (Month 3)
   - Drag-and-drop interface
   - For non-technical users
   - Generates SQL automatically

3. **Filter Composition** (Month 4)
   - Named filters for reuse
   - Filter inheritance
   - Filter versioning

4. **Advanced Analytics** (Month 5)
   - Filter impact analysis
   - Optimization suggestions
   - Usage analytics

---

## Risk Mitigation

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Complex SQL parsing failures | Medium | High | Use established SQL parser library |
| Performance degradation | Low | High | Implement caching and optimization |
| Schema changes breaking filters | Medium | Medium | Validation system with auto-fix |
| SQL injection attacks | Low | Critical | Input sanitization and parameterization |

### Mitigation Strategies
1. **Graceful Degradation**: Always allow widgets to work without filters
2. **Comprehensive Testing**: Extensive test coverage before production
3. **Rollback Plan**: Feature flag to disable filtering system
4. **Performance Monitoring**: Real-time metrics and alerts

---

## Success Metrics

### Technical Metrics
- [ ] Filter execution time < 2s for datasets up to 1M rows
- [ ] System uptime > 99.9%
- [ ] Zero SQL injection vulnerabilities
- [ ] Filter validation accuracy > 99%

### Business Metrics
- [ ] Reduced widget configuration time by 50%
- [ ] Improved data accuracy in dashboards
- [ ] Decreased support tickets for data issues
- [ ] Increased admin satisfaction scores

### Quality Metrics
- [ ] Code coverage > 90%
- [ ] Zero critical bugs in production
- [ ] API response time < 500ms
- [ ] UI responsiveness < 100ms

---

## Appendix

### A. SQL Filter Syntax Reference

```sql
-- Supported Operators
=, !=, <>, >, <, >=, <=

-- Logical Operators
AND, OR, NOT

-- NULL Checks
IS NULL, IS NOT NULL

-- IN Operator
IN ('value1', 'value2')
NOT IN ('value1', 'value2')

-- String Operations
LIKE 'pattern%'
NOT LIKE 'pattern%'

-- Examples
AESER = 'Y'
AGE >= 18 AND AGE <= 65
(AESER = 'Y' AND AETERM IS NOT NULL) OR AESIDAT IS NOT NULL
AESEV IN ('SEVERE', 'LIFE THREATENING')
AETERM LIKE '%HEADACHE%'
```

### B. Common Filter Templates

```sql
-- Serious Adverse Events
AESER = 'Y' OR AESEV IN ('SEVERE', 'LIFE THREATENING')

-- Protocol Deviations
DVTERM IS NOT NULL AND DVCAT = 'MAJOR'

-- Active Subjects
DSDECOD != 'COMPLETED' AND DSDECOD != 'DISCONTINUED'

-- Lab Abnormalities
LBNRIND IN ('HIGH', 'LOW') AND LBCAT = 'CHEMISTRY'

-- Vital Signs Out of Range
(VSORRES > VSORNRHI OR VSORRES < VSORNRLO) AND VSTESTCD IN ('SYSBP', 'DIABP', 'PULSE')
```

### C. Database Schema Details

```sql
-- Filter storage in studies table
field_mapping_filters JSONB
/*
Structure:
{
  "widget_id": {
    "expression": "AESER = 'Y'",
    "enabled": true,
    "validated": true,
    "validation_timestamp": "2024-01-20T10:00:00Z",
    "validation_errors": [],
    "referenced_columns": ["AESER"],
    "dataset": "ae"
  }
}
*/

-- Validation cache
filter_validation_cache (
  id UUID PRIMARY KEY,
  study_id UUID,
  widget_id VARCHAR(255),
  filter_expression TEXT,
  is_valid BOOLEAN,
  validation_errors JSONB,
  validated_columns JSONB,
  last_validated TIMESTAMP,
  INDEX idx_study_widget (study_id, widget_id)
)

-- Performance metrics
filter_metrics (
  id UUID PRIMARY KEY,
  study_id UUID,
  widget_id VARCHAR(255),
  execution_time_ms INTEGER,
  rows_before INTEGER,
  rows_after INTEGER,
  executed_at TIMESTAMP,
  INDEX idx_study_execution (study_id, executed_at)
)
```

---

## Sign-off

### Implementation Team
- [ ] Backend Developer
- [ ] Frontend Developer
- [ ] QA Engineer
- [ ] DevOps Engineer
- [ ] Product Owner

### Review & Approval
- [ ] Technical Lead
- [ ] Architecture Review
- [ ] Security Review
- [ ] Compliance Review
- [ ] Final Approval

---

**Document Version:** 1.0  
**Last Updated:** 2024-01-20  
**Status:** Ready for Implementation