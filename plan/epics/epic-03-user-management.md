# Epic 3 — User Management

> Full lifecycle management of user accounts: CRUD, profiles, group membership, and cross-company access.

---

## Feature 3.1 — User CRUD `[IN-PROGRESS]`

### Story 3.1.1 — User Creation by Admin `[OPEN]`

#### Backend
*As an API, I want to create user accounts within a tenant, so that administrators can onboard members programmatically.*
- `POST /api/v1/users` accepts `{email, full_name, password, tenant_id, role_ids?, group_ids?}`
- Email unique within a tenant (DB unique constraint on `email` + `tenant_id`)
- Password hashed with bcrypt; plaintext never persisted
- Welcome notification queued via `NotificationService` on creation

#### Frontend
*As a tenant administrator on the users page, I want to open a "New User" drawer, fill in the user's details, assign a role, and save — all without leaving the page, so that onboarding is fast.*
- Route: `#/users` → `users.html` + `users.js`
- Layout: FlexStack(direction=vertical) > page-header, content-area
  - page-header: FlexToolbar — "Users" title | "Add User" FlexButton(primary)
  - content-area: FlexSection — FlexDataGrid

- FlexDataGrid(server-side) — user list via GET /users
  - columns: Name, Email, Role (FlexBadge), Status (FlexBadge), Actions

- FlexDrawer(position=right, size=md) — "Add User" form, triggered by toolbar button
  - fields: Full Name (FlexInput, required) | Email (FlexInput, type=email, required, blur duplicate-check) | Password (FlexInput, type=password, strength meter) | Role (FlexSelect, multiple, loads GET /rbac/roles) | Group (FlexSelect, multiple, loads GET /rbac/groups) | Status (FlexCheckbox, default=active)
  - footer: Cancel | Save User (primary, spinner on submit)
  - on success: drawer closes; new user row at top of grid with FlexBadge(color=success) "New" fading after 3s
  - on blur email: if duplicate → inline error "This email is already in use within this tenant"

- Interactions:
  - click "Add User" button: opens FlexDrawer(position=right) "Add User" form
  - blur Email field: duplicate-check → inline error shown if email already in use (no submit required)
  - click Save User (drawer footer): POST /users → spinner → on success drawer closes; new row at top of grid

- States:
  - loading: FlexDataGrid shows skeleton rows while GET /users resolves
  - empty: "No users yet" + "Add User" FlexButton(primary)
  - error: FlexAlert(type=error) "Could not load users. Retry?" above the grid

---

### Story 3.1.2 — User Profile Management `[DONE]`

#### Backend
*As an API, I want to allow users to update their own profile fields, so that personal information stays current.*
- `PUT /api/v1/users/me` accepts `{full_name, phone, timezone, language, avatar_url}`
- `PUT /api/v1/users/{id}` restricted to tenant admin or superadmin (403 otherwise)

#### Frontend
*As a user on my profile page, I want to edit my name, phone, language, and timezone using a simple form with a live avatar preview, so that my profile reflects accurate information.*
- Route: `#/profile` → `profile.html` + `profile-page.js`
- Layout: FlexGrid(columns=2) > avatar-col, fields-col
  - avatar-col: FlexSection — avatar circle (initials fallback if no URL) with "Edit" icon overlay
  - fields-col: FlexStack(direction=vertical) — Full Name (FlexInput) | Phone (FlexInput) | Language (FlexSelect, flag icons) | Timezone (FlexSelect, searchable, UTC offset shown) | "Save Changes" FlexButton(primary)

- FlexModal(size=sm) — avatar edit, triggered by clicking avatar circle
  - fields: Avatar URL (FlexInput, type=url) | live image preview
  - footer: Cancel | Save Avatar (primary)

- Interactions:
  - click avatar circle: opens FlexModal(size=sm) with URL input and live image preview
  - change Language (FlexSelect): immediately calls i18next.changeLanguage() → page re-renders in chosen language
  - click "Save Changes": PUT /users/me → success toast "Profile updated" | error FlexAlert(type=error)
  - navigate away with unsaved changes: FlexAlert(type=warning) "You have unsaved changes" banner shown

