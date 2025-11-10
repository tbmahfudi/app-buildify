# Security Frontend Components

This document explains how to integrate the security administration frontend components into your application.

## Components Overview

### 1. Security Administration Dashboard (`components/security-admin.js`)

**Purpose**: Unified admin interface for managing all security features.

**Features**:
- View and manage security policies
- Monitor and unlock locked accounts
- View and revoke active user sessions
- Audit login attempts
- Configure notification settings

**Required Permissions**:
- `security_policy:read:all` - View policies
- `security_policy:write:all` - Create/update policies
- `security:view_locked_accounts:all` - View locked accounts
- `security:unlock_account:all` - Unlock accounts
- `security:view_sessions:all` - View sessions
- `security:revoke_session:all` - Revoke sessions
- `security:view_login_attempts:all` - View login attempts
- `notification_config:read:all` - View notification config
- `notification_config:write:all` - Update notification config

**Usage**:
```html
<!-- Add to your admin page -->
<div id="security-admin-container"></div>

<script type="module">
  import { SecurityAdmin } from './components/security-admin.js';

  // Initialize
  window.securityAdmin = new SecurityAdmin();
  await securityAdmin.init('security-admin-container');
</script>
```

Or with vanilla JS:
```html
<script src="/components/security-admin.js"></script>
<script>
  // Component auto-creates global instance
  securityAdmin.init('security-admin-container');
</script>
```

### 2. Password Policy Display (`components/password-policy-display.js`)

**Purpose**: Show password requirements to users during registration or password change.

**Features**:
- Dynamically loads current password policy
- Displays requirements in user-friendly format
- Real-time password validation
- Visual feedback (checkmarks/errors)

**Usage**:

**In Registration Form**:
```html
<div class="mb-4">
  <label class="block text-sm font-medium mb-1">Password</label>
  <input type="password" id="password" class="w-full px-3 py-2 border rounded-lg">
  <div id="password-feedback" class="mt-2"></div>
</div>

<!-- Show requirements -->
<div id="password-requirements" class="mb-4"></div>

<script src="/components/password-policy-display.js"></script>
<script>
  // Initialize and show requirements
  passwordPolicyDisplay.init('password-requirements');

  // Attach real-time validation
  passwordPolicyDisplay.attachRealTimeValidation('password', 'password-feedback');
</script>
```

**In Password Change Form**:
```html
<form id="password-change-form">
  <div class="mb-4">
    <label>Current Password</label>
    <input type="password" id="current-password" required>
  </div>

  <div class="mb-4">
    <label>New Password</label>
    <input type="password" id="new-password" required>
    <div id="new-password-feedback" class="mt-2"></div>
  </div>

  <div id="password-requirements" class="mb-4"></div>

  <button type="submit">Change Password</button>
</form>

<script>
  passwordPolicyDisplay.init('password-requirements');
  passwordPolicyDisplay.attachRealTimeValidation('new-password', 'new-password-feedback');

  document.getElementById('password-change-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const newPassword = document.getElementById('new-password').value;
    const validation = passwordPolicyDisplay.validatePassword(newPassword);

    if (!validation.valid) {
      alert('Password does not meet requirements:\n' + validation.errors.join('\n'));
      return;
    }

    // Proceed with password change API call...
  });
</script>
```

## Integration Steps

### Step 1: Add Components to Your Project

1. Ensure components are in `/frontend/components/`:
   - `security-admin.js`
   - `password-policy-display.js`

2. Components are standalone vanilla JavaScript (no build step required).

### Step 2: Add Security Admin Page to Navigation

Update your navigation menu to include security administration (for users with appropriate permissions):

```javascript
// In your navigation rendering code
const menuItems = [
  // ... existing menu items
  {
    label: 'Security',
    icon: 'ph-shield-star',
    permission: 'security_policy:read:all',
    href: '/security-admin'
  }
];

// Render only if user has permission
menuItems.filter(item => {
  return !item.permission || currentUser.permissions.includes(item.permission);
});
```

### Step 3: Create Security Admin Page

Create `/frontend/pages/security-admin.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Security Administration</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@phosphor-icons/web@2.1.2/src/regular/style.css">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@phosphor-icons/web@2.1.2/src/duotone/style.css">
</head>
<body class="bg-gray-50">
  <div id="app" class="h-screen">
    <div id="security-admin-container"></div>
  </div>

  <script src="../components/security-admin.js"></script>
  <script>
    // Check authentication
    const token = localStorage.getItem('access_token');
    if (!token) {
      window.location.href = '/login';
    }

    // Initialize component
    securityAdmin.init('security-admin-container');
  </script>
</body>
</html>
```

### Step 4: Update Registration/Password Change Forms

**Registration Form** (`/frontend/pages/register.html`):

