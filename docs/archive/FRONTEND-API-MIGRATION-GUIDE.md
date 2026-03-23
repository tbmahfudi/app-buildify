# Frontend API Migration Guide - Phase 2 Priority 2

**Date:** 2026-01-13
**Status:** Action Required - All deprecated endpoints removed
**Impact:** HIGH - All API calls must be updated

---

## Executive Summary

All backend APIs have been migrated to `/api/v1/*` prefix. **All deprecated unversioned endpoints have been removed** and will return 404 errors.

**Action Required:** Update all frontend API calls to use the new paths below.

---

## Quick Migration Reference

### Simple Find & Replace

For each service file, apply these find & replace operations:

```javascript
// Auth API
'/auth/'          → '/api/v1/auth/'

// Organization API
'/org/'           → '/api/v1/org/'

// Metadata API
'/metadata/'      → '/api/v1/metadata/'

// Data API
'/data/'          → '/api/v1/data/'

// Audit API
'/audit/'         → '/api/v1/audit/'

// Settings API
'/settings/'      → '/api/v1/settings/'

// Modules API
'/modules/'       → '/api/v1/modules/'

// RBAC API
'/rbac/'          → '/api/v1/rbac/'

// Reports API
'/reports/'       → '/api/v1/reports/'

// Dashboards API
'/dashboards/'    → '/api/v1/dashboards/'

// Scheduler API
'/scheduler/'     → '/api/v1/scheduler/'

// Menu API
'/menu/'          → '/api/v1/menu/'

// Admin Security API
'/admin/security/' → '/api/v1/admin/security/'
```

---

## Detailed API Migration Tables

### 1. Authentication API

**Old Prefix:** `/auth/*`
**New Prefix:** `/api/v1/auth/*`

| Endpoint | Old Path | New Path | Frontend Files Affected |
|----------|----------|----------|------------------------|
| Login | `POST /auth/login` | `POST /api/v1/auth/login` | `assets/js/auth.js` |
| Logout | `POST /auth/logout` | `POST /api/v1/auth/logout` | `assets/js/auth.js` |
| Refresh Token | `POST /auth/refresh` | `POST /api/v1/auth/refresh` | `assets/js/auth.js` |
| Get Current User | `GET /auth/me` | `GET /api/v1/auth/me` | `assets/js/auth.js` |
| Change Password | `POST /auth/change-password` | `POST /api/v1/auth/change-password` | `assets/js/auth.js` |

**Estimated Files:** 1 file
**Priority:** CRITICAL - Test immediately after changes

---

### 2. Organization API

**Old Prefix:** `/org/*`
**New Prefix:** `/api/v1/org/*`

| Endpoint | Old Path | New Path | Frontend Files Affected |
|----------|----------|----------|------------------------|
| List Companies | `GET /org/companies` | `GET /api/v1/org/companies` | `assets/js/companies.js` |
| Get Company | `GET /org/companies/{id}` | `GET /api/v1/org/companies/{id}` | `assets/js/companies.js` |
| Create Company | `POST /org/companies` | `POST /api/v1/org/companies` | `assets/js/companies.js` |
| Update Company | `PUT /org/companies/{id}` | `PUT /api/v1/org/companies/{id}` | `assets/js/companies.js` |
| Delete Company | `DELETE /org/companies/{id}` | `DELETE /api/v1/org/companies/{id}` | `assets/js/companies.js` |
| List Branches | `GET /org/branches` | `GET /api/v1/org/branches` | `assets/js/tenants.js` |
| Get Branch | `GET /org/branches/{id}` | `GET /api/v1/org/branches/{id}` | `assets/js/tenants.js` |
| Create Branch | `POST /org/branches` | `POST /api/v1/org/branches` | `assets/js/tenants.js` |
| Update Branch | `PUT /org/branches/{id}` | `PUT /api/v1/org/branches/{id}` | `assets/js/tenants.js` |
| Delete Branch | `DELETE /org/branches/{id}` | `DELETE /api/v1/org/branches/{id}` | `assets/js/tenants.js` |
| List Departments | `GET /org/departments` | `GET /api/v1/org/departments` | `assets/js/organization-hierarchy.js` |
| Get Department | `GET /org/departments/{id}` | `GET /api/v1/org/departments/{id}` | `assets/js/organization-hierarchy.js` |
| Create Department | `POST /org/departments` | `POST /api/v1/org/departments` | `assets/js/organization-hierarchy.js` |
| Update Department | `PUT /org/departments/{id}` | `PUT /api/v1/org/departments/{id}` | `assets/js/organization-hierarchy.js` |
| Delete Department | `DELETE /org/departments/{id}` | `DELETE /api/v1/org/departments/{id}` | `assets/js/organization-hierarchy.js` |
| List Tenants | `GET /org/tenants` | `GET /api/v1/org/tenants` | `assets/js/tenants.js` |
| Get Tenant | `GET /org/tenants/{id}` | `GET /api/v1/org/tenants/{id}` | `assets/js/tenants.js` |
| Create Tenant | `POST /org/tenants` | `POST /api/v1/org/tenants` | `assets/js/tenants.js` |
| Update Tenant | `PUT /org/tenants/{id}` | `PUT /api/v1/org/tenants/{id}` | `assets/js/tenants.js` |
| Delete Tenant | `DELETE /org/tenants/{id}` | `DELETE /api/v1/org/tenants/{id}` | `assets/js/tenants.js` |
| List Users | `GET /org/users` | `GET /api/v1/org/users` | Multiple files |

