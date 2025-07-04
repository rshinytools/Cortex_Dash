# Users API Documentation

## Overview
The Users API manages user accounts, authentication, authorization, and role-based access control (RBAC) across the Clinical Dashboard Platform. It ensures secure access to clinical trial data while maintaining compliance with healthcare regulations and data privacy laws.

## Business Purpose

### Why This API Exists
1. **Identity Management**: Centralized user authentication and authorization
2. **Regulatory Compliance**: Enforce access controls required by 21 CFR Part 11 and HIPAA
3. **Multi-Study Access**: Users often work across multiple studies and organizations
4. **Audit Requirements**: Track all user actions for regulatory audits
5. **Training Compliance**: Ensure users have required training before system access

### Key Business Benefits
- **Security**: Strong authentication and granular access control
- **Compliance**: Meets all regulatory requirements for user management
- **Efficiency**: Single sign-on across all platform features
- **Accountability**: Complete audit trail of user actions
- **Flexibility**: Role-based permissions adapt to organizational needs

## API Endpoints

### 1. List Users
```http
GET /api/v1/v1/users
```

**Purpose**: Retrieve paginated list of users with filtering capabilities.

**Business Need**:
- Administrators need to manage user accounts
- Study coordinators need to find team members
- Auditors need to review user access
- HR needs to track active users

**Query Parameters**:
- `org_id`: Filter by organization
- `study_id`: Filter by study access
- `role`: Filter by role
- `status`: active, inactive, locked
- `search`: Search by name or email

**Response Example**:
```json
{
  "items": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "email": "jane.doe@pharmacorp.com",
      "full_name": "Dr. Jane Doe",
      "title": "Principal Investigator",
      "organization": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Pharma Corp International"
      },
      "roles": ["principal_investigator", "study_reviewer"],
      "status": "active",
      "last_login": "2025-01-20T14:30:00Z",
      "created_at": "2023-06-15T10:00:00Z",
      "training_status": {
        "gcp": "completed",
        "protocol_specific": "completed",
        "system_training": "completed"
      },
      "studies_count": 5,
      "mfa_enabled": true,
      "password_last_changed": "2024-11-15T09:00:00Z"
    }
  ],
  "total": 234,
  "page": 1,
  "size": 20
}
```

### 2. Create User
```http
POST /api/v1/v1/users
```

**Purpose**: Create new user account with appropriate roles and permissions.

**Business Need**:
- Onboard new employees
- Grant system access to investigators
- Add external monitors
- Create service accounts for integrations

**Request Body**:
```json
{
  "email": "john.smith@clinicalsite.org",
  "full_name": "Dr. John Smith",
  "title": "Sub-Investigator",
  "phone": "+1-555-0123",
  "org_id": "550e8400-e29b-41d4-a716-446655440000",
  "roles": ["sub_investigator"],
  "sites": ["site_001", "site_002"],
  "credentials": {
    "medical_license": "MD123456",
    "npi_number": "1234567890",
    "cv_date": "2024-12-01"
  },
  "training": {
    "gcp_certificate": "GCP-2024-12345",
    "gcp_expiry": "2026-12-01"
  },
  "notification_preferences": {
    "email_alerts": true,
    "sms_alerts": false,
    "digest_frequency": "daily"
  }
}
```

### 3. Get User Details
```http
GET /api/v1/v1/users/{user_id}
```

**Purpose**: Retrieve comprehensive user information including roles, permissions, and access history.

**Business Need**:
- View user profile information
- Audit user access and permissions
- Verify training compliance
- Review user activity

**Response Includes**:
- Personal information
- Role assignments
- Study access list
- Training records
- Login history
- Audit trail summary

### 4. Update User
```http
PUT /api/v1/v1/users/{user_id}
```

**Purpose**: Update user information, roles, or status.

**Business Need**:
- Update contact information
- Change role assignments
- Modify study access
- Update training records
- Change notification preferences

**Validation Rules**:
- Email changes require verification
- Role changes require appropriate permissions
- Cannot remove last admin from organization
- Training updates require documentation

### 5. Delete User
```http
DELETE /api/v1/v1/users/{user_id}
```

**Purpose**: Deactivate user account (soft delete).

**Business Need**:
- Employee termination
- Remove external user access
- Compliance with data retention
- Security incident response

**Important Notes**:
- User data retained for audit trail
- Active sessions terminated
- Cannot delete users with signed documents
- Reassignment of responsibilities required

### 6. Get User Permissions
```http
GET /api/v1/v1/users/{user_id}/permissions
```

**Purpose**: Retrieve detailed permission matrix for a user.

**Business Need**:
- Verify user access rights
- Troubleshoot permission issues
- Audit access controls
- Plan permission changes

**Response Example**:
```json
{
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "global_permissions": [
    "VIEW_STUDIES",
    "CREATE_REPORTS"
  ],
  "organization_permissions": {
    "550e8400-e29b-41d4-a716-446655440000": [
      "MANAGE_USERS",
      "VIEW_ALL_STUDIES"
    ]
  },
  "study_permissions": {
    "750e8400-e29b-41d4-a716-446655440001": [
      "EDIT_STUDY",
      "VIEW_UNBLINDED_DATA",
      "SIGN_DOCUMENTS"
    ]
  },
  "effective_permissions": [
    "Full list of computed permissions"
  ]
}
```

