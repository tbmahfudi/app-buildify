# Security Policy

## Version 0.3.0 - Security Enhancements

This document outlines the security features, best practices, and recommendations for the Multi-Tenant NoCode Application API.

## Security Features

### 1. Authentication & Authorization

#### JWT Token Security
- **HS256 Algorithm** with configurable secret key
- **JTI (JWT ID)** for unique token identification and revocation
- **Token Expiration**
  - Access tokens: 30 minutes (configurable)
  - Refresh tokens: 7 days (configurable)
- **Token Rotation** - New refresh token issued on each refresh
- **Token Revocation** - Logout endpoint revokes tokens via Redis

#### Password Security
- **bcrypt hashing** with automatic salting
- **Password strength** - Configurable requirements
- **No password storage** - Only hashed values stored
- **Secure password reset** - (To be implemented)

#### Multi-Tenant Isolation
- **CRITICAL FIX (v0.3.0):** Tenant ID now extracted from JWT payload only
- **Previous vulnerability:** X-Tenant-Id header was client-controlled
- **Current implementation:** Server-side tenant validation from trusted JWT claims
- **Superuser bypass** for cross-tenant operations (audited)

### 2. Input Validation & Sanitization

#### Pydantic Validation
- **Automatic validation** of all request payloads
- **Type checking** enforced at runtime
- **String length limits** prevent buffer overflow
- **Pattern matching** for codes, UUIDs, emails
- **XSS prevention** - HTML tags rejected in text fields
- **SQL injection prevention** - ORM-based queries only

#### Custom Validators
- **Code validation** - Alphanumeric, underscore, hyphen only
- **UUID validation** - Strict format checking
- **JSON sanitization** - Dangerous patterns rejected
- **Email validation** - RFC-compliant format

### 3. Rate Limiting

#### Request Throttling
- **Default limit:** 60 requests/minute
- **User-based** rate limiting for authenticated requests
- **IP-based** fallback for anonymous requests
- **Configurable** via environment variables
- **Graceful handling** - Returns 429 Too Many Requests

### 4. Error Handling

#### Secure Error Responses
- **No stack traces** in production responses
- **Generic error messages** prevent information leakage
- **Detailed logging** for debugging (server-side only)
- **Request tracking** with unique request IDs

#### Exception Handling
- **Validation errors** - 422 with field-specific details
- **Authentication errors** - 401 without revealing user existence
- **Authorization errors** - 403 with minimal information
- **Database errors** - Sanitized messages prevent SQL injection discovery

### 5. Audit Logging

#### Comprehensive Audit Trail
- **All operations logged** - Create, Read, Update, Delete
- **User attribution** - User ID, email, tenant ID
- **Change tracking** - Before/after snapshots
- **Request context** - IP address, user agent, request ID
- **Tenant isolation** - Users can only see their tenant's logs
- **Immutable logs** - No deletion allowed (archive only)

### 6. API Security

#### API Versioning
- **Versioned endpoints** - `/api/v1/` for future-proof evolution
- **Backward compatibility** - Legacy endpoints deprecated but functional
- **Breaking change management** - New version for incompatible changes

#### CORS Configuration
- **Configurable origins** - Restrict to trusted domains
- **Credentials support** - Secure cookie/auth header handling
- **Preflight caching** - Performance optimization

### 7. Database Security

#### Connection Security
- **Connection pooling** with pre-ping health checks
- **Parameterized queries** via SQLAlchemy ORM
- **SQL injection prevention** - No raw SQL in user input
- **Prepared statements** - Automatic query compilation

#### Data Protection
- **Tenant isolation** at query level
- **Soft deletes** option for sensitive data
- **Encryption at rest** (database-level configuration)
- **Backup encryption** recommended

### 8. Monitoring & Observability

#### Health Checks
- **Comprehensive health endpoint** - `/api/health`
- **Component status** - Database, Redis, rate limiter
- **Degraded state detection** - Partial service availability

#### Structured Logging
- **JSON logs in production** - Easy parsing and analysis
- **Request correlation** - Track requests across services
- **PII redaction** - Sensitive data masked in logs
- **Log levels** - Configurable verbosity

#### Error Tracking
- **Sentry integration** (optional) - Automatic error reporting
- **Error grouping** - Similar errors aggregated
- **Release tracking** - Correlate errors with deployments

## Security Best Practices

### Production Deployment

#### 1. Environment Configuration

**CRITICAL:**
```bash
# Generate a strong secret key
SECRET_KEY=$(openssl rand -hex 32)

# Set production environment
ENVIRONMENT=production

# Restrict CORS origins
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

#### 2. Database Security

```bash
# Use strong credentials
SQLALCHEMY_DATABASE_URL=postgresql+psycopg2://username:$(openssl rand -base64 32)@localhost/db

# Enable SSL/TLS
SQLALCHEMY_DATABASE_URL=postgresql+psycopg2://user:pass@localhost/db?sslmode=require
```

#### 3. Redis Security

```bash
# Use password authentication
REDIS_URL=redis://:$(openssl rand -base64 32)@localhost:6379/0

# Or separate configuration
REDIS_PASSWORD=$(openssl rand -base64 32)
```

#### 4. Rate Limiting

```bash
# Enable rate limiting
RATE_LIMIT_ENABLED=true

# Adjust based on your needs
RATE_LIMIT_PER_MINUTE=100  # Higher for APIs, lower for auth endpoints
```

#### 5. Logging & Monitoring

```bash
# Production logging
LOG_LEVEL=INFO  # or WARNING in production
ENVIRONMENT=production  # Enables JSON logging

