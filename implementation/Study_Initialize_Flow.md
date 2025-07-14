# Study Initialize Flow Implementation Document

## 🎯 Overview

This document outlines the complete implementation plan for the Study Initialize Flow, ensuring seamless integration with the dashboard template and widget system. The goal is to create a unified, real-time experience for initializing clinical studies with automatic data mapping based on widget requirements.

## 📋 Current State Analysis

### Existing Components
- **Frontend**: 4-step wizard (Template → Data Source → Field Mapping → Review)
- **Backend**: File upload, conversion to Parquet, template application
- **Missing**: Real-time progress, widget-driven mapping, unified status tracking

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Next.js)                       │
├─────────────────────────────────────────────────────────────┤
│  Study Initialize Wizard                                     │
│  ├── Template Selection (with widget preview)               │
│  ├── Data Source Configuration                              │
│  │   └── Real-time upload progress                         │
│  ├── Smart Field Mapping                                    │
│  │   └── Widget-based auto-suggestions                     │
│  └── Review & Activate                                      │
│                                                             │
│  WebSocket Client (Progress Updates)                        │
└─────────────────────────────────────────────────────────────┘
                              │
                    WebSocket Connection
                              │
┌─────────────────────────────────────────────────────────────┐
│                     Backend (FastAPI)                        │
├─────────────────────────────────────────────────────────────┤
│  WebSocket Manager                                          │
│  ├── Progress Broadcasting                                  │
│  └── Status Updates                                         │
│                                                             │
│  Study Initialization Service                               │
│  ├── Template Analysis                                      │
│  ├── Widget Requirements Extraction                         │
│  ├── File Processing Pipeline                               │
│  ├── Smart Mapping Engine                                   │
│  └── Validation & Activation                                │
│                                                             │
│  Background Workers (Celery)                                │
│  ├── File Conversion (with progress)                        │
│  ├── Data Quality Checks                                    │
│  └── Initial Data Processing                                │
└─────────────────────────────────────────────────────────────┘
```

## 📝 Detailed Implementation Tasks

### Phase 1: Backend Infrastructure Enhancement

#### 1.1 Study Model Enhancement
- [ ] Add initialization tracking fields to Study model
  ```python
  # Additional fields for Study model
  initialization_status: Optional[str] = Field(default="not_started")  # not_started, in_progress, completed, failed
  initialization_progress: Optional[int] = Field(default=0)  # 0-100
  initialization_steps: Optional[Dict[str, Any]] = Field(default_factory=dict)  # Track each step status
  template_applied_at: Optional[datetime] = None
  data_uploaded_at: Optional[datetime] = None
  mappings_configured_at: Optional[datetime] = None
  activated_at: Optional[datetime] = None
  ```

#### 1.2 WebSocket Infrastructure
- [ ] Create WebSocket manager for real-time updates
  ```python
  # backend/app/core/websocket_manager.py
  class WebSocketManager:
      def __init__(self):
          self.active_connections: Dict[str, List[WebSocket]] = {}
      
      async def connect(self, websocket: WebSocket, study_id: str, user_id: str)
      async def disconnect(self, websocket: WebSocket, study_id: str)
      async def broadcast_progress(self, study_id: str, progress_data: dict)
  ```

- [ ] Add WebSocket endpoint for study initialization
  ```python
  # backend/app/api/v1/endpoints/websocket.py
  @router.websocket("/ws/studies/{study_id}/initialization")
  async def websocket_endpoint(websocket: WebSocket, study_id: str)
  ```

#### 1.3 Study Initialization Service
- [ ] Create comprehensive initialization service
  ```python
  # backend/app/services/study_initialization_service.py
  class StudyInitializationService:
      async def start_initialization(self, study_id: str, user_id: str)
      async def apply_template_with_analysis(self, study_id: str, template_id: str)
      async def extract_widget_requirements(self, template: DashboardTemplate) -> List[FieldRequirement]
      async def process_data_upload(self, upload_id: str, callback: Callable)
      async def suggest_field_mappings(self, study_id: str, available_fields: List[str]) -> Dict[str, str]
      async def validate_initialization(self, study_id: str) -> ValidationResult
      async def activate_study(self, study_id: str)
  ```

#### 1.4 Enhanced File Conversion Service
- [ ] Add progress tracking to FileConversionService
  ```python
  # Modify backend/app/services/file_conversion_service.py
  async def convert_file_with_progress(
      self, 
      file_path: Path, 
      output_path: Path, 
      progress_callback: Callable[[int, str], None]
  )
  ```

- [ ] Implement progress callbacks for each conversion step
  - [ ] ZIP extraction progress
  - [ ] File discovery progress
  - [ ] Individual file conversion progress
  - [ ] Data validation progress

#### 1.5 Smart Field Mapping Engine
- [ ] Create intelligent mapping suggestion system
  ```python
  # backend/app/services/smart_mapping_service.py
  class SmartMappingService:
      def __init__(self):
          self.cdisc_patterns = self.load_cdisc_patterns()
          self.common_mappings = self.load_common_mappings()
      
      async def analyze_data_structure(self, parquet_path: Path) -> DataStructure
      async def match_to_widget_requirements(self, data_fields: List[str], widget_reqs: List[FieldRequirement]) -> Dict[str, str]
      async def validate_mapping_coverage(self, mappings: Dict[str, str], requirements: List[FieldRequirement]) -> ValidationResult
      async def suggest_transformations(self, source_field: str, target_requirement: FieldRequirement) -> List[Transformation]
  ```

### Phase 2: API Endpoints Enhancement

#### 2.1 Enhanced Study Initialization Endpoints
- [ ] Create unified initialization endpoint
  ```python
  POST /api/v1/studies/{study_id}/initialize/start
  Request: {
      "template_id": "uuid",
      "data_source_config": {...}
  }
  Response: {
      "initialization_id": "uuid",
      "websocket_url": "/ws/studies/{study_id}/initialization"
  }
  ```

- [ ] Add progress polling endpoint (fallback)
  ```python
  GET /api/v1/studies/{study_id}/initialize/progress
  Response: {
      "overall_progress": 45,
      "current_step": "processing_files",
      "steps": {
          "template_applied": {"status": "completed", "progress": 100},
          "data_uploaded": {"status": "in_progress", "progress": 60},
          "files_converted": {"status": "pending", "progress": 0},
          "mappings_configured": {"status": "pending", "progress": 0}
      }
  }
  ```

- [ ] Widget requirements endpoint
  ```python
  GET /api/v1/studies/{study_id}/widget-requirements
  Response: {
      "requirements": [
          {
              "widget_id": "widget-1",
              "widget_name": "Enrollment Metrics",
              "required_fields": [
                  {"name": "USUBJID", "type": "string", "required": true},
                  {"name": "RFSTDTC", "type": "date", "required": true}
              ]
          }
      ]
  }
  ```

#### 2.2 Enhanced Data Upload Endpoints
- [ ] Modify upload endpoint to support progress
  ```python
  POST /api/v1/studies/{study_id}/data-sources/upload
  # Returns upload_id for tracking
  ```

- [ ] Add upload progress endpoint
  ```python
  GET /api/v1/studies/{study_id}/uploads/{upload_id}/progress
  ```

#### 2.3 Smart Mapping Endpoints
- [ ] Auto-suggest mappings endpoint
  ```python
  POST /api/v1/studies/{study_id}/mappings/suggest
  Request: {
      "available_fields": ["SUBJID", "VISIT", "VSTESTCD", ...],
      "template_id": "uuid"
  }
  Response: {
      "suggestions": {
          "USUBJID": {
              "suggested_field": "SUBJID",
              "confidence": 0.95,
              "transformation": null
          },
          "VISITNUM": {
              "suggested_field": "VISIT",
              "confidence": 0.88,
              "transformation": "extract_number"
          }
      },
      "unmapped_requirements": ["AETERM", "AESTDTC"],
      "unused_fields": ["CUSTOM1", "CUSTOM2"]
  }
  ```

- [ ] Validate mappings endpoint
  ```python
  POST /api/v1/studies/{study_id}/mappings/validate
  Request: {
      "mappings": {...},
      "template_id": "uuid"
  }
  Response: {
      "valid": true/false,
      "coverage": 85,  # percentage
      "issues": [...]
  }
  ```

### Phase 3: Frontend Implementation

#### 3.1 Enhanced Wizard Component
- [ ] Create new unified wizard component
  ```typescript
  // frontend/src/components/study/StudyInitializeWizard.tsx
  interface StudyInitializeWizardProps {
    studyId: string;
    onComplete: () => void;
  }
  
  // Steps:
  // 1. TemplateSelectionStep (with widget preview)
  // 2. DataSourceConfigStep (with upload progress)
  // 3. SmartMappingStep (with auto-suggestions)
  // 4. ReviewActivateStep (with validation summary)
  ```

#### 3.2 Real-time Progress Component
- [ ] Create progress tracking component
  ```typescript
  // frontend/src/components/study/InitializationProgress.tsx
  interface InitializationProgressProps {
    studyId: string;
  }
  
  // Features:
  // - WebSocket connection for real-time updates
  // - Progress bars for each step
  // - Detailed logs panel
  // - Error handling and retry options
  ```

#### 3.3 Template Selection with Widget Preview
- [ ] Enhance template selection to show widgets
  ```typescript
  // frontend/src/components/study/TemplateSelectionWithPreview.tsx
  // Shows:
  // - Template details
  // - List of dashboards and widgets
  // - Data requirements summary
  // - Preview of dashboard layout
  ```

#### 3.4 Smart Field Mapping Interface
- [ ] Create intelligent mapping UI
  ```typescript
  // frontend/src/components/study/SmartFieldMapping.tsx
  // Features:
  // - Auto-suggestions with confidence scores
  // - Drag-and-drop mapping
  // - Transformation options
  // - Real-time validation
  // - Widget requirement indicators
  ```

#### 3.5 WebSocket Integration
- [ ] Create WebSocket hook for progress
  ```typescript
  // frontend/src/hooks/useInitializationProgress.ts
  export function useInitializationProgress(studyId: string) {
    const [progress, setProgress] = useState<InitializationProgress>();
    const [status, setStatus] = useState<'connecting' | 'connected' | 'error'>();
    
    useEffect(() => {
      const ws = new WebSocket(`${WS_URL}/studies/${studyId}/initialization`);
      // Handle messages, reconnection, etc.
    }, [studyId]);
    
    return { progress, status };
  }
  ```

### Phase 4: Integration & Data Flow

#### 4.1 Complete Initialization Flow
1. [ ] User selects template
   - Analyze template for widget requirements
   - Extract all required fields across all widgets
   - Store requirements in initialization context

2. [ ] User configures data source
   - Upload files or configure API connection
   - Start background processing with progress tracking
   - Broadcast progress via WebSocket

3. [ ] Smart field mapping
   - Analyze uploaded data structure
   - Match against widget requirements
   - Provide intelligent suggestions
   - Allow manual override

4. [ ] Validation & activation
   - Validate all mappings cover widget requirements
   - Check data quality
   - Activate study with full configuration

#### 4.2 Background Processing Flow
- [ ] Implement Celery tasks with progress
  ```python
  # backend/app/workers/initialization_tasks.py
  @celery_app.task(bind=True)
  def process_study_initialization(self, study_id: str, upload_id: str):
      # Track progress at each step
      self.update_state(state='PROGRESS', meta={'current': 10, 'step': 'extracting_files'})
      # Process files
      self.update_state(state='PROGRESS', meta={'current': 50, 'step': 'converting_to_parquet'})
      # Convert formats
      self.update_state(state='PROGRESS', meta={'current': 90, 'step': 'validating_data'})
      # Final validation
  ```

### Phase 5: Testing & Validation

#### 5.1 Unit Tests
- [ ] Test smart mapping algorithm
- [ ] Test widget requirement extraction
- [ ] Test progress tracking
- [ ] Test WebSocket broadcasting

#### 5.2 Integration Tests
- [ ] Test complete initialization flow
- [ ] Test error handling and recovery
- [ ] Test concurrent initializations
- [ ] Test large file handling

#### 5.3 E2E Tests
- [ ] Test wizard flow completion
- [ ] Test real-time progress updates
- [ ] Test mapping suggestions
- [ ] Test activation validation

### Phase 6: Error Handling & Recovery

#### 6.1 Error States
- [ ] Handle upload failures
- [ ] Handle conversion errors
- [ ] Handle mapping conflicts
- [ ] Handle WebSocket disconnections

#### 6.2 Recovery Mechanisms
- [ ] Resume partial uploads
- [ ] Retry failed conversions
- [ ] Save draft mappings
- [ ] Restore from checkpoints

## 📊 Success Metrics

1. **Performance**
   - [ ] File upload and conversion < 5 min for 1GB
   - [ ] Real-time progress updates < 1s latency
   - [ ] Field mapping suggestions < 2s response

2. **Accuracy**
   - [ ] Auto-mapping accuracy > 80% for CDISC fields
   - [ ] Widget requirement coverage validation 100%
   - [ ] Data quality check accuracy > 95%

3. **User Experience**
   - [ ] Complete initialization in < 10 minutes
   - [ ] No manual page refreshes needed
   - [ ] Clear error messages and recovery options

## 🚀 Implementation Phases

### Week 1-2: Backend Infrastructure
- Study model enhancements
- WebSocket infrastructure
- Progress tracking in services

### Week 3-4: API Development
- All new endpoints
- Smart mapping engine
- Background task updates

### Week 5-6: Frontend Development
- New wizard component
- WebSocket integration
- Progress visualization

### Week 7: Integration & Testing
- End-to-end testing
- Performance optimization
- Error handling

### Week 8: Polish & Documentation
- UI/UX improvements
- User documentation
- Deployment guides

## 📝 Notes

- Priority should be given to real-time progress tracking as it significantly improves user experience
- Smart mapping should leverage existing CDISC patterns in the codebase
- WebSocket fallback to polling should be implemented for environments that don't support WebSockets
- All progress updates should be persisted to allow resuming after disconnection

---
*Last Updated: January 14, 2025*
*Status: Planning Phase*