### 7. Update User Permissions
```http
PUT /api/v1/v1/users/{user_id}/permissions
```

**Purpose**: Modify user permissions and role assignments.

**Business Need**:
- Grant additional access
- Revoke permissions
- Change study roles
- Update organization access

**Audit Requirements**:
- Reason for change required
- Electronic signature for critical permissions
- Notification to user
- Update to delegation log

## Authentication & Security

### Authentication Methods
1. **Username/Password**: With complexity requirements
2. **Multi-Factor Authentication**: Required for privileged users
3. **SSO Integration**: SAML 2.0 / OAuth 2.0
4. **API Keys**: For service accounts
5. **Biometric**: Optional for mobile access

### Password Policy
- Minimum 12 characters
- Complexity requirements enforced
- Password history (last 12)
- Expiration every 90 days
- Account lockout after 5 failed attempts

### Session Management
- JWT tokens with 8-hour expiration
- Refresh tokens for extended sessions
- Concurrent session limits
- Automatic logout on inactivity (30 minutes)
- Session recording for audit

## Role-Based Access Control (RBAC)

### System Roles
1. **Super Admin**: Platform-wide administration
2. **Organization Admin**: Organization-level management
3. **Study Director**: Full study access
4. **Principal Investigator**: Site-level study management
5. **Clinical Research Coordinator**: Data entry and management
6. **Monitor**: Read-only with monitoring tools
7. **Data Manager**: Data access without PHI
8. **Auditor**: Read-only access for audits

### Permission Model
```
User → Roles → Permissions → Resources
         ↓
    Study Roles → Study-Specific Permissions
```

### Dynamic Permissions
- Permissions computed based on:
  - Global roles
  - Organization roles
  - Study-specific roles
  - Site assignments
  - Delegation log entries

## Compliance Features

### 21 CFR Part 11
- **Unique User IDs**: System-enforced uniqueness
- **Password Controls**: Aging, history, complexity
- **Electronic Signatures**: Linked to user account
- **Authority Checks**: Role-based access control
- **Audit Trail**: All user actions logged

### HIPAA Compliance
- **Minimum Necessary**: Users only see required PHI
- **Access Logging**: Every data access recorded
- **Encryption**: Passwords hashed with bcrypt
- **Account Management**: Timely deactivation
- **Training Tracking**: HIPAA training required

### GDPR Compliance
- **Consent Management**: User consent tracking
- **Data Portability**: User data export
- **Right to be Forgotten**: Anonymization process
- **Privacy by Design**: Minimal data collection
- **Cross-border Transfer**: Location tracking

## Training Management

### Required Training
1. **Good Clinical Practice (GCP)**
2. **Protocol-Specific Training**
3. **System Training**
4. **HIPAA Privacy**
5. **Information Security**

### Training Verification
- Certificates uploaded and verified
- Expiration tracking
- Automatic access suspension
- Renewal notifications
- Training history maintained

## Audit Trail

### Logged Events
- Login/Logout
- Password changes
- Permission changes
- Failed login attempts
- Data access
- Report generation
- Export activities
- Configuration changes

### Audit Record Format
```json
{
  "event_id": "evt_123456",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "event_type": "LOGIN",
  "timestamp": "2025-01-21T10:30:00Z",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "details": {
    "authentication_method": "password+mfa",
    "session_id": "sess_789012"
  },
  "result": "success"
}
```

## Integration Points

### External Systems
1. **Active Directory/LDAP**: User synchronization
2. **Single Sign-On**: SAML/OAuth providers
3. **HR Systems**: Employee data sync
4. **Training Systems**: Completion tracking
5. **Email System**: Notifications

### Internal Dependencies
1. **Organizations API**: User belongs to organization
2. **Studies API**: Study access management
3. **Audit Trail API**: Activity logging
4. **Notification API**: User alerts
5. **Permission API**: Access control

## Performance & Scalability

### Optimization Strategies
- User list pagination (max 100 per page)
- Permission caching (5-minute TTL)
- Indexed on email, organization, status
- Async processing for bulk operations
- Read replicas for user queries

### Capacity Planning
- Supports 100,000+ users
- 1000+ concurrent sessions
- Sub-second authentication
- Horizontal scaling ready

## Error Handling

### User-Specific Error Codes
- `USR001`: User not found
- `USR002`: Email already exists
- `USR003`: Invalid password
- `USR004`: Account locked
- `USR005`: Insufficient permissions
- `USR006`: Training expired
- `USR007`: Invalid role assignment
- `USR008`: Cannot delete user with active studies

## Security Best Practices

### Account Security
1. Enforce strong passwords
2. Require MFA for privileged users
3. Regular access reviews
4. Prompt deactivation of unused accounts
5. Monitor for suspicious activity

### Data Protection
1. Never store plaintext passwords
2. Encrypt sensitive user data
3. Mask PHI in logs
4. Secure API endpoints
5. Regular security audits

## Change Log

### Version 1.0 (January 2025)
- Initial implementation
- Full RBAC system
- MFA support
- Training management
- Audit trail

### Planned Enhancements
- Biometric authentication
- Risk-based authentication
- Advanced user analytics
- Automated access reviews
- Integration with more IdPs

---

*Last Updated: January 2025*  
*API Version: 1.0*  
*Compliance: 21 CFR Part 11, HIPAA, GDPR*