- States:
  - saving: "Save Changes" button shows spinner; inputs disabled
  - dirty: yellow "You have unsaved changes" banner visible above the save button

---

### Story 3.1.3 — User Activation and Deactivation `[IN-PROGRESS]`

#### Backend
*As an API, I want to toggle a user's active status and revoke their sessions on deactivation, so that access is immediately blocked without deleting the account.*
- `PATCH /api/v1/users/{id}` with `{is_active: false}` deactivates the user
- All active sessions for the user are terminated via `SessionManager.revoke_all_sessions(user_id)`
- Audit log records: `{action: "user.deactivated", actor: admin_id, target: user_id}`

#### Frontend
*As a tenant administrator on the user detail page, I want a toggle to activate or deactivate a user, with a confirmation dialog that warns me their active sessions will be terminated, so that I act deliberately.*
- Route: `#/users` → `users.html` + `users.js` (operates on user list rows)

- FlexModal(size=sm) — deactivate confirm, triggered by clicking an "Active" status badge
  - body: "Deactivate [User Name]? They will be immediately signed out of all active sessions."
  - footer: Cancel | Deactivate (FlexButton, variant=danger)
  - on confirm: PATCH /users/{id} {is_active: false} → badge updates to FlexBadge(color=grey) "Inactive"; row text muted

- FlexModal(size=sm) — reactivate confirm, triggered by clicking an "Inactive" status badge
  - body: "Reactivate [User Name]?"
  - footer: Cancel | Reactivate (FlexButton, variant=primary)
  - on confirm: PATCH /users/{id} {is_active: true} → badge updates to FlexBadge(color=success) "Active"; row styling restored

- Interactions:
  - click "Active" FlexBadge on a row: opens deactivate FlexModal(size=sm)
  - click "Inactive" FlexBadge on a row: opens reactivate FlexModal(size=sm)
  - confirm deactivate: PATCH /users/{id} → badge → "Inactive" (grey); row styling → muted
  - confirm reactivate: PATCH /users/{id} → badge → "Active" (green); row styling → normal
  - keyboard Escape: closes open modal without any action

---

### Story 3.1.4 — Admin-Initiated Password Reset `[OPEN]`

#### Backend
*As an API, I want admins to trigger password resets for any user, so that locked-out users can be helped without superadmin involvement.*
- `POST /api/v1/users/{id}/reset-password` generates a `PasswordResetToken` and queues a reset email
- Superadmin can call for any user in any tenant; tenant admin only for their own tenant users

#### Frontend
*As a tenant administrator on the user detail page, I want a "Send Password Reset" button so that I can help users who cannot access the self-service reset flow.*
- Route: `#/users/{id}` → `user-detail.html` + `user-detail-page.js`
- Layout: FlexStack(direction=vertical) > page-header, tabs-area
  - page-header: FlexToolbar — FlexBreadcrumb | user name | status FlexBadge
  - tabs-area: FlexTabs — Overview | Activity | Security | …
    - Security tab: FlexSection — "Send Password Reset Email" FlexButton(primary) | "Force Password Change on Next Login" FlexCheckbox

- FlexModal(size=sm) — reset confirm, triggered by "Send Password Reset Email" button
  - body: "Send a password reset link to [email]?"
  - footer: Cancel | Send Reset Link (FlexButton, primary)
  - on confirm: POST /users/{id}/reset-password → button shows green checkmark + disabled for 60s; FlexAlert(type=success) "Reset email sent to [email]"

- Interactions:
  - click "Send Password Reset Email": opens confirm FlexModal(size=sm)
  - confirm send: POST /users/{id}/reset-password → button → green checkmark + disabled 60s → toast "Reset email sent to [email]"
  - toggle "Force Password Change on Next Login": PATCH /users/{id} {force_password_change: true/false}
  - keyboard Escape: closes modal without sending

