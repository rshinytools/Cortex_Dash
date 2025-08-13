# Study Initialization API Documentation

## Overview

The Study Initialization API provides endpoints for managing the comprehensive 4-phase study initialization process, including template application, data upload, field mapping, and activation.

## Endpoints

### Initialize Study with Progress Tracking

Start the full study initialization process with real-time progress tracking.

```http
POST /api/v1/studies/{study_id}/initialize/progress
```

**Parameters:**
- `study_id` (path): The ID of the study to initialize

**Request Body:**
```json
{
  "template_id": "string",
  "skip_data_upload": false
}
```

**Response:**
```json
{
  "task_id": "string",
  "status": "queued",
  "message": "Study initialization started"
}
```

### Get Initialization Status

Get the current initialization status and progress for a study.

```http
GET /api/v1/studies/{study_id}/initialization/status
```

**Response:**
```json
{
  "initialization_status": "in_progress",
  "initialization_progress": 75,
  "initialization_steps": {
    "current_step": "data_conversion",
    "steps": {
      "template_application": {
        "status": "completed",
        "progress": 100,
        "completed_at": "2024-01-15T10:30:00Z"
      },
      "data_upload": {
        "status": "completed",
        "progress": 100,
        "files_processed": 5
      },
      "data_conversion": {
        "status": "in_progress",
        "progress": 75,
        "current_file": "ae.sas7bdat"
      },
      "field_mapping": {
        "status": "pending",
        "progress": 0
      }
    }
  }
}
```

### Upload Study Data

Upload clinical data files for the study.

```http
POST /api/v1/studies/{study_id}/data/upload
```

**Request:** Multipart form data with files

**Response:**
```json
{
  "uploaded_files": ["dm.sas7bdat", "ae.csv"],
  "total_files": 2,
  "total_size": 5242880,
  "upload_path": "/data/studies/org123/study123/source_data/2024-01-15"
}
```

### Retry Failed Initialization

Retry a failed initialization from the last successful checkpoint.

```http
POST /api/v1/studies/{study_id}/initialization/retry
```

**Response:**
```json
{
  "task_id": "string",
  "status": "queued",
  "retry_from_step": "field_mapping"
}
```

### Cancel Initialization

Cancel an in-progress initialization.

```http
POST /api/v1/studies/{study_id}/initialization/cancel
```

**Response:**
```json
{
  "status": "cancelled",
  "message": "Study initialization cancelled"
}
```

## WebSocket Connection

Connect to receive real-time initialization progress updates.

```
WS /ws/studies/{study_id}/initialization?token={auth_token}
```

### Message Types

#### Progress Update
```json
{
  "type": "progress",
  "step": "data_conversion",
  "step_progress": 75,
  "overall_progress": 50,
  "message": "Converting ae.sas7bdat to Parquet format..."
}
```

#### Status Change
```json
{
  "type": "status_change",
  "status": "completed",
  "progress": 100,
  "message": "Study initialization completed successfully"
}
```

#### Error
```json
{
  "type": "error",
  "step": "field_mapping",
  "error": "Required field USUBJID not found in uploaded data",
  "recoverable": true
}
```

## Field Mapping Endpoints

### Get Study Field Mappings

Get all field mappings for a study.

```http
GET /api/v1/studies/{study_id}/field-mappings
```

**Response:**
```json
[
  {
    "id": "string",
    "widget_id": "string",
    "widget_title": "Adverse Events Summary",
    "dataset": "AE",
    "target_field": "USUBJID",
    "source_field": "SUBJECT_ID",
    "is_mapped": true,
    "confidence_score": 0.95,
    "mapping_type": "automatic"
  }
]
```

### Update Field Mapping

Update a specific field mapping.

```http
PUT /api/v1/field-mappings/{mapping_id}
```

**Request Body:**
```json
{
  "source_field": "USUBJID",
  "is_mapped": true,
  "confidence_score": 1.0
}
```

## Study Wizard Endpoints

### Start Wizard Session

Start a new study initialization wizard session.

```http
POST /api/v1/study-wizard/start
```

**Response:**
```json
{
  "session_id": "string",
  "current_step": 1,
  "total_steps": 4,
  "expires_at": "2024-01-15T12:00:00Z"
}
```

### Submit Wizard Step

Submit data for a wizard step.

```http
POST /api/v1/study-wizard/{session_id}/step
```

**Request Body:**
```json
{
  "step": 1,
  "data": {
    "study_name": "COVID Vaccine Trial",
    "study_code": "COV-VAC-001",
    "protocol_number": "2024-001"
  }
}
```

### Complete Wizard

Complete the wizard and create the study.

```http
POST /api/v1/study-wizard/{session_id}/complete
```

**Response:**
```json
{
  "study_id": "string",
  "initialization_started": true,
  "redirect_url": "/studies/string/initialization"
}
```

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "detail": "Invalid template ID provided"
}
```

### 404 Not Found
```json
{
  "detail": "Study not found"
}
```

### 409 Conflict
```json
{
  "detail": "Study initialization already in progress"
}
```

### 500 Internal Server Error
```json
{
  "detail": "An unexpected error occurred during initialization"
}
```