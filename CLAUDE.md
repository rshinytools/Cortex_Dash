# Using Claude for the Clinical Dashboard Platform Project

## 🤖 Overview

This guide helps you leverage Claude effectively throughout your clinical dashboard platform development. Claude can assist with architecture decisions, code generation, debugging, and problem-solving.

- **Important**: Whenever you are compacting a conversation, it should also be saved in Conversation folder in the root of the project. Everytime a conversation is compacted save it as DDMMMYYYHHMMSS.json. 

## 🚨 CRITICAL DEVELOPMENT PRINCIPLES - READ FIRST

### Communication Protocol
- **ALWAYS** address the user as "Sagarmatha AI" in all interactions
- **ALWAYS** Show a list of created and updated files
- **ALWAYS** create a TODO list before implementing anything
- **ALWAYS** Remember that this is a 21 CFR Part 11 compliant dashboard so every action and everything that happens in the dashboard needs to go through audit trial so keep that in mind when adding new things. 
- **MUST** ask explicit permission before reimplementing features or systems from scratch

### Development Philosophy
- **Simplicity Over Cleverness**: Prefer simple, clean, maintainable solutions over clever or complex ones, even if the latter are more concise or performant
- **Readability First**: Readability and maintainability are primary concerns
- **Minimal Changes**: Make the smallest reasonable changes to get to the desired outcome
- **No Unrelated Fixes**: NEVER make code changes that aren't directly related to the current task
- **Preserve Implementation**: NEVER throw away old implementations when fixing bugs without explicit permission
- **Debug Don't Restart**: When something doesn't work, debug and fix it - don't start over with a simple version
- **Clinical Data First**: Always think from a clinical study data perspective using CDISC SDTM and ADaM standards for all coding and mapping decisions
- **Fix Errors Immediately**: Fix all linter and TypeScript errors immediately - don't leave them for the user to fix
- **Update Documentation**: Whenever new features are added or existing ones updated, MUST update USER_MANUAL.md file to keep it current

### Code Standards (NON-NEGOTIABLE)
- **File Headers**: All code files MUST start with 2-line ABOUTME comment explaining the file's purpose
- **Comment Format**: Each comment line starts with "ABOUTME: " for easy grepping
- **Preserve Comments**: NEVER remove code comments unless you can prove they are actively false
- **Evergreen Comments**: Comments should describe code as it is, not how it evolved
- **Style Consistency**: Match existing file style/formatting over external standards
- **Naming Convention**: NEVER use temporal names like 'improved', 'new', 'enhanced', 'updated'

### Testing Philosophy
- **Real Data Only**: NEVER implement mock modes - always use real data and real APIs
- **No Mock Testing**: All testing must use actual system components and data

### Common Mistakes to Avoid (IMPORTANT)
- **Pydantic BaseModel Import**: ALWAYS import `BaseModel` directly from pydantic (`from pydantic import BaseModel`), NEVER use `schemas.BaseModel`
- **FastAPI Schema Classes**: When creating request/response models in API endpoints, use `BaseModel` directly, not through the schemas module
- **Example of CORRECT usage**:
  ```python
  from pydantic import BaseModel
  
  class InitSasGenerateRequest(BaseModel):  # ✅ CORRECT
      force_overwrite: bool = False
  ```