```html
<!-- Add password requirements display -->
<div id="password-requirements" class="mb-4"></div>

<div class="mb-4">
  <label class="block text-sm font-medium mb-1">Password</label>
  <input type="password" id="password" required
         class="w-full px-3 py-2 border rounded-lg">
  <div id="password-feedback" class="mt-2"></div>
</div>

<script src="../components/password-policy-display.js"></script>
<script>
  passwordPolicyDisplay.init('password-requirements');
  passwordPolicyDisplay.attachRealTimeValidation('password', 'password-feedback');

  // On form submit
  document.getElementById('register-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const password = document.getElementById('password').value;
    const validation = passwordPolicyDisplay.validatePassword(password);

    if (!validation.valid) {
      alert('Password does not meet requirements');
      return;
    }

    // Proceed with registration...
    const response = await fetch('http://localhost:8000/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: document.getElementById('email').value,
        password: password,
        // ... other fields
      })
    });

    // Handle response...
  });
</script>
```

### Step 5: Seed Security Permissions

Run the seeding script to create security roles and permissions:

```bash
cd backend
python -m app.scripts.seed_security_permissions
```

This creates:
- **security_admin** role: Full security management
- **security_viewer** role: Read-only monitoring
- **support_admin** role: Account unlock and session management

### Step 6: Assign Roles to Users

Assign security roles to appropriate users:

```sql
-- Example: Make a user a security admin
INSERT INTO user_roles (user_id, role_id)
SELECT 'user-uuid-here', id FROM roles WHERE code = 'security_admin';
```

Or use your user management UI to assign roles.

## API Endpoints Used

The frontend components use these backend endpoints:

### Security Policy Management
- `GET /admin/security/policies` - List all policies
- `POST /admin/security/policies` - Create policy
- `PUT /admin/security/policies/{id}` - Update policy
- `DELETE /admin/security/policies/{id}` - Delete policy

### Locked Accounts
- `GET /admin/security/locked-accounts` - List locked accounts
- `POST /admin/security/unlock-account` - Unlock account

### Sessions
- `GET /admin/security/sessions` - List active sessions
- `POST /admin/security/sessions/revoke` - Revoke session
- `POST /admin/security/sessions/revoke-all/{user_id}` - Revoke all user sessions

### Login Attempts
- `GET /admin/security/login-attempts` - List login attempts

### Notification Config
- `GET /admin/security/notification-config` - Get config
- `PUT /admin/security/notification-config/{id}` - Update config

### Password Policy (for users)
- `GET /auth/password-policy` - Get current user's password policy requirements

## Styling

Components use Tailwind CSS classes. Ensure Tailwind is loaded:

```html
<script src="https://cdn.tailwindcss.com"></script>
```

Components use Phosphor Icons:

```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@phosphor-icons/web@2.1.2/src/regular/style.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@phosphor-icons/web@2.1.2/src/duotone/style.css">
```

## Customization

### Changing API Base URL

Components default to `http://localhost:8000`. To change:

```javascript
// After initializing component
securityAdmin.apiBase = 'https://your-api-domain.com';
passwordPolicyDisplay.apiBase = 'https://your-api-domain.com';
```

### Custom Styling

Override Tailwind classes in your CSS:

```css
/* Custom security admin styles */
#security-admin-container {
  /* Your custom styles */
}

/* Custom password policy styles */
.password-requirements {
  /* Your custom styles */
}
```

## Testing

### Test Security Admin Component

1. Log in as a user with `security_admin` role
2. Navigate to `/security-admin`
3. Verify you can:
   - View existing policies
   - Create new tenant policy
   - Edit system default policy
   - View locked accounts (if any)
   - View active sessions
   - Revoke sessions

### Test Password Policy Display

1. Navigate to registration page
2. Enter password that violates policy
3. Verify real-time feedback shows errors
4. Enter valid password
5. Verify green checkmark appears
6. Submit form and verify backend validates

## Troubleshooting

### "Failed to load policies" error

**Cause**: Missing authentication token or insufficient permissions

**Solution**:
```javascript
// Check token exists
console.log(localStorage.getItem('access_token'));

// Check user permissions
console.log(currentUser.permissions);
```

Ensure user has required permissions (e.g., `security_policy:read:all`).

### Components not rendering

**Cause**: Container element not found

**Solution**:
```javascript
// Ensure container exists before initializing
const container = document.getElementById('security-admin-container');
if (container) {
  securityAdmin.init('security-admin-container');
} else {
  console.error('Container not found');
}
```

### Password validation not working

**Cause**: Policy not loaded

**Solution**:
```javascript
// Check if policy loaded
console.log(passwordPolicyDisplay.policy);

// Manually reload
await passwordPolicyDisplay.loadPolicy();
```

## Security Considerations

1. **Always validate on backend**: Client-side validation is for UX only
2. **Use HTTPS**: Never send passwords over HTTP
3. **Token security**: Store tokens in httpOnly cookies (better than localStorage)
4. **Permission checks**: Verify permissions on every request
5. **Input sanitization**: Backend must sanitize all inputs

## Next Steps

1. ✅ Install frontend components
2. ✅ Seed security permissions
3. ✅ Assign roles to users
4. ✅ Test security admin page
5. ✅ Update registration/password change forms
6. 🔄 Implement notification processor (backend)
7. 🔄 Add password expiration middleware (backend)
8. 🔄 Create password reset flow (backend + frontend)

## Support

For issues or questions:
- Review `backend/SECURITY_IMPLEMENTATION.md`
- Check backend logs for API errors
- Verify user permissions in database
- Test with Postman/curl to isolate frontend vs backend issues

---

**Version**: 1.0.0
**Last Updated**: 2025-11-10
