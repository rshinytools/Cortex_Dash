# Clinical Dashboard Platform

A multi-tenant, enterprise-grade clinical data dashboard platform for pharmaceutical companies to visualize and analyze clinical trial data with comprehensive widget-based visualization system.

## 🚀 Key Features

- **Multi-tenant SaaS Architecture**: Complete tenant isolation with organization-based data separation
- **Dynamic Data Pipeline**: Flexible data ingestion from multiple sources (Medidata Rave API, ZIP uploads)
- **Visual Dashboard Builder**: Create dashboards without code using drag-and-drop interface
- **Comprehensive Widget Library**: 20+ specialized clinical data visualization widgets
- **Smart Study Initialization**: 4-phase initialization with real-time progress tracking
- **Intelligent Field Mapping**: CDISC SDTM/ADaM pattern recognition with confidence scoring
- **Real-time WebSocket Updates**: Live progress monitoring for long-running operations
- **Compliance Ready**: 21 CFR Part 11 and HIPAA compliant with audit trails and electronic signatures
- **Role-Based Access Control**: Granular permissions with 6 predefined system roles
- **Export & Reporting**: Generate PDF, PowerPoint, and Excel reports with scheduling
- **Cloud-Agnostic**: Deploy on AWS, Azure, or standalone Linux VMs

## 📊 Widget System

The platform includes a comprehensive widget library for clinical data visualization:

### Core Visualization Widgets
- **MetricCard**: Display key performance indicators with trend analysis
- **LineChart**: Time-series data visualization for enrollment, biomarkers, and trends
- **BarChart**: Categorical data comparisons with horizontal/vertical orientations
- **PieChart**: Distribution analysis with donut chart support
- **DataTable**: Interactive tabular data with sorting, filtering, and pagination
- **SafetyMetrics**: Specialized adverse event monitoring and safety signal detection
- **PatientTimeline**: Chronological visualization of clinical events per patient

### Advanced Features
- **Interactive Dashboards**: Real-time data updates and drill-down capabilities
- **Export Functionality**: PNG, PDF, CSV, and JSON export formats
- **Responsive Design**: Mobile-first approach with adaptive layouts
- **Storybook Documentation**: Comprehensive component library with live examples
- **TypeScript Support**: Full type safety and IntelliSense support

## 🛠️ Tech Stack

- **Backend**: FastAPI, PostgreSQL, Redis, Celery, SQLModel
- **Frontend**: Next.js 14, shadcn/ui, TailwindCSS, TypeScript
- **Infrastructure**: Docker, Docker Compose (cloud-agnostic)
- **Testing**: Pytest with comprehensive test coverage

## 📋 Prerequisites

- Python 3.11+
- Node.js 18+
- Docker 24+
- Docker Compose 2.20+
- PostgreSQL 15+
- Redis 7+
- Make (for running commands)

## 🚦 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/rshinytools/Cortex_Dash.git
cd Cortex_Dash
```

### 2. Quick Start with Make

```bash
# Complete system setup and start
make restart-all

# Or for a quick start with test data
make quickstart
```

### 3. Access the application

- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Adminer (DB UI): http://localhost:8080
- Flower (Celery UI): http://localhost:5555

### 4. Available Make Commands

```bash
make help           # Show all available commands
make up             # Start all services
make down           # Stop all services
make restart-all    # Complete restart with setup
make dev            # Start in development mode
make test           # Run API tests
make status         # Check service status
make logs           # View logs
make clean          # Remove all data (with confirmation)
```

## 🧪 Testing

Run tests using Make commands:

```bash
# Run API tests
make test

# Run backend unit tests
make test-backend

# Format and lint code
make format
make lint
```

Test reports are generated in the `Reports/` directory.

## 📊 Project Structure

```
clinical-dashboard/
├── backend/              # FastAPI backend
│   ├── app/             # Application code
│   ├── alembic/         # Database migrations
│   └── tests/           # Backend tests
├── frontend/            # Next.js frontend
│   ├── src/            # Source code
│   │   └── components/widgets/  # Widget library
│   ├── .storybook/     # Storybook configuration
│   └── public/         # Static assets
├── tests/              # Comprehensive test suite
├── Reports/            # Test reports
├── deployment/         # Deployment configurations
└── docs/              # Comprehensive documentation
    ├── api/           # API documentation
    ├── user/          # User guides
    └── developer/     # Developer documentation
```

## 📚 Documentation

Comprehensive documentation is available in the `/docs` directory:

### 📖 User Documentation
- **[Dashboard User Guide](docs/user/dashboard-user-guide.md)**: End-user dashboard navigation and usage
- **[Study Manager Guide](docs/user/study-manager-guide.md)**: Study configuration and management
- **[System Admin Guide](docs/user/system-admin-guide.md)**: Platform administration and configuration
- **[Widget Configuration Guide](docs/user/widget-configuration-guide.md)**: Widget setup and customization

### 🔧 Developer Documentation
- **[Widget Development Guide](docs/developer/widget-development-guide.md)**: Creating custom widgets
- **[API Integration Guide](docs/developer/api-integration-guide.md)**: REST API usage and integration
- **[Deployment Guide](docs/developer/deployment-guide.md)**: Production deployment instructions
- **[Troubleshooting Guide](docs/developer/troubleshooting-guide.md)**: Common issues and solutions

### 🔌 API Documentation
- **[OpenAPI Specification](docs/api/openapi.yaml)**: Complete API specification
- **[Widget API Reference](docs/api/widget-api.md)**: Widget-specific endpoints
- **[Template API Reference](docs/api/template-api.md)**: Dashboard template management
- **[Export API Reference](docs/api/export-api.md)**: Data export functionality

### 📱 Component Library
- **Storybook**: Run `npm run storybook` in the frontend directory for interactive widget documentation
- **Widget Examples**: Comprehensive examples with live data and customization options

## 🔒 Security & Compliance

- **21 CFR Part 11**: Electronic signatures, audit trails, data integrity
- **HIPAA**: PHI encryption, access controls, audit logging
- **RBAC**: Role-based access control with granular permissions
- **Data Security**: Encryption at rest and in transit

## 📈 Performance Targets

- Dashboard loading: < 3 seconds
- API response time: < 500ms
- Data pipeline processing: < 10s for 100k rows
- Report generation: < 30 seconds

## 🤝 Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## 📄 License

This project is proprietary software. All rights reserved.

## 📞 Support

For support, email support@clinicaldashboard.com or join our Slack channel.

---

Built with ❤️ for the clinical research community