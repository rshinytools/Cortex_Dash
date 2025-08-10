// ABOUTME: Comprehensive test suite for data transformation components
// ABOUTME: Tests transformation creation, execution, validation, and UI interactions

import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { toast } from 'sonner';

import DataTransformationStep from '@/components/pipeline/data-transformation-step';
import { mockTransformations, mockStudy, mockDatasets } from './mocks/transformation-mocks';
import { api } from '@/lib/api';

// Mock API calls
vi.mock('@/lib/api', () => ({
  api: {
    studies: {
      getTransformations: vi.fn(),
      createTransformation: vi.fn(),
      updateTransformation: vi.fn(),
      deleteTransformation: vi.fn(),
      validateTransformation: vi.fn(),
      executeTransformation: vi.fn(),
      getTransformationStatus: vi.fn(),
      getAvailableDatasets: vi.fn()
    }
  }
}));

// Mock toast notifications
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    loading: vi.fn(),
    promise: vi.fn()
  }
}));

// Mock CodeMirror component
vi.mock('@uiw/react-codemirror', () => ({
  default: ({ value, onChange, placeholder }: any) => (
    <textarea
      data-testid="code-editor"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
    />
  )
}));

// Test utilities
const createQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: { retry: false },
    mutations: { retry: false }
  }
});

const renderWithProviders = (component: React.ReactElement) => {
  const queryClient = createQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      {component}
    </QueryClientProvider>
  );
};