**Estimated Files:** 3 files (companies.js, tenants.js, organization-hierarchy.js)
**Priority:** HIGH

---

### 3. Metadata API

**Old Prefix:** `/metadata/*`
**New Prefix:** `/api/v1/metadata/*`

| Endpoint | Old Path | New Path | Frontend Files Affected |
|----------|----------|----------|------------------------|
| List Entities | `GET /metadata/entities` | `GET /api/v1/metadata/entities` | `assets/js/metadata-service.js` |
| Get Entity Metadata | `GET /metadata/entities/{name}` | `GET /api/v1/metadata/entities/{name}` | `assets/js/metadata-service.js` |
| Create Metadata | `POST /metadata/entities` | `POST /api/v1/metadata/entities` | `assets/js/metadata-service.js` |
| Update Metadata | `PUT /metadata/entities/{name}` | `PUT /api/v1/metadata/entities/{name}` | `assets/js/metadata-service.js` |
| Delete Metadata | `DELETE /metadata/entities/{name}` | `DELETE /api/v1/metadata/entities/{name}` | `assets/js/metadata-service.js` |

**Estimated Files:** 3 files (metadata-service.js, dynamic-table.js, dynamic-form.js)
**Priority:** HIGH

---

### 4. Data API

**Old Prefix:** `/data/*`
**New Prefix:** `/api/v1/data/*`

| Endpoint | Old Path | New Path | Frontend Files Affected |
|----------|----------|----------|------------------------|
| Search/List | `POST /data/{entity}/list` | `GET /api/v1/data/{entity}/list` | `assets/js/data-service.js` |
| Get Record | `GET /data/{entity}/{id}` | `GET /api/v1/data/{entity}/{id}` | `assets/js/data-service.js` |
| Create | `POST /data/{entity}` | `POST /api/v1/data/{entity}` | `assets/js/data-service.js` |
| Update | `PUT /data/{entity}/{id}` | `PUT /api/v1/data/{entity}/{id}` | `assets/js/data-service.js` |
| Delete | `DELETE /data/{entity}/{id}` | `DELETE /api/v1/data/{entity}/{id}` | `assets/js/data-service.js` |
| Bulk Operations | `POST /data/{entity}/bulk` | `POST /api/v1/data/{entity}/bulk` | `assets/js/data-service.js` |

**Estimated Files:** 2 files (data-service.js, entity-manager.js)
**Priority:** HIGH

**Note:** List endpoint method changed from POST to GET - update accordingly

---

### 5. Audit API

**Old Prefix:** `/audit/*`
**New Prefix:** `/api/v1/audit/*`

| Endpoint | Old Path | New Path | Frontend Files Affected |
|----------|----------|----------|------------------------|
| List Audit Logs | `GET /audit/logs` | `GET /api/v1/audit/logs` | `assets/js/audit-viewer.js` |
| Get Audit Log | `GET /audit/logs/{id}` | `GET /api/v1/audit/logs/{id}` | `assets/js/audit-viewer.js` |

**Estimated Files:** 1 file
**Priority:** MEDIUM

---

### 6. Settings API

**Old Prefix:** `/settings/*`
**New Prefix:** `/api/v1/settings/*`

| Endpoint | Old Path | New Path | Frontend Files Affected |
|----------|----------|----------|------------------------|
| Get Settings | `GET /settings` | `GET /api/v1/settings` | `assets/js/settings.js` |
| Update Settings | `PUT /settings` | `PUT /api/v1/settings` | `assets/js/settings.js` |
| Get User Preferences | `GET /settings/preferences` | `GET /api/v1/settings/preferences` | `assets/js/settings.js` |
| Update User Preferences | `PUT /settings/preferences` | `PUT /api/v1/settings/preferences` | `assets/js/settings.js` |

