# Clinical Dashboard Platform

A multi-tenant, enterprise-grade clinical data dashboard platform for pharmaceutical companies to visualize and analyze clinical trial data.

## 🚀 Features

- **Multi-tenant SaaS Architecture**: Complete tenant isolation with organization-based data separation
- **Dynamic Data Pipeline**: Flexible data ingestion from multiple sources (Medidata Rave API, ZIP uploads)
- **Visual Dashboard Builder**: Create dashboards without code using drag-and-drop interface
- **Compliance Ready**: 21 CFR Part 11 and HIPAA compliant with audit trails and electronic signatures
- **Role-Based Access Control**: Granular permissions with 6 predefined system roles
- **Export & Reporting**: Generate PDF, PowerPoint, and Excel reports with scheduling
- **Cloud-Agnostic**: Deploy on AWS, Azure, or standalone Linux VMs

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

## 🚦 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/clinical-dashboard.git
cd clinical-dashboard
```

### 2. Set up environment variables

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Run with Docker Compose

```bash
docker-compose up -d
```

### 4. Run database migrations

```bash
docker-compose exec backend alembic upgrade head
```

### 5. Access the application

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Run all tests
python run_tests.py

# Run specific phase tests
python run_tests.py --phase 1

# Run compliance tests
python run_tests.py --compliance
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
│   └── public/         # Static assets
├── tests/              # Comprehensive test suite
├── Reports/            # Test reports
├── deployment/         # Deployment configurations
└── docs/              # Documentation
```

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