describe('DataTransformationStep', () => {
  const mockOnComplete = vi.fn();
  const mockOnPrevious = vi.fn();
  const defaultProps = {
    studyId: 'test-study-id',
    onComplete: mockOnComplete,
    onPrevious: mockOnPrevious
  };

  beforeEach(() => {
    vi.clearAllMocks();
    // Setup default mock responses
    (api.studies.getTransformations as any).mockResolvedValue(mockTransformations);
    (api.studies.getAvailableDatasets as any).mockResolvedValue(mockDatasets);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Component Rendering', () => {
    it('should render the transformation step with all sections', async () => {
      renderWithProviders(<DataTransformationStep {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Data Transformation')).toBeInTheDocument();
        expect(screen.getByText('Create Transformation')).toBeInTheDocument();
        expect(screen.getByText('Skip Transformation')).toBeInTheDocument();
      });
    });

    it('should load and display existing transformations', async () => {
      renderWithProviders(<DataTransformationStep {...defaultProps} />);

      await waitFor(() => {
        expect(api.studies.getTransformations).toHaveBeenCalledWith('test-study-id');
        mockTransformations.forEach(transformation => {
          expect(screen.getByText(transformation.name)).toBeInTheDocument();
        });
      });
    });

    it('should display available datasets in the form', async () => {
      renderWithProviders(<DataTransformationStep {...defaultProps} />);

      const createButton = screen.getByText('Create Transformation');
      fireEvent.click(createButton);

      await waitFor(() => {
        expect(api.studies.getAvailableDatasets).toHaveBeenCalledWith('test-study-id');
        // Check that datasets appear in the multiselect
        const inputDatasetsSelect = screen.getByLabelText('Input Datasets');
        expect(inputDatasetsSelect).toBeInTheDocument();
      });
    });
  });

  describe('Transformation Creation', () => {
    it('should create a new transformation with valid data', async () => {
      const user = userEvent.setup();
      (api.studies.createTransformation as any).mockResolvedValue({
        id: 'new-transformation-id',
        name: 'Test Transformation',
        status: 'draft'
      });

      renderWithProviders(<DataTransformationStep {...defaultProps} />);

      // Click create button
      const createButton = screen.getByText('Create Transformation');
      fireEvent.click(createButton);

      // Fill in the form
      await user.type(screen.getByLabelText('Name'), 'Test Transformation');
      await user.type(screen.getByLabelText('Description'), 'Test description');
      
      // Select input datasets
      const inputSelect = screen.getByLabelText('Input Datasets');
      await user.click(inputSelect);
      await user.click(screen.getByText('dm'));
      await user.click(screen.getByText('ae'));

      // Enter output dataset name
      await user.type(screen.getByLabelText('Output Dataset Name'), 'transformed_data');

      // Enter transformation script
      const codeEditor = screen.getByTestId('code-editor');
      await user.type(codeEditor, "df['new_col'] = df['old_col'] * 2");

      // Submit form
      const saveButton = screen.getByText('Save Transformation');
      await user.click(saveButton);

      await waitFor(() => {
        expect(api.studies.createTransformation).toHaveBeenCalledWith('test-study-id', {
          name: 'Test Transformation',
          description: 'Test description',
          input_datasets: ['dm', 'ae'],
          output_dataset: 'transformed_data',
          script_content: "df['new_col'] = df['old_col'] * 2"
        });
        expect(toast.success).toHaveBeenCalledWith('Transformation created successfully');
      });
    });

    it('should validate transformation before saving', async () => {
      const user = userEvent.setup();
      (api.studies.validateTransformation as any).mockResolvedValue({
        is_valid: true,
        sample_output: { columns: ['col1', 'col2'], rows: 5 }
      });

      renderWithProviders(<DataTransformationStep {...defaultProps} />);

      const createButton = screen.getByText('Create Transformation');
      fireEvent.click(createButton);

      // Fill basic fields
      await user.type(screen.getByLabelText('Name'), 'Test Transformation');
      await user.type(screen.getByTestId('code-editor'), "df['test'] = 1");

      // Click validate button
      const validateButton = screen.getByText('Validate Script');
      await user.click(validateButton);

      await waitFor(() => {
        expect(api.studies.validateTransformation).toHaveBeenCalled();
        expect(screen.getByText('Script is valid')).toBeInTheDocument();
      });
    });

    it('should show validation errors for invalid scripts', async () => {
      const user = userEvent.setup();
      (api.studies.validateTransformation as any).mockResolvedValue({
        is_valid: false,
        error: 'NameError: name "undefined_var" is not defined'
      });

      renderWithProviders(<DataTransformationStep {...defaultProps} />);

      const createButton = screen.getByText('Create Transformation');
      fireEvent.click(createButton);

      await user.type(screen.getByTestId('code-editor'), 'df = undefined_var');

      const validateButton = screen.getByText('Validate Script');
      await user.click(validateButton);

      await waitFor(() => {
        expect(screen.getByText(/NameError/)).toBeInTheDocument();
      });
    });

    it('should show error for security violations', async () => {
      const user = userEvent.setup();
      (api.studies.createTransformation as any).mockRejectedValue({
        response: { data: { detail: 'Security violation: import statements not allowed' } }
      });

      renderWithProviders(<DataTransformationStep {...defaultProps} />);

      const createButton = screen.getByText('Create Transformation');
      fireEvent.click(createButton);

      await user.type(screen.getByLabelText('Name'), 'Malicious');
      await user.type(screen.getByTestId('code-editor'), 'import os');

      const saveButton = screen.getByText('Save Transformation');
      await user.click(saveButton);

      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith(
          expect.stringContaining('Security violation')
        );
      });
    });
  });

  describe('Transformation Execution', () => {
    it('should execute a transformation and show progress', async () => {
      const user = userEvent.setup();
      (api.studies.executeTransformation as any).mockResolvedValue({
        task_id: 'test-task-id',
        status: 'running'
      });

      // Mock status polling
      (api.studies.getTransformationStatus as any)
        .mockResolvedValueOnce({ state: 'PENDING', current: 0, total: 100 })
        .mockResolvedValueOnce({ state: 'PROGRESS', current: 50, total: 100 })
        .mockResolvedValue({ state: 'SUCCESS', current: 100, total: 100 });

      renderWithProviders(<DataTransformationStep {...defaultProps} />);

      await waitFor(() => {
        const firstTransformation = screen.getByTestId(`transformation-${mockTransformations[0].id}`);
        const runButton = within(firstTransformation).getByText('Run');
        fireEvent.click(runButton);
      });

      await waitFor(() => {
        expect(api.studies.executeTransformation).toHaveBeenCalledWith(
          'test-study-id',
          mockTransformations[0].id
        );
        // Check for progress indicator
        expect(screen.getByText(/Running/)).toBeInTheDocument();
      });

      // Wait for completion
      await waitFor(() => {
        expect(screen.getByText(/Completed/)).toBeInTheDocument();
        expect(toast.success).toHaveBeenCalledWith('Transformation completed successfully');
      }, { timeout: 5000 });
    });

    it('should handle execution errors', async () => {
      (api.studies.executeTransformation as any).mockRejectedValue({
        response: { data: { detail: 'Transformation failed: Memory limit exceeded' } }
      });

      renderWithProviders(<DataTransformationStep {...defaultProps} />);

      await waitFor(() => {
        const firstTransformation = screen.getByTestId(`transformation-${mockTransformations[0].id}`);
        const runButton = within(firstTransformation).getByText('Run');
        fireEvent.click(runButton);
      });

      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith(
          expect.stringContaining('Memory limit exceeded')
        );
      });
    });
  });

  describe('Skip Transformation Flow', () => {
    it('should allow skipping transformation step', async () => {
      const user = userEvent.setup();
      renderWithProviders(<DataTransformationStep {...defaultProps} />);

      const skipButton = screen.getByText('Skip Transformation');
      await user.click(skipButton);

      // Check for confirmation dialog
      await waitFor(() => {
        expect(screen.getByText(/Are you sure you want to skip/)).toBeInTheDocument();
      });

      const confirmButton = screen.getByText('Skip');
      await user.click(confirmButton);

      expect(mockOnComplete).toHaveBeenCalledWith({ skipped: true });
    });

    it('should not skip when cancelled', async () => {
      const user = userEvent.setup();
      renderWithProviders(<DataTransformationStep {...defaultProps} />);

      const skipButton = screen.getByText('Skip Transformation');
      await user.click(skipButton);

      const cancelButton = screen.getByText('Cancel');
      await user.click(cancelButton);

      expect(mockOnComplete).not.toHaveBeenCalled();
    });
  });

  describe('Transformation Management', () => {
    it('should edit existing transformation', async () => {
      const user = userEvent.setup();
      (api.studies.updateTransformation as any).mockResolvedValue({
        ...mockTransformations[0],
        name: 'Updated Name'
      });

      renderWithProviders(<DataTransformationStep {...defaultProps} />);

      await waitFor(() => {
        const firstTransformation = screen.getByTestId(`transformation-${mockTransformations[0].id}`);
        const editButton = within(firstTransformation).getByText('Edit');
        fireEvent.click(editButton);
      });

      // Update name
      const nameInput = screen.getByDisplayValue(mockTransformations[0].name);
      await user.clear(nameInput);
      await user.type(nameInput, 'Updated Name');

      const saveButton = screen.getByText('Update Transformation');
      await user.click(saveButton);

      await waitFor(() => {
        expect(api.studies.updateTransformation).toHaveBeenCalledWith(
          'test-study-id',
          mockTransformations[0].id,
          expect.objectContaining({ name: 'Updated Name' })
        );
        expect(toast.success).toHaveBeenCalledWith('Transformation updated successfully');
      });
    });

    it('should delete transformation with confirmation', async () => {
      const user = userEvent.setup();
      (api.studies.deleteTransformation as any).mockResolvedValue({});

      renderWithProviders(<DataTransformationStep {...defaultProps} />);

      await waitFor(() => {
        const firstTransformation = screen.getByTestId(`transformation-${mockTransformations[0].id}`);
        const deleteButton = within(firstTransformation).getByText('Delete');
        fireEvent.click(deleteButton);
      });

      // Confirm deletion
      const confirmButton = screen.getByText('Delete', { selector: 'button.destructive' });
      await user.click(confirmButton);

      await waitFor(() => {
        expect(api.studies.deleteTransformation).toHaveBeenCalledWith(
          'test-study-id',
          mockTransformations[0].id
        );
        expect(toast.success).toHaveBeenCalledWith('Transformation deleted successfully');
      });
    });
  });

  describe('Error States', () => {
    it('should handle API errors gracefully', async () => {
      (api.studies.getTransformations as any).mockRejectedValue(
        new Error('Failed to load transformations')
      );

      renderWithProviders(<DataTransformationStep {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText(/Failed to load transformations/)).toBeInTheDocument();
      });
    });

    it('should show empty state when no transformations exist', async () => {
      (api.studies.getTransformations as any).mockResolvedValue([]);

      renderWithProviders(<DataTransformationStep {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText(/No transformations created yet/)).toBeInTheDocument();
      });
    });
  });

  describe('Performance and Large Datasets', () => {
    it('should handle large transformation results', async () => {
      const largeResult = {
        is_valid: true,
        sample_output: {
          columns: Array(50).fill(null).map((_, i) => `col_${i}`),
          rows: 10000,
          preview: 'Large dataset preview...'
        }
      };

      (api.studies.validateTransformation as any).mockResolvedValue(largeResult);

      renderWithProviders(<DataTransformationStep {...defaultProps} />);

      const createButton = screen.getByText('Create Transformation');
      fireEvent.click(createButton);

      const validateButton = screen.getByText('Validate Script');
      fireEvent.click(validateButton);

      await waitFor(() => {
        expect(screen.getByText(/10000 rows/)).toBeInTheDocument();
        expect(screen.getByText(/50 columns/)).toBeInTheDocument();
      });
    });
  });

  describe('Code Editor Features', () => {
    it('should show code snippets and examples', async () => {
      const user = userEvent.setup();
      renderWithProviders(<DataTransformationStep {...defaultProps} />);

      const createButton = screen.getByText('Create Transformation');
      fireEvent.click(createButton);

      // Check for example snippets button
      const snippetsButton = screen.getByText('Show Examples');
      await user.click(snippetsButton);

      await waitFor(() => {
        expect(screen.getByText(/Example transformations/)).toBeInTheDocument();
        expect(screen.getByText(/Filter rows/)).toBeInTheDocument();
        expect(screen.getByText(/Create calculated columns/)).toBeInTheDocument();
      });
    });

    it('should provide available variables context', async () => {
      renderWithProviders(<DataTransformationStep {...defaultProps} />);

      const createButton = screen.getByText('Create Transformation');
      fireEvent.click(createButton);

      // Check for available variables display
      expect(screen.getByText(/Available variables/)).toBeInTheDocument();
      expect(screen.getByText(/df - Main dataframe/)).toBeInTheDocument();
      expect(screen.getByText(/pd - Pandas library/)).toBeInTheDocument();
      expect(screen.getByText(/np - NumPy library/)).toBeInTheDocument();
    });
  });

  describe('Complete Workflow', () => {
    it('should complete full transformation workflow', async () => {
      const user = userEvent.setup();
      
      // Mock all API calls for complete workflow
      (api.studies.createTransformation as any).mockResolvedValue({
        id: 'new-id',
        name: 'Complete Transformation',
        status: 'draft'
      });
      
      (api.studies.validateTransformation as any).mockResolvedValue({
        is_valid: true,
        sample_output: { columns: ['result'], rows: 100 }
      });
      
      (api.studies.executeTransformation as any).mockResolvedValue({
        task_id: 'task-123',
        status: 'running'
      });
      
      (api.studies.getTransformationStatus as any).mockResolvedValue({
        state: 'SUCCESS',
        current: 100,
        total: 100
      });

      renderWithProviders(<DataTransformationStep {...defaultProps} />);

      // Create transformation
      const createButton = screen.getByText('Create Transformation');
      await user.click(createButton);

      await user.type(screen.getByLabelText('Name'), 'Complete Transformation');
      await user.type(screen.getByTestId('code-editor'), "df['result'] = df['value'] * 10");

      // Validate
      const validateButton = screen.getByText('Validate Script');
      await user.click(validateButton);

      await waitFor(() => {
        expect(screen.getByText('Script is valid')).toBeInTheDocument();
      });

      // Save
      const saveButton = screen.getByText('Save Transformation');
      await user.click(saveButton);

      await waitFor(() => {
        expect(toast.success).toHaveBeenCalledWith('Transformation created successfully');
      });

      // Complete step
      const completeButton = screen.getByText('Continue to Publishing');
      await user.click(completeButton);

      expect(mockOnComplete).toHaveBeenCalledWith({ 
        transformationId: 'new-id',
        skipped: false 
      });
    });
  });
});