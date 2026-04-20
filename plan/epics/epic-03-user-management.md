# Epic 3 — User Management

> Full lifecycle management of user accounts: CRUD, profiles, group membership, and cross-company access.

---

## Feature 3.1 — User CRUD `[DONE]`

### Story 3.1.1 — User Creation by Admin `[DONE]`

#### Backend
*As an API, I want to create user accounts within a tenant, so that administrators can onboard members programmatically.*
- `POST /api/v1/users` accepts `{email, full_name, password, tenant_id, role_ids?, group_ids?}`
- Email unique within a tenant (DB unique constraint on `email` + `tenant_id`)
- Password hashed with bcrypt; plaintext never persisted
- Welcome notification queued via `NotificationService` on creation

#### Frontend
*As a tenant administrator on the users page, I want to open a "New User" drawer, fill in the user's details, assign a role, and save — all without leaving the page, so that onboarding is fast.*
- Route: `#/users` renders `frontend/assets/templates/users.html` + `users.js`
- "Add User" button opens a `FlexDrawer` (right panel) with fields:
  - Full Name (`FlexInput`, required)
  - Email (`FlexInput` type=email, required; inline duplicate-check on blur)
  - Password (`FlexInput` type=password with strength meter)
  - Role (multi-select `FlexSelect` loading `GET /rbac/roles`)
  - Group (multi-select `FlexSelect` loading `GET /rbac/groups`)
  - Status toggle (Active by default)
- On submit: spinner in drawer footer; on success drawer closes and new user appears at top of table with a green "New" badge that fades after 3 seconds
- Email duplicate: inline error "This email is already in use within this tenant" shown on blur without waiting for submit

---

### Story 3.1.2 — User Profile Management `[DONE]`

#### Backend
*As an API, I want to allow users to update their own profile fields, so that personal information stays current.*
- `PUT /api/v1/users/me` accepts `{full_name, phone, timezone, language, avatar_url}`
- `PUT /api/v1/users/{id}` restricted to tenant admin or superadmin (403 otherwise)

#### Frontend
*As a user on my profile page, I want to edit my name, phone, language, and timezone using a simple form with a live avatar preview, so that my profile reflects accurate information.*
- Route: `#/profile` renders `frontend/assets/templates/profile.html` + `profile-page.js`
- Profile page layout: left column — avatar circle (shows initials if no URL) with an "Edit" icon overlay; right column — form fields
- Avatar edit: clicking the circle opens a modal with a URL input and a preview of the image
- Language select: `FlexSelect` with flag icons; changing language immediately calls `i18next.changeLanguage()` so the page re-renders in the chosen language as a demo
- Timezone select: searchable `FlexSelect` with UTC offset shown next to each timezone name
- "Save Changes" button at bottom; unsaved changes show a yellow "You have unsaved changes" banner if user tries to navigate away

---

### Story 3.1.3 — User Activation and Deactivation `[DONE]`

#### Backend
*As an API, I want to toggle a user's active status and revoke their sessions on deactivation, so that access is immediately blocked without deleting the account.*
- `PATCH /api/v1/users/{id}` with `{is_active: false}` deactivates the user
- All active sessions for the user are terminated via `SessionManager.revoke_all_sessions(user_id)`
- Audit log records: `{action: "user.deactivated", actor: admin_id, target: user_id}`

#### Frontend
*As a tenant administrator on the user detail page, I want a toggle to activate or deactivate a user, with a confirmation dialog that warns me their active sessions will be terminated, so that I act deliberately.*
- User table row has a status toggle (`FlexBadge` "Active"/"Inactive" clickable)
- Clicking "Active" badge opens `FlexModal`: "Deactivate [User Name]? They will be immediately signed out of all active sessions."
- Confirm button in modal calls `PATCH /users/{id}`; badge updates in-place to "Inactive" (grey)
- Reactivation: clicking "Inactive" badge opens simpler modal "Reactivate [User Name]?" — no session warning needed
- Deactivated users shown with muted/grey row styling in the users table

---

### Story 3.1.4 — Admin-Initiated Password Reset `[DONE]`

#### Backend
*As an API, I want admins to trigger password resets for any user, so that locked-out users can be helped without superadmin involvement.*
- `POST /api/v1/users/{id}/reset-password` generates a `PasswordResetToken` and queues a reset email
- Superadmin can call for any user in any tenant; tenant admin only for their own tenant users

#### Frontend
*As a tenant administrator on the user detail page, I want a "Send Password Reset" button so that I can help users who cannot access the self-service reset flow.*
- User detail page `#/users/{id}` has a "Security" tab
- "Send Password Reset Email" button with a confirmation: "Send a password reset link to [email]?"
- On success: button shows a green checkmark and becomes disabled for 60 seconds to prevent duplicate sends; toast "Reset email sent to [email]"
- "Force Password Change on Next Login" toggle sets `force_password_change = true` on the user record; user is redirected to change-password screen after their next successful login

---

## Feature 3.2 — User Groups and Teams `[DONE]`

### Story 3.2.1 — Group Creation and Membership `[DONE]`

#### Backend
*As an API, I want to create user groups and manage their membership, so that role assignments can be managed at scale.*
- `POST /api/v1/rbac/groups` creates a group with `name`, `description`, `tenant_id`
- `POST /api/v1/rbac/groups/{id}/members` adds `{user_ids: []}` to the group
- `DELETE /api/v1/rbac/groups/{id}/members/{user_id}` removes a member
- Effective permissions for a user = union of all permissions from all groups they belong to

#### Frontend
*As a tenant administrator on the groups page, I want to create groups, set their roles, and add members using a searchable user picker, so that I can manage access for a whole department at once.*
- Route: `#/rbac` → "Groups" tab renders the groups list as `FlexCard` items
- "New Group" button opens a `FlexModal` with: Group Name, Description, Role assignment (multi-select)
- Group card shows: group name, role count, member count, "Manage" button
- "Manage" opens a `FlexDrawer` with two tabs: "Roles" and "Members"
  - Roles tab: checklist of all available roles with toggles
  - Members tab: list of current members with "Remove" icon per row; "Add Members" button opens a user search modal
- User search modal: `FlexInput` search bar; results show avatar + name + email; click to add; selected users shown as chips above the search bar

---

### Story 3.2.2 — Group Role Assignment `[DONE]`

#### Backend
*As an API, I want to assign roles to groups so that all group members inherit those permissions, so that role management scales with org size.*
- `POST /api/v1/rbac/groups/{id}/roles` accepts `{role_ids: []}` and creates `GroupRole` junction records
- `DELETE /api/v1/rbac/groups/{id}/roles/{role_id}` removes a role from the group
- Permission changes take effect on the next authenticated request (no re-login needed)

#### Frontend
*As a tenant administrator editing a group's roles, I want to see a list of all available roles with checkboxes and save my selection with a single click, so that role assignment is efficient.*
- Group detail drawer "Roles" tab shows: checklist of all tenant roles
- Each role row shows: role name, description, permission count badge
- Clicking a role name expands it to show its permission list
- "Select All" / "Deselect All" convenience buttons at the top
- "Save Roles" button at the bottom calls `POST /rbac/groups/{id}/roles` with the selected IDs; success toast: "Group roles updated"
- Dirty-state indicator: "Unsaved changes" yellow pill shown in the drawer header when selections differ from saved state
