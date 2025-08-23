# Security Configuration Documentation

## Overview
This document outlines the comprehensive security measures implemented in the Cortex Clinical Dashboard platform to ensure data protection, prevent common web vulnerabilities, and maintain compliance with healthcare regulations.

## Security Headers Implementation

### Content Security Policy (CSP)
**Location**: `frontend/next.config.ts`

The CSP header is configured to prevent XSS attacks by controlling which resources can be loaded:
- `default-src 'self'`: Only allow resources from the same origin by default
- `script-src`: Allows scripts from self and CDN (required for Swagger UI)
- `frame-ancestors 'none'`: Prevents clickjacking attacks
- `upgrade-insecure-requests`: Forces HTTPS for all requests

### X-Frame-Options
**Value**: `DENY`
- Prevents the site from being embedded in iframes
- Provides clickjacking protection for older browsers

### X-Content-Type-Options
**Value**: `nosniff`
- Prevents MIME type sniffing
- Forces browsers to respect the declared content-type

### Referrer-Policy
**Value**: `strict-origin-when-cross-origin`
- Controls information sent with external requests
- Prevents leaking sensitive URLs to third parties

### Permissions-Policy
Restricts access to browser features:
- Camera, microphone, geolocation: Disabled
- Payment, USB: Disabled
- Notifications: Self only
- Fullscreen: Self only

### HSTS (HTTP Strict Transport Security)
**Note**: Should be configured at the reverse proxy level in production
- Forces HTTPS connections
- Prevents protocol downgrade attacks
- Example configuration included in comments

## Authentication Security

### JWT Token Storage
**Implementation**: Memory-only storage with httpOnly refresh tokens

#### Access Tokens
- Stored in memory only (not in localStorage)
- Prevents XSS attacks from stealing tokens
- Automatically refreshed before expiry
- 30-minute expiration

#### Refresh Tokens
- Stored as httpOnly cookies
- Cannot be accessed via JavaScript
- Secure flag set in production (HTTPS only)
- SameSite attribute prevents CSRF attacks
- 7-day expiration with rotation on use

### Files Updated:
- `backend/app/core/security.py`: Token generation and validation
- `backend/app/api/routes/login.py`: Login endpoints with cookie management
- `frontend/src/lib/auth-context.tsx`: Memory-only token storage
- `frontend/src/lib/api/secure-client.ts`: Secure API client with auto-refresh

## External Link Security

### URL Validation
**Location**: `frontend/src/components/dashboard/DashboardNavigation.tsx`

- Blocks `javascript:` and `data:` protocols
- Only allows `http://` and `https://` URLs
- Logs blocked attempts for monitoring

### Target Attribute Validation
- Only allows safe target values: `_blank`, `_self`, `_parent`, `_top`
- Defaults to `_blank` if invalid value provided
- Prevents attacker-controlled window targeting

### Tab-nabbing Prevention
- All external links include `noopener,noreferrer`
- Prevents opened pages from accessing `window.opener`
- Protects against reverse tabnabbing attacks

## Role-Based Access Control (RBAC)

### Admin Route Protection
**Location**: `frontend/src/app/admin/layout.tsx`

All admin routes are protected by `AuthGuard` component:
```typescript
<AuthGuard requiredRoles={['system_admin', 'org_admin']}>
  {children}
</AuthGuard>
```

### Permission System
- Dynamic permission checking
- Role-based access control
- Audit logging for all permission changes

## API Security

### CORS Configuration
**Location**: `backend/app/main.py`

- Credentials allowed for cookie-based auth
- Origin whitelist configured
- Prevents unauthorized cross-origin requests

### Request Validation
- Pydantic models for input validation
- SQL injection prevention via SQLAlchemy ORM
- Rate limiting (to be implemented)

## Audit Trail

### Activity Logging
All sensitive operations are logged:
- User authentication (login/logout)
- Data access and modifications
- Permission changes
- Failed authentication attempts

### Log Contents
- User identification
- IP address
- User agent
- Timestamp
- Action details

## Development vs Production

### Development Settings
- Relaxed CSP for hot reload
- Secure cookies disabled (HTTP localhost)
- SameSite=lax for cookies

### Production Settings
- Strict CSP policy
- Secure cookies (HTTPS only)
- SameSite=strict for cookies
- HSTS at reverse proxy

## Security Best Practices

### Regular Updates
- Keep dependencies updated
- Monitor security advisories
- Regular security audits

### Secrets Management
- Never commit secrets to repository
- Use environment variables
- Rotate tokens regularly

### Input Validation
- Always validate user input
- Use parameterized queries
- Sanitize output

### Error Handling
- Never expose sensitive information in errors
- Log errors securely
- Generic error messages to users

## Compliance Considerations

### HIPAA Compliance
- Encryption in transit (HTTPS)
- Audit logging
- Access controls
- Session management

### 21 CFR Part 11
- User authentication
- Audit trails
- Data integrity
- Electronic signatures (planned)

## Security Testing Checklist

- [ ] CSP headers properly set
- [ ] No tokens in localStorage
- [ ] External links validated
- [ ] RBAC functioning correctly
- [ ] Audit logs capturing events
- [ ] No sensitive data in errors
- [ ] HTTPS enforced in production
- [ ] Session timeout implemented
- [ ] Input validation working
- [ ] SQL injection prevention tested

## Incident Response

In case of security incident:
1. Immediately revoke affected tokens
2. Check audit logs for unauthorized access
3. Notify affected users
4. Document incident
5. Update security measures

## Contact

For security concerns or vulnerability reports, contact:
- Security Team: security@sagarmatha.ai
- Emergency: Use designated security hotline

---

Last Updated: 2024-12-23
Version: 1.0