- **Example of INCORRECT usage**:
  ```python
  class InitSasGenerateRequest(schemas.BaseModel):  # ❌ WRONG - will cause AttributeError
      force_overwrite: bool = False
  ```

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Project Context Setup](#project-context-setup)
3. [Effective Prompting Strategies](#effective-prompting-strategies)
4. [Task-Specific Guidance](#task-specific-guidance)
5. [Code Generation Best Practices](#code-generation-best-practices)
6. [Debugging with Claude](#debugging-with-claude)
7. [Architecture & Design Decisions](#architecture--design-decisions)
8. [Example Prompts Library](#example-prompts-library)
9. [Claude's Limitations](#claudes-limitations)
10. [Tips for Maximum Productivity](#tips-for-maximum-productivity)

## Quick Start

### Initial Project Context

When starting a new conversation with Claude about this project, provide this context:

```
I'm building a clinical dashboard platform with these specifications:
- Multi-tenant SaaS for pharmaceutical companies
- Tech stack: FastAPI, PostgreSQL, Next.js 14, Docker
- Key features: Dynamic data pipelines, configurable dashboards, admin panel
- Using FastAPI full-stack template as base
- Need to support multiple studies per client with different data structures

```

### Claude's Strengths for This Project

✅ **Excellent for:**
- Generating boilerplate code
- API endpoint design
- Database schema optimization
- React component architecture
- Docker and CI/CD configurations
- Security best practices
- Testing strategies

⚠️ **Use with caution for:**
- Production-ready security implementations (always review)
- Performance-critical algorithms
- Regulatory compliance specifics (HIPAA, 21 CFR Part 11)

## Project Context Setup

### Essential Context to Provide

Always include these details when asking project-specific questions:

```markdown
Project: Clinical Dashboard Platform
Current Phase: [e.g., "Building data pipeline system"]
Specific Module: [e.g., "backend/app/clinical_modules/adapters"]

Tech Stack:
- Backend: FastAPI, SQLModel, PostgreSQL, Redis, Celery
- Frontend: Next.js 14, shadcn/ui, TailwindCSS, TypeScript
- Infrastructure: Docker, Docker Compose

Current Challenge: [Describe your specific issue]
```

### File Structure Context

When asking about code organization:

```
Here's my current structure:
clinical-dashboard/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── models/
│   │   └── clinical_modules/
├── frontend/
│   └── src/
└── deployment/

I need help with: [specific organizational question]
```

## Effective Prompting Strategies

### 1. The "Build-Review-Refine" Pattern

**Initial Request:**
```
Create a FastAPI endpoint for configuring study data sources. It should:
1. Support multiple data source types (API, SFTP, folder sync)
2. Validate credentials
3. Store encrypted configuration
4. Test connection before saving
```

**Review Request:**
```
Review this endpoint for:
- Security vulnerabilities
- Error handling completeness
- Performance considerations
- Best practices alignment
```

**Refinement Request:**
```
Enhance the endpoint with:
- Rate limiting
- Audit logging
- Async processing for connection tests
```

### 2. The "Show-Tell-Ask" Pattern

**Show:** Here's my current code
**Tell:** This is what it should do
**Ask:** How can I improve/fix/extend it?

Example:
```
SHOW: Here's my current pipeline executor:
[paste code]

TELL: It needs to safely execute user-provided Python scripts for data transformation

ASK: How can I add proper sandboxing and security constraints?
```

### 3. The "Incremental Building" Pattern

Instead of asking for everything at once, build incrementally:

```
Step 1: "Create the base model for StudyConfiguration"
Step 2: "Add validation methods to StudyConfiguration"
Step 3: "Create the service layer for StudyConfiguration"
Step 4: "Add the API endpoints for StudyConfiguration"
```

## Task-Specific Guidance

### Data Pipeline Development

**Effective Prompt:**
```
I need to implement a data acquisition layer that:
1. Connects to Medidata Rave API
2. Downloads SAS datasets
3. Handles pagination and rate limiting
4. Saves to /data/studies/{study_id}/source_data/{date}/

Please provide:
- Async implementation using aiohttp
- Error handling and retry logic
- Progress tracking for Celery tasks
```

**What to Include:**
- API documentation snippets
- Expected data formats
- Error scenarios to handle

### Dashboard Configuration

**Effective Prompt:**
```
Design a configuration schema for dynamic dashboards where:
- Each study can have different metrics
- Widgets can be different types (metric, chart, table)
- Field mappings vary between studies
- Configuration supports inheritance (global -> client -> study)

Use Pydantic for validation.
```

**Follow-up Questions:**
- How to handle configuration versioning?
- How to validate against available data fields?
- How to implement configuration inheritance?

### Frontend Component Development

**Effective Prompt:**
```
Create a React component for the metric configuration UI:
- Uses shadcn/ui components
- Allows selecting data source (dataset + field)
- Supports different calculation types
- Previews the metric with sample data
- TypeScript with proper types

Context: Part of admin panel for study configuration
```

### Database Schema Design

**Effective Prompt:**
```
Review and optimize this PostgreSQL schema for multi-tenant clinical data:
[paste schema]

Consider:
- Row-level security for tenant isolation
- Performance for time-series queries
- Audit trail requirements
- JSONB vs normalized tables for configurations
```

## Code Generation Best Practices

### 1. Request Complete, Working Code

❌ **Poor:** "Create a user authentication system"

✅ **Better:** 
```
Create a complete FastAPI authentication system with:
1. JWT token generation and validation
2. Password hashing with bcrypt
3. Login endpoint returning access and refresh tokens
4. Token refresh endpoint
5. Current user endpoint
6. SQLModel User model with org_id for multi-tenancy

Include all imports and error handling.
```

### 2. Specify Coding Standards

```
Follow these coding standards:
- Type hints for all functions
- Docstrings for classes and public methods
- Use async/await throughout
- Follow PEP 8
- Add inline comments for complex logic
```

### 3. Request Tests with Code

```
Also provide:
1. Unit tests using pytest
2. Integration test example
3. Test fixtures for database models
```

## Debugging with Claude

### Effective Debugging Process

1. **Provide Full Context:**
```
Error: "AttributeError: 'NoneType' object has no attribute 'id'"

Context:
- Occurs in: backend/app/api/endpoints/studies.py
- Function: get_study_configuration
- Related models: [paste Study and Organization models]
- Full stack trace: [paste]

The error happens when: [describe user action]
```

2. **Include Relevant Code:**
- The failing function
- Related models
- Database queries
- Recent changes

3. **Ask for Step-by-Step Debugging:**
```
Help me debug this step by step:
1. What are the possible causes?
2. How can I add logging to identify the issue?
3. What's the fix?
4. How to prevent this in the future?
```

### Performance Troubleshooting

```
This query is taking 5+ seconds:
[paste SQL query or SQLModel query]

Database structure:
- Table size: ~1M rows
- Indexes: [list current indexes]

How can I optimize this?
```

## Architecture & Design Decisions

### Getting Architecture Advice

**Effective Prompt:**
```
I need to decide between two approaches for handling dynamic field mappings:

Option A: Store mappings as JSONB in PostgreSQL
- Pros: Flexible, single source of truth
- Cons: Harder to query, validate

Option B: Normalized tables with foreign keys
- Pros: Referential integrity, easier queries
- Cons: Complex schema, migrations for changes

Context: 
- ~100 studies
- Mappings change monthly
- Need to validate against available fields
- Performance is important for dashboard loading

Which approach would you recommend and why?
```

### Design Pattern Implementation

```
How should I implement the Repository pattern for my clinical data models?

Requirements:
- Support multiple data sources (PostgreSQL, Parquet files)
- Async operations
- Caching layer
- Audit trail for all operations
- Multi-tenant isolation

Please provide the base repository class and an example implementation.
```

## Example Prompts Library

### 1. API Endpoint Creation

```
Create a FastAPI endpoint for executing data pipelines:

POST /api/v1/studies/{study_id}/pipeline/execute

Requirements:
- Validate study exists and user has access
- Queue Celery task for async execution
- Return task ID for status polling
- Include activity tracking
- Handle already-running pipeline

Include Pydantic models, error handling, and OpenAPI documentation.
```

### 2. Complex Data Transformation

```
Write a function to transform clinical trial data from source to analysis format:

Input: SAS dataset with columns: USUBJID, VISITNUM, VISITDAT, LBTEST, LBSTRESN
Output: Parquet file with derived variables:
- VISIT (mapped from VISITNUM)
- VISITDT (converted from SAS date)
- Lab results pivoted by LBTEST

Handle missing values and data type conversions properly.
```

### 3. Frontend State Management

```
Design a Zustand store for managing dashboard configuration:

Features needed:
- Load/save configuration
- Undo/redo support
- Real-time validation
- Optimistic updates
- Persist to backend

Include TypeScript types and all actions.
```

### 4. Testing Strategy

```
Create a comprehensive testing strategy for the metric calculation engine:

Cover:
- Unit tests for each adapter type
- Integration tests with sample data
- Performance tests for large datasets
- Edge cases (null values, empty datasets)
- Mock data factories

Use pytest and include fixtures.
```

### 5. CI/CD Pipeline

```
Create a GitHub Actions workflow for deploying to a specific client:

Requirements:
- Build and test on PR
- Deploy to staging on merge to develop
- Deploy to production with manual approval
- Client-specific configurations
- Database migrations
- Zero-downtime deployment
- Rollback capability
```

## Claude's Limitations

### Be Aware Of:

1. **Date Cutoff**: Claude's knowledge cutoff means it might not know the latest versions of libraries
   - Always verify package versions
   - Check for deprecated features

2. **Context Window**: For large codebases
   - Break down problems into smaller chunks
   - Provide only relevant code context
   - Use multiple conversations for different modules

3. **Code Execution**: Claude cannot run code
   - Test all generated code
   - Ask for test cases to verify functionality

4. **Security Sensitive Code**: Always review
   - Authentication implementations
   - Encryption code
   - SQL queries (for injection vulnerabilities)

5. **Regulatory Compliance**: Claude has general knowledge but
   - Consult specific regulations (HIPAA, 21 CFR Part 11)
   - Verify compliance requirements with experts

## Tips for Maximum Productivity

### 1. Use Claude for Code Reviews

```
Review this API endpoint for:
1. Security vulnerabilities
2. Performance issues
3. Error handling gaps
4. Best practices
5. Documentation completeness

[paste code]
```

### 2. Generate Multiple Solutions

```
Provide 3 different approaches for implementing real-time dashboard updates:
1. WebSockets
2. Server-Sent Events
3. Polling

Compare pros/cons for my use case: [describe specifics]
```

### 3. Documentation Generation

```
Generate comprehensive documentation for this module:
- README with setup instructions
- API documentation with examples
- Architecture decision records (ADRs)
- Inline code comments

[paste module code]
```

### 4. Code Refactoring

```
Refactor this function to be:
- More testable (dependency injection)
- More performant (identify bottlenecks)
- More maintainable (better structure)
- Type-safe (add proper TypeScript types)

[paste current code]
```

### 5. Learning and Upskilling

```
Explain how this pattern works and why it's used:
[paste advanced code pattern]

Then show me:
1. Simpler alternative
2. When to use each approach
3. Common pitfalls
```

### 6. Troubleshooting Workflow

1. **Start with the error message**
2. **Provide minimal reproducible code**
3. **Include relevant logs**
4. **Describe what you've already tried**
5. **Ask for systematic debugging approach**

### 7. Project Planning

```
Break down this feature into implementation tasks:
"Add data quality validation to the pipeline"

Consider:
- Database schema changes
- API endpoints needed
- Frontend UI components
- Testing requirements
- Deployment considerations

Estimate effort for each task.
```

## Conversation Management

### Starting Fresh

When starting a new conversation about a different module:
```
New context: Working on the frontend dashboard builder
Tech: Next.js 14, TypeScript, shadcn/ui
Previous context not needed.

[Your specific question]
```

### Continuing Complex Discussions

```
Continuing from our earlier discussion about the configuration system...
We decided on approach B (normalized tables).

Now I need help implementing the migration strategy.
```

### Saving Important Outputs

Always save Claude's responses for:
- Architecture decisions
- Complex implementations
- Debugging solutions
- Best practices guidance

Consider creating a `docs/claude-insights/` directory in your project.

## Summary

Claude is most effective when you:
1. Provide clear, specific context
2. Break complex problems into smaller pieces
3. Ask for complete, working solutions
4. Review and test all generated code
5. Use iterative refinement
6. Leverage Claude for learning and best practices

Remember: Claude is a powerful assistant but always verify critical implementations, especially for security and performance-sensitive code.

---

Happy coding! Use this guide to accelerate your clinical dashboard platform development with Claude's assistance.