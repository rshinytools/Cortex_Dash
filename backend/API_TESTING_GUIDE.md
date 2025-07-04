# API Testing Guide for Clinical Dashboard Platform

## 🚀 Quick Start

### 1. Prerequisites

Before testing the APIs, ensure you have:

1. **PostgreSQL** running locally
2. **Redis** running locally (for Celery tasks)
3. **Python environment** set up

### 2. Environment Setup

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up the database
createdb clinical_dashboard

# Run migrations
alembic upgrade head

# Start the FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# In another terminal, start Celery worker (optional, for async tasks)
celery -A app.core.celery_app worker --loglevel=info

# In another terminal, start Celery beat (optional, for scheduled tasks)
celery -A app.core.celery_app beat --loglevel=info
```

## 📚 API Documentation

Once the server is running, you can access:

- **Interactive API Docs (Swagger)**: http://localhost:8000/docs
- **Alternative API Docs (ReDoc)**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## 🧪 Testing Methods

### Method 1: Using FastAPI's Interactive Docs (Recommended)

1. Go to http://localhost:8000/docs
2. Click on any endpoint to expand it
3. Click "Try it out"
4. Fill in the required parameters
5. Click "Execute"

### Method 2: Using cURL

```bash
# Login to get access token
curl -X POST "http://localhost:8000/api/v1/login/access-token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=changethis"

# Use the token for authenticated requests
export TOKEN="your_access_token_here"

# Example: Get organizations
curl -X GET "http://localhost:8000/api/v1/organizations" \
  -H "Authorization: Bearer $TOKEN"
```

### Method 3: Using Python Requests

```python
import requests

# Base URL
BASE_URL = "http://localhost:8000/api/v1"

# Login
response = requests.post(
    f"{BASE_URL}/login/access-token",
    data={"username": "admin@example.com", "password": "changethis"}
)
token = response.json()["access_token"]

# Make authenticated requests
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(f"{BASE_URL}/organizations", headers=headers)
print(response.json())
```

### Method 4: Using Postman

1. Download and install [Postman](https://www.postman.com/)
2. Import the OpenAPI schema from http://localhost:8000/openapi.json
3. Set up environment variables for the base URL and token
4. Test endpoints interactively

## 🔑 Authentication Flow

### 1. Initial Login

```bash
# Get access token
POST /api/v1/login/access-token
Content-Type: application/x-www-form-urlencoded

username=admin@example.com
password=changethis
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

### 2. Use Token in Requests

Add the token to the Authorization header:
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

## 📋 API Testing Sequence

### Step 1: Create an Organization (System Admin Only)

```bash
POST /api/v1/organizations
Authorization: Bearer $TOKEN
Content-Type: application/json

{
  "name": "Pharma Corp",
  "slug": "pharma-corp",
  "license_type": "enterprise",
  "max_users": 50,
  "max_studies": 20
}
```

### Step 2: Create a User

```bash
POST /api/v1/v1/users
Authorization: Bearer $TOKEN
Content-Type: application/json

{
  "email": "study.manager@pharmarcorp.com",
  "password": "securePassword123!",
  "full_name": "Study Manager",
  "role": "study_manager",
  "org_id": "organization_id_from_step_1"
}
```

### Step 3: Create a Study

```bash
POST /api/v1/studies
Authorization: Bearer $TOKEN
Content-Type: application/json

{
  "org_id": "organization_id_from_step_1",
  "name": "COVID-19 Vaccine Trial",
  "protocol_number": "COV-2023-001",
  "description": "Phase 3 clinical trial",
  "status": "active"
}
```

### Step 4: Create a Data Source

```bash
POST /api/v1/studies/{study_id}/data-sources
Authorization: Bearer $TOKEN
Content-Type: application/json

{
  "name": "Medidata Rave Production",
  "type": "medidata_rave",
  "config": {
    "base_url": "https://your-rave-instance.mdsol.com",
    "username": "api_user",
    "password": "api_password",
    "study_oid": "STUDY-001",
    "environment": "PROD"
  }
}
```

### Step 5: Test Data Source Connection

```bash
POST /api/v1/pipelines/data-sources/{data_source_id}/test
Authorization: Bearer $TOKEN
```

### Step 6: Execute Pipeline

```bash
POST /api/v1/pipelines/studies/{study_id}/pipeline/execute
Authorization: Bearer $TOKEN
Content-Type: application/json

{
  "data_sources": ["data_source_id"],
  "transformations": [
    {
      "name": "Standardize Demographics",
      "type": "standardize",
      "column_mapping": {
        "SUBJID": "subject_id",
        "AGE": "age",
        "SEX": "gender"
      }
    }
  ]
}
```

### Step 7: Check Pipeline Status

```bash
GET /api/v1/pipelines/pipeline/status/{task_id}
Authorization: Bearer $TOKEN
```

## 🎭 Testing Different User Roles