- States:
  - reset-sent: button shows green checkmark; disabled for 60s; re-enables automatically after cooldown

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
- Route: `#/rbac` → `rbac.html` + `rbac-page.js` (Groups tab active)
- Layout: FlexStack(direction=vertical) > page-header, groups-grid
  - page-header: FlexToolbar — "Groups" title | FlexBreadcrumb | "New Group" FlexButton(primary)
  - groups-grid: FlexGrid(columns=3, gap=md) — FlexCard per group (group name, role count, member count, "Manage" button)

- FlexModal(size=sm) — "New Group" form, triggered by toolbar button
  - fields: Group Name (FlexInput, required) | Description (FlexTextarea) | Roles (FlexSelect, multiple)
  - footer: Cancel | Create Group (primary)

- FlexDrawer(position=right, size=md) — group detail, triggered by "Manage" on a card
  - tabs: Roles | Members
    - Roles tab: checklist of all tenant roles with toggles | "Save Roles" FlexButton(primary)
    - Members tab: current members list (avatar + name, "Remove" icon per row) | "Add Members" FlexButton

- FlexModal(size=md) — user search, triggered by "Add Members" inside the Members tab
  - fields: search bar (FlexInput, live search GET /users?search=[term])
  - results: avatar + name + email per row; click to select; selected users shown as chips above search bar
  - footer: Cancel | Add Selected (primary)

- Interactions:
  - click "New Group": opens FlexModal(size=sm) new-group form
  - click "Manage" on a group card: opens FlexDrawer(position=right) group detail
  - click "Add Members" (Members tab): opens FlexModal(size=md) user search
  - type in user search bar: GET /users?search=[term] → results list updates
  - click user in search results: adds to selected chips; click chip × to deselect
  - click "Remove" icon on member row: DELETE /rbac/groups/{id}/members/{user_id} → row removed
  - confirm "Add Selected": POST /rbac/groups/{id}/members → modal closes; members list refreshes

- States:
  - loading (groups grid): 6 skeleton cards while GET /rbac/groups resolves
  - empty (groups): illustration + "No groups yet" + "New Group" FlexButton(primary)
  - empty (Members tab): "No members in this group yet" + "Add Members" FlexButton

---

### Story 3.2.2 — Group Role Assignment `[DONE]`

#### Backend
*As an API, I want to assign roles to groups so that all group members inherit those permissions, so that role management scales with org size.*
- `POST /api/v1/rbac/groups/{id}/roles` accepts `{role_ids: []}` and creates `GroupRole` junction records
- `DELETE /api/v1/rbac/groups/{id}/roles/{role_id}` removes a role from the group
- Permission changes take effect on the next authenticated request (no re-login needed)

#### Frontend
*As a tenant administrator editing a group's roles, I want to see a list of all available roles with checkboxes and save my selection with a single click, so that role assignment is efficient.*
- Route: `#/rbac` → `rbac-page.js` — operates within the "Roles" tab of the group FlexDrawer (see Story 3.2.1)

- FlexDrawer(position=right, size=md) — Roles tab content (within group detail drawer)
  - toolbar: "Select All" | "Deselect All" FlexButton(ghost) | "Unsaved changes" FlexBadge(color=warning) [shown when dirty]
  - roles list: checklist — each row: FlexCheckbox | role name | description | permission count FlexBadge (clickable, expands to show permission list)
  - footer: Save Roles (FlexButton, primary)

- Interactions:
  - click role row checkbox: toggles selection; dirty indicator appears if selections differ from saved state
  - click role name: expands row to show permission list (accordion-style); click again to collapse
  - click "Select All": checks all role checkboxes
  - click "Deselect All": unchecks all role checkboxes
  - click "Save Roles": POST /rbac/groups/{id}/roles with selected IDs → success toast "Group roles updated" | error FlexAlert(type=error)

- States:
  - loading: checklist shows skeleton rows while GET /rbac/roles resolves
  - dirty: "Unsaved changes" FlexBadge(color=warning) visible in drawer header
  - saving: "Save Roles" button shows spinner; checkboxes disabled