# Error tracking
SENTRY_DSN=https://your-sentry-dsn-here
```

### Application Security

#### Password Policies
- **Minimum length:** 12 characters (recommended)
- **Complexity:** Mix of uppercase, lowercase, numbers, symbols
- **No common passwords** - Check against common password lists
- **Password expiration** - Consider 90-day rotation for sensitive applications
- **Account lockout** - Implement after N failed login attempts

#### Session Management
- **Short-lived tokens** - 30-minute access tokens
- **Refresh token rotation** - New refresh token on each use
- **Token revocation** - Logout invalidates tokens immediately (with Redis)
- **Concurrent session limits** - Consider limiting active sessions per user

#### Access Control
- **Principle of least privilege** - Grant minimal necessary permissions
- **Role-based access** - Use roles for permission grouping
- **Tenant isolation** - Enforce at every data access point
- **Superuser auditing** - Log all superuser actions

### Network Security

#### HTTPS/TLS
```nginx
# Example nginx configuration
server {
    listen 443 ssl http2;
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### Firewall Rules
```bash
# Allow only necessary ports
ufw allow 443/tcp  # HTTPS
ufw allow 22/tcp   # SSH (restrict to specific IPs)
ufw deny 8000/tcp  # Block direct access to API
ufw enable
```

#### Database Access
```bash
# Restrict database to localhost or specific IPs
# PostgreSQL pg_hba.conf example:
host    all    all    127.0.0.1/32    scram-sha-256
host    all    all    10.0.0.0/24     scram-sha-256  # App servers only
```

### Dependency Security

#### Regular Updates
```bash
# Check for security vulnerabilities
pip install safety
safety check

# Update dependencies
pip list --outdated
pip install --upgrade <package>
```

#### Dependency Scanning
- **GitHub Dependabot** - Automatic security alerts
- **Snyk** - Continuous vulnerability monitoring
- **OWASP Dependency-Check** - Periodic scans

## Security Vulnerabilities

### Reporting Security Issues

**DO NOT** create public GitHub issues for security vulnerabilities.

Instead, please email security reports to: **[your-security-email@domain.com]**

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if available)

We will respond within 48 hours.

### Security Advisories

Security advisories will be published on:
- GitHub Security Advisories
- Project release notes
- Security mailing list (if configured)

## Threat Model

### Assets
1. **User credentials** (passwords, tokens)
2. **Tenant data** (business-critical information)
3. **Audit logs** (compliance and forensics)
4. **System configuration** (secrets, API keys)

### Threats
1. **Unauthorized access** - Token theft, session hijacking
2. **Data breach** - SQL injection, tenant isolation bypass
3. **Denial of service** - Rate limiting bypass, resource exhaustion
4. **Information disclosure** - Error messages, verbose logging
5. **Privilege escalation** - RBAC bypass, superuser exploitation

### Mitigations
1. **JWT tokens** with short expiration and revocation
2. **Tenant isolation** at JWT level with server-side validation
3. **Rate limiting** per user/IP with configurable thresholds
4. **Error sanitization** with generic messages in production
5. **RBAC enforcement** at endpoint and data query levels

## Compliance Considerations

### GDPR
- **Data minimization** - Collect only necessary information
- **Right to erasure** - Implement user data deletion
- **Data portability** - Export user data in standard formats
- **Audit logging** - Track all data access and modifications

### SOC 2
- **Access controls** - RBAC with audit trails
- **Encryption** - In transit (HTTPS) and at rest (database encryption)
- **Monitoring** - Health checks, error tracking, audit logs
- **Incident response** - Error tracking, alerting, logging

### HIPAA (if applicable)
- **Encryption** - All PHI encrypted
- **Access logs** - Comprehensive audit trails
- **Authentication** - Strong password policies
- **Transmission security** - HTTPS/TLS only

## Security Checklist

### Pre-Production
- [ ] Strong `SECRET_KEY` configured (32+ chars)
- [ ] `ENVIRONMENT=production` set
- [ ] CORS restricted to specific domains
- [ ] PostgreSQL/MySQL configured (not SQLite)
- [ ] Database credentials are strong and unique
- [ ] Redis password configured
- [ ] Rate limiting enabled
- [ ] HTTPS/TLS configured
- [ ] Firewall rules configured
- [ ] Dependencies updated and scanned
- [ ] Test credentials removed
- [ ] Sentry/error tracking configured
- [ ] Health check monitoring set up
- [ ] Backup strategy implemented
- [ ] Incident response plan documented

### Post-Deployment
- [ ] Monitor error rates
- [ ] Review audit logs regularly
- [ ] Test backup restoration
- [ ] Perform security assessments
- [ ] Keep dependencies updated
- [ ] Review access logs for anomalies
- [ ] Test disaster recovery procedures

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [Python Security Best Practices](https://python.readthedocs.io/en/latest/library/security_warnings.html)

## Version History

### v0.3.0 (Current)
- **SECURITY FIX:** Removed client-controlled X-Tenant-Id header
- Added JWT-based tenant isolation
- Implemented token revocation with Redis
- Added rate limiting
- Enhanced error handling and logging
- Implemented API versioning
- Added comprehensive input validation

### v0.2.0
- Basic JWT authentication
- RBAC implementation
- Audit logging
- Multi-tenant support (with security vulnerability)

---

**Last Updated:** 2025-10-26
**Maintained By:** Development Team
