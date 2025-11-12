# Fix: API Base URL Configuration for Frontend Components

## Problem

Several frontend components were hardcoding the API base URL as `http://localhost:8000`, which bypassed the nginx proxy and caused 404 errors when accessing backend endpoints.

### Error Messages
```
GET http://localhost:8000/admin/security/policies 404 (Not Found)
GET http://localhost:8000/admin/security/locked-accounts 404 (Not Found)
GET http://localhost:8000/admin/security/sessions?limit=50 404 (Not Found)
GET http://localhost:8000/admin/security/login-attempts?limit=50 404 (Not Found)
GET http://localhost:8000/admin/security/notification-config 404 (Not Found)
```

## Root Cause

### The Problem
1. Frontend components (`security-admin.js`, `password-policy-display.js`) were using:
   ```javascript
   this.apiBase = 'http://localhost:8000';
   ```

2. This directly targeted the backend container, bypassing nginx

3. Nginx is configured to proxy `/api/*` to the backend:
   ```nginx
   location /api/ {
     proxy_pass http://backend:8000/;
     ...
   }
   ```

4. Requests to `http://localhost:8000/admin/security/...` didn't match the `/api/` pattern, resulting in 404 errors

### Why This Matters
- In production, the backend container isn't directly accessible
- All API calls must go through nginx proxy
- The correct pattern is `/api/v1/...` which nginx proxies to the backend

## Solution

### Changed API Base URL
Updated both components to use the correct API base:

```javascript
// Before
this.apiBase = 'http://localhost:8000';

// After
this.apiBase = '/api/v1';
```

This ensures:
- Requests go through nginx proxy: `/api/v1/admin/security/policies`
- Nginx strips `/api/` and forwards to backend: `/v1/admin/security/policies`
- Backend router handles: `/admin/security/policies` (with `/v1` prefix from main.py)

### Fixed Token Retrieval
Also fixed token retrieval in `security-admin.js`:

```javascript
// Before (incorrect)
const token = localStorage.getItem('access_token');

// After (correct, matching api.js pattern)
const tokens = JSON.parse(localStorage.getItem('tokens') || '{}');
const token = tokens.access;
```

The tokens are stored as a JSON object by `api.js`:
```javascript
{
  "access": "eyJhbGc...",
  "refresh": "eyJhbGc..."
}
```

## Files Modified

1. **`frontend/components/security-admin.js`**
   - Changed `apiBase` from `http://localhost:8000` to `/api/v1`
   - Fixed token retrieval in 4 locations (lines 33, 368, 394, 430)

2. **`frontend/components/password-policy-display.js`**
   - Changed `apiBase` from `http://localhost:8000` to `/api/v1`

## Benefits

1. **Consistent API Access**: All components now use the same API pattern
2. **Works in Production**: Components work correctly when backend isn't directly accessible
3. **Follows Best Practices**: Uses nginx proxy as intended
4. **No More 404s**: Endpoints are correctly routed to the backend

## Testing

After deploying this change:

1. **Restart the containers** (if needed):
   ```bash
   docker-compose -f infra/docker-compose.dev.yml restart frontend backend
   ```

2. **Test the auth-policies page**:
   - Navigate to the auth-policies route
   - Check browser console - no more 404 errors
   - Verify security policies, locked accounts, sessions, etc. load correctly

3. **Check Network tab**:
   - API calls should go to `/api/v1/admin/security/...`
   - Should return 200 OK (or appropriate auth errors if permissions missing)

## Related Issues

This fix works together with the nginx static file fix (`FIX_NGINX_STATIC_FILES.md`):
1. Nginx fix: Returns 404 for missing static files (not HTML)
2. API fix: Ensures API calls use correct proxy path

## Notes

- The main `api.js` module already uses the correct pattern with `apiFetch()`
- These components (`security-admin.js`, `password-policy-display.js`) were using raw `fetch()` calls
- Future components should prefer using `apiFetch()` from `api.js` which handles:
  - Correct API base URL
  - Token management
  - Token refresh on 401
  - Tenant ID headers

## Recommended Follow-up

Consider refactoring these components to use `apiFetch()` from `api.js` instead of raw `fetch()` calls for:
- Automatic token refresh
- Consistent error handling
- Tenant ID management
- Less duplicated code
