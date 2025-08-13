# Contributing to Clinical Dashboard Platform

Thank you for your interest in contributing to the Clinical Dashboard Platform! This guide will help you get started with contributing to our clinical data visualization platform.

## 🤝 Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker 24+
- Git
- Basic understanding of clinical trial data and regulatory requirements

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/yourusername/Cortex_Dash.git
   cd Cortex_Dash
   ```

2. **Setup Development Environment**
   ```bash
   # Start all services
   make restart-all
   
   # Or use Docker Compose directly
   docker-compose -f docker-compose.local.yml up -d
   ```

3. **Install Frontend Dependencies**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

4. **Install Backend Dependencies**
   ```bash
   cd backend
   pip install -e ".[dev]"
   ```

## 📋 Development Workflow

### Branch Naming Convention
- `feature/widget-enhancement` - New features
- `fix/chart-rendering-issue` - Bug fixes
- `docs/api-documentation` - Documentation updates
- `refactor/widget-architecture` - Code refactoring

### Commit Messages
Follow conventional commit format:
```
type(scope): description

Examples:
feat(widgets): add scatter plot widget
fix(safety-metrics): resolve severity color mapping
docs(api): update widget configuration examples
```

### Code Style and Standards

#### Backend (Python)
- Follow PEP 8 style guidelines
- Use type hints for all functions
- Add docstrings for classes and public methods
- Maximum line length: 100 characters

```python
# Good example
def create_widget_config(
    widget_type: str, 
    configuration: Dict[str, Any],
    user_id: int
) -> WidgetConfig:
    """Create a new widget configuration.
    
    Args:
        widget_type: Type of widget to create
        configuration: Widget-specific configuration
        user_id: ID of the user creating the widget
        
    Returns:
        Created widget configuration object
    """
    pass
```

#### Frontend (TypeScript/React)
- Use TypeScript for all new code
- Follow React functional component patterns
- Use shadcn/ui components when possible
- Add proper type definitions

```typescript
// Good example
interface WidgetProps {
  title: string;
  data: ChartData;
  configuration: WidgetConfiguration;
  loading?: boolean;
  error?: string;
}

export const MyWidget: React.FC<WidgetProps> = ({
  title,
  data,
  configuration,
  loading = false,
  error
}) => {
  // Component implementation
};
```

### File Headers
All code files must start with a 2-line ABOUTME comment:

```typescript
// ABOUTME: Brief description of what this file does
// ABOUTME: Additional context about the implementation approach
```

## 🎨 Widget Development

### Creating a New Widget

1. **Create Widget Component**
   ```bash
   # Create widget file
   touch frontend/src/components/widgets/my-new-widget.tsx
   ```

2. **Implement Widget Interface**
   ```typescript
   import { WidgetComponent } from './base-widget';
   
   export const MyNewWidget: WidgetComponent = ({
     title,
     description,
     configuration,
     data,
     loading,
     error,
     className
   }) => {
     // Widget implementation
   };
   
   // Widget metadata
   MyNewWidget.displayName = 'MyNewWidget';
   MyNewWidget.defaultHeight = 4;
   MyNewWidget.defaultWidth = 6;
   MyNewWidget.supportedExportFormats = ['png', 'json', 'csv'];
   MyNewWidget.validateConfiguration = (config) => {
     // Validation logic
     return true;
   };
   ```

3. **Add to Widget Registry**
   ```typescript
   // In widget-registry.ts
   import { MyNewWidget } from './my-new-widget';
   
   widgetRegistry.register('my-new-widget', MyNewWidget);
   ```

4. **Create Storybook Stories**
   ```bash
   touch frontend/src/components/widgets/my-new-widget.stories.tsx
   ```

5. **Add Tests**
   ```bash
   touch frontend/src/components/widgets/__tests__/my-new-widget.test.tsx
   ```

### Widget Guidelines

#### Clinical Data Considerations
- Always validate data formats and handle missing values
- Follow CDISC standards for variable naming when applicable
- Include appropriate error handling for clinical data edge cases
- Consider regulatory compliance (21 CFR Part 11, HIPAA)

#### User Experience
- Provide meaningful loading states
- Show clear error messages
- Support responsive design (mobile-first)
- Include tooltips and help text

#### Performance
- Implement virtualization for large datasets
- Use React.memo for expensive components
- Optimize re-renders with proper dependency arrays
- Consider data sampling for visualization performance

## 🧪 Testing

### Running Tests

```bash
# Backend tests
make test-backend

# Frontend tests
cd frontend && npm test

# End-to-end tests
make test

# Storybook visual tests
cd frontend && npm run test-storybook
```

### Test Coverage Requirements
- Minimum 80% code coverage for new features
- All widget components must have unit tests
- API endpoints require integration tests
- Critical paths need end-to-end tests

### Writing Tests

#### Widget Tests
```typescript
import { render, screen } from '@testing-library/react';
import { MyWidget } from '../my-widget';