### 1. System Admin
- Can access all endpoints
- Can create organizations
- Can manage all users

### 2. Organization Admin
- Can manage their organization
- Can create studies
- Can manage users in their org

### 3. Study Manager
- Can manage studies
- Can configure pipelines
- Can view reports

### 4. Data Manager
- Can sync data sources
- Can execute pipelines
- Can export data

### 5. Analyst
- Can view dashboards
- Can create reports
- Can export data

### 6. Viewer
- Can only view dashboards and reports

## 🛠️ Troubleshooting

### Common Issues

1. **Database Connection Error**
   ```bash
   # Check PostgreSQL is running
   psql -U postgres -c "SELECT 1"
   
   # Create database if needed
   createdb clinical_dashboard
   ```

2. **Redis Connection Error**
   ```bash
   # Start Redis
   redis-server
   
   # Test Redis connection
   redis-cli ping
   ```

3. **Migration Issues**
   ```bash
   # Reset database (CAUTION: This deletes all data)
   dropdb clinical_dashboard
   createdb clinical_dashboard
   alembic upgrade head
   ```

4. **Permission Denied Errors**
   - Ensure you're using the correct role
   - Check the token hasn't expired
   - Verify user has required permissions

## 📊 Sample Test Data Script

Create a file `test_data.py`:

```python
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def login(email, password):
    response = requests.post(
        f"{BASE_URL}/login/access-token",
        data={"username": email, "password": password}
    )
    return response.json()["access_token"]

def create_test_data():
    # Login as superuser
    token = login("admin@example.com", "changethis")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create organization
    org_response = requests.post(
        f"{BASE_URL}/organizations",
        headers=headers,
        json={
            "name": "Test Pharma",
            "slug": "test-pharma",
            "license_type": "enterprise",
            "max_users": 100,
            "max_studies": 50
        }
    )
    org_id = org_response.json()["id"]
    print(f"Created organization: {org_id}")
    
    # Create users
    users = [
        {"email": "org.admin@test.com", "role": "org_admin", "full_name": "Org Admin"},
        {"email": "study.manager@test.com", "role": "study_manager", "full_name": "Study Manager"},
        {"email": "data.manager@test.com", "role": "data_manager", "full_name": "Data Manager"},
        {"email": "analyst@test.com", "role": "analyst", "full_name": "Analyst"},
        {"email": "viewer@test.com", "role": "viewer", "full_name": "Viewer"}
    ]
    
    for user in users:
        user_response = requests.post(
            f"{BASE_URL}/v1/users",
            headers=headers,
            json={
                **user,
                "password": "TestPass123!",
                "org_id": org_id
            }
        )
        print(f"Created user: {user['email']}")
    
    # Create study
    study_response = requests.post(
        f"{BASE_URL}/studies",
        headers=headers,
        json={
            "org_id": org_id,
            "name": "Test Study 001",
            "protocol_number": "TEST-001",
            "description": "Test clinical study",
            "status": "active"
        }
    )
    study_id = study_response.json()["id"]
    print(f"Created study: {study_id}")
    
    print("\nTest data created successfully!")
    print(f"Organization ID: {org_id}")
    print(f"Study ID: {study_id}")

if __name__ == "__main__":
    create_test_data()
```

## 🔒 Security Testing

### Test Authentication
```bash
# Test without token (should fail)
curl -X GET "http://localhost:8000/api/v1/organizations"

# Test with invalid token (should fail)
curl -X GET "http://localhost:8000/api/v1/organizations" \
  -H "Authorization: Bearer invalid_token"

# Test with expired token (should fail)
# Use a token from a previous session
```

### Test RBAC Permissions
```bash
# Login as viewer
TOKEN=$(curl -X POST "http://localhost:8000/api/v1/login/access-token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=viewer@test.com&password=TestPass123!" | jq -r .access_token)

# Try to create a study (should fail - insufficient permissions)
curl -X POST "http://localhost:8000/api/v1/studies" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Unauthorized Study", "protocol_number": "UNAUTH-001"}'
```

## 🚦 Health Check

```bash
# Basic health check
curl http://localhost:8000/health

# API version
curl http://localhost:8000/api/v1
```

## 📝 Activity Logs

All API operations are logged. To view activity logs:

```bash
GET /api/v1/activity-logs?limit=50
Authorization: Bearer $TOKEN
```

## 🔄 Async Task Monitoring

For long-running operations (pipelines, data sync):

1. The API returns a task_id
2. Poll the status endpoint:
   ```bash
   GET /api/v1/pipelines/pipeline/status/{task_id}
   ```
3. Status values: PENDING, PROGRESS, SUCCESS, FAILURE

## 🎯 Next Steps

1. Set up automated API tests using pytest
2. Create a Postman collection for the API
3. Implement API performance testing
4. Set up API monitoring and alerting

---

Happy Testing! 🧪