**Estimated Files:** 1 file
**Priority:** MEDIUM

---

### 7. Modules API

**Old Prefix:** `/modules/*`
**New Prefix:** `/api/v1/modules/*`

| Endpoint | Old Path | New Path | Frontend Files Affected |
|----------|----------|----------|------------------------|
| List Modules | `GET /modules` | `GET /api/v1/modules` | `assets/js/module-manager.js` |
| Get Module | `GET /modules/{id}` | `GET /api/v1/modules/{id}` | `assets/js/module-manager.js` |
| Activate Module | `POST /modules/{id}/activate` | `POST /api/v1/modules/{id}/activate` | `assets/js/module-manager.js` |
| Deactivate Module | `POST /modules/{id}/deactivate` | `POST /api/v1/modules/{id}/deactivate` | `assets/js/module-manager.js` |

**Estimated Files:** 1 file
**Priority:** MEDIUM

---

### 8. RBAC API

**Old Prefix:** `/rbac/*`
**New Prefix:** `/api/v1/rbac/*`

| Endpoint | Old Path | New Path | Frontend Files Affected |
|----------|----------|----------|------------------------|
| List Roles | `GET /rbac/roles` | `GET /api/v1/rbac/roles` | `assets/js/rbac-management.js` |
| Create Role | `POST /rbac/roles` | `POST /api/v1/rbac/roles` | `assets/js/rbac-management.js` |
| Update Role | `PUT /rbac/roles/{id}` | `PUT /api/v1/rbac/roles/{id}` | `assets/js/rbac-management.js` |
| Delete Role | `DELETE /rbac/roles/{id}` | `DELETE /api/v1/rbac/roles/{id}` | `assets/js/rbac-management.js` |
| List Permissions | `GET /rbac/permissions` | `GET /api/v1/rbac/permissions` | `assets/js/rbac-management.js` |
| Assign Permission | `POST /rbac/roles/{id}/permissions` | `POST /api/v1/rbac/roles/{id}/permissions` | `assets/js/rbac-management.js` |
| Remove Permission | `DELETE /rbac/roles/{id}/permissions/{perm_id}` | `DELETE /api/v1/rbac/roles/{id}/permissions/{perm_id}` | `assets/js/rbac-management.js` |
| List Groups | `GET /rbac/groups` | `GET /api/v1/rbac/groups` | `assets/js/rbac-management.js` |
| Create Group | `POST /rbac/groups` | `POST /api/v1/rbac/groups` | `assets/js/rbac-management.js` |

**Estimated Files:** 1 file
**Priority:** HIGH

---

### 9. Reports API

**Old Prefix:** `/reports/*`
**New Prefix:** `/api/v1/reports/*`

| Endpoint | Old Path | New Path | Frontend Files Affected |
|----------|----------|----------|------------------------|
| Create Report Definition | `POST /reports/definitions` | `POST /api/v1/reports/definitions` | `components/report-designer.js` |
| List Report Definitions | `GET /reports/definitions` | `GET /api/v1/reports/definitions` | `components/report-designer.js` |
| Get Report Definition | `GET /reports/definitions/{id}` | `GET /api/v1/reports/definitions/{id}` | `components/report-designer.js` |
| Update Report Definition | `PUT /reports/definitions/{id}` | `PUT /api/v1/reports/definitions/{id}` | `components/report-designer.js` |
| Delete Report Definition | `DELETE /reports/definitions/{id}` | `DELETE /api/v1/reports/definitions/{id}` | `components/report-designer.js` |
| Execute Report | `POST /reports/execute` | `POST /api/v1/reports/execute` | `components/report-designer.js` |
| Execute & Export | `POST /reports/execute/export` | `POST /api/v1/reports/execute/export` | `components/report-designer.js` |
| Get Execution History | `GET /reports/executions/{id}` | `GET /api/v1/reports/executions/{id}` | `components/report-designer.js` |
| Get Lookup Data | `GET /reports/lookup-data` | `GET /api/v1/reports/lookup-data` | `components/report-designer.js` |
| Create Schedule | `POST /reports/schedules` | `POST /api/v1/reports/schedules` | `components/report-designer.js` |
| List Templates | `GET /reports/templates` | `GET /api/v1/reports/templates` | `components/report-designer.js` |
| Create from Template | `POST /reports/templates/{id}/create` | `POST /api/v1/reports/templates/{id}/create` | `components/report-designer.js` |

