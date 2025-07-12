# Clinical Dashboard Platform - Implementation Guide

> **Note**: This implementation guide has been enhanced with enterprise features including:
> - Role-Based Access Control (RBAC) system with 21 CFR Part 11 & HIPAA compliance
> - Platform administration panel for SaaS management  
> - Comprehensive export engine with scheduled reporting
> - Public API for external integrations
> - Fully asynchronous, non-blocking data pipeline architecture
> - Cloud-agnostic deployment (AWS, Azure, or Linux VM)
> - Priority integrations: Medidata Rave API and ZIP file uploads

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Prerequisites](#prerequisites)
3. [Phase 1: Foundation Setup (Week 1-2)](#phase-1-foundation-setup-week-1-2)
4. [Phase 2: Core Infrastructure with RBAC (Week 3-4)](#phase-2-core-infrastructure-week-3-4)
5. [Phase 3: Data Pipeline System (Week 5-6)](#phase-3-data-pipeline-system-week-5-6)
6. [Phase 4: Export & Reporting System (Week 7-8)](#phase-4-export--reporting-system-week-7-8)
7. [Phase 5: Configuration Engine (Week 9-10)](#phase-5-configuration-engine-week-9-10)
8. [Phase 6: Dashboard Builder (Week 11-12)](#phase-6-dashboard-builder-week-11-12)
9. [Phase 7: Admin Panel (Week 13-14)](#phase-7-admin-panel-week-13-14)
10. [Phase 8: Testing & Security (Week 15-16)](#phase-8-testing--security-week-15-16)
11. [Phase 9: Deployment & CI/CD (Week 17-18)](#phase-9-deployment--cicd-week-17-18)
12. [Troubleshooting Guide](#troubleshooting-guide)
13. [Best Practices](#best-practices)

## Project Overview

**Goal**: Build a multi-tenant, enterprise-grade clinical data dashboard platform that allows pharmaceutical companies to visualize and analyze clinical trial data without requiring code changes for new studies.

**Key Features**:
- Multi-client SaaS architecture with complete tenant isolation
- Dynamic data pipeline configuration with multiple source support (Priority: Medidata Rave API, ZIP file uploads)
- Flexible dashboard builder with visual configuration
- Complete admin panel for self-service management
- Comprehensive activity tracking and audit trail for 21 CFR Part 11 compliance
- Role-Based Access Control (RBAC) for enterprise security
- Platform administration panel for SaaS management
- Export engine with scheduled reporting (PDF, PowerPoint, Excel)
- Public API for external integrations and automation
- Asynchronous, non-blocking architecture for scalability
- HIPAA compliant with PHI encryption and access controls
- Flexible data transformation pipeline with extensive Python scripting capabilities

**Tech Stack**:
- **Backend**: FastAPI, PostgreSQL, Redis, Celery, SQLModel
- **Frontend**: Next.js 14, shadcn/ui, TailwindCSS, TypeScript
- **Infrastructure**: Docker, Docker Compose (cloud-agnostic)
- **CI/CD**: GitHub Actions, GitOps, Blue-Green Deployments
- **Security**: JWT, API Keys, RBAC, encryption at rest and in transit

**Data Architecture**:
- **Raw Data**: Direct from EDC systems (Medidata Rave) - immutable after upload
- **Processed Data**: Standardized and cleaned datasets
- **Analysis Data**: Derived datasets from complex transformations
- **Storage**: PostgreSQL for metadata, Parquet files for clinical data
- **Volume**: Designed to scale from MB to GB per study extract

**Compliance & Performance**:
- **21 CFR Part 11**: Complete audit trail, electronic signatures, access controls
- **HIPAA**: PHI encryption, access logging, secure data handling
- **Performance Targets**: 
  - Dashboard loading < 3 seconds
  - API response < 500ms
  - Report generation < 30 seconds
- **User Scale**: 10-40 concurrent users per tenant

## Prerequisites

### Required Tools
```bash
# Check versions
python --version          # Python 3.11+
node --version           # Node.js 18+
docker --version         # Docker 24+
docker-compose --version # Docker Compose 2.20+
git --version           # Git 2.40+

# Optional but recommended
terraform --version      # Terraform 1.5+
ansible --version       # Ansible 2.15+
```

### Development Environment Setup
```bash
# Clone the FastAPI template
git clone https://github.com/fastapi/full-stack-fastapi-template.git clinical-dashboard
cd clinical-dashboard

# Create project structure
mkdir -p backend/app/clinical_modules/{data_pipeline,adapters,validators}
mkdir -p frontend/src/components/{dashboard,admin,clinical}
mkdir -p deployment/{terraform,ansible,scripts}
mkdir -p docs/{api,user,technical}

# Initialize git for your project
rm -rf .git
git init
git add .
git commit -m "Initial commit from FastAPI template"
```

## Phase 1: Foundation Setup (Week 1-2)

### Task 1.1: Database Schema Design

Create the multi-tenant schema:

```python
# backend/app/models/__init__.py
from .user import User, UserCreate, UserUpdate
from .organization import Organization, OrganizationCreate
from .study import Study, StudyCreate, StudyUpdate
from .dashboard import Dashboard, DashboardConfig
from .activity_log import ActivityLog
from .data_source import DataSource, DataSourceConfig

# backend/app/models/organization.py
from sqlmodel import SQLModel, Field, Column, JSON, Relationship
from typing import Optional, List
from datetime import datetime
import uuid

class Organization(SQLModel, table=True):
    """Multi-tenant organization model"""
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(index=True, nullable=False)
    code: str = Field(unique=True, index=True, nullable=False)
    config: dict = Field(default={}, sa_column=Column(JSON))
    theme: dict = Field(default={}, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)
    
    # Relationships
    studies: List["Study"] = Relationship(back_populates="organization")
    users: List["User"] = Relationship(back_populates="organization")
```

### Task 1.2: Update Environment Configuration

```bash
# .env.local
# FastAPI Template Settings
PROJECT_NAME="Clinical Dashboard Platform"
STACK_NAME=clinical-dashboard

# Security
SECRET_KEY=your-secret-key-here
FIRST_SUPERUSER=admin@example.com
FIRST_SUPERUSER_PASSWORD=changethis
BACKEND_CORS_ORIGINS=["http://localhost:3000","http://localhost:8000"]

# Database
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=changethis
POSTGRES_DB=clinical_dashboard

# Redis
REDIS_URL=redis://localhost:6379/0

# Clinical Platform Specific
ENABLE_MULTI_TENANCY=true
DEFAULT_TENANT=demo
DATA_STORAGE_PATH=/data/studies
ACTIVITY_TRACKING_ENABLED=true
```

### Task 1.3: Initialize Database Migrations

```bash
# Create new migration
docker-compose exec backend alembic revision --autogenerate -m "Add clinical platform models"

# Apply migrations
docker-compose exec backend alembic upgrade head
```

### Task 1.4: Study Creation Workflow & Folder Structure

When an admin creates a study, the system automatically initializes a comprehensive folder structure for data management:

```
/data/studies/{org_id}/{study_id}/
├── source_data/
│   └── {YYYYMMDD_HHMMSS}/  # Timestamped folders for each data upload/sync
│       ├── *.parquet        # Converted data files
│       └── metadata.json    # Upload metadata
├── pipeline_output/
│   └── {YYYYMMDD_HHMMSS}/  # Timestamped folders for pipeline outputs
│       ├── *.parquet        # Transformed data
│       └── metadata.json    # Pipeline execution metadata
├── exports/                 # User-generated exports
├── temp/                    # Temporary processing files
└── logs/                    # Processing logs
```

**Key Features:**
- Unified folder structure for all data sources (manual upload, API, sFTP)
- YYYYMMDD_HHMMSS timestamp format for version tracking
- Automatic parquet conversion for all file types
- Version management with activation/rollback capabilities
        
        # Define folder structure
        folders = [
            f"{study_root}/raw",                    # Original EDC data
            f"{study_root}/raw/medidata",           # Medidata Rave extracts
            f"{study_root}/raw/uploads",            # Manual ZIP uploads
            f"{study_root}/raw/archive",            # Old versions
            
            f"{study_root}/processed",              # Cleaned/standardized data
            f"{study_root}/processed/current",      # Latest processed data
            f"{study_root}/processed/archive",      # Historical processed data
            
            f"{study_root}/analysis",               # Derived datasets
            f"{study_root}/analysis/datasets",      # Analysis-ready data
            f"{study_root}/analysis/scripts",       # Transformation scripts
            
            f"{study_root}/exports",                # Generated reports
            f"{study_root}/exports/pdf",            
            f"{study_root}/exports/excel",
            f"{study_root}/exports/powerpoint",
            f"{study_root}/exports/scheduled",      # Scheduled report outputs
            
            f"{study_root}/temp",                   # Temporary processing files
            f"{study_root}/logs",                   # Pipeline execution logs
            f"{study_root}/metadata",               # Data dictionaries, mappings
            f"{study_root}/config",                 # Study-specific configurations
        ]
        
        # Create all folders
        for folder in folders:
            os.makedirs(folder, exist_ok=True)
            
        # Set permissions for 21 CFR Part 11 compliance
        self._set_folder_permissions(study_root)
        
        # Create initial metadata files
        await self._create_initial_metadata(study, study_root)
        
    def _set_folder_permissions(self, study_root: str):
        """Set appropriate permissions for study folders"""
        # Raw data folders become read-only after data upload (21 CFR Part 11)
        # Owner: read, write, execute | Group: read, execute | Others: no access
        for root, dirs, files in os.walk(study_root):
            for dir in dirs:
                os.chmod(os.path.join(root, dir), 0o750)
            for file in files:
                os.chmod(os.path.join(root, file), 0o640)
```

**Created Folder Structure**:
```
/data/studies/
└── {organization_id}/
    └── {study_id}/
        ├── raw/                    # Source data (immutable after upload)
        │   ├── medidata/          # Medidata Rave API downloads
        │   ├── uploads/           # Manual ZIP uploads
        │   └── archive/           # Version history
        ├── processed/             # Standardized data
        │   ├── current/          # Latest version
        │   └── archive/          # Historical versions
        ├── analysis/             # Derived datasets
        │   ├── datasets/        # Analysis-ready data
        │   └── scripts/         # Transformation scripts
        ├── exports/             # Generated outputs
        ├── temp/                # Temporary processing
        ├── logs/                # Execution logs
        ├── metadata/            # Data dictionaries
        └── config/              # Study configurations
```

### Deliverables - Phase 1
- [ ] Complete database schema with compliance fields
- [ ] Environment configuration
- [ ] Initial migrations
- [ ] Basic project structure
- [ ] Study folder creation service
- [ ] File permission management for 21 CFR Part 11

## Phase 2: Core Infrastructure (Week 3-4)

### Task 2.1: Role-Based Access Control (RBAC)

```python
# backend/app/models/rbac.py
from sqlmodel import SQLModel, Field, Relationship, Column, JSON, UniqueConstraint
from typing import List, Optional
from datetime import datetime
import uuid
from sqlalchemy import String, Integer, ARRAY

class Permission(SQLModel, table=True):
    """Granular permissions for the platform"""
    __tablename__ = "permissions"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    resource: str = Field(index=True)  # e.g., "study", "dashboard", "pipeline"
    action: str = Field(index=True)    # e.g., "read", "write", "execute", "delete"
    scope: Optional[str] = Field(default="own")  # e.g., "own", "team", "all"
    description: Optional[str] = None
    
    # Relationships
    roles: List["Role"] = Relationship(back_populates="permissions", link_model="RolePermission")
    
    __table_args__ = (
        UniqueConstraint("resource", "action", "scope", name="unique_permission"),
    )
    
    @property
    def code(self) -> str:
        """Generate permission code for easy checking"""
        return f"{self.resource}:{self.action}:{self.scope or 'all'}"

class Role(SQLModel, table=True):
    """Roles that group permissions"""
    __tablename__ = "roles"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(unique=True, index=True)
    description: Optional[str] = None
    org_id: Optional[uuid.UUID] = Field(foreign_key="organizations.id", nullable=True)
    is_system_role: bool = Field(default=False)  # Platform-wide roles
    is_default: bool = Field(default=False)  # Auto-assign to new users
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    permissions: List[Permission] = Relationship(back_populates="roles", link_model="RolePermission")
    users: List["User"] = Relationship(back_populates="roles", link_model="UserRole")
    organization: Optional["Organization"] = Relationship(back_populates="roles")

class RolePermission(SQLModel, table=True):
    """Many-to-many relationship between roles and permissions"""
    __tablename__ = "role_permissions"
    
    role_id: uuid.UUID = Field(foreign_key="roles.id", primary_key=True)
    permission_id: uuid.UUID = Field(foreign_key="permissions.id", primary_key=True)
    granted_at: datetime = Field(default_factory=datetime.utcnow)
    
class UserRole(SQLModel, table=True):
    """Many-to-many relationship between users and roles"""
    __tablename__ = "user_roles"
    
    user_id: uuid.UUID = Field(foreign_key="users.id", primary_key=True)
    role_id: uuid.UUID = Field(foreign_key="roles.id", primary_key=True)
    study_id: Optional[uuid.UUID] = Field(foreign_key="studies.id", nullable=True)
    assigned_at: datetime = Field(default_factory=datetime.utcnow)
    assigned_by: uuid.UUID = Field(foreign_key="users.id")
    expires_at: Optional[datetime] = None

# backend/app/core/rbac_setup.py
"""Initialize system roles and permissions"""
from typing import Dict, List
from app.models import Role, Permission
from app.core.db import get_session

SYSTEM_PERMISSIONS = [
    # Platform administration
    ("platform", "manage", "all", "Manage platform settings"),
    ("tenant", "create", "all", "Create new tenants"),
    ("tenant", "manage", "all", "Manage all tenants"),
    ("tenant", "view", "all", "View all tenants"),
    
    # Organization management
    ("organization", "manage", "own", "Manage own organization"),
    ("organization", "view", "own", "View own organization"),
    
    # Study management
    ("study", "create", "own", "Create studies in own organization"),
    ("study", "manage", "assigned", "Manage assigned studies"),
    ("study", "view", "assigned", "View assigned studies"),
    ("study", "delete", "assigned", "Delete assigned studies"),
    
    # Pipeline operations
    ("pipeline", "execute", "assigned", "Execute data pipelines"),
    ("pipeline", "configure", "assigned", "Configure pipelines"),
    ("pipeline", "view", "assigned", "View pipeline status"),
    
    # Dashboard operations
    ("dashboard", "create", "assigned", "Create dashboards"),
    ("dashboard", "edit", "assigned", "Edit dashboards"),
    ("dashboard", "view", "assigned", "View dashboards"),
    ("dashboard", "delete", "assigned", "Delete dashboards"),
    ("dashboard", "export", "assigned", "Export dashboard data"),
    
    # Data operations
    ("data", "upload", "assigned", "Upload data files"),
    ("data", "view", "assigned", "View data"),
    ("data", "export", "assigned", "Export data"),
    ("data", "delete", "assigned", "Delete data"),
    
    # User management
    ("user", "create", "own", "Create users in organization"),
    ("user", "manage", "own", "Manage organization users"),
    ("user", "view", "own", "View organization users"),
    
    # Audit
    ("audit", "view", "own", "View audit logs"),
    ("audit", "export", "own", "Export audit logs"),
    
    # API access
    ("api", "create_key", "own", "Create API keys"),
    ("api", "manage_key", "own", "Manage API keys"),
]

SYSTEM_ROLES: Dict[str, Dict] = {
    "platform_admin": {
        "description": "Full platform administration access",
        "is_system_role": True,
        "permissions": ["*:*:*"]  # Special case: all permissions
    },
    "org_admin": {
        "description": "Organization administrator",
        "is_system_role": True,
        "permissions": [
            "organization:manage:own",
            "study:create:own",
            "study:manage:assigned",
            "user:create:own",
            "user:manage:own",
            "dashboard:*:assigned",
            "pipeline:*:assigned",
            "data:*:assigned",
            "audit:view:own",
            "api:*:own"
        ]
    },
    "study_manager": {
        "description": "Manage specific studies",
        "is_system_role": True,
        "permissions": [
            "study:manage:assigned",
            "study:view:assigned",
            "pipeline:*:assigned",
            "dashboard:*:assigned",
            "data:*:assigned",
            "user:view:own"
        ]
    },
    "data_scientist": {
        "description": "Analyze data and create dashboards",
        "is_system_role": True,
        "permissions": [
            "study:view:assigned",
            "dashboard:create:assigned",
            "dashboard:edit:assigned",
            "dashboard:view:assigned",
            "dashboard:export:assigned",
            "data:view:assigned",
            "data:export:assigned",
            "pipeline:view:assigned"
        ]
    },
    "clinical_monitor": {
        "description": "View dashboards and export reports",
        "is_system_role": True,
        "permissions": [
            "study:view:assigned",
            "dashboard:view:assigned",
            "dashboard:export:assigned",
            "data:export:assigned"
        ]
    },
    "auditor": {
        "description": "Read-only access with audit trail visibility",
        "is_system_role": True,
        "permissions": [
            "study:view:assigned",
            "dashboard:view:assigned",
            "audit:view:own",
            "audit:export:own"
        ]
    }
}

async def initialize_rbac():
    """Initialize system roles and permissions"""
    async with get_session() as session:
        # Create permissions
        for resource, action, scope, description in SYSTEM_PERMISSIONS:
            perm = await session.exec(
                select(Permission).where(
                    Permission.resource == resource,
                    Permission.action == action,
                    Permission.scope == scope
                )
            )
            if not perm.first():
                permission = Permission(
                    resource=resource,
                    action=action,
                    scope=scope,
                    description=description
                )
                session.add(permission)
        
        await session.commit()
        
        # Create system roles
        for role_name, role_config in SYSTEM_ROLES.items():
            role = await session.exec(
                select(Role).where(Role.name == role_name)
            )
            if not role.first():
                role = Role(
                    name=role_name,
                    description=role_config["description"],
                    is_system_role=role_config["is_system_role"]
                )
                session.add(role)
                await session.commit()
                
                # Assign permissions
                if role_config["permissions"] == ["*:*:*"]:
                    # Assign all permissions for platform admin
                    all_perms = await session.exec(select(Permission))
                    for perm in all_perms:
                        role.permissions.append(perm)
                else:
                    # Assign specific permissions
                    for perm_code in role_config["permissions"]:
                        if "*" in perm_code:
                            # Handle wildcard permissions
                            resource, action, scope = perm_code.split(":")
                            query = select(Permission)
                            if resource != "*":
                                query = query.where(Permission.resource == resource)
                            if action != "*":
                                query = query.where(Permission.action == action)
                            if scope != "*":
                                query = query.where(Permission.scope == scope)
                            
                            perms = await session.exec(query)
                            for perm in perms:
                                role.permissions.append(perm)
                        else:
                            # Exact permission match
                            resource, action, scope = perm_code.split(":")
                            perm = await session.exec(
                                select(Permission).where(
                                    Permission.resource == resource,
                                    Permission.action == action,
                                    Permission.scope == scope
                                )
                            )
                            if perm_obj := perm.first():
                                role.permissions.append(perm_obj)
                
                await session.commit()

# backend/app/core/rbac_middleware.py
from typing import List, Optional, Set
from fastapi import Depends, HTTPException, status, Request
from sqlmodel import select
from app.models import User, UserRole, Role, Permission
from app.core.db import get_session
from app.api.deps import get_current_user

class PermissionChecker:
    """Check if user has required permissions"""
    
    def __init__(self, required_permissions: List[str]):
        """
        Initialize with required permissions
        Args:
            required_permissions: List of permission codes like ["study:read:assigned", "dashboard:view:assigned"]
        """
        self.required_permissions = set(required_permissions)
    
    async def __call__(
        self,
        request: Request,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_session)
    ) -> User:
        """Check if user has all required permissions"""
        
        # Platform admins bypass all checks
        if await self.is_platform_admin(current_user, db):
            return current_user
        
        # Get user's effective permissions
        user_permissions = await self.get_user_permissions(current_user, db, request)
        
        # Check if user has all required permissions
        missing_permissions = self.required_permissions - user_permissions
        
        if missing_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permissions: {', '.join(missing_permissions)}"
            )
        
        return current_user
    
    async def is_platform_admin(self, user: User, db: AsyncSession) -> bool:
        """Check if user has platform admin role"""
        user_roles = await db.exec(
            select(Role)
            .join(UserRole)
            .where(UserRole.user_id == user.id)
            .where(Role.name == "platform_admin")
        )
        return bool(user_roles.first())
    
    async def get_user_permissions(
        self, 
        user: User, 
        db: AsyncSession,
        request: Request
    ) -> Set[str]:
        """Get all effective permissions for a user"""
        permissions = set()
        
        # Get user's roles (including study-specific roles)
        study_id = request.path_params.get("study_id")
        
        query = (
            select(Permission)
            .join(RolePermission)
            .join(Role)
            .join(UserRole)
            .where(UserRole.user_id == user.id)
        )
        
        # If checking study-specific permission, include study-specific roles
        if study_id:
            query = query.where(
                (UserRole.study_id == None) | (UserRole.study_id == study_id)
            )
        
        perms = await db.exec(query)
        
        for perm in perms:
            permissions.add(perm.code)
            
            # Handle scope inheritance
            if perm.scope == "all":
                # "all" scope includes "own" and "assigned"
                permissions.add(f"{perm.resource}:{perm.action}:own")
                permissions.add(f"{perm.resource}:{perm.action}:assigned")
            elif perm.scope == "own" and user.org_id:
                # Check if resource belongs to user's org
                permissions.add(f"{perm.resource}:{perm.action}:assigned")
        
        return permissions

# Convenience permission checkers
require_study_read = PermissionChecker(["study:view:assigned"])
require_study_write = PermissionChecker(["study:manage:assigned"])
require_pipeline_execute = PermissionChecker(["pipeline:execute:assigned"])
require_dashboard_edit = PermissionChecker(["dashboard:edit:assigned"])
require_org_admin = PermissionChecker(["organization:manage:own"])
require_platform_admin = PermissionChecker(["platform:manage:all"])

### Task 2.2: Multi-Tenant Middleware

```python
# backend/app/core/multi_tenant.py
from fastapi import Request, HTTPException, Depends
from typing import Optional, Annotated
from sqlmodel import select
from app.core.db import get_session
from app.models import Organization

class TenantContext:
    def __init__(self):
        self.current_tenant: Optional[str] = None
        self.current_org: Optional[Organization] = None

tenant_context = TenantContext()

async def get_current_tenant(request: Request) -> str:
    """Extract tenant from request"""
    # Option 1: From subdomain
    host = request.headers.get("host", "")
    if "." in host:
        subdomain = host.split(".")[0]
        if subdomain not in ["www", "api", "platform"]:  # platform subdomain for super admin
            return subdomain
    
    # Option 2: From header
    if "X-Tenant-ID" in request.headers:
        return request.headers["X-Tenant-ID"]
    
    # Option 3: From JWT
    if hasattr(request.state, "user") and request.state.user:
        return request.state.user.org_code
    
    # Default tenant
    return "demo"

async def get_current_organization(
    tenant: Annotated[str, Depends(get_current_tenant)],
    session: Annotated[AsyncSession, Depends(get_session)]
) -> Organization:
    """Get current organization from tenant"""
    stmt = select(Organization).where(Organization.code == tenant)
    org = await session.exec(stmt)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org.first()
```

### Task 2.3: API Structure with RBAC

```python
# backend/app/api/api_v1/api.py
from fastapi import APIRouter
from app.api.api_v1.endpoints import (
    login, users, utils, 
    organizations, studies, pipelines, 
    dashboards, configurations, metrics,
    activity_logs, platform_admin, public_api,
    exports, scheduled_reports
)

api_router = APIRouter()

# Original endpoints
api_router.include_router(login.router, tags=["login"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(utils.router, prefix="/utils", tags=["utils"])

# Clinical platform endpoints with RBAC
api_router.include_router(
    organizations.router, 
    prefix="/organizations", 
    tags=["organizations"]
)
api_router.include_router(
    studies.router, 
    prefix="/studies", 
    tags=["studies"]
)
api_router.include_router(
    pipelines.router, 
    prefix="/pipelines", 
    tags=["pipelines"]
)
api_router.include_router(
    dashboards.router, 
    prefix="/dashboards", 
    tags=["dashboards"]
)
api_router.include_router(
    configurations.router, 
    prefix="/configurations", 
    tags=["configurations"]
)
api_router.include_router(
    metrics.router, 
    prefix="/metrics", 
    tags=["metrics"]
)
api_router.include_router(
    activity_logs.router, 
    prefix="/activity-logs", 
    tags=["activity-logs"]
)
api_router.include_router(
    exports.router,
    prefix="/exports",
    tags=["exports"]
)
api_router.include_router(
    scheduled_reports.router,
    prefix="/scheduled-reports",
    tags=["scheduled-reports"]
)

# Platform admin endpoints (separate subdomain/path)
platform_router = APIRouter()
platform_router.include_router(
    platform_admin.router,
    prefix="/platform-admin",
    tags=["platform-admin"],
    dependencies=[Depends(require_platform_admin)]
)

# Public API for external integrations
public_router = APIRouter()
public_router.include_router(
    public_api.router,
    prefix="/api/v1",
    tags=["public-api"]
)

# backend/app/api/api_v1/endpoints/studies.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.models import Study, User
from app.schemas.study import StudyCreate, StudyUpdate, StudyResponse
from app.core.rbac_middleware import require_study_read, require_study_write, require_org_admin

router = APIRouter()

@router.get("/", response_model=List[StudyResponse])
async def list_studies(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_study_read),
    db: AsyncSession = Depends(get_session)
):
    """List studies user has access to"""
    # Filter based on user's permissions
    query = select(Study).join(UserRole).where(
        UserRole.user_id == current_user.id
    )
    
    studies = await db.exec(query.offset(skip).limit(limit))
    return studies.all()

@router.post("/", response_model=StudyResponse, status_code=status.HTTP_201_CREATED)
async def create_study(
    study_data: StudyCreate,
    current_user: User = Depends(require_org_admin),
    db: AsyncSession = Depends(get_session)
):
    """Create a new study (requires org admin)"""
    study = Study(
        **study_data.dict(),
        org_id=current_user.org_id,
        created_by=current_user.id
    )
    db.add(study)
    await db.commit()
    await db.refresh(study)
    
    # Assign creator as study manager
    user_role = UserRole(
        user_id=current_user.id,
        role_id=await get_role_id("study_manager"),
        study_id=study.id,
        assigned_by=current_user.id
    )
    db.add(user_role)
    await db.commit()
    
    return study

@router.put("/{study_id}", response_model=StudyResponse)
async def update_study(
    study_id: str,
    study_update: StudyUpdate,
    current_user: User = Depends(require_study_write),
    db: AsyncSession = Depends(get_session)
):
    """Update study configuration (requires study write permission)"""
    study = await db.get(Study, study_id)
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    for key, value in study_update.dict(exclude_unset=True).items():
        setattr(study, key, value)
    
    study.updated_at = datetime.utcnow()
    study.updated_by = current_user.id
    
    await db.commit()
    await db.refresh(study)
    
    return study
```

### Task 2.4: Platform Administration

```python
# backend/app/api/api_v1/endpoints/platform_admin.py
from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from datetime import datetime, timedelta
from app.models import Organization, User, Study, PipelineExecution
from app.core.rbac_middleware import require_platform_admin
from app.services.platform_service import PlatformService

router = APIRouter()

@router.get("/overview")
async def get_platform_overview(
    current_user: User = Depends(require_platform_admin),
    service: PlatformService = Depends()
):
    """Get platform-wide metrics and health status"""
    return await service.get_platform_metrics()

@router.get("/tenants", response_model=List[TenantDetails])
async def list_all_tenants(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    current_user: User = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_session)
):
    """List all organizations/tenants in the platform"""
    query = select(Organization)
    if status:
        query = query.where(Organization.is_active == (status == "active"))
    
    orgs = await db.exec(query.offset(skip).limit(limit))
    
    # Enrich with metrics
    results = []
    for org in orgs:
        study_count = await db.exec(
            select(func.count(Study.id)).where(Study.org_id == org.id)
        )
        user_count = await db.exec(
            select(func.count(User.id)).where(User.org_id == org.id)
        )
        
        results.append({
            "organization": org,
            "study_count": study_count.one(),
            "user_count": user_count.one(),
            "storage_used_gb": await service.get_org_storage(org.id),
            "last_activity": await service.get_last_activity(org.id)
        })
    
    return results

@router.post("/tenants")
async def create_tenant(
    tenant_data: TenantCreate,
    current_user: User = Depends(require_platform_admin),
    service: PlatformService = Depends()
):
    """Create a new tenant/organization"""
    return await service.create_tenant(tenant_data, current_user.id)

@router.put("/tenants/{tenant_id}/features")
async def update_tenant_features(
    tenant_id: str,
    features: Dict[str, bool],
    current_user: User = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_session)
):
    """Enable/disable features for specific tenant"""
    org = await db.get(Organization, tenant_id)
    if not org:
        raise HTTPException(404, "Tenant not found")
    
    # Update feature flags
    org.feature_flags = {
        **org.feature_flags,
        **features,
        "updated_at": datetime.utcnow().isoformat(),
        "updated_by": str(current_user.id)
    }
    
    await db.commit()
    return {"status": "success", "features": org.feature_flags}

@router.get("/metrics/system")
async def get_system_metrics(
    current_user: User = Depends(require_platform_admin),
    service: PlatformService = Depends()
):
    """Get real-time system metrics"""
    return {
        "cpu_usage": await service.get_cpu_usage(),
        "memory_usage": await service.get_memory_usage(),
        "disk_usage": await service.get_disk_usage(),
        "active_connections": await service.get_active_connections(),
        "queue_lengths": await service.get_queue_lengths(),
        "error_rates": await service.get_error_rates()
    }

@router.get("/audit/platform")
async def get_platform_audit_log(
    start_date: datetime = Query(default=datetime.utcnow() - timedelta(days=7)),
    end_date: datetime = Query(default=datetime.utcnow()),
    event_type: Optional[str] = None,
    current_user: User = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_session)
):
    """Get platform-wide audit logs"""
    query = select(AuditLog).where(
        AuditLog.timestamp.between(start_date, end_date)
    )
    
    if event_type:
        query = query.where(AuditLog.event_type == event_type)
    
    logs = await db.exec(query.order_by(AuditLog.timestamp.desc()).limit(1000))
    return logs.all()

# backend/app/services/platform_service.py
class PlatformService:
    """Service for platform-wide operations"""
    
    async def get_platform_metrics(self) -> Dict[str, Any]:
        """Get comprehensive platform metrics"""
        async with get_session() as db:
            metrics = {
                "tenants": {
                    "total": await self._count_total(db, Organization),
                    "active": await self._count_active(db, Organization),
                    "trial": await self._count_trial(db, Organization)
                },
                "studies": {
                    "total": await self._count_total(db, Study),
                    "active": await self._count_by_status(db, Study, "active"),
                    "completed": await self._count_by_status(db, Study, "completed")
                },
                "users": {
                    "total": await self._count_total(db, User),
                    "active_today": await self._count_active_users_today(db),
                    "new_this_month": await self._count_new_users_month(db)
                },
                "pipelines": {
                    "running": await self._count_running_pipelines(db),
                    "completed_today": await self._count_completed_pipelines_today(db),
                    "failed_today": await self._count_failed_pipelines_today(db)
                },
                "storage": {
                    "total_gb": await self._get_total_storage_gb(),
                    "by_tenant": await self._get_storage_by_tenant()
                },
                "api": {
                    "calls_today": await self._get_api_calls_today(),
                    "avg_response_time_ms": await self._get_avg_response_time()
                }
            }
            
            return metrics
    
    async def create_tenant(
        self, 
        tenant_data: TenantCreate, 
        created_by: str
    ) -> Organization:
        """Create a new tenant with all necessary setup"""
        async with get_session() as db:
            # Create organization
            org = Organization(
                name=tenant_data.name,
                code=tenant_data.code,
                config=tenant_data.config or {},
                feature_flags={
                    "max_studies": tenant_data.max_studies or 10,
                    "max_users": tenant_data.max_users or 50,
                    "api_access": tenant_data.api_access or False,
                    "advanced_analytics": tenant_data.advanced_analytics or False,
                    "custom_scripting": tenant_data.custom_scripting or False,
                    "export_enabled": True,
                    "scheduled_reports": tenant_data.scheduled_reports or False
                }
            )
            db.add(org)
            await db.commit()
            
            # Create default admin user
            admin_user = User(
                email=tenant_data.admin_email,
                full_name=tenant_data.admin_name,
                org_id=org.id,
                is_active=True
            )
            admin_user.hashed_password = get_password_hash(tenant_data.admin_password)
            db.add(admin_user)
            await db.commit()
            
            # Assign org admin role
            org_admin_role = await db.exec(
                select(Role).where(Role.name == "org_admin")
            )
            user_role = UserRole(
                user_id=admin_user.id,
                role_id=org_admin_role.first().id,
                assigned_by=created_by
            )
            db.add(user_role)
            await db.commit()
            
            # Create audit log
            await self.audit_service.log(
                "tenant_created",
                resource_type="organization",
                resource_id=str(org.id),
                user_id=created_by,
                details={"org_name": org.name}
            )
            
            return org
```

### Task 2.5: Activity Tracking System

```python
# backend/app/core/activity_tracker.py
from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import Request, BackgroundTasks
from app.models import ActivityLog
from app.core.db import get_session

class ActivityTracker:
    @staticmethod
    async def track(
        request: Request,
        background_tasks: BackgroundTasks,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Track user activity asynchronously"""
        background_tasks.add_task(
            ActivityTracker._save_activity,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            timestamp=datetime.utcnow()
        )
    
    @staticmethod
    async def _save_activity(**kwargs):
        """Save activity to database"""
        async with get_session() as session:
            activity = ActivityLog(**kwargs)
            session.add(activity)
            await session.commit()
```

### Deliverables - Phase 2
- [ ] Multi-tenant middleware
- [ ] Core API structure
- [ ] Activity tracking system
- [ ] Authentication enhancements

## Phase 3: Data Pipeline System (Week 5-6)

> **Priority Integrations**: Medidata Rave API and ZIP file uploads are the primary data sources

### Task 3.1: Data Source Configuration

```python
# backend/app/clinical_modules/data_pipeline/data_sources.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List
import aiohttp
import asyncssh
import pandas as pd
import zipfile
import os
from pathlib import Path

class BaseDataSource(ABC):
    """Base class for all data sources"""
    
    @abstractmethod
    async def connect(self) -> bool:
        """Test connection to data source"""
        pass
    
    @abstractmethod
    async def fetch_data(self, config: Dict[str, Any]) -> pd.DataFrame:
        """Fetch data from source"""
        pass

class MedidataAPISource(BaseDataSource):
    """Medidata Rave API data source - PRIMARY INTEGRATION"""
    
    def __init__(self, config: Dict[str, Any]):
        self.base_url = config['api_url']
        self.api_key = config['api_key']
        self.study_oid = config['study_oid']
        
    async def connect(self) -> bool:
        async with aiohttp.ClientSession() as session:
            headers = {'Authorization': f'Bearer {self.api_key}'}
            async with session.get(f"{self.base_url}/studies", headers=headers) as resp:
                return resp.status == 200
    
    async def fetch_data(self, config: Dict[str, Any]) -> pd.DataFrame:
        dataset_name = config['dataset']
        
        async with aiohttp.ClientSession() as session:
            headers = {'Authorization': f'Bearer {self.api_key}'}
            url = f"{self.base_url}/studies/{self.study_oid}/datasets/{dataset_name}"
            
            async with session.get(url, headers=headers) as resp:
                data = await resp.json()
                return pd.DataFrame(data['items'])

class SFTPDataSource(BaseDataSource):
    """SFTP data source"""
    
    def __init__(self, config: Dict[str, Any]):
        self.host = config['host']
        self.port = config.get('port', 22)
        self.username = config['username']
        self.password = config.get('password')
        self.key_path = config.get('key_path')
        
    async def connect(self) -> bool:
        try:
            async with asyncssh.connect(
                self.host, 
                port=self.port,
                username=self.username,
                password=self.password,
                client_keys=[self.key_path] if self.key_path else None
            ) as conn:
                return True
        except:
            return False
    
    async def fetch_data(self, config: Dict[str, Any]) -> pd.DataFrame:
        remote_path = config['remote_path']
        
        async with asyncssh.connect(
            self.host, 
            port=self.port,
            username=self.username,
            password=self.password
        ) as conn:
            async with conn.start_sftp_client() as sftp:
                # Download file to temp location
                local_path = f"/tmp/{remote_path.split('/')[-1]}"
                await sftp.get(remote_path, local_path)
                
                # Read based on file type
                if local_path.endswith('.sas7bdat'):
                    import pyreadstat
                    df, meta = pyreadstat.read_sas7bdat(local_path)
                    return df
                elif local_path.endswith('.csv'):
                    return pd.read_csv(local_path)
                else:
                    raise ValueError(f"Unsupported file type: {local_path}")

class ZipFileUploadSource(BaseDataSource):
    """ZIP file upload data source - PRIMARY INTEGRATION"""
    
    def __init__(self, config: Dict[str, Any]):
        self.study_id = config['study_id']
        self.org_id = config['org_id']
        self.upload_path = config['upload_path']  # Path to uploaded ZIP file
        
    async def connect(self) -> bool:
        """Verify ZIP file exists and is valid"""
        return Path(self.upload_path).exists() and zipfile.is_zipfile(self.upload_path)
    
    async def fetch_data(self, config: Dict[str, Any]) -> pd.DataFrame:
        """Extract and process data from ZIP file"""
        dataset_name = config.get('dataset')
        
        # Extract ZIP to temporary location
        extract_path = f"/data/studies/{self.org_id}/{self.study_id}/temp/zip_extract"
        os.makedirs(extract_path, exist_ok=True)
        
        with zipfile.ZipFile(self.upload_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        
        # Find and load the requested dataset
        data_files = []
        for root, dirs, files in os.walk(extract_path):
            for file in files:
                if dataset_name and dataset_name in file:
                    data_files.append(os.path.join(root, file))
                elif not dataset_name:
                    # If no specific dataset, get all data files
                    if file.endswith(('.sas7bdat', '.csv', '.xlsx', '.parquet')):
                        data_files.append(os.path.join(root, file))
        
        if not data_files:
            raise FileNotFoundError(f"No data files found in ZIP")
        
        # Load the first matching file (extend for multiple files if needed)
        file_path = data_files[0]
        
        if file_path.endswith('.sas7bdat'):
            import pyreadstat
            df, meta = pyreadstat.read_sas7bdat(file_path)
            return df
        elif file_path.endswith('.csv'):
            return pd.read_csv(file_path)
        elif file_path.endswith('.xlsx'):
            return pd.read_excel(file_path)
        elif file_path.endswith('.parquet'):
            return pd.read_parquet(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_path}")
```

### Task 3.2: Secure Pipeline Executor

> **CRITICAL SECURITY UPDATE**: The pipeline executor provides maximum flexibility while maintaining security:
> - **Layer 1**: Domain-Specific Language (DSL) for standard transformations
> - **Layer 2**: Docker containerization for complex Python scripts with extensive library support
> - **Flexibility**: Support for custom Python libraries, Git integration for version control, and full Python execution capabilities in isolated containers

#### Layer 1: DSL-Based Pipeline Executor

```python
# backend/app/clinical_modules/data_pipeline/dsl_executor.py
from typing import Dict, Any, List, Optional
import pandas as pd
from pydantic import BaseModel, validator
import json
from pathlib import Path
from datetime import datetime

class TransformationStep(BaseModel):
    """Single transformation step in the pipeline"""
    operation: str
    parameters: Dict[str, Any]
    
    @validator('operation')
    def validate_operation(cls, v):
        allowed_ops = {
            'select_columns', 'drop_columns', 'rename_columns',
            'filter_rows', 'drop_duplicates', 'fill_missing',
            'convert_types', 'add_calculated_column', 'pivot',
            'merge_datasets', 'aggregate', 'sort_by', 'save_dataset'
        }
        if v not in allowed_ops:
            raise ValueError(f"Operation '{v}' not allowed")
        return v

class PipelineDefinition(BaseModel):
    """Complete pipeline definition in safe DSL format"""
    version: str = "1.0"
    name: str
    description: Optional[str]
    inputs: List[str]  # Required input datasets
    outputs: List[str]  # Output datasets to create
    steps: List[TransformationStep]

class DSLPipelineExecutor:
    """Execute pipelines defined in safe DSL format"""
    
    def __init__(self):
        self.operations = {
            'select_columns': self._select_columns,
            'drop_columns': self._drop_columns,
            'rename_columns': self._rename_columns,
            'filter_rows': self._filter_rows,
            'drop_duplicates': self._drop_duplicates,
            'fill_missing': self._fill_missing,
            'convert_types': self._convert_types,
            'add_calculated_column': self._add_calculated_column,
            'aggregate': self._aggregate,
            'pivot': self._pivot,
            'merge_datasets': self._merge_datasets,
            'sort_by': self._sort_by,
            'save_dataset': self._save_dataset
        }
    
    async def execute(self, 
                     pipeline_json: str, 
                     study_id: str, 
                     run_date: str) -> Dict[str, Any]:
        """Execute a DSL pipeline definition"""
        
        # Parse and validate pipeline
        try:
            pipeline = PipelineDefinition.parse_raw(pipeline_json)
        except Exception as e:
            raise ValueError(f"Invalid pipeline definition: {e}")
        
        # Load input datasets
        datasets = {}
        base_path = Path(f"/data/studies/{study_id}")
        
        for input_name in pipeline.inputs:
            # Try multiple locations and formats
            file_found = False
            for subdir in ['source_data', 'analysis_data']:
                for ext in ['.sas7bdat', '.parquet', '.csv']:
                    file_path = base_path / subdir / run_date / f"{input_name}{ext}"
                    if file_path.exists():
                        datasets[input_name] = await self._load_dataset(file_path)
                        file_found = True
                        break
                if file_found:
                    break
            
            if not file_found:
                raise FileNotFoundError(f"Input dataset '{input_name}' not found")
        
        # Execute transformation steps
        execution_log = []
        for idx, step in enumerate(pipeline.steps):
            try:
                operation = self.operations.get(step.operation)
                if not operation:
                    raise ValueError(f"Unknown operation: {step.operation}")
                
                # Execute operation
                datasets = await operation(datasets, **step.parameters)
                
                execution_log.append({
                    "step": idx + 1,
                    "operation": step.operation,
                    "status": "success"
                })
                
            except Exception as e:
                execution_log.append({
                    "step": idx + 1,
                    "operation": step.operation,
                    "status": "error",
                    "error": str(e)
                })
                raise
        
        # Save outputs
        output_path = base_path / "analysis_data" / run_date
        output_path.mkdir(parents=True, exist_ok=True)
        
        results = {}
        for output_name in pipeline.outputs:
            if output_name in datasets:
                output_file = output_path / f"{output_name}.parquet"
                datasets[output_name].to_parquet(output_file, index=False)
                
                results[output_name] = {
                    "rows": len(datasets[output_name]),
                    "columns": list(datasets[output_name].columns),
                    "path": str(output_file)
                }
        
        return {
            "pipeline": pipeline.name,
            "execution_time": datetime.utcnow().isoformat(),
            "outputs": results,
            "execution_log": execution_log
        }
    
    async def _load_dataset(self, file_path: Path) -> pd.DataFrame:
        """Load dataset from various formats"""
        if file_path.suffix == '.sas7bdat':
            import pyreadstat
            df, meta = pyreadstat.read_sas7bdat(str(file_path))
            return df
        elif file_path.suffix == '.parquet':
            return pd.read_parquet(file_path)
        elif file_path.suffix == '.csv':
            return pd.read_csv(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")
    
    async def _select_columns(self, datasets: Dict, 
                             dataset: str, 
                             columns: List[str], 
                             output_name: Optional[str] = None,
                             **kwargs) -> Dict:
        """Select specific columns from dataset"""
        df = datasets[dataset]
        result = df[columns].copy()
        datasets[output_name or dataset] = result
        return datasets
    
    async def _filter_rows(self, datasets: Dict,
                          dataset: str,
                          conditions: List[Dict],
                          output_name: Optional[str] = None,
                          **kwargs) -> Dict:
        """Filter rows based on conditions"""
        df = datasets[dataset].copy()
        
        for condition in conditions:
            column = condition['column']
            operator = condition['operator']
            value = condition['value']
            
            if operator == 'equals':
                df = df[df[column] == value]
            elif operator == 'not_equals':
                df = df[df[column] != value]
            elif operator == 'greater_than':
                df = df[df[column] > value]
            elif operator == 'less_than':
                df = df[df[column] < value]
            elif operator == 'in':
                df = df[df[column].isin(value)]
            elif operator == 'not_in':
                df = df[~df[column].isin(value)]
            elif operator == 'contains':
                df = df[df[column].str.contains(value, na=False)]
            elif operator == 'is_null':
                df = df[df[column].isna()]
            elif operator == 'is_not_null':
                df = df[df[column].notna()]
            else:
                raise ValueError(f"Unknown operator: {operator}")
        
        datasets[output_name or dataset] = df
        return datasets
    
    async def _add_calculated_column(self, datasets: Dict,
                                   dataset: str,
                                   column_name: str,
                                   expression: str,
                                   **kwargs) -> Dict:
        """Add calculated column using safe expressions"""
        df = datasets[dataset]
        
        # Only allow specific safe calculations
        allowed_calcs = {
            'age_years': lambda df: (pd.Timestamp.now() - pd.to_datetime(df['BIRTHDT'])).dt.days / 365.25,
            'bmi': lambda df: df['WEIGHT'] / (df['HEIGHT'] / 100) ** 2,
            'visit_day': lambda df: (pd.to_datetime(df['VISITDT']) - pd.to_datetime(df['RFSTDTC'])).dt.days,
            'treatment_duration': lambda df: (pd.to_datetime(df['RFENDTC']) - pd.to_datetime(df['RFSTDTC'])).dt.days
        }
        
        if expression in allowed_calcs:
            df[column_name] = allowed_calcs[expression](df)
        else:
            raise ValueError(f"Calculation '{expression}' not allowed")
        
        datasets[dataset] = df
        return datasets

# Example DSL pipeline configuration
EXAMPLE_LAYER1_PIPELINE = {
    "version": "1.0",
    "name": "Demographics Data Preparation",
    "description": "Clean and standardize demographics data from EDC",
    "inputs": ["DM", "ENROL"],
    "outputs": ["dm_clean", "enrollment_summary"],
    "steps": [
        {
            "operation": "drop_columns",
            "parameters": {
                "dataset": "DM",
                "columns": ["DOMAIN", "STUDYID", "USUBJID_"]
            }
        },
        {
            "operation": "filter_rows",
            "parameters": {
                "dataset": "DM",
                "conditions": [
                    {
                        "column": "DMDTC",
                        "operator": "is_not_null"
                    },
                    {
                        "column": "ARMCD",
                        "operator": "not_equals",
                        "value": "SCRNFAIL"
                    }
                ]
            }
        },
        {
            "operation": "convert_types",
            "parameters": {
                "dataset": "DM",
                "conversions": {
                    "AGE": "numeric",
                    "DMDTC": "datetime"
                }
            }
        },
        {
            "operation": "add_calculated_column",
            "parameters": {
                "dataset": "DM",
                "column_name": "AGE_GROUP",
                "expression": "age_group_standard"
            }
        },
        {
            "operation": "merge_datasets",
            "parameters": {
                "left": "DM",
                "right": "ENROL",
                "on": "USUBJID",
                "how": "left",
                "output_name": "dm_enriched"
            }
        },
        {
            "operation": "save_dataset",
            "parameters": {
                "dataset": "dm_enriched",
                "output_name": "dm_clean"
            }
        }
    ]
}
```

#### Layer 2: Containerized Python Executor

```python
# backend/app/clinical_modules/data_pipeline/container_executor.py
import docker
import tempfile
import shutil
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
import uuid
import logging

logger = logging.getLogger(__name__)

class ContainerizedPipelineExecutor:
    """Execute pipeline scripts in isolated Docker containers"""
    
    def __init__(self):
        self.docker_client = docker.from_env()
        self.base_image = "python:3.11-slim"
        self.execution_timeout = 300  # 5 minutes
        
        # Resource limits for container
        self.container_limits = {
            'mem_limit': '2g',          # 2GB RAM limit
            'memswap_limit': '2g',      # No swap
            'cpu_period': 100000,
            'cpu_quota': 80000,         # 80% of one CPU
            'pids_limit': 100,          # Process limit
            'read_only': False,         # Need to write to output
            'network_disabled': True    # No network access
        }
    
    async def execute_script(self,
                           script_code: str,
                           study_id: str,
                           run_date: str,
                           script_name: str = 'analysis_script') -> Dict[str, Any]:
        """Execute a Python script in an isolated container"""
        
        execution_id = str(uuid.uuid4())
        logger.info(f"Starting containerized execution {execution_id} for {study_id}")
        
        # Create temporary directories
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            input_dir = temp_path / "input"
            output_dir = temp_path / "output"
            script_dir = temp_path / "script"
            
            input_dir.mkdir()
            output_dir.mkdir()
            script_dir.mkdir()
            
            try:
                # Copy input data (will be mounted as read-only)
                await self._prepare_input_data(study_id, run_date, input_dir)
                
                # Prepare script and environment
                await self._prepare_script_environment(
                    script_code, script_name, script_dir, 
                    study_id, run_date, execution_id
                )
                
                # Build custom image with dependencies
                image_tag = f"pipeline-executor:{execution_id}"
                await self._build_executor_image(script_dir, image_tag)
                
                # Run container with security restrictions
                result = await self._run_container(
                    image_tag, input_dir, output_dir, execution_id
                )
                
                # Process results
                if result['exit_code'] == 0:
                    # Copy outputs back to study directory
                    await self._save_outputs(study_id, run_date, output_dir)
                    
                    result['output_files'] = [
                        f.name for f in output_dir.iterdir() if f.is_file()
                    ]
                
                return result
                
            except Exception as e:
                logger.error(f"Container execution failed: {str(e)}")
                return {
                    "status": "error",
                    "execution_id": execution_id,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            
            finally:
                # Cleanup
                try:
                    # Remove container if it exists
                    containers = self.docker_client.containers.list(
                        all=True, 
                        filters={'label': f'execution_id={execution_id}'}
                    )
                    for container in containers:
                        container.remove(force=True)
                    
                    # Remove custom image
                    try:
                        self.docker_client.images.remove(image_tag, force=True)
                    except:
                        pass
                        
                except Exception as cleanup_error:
                    logger.warning(f"Cleanup error: {cleanup_error}")
    
    async def _prepare_input_data(self, study_id: str, run_date: str, input_dir: Path):
        """Copy input data to temporary directory"""
        source_paths = [
            Path(f"/data/studies/{study_id}/source_data/{run_date}"),
            Path(f"/data/studies/{study_id}/analysis_data/{run_date}")
        ]
        
        for source_path in source_paths:
            if source_path.exists():
                for file in source_path.iterdir():
                    if file.is_file() and file.suffix in ['.parquet', '.csv', '.sas7bdat']:
                        shutil.copy2(file, input_dir / file.name)
    
    async def _prepare_script_environment(self, script_code: str, script_name: str,
                                        script_dir: Path, study_id: str, 
                                        run_date: str, execution_id: str):
        """Prepare script and metadata for execution"""
        
        # Write the main script
        script_path = script_dir / "pipeline_script.py"
        wrapped_script = self._wrap_script(script_code)
        script_path.write_text(wrapped_script)
        
        # Write requirements
        requirements_path = script_dir / "requirements.txt"
        requirements_path.write_text(self._get_safe_requirements())
        
        # Write metadata
        metadata = {
            "study_id": study_id,
            "run_date": run_date,
            "execution_id": execution_id,
            "script_name": script_name,
            "input_path": "/data/input",
            "output_path": "/data/output"
        }
        
        (script_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))
    
    def _wrap_script(self, user_code: str) -> str:
        """Wrap user code with safety measures and standard imports"""
        return f"""#!/usr/bin/env python3
# Pipeline Execution Environment
import sys
import json
import warnings
warnings.filterwarnings('ignore')

# Standard imports allowed in clinical data processing
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from pathlib import Path
import pyreadstat

# Load execution metadata
with open('/app/metadata.json', 'r') as f:
    metadata = json.load(f)

# Set up paths
input_path = Path(metadata['input_path'])
output_path = Path(metadata['output_path'])
study_id = metadata['study_id']
run_date = metadata['run_date']

# Restrict dangerous operations
import builtins
restricted_builtins = {{
    k: v for k, v in builtins.__dict__.items()
    if k not in ['exec', 'eval', 'compile', '__import__', 'open']
}}

# Safe file operations
def safe_read_parquet(filename):
    '''Safely read parquet file from input directory'''
    return pd.read_parquet(input_path / filename)

def safe_read_csv(filename, **kwargs):
    '''Safely read CSV file from input directory'''
    return pd.read_csv(input_path / filename, **kwargs)

def safe_read_sas(filename):
    '''Safely read SAS file from input directory'''
    df, meta = pyreadstat.read_sas7bdat(str(input_path / filename))
    return df

def safe_save_parquet(df, filename):
    '''Safely save DataFrame to parquet in output directory'''
    df.to_parquet(output_path / filename, index=False)
    print(f"Saved {{len(df)}} rows to {{filename}}")

# Make safe functions available
read_parquet = safe_read_parquet
read_csv = safe_read_csv
read_sas = safe_read_sas
save_parquet = safe_save_parquet
to_parquet = safe_save_parquet

print(f"Starting pipeline execution for study {{study_id}}, date {{run_date}}")
print(f"Available input files: {{list(input_path.glob('*'))}}")

# Execute user code
try:
    {user_code}
    print("\\nPipeline execution completed successfully")
except Exception as e:
    import traceback
    print(f"\\nERROR in pipeline execution: {{e}}", file=sys.stderr)
    print(traceback.format_exc(), file=sys.stderr)
    sys.exit(1)

# List output files
output_files = list(output_path.glob('*'))
print(f"\\nGenerated output files: {{output_files}}")
"""
    
    def _get_safe_requirements(self) -> str:
        """Get safe Python requirements for clinical data processing"""
        return """# Clinical data processing requirements
pandas==2.0.3
numpy==1.24.3
pyarrow==12.0.1
pyreadstat==1.2.2
scipy==1.10.1
statsmodels==0.14.0
scikit-learn==1.3.0
matplotlib==3.7.2
seaborn==0.12.2
openpyxl==3.1.2
"""
    
    async def _build_executor_image(self, script_dir: Path, image_tag: str):
        """Build a custom Docker image for the executor"""
        dockerfile_content = f"""FROM {self.base_image}

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \\
    gcc \\
    g++ \\
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r pipeline && useradd -r -g pipeline -u 1000 pipeline

# Set up working directory
WORKDIR /app

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \\
    rm -rf /root/.cache/pip

# Copy scripts
COPY pipeline_script.py metadata.json ./
RUN chmod 444 pipeline_script.py metadata.json

# Create data directories
RUN mkdir -p /data/input /data/output && \\
    chown -R pipeline:pipeline /data/output

# Switch to non-root user
USER pipeline

# Set Python to unbuffered mode
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Default command
CMD ["python", "pipeline_script.py"]
"""
        
        dockerfile_path = script_dir / "Dockerfile"
        dockerfile_path.write_text(dockerfile_content)
        
        # Build image
        logger.info(f"Building Docker image {image_tag}")
        self.docker_client.images.build(
            path=str(script_dir),
            tag=image_tag,
            rm=True,
            forcerm=True
        )
    
    async def _run_container(self, image_tag: str, input_dir: Path, 
                           output_dir: Path, execution_id: str) -> Dict[str, Any]:
        """Run the container with security restrictions"""
        
        logger.info(f"Starting container for execution {execution_id}")
        
        # Run container
        container = self.docker_client.containers.run(
            image=image_tag,
            command=["python", "/app/pipeline_script.py"],
            volumes={
                str(input_dir): {'bind': '/data/input', 'mode': 'ro'},
                str(output_dir): {'bind': '/data/output', 'mode': 'rw'},
            },
            working_dir="/app",
            user="pipeline",
            labels={'execution_id': execution_id},
            remove=False,
            detach=True,
            **self.container_limits
        )
        
        # Wait for completion with timeout
        try:
            exit_result = container.wait(timeout=self.execution_timeout)
            exit_code = exit_result['StatusCode']
            
            # Get logs
            logs = container.logs(stdout=True, stderr=True).decode('utf-8')
            
            # Remove container
            container.remove()
            
            return {
                "status": "success" if exit_code == 0 else "error",
                "execution_id": execution_id,
                "exit_code": exit_code,
                "logs": logs[-5000:],  # Last 5000 chars
                "container_id": container.short_id
            }
            
        except Exception as e:
            # Force remove container
            try:
                container.remove(force=True)
            except:
                pass
                
            raise RuntimeError(f"Container execution failed: {str(e)}")
    
    async def _save_outputs(self, study_id: str, run_date: str, output_dir: Path):
        """Copy output files back to study directory"""
        output_path = Path(f"/data/studies/{study_id}/analysis_data/{run_date}")
        output_path.mkdir(parents=True, exist_ok=True)
        
        for file in output_dir.iterdir():
            if file.is_file():
                shutil.copy2(file, output_path / file.name)
                logger.info(f"Saved output file: {file.name}")

# backend/app/clinical_modules/data_pipeline/executor.py
class PipelineExecutor:
    """Main pipeline executor that chooses appropriate execution method"""
    
    def __init__(self, study_id: str):
        self.study_id = study_id
        self.dsl_executor = DSLPipelineExecutor()
        self.container_executor = ContainerizedPipelineExecutor()
        
    async def execute_layer1(self, pipeline_config: Dict[str, Any], run_date: str) -> Dict[str, Any]:
        """Execute Layer 1 pipeline (data acquisition/transformation)"""
        
        if pipeline_config.get('type') == 'dsl':
            # Use DSL executor for standard transformations
            return await self.dsl_executor.execute(
                pipeline_config['definition'],
                self.study_id,
                run_date
            )
        else:
            # Use container executor for custom Python scripts
            return await self.container_executor.execute_script(
                pipeline_config['script'],
                self.study_id,
                run_date,
                script_name='layer1_acquisition'
            )
    
    async def execute_layer2(self, script_name: str, run_date: str) -> Dict[str, Any]:
        """Execute Layer 2 analysis script in container"""
        
        script_path = Path(f"/data/studies/{self.study_id}/analysis/{script_name}")
        
        if not script_path.exists():
            raise FileNotFoundError(f"Analysis script not found: {script_name}")
        
        script_code = script_path.read_text()
        
        return await self.container_executor.execute_script(
            script_code,
            self.study_id,
            run_date,
            script_name=script_name
        )
```

### Task 3.3: Asynchronous Pipeline Execution

```python
# backend/app/models/pipeline_execution.py
from sqlmodel import SQLModel, Field, Column, JSON
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

class PipelineExecution(SQLModel, table=True):
    """Track pipeline execution status"""
    __tablename__ = "pipeline_executions"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    study_id: uuid.UUID = Field(foreign_key="studies.id", index=True)
    user_id: uuid.UUID = Field(foreign_key="users.id")
    
    # Execution tracking
    celery_task_id: Optional[str] = Field(index=True)
    status: str = Field(default="QUEUED", index=True)  # QUEUED, IN_PROGRESS, COMPLETED, FAILED
    progress_data: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    result_data: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    error_message: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Relationships
    study: "Study" = Relationship(back_populates="executions")
    user: "User" = Relationship()

# backend/app/api/api_v1/endpoints/pipelines.py
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from app.models import PipelineExecution, Study, User
from app.workers.pipeline_tasks import execute_data_pipeline
from app.core.rbac_middleware import require_pipeline_execute
from app.schemas.pipeline import PipelineExecutionResponse, TaskStatusResponse
from celery.result import AsyncResult

router = APIRouter()

@router.post(
    "/studies/{study_id}/pipeline/execute",
    response_model=PipelineExecutionResponse,
    status_code=status.HTTP_202_ACCEPTED
)
async def trigger_pipeline_execution(
    study_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_pipeline_execute),
    db: AsyncSession = Depends(get_session)
):
    """
    Trigger pipeline execution asynchronously
    Returns immediately with task ID for status polling
    """
    # Quick validation (target: < 50ms)
    study = await db.get(Study, study_id)
    if not study:
        raise HTTPException(404, "Study not found")
    
    # Check if pipeline is already running
    running_execution = await db.exec(
        select(PipelineExecution)
        .where(PipelineExecution.study_id == study_id)
        .where(PipelineExecution.status.in_(["QUEUED", "IN_PROGRESS"]))
    )
    if running_execution.first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Pipeline is already running for this study"
        )
    
    # Create execution record
    execution = PipelineExecution(
        study_id=study_id,
        user_id=current_user.id,
        status="QUEUED",
        progress_data={"stage": "queued", "progress": 0}
    )
    db.add(execution)
    await db.commit()
    await db.refresh(execution)
    
    # Queue the task
    task = execute_data_pipeline.apply_async(
        args=[str(execution.id), study_id],
        queue='pipeline_queue',
        priority=5  # Medium priority
    )
    
    # Update with Celery task ID
    execution.celery_task_id = task.id
    await db.commit()
    
    # Track activity (non-blocking)
    background_tasks.add_task(
        ActivityTracker.track,
        request=request,
        user_id=str(current_user.id),
        action="pipeline_execute",
        resource_type="study",
        resource_id=study_id
    )
    
    # Return immediately
    return PipelineExecutionResponse(
        execution_id=str(execution.id),
        task_id=task.id,
        status="QUEUED",
        message="Pipeline execution queued successfully",
        status_url=f"/api/v1/tasks/{task.id}"
    )

@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """Get real-time task status for polling"""
    # Get execution record
    execution = await db.exec(
        select(PipelineExecution)
        .where(PipelineExecution.celery_task_id == task_id)
    )
    execution = execution.first()
    
    if not execution:
        raise HTTPException(404, "Task not found")
    
    # Check user has access to this execution
    if execution.user_id != current_user.id and not current_user.is_superuser:
        # Check if user has access to the study
        if not await user_has_study_access(current_user, execution.study_id):
            raise HTTPException(403, "Access denied")
    
    # Get Celery task status
    celery_task = AsyncResult(task_id)
    
    # Build response
    response = TaskStatusResponse(
        task_id=task_id,
        execution_id=str(execution.id),
        status=execution.status,
        progress=execution.progress_data,
        created_at=execution.created_at,
        started_at=execution.started_at,
        completed_at=execution.completed_at,
        celery_state=celery_task.state,
        celery_info=celery_task.info if celery_task.state != "PENDING" else None
    )
    
    # Include result or error based on status
    if execution.status == "COMPLETED":
        response.result = execution.result_data
    elif execution.status == "FAILED":
        response.error = execution.error_message
    
    return response

@router.delete("/tasks/{task_id}")
async def cancel_task(
    task_id: str,
    current_user: User = Depends(require_pipeline_execute),
    db: AsyncSession = Depends(get_session)
):
    """Cancel a running pipeline task"""
    execution = await db.exec(
        select(PipelineExecution)
        .where(PipelineExecution.celery_task_id == task_id)
    )
    execution = execution.first()
    
    if not execution:
        raise HTTPException(404, "Task not found")
    
    # Only allow cancellation of queued or running tasks
    if execution.status not in ["QUEUED", "IN_PROGRESS"]:
        raise HTTPException(400, f"Cannot cancel task with status: {execution.status}")
    
    # Revoke Celery task
    AsyncResult(task_id).revoke(terminate=True)
    
    # Update execution status
    execution.status = "CANCELLED"
    execution.completed_at = datetime.utcnow()
    execution.error_message = "Cancelled by user"
    
    await db.commit()
    
    return {"status": "cancelled", "task_id": task_id}

# backend/app/workers/pipeline_tasks.py
from celery import Celery, Task, states
from celery.result import AsyncResult
from typing import Dict, Any
import logging
import traceback
from datetime import datetime

from app.core.config import settings
from app.clinical_modules.data_pipeline import PipelineExecutor
from app.models import Study, PipelineExecution

logger = logging.getLogger(__name__)

celery_app = Celery("clinical_dashboard")
celery_app.config_from_object(settings.celery_config)

class CallbackTask(Task):
    """Task that updates execution record on state changes"""
    
    def on_success(self, retval, task_id, args, kwargs):
        """Called on successful completion"""
        execution_id = args[0]
        self.update_execution_status(execution_id, "COMPLETED", result_data=retval)
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called on task failure"""
        execution_id = args[0]
        self.update_execution_status(
            execution_id, 
            "FAILED", 
            error_message=f"{type(exc).__name__}: {str(exc)}\n{traceback.format_exc()}"
        )
    
    def update_execution_status(self, execution_id: str, status: str, **kwargs):
        """Update execution record in database"""
        from app.core.db import SessionLocal
        
        with SessionLocal() as db:
            execution = db.query(PipelineExecution).filter(
                PipelineExecution.id == execution_id
            ).first()
            
            if execution:
                execution.status = status
                execution.completed_at = datetime.utcnow() if status in ["COMPLETED", "FAILED"] else None
                
                for key, value in kwargs.items():
                    setattr(execution, key, value)
                
                db.commit()

@celery_app.task(
    bind=True,
    base=CallbackTask,
    name='execute_data_pipeline',
    max_retries=3,
    default_retry_delay=60
)
def execute_data_pipeline(self, execution_id: str, study_id: str) -> Dict[str, Any]:
    """
    Execute complete data pipeline for a study
    This runs in a separate worker process
    """
    from app.core.db import SessionLocal
    
    logger.info(f"Starting pipeline execution {execution_id} for study {study_id}")
    
    try:
        # Update status to IN_PROGRESS
        with SessionLocal() as db:
            execution = db.query(PipelineExecution).filter(
                PipelineExecution.id == execution_id
            ).first()
            
            if not execution:
                raise ValueError(f"Execution {execution_id} not found")
            
            execution.status = "IN_PROGRESS"
            execution.started_at = datetime.utcnow()
            execution.progress_data = {"stage": "initializing", "progress": 0}
            db.commit()
            
            # Get study configuration
            study = db.query(Study).filter(Study.id == study_id).first()
            if not study:
                raise ValueError(f"Study {study_id} not found")
        
        # Update progress
        self.update_state(
            state=states.STARTED,
            meta={'stage': 'layer1', 'progress': 10, 'message': 'Starting Layer 1 processing'}
        )
        
        # Execute Layer 1
        executor = PipelineExecutor(study_id)
        run_date = datetime.utcnow().strftime("%d%b%Y").upper()
        
        layer1_result = executor.execute_layer1(
            study.pipeline_config.get('layer1_script', ''),
            run_date
        )
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'stage': 'layer1', 'progress': 50, 'message': 'Layer 1 complete, starting Layer 2'}
        )
        
        # Update execution record
        with SessionLocal() as db:
            execution = db.query(PipelineExecution).filter(
                PipelineExecution.id == execution_id
            ).first()
            execution.progress_data = {
                "stage": "layer2",
                "progress": 50,
                "layer1_result": layer1_result
            }
            db.commit()
        
        # Execute Layer 2 scripts
        layer2_results = []
        layer2_scripts = study.pipeline_config.get('layer2_scripts', [])
        
        for idx, script_name in enumerate(layer2_scripts):
            progress = 50 + (40 * (idx + 1) / len(layer2_scripts))
            
            self.update_state(
                state='PROGRESS',
                meta={
                    'stage': 'layer2',
                    'progress': progress,
                    'message': f'Processing {script_name}'
                }
            )
            
            result = executor.execute_layer2(script_name, run_date)
            layer2_results.append(result)
        
        # Final update
        self.update_state(
            state='PROGRESS',
            meta={'stage': 'finalizing', 'progress': 95, 'message': 'Finalizing pipeline execution'}
        )
        
        # Prepare final result
        final_result = {
            'status': 'success',
            'execution_id': execution_id,
            'study_id': study_id,
            'run_date': run_date,
            'layer1_result': layer1_result,
            'layer2_results': layer2_results,
            'summary': {
                'files_processed': len(layer1_result.get('files_created', [])),
                'analysis_datasets': len(layer2_results),
                'execution_time_seconds': (datetime.utcnow() - execution.started_at).total_seconds()
            }
        }
        
        # Update execution record with results
        with SessionLocal() as db:
            execution = db.query(PipelineExecution).filter(
                PipelineExecution.id == execution_id
            ).first()
            execution.result_data = final_result
            execution.progress_data = {"stage": "completed", "progress": 100}
            db.commit()
        
        logger.info(f"Pipeline execution {execution_id} completed successfully")
        return final_result
        
    except Exception as e:
        logger.error(f"Pipeline execution {execution_id} failed: {str(e)}")
        
        # Update execution record with error
        with SessionLocal() as db:
            execution = db.query(PipelineExecution).filter(
                PipelineExecution.id == execution_id
            ).first()
            if execution:
                execution.progress_data = {
                    "stage": "failed",
                    "progress": execution.progress_data.get("progress", 0),
                    "error": str(e)
                }
                db.commit()
        
        # Retry on certain errors
        if self.request.retries < self.max_retries:
            if isinstance(e, (ConnectionError, TimeoutError)):
                logger.info(f"Retrying pipeline execution {execution_id} (attempt {self.request.retries + 1})")
                raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))
        
        raise
```

### Deliverables - Phase 3
- [ ] Data source integrations
- [ ] Pipeline executor
- [ ] Celery task queue
- [ ] Pipeline monitoring API

## Phase 4: Export & Reporting System (Week 7-8)

### Task 4.1: Export Engine

```python
# backend/app/models/scheduled_report.py
from sqlmodel import SQLModel, Field, Column, JSON, ARRAY
from typing import List, Optional, Dict, Any
from datetime import datetime, time
import uuid
from sqlalchemy import String, Integer, Time

class ScheduledReport(SQLModel, table=True):
    """Scheduled report configuration"""
    __tablename__ = "scheduled_reports"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(index=True)
    description: Optional[str] = None
    study_id: uuid.UUID = Field(foreign_key="studies.id", index=True)
    dashboard_id: uuid.UUID = Field(foreign_key="dashboards.id")
    created_by: uuid.UUID = Field(foreign_key="users.id")
    
    # Schedule configuration
    schedule_type: str = Field(index=True)  # "daily", "weekly", "monthly", "custom"
    schedule_time: time = Field(sa_column=Column(Time))  # Time of day to send
    schedule_days: Optional[List[int]] = Field(sa_column=Column(ARRAY(Integer)))  # Days of week/month
    schedule_cron: Optional[str] = None  # For custom schedules
    timezone: str = Field(default="UTC")
    
    # Export configuration
    export_format: str = Field(default="pdf")  # "pdf", "pptx", "excel"
    export_options: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    include_filters: bool = Field(default=True)
    include_date_range: bool = Field(default=True)
    
    # Email configuration
    recipient_emails: List[str] = Field(sa_column=Column(ARRAY(String)))
    cc_emails: Optional[List[str]] = Field(default=[], sa_column=Column(ARRAY(String)))
    email_subject: str
    email_body: str
    
    # Status tracking
    is_active: bool = Field(default=True, index=True)
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    last_status: Optional[str] = None
    failure_count: int = Field(default=0)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    study: "Study" = Relationship(back_populates="scheduled_reports")
    dashboard: "Dashboard" = Relationship(back_populates="scheduled_reports")
    creator: "User" = Relationship()

# backend/app/services/export_service.py
from typing import Literal, BinaryIO
import asyncio
from io import BytesIO
import pandas as pd
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
import matplotlib.pyplot as plt
import seaborn as sns

class ExportService:
    """Generate various export formats from dashboard data"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Setup custom styles for reports"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=1  # Center
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#333333'),
            spaceAfter=12
        ))
    
    async def export_dashboard(
        self,
        study_id: str,
        dashboard_id: str,
        format: Literal["pdf", "pptx", "excel"],
        options: Dict[str, Any],
        user_id: str
    ) -> bytes:
        """Export dashboard in requested format"""
        
        # Fetch dashboard configuration and data
        dashboard_data = await self.fetch_dashboard_data(study_id, dashboard_id, options)
        
        # Add metadata
        dashboard_data['metadata'] = {
            'generated_at': datetime.utcnow().isoformat(),
            'generated_by': user_id,
            'study_id': study_id,
            'filters_applied': options.get('filters', {}),
            'date_range': options.get('date_range', {})
        }
        
        # Generate export based on format
        if format == "pdf":
            return await self.generate_pdf(dashboard_data, options)
        elif format == "pptx":
            return await self.generate_pptx(dashboard_data, options)
        elif format == "excel":
            return await self.generate_excel(dashboard_data, options)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    async def generate_pdf(self, data: Dict, options: Dict) -> bytes:
        """Generate pixel-perfect PDF report"""
        buffer = BytesIO()
        
        # Create PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4 if options.get('page_size') == 'A4' else letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )
        
        # Build content
        elements = []
        
        # Add header with logo
        if logo_path := options.get('logo_path'):
            logo = Image(logo_path, width=2*inch, height=0.75*inch)
            elements.append(logo)
            elements.append(Spacer(1, 0.5*inch))
        
        # Add title
        title = Paragraph(data['dashboard_name'], self.styles['CustomTitle'])
        elements.append(title)
        
        # Add metadata section
        metadata_text = f"Generated on: {data['metadata']['generated_at']}<br/>"
        if data['metadata']['filters_applied']:
            metadata_text += f"Filters: {', '.join(f'{k}={v}' for k, v in data['metadata']['filters_applied'].items())}<br/>"
        
        metadata = Paragraph(metadata_text, self.styles['Normal'])
        elements.append(metadata)
        elements.append(Spacer(1, 0.5*inch))
        
        # Process each widget
        for page in data['pages']:
            # Page header
            page_header = Paragraph(page['name'], self.styles['SectionHeader'])
            elements.append(page_header)
            
            for widget in page['widgets']:
                elements.extend(await self.render_widget_to_pdf(widget))
                elements.append(Spacer(1, 0.25*inch))
            
            elements.append(PageBreak())
        
        # Build PDF
        doc.build(elements)
        
        return buffer.getvalue()
    
    async def render_widget_to_pdf(self, widget: Dict) -> List:
        """Render a single widget to PDF elements"""
        elements = []
        
        # Widget title
        title = Paragraph(widget['title'], self.styles['Heading3'])
        elements.append(title)
        
        if widget['type'] == 'metric':
            # Render metric as a styled paragraph
            metric_text = f"<font size=24><b>{widget['data']['value']}</b></font><br/>"
            metric_text += f"<font size=12>{widget['data']['label']}</font>"
            
            if trend := widget['data'].get('trend'):
                trend_symbol = "↑" if trend > 0 else "↓"
                trend_color = "green" if trend > 0 else "red"
                metric_text += f"<br/><font color='{trend_color}'>{trend_symbol} {abs(trend)}%</font>"
            
            metric = Paragraph(metric_text, self.styles['Normal'])
            elements.append(metric)
            
        elif widget['type'] == 'table':
            # Convert data to table
            table_data = [widget['data']['headers']] + widget['data']['rows']
            
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(table)
            
        elif widget['type'] == 'chart':
            # Render chart to image
            chart_img = await self.render_chart_to_image(widget)
            elements.append(Image(chart_img, width=6*inch, height=4*inch))
        
        return elements
    
    async def render_chart_to_image(self, widget: Dict) -> BytesIO:
        """Render chart widget to image"""
        plt.figure(figsize=(10, 6))
        
        chart_type = widget['config']['chart_type']
        data = pd.DataFrame(widget['data']['data'])
        
        if chart_type == 'line':
            plt.plot(data[widget['config']['x_axis']], data[widget['config']['y_axis']])
        elif chart_type == 'bar':
            plt.bar(data[widget['config']['x_axis']], data[widget['config']['y_axis']])
        elif chart_type == 'scatter':
            plt.scatter(data[widget['config']['x_axis']], data[widget['config']['y_axis']])
        elif chart_type == 'pie':
            plt.pie(data[widget['config']['value']], labels=data[widget['config']['label']])
        
        plt.title(widget['title'])
        plt.xlabel(widget['config'].get('x_label', ''))
        plt.ylabel(widget['config'].get('y_label', ''))
        
        # Save to buffer
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        plt.close()
        
        buffer.seek(0)
        return buffer
    
    async def generate_pptx(self, data: Dict, options: Dict) -> bytes:
        """Generate PowerPoint presentation"""
        prs = Presentation()
        
        # Set slide size
        prs.slide_width = Inches(10)
        prs.slide_height = Inches(7.5)
        
        # Title slide
        title_slide_layout = prs.slide_layouts[0]
        slide = prs.slides.add_slide(title_slide_layout)
        
        title = slide.shapes.title
        subtitle = slide.placeholders[1]
        
        title.text = data['dashboard_name']
        subtitle.text = f"Generated on {data['metadata']['generated_at']}"
        
        # Process each page as a section
        for page in data['pages']:
            # Section title slide
            section_layout = prs.slide_layouts[2]
            section_slide = prs.slides.add_slide(section_layout)
            section_slide.shapes.title.text = page['name']
            
            # Add widgets to slides
            for widget in page['widgets']:
                slide_layout = prs.slide_layouts[5]  # Blank layout
                slide = prs.slides.add_slide(slide_layout)
                
                # Add title
                title_shape = slide.shapes.add_textbox(
                    Inches(0.5), Inches(0.5), Inches(9), Inches(1)
                )
                title_frame = title_shape.text_frame
                title_frame.text = widget['title']
                title_frame.paragraphs[0].font.size = Pt(24)
                title_frame.paragraphs[0].font.bold = True
                
                # Add content based on widget type
                if widget['type'] == 'metric':
                    await self.add_metric_to_slide(slide, widget)
                elif widget['type'] == 'table':
                    await self.add_table_to_slide(slide, widget)
                elif widget['type'] == 'chart':
                    await self.add_chart_to_slide(slide, widget)
        
        # Save to buffer
        buffer = BytesIO()
        prs.save(buffer)
        
        return buffer.getvalue()
    
    async def generate_excel(self, data: Dict, options: Dict) -> bytes:
        """Generate Excel workbook with multiple sheets"""
        buffer = BytesIO()
        
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            workbook = writer.book
            
            # Add metadata sheet
            metadata_df = pd.DataFrame([data['metadata']])
            metadata_df.to_excel(writer, sheet_name='Metadata', index=False)
            
            # Add a sheet for each page
            for page in data['pages']:
                # Create a sheet for the page
                worksheet = workbook.add_worksheet(page['name'][:31])  # Excel sheet name limit
                
                row = 0
                for widget in page['widgets']:
                    # Write widget title
                    worksheet.write(row, 0, widget['title'], workbook.add_format({'bold': True, 'size': 14}))
                    row += 2
                    
                    if widget['type'] == 'table':
                        # Write table data
                        df = pd.DataFrame(widget['data']['rows'], columns=widget['data']['headers'])
                        df.to_excel(writer, sheet_name=page['name'][:31], startrow=row, index=False)
                        row += len(df) + 3
                    
                    elif widget['type'] == 'metric':
                        # Write metric data
                        worksheet.write(row, 0, widget['data']['label'])
                        worksheet.write(row, 1, widget['data']['value'])
                        if trend := widget['data'].get('trend'):
                            worksheet.write(row, 2, f"{trend}%")
                        row += 3
        
        return buffer.getvalue()
```

### Task 4.2: Scheduled Reports Implementation

```python
# backend/app/api/api_v1/endpoints/scheduled_reports.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.models import ScheduledReport, User
from app.schemas.scheduled_report import (
    ScheduledReportCreate, 
    ScheduledReportUpdate, 
    ScheduledReportResponse
)
from app.core.rbac_middleware import require_dashboard_edit
from app.services.scheduler_service import SchedulerService

router = APIRouter()

@router.get("/studies/{study_id}/scheduled-reports", response_model=List[ScheduledReportResponse])
async def list_scheduled_reports(
    study_id: str,
    current_user: User = Depends(require_study_read),
    db: AsyncSession = Depends(get_session)
):
    """List all scheduled reports for a study"""
    reports = await db.exec(
        select(ScheduledReport)
        .where(ScheduledReport.study_id == study_id)
        .order_by(ScheduledReport.created_at.desc())
    )
    return reports.all()

@router.post("/scheduled-reports", response_model=ScheduledReportResponse)
async def create_scheduled_report(
    report_data: ScheduledReportCreate,
    current_user: User = Depends(require_dashboard_edit),
    scheduler: SchedulerService = Depends(),
    db: AsyncSession = Depends(get_session)
):
    """Create a new scheduled report"""
    # Create report record
    report = ScheduledReport(
        **report_data.dict(),
        created_by=current_user.id,
        next_run=scheduler.calculate_next_run(report_data)
    )
    
    db.add(report)
    await db.commit()
    await db.refresh(report)
    
    # Schedule the job
    await scheduler.schedule_report(report)
    
    return report

@router.put("/scheduled-reports/{report_id}")
async def update_scheduled_report(
    report_id: str,
    updates: ScheduledReportUpdate,
    current_user: User = Depends(require_dashboard_edit),
    scheduler: SchedulerService = Depends(),
    db: AsyncSession = Depends(get_session)
):
    """Update scheduled report configuration"""
    report = await db.get(ScheduledReport, report_id)
    if not report:
        raise HTTPException(404, "Report not found")
    
    # Update fields
    for key, value in updates.dict(exclude_unset=True).items():
        setattr(report, key, value)
    
    report.updated_at = datetime.utcnow()
    
    # Reschedule if schedule changed
    if any(field in updates.dict() for field in ['schedule_type', 'schedule_time', 'schedule_days']):
        report.next_run = scheduler.calculate_next_run(report)
        await scheduler.reschedule_report(report)
    
    await db.commit()
    return report

@router.post("/scheduled-reports/{report_id}/test")
async def test_scheduled_report(
    report_id: str,
    current_user: User = Depends(require_dashboard_edit),
    service: SchedulerService = Depends()
):
    """Send a test report immediately"""
    return await service.send_test_report(report_id, current_user.email)

# backend/app/services/scheduler_service.py
from datetime import datetime, timedelta
from typing import Optional
from celery.schedules import crontab
from app.models import ScheduledReport
from app.services.export_service import ExportService
from app.services.email_service import EmailService
from app.workers.celery_app import celery_app

class SchedulerService:
    """Manage scheduled report execution"""
    
    def __init__(self):
        self.export_service = ExportService()
        self.email_service = EmailService()
    
    def calculate_next_run(self, report: ScheduledReport) -> datetime:
        """Calculate next run time based on schedule configuration"""
        now = datetime.utcnow()
        
        if report.schedule_type == "daily":
            # Next occurrence of schedule_time
            next_run = now.replace(
                hour=report.schedule_time.hour,
                minute=report.schedule_time.minute,
                second=0,
                microsecond=0
            )
            if next_run <= now:
                next_run += timedelta(days=1)
                
        elif report.schedule_type == "weekly":
            # Next occurrence on specified days
            days_ahead = None
            for day in sorted(report.schedule_days):
                days_until = (day - now.weekday()) % 7
                if days_until == 0 and now.time() >= report.schedule_time:
                    days_until = 7
                if days_ahead is None or days_until < days_ahead:
                    days_ahead = days_until
            
            next_run = now + timedelta(days=days_ahead)
            next_run = next_run.replace(
                hour=report.schedule_time.hour,
                minute=report.schedule_time.minute,
                second=0,
                microsecond=0
            )
            
        elif report.schedule_type == "monthly":
            # Next occurrence on specified days of month
            # Implementation for monthly schedules
            pass
            
        return next_run
    
    async def schedule_report(self, report: ScheduledReport):
        """Schedule a report in Celery Beat"""
        schedule_name = f"scheduled_report_{report.id}"
        
        if report.schedule_type == "custom" and report.schedule_cron:
            # Parse cron expression
            hour, minute = report.schedule_cron.split()[:2]
            schedule = crontab(hour=hour, minute=minute)
        else:
            # Convert to cron based on schedule type
            if report.schedule_type == "daily":
                schedule = crontab(
                    hour=report.schedule_time.hour,
                    minute=report.schedule_time.minute
                )
            elif report.schedule_type == "weekly":
                schedule = crontab(
                    hour=report.schedule_time.hour,
                    minute=report.schedule_time.minute,
                    day_of_week=','.join(str(d) for d in report.schedule_days)
                )
        
        # Add to Celery Beat schedule
        celery_app.conf.beat_schedule[schedule_name] = {
            'task': 'app.workers.report_tasks.generate_and_send_report',
            'schedule': schedule,
            'args': [str(report.id)],
            'options': {'queue': 'reports'}
        }
    
    async def send_test_report(self, report_id: str, test_email: str):
        """Generate and send a test report immediately"""
        from app.workers.report_tasks import generate_and_send_report
        
        # Queue the task with test flag
        task = generate_and_send_report.apply_async(
            args=[report_id],
            kwargs={'test_mode': True, 'test_email': test_email},
            queue='reports'
        )
        
        return {
            "status": "queued",
            "task_id": task.id,
            "message": f"Test report will be sent to {test_email}"
        }

# backend/app/workers/report_tasks.py
@celery_app.task(name='generate_and_send_report')
def generate_and_send_report(report_id: str, test_mode: bool = False, test_email: str = None):
    """Generate and send a scheduled report"""
    from app.core.db import SessionLocal
    from app.services.export_service import ExportService
    from app.services.email_service import EmailService
    
    logger.info(f"Generating scheduled report {report_id}")
    
    try:
        with SessionLocal() as db:
            # Get report configuration
            report = db.query(ScheduledReport).filter(
                ScheduledReport.id == report_id
            ).first()
            
            if not report:
                raise ValueError(f"Report {report_id} not found")
            
            # Skip if not active (unless test mode)
            if not report.is_active and not test_mode:
                logger.info(f"Report {report_id} is not active, skipping")
                return
            
            # Generate export
            export_service = ExportService()
            export_data = asyncio.run(
                export_service.export_dashboard(
                    study_id=str(report.study_id),
                    dashboard_id=str(report.dashboard_id),
                    format=report.export_format,
                    options=report.export_options,
                    user_id=str(report.created_by)
                )
            )
            
            # Prepare email
            email_service = EmailService()
            recipients = [test_email] if test_mode else report.recipient_emails
            
            # Send email with attachment
            asyncio.run(
                email_service.send_report(
                    to_emails=recipients,
                    cc_emails=report.cc_emails if not test_mode else [],
                    subject=report.email_subject,
                    body=report.email_body,
                    attachment_data=export_data,
                    attachment_name=f"{report.name}_{datetime.utcnow().strftime('%Y%m%d')}.{report.export_format}",
                    attachment_type=report.export_format
                )
            )
            
            # Update report status (unless test mode)
            if not test_mode:
                report.last_run = datetime.utcnow()
                report.last_status = "success"
                report.failure_count = 0
                report.next_run = SchedulerService().calculate_next_run(report)
                db.commit()
            
            logger.info(f"Successfully sent report {report_id}")
            
    except Exception as e:
        logger.error(f"Failed to generate report {report_id}: {str(e)}")
        
        if not test_mode:
            with SessionLocal() as db:
                report = db.query(ScheduledReport).filter(
                    ScheduledReport.id == report_id
                ).first()
                if report:
                    report.last_status = "failed"
                    report.failure_count += 1
                    
                    # Disable after 3 failures
                    if report.failure_count >= 3:
                        report.is_active = False
                        logger.error(f"Report {report_id} disabled after 3 failures")
                    
                    db.commit()
        
        raise
```

### Task 5.1: Configuration Schema

```python
# backend/app/clinical_modules/configuration/schema.py
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any, Union
from enum import Enum

class DataSourceType(str, Enum):
    MEDIDATA_API = "medidata_api"
    EDC_API = "edc_api"
    SFTP = "sftp"
    FOLDER_SYNC = "folder_sync"

class FieldMapping(BaseModel):
    source_field: Union[str, List[str]]
    target_field: str
    transformation: Optional[str] = None
    default_value: Optional[Any] = None
    required: bool = False

class MetricConfig(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    type: str  # row_count, unique_count, aggregation, calculation, custom
    data_source: Dict[str, Any]
    cache_duration: Optional[int] = 300
    
class WidgetConfig(BaseModel):
    id: str
    type: str  # metric, chart, table, custom
    title: str
    data_config: Dict[str, Any]
    visualization_config: Dict[str, Any]
    position: Dict[str, int]  # grid position
    size: Dict[str, int]  # width, height
    
class DashboardPageConfig(BaseModel):
    id: str
    name: str
    icon: Optional[str] = None
    layout: str = "grid"  # grid, flex
    widgets: List[WidgetConfig]
    permissions: Optional[List[str]] = None

class StudyConfiguration(BaseModel):
    """Complete study configuration"""
    version: int = 1
    extends: Optional[str] = None  # Parent template
    
    # Data configuration
    data_source: Dict[str, Any]
    field_mappings: Dict[str, FieldMapping]
    
    # Metrics
    metrics: Dict[str, MetricConfig]
    
    # Dashboard
    pages: List[DashboardPageConfig]
    theme: Optional[Dict[str, Any]] = None
    
    # Features
    features: Dict[str, bool] = {
        "activity_tracking": True,
        "data_export": True,
        "real_time_updates": False
    }
```

### Task 5.2: Configuration Service

```python
# backend/app/services/configuration_service.py
from typing import Dict, Optional, List
import json
import yaml
from deepmerge import always_merger

from app.models import Study, Organization
from app.clinical_modules.configuration.schema import StudyConfiguration
from app.clinical_modules.configuration.validator import ConfigurationValidator

class ConfigurationService:
    """Manages study configurations with inheritance"""
    
    def __init__(self):
        self.validator = ConfigurationValidator()
        self.template_cache = {}
        
    async def get_effective_configuration(
        self, 
        study_id: str,
        include_inherited: bool = True
    ) -> StudyConfiguration:
        """Get merged configuration for a study"""
        
        # Get study
        study = await self._get_study(study_id)
        
        # Start with base template
        config = {}
        
        if include_inherited and study.template_id:
            template = await self._get_template(study.template_id)
            config = template.dict()
        
        # Merge organization config
        if study.organization.config:
            config = always_merger.merge(config, study.organization.config)
        
        # Merge study config
        if study.dashboard_config:
            config = always_merger.merge(config, study.dashboard_config)
        
        # Validate final configuration
        validation = await self.validator.validate(config)
        if not validation.is_valid:
            raise ValueError(f"Invalid configuration: {validation.errors}")
        
        return StudyConfiguration(**config)
    
    async def update_configuration(
        self,
        study_id: str,
        updates: Dict[str, Any],
        user_id: str,
        validate_only: bool = False
    ) -> StudyConfiguration:
        """Update study configuration with validation"""
        
        # Get current config
        current = await self.get_effective_configuration(study_id)
        
        # Apply updates
        updated_dict = always_merger.merge(current.dict(), updates)
        
        # Validate
        validation = await self.validator.validate(updated_dict)
        if not validation.is_valid:
            raise ValueError(f"Invalid configuration: {validation.errors}")
        
        if validate_only:
            return StudyConfiguration(**updated_dict)
        
        # Save to database
        study = await self._get_study(study_id)
        study.dashboard_config = updates  # Store only the overrides
        study.config_version += 1
        
        # Create audit log
        await self._create_config_audit(
            study_id=study_id,
            user_id=user_id,
            changes=updates,
            version=study.config_version
        )
        
        await study.save()
        
        return await self.get_effective_configuration(study_id)
```

### Task 5.3: Configuration API

```python
# backend/app/api/api_v1/endpoints/configurations.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Dict, Any

from app.api import deps
from app.models import User
from app.services.configuration_service import ConfigurationService
from app.clinical_modules.configuration.schema import StudyConfiguration

router = APIRouter()

@router.get("/studies/{study_id}/configuration")
async def get_study_configuration(
    study_id: str,
    current_user: User = Depends(deps.get_current_active_user),
    service: ConfigurationService = Depends()
) -> StudyConfiguration:
    """Get effective configuration for a study"""
    
    # Check permissions
    if not await deps.user_has_study_access(current_user, study_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return await service.get_effective_configuration(study_id)

@router.put("/studies/{study_id}/configuration")
async def update_study_configuration(
    study_id: str,
    updates: Dict[str, Any],
    background_tasks: BackgroundTasks,
    current_user: User = Depends(deps.get_current_active_superuser),
    service: ConfigurationService = Depends()
) -> StudyConfiguration:
    """Update study configuration"""
    
    # Update configuration
    config = await service.update_configuration(
        study_id=study_id,
        updates=updates,
        user_id=str(current_user.id)
    )
    
    # Trigger configuration reload in background
    background_tasks.add_task(
        reload_study_configuration,
        study_id=study_id
    )
    
    return config

@router.post("/studies/{study_id}/configuration/validate")
async def validate_configuration(
    study_id: str,
    config: Dict[str, Any],
    current_user: User = Depends(deps.get_current_active_user),
    service: ConfigurationService = Depends()
) -> Dict[str, Any]:
    """Validate configuration without saving"""
    
    try:
        await service.update_configuration(
            study_id=study_id,
            updates=config,
            user_id=str(current_user.id),
            validate_only=True
        )
        return {"valid": True, "errors": []}
    except ValueError as e:
        return {"valid": False, "errors": [str(e)]}
```

### Task 5.4: Public API for External Integrations

```python
# backend/app/models/api_key.py
from sqlmodel import SQLModel, Field
from typing import Optional, List
from datetime import datetime, timedelta
import uuid
import secrets

class APIKey(SQLModel, table=True):
    """API keys for external integrations"""
    __tablename__ = "api_keys"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(index=True)
    key_hash: str = Field(unique=True, index=True)  # Store hashed version
    org_id: uuid.UUID = Field(foreign_key="organizations.id", index=True)
    created_by: uuid.UUID = Field(foreign_key="users.id")
    
    # Permissions
    scopes: List[str] = Field(default=[], sa_column=Column(ARRAY(String)))
    study_ids: Optional[List[uuid.UUID]] = Field(default=None, sa_column=Column(ARRAY(UUID)))  # Null = all studies
    
    # Rate limiting
    rate_limit_per_hour: int = Field(default=1000)
    rate_limit_per_day: int = Field(default=10000)
    
    # Status
    is_active: bool = Field(default=True, index=True)
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    revoked_at: Optional[datetime] = None
    
    @staticmethod
    def generate_key() -> tuple[str, str]:
        """Generate API key and return (plain_key, hashed_key)"""
        plain_key = f"cdp_{secrets.token_urlsafe(32)}"
        hashed_key = hashlib.sha256(plain_key.encode()).hexdigest()
        return plain_key, hashed_key

# backend/app/core/api_key_auth.py
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from app.models import APIKey, Organization
from app.core.db import get_session
import hashlib

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def validate_api_key(
    api_key: str = Security(api_key_header),
    db: AsyncSession = Depends(get_session)
) -> APIKey:
    """Validate API key and return associated organization"""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )
    
    # Hash the provided key
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    
    # Look up API key
    key_record = await db.exec(
        select(APIKey)
        .where(APIKey.key_hash == key_hash)
        .where(APIKey.is_active == True)
    )
    key_record = key_record.first()
    
    if not key_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    # Check expiration
    if key_record.expires_at and key_record.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key expired"
        )
    
    # Update last used
    key_record.last_used_at = datetime.utcnow()
    await db.commit()
    
    return key_record

# backend/app/api/api_v1/endpoints/public_api.py
"""
Public API endpoints for external integrations
All functionality available in UI is also available via API
"""
from fastapi import APIRouter, Depends, Query, Header
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from app.core.api_key_auth import validate_api_key
from app.models import APIKey, Study, Dashboard
from app.schemas.public_api import *
from app.services.public_api_service import PublicAPIService

router = APIRouter()

# Rate limiting decorator
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.get("/studies", response_model=List[StudyPublicResponse])
@limiter.limit("100/hour")
async def list_studies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    api_key: APIKey = Depends(validate_api_key),
    service: PublicAPIService = Depends()
):
    """List all studies accessible with this API key"""
    return await service.list_studies(api_key, skip, limit)

@router.get("/studies/{study_id}", response_model=StudyDetailResponse)
@limiter.limit("1000/hour")
async def get_study(
    study_id: str,
    api_key: APIKey = Depends(validate_api_key),
    service: PublicAPIService = Depends()
):
    """Get detailed study information"""
    return await service.get_study(api_key, study_id)

@router.post("/studies/{study_id}/pipeline/execute")
@limiter.limit("10/hour")
async def execute_pipeline(
    study_id: str,
    options: Optional[PipelineExecutionOptions] = None,
    api_key: APIKey = Depends(validate_api_key),
    service: PublicAPIService = Depends()
):
    """Execute data pipeline for a study"""
    if "pipeline:execute" not in api_key.scopes:
        raise HTTPException(403, "API key lacks pipeline execution permission")
    
    return await service.execute_pipeline(api_key, study_id, options)

@router.get("/studies/{study_id}/pipeline/status/{execution_id}")
async def get_pipeline_status(
    study_id: str,
    execution_id: str,
    api_key: APIKey = Depends(validate_api_key),
    service: PublicAPIService = Depends()
):
    """Get pipeline execution status"""
    return await service.get_pipeline_status(api_key, study_id, execution_id)

@router.get("/studies/{study_id}/dashboards")
async def list_dashboards(
    study_id: str,
    api_key: APIKey = Depends(validate_api_key),
    service: PublicAPIService = Depends()
):
    """List all dashboards for a study"""
    return await service.list_dashboards(api_key, study_id)

@router.get("/studies/{study_id}/dashboards/{dashboard_id}/data")
@limiter.limit("100/hour")
async def get_dashboard_data(
    study_id: str,
    dashboard_id: str,
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    filters: Optional[Dict[str, Any]] = Query({}),
    api_key: APIKey = Depends(validate_api_key),
    service: PublicAPIService = Depends()
):
    """Get dashboard data with optional filters"""
    return await service.get_dashboard_data(
        api_key, study_id, dashboard_id, 
        date_from, date_to, filters
    )

@router.post("/studies/{study_id}/dashboards/{dashboard_id}/export")
@limiter.limit("20/hour")
async def export_dashboard(
    study_id: str,
    dashboard_id: str,
    export_request: ExportRequest,
    api_key: APIKey = Depends(validate_api_key),
    service: PublicAPIService = Depends()
):
    """Export dashboard in various formats"""
    if "dashboard:export" not in api_key.scopes:
        raise HTTPException(403, "API key lacks export permission")
    
    return await service.export_dashboard(
        api_key, study_id, dashboard_id, export_request
    )

@router.get("/studies/{study_id}/data/{dataset}")
@limiter.limit("50/hour")
async def get_study_data(
    study_id: str,
    dataset: str,
    format: Literal["json", "csv", "parquet"] = "json",
    filters: Optional[Dict[str, Any]] = Query({}),
    api_key: APIKey = Depends(validate_api_key),
    service: PublicAPIService = Depends()
):
    """Get raw study data"""
    if "data:read" not in api_key.scopes:
        raise HTTPException(403, "API key lacks data read permission")
    
    return await service.get_study_data(
        api_key, study_id, dataset, format, filters
    )

@router.post("/studies/{study_id}/data/upload")
@limiter.limit("10/hour")
async def upload_data(
    study_id: str,
    file: UploadFile,
    dataset: str = Form(...),
    api_key: APIKey = Depends(validate_api_key),
    service: PublicAPIService = Depends()
):
    """Upload data files to study"""
    if "data:write" not in api_key.scopes:
        raise HTTPException(403, "API key lacks data write permission")
    
    return await service.upload_data(api_key, study_id, file, dataset)

# Webhook endpoints
@router.post("/webhooks")
async def register_webhook(
    webhook: WebhookCreate,
    api_key: APIKey = Depends(validate_api_key),
    service: PublicAPIService = Depends()
):
    """Register a webhook for events"""
    return await service.register_webhook(api_key, webhook)

@router.get("/webhooks")
async def list_webhooks(
    api_key: APIKey = Depends(validate_api_key),
    service: PublicAPIService = Depends()
):
    """List registered webhooks"""
    return await service.list_webhooks(api_key)

# API documentation
@router.get("/openapi.json")
async def get_openapi_spec():
    """Get OpenAPI specification for this API"""
    return app.openapi()

@router.get("/postman-collection")
async def get_postman_collection():
    """Get Postman collection for easy testing"""
    return generate_postman_collection()

# SDK generation endpoints
@router.get("/sdk/{language}")
async def generate_sdk(
    language: Literal["python", "javascript", "java", "csharp"],
    api_key: APIKey = Depends(validate_api_key)
):
    """Generate SDK for specified language"""
    return await generate_client_sdk(language, api_key.org_id)

# backend/app/services/public_api_service.py
class PublicAPIService:
    """Service layer for public API operations"""
    
    async def check_study_access(self, api_key: APIKey, study_id: str) -> bool:
        """Check if API key has access to study"""
        if api_key.study_ids is None:
            # Access to all studies in organization
            study = await self.db.get(Study, study_id)
            return study and study.org_id == api_key.org_id
        else:
            # Access to specific studies only
            return uuid.UUID(study_id) in api_key.study_ids
    
    async def list_studies(
        self, 
        api_key: APIKey, 
        skip: int, 
        limit: int
    ) -> List[Study]:
        """List studies accessible to API key"""
        query = select(Study).where(Study.org_id == api_key.org_id)
        
        if api_key.study_ids:
            query = query.where(Study.id.in_(api_key.study_ids))
        
        studies = await self.db.exec(query.offset(skip).limit(limit))
        return studies.all()
    
    async def execute_pipeline(
        self,
        api_key: APIKey,
        study_id: str,
        options: Optional[PipelineExecutionOptions]
    ) -> Dict[str, Any]:
        """Execute pipeline via API"""
        # Check access
        if not await self.check_study_access(api_key, study_id):
            raise HTTPException(403, "Access denied to study")
        
        # Use same logic as UI endpoint
        from app.api.api_v1.endpoints.pipelines import trigger_pipeline_execution
        
        # Create synthetic user for API key
        api_user = User(
            id=api_key.id,
            email=f"api-key-{api_key.id}@system",
            org_id=api_key.org_id,
            is_api_user=True
        )
        
        return await trigger_pipeline_execution(
            study_id=study_id,
            current_user=api_user,
            db=self.db
        )

# API Key Management UI
# frontend/src/app/admin/api-keys/page.tsx
export default function APIKeysPage() {
  const [apiKeys, setApiKeys] = useState<APIKey[]>([]);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  
  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">API Keys</h1>
        <Button onClick={() => setShowCreateDialog(true)}>
          <Key className="mr-2 h-4 w-4" />
          Create API Key
        </Button>
      </div>
      
      <Card>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Scopes</TableHead>
                <TableHead>Rate Limit</TableHead>
                <TableHead>Last Used</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {apiKeys.map(key => (
                <TableRow key={key.id}>
                  <TableCell>{key.name}</TableCell>
                  <TableCell>
                    <div className="flex flex-wrap gap-1">
                      {key.scopes.map(scope => (
                        <Badge key={scope} variant="secondary">
                          {scope}
                        </Badge>
                      ))}
                    </div>
                  </TableCell>
                  <TableCell>{key.rateLimitPerHour}/hr</TableCell>
                  <TableCell>{key.lastUsedAt || 'Never'}</TableCell>
                  <TableCell>
                    <Badge variant={key.isActive ? 'success' : 'destructive'}>
                      {key.isActive ? 'Active' : 'Revoked'}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger>
                        <MoreHorizontal className="h-4 w-4" />
                      </DropdownMenuTrigger>
                      <DropdownMenuContent>
                        <DropdownMenuItem onClick={() => copyKey(key.id)}>
                          Copy Key
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => editKey(key.id)}>
                          Edit Scopes
                        </DropdownMenuItem>
                        <DropdownMenuItem 
                          onClick={() => revokeKey(key.id)}
                          className="text-red-600"
                        >
                          Revoke Key
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
      
      <CreateAPIKeyDialog 
        open={showCreateDialog}
        onOpenChange={setShowCreateDialog}
        onCreated={handleKeyCreated}
      />
    </div>
  );
}
```

### Deliverables - Phase 5
- [ ] Configuration schema and inheritance
- [ ] Configuration service with validation
- [ ] Configuration APIs with RBAC
- [ ] Public API for external integrations
- [ ] API key management system
- [ ] Rate limiting and security

## Phase 5: Configuration Engine (Week 9-10)

### Task 5.1: Widget System

```python
# backend/app/clinical_modules/dashboard/widgets.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import pandas as pd

class BaseWidget(ABC):
    """Base class for all dashboard widgets"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.id = config.get('id')
        self.title = config.get('title', 'Untitled')
        
    @abstractmethod
    async def fetch_data(self, context: Dict[str, Any]) -> Any:
        """Fetch data for the widget"""
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """Validate widget configuration"""
        pass

class MetricWidget(BaseWidget):
    """Simple metric display widget"""
    
    async def fetch_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        metric_id = self.config['metric_id']
        study_id = context['study_id']
        
        # Get metric value from unified adapter
        from app.clinical_modules.adapters import UnifiedAdapterEngine
        engine = UnifiedAdapterEngine()
        
        value = await engine.execute_metric(study_id, metric_id)
        
        return {
            "value": value,
            "label": self.config.get('label', metric_id),
            "format": self.config.get('format', 'number')
        }
    
    def validate_config(self) -> bool:
        return 'metric_id' in self.config

class ChartWidget(BaseWidget):
    """Chart visualization widget"""
    
    async def fetch_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        # Get data based on configuration
        data_config = self.config['data_config']
        
        # Fetch data using appropriate adapter
        data = await self._fetch_chart_data(context, data_config)
        
        return {
            "data": data.to_dict('records'),
            "chart_type": self.config.get('chart_type', 'line'),
            "options": self.config.get('chart_options', {})
        }
    
    async def _fetch_chart_data(
        self, 
        context: Dict[str, Any], 
        data_config: Dict[str, Any]
    ) -> pd.DataFrame:
        # Implementation for fetching chart data
        pass
```

### Task 6.2: Frontend Dashboard Components

```typescript
// frontend/src/components/dashboard/DashboardRenderer.tsx
import React, { useEffect, useState } from 'react';
import { Grid, Responsive, WidthProvider } from 'react-grid-layout';
import { useQuery } from '@tanstack/react-query';
import { Skeleton } from '@/components/ui/skeleton';
import { MetricWidget } from './widgets/MetricWidget';
import { ChartWidget } from './widgets/ChartWidget';
import { TableWidget } from './widgets/TableWidget';
import { api } from '@/lib/api-client';

const ResponsiveGridLayout = WidthProvider(Responsive);

interface DashboardRendererProps {
  studyId: string;
  pageId: string;
}

export function DashboardRenderer({ studyId, pageId }: DashboardRendererProps) {
  const [layouts, setLayouts] = useState({});
  
  // Fetch dashboard configuration
  const { data: config, isLoading } = useQuery({
    queryKey: ['dashboard-config', studyId, pageId],
    queryFn: () => api.get(`/studies/${studyId}/dashboard/pages/${pageId}`)
  });
  
  if (isLoading) {
    return <DashboardSkeleton />;
  }
  
  const renderWidget = (widget: any) => {
    const components: Record<string, any> = {
      metric: MetricWidget,
      chart: ChartWidget,
      table: TableWidget,
    };
    
    const Component = components[widget.type];
    if (!Component) return null;
    
    return (
      <div key={widget.id} data-grid={widget.position}>
        <Component
          widgetId={widget.id}
          config={widget}
          studyId={studyId}
        />
      </div>
    );
  };
  
  return (
    <ResponsiveGridLayout
      className="layout"
      layouts={layouts}
      onLayoutChange={(layout, layouts) => setLayouts(layouts)}
      cols={{ lg: 12, md: 10, sm: 6, xs: 4, xxs: 2 }}
      rowHeight={60}
      isDraggable={false}
      isResizable={false}
    >
      {config?.data.widgets.map(renderWidget)}
    </ResponsiveGridLayout>
  );
}

// frontend/src/components/dashboard/widgets/MetricWidget.tsx
import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api-client';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface MetricWidgetProps {
  widgetId: string;
  config: any;
  studyId: string;
}

export function MetricWidget({ widgetId, config, studyId }: MetricWidgetProps) {
  const { data, isLoading } = useQuery({
    queryKey: ['widget-data', studyId, widgetId],
    queryFn: () => api.get(`/studies/${studyId}/widgets/${widgetId}/data`),
    refetchInterval: config.refreshInterval || 60000,
  });
  
  if (isLoading) {
    return (
      <Card className="h-full">
        <CardContent className="p-6">
          <Skeleton className="h-8 w-24" />
          <Skeleton className="h-4 w-32 mt-2" />
        </CardContent>
      </Card>
    );
  }
  
  const { value, label, trend } = data?.data || {};
  
  return (
    <Card className="h-full">
      <CardContent className="p-6">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-3xl font-bold">{value || 0}</p>
            <p className="text-sm text-muted-foreground mt-1">{label}</p>
          </div>
          {trend && (
            <div className={`flex items-center ${trend > 0 ? 'text-green-500' : 'text-red-500'}`}>
              {trend > 0 ? <TrendingUp size={20} /> : <TrendingDown size={20} />}
              <span className="ml-1 text-sm">{Math.abs(trend)}%</span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
```

### Task 6.3: Dashboard Builder UI

```typescript
// frontend/src/app/admin/studies/[studyId]/dashboard/builder/page.tsx
import React, { useState } from 'react';
import { DndProvider } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { WidgetLibrary } from '@/components/admin/dashboard/WidgetLibrary';
import { DashboardCanvas } from '@/components/admin/dashboard/DashboardCanvas';
import { WidgetPropertiesPanel } from '@/components/admin/dashboard/WidgetPropertiesPanel';
import { Save, Eye, Undo, Redo } from 'lucide-react';

export default function DashboardBuilderPage({ 
  params 
}: { 
  params: { studyId: string } 
}) {
  const [selectedWidget, setSelectedWidget] = useState(null);
  const [isDirty, setIsDirty] = useState(false);
  const [layout, setLayout] = useState([]);
  
  const handleSave = async () => {
    // Save dashboard configuration
    const config = {
      layout,
      widgets: layout.map(item => ({
        id: item.i,
        ...item.config
      }))
    };
    
    await api.put(`/studies/${params.studyId}/dashboard`, config);
    setIsDirty(false);
  };
  
  return (
    <DndProvider backend={HTML5Backend}>
      <div className="h-screen flex flex-col">
        {/* Toolbar */}
        <div className="border-b p-4 flex items-center justify-between">
          <h1 className="text-2xl font-bold">Dashboard Builder</h1>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm">
              <Undo className="h-4 w-4" />
            </Button>
            <Button variant="outline" size="sm">
              <Redo className="h-4 w-4" />
            </Button>
            <Button variant="outline" size="sm">
              <Eye className="h-4 w-4 mr-2" />
              Preview
            </Button>
            <Button 
              onClick={handleSave}
              disabled={!isDirty}
              size="sm"
            >
              <Save className="h-4 w-4 mr-2" />
              Save
            </Button>
          </div>
        </div>
        
        <div className="flex-1 flex overflow-hidden">
          {/* Widget Library */}
          <div className="w-64 border-r bg-gray-50 p-4 overflow-y-auto">
            <WidgetLibrary studyId={params.studyId} />
          </div>
          
          {/* Canvas */}
          <div className="flex-1 p-6 overflow-auto bg-gray-100">
            <DashboardCanvas
              layout={layout}
              onLayoutChange={(newLayout) => {
                setLayout(newLayout);
                setIsDirty(true);
              }}
              onWidgetSelect={setSelectedWidget}
            />
          </div>
          
          {/* Properties Panel */}
          <div className="w-80 border-l bg-gray-50 p-4 overflow-y-auto">
            <WidgetPropertiesPanel
              widget={selectedWidget}
              onChange={(updates) => {
                // Update widget configuration
                setIsDirty(true);
              }}
            />
          </div>
        </div>
      </div>
    </DndProvider>
  );
}
```

### Deliverables - Phase 6
- [ ] Widget system architecture
- [ ] Frontend widget components
- [ ] Dashboard builder UI
- [ ] Widget configuration system

## Phase 7: Admin Panel (Week 13-14)

### Task 7.1: Admin Panel Structure

```typescript
// frontend/src/app/admin/layout.tsx
import React from 'react';
import { AdminSidebar } from '@/components/admin/AdminSidebar';
import { AdminHeader } from '@/components/admin/AdminHeader';
import { Toaster } from '@/components/ui/toaster';

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-gray-50">
      <AdminHeader />
      <div className="flex">
        <AdminSidebar />
        <main className="flex-1 p-6">
          {children}
        </main>
      </div>
      <Toaster />
    </div>
  );
}

// frontend/src/components/admin/AdminSidebar.tsx
import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import {
  LayoutDashboard,
  Database,
  GitBranch,
  Settings,
  Users,
  Activity,
  FileText,
} from 'lucide-react';

const navigation = [
  { name: 'Overview', href: '/admin', icon: LayoutDashboard },
  { name: 'Studies', href: '/admin/studies', icon: FileText },
  { name: 'Data Sources', href: '/admin/data-sources', icon: Database },
  { name: 'Pipelines', href: '/admin/pipelines', icon: GitBranch },
  { name: 'Users', href: '/admin/users', icon: Users },
  { name: 'Activity', href: '/admin/activity', icon: Activity },
  { name: 'Settings', href: '/admin/settings', icon: Settings },
];

export function AdminSidebar() {
  const pathname = usePathname();
  
  return (
    <div className="w-64 bg-white border-r h-[calc(100vh-4rem)]">
      <nav className="p-4 space-y-1">
        {navigation.map((item) => {
          const isActive = pathname === item.href || 
                          pathname.startsWith(`${item.href}/`);
          
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                'flex items-center px-3 py-2 text-sm font-medium rounded-md',
                isActive
                  ? 'bg-gray-100 text-gray-900'
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
              )}
            >
              <item.icon className="mr-3 h-5 w-5" />
              {item.name}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
```

### Task 7.2: Study Management

```typescript
// frontend/src/app/admin/studies/page.tsx
import React from 'react';
import { Button } from '@/components/ui/button';
import { StudiesTable } from '@/components/admin/studies/StudiesTable';
import { Plus } from 'lucide-react';
import Link from 'next/link';

export default function StudiesPage() {
  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold">Studies</h1>
          <p className="text-gray-600 mt-1">
            Manage clinical studies and their configurations
          </p>
        </div>
        <Link href="/admin/studies/new">
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            New Study
          </Button>
        </Link>
      </div>
      
      <StudiesTable />
    </div>
  );
}

// frontend/src/components/admin/studies/StudiesTable.tsx
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { MoreHorizontal, Settings, BarChart } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { api } from '@/lib/api-client';
import Link from 'next/link';

export function StudiesTable() {
  const { data: studies, isLoading } = useQuery({
    queryKey: ['admin', 'studies'],
    queryFn: () => api.get('/studies'),
  });
  
  if (isLoading) {
    return <div>Loading...</div>;
  }
  
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Study Code</TableHead>
          <TableHead>Name</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Data Source</TableHead>
          <TableHead>Last Updated</TableHead>
          <TableHead className="w-[100px]">Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {studies?.data.map((study: any) => (
          <TableRow key={study.id}>
            <TableCell className="font-medium">{study.study_code}</TableCell>
            <TableCell>{study.name}</TableCell>
            <TableCell>
              <Badge
                variant={study.status === 'active' ? 'default' : 'secondary'}
              >
                {study.status}
              </Badge>
            </TableCell>
            <TableCell>{study.data_source_config?.type || 'Not configured'}</TableCell>
            <TableCell>{new Date(study.updated_at).toLocaleDateString()}</TableCell>
            <TableCell>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" className="h-8 w-8 p-0">
                    <MoreHorizontal className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem asChild>
                    <Link href={`/admin/studies/${study.id}/configuration`}>
                      <Settings className="mr-2 h-4 w-4" />
                      Configure
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <Link href={`/admin/studies/${study.id}/dashboard/builder`}>
                      <BarChart className="mr-2 h-4 w-4" />
                      Dashboard Builder
                    </Link>
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
```

### Deliverables - Phase 7
- [ ] Admin panel layout
- [ ] Study management interface
- [ ] User management
- [ ] Activity monitoring
- [ ] Platform admin panel

## Phase 8: Testing & Security (Week 15-16)

> **Compliance Focus**: Implementation includes 21 CFR Part 11 and HIPAA compliance requirements

### Task 8.1: Testing Infrastructure

```python
# backend/tests/test_pipeline.py
import pytest
from httpx import AsyncClient
from sqlmodel import Session

from app.models import Study, Organization
from app.clinical_modules.data_pipeline import PipelineExecutor

@pytest.mark.asyncio
async def test_pipeline_execution(
    client: AsyncClient,
    db: Session,
    test_study: Study
):
    """Test complete pipeline execution"""
    
    # Configure pipeline
    test_study.pipeline_config = {
        "layer1_script": """
import pandas as pd
data = {'USUBJID': ['001', '002'], 'AGE': [45, 52]}
df = pd.DataFrame(data)
save_parquet(df, f"{study_path}/source_data/{run_date}/DM.parquet")
        """,
        "layer2_scripts": ["ADSL.py"]
    }
    db.commit()
    
    # Execute pipeline
    response = await client.post(
        f"/api/v1/studies/{test_study.id}/pipeline/execute",
        json={"run_date": "01JAN2024"}
    )
    
    assert response.status_code == 200
    assert response.json()["status"] == "queued"
    
    # Wait for execution
    task_id = response.json()["task_id"]
    
    # Check result
    result = await client.get(f"/api/v1/tasks/{task_id}")
    assert result.json()["state"] == "SUCCESS"

@pytest.mark.asyncio
async def test_configuration_inheritance(
    client: AsyncClient,
    db: Session,
    test_org: Organization,
    test_study: Study
):
    """Test configuration inheritance"""
    
    # Set org config
    test_org.config = {
        "theme": {"primary_color": "#0066CC"}
    }
    
    # Set study config
    test_study.dashboard_config = {
        "theme": {"secondary_color": "#666666"}
    }
    
    db.commit()
    
    # Get effective config
    response = await client.get(
        f"/api/v1/studies/{test_study.id}/configuration"
    )
    
    config = response.json()
    assert config["theme"]["primary_color"] == "#0066CC"
    assert config["theme"]["secondary_color"] == "#666666"
```

### Task 8.2: Security Implementation

```python
# backend/app/core/security_extensions.py
from typing import Optional, List
from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models import User, Study, Organization

class PermissionChecker:
    """Check user permissions for resources"""
    
    @staticmethod
    async def check_study_access(
        user: User,
        study_id: str,
        required_permission: str,
        db: Session
    ) -> bool:
        """Check if user has access to study"""
        
        # Superusers have all access
        if user.is_superuser:
            return True
        
        # Get study
        stmt = select(Study).where(Study.id == study_id)
        study = await db.exec(stmt).first()
        
        if not study:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Study not found"
            )
        
        # Check organization match
        if study.org_id != user.org_id:
            return False
        
        # Check specific permission
        user_permissions = user.permissions or {}
        study_permissions = user_permissions.get(f"study:{study_id}", [])
        
        return required_permission in study_permissions
    
    @staticmethod
    async def check_org_admin(user: User) -> bool:
        """Check if user is organization admin"""
        return user.is_superuser or "org_admin" in (user.roles or [])

# backend/app/api/deps_extended.py
from typing import Annotated
from fastapi import Depends, HTTPException, status

from app.api.deps import get_current_active_user
from app.core.security_extensions import PermissionChecker
from app.models import User

async def require_study_read(
    study_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)]
) -> User:
    """Require read permission for study"""
    
    has_access = await PermissionChecker.check_study_access(
        user=current_user,
        study_id=study_id,
        required_permission="read",
        db=db
    )
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return current_user
```

### Task 8.3: 21 CFR Part 11 & HIPAA Compliance

```python
# backend/app/core/compliance.py
from typing import Dict, Any, Optional
from datetime import datetime
from cryptography.fernet import Fernet
import hashlib
import json

class ComplianceManager:
    """Manages 21 CFR Part 11 and HIPAA compliance requirements"""
    
    def __init__(self, encryption_key: bytes):
        self.cipher = Fernet(encryption_key)
    
    # 21 CFR Part 11 - Electronic Signatures
    async def create_electronic_signature(
        self, 
        user_id: str, 
        action: str, 
        document_id: str,
        reason: str,
        password: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Create electronic signature for critical actions"""
        # Verify user password
        user = await db.get(User, user_id)
        if not verify_password(password, user.hashed_password):
            raise HTTPException(401, "Invalid password for signature")
        
        # Create signature record
        signature = ElectronicSignature(
            user_id=user_id,
            full_name=user.full_name,
            action=action,
            document_id=document_id,
            reason=reason,
            timestamp=datetime.utcnow(),
            ip_address=request.client.host,
            signature_hash=hashlib.sha256(
                f"{user_id}{action}{document_id}{timestamp}".encode()
            ).hexdigest()
        )
        
        db.add(signature)
        await db.commit()
        
        return signature.dict()
    
    # HIPAA - PHI Encryption
    def encrypt_phi(self, data: str) -> str:
        """Encrypt Protected Health Information"""
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt_phi(self, encrypted_data: str) -> str:
        """Decrypt Protected Health Information"""
        return self.cipher.decrypt(encrypted_data.encode()).decode()
    
    # Audit Trail for 21 CFR Part 11
    async def create_audit_record(
        self,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        old_value: Optional[Dict] = None,
        new_value: Optional[Dict] = None,
        reason: Optional[str] = None,
        db: AsyncSession = None
    ):
        """Create comprehensive audit trail record"""
        audit = AuditLog(
            user_id=user_id,
            timestamp=datetime.utcnow(),
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            old_value=json.dumps(old_value) if old_value else None,
            new_value=json.dumps(new_value) if new_value else None,
            reason=reason,
            # Computer-generated, time-stamped audit trail
            system_timestamp=datetime.utcnow(),
            sequence_number=await self._get_next_sequence_number(db)
        )
        
        db.add(audit)
        await db.commit()

# backend/app/models/compliance.py
class ElectronicSignature(SQLModel, table=True):
    """21 CFR Part 11 compliant electronic signature"""
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id")
    full_name: str  # Name at time of signature
    action: str  # What was signed
    document_id: str  # What document/record
    reason: str  # Why it was signed
    timestamp: datetime
    ip_address: str
    signature_hash: str  # Cryptographic hash
    
    # Ensure signatures cannot be modified
    __table_args__ = (
        Index("idx_signature_immutable", "id", "signature_hash"),
    )

# backend/app/core/hipaa_middleware.py
class HIPAALoggingMiddleware:
    """Log all PHI access for HIPAA compliance"""
    
    async def __call__(self, request: Request, call_next):
        # Log PHI access
        if self._is_phi_endpoint(request.url.path):
            await self._log_phi_access(
                user_id=request.state.user.id if hasattr(request.state, 'user') else None,
                endpoint=request.url.path,
                method=request.method,
                ip_address=request.client.host
            )
        
        response = await call_next(request)
        return response
```

### Deliverables - Phase 8
- [ ] Unit tests for all modules
- [ ] Integration tests
- [ ] Security implementation with RBAC
- [ ] Performance tests
- [ ] API security and rate limiting
- [ ] 21 CFR Part 11 compliance (audit trail, e-signatures)
- [ ] HIPAA compliance (PHI encryption, access logging)

## Phase 9: Deployment & CI/CD (Week 17-18)

> **Cloud-Agnostic Deployment**: Designed to run on AWS, Azure, or standalone Linux VMs without cloud-specific dependencies

### Task 9.1: Docker Configuration

```dockerfile
# backend/Dockerfile.production
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY ./app ./app
COPY ./alembic ./alembic
COPY ./alembic.ini .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Docker Build Optimization

> **Important**: The production docker-compose file has been optimized to build the backend image only once and reuse it across multiple services.

When using `make restart-all-prod`:
- The command uses `requirements-prod.txt` for production dependencies
- The backend Dockerfile specifically installs from `requirements-prod.txt`
- The backend image is built once with tag `cortex-backend:prod` and reused by:
  - `prestart` service (database migrations)
  - `backend` service (API server)
  - `celery-worker` service (background tasks)
  - `celery-beat` service (scheduled tasks)

This optimization reduces build time from ~4x to 1x the backend build duration.

### Task 9.2: CI/CD Pipeline

```yaml
# .github/workflows/deploy.yml
name: Deploy to Client

on:
  workflow_dispatch:
    inputs:
      client:
        description: 'Client to deploy to'
        required: true
        type: choice
        options:
          - pharmcorp
          - biotech-inc
          - medical-research
      environment:
        description: 'Environment'
        required: true
        type: choice
        options:
          - staging
          - production

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: ${{ github.event.inputs.environment }}
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Login to ECR
        uses: aws-actions/amazon-ecr-login@v1
      
      - name: Build and push images
        run: |
          # Build images
          docker build -t clinical-dashboard-backend:${{ github.sha }} -f backend/Dockerfile.production ./backend
          docker build -t clinical-dashboard-frontend:${{ github.sha }} -f frontend/Dockerfile.production ./frontend
          
          # Tag and push
          docker tag clinical-dashboard-backend:${{ github.sha }} $ECR_REGISTRY/clinical-dashboard-backend:${{ github.sha }}
          docker tag clinical-dashboard-frontend:${{ github.sha }} $ECR_REGISTRY/clinical-dashboard-frontend:${{ github.sha }}
          
          docker push $ECR_REGISTRY/clinical-dashboard-backend:${{ github.sha }}
          docker push $ECR_REGISTRY/clinical-dashboard-frontend:${{ github.sha }}
      
      - name: Deploy to client
        run: |
          # Run deployment script
          ./deployment/scripts/deploy.sh \
            --client ${{ github.event.inputs.client }} \
            --environment ${{ github.event.inputs.environment }} \
            --version ${{ github.sha }}
```

### Task 9.3: Infrastructure as Code

```hcl
# deployment/terraform/client-infrastructure/main.tf
variable "client_name" {
  description = "Client identifier"
  type        = string
}

variable "environment" {
  description = "Environment (staging/production)"
  type        = string
}

resource "aws_instance" "app_server" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = var.environment == "production" ? "t3.xlarge" : "t3.large"
  
  vpc_security_group_ids = [aws_security_group.app.id]
  subnet_id              = aws_subnet.private.id
  
  root_block_device {
    volume_size = 100
    volume_type = "gp3"
    encrypted   = true
  }
  
  user_data = templatefile("${path.module}/user_data.sh", {
    client_name = var.client_name
    environment = var.environment
  })
  
  tags = {
    Name        = "clinical-dashboard-${var.client_name}-${var.environment}"
    Client      = var.client_name
    Environment = var.environment
    Application = "clinical-dashboard"
  }
}

resource "aws_db_instance" "postgres" {
  identifier = "clinical-dashboard-${var.client_name}-${var.environment}"
  
  engine         = "postgres"
  engine_version = "15.3"
  instance_class = var.environment == "production" ? "db.r6g.xlarge" : "db.t3.medium"
  
  allocated_storage     = 100
  max_allocated_storage = 1000
  storage_encrypted     = true
  
  db_name  = "clinical_dashboard"
  username = "dbadmin"
  password = random_password.db_password.result
  
  vpc_security_group_ids = [aws_security_group.db.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
  
  backup_retention_period = var.environment == "production" ? 30 : 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  tags = {
    Client      = var.client_name
    Environment = var.environment
  }
}
```

### Deliverables - Phase 9
- [ ] Production Docker images
- [ ] CI/CD pipelines with multi-client support
- [ ] Infrastructure as Code
- [ ] Deployment documentation
- [ ] Blue-green deployment strategy

## Troubleshooting Guide

### Common Issues and Solutions

#### Issue 1: Database Connection Errors
```bash
# Check PostgreSQL status
docker-compose ps postgres

# View logs
docker-compose logs postgres

# Test connection
docker-compose exec backend python -c "from app.core.db import engine; print(engine)"
```

#### Issue 2: Redis Connection Issues
```bash
# Check Redis status
docker-compose exec redis redis-cli ping

# Clear Redis cache
docker-compose exec redis redis-cli FLUSHALL
```

#### Issue 3: Frontend Build Errors
```bash
# Clear Next.js cache
rm -rf frontend/.next
rm -rf frontend/node_modules/.cache

# Reinstall dependencies
cd frontend && npm ci
```

#### Issue 4: Celery Task Failures
```bash
# Monitor Celery workers
docker-compose logs -f celery_worker

# Inspect task queue
docker-compose exec backend celery -A app.workers.celery_app inspect active

# Purge task queue
docker-compose exec backend celery -A app.workers.celery_app purge
```

## Best Practices

### 1. Code Organization
- Keep clinical modules separate from core application
- Use dependency injection for services
- Implement proper error handling and logging

### 2. Configuration Management
- Store sensitive data in environment variables
- Use configuration schemas for validation
- Implement proper configuration inheritance

### 3. Security
- Always validate user permissions
- Encrypt sensitive data at rest and in transit
- Implement proper audit logging
- Regular security updates

### 4. Performance
- Use database indexes for common queries
- Implement caching for expensive operations
- Use pagination for large datasets
- Monitor query performance

### 5. Testing
- Write tests for critical business logic
- Use fixtures for test data
- Mock external services in tests
- Run tests in CI/CD pipeline

### 6. Deployment
- Use blue-green deployments for zero downtime
- Implement proper health checks
- Monitor application metrics
- Have rollback procedures ready

## Widget System Implementation

### Overview
The widget system has been completely redesigned to support ANY data format (not limited to SDTM/ADaM) with a flexible, schema-agnostic approach.

### Key Components Implemented

#### Phase 1: Widget Model & Display ✓
- Removed all SDTM/ADaM constraints from Widget model
- Created flexible data contract system with JSON schema
- Built MetricCard widget component with dynamic field mapping
- Implemented widget API endpoints for CRUD operations

#### Phase 2: Data Source Management ✓
- Unified folder structure: `/data/studies/{org_id}/{study_id}/source_data/{YYYYMMDD_HHMMSS}/`
- Automatic parquet conversion for all file types (CSV, SAS7BDAT, XPT, XLSX)
- Version management system with activation/rollback
- Support for manual upload, API, and sFTP data sources

#### Phase 3: Pipeline & Transformation System ✓
- Secure Python script execution with sandboxing
- Resource limits (memory, CPU, execution time)
- Pipeline versioning and rollback capabilities
- Built-in safe modules (pandas, numpy, scipy)

#### Phase 4: Data Mapping Interface ✓
- Field mapping configuration with AI-powered suggestions (fuzzywuzzy)
- Preview and validation for mappings
- Study initialization wizard
- Template system for reusable mappings

### Files Created/Modified
- `/backend/app/models/widget.py` - Flexible widget model
- `/backend/app/models/data_source.py` - Data source management
- `/backend/app/models/pipeline.py` - Pipeline execution models
- `/backend/app/models/data_mapping.py` - Field mapping configuration
- `/backend/app/clinical_modules/utils/folder_structure.py` - Unified path management
- `/backend/app/clinical_modules/pipeline/script_executor.py` - Secure script execution
- `/frontend/src/components/widgets/MetricWidget.tsx` - Display component
- `/frontend/src/components/data-mapping/FieldMappingBuilder.tsx` - Mapping UI

## Completion Checklist

### Phase 1-2: Foundation ✓
- [x] Project setup from template
- [x] Database schema implementation
- [x] RBAC system with roles and permissions
- [x] Multi-tenant architecture
- [x] Basic API structure with authentication
- [x] Platform admin infrastructure

### Phase 3: Data Pipeline ✓
- [x] Data source integrations (Manual upload completed, API/sFTP structure ready)
- [x] Asynchronous pipeline executor with secure sandboxing
- [x] Pipeline versioning and rollback
- [x] Transformation script system

### Widget System Implementation ✓
- [x] Flexible widget model (removed SDTM/ADaM constraints)
- [x] Data source management with parquet conversion
- [x] Unified folder structure for all data sources
- [x] Version management system
- [x] Secure Python script execution
- [x] Field mapping with AI suggestions
- [x] Widget data mapping interface
- [x] Study initialization wizard
- [ ] Non-blocking task queue with Celery
- [ ] Real-time progress tracking
- [ ] Pipeline monitoring and status API

### Phase 4: Export & Reporting ✓
- [ ] PDF/PowerPoint/Excel export engine
- [ ] Scheduled report system
- [ ] Email integration
- [ ] Report templates
- [ ] Export API endpoints

### Phase 5: Configuration System ✓
- [ ] Configuration schema and validation
- [ ] Configuration inheritance (global → client → study)
- [ ] Public API for external integrations
- [ ] API key management
- [ ] Rate limiting and quotas

### Phase 6: Dashboard Builder ✓
- [ ] Widget system architecture
- [ ] Dynamic dashboard rendering
- [ ] Visual dashboard builder
- [ ] Widget library

### Phase 7: Admin Panel ✓
- [ ] Organization admin panel
- [ ] Platform super admin panel
- [ ] User and role management
- [ ] Study configuration UI
- [ ] API key management UI

### Phase 8: Testing & Security ✓
- [ ] Comprehensive test suite
- [ ] RBAC implementation
- [ ] API security
- [ ] Performance optimization
- [ ] Security audit

### Phase 9: Production Deployment ✓
- [ ] Multi-client Docker deployment
- [ ] CI/CD with GitOps
- [ ] Blue-green deployments
- [ ] Infrastructure as Code
- [ ] Monitoring and alerting

### Final Steps
- [ ] User documentation
- [ ] API documentation with OpenAPI
- [ ] Deployment guide
- [ ] Training materials
- [ ] SDK generation for multiple languages

## Support Resources

- **Documentation**: `/docs` directory
- **API Reference**: `http://localhost:8000/docs`
- **Issue Tracking**: GitHub Issues
- **Community**: Slack channel

---

## Key Implementation Updates

Based on project requirements, the following critical updates have been incorporated:

**Data Architecture**:
- Raw data from EDC systems (primarily Medidata Rave) stored as immutable records
- Analysis data derived from complex transformations on multiple source datasets
- Storage designed to scale from MB to GB per study extract
- Hybrid approach: PostgreSQL for metadata, Parquet files for clinical data

**Compliance & Security**:
- **21 CFR Part 11**: Complete audit trail, electronic signatures, access controls, data integrity
- **HIPAA**: PHI encryption at rest and in transit, access logging, secure data handling
- Folder permissions automatically set for compliance (raw data becomes read-only after upload)

**Priority Integrations**:
- **Medidata Rave API**: Primary data source integration
- **ZIP File Upload**: Manual data upload with automatic extraction and validation
- Future extensibility for other EDC systems

**Infrastructure**:
- **Cloud-Agnostic**: Deployable on AWS, Azure, or standalone Linux VMs
- No cloud-specific service dependencies (uses standard PostgreSQL, Redis, Docker)
- Designed for 10-40 concurrent users per tenant

**Data Transformation**:
- Maximum flexibility with two-layer approach
- DSL for standard transformations
- Full Python execution in Docker containers for complex scripts
- Support for custom libraries and Git integration

This implementation guide provides a comprehensive roadmap for building your enterprise clinical dashboard platform with all critical features. Follow each phase systematically, and you'll have a production-ready system in 18 weeks.

**Timeline Summary**:
- **Weeks 1-2**: Foundation and setup
- **Weeks 3-4**: Core infrastructure with RBAC
- **Weeks 5-6**: Asynchronous data pipeline
- **Weeks 7-8**: Export and reporting system
- **Weeks 9-10**: Configuration engine
- **Weeks 11-12**: Dashboard builder
- **Weeks 13-14**: Admin panels
- **Weeks 15-16**: Testing and security
- **Weeks 17-18**: Deployment and go-live

---

## Completed Tasks

### Dashboard Template System (Completed)
- ✅ Fixed dashboard template API to show correct counts
- ✅ Updated template structure to support single dashboard with multiple views
- ✅ Fixed TypeScript errors with StudyStatus enum
- ✅ Fixed data mapping step in study initialization
- ✅ Added data source configuration step to wizard

### Widget System Architecture (Completed)
- ✅ Analyzed old codebase to understand widget data flow
- ✅ Created comprehensive widget architecture documentation
- ✅ Implemented widget data requirements schema
- ✅ Created seed data script for widget library with 11 standard widgets:
  - Metric widgets: Total Screened, Screen Failures, Total AEs, SAEs
  - Chart widgets: Enrollment Trend, AE Timeline
  - Table widgets: Site Summary Table, Subject Listing
  - Map widgets: Site Enrollment Map
  - Flow diagrams: Subject Flow Diagram
- ✅ Created proof-of-concept MetricWidget component
- ✅ Implemented useWidgetData hook for data fetching
- ✅ Created WidgetRenderer component for dynamic widget rendering

### Key Files Created/Updated
- `/backend/app/db/seed_widgets.py` - Widget library seed data
- `/backend/app/cli/seed_widgets_command.py` - CLI command for seeding widgets
- `/frontend/src/components/widgets/MetricWidget.tsx` - Metric widget component
- `/frontend/src/hooks/useWidgetData.ts` - Widget data fetching hook
- `/frontend/src/components/widgets/WidgetRenderer.tsx` - Dynamic widget renderer
- `/implementation/widget-architecture-findings.md` - Architecture documentation

## Widget System Implementation (Phase 1-4 Completed)

### Phase 1: Widget Library (Completed ✅)
- **Removed SDTM/ADaM constraints** - Widget models now support ANY data format
- **Created flexible data contract** - JSON schema for widget data requirements
- **Built MetricCard widget** - First widget type with value/label/trend display
- **Implemented widget API endpoints** - CRUD operations for widget management

### Phase 2: Data Source Management (Completed ✅)
- **File Upload System**:
  - Support for CSV, SAS7BDAT, XPT, XLSX, ZIP files
  - Automatic conversion to Parquet format
  - Progress tracking and error handling
  
- **Unified Folder Structure**:
  ```
  /data/studies/{org_id}/{study_id}/source_data/{YYYYMMDD_HHMMSS}/
  ```
  - Same structure for manual uploads, API sync, and sFTP
  - Version tracking with timestamp folders
  
- **Version Management**:
  - Multiple versions per study
  - Version activation/rollback
  - Version comparison UI
  - Dataset and column-level diff view

### Phase 3: Data Pipeline System (Completed ✅)
- **Pipeline Configuration Model**:
  - Version-controlled pipeline configurations
  - Support for multiple transformation types
  - Schedule support (cron expressions)
  
- **Transformation Script Executor**:
  - Secure Python script execution with sandboxing
  - Resource limits (memory, CPU, time)
  - Allowed imports whitelist
  - Built-in transformation types (filter, aggregate, pivot)
  
- **Pipeline Management UI**:
  - Visual pipeline builder
  - Drag-and-drop transformation steps
  - Script editor with syntax validation
  - Real-time execution monitoring
  - Step-by-step execution logs

### Phase 4: Widget Data Mapping (In Progress 🚧)
- **Data Mapping Models** (Completed ✅):
  - Field mapping configuration
  - Study data configuration
  - Mapping templates
  
- **Mapping Service** (Completed ✅):
  - Automatic field suggestions using fuzzy matching
  - Data type compatibility checking
  - Mapping validation with coverage metrics
  
- **Next Steps**:
  - [ ] Build field mapping UI component
  - [ ] Implement mapping preview/validation UI
  - [ ] Create study initialization wizard

### Files Created in Widget System Implementation

**Backend:**
- `/backend/app/models/widget.py` - Updated widget models without SDTM constraints
- `/backend/app/models/data_source.py` - Data source and upload models
- `/backend/app/models/pipeline.py` - Pipeline configuration models
- `/backend/app/models/data_mapping.py` - Widget data mapping models
- `/backend/app/api/v1/endpoints/data_uploads.py` - File upload endpoints
- `/backend/app/api/v1/endpoints/pipeline_config.py` - Pipeline management endpoints
- `/backend/app/clinical_modules/data_sources/file_converter.py` - File conversion service
- `/backend/app/clinical_modules/pipeline/script_executor.py` - Secure script execution
- `/backend/app/clinical_modules/pipeline/pipeline_service.py` - Pipeline orchestration
- `/backend/app/clinical_modules/mapping/mapping_service.py` - Data mapping service

**Frontend:**
- `/frontend/src/components/data-sources/DataSourceManager.tsx` - Upload management UI
- `/frontend/src/components/data-sources/DataSourceUpload.tsx` - Upload dialog
- `/frontend/src/components/data-sources/VersionSwitcher.tsx` - Version switching UI
- `/frontend/src/components/data-sources/VersionComparison.tsx` - Version diff view
- `/frontend/src/components/pipelines/PipelineManager.tsx` - Pipeline list/execution
- `/frontend/src/components/pipelines/PipelineBuilder.tsx` - Visual pipeline builder
- `/frontend/src/components/pipelines/ScriptEditor.tsx` - Python script editor
- `/frontend/src/components/pipelines/FilterBuilder.tsx` - Filter condition builder
- `/frontend/src/components/pipelines/PipelineExecutionDetails.tsx` - Execution monitoring
- `/frontend/src/lib/api/data-uploads.ts` - Data upload API client
- `/frontend/src/lib/api/pipelines.ts` - Pipeline API client

### Architecture Decisions

1. **Data Format Flexibility**: Removed all SDTM/ADaM constraints to support any data format
2. **Parquet as Internal Format**: All uploaded files converted to Parquet for performance
3. **Version Control Everything**: Data uploads, pipelines, and mappings all versioned
4. **Security First**: Sandboxed script execution with resource limits
5. **Real-time Monitoring**: WebSocket/polling for pipeline execution progress
6. **Fuzzy Matching**: Smart field suggestions for data mapping

## Dashboard Template System Updates (Completed ✅)

### Unified Dashboard Template Architecture
- **Menu and Dashboard Integration**: Menu templates and dashboard templates have been unified into a single "Dashboard Template" system
- **Single Source of Truth**: All navigation and dashboard configurations are now stored in the `dashboard_templates` table
- **Backward Compatibility**: Menu endpoints marked as deprecated with warnings, will be removed in v2.0

### Changes Made:
1. **Frontend Updates**:
   - ✅ Removed separate menu templates UI from admin page
   - ✅ Removed `/admin/menus` route and components
   - ✅ Updated sidebar navigation to remove menu templates
   - ✅ Updated `use-study-menu` hook to fetch menus from dashboard templates

2. **Backend Updates**:
   - ✅ Marked all menu endpoints as deprecated with `deprecated=True` flag
   - ✅ Added deprecation warnings to `/api/v1/admin/menus` endpoints
   - ✅ Menu functionality now part of `template_structure` in dashboard templates

3. **Data Model**:
   ```python
   # Dashboard template now includes menu structure
   template_structure = {
       "menu": {
           "items": [
               {
                   "id": "overview",
                   "type": "dashboard_page",
                   "label": "Overview",
                   "icon": "LayoutDashboard",
                   "dashboard": {
                       "layout": {...},
                       "widgets": [...]
                   }
               }
           ]
       }
   }
   ```

### Migration Path:
- Existing menu templates continue to work through the deprecated endpoints
- New templates should use the unified dashboard template structure
- Menu endpoints will be removed in version 2.0