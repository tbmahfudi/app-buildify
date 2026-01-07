# No-Code Template System - Complete Guide

## Table of Contents
1. [Overview](#overview)
2. [Platform vs Tenant Level](#platform-vs-tenant-level)
3. [Template Categories](#template-categories)
4. [Version Control](#version-control)
5. [Import/Export System](#importexport-system)
6. [API Reference](#api-reference)
7. [Usage Examples](#usage-examples)

---

## Overview

The No-Code Template System provides a comprehensive framework for creating, managing, and distributing reusable templates across your platform. It supports:

- **Multi-level Scope**: Platform-wide templates and tenant-specific customizations
- **Rich Categorization**: Organize templates by industry, use-case, or function
- **Version Control**: Track changes, compare versions, and rollback if needed
- **Import/Export**: Package and distribute templates as ZIP files
- **Granular Permissions**: Fine-grained access control for all operations

---

## Platform vs Tenant Level

### Platform-Level Templates (`tenant_id = NULL`)
- **Visibility**: Available to ALL tenants
- **Use Case**: Standard templates, starter kits, best practices
- **Access**: Read-only for tenants, modifiable only by superusers
- **Examples**: Generic Task, Contact, Document templates

### Tenant-Level Templates (`tenant_id = <specific>`)
- **Visibility**: Only visible to the owning tenant
- **Use Case**: Custom configurations, tenant-specific workflows
- **Access**: Full CRUD access for tenant admins
- **Examples**: "Acme Corp Customer", "XYZ Inc Orders"

### Clone Functionality
Tenants can clone platform templates to create customizable tenant-specific versions:

```javascript
// Clone platform template to tenant scope
POST /api/v1/data-model/entities/{id}/clone?new_name=acme_customer&new_label=Acme Customer
```

**Result**: Creates a tenant-specific copy that can be modified independently.

---

## Template Categories

### Category Hierarchy

```
Industry Templates
├── Healthcare
├── Finance & Banking
├── Retail & E-commerce
├── Manufacturing
├── Education
└── Real Estate

Use Case Templates
├── CRM & Sales ⭐
├── Project Management ⭐
├── Human Resources
├── Inventory Management
├── Document Management
└── Customer Support

Functional Templates
├── Data Collection
├── Reporting & Analytics
├── Workflow Automation
└── Communication

General Templates ⭐
└── Generic templates suitable for any industry
```

⭐ = Featured categories

### Category Model

```python
class TemplateCategory:
    code: str           # Unique identifier (e.g., "crm")
    name: str           # Display name (e.g., "CRM & Sales")
    description: str    # Category description
    icon: str           # Phosphor icon name
    color: str          # UI color theme
    category_type: str  # 'industry', 'use_case', 'function'
    parent_id: UUID     # For hierarchy
    path: str           # Materialized path (/use_case/crm/)
    is_featured: bool   # Show in featured section
```

### Seeding Categories

```bash
python -m app.seeds.seed_template_categories
```

This creates 24+ categories with proper hierarchy and metadata.

---

## Version Control

### Overview
Track every change to platform templates with immutable version history.

### Key Features

1. **Automatic Snapshots**: Full template state captured in JSON
2. **Version Numbering**: Sequential version numbers (1, 2, 3...)
3. **Change Types**: major, minor, patch, hotfix, rollback
4. **Changelog**: Detailed change descriptions
5. **Comparison**: Diff between any two versions
6. **Rollback**: Restore to any previous version

### Version Model

```python
class TemplateVersion:
    template_type: str       # 'entity', 'workflow', 'automation', 'lookup'
    template_id: UUID        # ID of the template
    version_number: int      # Sequential version number
    version_name: str        # e.g., "v1.0", "Initial Release"
    change_summary: str      # Brief summary of changes
    change_type: str         # 'major', 'minor', 'patch', 'hotfix'
    changelog: Text          # Detailed changelog
    template_snapshot: JSON  # Complete template state
    is_current: bool         # Is this the current version?
    is_published: bool       # Is this published?
    published_at: DateTime
    created_by: UUID
```

### Creating a Version

```python
# After modifying a template
POST /api/v1/templates/versions
{
    "template_type": "entity",
    "template_id": "uuid-here",
    "change_summary": "Added new fields for customer segmentation",
    "change_type": "minor",
    "changelog": "- Added 'segment' field\n- Added 'tier' field\n- Updated validation rules"
}
```

### Viewing Version History

```python
GET /api/v1/templates/versions?template_type=entity&template_id=uuid-here

Response:
[
    {
        "version_number": 3,
        "version_name": "v3.0",
        "change_summary": "Added new fields",
        "created_at": "2026-01-06T10:30:00Z",
        "is_current": true
    },
    {
        "version_number": 2,
        "version_name": "v2.0",
        "change_summary": "Updated field types",
        "created_at": "2026-01-05T14:20:00Z",
        "is_current": false
    }
]
```

### Comparing Versions

```python
GET /api/v1/templates/versions/compare?template_type=entity&template_id=uuid&from_version=1&to_version=3

Response:
{
    "from_version": 1,
    "to_version": 3,
    "changes": [
        {
            "type": "added",
            "field": "segment",
            "to": "VARCHAR(50)"
        },
        {
            "type": "modified",
            "field": "description",
            "from": "Customer record",
            "to": "Customer record with segmentation"
        }
    ]
}
```

### Rolling Back

```python
POST /api/v1/templates/versions/rollback
{
    "template_type": "entity",
    "template_id": "uuid-here",
    "version_number": 2
}

# This will:
# 1. Restore the template to version 2 state
# 2. Create a new version entry documenting the rollback
```

---

## Import/Export System

### Overview
Package templates for distribution across systems, organizations, or tenants.

### Package Format

#### ZIP Structure
```
my-crm-templates.zip
├── package.json        # Package metadata
├── templates.json      # All template definitions
└── README.md          # Documentation
```

#### package.json
```json
{
    "name": "CRM Starter Pack",
    "code": "crm_starter_pack",
    "version": "1.0.0",
    "description": "Essential CRM templates for sales teams",
    "author": "admin@example.com",
    "license": "MIT",
    "created_at": "2026-01-06T00:00:00Z"
}
```

#### templates.json
```json
{
    "templates": [
        {
            "type": "entity",
            "version": "1.0",
            "exported_at": "2026-01-06T10:00:00Z",
            "template": {
                "name": "customer",
                "label": "Customer",
                "description": "Customer management entity",
                "fields": [...]
            },
            "fields": [...]
        }
    ],
    "metadata": {
        "template_count": 1,
        "created_at": "2026-01-06T10:00:00Z"
    }
}
```

### Export Operations

#### Export Single Entity
```python
GET /api/v1/templates/export/entity/{entity_id}?include_fields=true

Response:
{
    "type": "entity",
    "version": "1.0",
    "exported_at": "2026-01-06T10:00:00Z",
    "exported_by": "user-uuid",
    "template": {...},
    "fields": [...]
}
```

#### Create Package
```python
POST /api/v1/templates/packages
{
    "name": "CRM Starter Pack",
    "description": "Essential templates for CRM",
    "template_ids": [
        {"type": "entity", "id": "customer-uuid"},
        {"type": "entity", "id": "contact-uuid"},
        {"type": "workflow", "id": "sales-workflow-uuid"}
    ],
    "category_code": "crm",
    "version": "1.0.0",
    "author": "Your Name",
    "license": "MIT"
}
```

#### Download Package
```python
GET /api/v1/templates/packages/{package_id}/download

Response: ZIP file download
```

### Import Operations

#### Import Single Entity
```python
POST /api/v1/templates/import/entity
{
    "template_data": {
        "type": "entity",
        "template": {...},
        "fields": [...]
    },
    "make_platform_level": false  # true = platform, false = tenant
}
```

#### Import from ZIP
```python
POST /api/v1/templates/import/zip
Content-Type: multipart/form-data

file: my-crm-templates.zip
make_platform_level: false

Response:
{
    "imported": 3,
    "failed": 0,
    "templates": [
        {"type": "entity", "id": "new-uuid-1", "name": "customer"},
        {"type": "entity", "id": "new-uuid-2", "name": "contact"},
        {"type": "workflow", "id": "new-uuid-3", "name": "sales_workflow"}
    ],
    "errors": []
}
```

---

## API Reference

### Version Control Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/templates/versions` | Create version snapshot |
| GET | `/api/v1/templates/versions` | List all versions |
| GET | `/api/v1/templates/versions/{id}` | Get specific version |
| POST | `/api/v1/templates/versions/rollback` | Rollback to version |
| GET | `/api/v1/templates/versions/compare` | Compare two versions |

### Package Management Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/templates/export/entity/{id}` | Export entity as JSON |
| POST | `/api/v1/templates/packages` | Create template package |
| GET | `/api/v1/templates/packages` | List all packages |
| GET | `/api/v1/templates/packages/{id}/download` | Download package ZIP |

### Import Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/templates/import/entity` | Import entity from JSON |
| POST | `/api/v1/templates/import/package` | Import package from JSON |
| POST | `/api/v1/templates/import/zip` | Import from ZIP file |

---

## Usage Examples

### Example 1: Creating and Distributing a Template Package

```python
# Step 1: Create platform templates
POST /api/v1/data-model/entities
{
    "name": "lead",
    "label": "Lead",
    "is_platform_level": true,
    # ... other fields
}

# Step 2: Version the template
POST /api/v1/templates/versions
{
    "template_type": "entity",
    "template_id": "lead-uuid",
    "change_summary": "Initial release",
    "change_type": "major"
}

# Step 3: Create package
POST /api/v1/templates/packages
{
    "name": "Sales Starter Pack",
    "description": "Lead and opportunity management",
    "template_ids": [
        {"type": "entity", "id": "lead-uuid"},
        {"type": "entity", "id": "opportunity-uuid"}
    ]
}

# Step 4: Download and distribute
GET /api/v1/templates/packages/{package-id}/download
```

### Example 2: Importing Templates to New Tenant

```python
# Upload ZIP file
POST /api/v1/templates/import/zip
file: sales-starter-pack.zip
make_platform_level: false

# Templates are now available in tenant's scope
GET /api/v1/data-model/entities
# Returns imported entities as tenant-specific
```

### Example 3: Version Control Workflow

```python
# Initial version
POST /api/v1/templates/versions
{
    "template_type": "entity",
    "template_id": "customer-uuid",
    "change_summary": "Initial version",
    "version_name": "v1.0"
}

# Make changes to template...

# Create new version
POST /api/v1/templates/versions
{
    "template_type": "entity",
    "template_id": "customer-uuid",
    "change_summary": "Added email validation",
    "change_type": "minor",
    "version_name": "v1.1"
}

# Something went wrong, rollback
POST /api/v1/templates/versions/rollback
{
    "template_type": "entity",
    "template_id": "customer-uuid",
    "version_number": 1
}
```

---

## Security & Permissions

### Permission Matrix

| Operation | Platform Templates | Tenant Templates |
|-----------|-------------------|------------------|
| Create | `data_model:create:platform` | `data_model:create:tenant` |
| Read | `data_model:read:platform` | `data_model:read:tenant` |
| Update | `data_model:update:platform` | `data_model:update:tenant` |
| Delete | `data_model:delete:platform` | `data_model:delete:tenant` |
| Clone | `data_model:clone:platform` | N/A |
| Version | Superuser only | N/A |
| Package | Superuser only | N/A |
| Import Platform | Superuser only | N/A |
| Import Tenant | Tenant admin | N/A |

### Best Practices

1. **Platform Templates**: Only verified, tested templates
2. **Versioning**: Create version before major changes
3. **Packages**: Include comprehensive documentation
4. **Import**: Always review before importing to production
5. **Categories**: Use consistent categorization scheme

---

## Database Schema

### Template Categories
```sql
CREATE TABLE template_categories (
    id UUID PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    icon VARCHAR(50),
    color VARCHAR(50),
    parent_id UUID REFERENCES template_categories(id),
    level INTEGER DEFAULT 0,
    path VARCHAR(500),
    category_type VARCHAR(50) NOT NULL,
    display_order INTEGER DEFAULT 0,
    is_featured BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    is_system BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Template Versions
```sql
CREATE TABLE template_versions (
    id UUID PRIMARY KEY,
    template_type VARCHAR(50) NOT NULL,
    template_id UUID NOT NULL,
    version_number INTEGER NOT NULL,
    version_name VARCHAR(100),
    change_summary TEXT NOT NULL,
    change_type VARCHAR(50),
    changelog TEXT,
    template_snapshot TEXT NOT NULL,
    is_published BOOLEAN DEFAULT FALSE,
    is_current BOOLEAN DEFAULT TRUE,
    published_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES users(id) NOT NULL
);
```

### Template Packages
```sql
CREATE TABLE template_packages (
    id UUID PRIMARY KEY,
    code VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    version VARCHAR(50) DEFAULT '1.0.0',
    author VARCHAR(200),
    author_email VARCHAR(255),
    license VARCHAR(100),
    homepage_url VARCHAR(500),
    category_id UUID REFERENCES template_categories(id),
    package_data TEXT NOT NULL,
    dependencies TEXT,
    install_count INTEGER DEFAULT 0,
    last_installed_at TIMESTAMP,
    is_published BOOLEAN DEFAULT FALSE,
    is_verified BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES users(id)
);
```

---

## Troubleshooting

### Common Issues

**Q: Template import fails with "already exists" error**
A: Check for name conflicts. Either delete existing template or rename during import.

**Q: Can't create platform-level template**
A: Only superusers can create platform templates. Check permissions.

**Q: Version rollback doesn't restore all fields**
A: Ensure the version snapshot was created correctly. Check `template_snapshot` JSON.

**Q: Package download returns empty ZIP**
A: Verify package has template data. Check `package_data` field is populated.

---

## Future Enhancements

- [ ] Template marketplace UI
- [ ] Automatic dependency resolution
- [ ] Template analytics (usage, popularity)
- [ ] Multi-version package support
- [ ] Template rating and reviews
- [ ] Automated testing for templates
- [ ] Template diff visualization

---

## Support

For issues, questions, or feature requests:
- Documentation: `/docs/TEMPLATE_SYSTEM_GUIDE.md`
- API Reference: `/docs/API.md`
- Issue Tracker: GitHub Issues

---

**Last Updated**: 2026-01-06
**Version**: 1.0.0
**Author**: Platform Team