describe('MyWidget', () => {
  const defaultProps = {
    title: 'Test Widget',
    data: mockData,
    configuration: mockConfig,
  };

  it('renders with provided title', () => {
    render(<MyWidget {...defaultProps} />);
    expect(screen.getByText('Test Widget')).toBeInTheDocument();
  });

  it('handles loading state', () => {
    render(<MyWidget {...defaultProps} loading={true} />);
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });
});
```

#### API Tests
```python
def test_create_widget_config(client: TestClient, db: Session):
    """Test widget configuration creation."""
    widget_data = {
        "widget_type": "line-chart",
        "configuration": {"xAxis": "date", "yAxis": "value"}
    }
    
    response = client.post("/api/v1/widgets/config", json=widget_data)
    assert response.status_code == 201
    assert response.json()["widget_type"] == "line-chart"
```

## 📖 Documentation

### Documentation Standards
- Update relevant documentation for all changes
- Include code examples in documentation
- Use clear, clinical-context appropriate language
- Add screenshots for UI changes

### API Documentation
- Update OpenAPI schema for API changes
- Include request/response examples
- Document error codes and responses
- Add security considerations

### Widget Documentation
- Create comprehensive Storybook stories
- Include multiple data scenarios
- Document configuration options
- Add accessibility notes

## 🔒 Security Guidelines

### Clinical Data Handling
- Never log PHI or PII data
- Use parameterized queries for database operations
- Validate all input data
- Implement proper access controls

### Code Security
- Follow OWASP guidelines
- Use security headers
- Implement CSRF protection
- Validate file uploads

### Dependency Management
- Keep dependencies updated
- Review security advisories
- Use npm audit and pip-audit
- Document security exceptions

## 🚀 Deployment and Release

### Development Process
1. Create feature branch from `develop`
2. Implement changes with tests
3. Update documentation
4. Create pull request
5. Code review and approval
6. Merge to `develop`
7. Deploy to staging for testing
8. Merge to `main` for production

### Release Process
- Semantic versioning (MAJOR.MINOR.PATCH)
- Changelog updates
- Migration scripts for database changes
- Deployment validation checklist

## 🤝 Pull Request Guidelines

### PR Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No breaking changes (or properly documented)
- [ ] Database migrations included if needed
- [ ] Security considerations addressed

### PR Description Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Clinical Impact
Describe impact on clinical workflows

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Screenshots (if applicable)
Add screenshots for UI changes

## Checklist
- [ ] Code review completed
- [ ] Documentation updated
- [ ] Tests added/updated
```

## 🐛 Bug Reports

### Bug Report Template
```markdown
**Bug Description**
Clear description of the bug

**Steps to Reproduce**
1. Go to '...'
2. Click on '....'
3. See error

**Expected Behavior**
What should happen

**Actual Behavior**
What actually happens

**Clinical Context**
How this affects clinical workflows

**Environment**
- Browser: [e.g. Chrome 91]
- OS: [e.g. Windows 10]
- Widget: [e.g. SafetyMetrics]
- Data: [e.g. SDTM datasets]

**Additional Context**
Any other relevant information
```

## 💡 Feature Requests

### Feature Request Template
```markdown
**Feature Description**
Clear description of the proposed feature

**Clinical Use Case**
Specific clinical scenario this addresses

**Proposed Solution**
How you envision this working

**Alternative Solutions**
Other approaches considered

**Impact Assessment**
- User types affected: [ ]
- Regulatory considerations: [ ]
- Performance impact: [ ]
```

## 📞 Getting Help

### Communication Channels
- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and ideas
- **Email**: technical-team@clinicaldashboard.com

### Code Review Process
- All PRs require at least 2 approvals
- Security-sensitive changes require security team review
- Clinical features require clinical SME review
- Breaking changes require architecture team review

## 🏆 Recognition

We value all contributions! Contributors will be:
- Listed in our CONTRIBUTORS.md file
- Recognized in release notes
- Invited to contributor meetings
- Eligible for contributor swag

## 📜 Code of Conduct

### Our Pledge
We pledge to make participation in our project a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, gender identity and expression, level of experience, nationality, personal appearance, race, religion, or sexual identity and orientation.

### Standards
Examples of behavior that contributes to creating a positive environment:
- Using welcoming and inclusive language
- Being respectful of differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

### Enforcement
Instances of abusive, harassing, or otherwise unacceptable behavior may be reported by contacting the project team at conduct@clinicaldashboard.com.

---

Thank you for contributing to the Clinical Dashboard Platform! Your contributions help improve clinical data visualization for the entire research community. 🎉