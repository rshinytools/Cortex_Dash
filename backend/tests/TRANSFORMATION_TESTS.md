# Data Transformation Testing Guide

## Overview

This document describes the comprehensive test suite for the data transformation pipeline feature.

## Test Structure

### Backend Tests (`backend/tests/api/test_study_transformation.py`)

The backend test suite covers:

1. **API Endpoint Tests** (`TestStudyTransformationAPI`)
   - Creating transformations
   - Retrieving transformations (list and by ID)
   - Updating transformations
   - Deleting transformations
   - Script validation
   - Transformation execution
   - Status tracking
   - Authorization and permissions

2. **Service Layer Tests** (`TestStudyTransformationService`)
   - Script security validation
   - Safe script execution
   - Resource limit enforcement
   - Dataset merging capabilities

3. **Edge Case Tests** (`TestTransformationEdgeCases`)
   - Empty dataset handling
   - Malformed script handling
   - Output validation
   - Error recovery

4. **Performance Tests** (`TestTransformationPerformance`)
   - Large dataset transformations
   - Complex query performance
   - Memory usage validation

### Frontend Tests (`frontend/tests/data-transformation.test.tsx`)

The frontend test suite covers:

1. **Component Rendering**
   - Initial state rendering
   - Loading existing transformations
   - Available datasets display

2. **Transformation Creation**
   - Form validation
   - Script validation UI
   - Security violation handling
   - Success flow

3. **Transformation Execution**
   - Progress tracking
   - Error handling
   - Completion notifications

4. **Skip Transformation Flow**
   - Skip confirmation
   - Navigation without transformation

5. **Transformation Management**
   - Edit existing transformations
   - Delete with confirmation
   - List management

6. **Error States**
   - API error handling
   - Empty states
   - Loading states

7. **Code Editor Features**
   - Syntax highlighting (mocked)
   - Example snippets
   - Available variables display

## Running Tests

### Backend Tests

```bash
# Run all transformation tests
cd backend
python tests/run_transformation_tests.py

# Run specific test suite
pytest tests/api/test_study_transformation.py::TestStudyTransformationAPI -v

# Run specific test
pytest tests/api/test_study_transformation.py::TestStudyTransformationAPI::test_create_transformation -v

# Run with coverage
pytest tests/api/test_study_transformation.py --cov=app.services.study_transformation --cov=app.api.v1.endpoints.study_transformation
```

### Frontend Tests

```bash
# Run all frontend tests
cd frontend
npm test

# Run transformation tests specifically
npm test data-transformation

# Run in watch mode
npm test -- --watch

# Run with coverage
npm test -- --coverage
```

## Test Data Helpers

The test suite includes helper utilities in `backend/tests/helpers/transformation_test_helpers.py`:

1. **TransformationTestDataGenerator**
   - Creates mock clinical trial datasets (demographics, adverse events, laboratory)
   - Generates realistic data distributions
   - Supports configurable dataset sizes

2. **TransformationTestValidator**
   - Validates transformation outputs
   - Checks data integrity
   - Verifies calculations

3. **TransformationSecurityTester**
   - Tests security restrictions
   - Validates script sandboxing
   - Checks resource limits

## Mock Data

Frontend tests use mock data from `frontend/tests/mocks/transformation-mocks.ts`:

- Mock study data
- Mock transformations with various states
- Mock datasets with SDTM structure
- Mock API responses and errors
- Example transformation scripts

## Security Testing

The test suite includes comprehensive security tests:

1. **Script Validation**
   - Import statement blocking
   - File system access prevention
   - Network access prevention
   - Code execution prevention

2. **Resource Limits**
   - Memory usage limits
   - CPU time limits
   - Output size limits

3. **Sandboxing**
   - Namespace restrictions
   - Built-in function access control
   - Module availability limits

## Performance Testing

Performance tests validate:

1. **Large Dataset Handling**
   - 100k+ row transformations
   - Complex aggregations
   - Memory efficiency

2. **Execution Time**
   - Transformation completion within limits
   - Progress tracking accuracy
   - Timeout handling

## Integration Testing

The tests verify integration between:

1. **API and Database**
   - Proper data persistence
   - Transaction handling
   - Concurrent access

2. **Frontend and Backend**
   - API contract adherence
   - Error message propagation
   - Progress updates via polling

3. **Celery Task Queue**
   - Task submission
   - Status tracking
   - Result retrieval

## Test Coverage Goals

- **Backend**: >90% coverage for transformation services and endpoints
- **Frontend**: >85% coverage for transformation components
- **Security**: 100% coverage for security validation
- **Edge Cases**: Comprehensive edge case coverage

## Adding New Tests

When adding new transformation features:

1. Add API endpoint tests in `TestStudyTransformationAPI`
2. Add service logic tests in `TestStudyTransformationService`
3. Add frontend component tests in corresponding test files
4. Update mock data as needed
5. Add security tests for any new script capabilities
6. Document test scenarios in this file

## Continuous Integration

Tests are run automatically on:

- Pull request creation
- Commits to main branch
- Nightly builds

Failed tests block deployment to ensure quality.