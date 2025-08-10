# Study Components

## Transformation Progress Component

The transformation progress tracking system provides real-time monitoring of pipeline execution status.

### Components

#### `TransformationProgress`
Main component for displaying pipeline execution progress with:
- Real-time status updates via WebSocket or polling
- Individual pipeline progress tracking
- Error handling and retry capabilities
- Execution logs viewer
- Collapsible pipeline details

#### `useTransformationProgress` Hook
React hook for managing transformation progress state:
- WebSocket connection management with automatic reconnection
- Polling fallback when WebSocket is unavailable
- Methods for retrying failed pipelines
- Execution log filtering
- Pipeline status queries

### Usage

```tsx
import { TransformationProgress } from '@/components/study/transformation-progress';

// Basic usage
<TransformationProgress
  studyId="study-123"
  executionId="exec-456" // Optional, will fetch latest if not provided
  onComplete={() => console.log('Execution completed')}
/>

// Using the hook directly
import { useTransformationProgress } from '@/hooks/use-transformation-progress';

const {
  execution,
  isLoading,
  isConnected,
  retryPipeline,
  cancelExecution,
  getLogs,
  getPipeline
} = useTransformationProgress({
  studyId: 'study-123',
  executionId: 'exec-456',
  pollingInterval: 2000, // Optional, defaults to 2s
  enableWebSocket: true  // Optional, defaults to true
});
```

### Features

1. **Real-time Updates**
   - WebSocket connection for instant updates
   - Automatic fallback to polling if WebSocket fails
   - Connection status indicator

2. **Pipeline Status Display**
   - Visual progress bars for each pipeline
   - Status icons (pending, running, success, failed)
   - Execution time tracking
   - Output summary (rows processed, execution time)

3. **Error Handling**
   - Display error messages for failed pipelines
   - Retry individual failed pipelines
   - Cancel running executions

4. **Execution Logs**
   - Real-time log streaming
   - Log level filtering (all, errors, warnings)
   - Timestamped entries
   - Pipeline-specific logs

5. **Summary View**
   - Total execution duration
   - Pipeline success/failure counts
   - Overall progress percentage

### API Endpoints Required

The component expects these backend endpoints:

```
GET  /api/v1/studies/{studyId}/pipeline/executions/latest
GET  /api/v1/studies/{studyId}/pipeline/executions/{executionId}
POST /api/v1/studies/{studyId}/pipeline/executions/{executionId}/retry
POST /api/v1/studies/{studyId}/pipeline/executions/{executionId}/cancel
WS   /ws/studies/{studyId}/pipeline/progress
```

### WebSocket Message Format

```typescript
// Execution update message
{
  type: 'execution_update',
  execution: PipelineExecution
}

// Log message
{
  type: 'log',
  log: ExecutionLog
}

// Subscribe to execution
{
  type: 'subscribe',
  execution_id: string
}
```

### Demo

View the live demo at `/demo/transformation-progress` to see the component in action with simulated data.