**Estimated Files:** 1 file
**Priority:** HIGH

---

### 10. Dashboards API

**Old Prefix:** `/dashboards/*`
**New Prefix:** `/api/v1/dashboards/*`

| Endpoint | Old Path | New Path | Frontend Files Affected |
|----------|----------|----------|------------------------|
| List Dashboards | `GET /dashboards` | `GET /api/v1/dashboards` | `components/dashboard-designer.js` |
| Get Dashboard | `GET /dashboards/{id}` | `GET /api/v1/dashboards/{id}` | `components/dashboard-designer.js` |
| Create Dashboard | `POST /dashboards` | `POST /api/v1/dashboards` | `components/dashboard-designer.js` |
| Update Dashboard | `PUT /dashboards/{id}` | `PUT /api/v1/dashboards/{id}` | `components/dashboard-designer.js` |
| Delete Dashboard | `DELETE /dashboards/{id}` | `DELETE /api/v1/dashboards/{id}` | `components/dashboard-designer.js` |
| Clone Dashboard | `POST /dashboards/{id}/clone` | `POST /api/v1/dashboards/{id}/clone` | `components/dashboard-designer.js` |
| Create Page | `POST /dashboards/pages` | `POST /api/v1/dashboards/pages` | `components/dashboard-designer.js` |
| Update Page | `PUT /dashboards/pages/{id}` | `PUT /api/v1/dashboards/pages/{id}` | `components/dashboard-designer.js` |
| Delete Page | `DELETE /dashboards/pages/{id}` | `DELETE /api/v1/dashboards/pages/{id}` | `components/dashboard-designer.js` |
| Create Widget | `POST /dashboards/widgets` | `POST /api/v1/dashboards/widgets` | `components/dashboard-designer.js` |
| Update Widget | `PUT /dashboards/widgets/{id}` | `PUT /api/v1/dashboards/widgets/{id}` | `components/dashboard-designer.js` |
| Delete Widget | `DELETE /dashboards/widgets/{id}` | `DELETE /api/v1/dashboards/widgets/{id}` | `components/dashboard-designer.js` |
| Get Widget Data | `GET /dashboards/widgets/{id}/data` | `GET /api/v1/dashboards/widgets/{id}/data` | `components/dashboard-designer.js` |
| Create Share | `POST /dashboards/{id}/share` | `POST /api/v1/dashboards/{id}/share` | `components/dashboard-designer.js` |
| Create Snapshot | `POST /dashboards/{id}/snapshots` | `POST /api/v1/dashboards/{id}/snapshots` | `components/dashboard-designer.js` |

**Estimated Files:** 1 file
**Priority:** HIGH

---

### 11. Scheduler API

**Old Prefix:** `/scheduler/*`
**New Prefix:** `/api/v1/scheduler/*`

| Endpoint | Old Path | New Path | Frontend Files Affected |
|----------|----------|----------|------------------------|
| List Jobs | `GET /scheduler/jobs` | `GET /api/v1/scheduler/jobs` | `assets/js/scheduler-management.js` |
| Create Job | `POST /scheduler/jobs` | `POST /api/v1/scheduler/jobs` | `assets/js/scheduler-management.js` |
| Update Job | `PUT /scheduler/jobs/{id}` | `PUT /api/v1/scheduler/jobs/{id}` | `assets/js/scheduler-management.js` |
| Delete Job | `DELETE /scheduler/jobs/{id}` | `DELETE /api/v1/scheduler/jobs/{id}` | `assets/js/scheduler-management.js` |
| Trigger Job | `POST /scheduler/jobs/{id}/trigger` | `POST /api/v1/scheduler/jobs/{id}/trigger` | `assets/js/scheduler-management.js` |

**Estimated Files:** 1 file
**Priority:** MEDIUM

---

### 12. Menu API

**Old Prefix:** `/menu/*`
**New Prefix:** `/api/v1/menu/*`

| Endpoint | Old Path | New Path | Frontend Files Affected |
|----------|----------|----------|------------------------|
| Get User Menu | `GET /menu` | `GET /api/v1/menu` | `assets/js/menu-service.js` |
| List Menu Items | `GET /menu/items` | `GET /api/v1/menu/items` | `assets/js/menu-service.js` |
| Create Menu Item | `POST /menu/items` | `POST /api/v1/menu/items` | `assets/js/menu-service.js` |
| Update Menu Item | `PUT /menu/items/{id}` | `PUT /api/v1/menu/items/{id}` | `assets/js/menu-service.js` |
| Delete Menu Item | `DELETE /menu/items/{id}` | `DELETE /api/v1/menu/items/{id}` | `assets/js/menu-service.js` |

