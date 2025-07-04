# Clinical Dashboard Platform - Testing Framework

## Overview

This comprehensive testing framework ensures all components of the Clinical Dashboard Platform are thoroughly tested with a focus on compliance (21 CFR Part 11 & HIPAA), functionality, and performance. All test results are automatically saved in the `Reports/` folder with detailed descriptions, expected results, and pass/fail status.

## Test Structure

```
tests/
├── unit/                    # Unit tests for individual components
├── integration/             # Integration tests for component interactions
├── compliance/              # 21 CFR Part 11 & HIPAA compliance tests
├── performance/             # Performance and load tests
├── e2e/                     # End-to-end workflow tests
├── fixtures/                # Test data and utilities
└── report_templates/        # HTML/PDF report templates
```

## Running Tests

### Basic Commands

```bash
# Run all tests
python run_tests.py

# Run specific phase tests
python run_tests.py --phase 1  # Foundation tests
python run_tests.py --phase 2  # RBAC tests
python run_tests.py --phase 3  # Data Pipeline tests

# Run compliance tests only
python run_tests.py --compliance

# Run specific test types
python run_tests.py --type unit
python run_tests.py --type integration

# Run specific test file
python run_tests.py --file tests/test_phase1_foundation.py
```

### Advanced Usage

```bash
# Run with custom pytest arguments
python run_tests.py --pytest-args "-v --tb=long"

# Run performance tests
python run_tests.py --performance

# Run tests matching pattern
pytest -k "test_medidata"

# Run with specific markers
pytest -m "compliance and critical"

# Run in parallel (faster)
pytest -n auto
```

## Test Categories

### By Phase

- **phase1**: Foundation Setup (database, models, folder structure)
- **phase2**: RBAC Implementation
- **phase3**: Data Pipeline System
- **phase4**: Export & Reporting System
- **phase5**: Configuration Engine
- **phase6**: Dashboard Builder
- **phase7**: Admin Panel
- **phase8**: Security & Compliance
- **phase9**: Deployment & CI/CD

### By Type

- **unit**: Individual component tests
- **integration**: Component interaction tests
- **compliance**: 21 CFR Part 11 & HIPAA tests
- **performance**: Load and speed tests
- **e2e**: Complete workflow tests
- **critical**: Must-pass functionality

## Reports

All test executions generate comprehensive reports in `Reports/{timestamp}/`:

### Generated Reports

1. **test_report.html** - Interactive HTML report with:
   - Test summary and statistics
   - Detailed results by category
   - Failed test details with stack traces
   - Performance metrics
   - Code coverage summary

2. **coverage/** - Code coverage HTML reports:
   - Line-by-line coverage
   - Module-wise statistics
   - Missing lines highlighted

3. **junit.xml** - JUnit format for CI/CD integration

4. **coverage.json** - Machine-readable coverage data

5. **summary.json** - Execution summary with all metrics

### Report Features

- **Expected Results**: Each test documents its expected outcome
- **Actual Results**: Pass/fail status with details
- **Compliance Tracking**: 21 CFR Part 11 & HIPAA specific results
- **Performance Metrics**: Execution times and benchmarks
- **Failure Analysis**: Detailed error messages and stack traces

## Compliance Testing

### 21 CFR Part 11 Tests

- Electronic signature validation
- Audit trail immutability
- User authentication requirements
- Data integrity checks
- Access control enforcement

### HIPAA Compliance Tests

- PHI encryption at rest and in transit
- Access logging and monitoring
- Minimum necessary standard
- Data retention policies
- Role-based access controls

## Performance Benchmarks

| Operation | Target | Test |
|-----------|--------|------|
| Dashboard Load | < 3s | `test_dashboard_performance` |
| API Response | < 500ms | `test_api_response_time` |
| Data Pipeline (100k rows) | < 10s | `test_pipeline_performance_large_data` |
| Report Generation | < 30s | `test_report_generation_speed` |
| PHI Encryption | < 1ms/record | `test_encryption_performance` |

## Writing Tests

### Test Structure

```python
import pytest
from tests.conftest import expected_result

class TestFeatureName:
    """Test suite description"""
    
    @pytest.mark.unit
    @pytest.mark.critical
    @expected_result("Clear description of expected outcome")
    async def test_specific_functionality(self, db_session, test_user):
        """Test description explaining what is being validated"""
        # Arrange
        test_data = create_test_data()
        
        # Act
        result = await perform_action(test_data)
        
        # Assert
        assert result.status == "success"
        assert result.data == expected_data
```

### Best Practices

1. **Use Markers**: Tag tests appropriately for easy filtering
2. **Document Expected Results**: Use `@expected_result` decorator
3. **Clear Descriptions**: Write descriptive docstrings
4. **Isolated Tests**: Each test should be independent
5. **Use Fixtures**: Leverage pytest fixtures for setup
6. **Mock External Services**: Use httpx_mock for API calls
7. **Test Data**: Use factories for consistent test data

## CI/CD Integration

### GitHub Actions

```yaml
name: Run Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Run tests
      run: python run_tests.py
    - name: Upload reports
      uses: actions/upload-artifact@v3
      with:
        name: test-reports
        path: Reports/
```

### Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit
python run_tests.py --type unit --pytest-args "-x"
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure PYTHONPATH includes project root
2. **Database Connection**: Check test database is running
3. **Slow Tests**: Use `-n auto` for parallel execution
4. **Failed Compliance Tests**: Review audit requirements

### Debug Mode

```bash
# Run with detailed output
pytest -vvs tests/test_phase1_foundation.py::TestPhase1Foundation::test_create_organization

# Run with pdb on failure
pytest --pdb tests/test_compliance_21cfr_hipaa.py
```

## Coverage Goals

- Overall: 80% minimum
- Critical paths: 95% minimum
- Compliance code: 100% required
- New features: 90% before merge

## Contributing

1. Write tests for all new features
2. Ensure compliance tests pass
3. Update test documentation
4. Review coverage reports
5. Fix any failing tests before PR

---

For questions or issues with the testing framework, please contact the development team.