**Estimated Files:** 1-2 files
**Priority:** HIGH

---

### 13. Admin Security API

**Old Prefix:** `/admin/security/*`
**New Prefix:** `/api/v1/admin/security/*`

| Endpoint | Old Path | New Path | Frontend Files Affected |
|----------|----------|----------|------------------------|
| Get Security Policies | `GET /admin/security/policies` | `GET /api/v1/admin/security/policies` | `assets/js/security-admin.js` |
| Update Security Policies | `PUT /admin/security/policies` | `PUT /api/v1/admin/security/policies` | `assets/js/security-admin.js` |
| List Failed Logins | `GET /admin/security/failed-logins` | `GET /api/v1/admin/security/failed-logins` | `assets/js/security-admin.js` |
| List Active Sessions | `GET /admin/security/sessions` | `GET /api/v1/admin/security/sessions` | `assets/js/security-admin.js` |
| Terminate Session | `DELETE /admin/security/sessions/{id}` | `DELETE /api/v1/admin/security/sessions/{id}` | `assets/js/security-admin.js` |

**Estimated Files:** 1 file
**Priority:** MEDIUM

---

## Migration Checklist

### Phase 1: Update Service Files (1-2 days)

- [ ] Update `assets/js/auth.js` (CRITICAL - test immediately)
- [ ] Update `assets/js/companies.js`
- [ ] Update `assets/js/tenants.js`
- [ ] Update `assets/js/organization-hierarchy.js`
- [ ] Update `assets/js/metadata-service.js`
- [ ] Update `assets/js/data-service.js`
- [ ] Update `assets/js/entity-manager.js`
- [ ] Update `assets/js/audit-viewer.js`
- [ ] Update `assets/js/settings.js`
- [ ] Update `assets/js/module-manager.js`
- [ ] Update `assets/js/rbac-management.js`
- [ ] Update `components/report-designer.js`
- [ ] Update `components/dashboard-designer.js`
- [ ] Update `assets/js/scheduler-management.js`
- [ ] Update `assets/js/menu-service.js`
- [ ] Update `assets/js/security-admin.js`
- [ ] Update `assets/js/dynamic-table.js`
- [ ] Update `assets/js/dynamic-form.js`

### Phase 2: Update Component Files (1 day)

- [ ] Search for any hardcoded API paths in component files
- [ ] Update navigation components
- [ ] Update any other files with direct API calls

### Phase 3: Testing (1-2 days)

- [ ] Test authentication (login, logout, token refresh)
- [ ] Test organization management (companies, branches, departments, tenants)
- [ ] Test all CRUD operations for each entity
- [ ] Test report generation and execution
- [ ] Test dashboard widgets
- [ ] Test menu navigation
- [ ] Test RBAC permissions
- [ ] Test audit log viewing
- [ ] Test settings and preferences
- [ ] Regression testing on all modules

---

## Testing Recommendations

### 1. Start with Authentication
Test auth endpoints first, as all other endpoints depend on authentication working correctly.

### 2. Use Browser DevTools
Monitor Network tab for any 404 errors indicating missed API calls.

### 3. Check Console for Errors
Look for failed fetch/axios requests.

### 4. Automated Testing
Update any integration tests or E2E tests to use new paths.

---

## Rollback Plan

If issues are found, the old deprecated endpoints can be temporarily restored by:

1. Reverting the main.py changes
2. Re-adding the deprecated router registrations
3. However, this should only be done in emergency situations

**Recommended:** Complete the frontend migration as planned using this guide.

---

## Support

If you encounter any issues during migration:

1. Check this guide for the correct endpoint path
2. Verify the API is responding at the new path (test with curl or Postman)
3. Check browser console for specific error messages
4. Review the NO-CODE-PHASE2.md document for additional context

---

## Summary

- **Total APIs migrated:** 13
- **Total endpoints affected:** 100+
- **Estimated frontend files to update:** 18-20 files
- **Estimated migration time:** 3-5 days (including testing)
- **Breaking change:** Yes - all old paths removed
- **Backwards compatibility:** None - immediate action required

---

**Document Version:** 1.0
**Last Updated:** 2026-01-13
**Status:** Active - Migration Required
