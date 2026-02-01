# Complete No-Code Module Creation Guide

**Date:** 2026-01-21 (Updated for Phase 4)
**Purpose:** Step-by-step guide to create a fully functional module using only the No-Code Platform
**Example Module:** Customer Support Ticket System
**Estimated Time:** 2-3 hours

---

## Table of Contents

1. [Introduction](#introduction)
2. [Module Overview](#module-overview)
3. [Prerequisites](#prerequisites)
4. [Phase 4: Module System Setup](#phase-4-module-system-setup)
5. [Step-by-Step Implementation](#step-by-step-implementation)
6. [Testing & Validation](#testing--validation)
7. [Going Live](#going-live)
8. [Advanced: Module Extensions](#advanced-module-extensions)
9. [Appendix](#appendix)

---

## Introduction

This guide demonstrates how to build a complete, production-ready **Customer Support Ticket System** using ONLY the No-Code Platform features. No backend coding required!

### What's New in Phase 4

With the **Module System Foundation** (Phase 4), you can now:
- ✅ Create **organized modules** per business domain
- ✅ Define **module dependencies** with version constraints
- ✅ Use **cross-module services** to access data from other modules
- ✅ **Extend other modules** by adding fields, UI tabs, and menu items
- ✅ **Version and publish** modules independently
- ✅ Export/import modules for reuse across tenants

### What You'll Build

A complete support ticket system with:
- **Module Definition** - Organized "Support" module with version control
- Custom data models (Tickets, Categories, SLA Policies)
- Automated workflows (ticket assignment, escalation)
- Business automation (SLA monitoring, notifications)
- Dynamic lookups (priority, status, categories)
- Auto-generated CRUD UI
- Reports and dashboards
- Custom pages for end-users
- **Optional:** Extend HR module to link tickets to employees

### Features You'll Use

✅ **Module Management** - Create and version your module
✅ **Data Model Designer** - Create 4 entities within the module
✅ **Lookup Configuration** - Configure dropdowns
✅ **Workflow Designer** - Ticket approval workflow
✅ **Automation System** - Auto-assignment & SLA alerts
✅ **Auto-Generated UI** - Instant CRUD interfaces
✅ **Report Designer** - Ticket analytics
✅ **Dashboard Designer** - Support metrics dashboard
✅ **Menu Management** - Navigation structure
✅ **Extension Framework** - Extend other modules
✅ **Page Builder** (Optional) - Custom ticket portal

---

## Module Overview

### Business Requirements

**Scenario:** Your company needs a customer support ticket system where:
1. Customers can submit support tickets
2. Tickets are automatically assigned to support teams
3. High-priority tickets are escalated
4. SLA violations trigger alerts
5. Managers can track ticket metrics
6. Approval is required for refund requests
7. **New:** Link tickets to employees from HR module (via extension)

### Module Architecture (Phase 4)

```
┌─────────────────────────────────────────────────────────┐
│  MODULE: Support Ticket System (v1.0.0)                 │
│  Table Prefix: support                                  │
│  Status: Active                                         │
│  Dependencies: None                                     │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  DATA LAYER (4 Entities)                                │
│  ├── SupportTicket (support_tickets)                    │
│  ├── TicketCategory (support_categories)                │
│  ├── TicketComment (support_comments)                   │
│  └── SLAPolicy (support_sla_policies)                   │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  BUSINESS LOGIC                                         │
│  ├── Workflow: Refund Approval Process                  │
│  ├── Automation: Auto-assign new tickets                │
│  ├── Automation: SLA monitoring & escalation            │
│  └── Automation: Send notification on status change     │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  PRESENTATION LAYER                                     │
│  ├── Auto-Generated CRUD UI (list, create, edit)        │
│  ├── Reports: Ticket Analytics, SLA Report              │
│  ├── Dashboard: Support Metrics Overview                │
│  └── Custom Page: Customer Ticket Portal (Optional)     │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  EXTENSIONS (Optional)                                  │
│  └── Extend HR Employee entity with support fields      │
│      (total_tickets, avg_resolution_time)               │
└─────────────────────────────────────────────────────────┘
```

---

## Prerequisites

### Required Permissions

Ensure you have these permissions:
- `modules:create:tenant` - **NEW:** Create modules
- `modules:publish:tenant` - **NEW:** Publish modules
- `data-model:create:tenant` - Create entities
- `workflows:create:tenant` - Create workflows
- `automations:create:tenant` - Create automation rules
- `lookups:create:tenant` - Configure lookups
- `reports:create:tenant` - Create reports
- `dashboards:create:tenant` - Create dashboards
- `menu:manage:tenant` - Manage menu items

### Platform Status Check

Before starting, verify:
1. ✅ **Phase 1 Complete** (Data Model, Workflow, Automation, Lookups)
2. ✅ **Phase 2 Complete** (Runtime CRUD, Auto-UI, Integration)
3. ✅ **Phase 3 Priority 1-3 Complete** (Menu, Report/Dashboard Designers)
4. ✅ **Phase 4 Complete** (Module System Foundation) - **NEW!**

You can verify by checking:
- "No-Code Platform" menu exists and contains all submenus
- "Module Management" menu item exists (Phase 4)
- Database migrations are up to date: `alembic upgrade head`

### Database Migrations

**IMPORTANT:** Before creating modules, ensure Phase 4 migrations have been applied:

```bash
cd /home/user/app-buildify/backend
alembic upgrade head
```

Expected output should include:
```
INFO  [alembic.runtime.migration] Running upgrade -> pg_nocode_module_system
INFO  [alembic.runtime.migration] Running upgrade -> pg_module_services
INFO  [alembic.runtime.migration] Running upgrade -> pg_module_extensions
```

---

## Phase 4: Module System Setup

### Step 0.1: Create the Support Module

**Navigation:** Module Management (or direct URL: `/nocode-modules.html`)

**Why Module First?**
In Phase 4, all no-code components (entities, workflows, automations, etc.) must belong to a module. This ensures proper organization, versioning, and dependency management.

#### Create Module Wizard

1. **Navigate to Module Management**
   - Click "Module Management" in the main navigation
   - Or go directly to: `http://your-domain/nocode-modules.html`

2. **Click "Create Module"**

#### Step 1: Basic Info

| Field | Value | Description |
|-------|-------|-------------|
| **Module Name** | `support_management` | Technical name (lowercase, underscore) |
| **Display Name** | `Support Management` | User-friendly name |
| **Description** | `Customer support ticket system with SLA tracking and automated workflows` | Brief module description |
| **Category** | `Support` | Business domain category |
| **Tags** | `tickets, support, sla, customer-service` | Comma-separated tags |

Click **"Next"** →

#### Step 2: Table Prefix

| Field | Value | Notes |
|-------|-------|-------|
| **Table Prefix** | `support` | • Max 10 characters<br>• Lowercase only<br>• No underscores<br>• Must be unique |

**How it works:**
- All tables in this module will be prefixed with `support_`
- Example tables: `support_tickets`, `support_categories`, `support_comments`
- This ensures no naming conflicts with other modules

The system will validate the prefix in real-time:
- ✅ **Green checkmark** = Available
- ❌ **Red X** = Already in use or invalid format

Click **"Next"** →

#### Step 3: Visual Config

**Module Icon:**
- Select icon: `headset` (support/help desk icon)
- Or choose any icon from the picker

**Module Color:**
- Select color: Blue (`#3b82f6`)
- Or choose any color from the picker

**Preview:**
You'll see a live preview of how the module will appear in lists and menus.

Click **"Next"** →

#### Step 4: Review & Create

Review all information:
- ✅ Module Name: `support_management`
- ✅ Display Name: `Support Management`
- ✅ Category: Support
- ✅ Table Prefix: `support`
- ✅ Icon: headset
- ✅ Color: Blue

Click **"Create Module"** ✨

**Result:**
- Module created with status: **Draft**
- Version: **1.0.0**
- You can now add entities, workflows, and other components to this module

---

### Step 0.2: Understanding Module Status

Your module has these lifecycle stages:

| Status | Description | Can Edit? | Visible to Users? |
|--------|-------------|-----------|-------------------|
| **Draft** | Initial state, under development | ✅ Yes | ❌ No |
| **Active** | Published and ready for use | ⚠️ Limited | ✅ Yes |
| **Deprecated** | Old version, still works but discouraged | ❌ No | ✅ Yes (with warning) |
| **Archived** | Inactive, kept for records | ❌ No | ❌ No |

**Current Status:** Your module is in **Draft** mode. You can freely add and modify components. When ready, you'll publish it to make it active.

---

## Step-by-Step Implementation

### Phase 1: Data Model Design (30 minutes)

#### Step 1.1: Create SupportTicket Entity

**Navigation:** No-Code Platform > Data & Schema > Data Model Designer

1. **Click "Create New Entity"**

2. **Basic Information:**
   - **Module:** `Support Management` ⬅️ **NEW: Select your module!**
   - **Entity Name:** `SupportTicket`
   - **Display Name:** `Support Ticket`
   - **Table Name:** `support_tickets` (auto-prefixed: will become `support_tickets`)
   - **Description:** `Customer support ticket with SLA tracking`
   - **Icon:** `ticket` (or choose from Phosphor icons)

> **💡 Phase 4 Note:** The table name will automatically be prefixed with `support_` because it belongs to the Support module. You just enter the entity name part.

3. **Add Fields:** Click "Add Field" for each field below

   > **💡 Note:** All entities automatically include these system fields (you don't need to add them):
   > - `id` (UUID, Primary Key) - Unique identifier for each record
   > - `created_at` (DateTime) - Timestamp when record was created
   > - `updated_at` (DateTime) - Timestamp when record was last updated
   > - `created_by` (UUID, FK to users) - User who created the record
   > - `updated_by` (UUID, FK to users) - User who last updated the record
   > - `is_deleted` (Boolean) - Soft delete flag

   | Field Name | Display Name | Type | Required | Settings |
   |------------|--------------|------|----------|----------|
   | `ticket_number` | Ticket Number | String | Yes | Max Length: 20, Unique: Yes, Indexed: Yes |
   | `subject` | Subject | String | Yes | Max Length: 200 |
   | `description` | Description | Text | Yes | |
   | `priority` | Priority | Select | Yes | Options: Low, Medium, High, Critical |
   | `status` | Status | Select | Yes | Options: New, Open, In Progress, Pending, Resolved, Closed |
   | `category_id` | Category | Reference | No | Entity: TicketCategory (will create later) |
   | `customer_name` | Customer Name | String | Yes | Max Length: 100 |
   | `customer_email` | Customer Email | Email | Yes | |
   | `customer_phone` | Customer Phone | Phone | No | |
   | `assigned_to` | Assigned To | Reference | No | Entity: User |
   | `assigned_team` | Assigned Team | String | No | Max Length: 50 |
   | `sla_due_date` | SLA Due Date | DateTime | No | |
   | `resolution_notes` | Resolution Notes | Text | No | |
   | `estimated_hours` | Estimated Hours | Decimal | No | Precision: 5,2 |
   | `actual_hours` | Actual Hours | Decimal | No | Precision: 5,2 |
   | `tags` | Tags | JSON | No | |
   | `attachments` | Attachments | JSON | No | |

4. **Add Relationships:**

   > **💡 Understanding Relationships:**
   > - **Source Entity** = Current entity (SupportTicket) - the "one" side
   > - **Target Entity** = Related entity (TicketComment) - the "many" side
   > - **Target Field** = Reference field in target entity that links back to source
   > - The relationship represents: `SupportTicket.id` (auto-created) ← `TicketComment.ticket_id` (reference field)

   - Click "Add Relationship"
   - **Relationship Name:** `comments` (technical name)
   - **Relationship Type:** One-to-Many
   - **Target Entity:** `TicketComment` (will create later)
   - **Source Field:** Leave empty (SupportTicket doesn't have a FK to comments)
   - **Target Field:** `ticket_id` (the reference field in TicketComment that points to SupportTicket.id)
   - **Description:** "Comments and updates on this ticket"

   > **Note:** You'll create the TicketComment entity with the `ticket_id` reference field in Step 1.3 below.

5. **Field Indexing:**

   > **💡 Current Limitation:**
   > - Individual field indexes can be set when adding/editing fields (checkbox "Indexed")
   > - Composite indexes (multi-column indexes like `idx_ticket_status_priority`) are not yet available through the UI
   > - For now, mark frequently queried fields as "Indexed" (already done for `ticket_number`)
   > - Composite indexes can be added manually via SQL or will be available in a future platform update

   Fields already marked as indexed:
   - ✅ `ticket_number` (unique index)
   - ✅ `category_id` (FK index, auto-created)
   - ✅ `assigned_to` (FK index, auto-created)

   **Optional:** Mark these fields as indexed for better query performance:
   - `status` - frequently used in filters
   - `priority` - frequently used in filters
   - `sla_due_date` - used in SLA monitoring queries

   To mark a field as indexed: Edit the field > Check "Indexed" > Save

6. **Save as Draft** (Don't publish yet)

---

#### Step 1.2: Create TicketCategory Entity

1. **Click "Create New Entity"**

2. **Basic Information:**
   - **Entity Name:** `TicketCategory`
   - **Display Name:** `Ticket Category`
   - **Table Name:** `ticket_categories`
   - **Description:** `Categorization for support tickets`

3. **Add Fields:**

   | Field Name | Display Name | Type | Required | Settings |
   |------------|--------------|------|----------|----------|
   | `name` | Category Name | String | Yes | Max Length: 100, Unique: Yes |
   | `description` | Description | Text | No | |
   | `default_sla_hours` | Default SLA (Hours) | Integer | Yes | Default: 24 |
   | `assigned_team` | Default Team | String | No | Max Length: 50 |
   | `is_active` | Is Active | Boolean | Yes | Default: True |
   | `color_code` | Color Code | String | No | Max Length: 7 (hex color) |

4. **Save as Draft**

---

#### Step 1.3: Create TicketComment Entity

1. **Click "Create New Entity"**

2. **Basic Information:**
   - **Entity Name:** `TicketComment`
   - **Display Name:** `Ticket Comment`
   - **Table Name:** `ticket_comments`
   - **Description:** `Comments and updates on support tickets`

3. **Add Fields:**

   | Field Name | Display Name | Type | Required | Settings |
   |------------|--------------|------|----------|----------|
   | `ticket_id` | Ticket | Reference | Yes | Entity: SupportTicket |
   | `comment_text` | Comment | Text | Yes | |
   | `comment_type` | Type | Select | Yes | Options: Internal Note, Customer Reply, Status Update |
   | `is_public` | Visible to Customer | Boolean | Yes | Default: False |
   | `attachments` | Attachments | JSON | No | |

   > **💡 About the ticket_id Reference Field:**
   > - This creates a foreign key relationship: `TicketComment.ticket_id` → `SupportTicket.id`
   > - Each comment must belong to exactly one ticket (Required = Yes)
   > - This is the "target field" referenced in the relationship we created in Step 1.1.4
   > - Database will automatically create an index on `ticket_id` for performance
   > - Database enforces referential integrity (can't create comment for non-existent ticket)

4. **Save as Draft**

---

#### Step 1.4: Create SLAPolicy Entity

1. **Click "Create New Entity"**

2. **Basic Information:**
   - **Entity Name:** `SLAPolicy`
   - **Display Name:** `SLA Policy`
   - **Table Name:** `sla_policies`
   - **Description:** `Service Level Agreement policies`

3. **Add Fields:**

   | Field Name | Display Name | Type | Required | Settings |
   |------------|--------------|------|----------|----------|
   | `name` | Policy Name | String | Yes | Max Length: 100 |
   | `priority` | Priority | Select | Yes | Options: Low, Medium, High, Critical |
   | `response_time_hours` | Response Time (Hours) | Integer | Yes | |
   | `resolution_time_hours` | Resolution Time (Hours) | Integer | Yes | |
   | `escalation_hours` | Escalation After (Hours) | Integer | Yes | |
   | `is_active` | Is Active | Boolean | Yes | Default: True |

4. **Save as Draft**

---

#### Step 1.5: Generate and Run Migrations

1. **Review All Entities:**
   - Go to Data Model Designer
   - Verify all 4 entities are created

2. **Generate Migration for Each Entity:**
   - Select `TicketCategory` entity
   - Click "Generate Migration"
   - Review the SQL preview
   - Click "Confirm & Save Migration"
   - **Repeat for:** `SLAPolicy`, `SupportTicket`, `TicketComment` (in this order due to foreign key dependencies)

> **⚠️ IMPORTANT - Migration Order:**
> The order matters because of foreign key relationships:
> - `TicketCategory` and `SLAPolicy` have no dependencies (can be first)
> - `SupportTicket` references `TicketCategory` (must be after TicketCategory)
> - `TicketComment` has a **required** foreign key to `SupportTicket` via `ticket_id` (must be last)
>
> **Correct Order:** TicketCategory → SLAPolicy → SupportTicket → TicketComment

3. **Run Migrations:**
   - Click "Migration History" tab
   - Select each pending migration **in the same order**
   - Click "Run Migration" for each one
   - Verify success message after each migration

4. **Publish All Entities:**
   - After all migrations complete successfully
   - Each entity should now have status "Published"
   - This makes them available for runtime CRUD operations

**✅ Checkpoint:** You should now have 4 database tables created and visible in the Data Model Designer.

---

### Phase 2: Lookup Configuration (15 minutes)

**Navigation:** No-Code Platform > Business Logic > Lookup Configuration

> **💡 Understanding the Create Lookup Form:**
> The lookup creation form dynamically shows different fields based on the selected **Source Type**:
> - **Entity (Database Table):** Shows entity dropdown, display field, and value field inputs
> - **Static List:** Shows a JSON textarea for entering static options
> - **Custom Query:** Shows SQL query textarea and query parameters
> - **External API:** Shows API endpoint, method, headers, and response mapping fields

#### Step 2.1: Create Priority Lookup (Static List)

1. **Click "Create Lookup"**

2. **Basic Information:**
   | Field | Value |
   |-------|-------|
   | **Configuration Name** | `ticket_priority` |
   | **Display Label** | `Ticket Priority` |
   | **Description** | `Priority levels for tickets` |
   | **Source Type** | `Static List` |

3. **Static Options (JSON):**
   When you select "Static List" as the source type, a JSON textarea appears. Enter the following:
   ```json
   [
     { "value": "low", "label": "Low", "color": "#10b981" },
     { "value": "medium", "label": "Medium", "color": "#f59e0b" },
     { "value": "high", "label": "High", "color": "#ef4444" },
     { "value": "critical", "label": "Critical", "color": "#dc2626" }
   ]
   ```

   > **💡 Static Options Format:**
   > Each option must have `value` and `label` properties. Optional properties include:
   > - `color` - Hex color code for visual styling (e.g., badges)
   > - `icon` - Phosphor icon name for display
   > - `metadata` - Any additional data as JSON object

4. **Settings (checkboxes at bottom):**
   - ☑️ **Enable Search:** Check this box
   - ☑️ **Enable Caching:** Check this box

5. **Click "Create Lookup"**

---

#### Step 2.2: Create Status Lookup (Static List)

1. **Click "Create Lookup"**

2. **Basic Information:**
   | Field | Value |
   |-------|-------|
   | **Configuration Name** | `ticket_status` |
   | **Display Label** | `Ticket Status` |
   | **Description** | `Ticket workflow status values` |
   | **Source Type** | `Static List` |

3. **Static Options (JSON):**
   ```json
   [
     { "value": "new", "label": "New", "icon": "spark" },
     { "value": "open", "label": "Open", "icon": "folder-open" },
     { "value": "in_progress", "label": "In Progress", "icon": "spinner" },
     { "value": "pending", "label": "Pending", "icon": "clock" },
     { "value": "resolved", "label": "Resolved", "icon": "check-circle" },
     { "value": "closed", "label": "Closed", "icon": "lock" }
   ]
   ```

4. **Settings:**
   - ☑️ **Enable Search:** Check this box
   - ☑️ **Enable Caching:** Check this box

5. **Click "Create Lookup"**

---

#### Step 2.3: Create Category Lookup (Entity/Dynamic)

1. **Click "Create Lookup"**

2. **Basic Information:**
   | Field | Value |
   |-------|-------|
   | **Configuration Name** | `ticket_categories` |
   | **Display Label** | `Ticket Categories` |
   | **Description** | `Dynamic categories from database` |
   | **Source Type** | `Entity (Database Table)` |

3. **Entity Configuration:**
   When you select "Entity (Database Table)" as source type, entity-specific fields appear:

   | Field | Value |
   |-------|-------|
   | **Source Entity** | Select `TicketCategory` from dropdown |
   | **Display Field** | `name` |
   | **Value Field** | `id` |

   > **💡 Entity Lookups:**
   > - **Source Entity:** The database table to fetch options from
   > - **Display Field:** The field shown to users (usually `name`)
   > - **Value Field:** The field stored when selected (usually `id`)

4. **Settings:**
   - ☑️ **Enable Search:** Check this box
   - ☑️ **Enable Caching:** Check this box

5. **Click "Create Lookup"**

> **Note:** Advanced entity options like filters (`is_active = true`), sorting, and additional return fields can be configured by editing the lookup after creation.

---

#### Step 2.4: Create Team Lookup (Static List)

1. **Click "Create Lookup"**

2. **Basic Information:**
   | Field | Value |
   |-------|-------|
   | **Configuration Name** | `support_teams` |
   | **Display Label** | `Support Teams` |
   | **Description** | `Available support team assignments` |
   | **Source Type** | `Static List` |

3. **Static Options (JSON):**
   ```json
   [
     { "value": "tier1", "label": "Tier 1 Support" },
     { "value": "tier2", "label": "Tier 2 Support" },
     { "value": "technical", "label": "Technical Team" },
     { "value": "billing", "label": "Billing Team" },
     { "value": "management", "label": "Management" }
   ]
   ```

4. **Settings:**
   - ☑️ **Enable Search:** Check this box
   - ☑️ **Enable Caching:** Check this box

5. **Click "Create Lookup"**

**✅ Checkpoint:** You should have 4 lookups configured. Test by clicking "Test" button on any lookup card to verify data retrieval.

---

### Phase 3: Workflow Design (30 minutes)

**Navigation:** No-Code Platform > Business Logic > Workflow Designer

> **💡 Understanding the Workflow Designer:**
> The Workflow Designer provides a visual canvas for creating approval workflows. Key concepts:
> - **States:** Nodes in the workflow (Start, Intermediate, Approval, Condition, End)
> - **Transitions:** Connections between states with button labels
> - **Trigger Types:** Manual, Automatic, or Scheduled workflow initiation

#### Step 3.1: Create Refund Approval Workflow

1. **Click "Create Workflow"**

2. **Basic Information:**
   | Field | Value |
   |-------|-------|
   | **Workflow Name** | `ticket_refund_approval` |
   | **Display Label** | `Ticket Refund Approval` |
   | **Description** | `Approval process for ticket refunds` |
   | **Category** | `Approvals` |
   | **Target Entity** | Select `SupportTicket` from dropdown |
   | **Trigger Type** | `Automatic (On Entity Change)` |

3. **Trigger Conditions:**
   When you select "Automatic" trigger type, the trigger conditions section appears:

   | Field | Value |
   |-------|-------|
   | **Field to Monitor** | `tags` |
   | **Condition Operator** | `Contains` |
   | **Value** | `refund_requested` |

   > **💡 How Automatic Triggers Work:**
   > The workflow will automatically start when a SupportTicket is created or updated AND the `tags` field contains `refund_requested`. This is how workflows respond to entity changes without manual intervention.

4. **Click "Create Workflow"**

   The workflow is created with an empty canvas. You'll now see the workflow detail view with the visual canvas.

---

#### Step 3.2: Add Workflow States

Click **"Add State"** button to add each state.

> **💡 Add State Form Fields:**
> The Add State form shows different fields based on the selected State Type:
>
> | Field | Description | Shown For |
> |-------|-------------|-----------|
> | **State Type** | Type of state (start, intermediate, end, approval, condition) | All |
> | **State Name** | Technical name (lowercase, underscore) | intermediate, approval, condition |
> | **Label** | Display name shown in UI | intermediate, approval, condition |
> | **Description** | Brief state description | intermediate, approval, condition |
> | **Color** | Hex color code for visual styling | intermediate, approval, condition |
> | **SLA Hours** | Service level agreement time limit | intermediate, approval, condition |
> | **Final State** | Marks this as a terminal state | intermediate, approval, condition |
> | **Requires Approval** | Shows approval configuration | intermediate, approval, condition |
>
> **Approval Configuration** (shown when "Requires Approval" is checked):
> | Field | Description |
> |-------|-------------|
> | **Approval Type** | any, all, majority, or sequential |
> | **Approver Roles** | Comma-separated list of roles |
> | **Auto-approve after (hours)** | Auto-approve if not actioned within time |

**State 1: Start**
| Field | Value |
|-------|-------|
| **State Type** | `start` |

> **💡 Auto-Configuration:** When you select "Start" as the State Type, the form automatically configures the state with:
> - State Name: `start`
> - Label: `Start`
> - Description: `Workflow entry point`
>
> No additional input is required. Click "Add State" to create.

**State 2: Supervisor Review**
| Field | Value |
|-------|-------|
| **State Type** | `approval` |
| **State Name** | `supervisor_review` |
| **Label** | `Supervisor Review` |
| **Description** | `Supervisor reviews refund request` |
| **Color** | (optional) Leave blank or enter hex color e.g., `#8B5CF6` |
| **SLA Hours** | `4` |
| **Final State** | ☐ Leave unchecked |
| **Requires Approval** | ☑️ Check this (auto-checked for approval type) |

When "Requires Approval" is checked, the Approval Configuration section appears:
| Field | Value |
|-------|-------|
| **Approval Type** | `Sequential` |
| **Approver Roles** | `Support Supervisor` |
| **Auto-approve after (hours)** | (optional) Leave blank for no auto-approval |

**State 3: Manager Approval**
| Field | Value |
|-------|-------|
| **State Type** | `approval` |
| **State Name** | `manager_approval` |
| **Label** | `Manager Approval` |
| **Description** | `Manager final approval for refund` |
| **Color** | (optional) Leave blank or enter hex color |
| **SLA Hours** | `8` |
| **Final State** | ☐ Leave unchecked |
| **Requires Approval** | ☑️ Check this |

Approval Configuration:
| Field | Value |
|-------|-------|
| **Approval Type** | `Sequential` |
| **Approver Roles** | `Support Manager` |
| **Auto-approve after (hours)** | (optional) Leave blank |

**State 4: Process Refund**
| Field | Value |
|-------|-------|
| **State Type** | `intermediate` |
| **State Name** | `process_refund` |
| **Label** | `Process Refund` |
| **Description** | `Billing team processes the refund` |
| **Color** | (optional) Leave blank or enter hex color |
| **SLA Hours** | (optional) Leave blank |
| **Final State** | ☐ Leave unchecked |
| **Requires Approval** | ☐ Leave unchecked |

**State 5: End**
| Field | Value |
|-------|-------|
| **State Type** | `end` |

> **💡 Auto-Configuration:** When you select "End" as the State Type, the form automatically configures the state with:
> - State Name: `end`
> - Label: `End`
> - Description: `Workflow completion`
> - Final State: Checked (automatically)
>
> No additional input is required. Click "Add State" to create.

> **💡 State Types & Colors:**
> - **Start** (Green): Entry point of workflow
> - **Intermediate** (Blue): Regular processing step
> - **Approval** (Purple): Requires user approval
> - **Condition** (Yellow): Decision/branching point
> - **End** (Red): Terminal state

---

#### Step 3.3: Add Transitions

Click **"Add Transition"** to connect states.

> **💡 Add Transition Form Fields:**
> | Field | Description | Required |
> |-------|-------------|----------|
> | **Transition Name** | Technical name (lowercase, underscore) | Yes |
> | **From State** | Starting state for this transition | Yes |
> | **To State** | Destination state for this transition | Yes |
> | **Button Label** | Text shown on the action button | Yes |
> | **Condition Type** | `Always`, `Conditional`, or `Approval Required` | No (default: Always) |
> | **Button Style** | `Primary` (Blue), `Success` (Green), `Danger` (Red), `Warning` (Yellow) | No (default: Primary) |

**Transition 1: Start to Supervisor**
| Field | Value |
|-------|-------|
| **Transition Name** | `to_supervisor` |
| **From State** | `Start` |
| **To State** | `Supervisor Review` |
| **Button Label** | `Submit for Review` |
| **Condition Type** | `Always` |
| **Button Style** | `Primary (Blue)` |

**Transition 2: Supervisor Approves**
| Field | Value |
|-------|-------|
| **Transition Name** | `supervisor_approved` |
| **From State** | `Supervisor Review` |
| **To State** | `Manager Approval` |
| **Button Label** | `Approve` |
| **Condition Type** | `Approval Required` |
| **Button Style** | `Success (Green)` |

**Transition 3: Supervisor Rejects**
| Field | Value |
|-------|-------|
| **Transition Name** | `supervisor_rejected` |
| **From State** | `Supervisor Review` |
| **To State** | `End` |
| **Button Label** | `Reject` |
| **Condition Type** | `Approval Required` |
| **Button Style** | `Danger (Red)` |

**Transition 4: Manager Approves**
| Field | Value |
|-------|-------|
| **Transition Name** | `manager_approved` |
| **From State** | `Manager Approval` |
| **To State** | `Process Refund` |
| **Button Label** | `Approve` |
| **Condition Type** | `Approval Required` |
| **Button Style** | `Success (Green)` |

**Transition 5: Manager Rejects**
| Field | Value |
|-------|-------|
| **Transition Name** | `manager_rejected` |
| **From State** | `Manager Approval` |
| **To State** | `End` |
| **Button Label** | `Reject` |
| **Condition Type** | `Approval Required` |
| **Button Style** | `Danger (Red)` |

**Transition 6: Refund Complete**
| Field | Value |
|-------|-------|
| **Transition Name** | `refund_complete` |
| **From State** | `Process Refund` |
| **To State** | `End` |
| **Button Label** | `Complete` |
| **Condition Type** | `Always` |
| **Button Style** | `Success (Green)` |

> **💡 Button Styles:**
> - `Primary (Blue)` - Default action
> - `Success (Green)` - Positive action (approve, complete)
> - `Danger (Red)` - Negative action (reject, cancel)
> - `Warning (Yellow)` - Caution action

---

#### Step 3.4: Arrange States on Canvas

The visual canvas shows your workflow as a diagram:
- **Drag states** to reposition them for better visualization
- States are color-coded by type (see legend in top-right)
- Transitions appear as arrows between states with button labels

Suggested layout:
```
[Start] → [Supervisor Review] → [Manager Approval] → [Process Refund] → [End]
                    ↓                    ↓
                  [End]                [End]
```

---

#### Step 3.5: Test Workflow (Simulation)

1. Click **"Simulate"** button
2. Select initial state: `Start`
3. Enter test data (JSON):
   ```json
   {
     "ticket_id": "test-123",
     "refund_amount": 50.00,
     "reason": "Product defect"
   }
   ```
4. Click through the transitions to verify the flow
5. Verify state changes work as expected

---

#### Step 3.6: Publish Workflow

1. Click **"Publish"** button (or toggle the publish switch)
2. The workflow status changes from "Draft" to "Published"
3. Published workflows are active and can be triggered

**✅ Checkpoint:** Workflow should be published and visible in the Workflow List with a "Published" badge.

---

### Phase 4: Automation Rules (45 minutes)

**Navigation:** No-Code Platform > Business Logic > Automation Rules

> **💡 Create Automation Rule Form Fields:**
> The Create Automation Rule form has three sections:
>
> **Basic Information:**
> | Field | Description |
> |-------|-------------|
> | **Rule Name** | Technical name (lowercase, underscore) |
> | **Display Label** | User-friendly name shown in UI |
> | **Description** | Brief description of what the rule does |
> | **Category** | Organizational category (e.g., Ticket Management) |
>
> **Trigger Configuration:**
> | Field | Description | Shown For |
> |-------|-------------|-----------|
> | **Trigger Type** | Database Event, Scheduled, Manual, or Webhook | All |
> | **Event** | On Create, On Update, or On Delete | Database Event |
> | **Entity** | Target entity to monitor | Database Event |
> | **Watch Fields** | Specific fields to monitor for changes | Database Event (onUpdate) |
> | **Schedule Type** | Interval or Cron Expression | Scheduled |
> | **Run Every** | Interval value and unit (minutes/hours/days) | Scheduled (Interval) |
> | **Cron Expression** | Cron format schedule | Scheduled (Cron) |
>
> **Execution Settings:**
> | Field | Description | Default |
> |-------|-------------|---------|
> | **Active** | Rule will run automatically when triggered | Checked |
> | **Run Asynchronously** | Execute in background | Checked |
> | **Max Retries** | Number of retry attempts on failure | 3 |
> | **Timeout (seconds)** | Maximum execution time | 30 |

#### Step 4.1: Auto-Assign New Tickets

1. **Click "Create Rule"**

2. **Basic Information:**
   | Field | Value |
   |-------|-------|
   | **Rule Name** | `auto_assign_new_tickets` |
   | **Display Label** | `Auto-Assign New Tickets` |
   | **Description** | `Automatically assign tickets based on category` |
   | **Category** | `Ticket Management` |

3. **Trigger Configuration:**
   | Field | Value |
   |-------|-------|
   | **Trigger Type** | `Database Event` |
   | **Event** | `On Create` |
   | **Entity** | `SupportTicket` |
   | **Watch Fields** | (leave empty) |

4. **Execution Settings:**
   | Field | Value |
   |-------|-------|
   | **Active** | ☑️ Checked |
   | **Run Asynchronously** | ☑️ Checked |
   | **Max Retries** | `3` |
   | **Timeout (seconds)** | `30` |

5. **Click "Create Rule"**

> **💡 Note:** After creating the rule, you can add conditions and actions using the visual builders accessible from the rule detail view.

---

#### Step 4.2: SLA Monitoring & Escalation

1. **Click "Create Rule"**

2. **Basic Information:**
   | Field | Value |
   |-------|-------|
   | **Rule Name** | `sla_monitoring_escalation` |
   | **Display Label** | `SLA Monitoring & Escalation` |
   | **Description** | `Monitor SLA violations and escalate tickets` |
   | **Category** | `SLA Management` |

3. **Trigger Configuration:**
   | Field | Value |
   |-------|-------|
   | **Trigger Type** | `Scheduled` |
   | **Schedule Type** | `Cron Expression` |
   | **Cron Expression** | `0 * * * *` (every hour at minute 0) |

   Or using Interval:
   | Field | Value |
   |-------|-------|
   | **Schedule Type** | `Interval` |
   | **Run Every** | `1` `Hours` |

4. **Execution Settings:**
   | Field | Value |
   |-------|-------|
   | **Active** | ☑️ Checked |
   | **Run Asynchronously** | ☑️ Checked |
   | **Max Retries** | `3` |
   | **Timeout (seconds)** | `60` |

5. **Click "Create Rule"**

> **💡 Note:** After creating the rule, configure conditions and actions through the visual builders to filter for SLA violations and send notifications.

---

#### Step 4.3: Status Change Notification

1. **Click "Create Rule"**

2. **Basic Information:**
   | Field | Value |
   |-------|-------|
   | **Rule Name** | `ticket_status_notification` |
   | **Display Label** | `Ticket Status Change Notification` |
   | **Description** | `Notify customer when ticket status changes` |
   | **Category** | `Notifications` |

3. **Trigger Configuration:**
   | Field | Value |
   |-------|-------|
   | **Trigger Type** | `Database Event` |
   | **Event** | `On Update` |
   | **Entity** | `SupportTicket` |
   | **Watch Fields** | `status` |

4. **Execution Settings:**
   | Field | Value |
   |-------|-------|
   | **Active** | ☑️ Checked |
   | **Run Asynchronously** | ☑️ Checked |
   | **Max Retries** | `3` |
   | **Timeout (seconds)** | `30` |

5. **Click "Create Rule"**

> **💡 Note:** After creating the rule, use the visual builders to add conditions (status in ['resolved', 'closed']) and actions (create comment, send email).

---

#### Step 4.4: Daily Ticket Summary Report

1. **Click "Create Rule"**

2. **Basic Information:**
   | Field | Value |
   |-------|-------|
   | **Rule Name** | `daily_ticket_summary` |
   | **Display Label** | `Daily Ticket Summary Email` |
   | **Description** | `Send daily summary of ticket metrics to management` |
   | **Category** | `Reports` |

3. **Trigger Configuration:**
   | Field | Value |
   |-------|-------|
   | **Trigger Type** | `Scheduled` |
   | **Schedule Type** | `Cron Expression` |
   | **Cron Expression** | `0 8 * * *` (Daily at 8:00 AM) |

4. **Execution Settings:**
   | Field | Value |
   |-------|-------|
   | **Active** | ☑️ Checked |
   | **Run Asynchronously** | ☑️ Checked |
   | **Max Retries** | `3` |
   | **Timeout (seconds)** | `60` |

5. **Click "Create Rule"**

> **💡 Note:** After creating the rule, configure actions to query metrics and send the summary email through the visual action builder.

**✅ Checkpoint:** You should have 4 active automation rules. Check the Automation Rules list to see all rules and their status.

---

### Phase 5: Auto-Generated UI (10 minutes)

The platform automatically generates CRUD UI when you publish entities. Let's verify and customize.

**Navigation:** Check your main menu - you should see "No-Code Entities" menu with 4 submenus.

#### Step 5.1: Verify Auto-Generated Routes

1. **Navigate to:** No-Code Entities > Support Tickets
2. **You should see:** Auto-generated list view with columns:
   - Ticket Number
   - Subject
   - Priority
   - Status
   - Customer Name
   - Assigned To
   - SLA Due Date
   - Created At

3. **Test Create:**
   - Click "Create New"
   - You should see a form with all fields
   - Fill in a test ticket
   - Click "Save"
   - Verify it appears in the list

4. **Test Edit:**
   - Click on a ticket row
   - Modify fields
   - Click "Save"
   - Verify changes are saved

5. **Test Delete:**
   - Click delete icon
   - Confirm deletion
   - Verify record is removed

**Repeat for other entities:**
- Ticket Categories
- Ticket Comments
- SLA Policies

---

#### Step 5.2: Customize Entity Metadata (Optional)

If you want to customize the UI beyond auto-generation:

**Navigation:** No-Code Platform > Platform Configuration > Entity Metadata

1. **Select Entity:** `SupportTicket`

2. **Table Configuration:**
   ```json
   {
     "columns": [
       { "field": "ticket_number", "visible": true, "width": 120, "pinned": true },
       { "field": "subject", "visible": true, "width": 300 },
       { "field": "priority", "visible": true, "width": 100, "cellRenderer": "badge" },
       { "field": "status", "visible": true, "width": 120, "cellRenderer": "badge" },
       { "field": "customer_name", "visible": true, "width": 150 },
       { "field": "assigned_to", "visible": true, "width": 150 },
       { "field": "sla_due_date", "visible": true, "width": 150, "cellRenderer": "date" },
       { "field": "created_at", "visible": true, "width": 150, "cellRenderer": "datetime" }
     ],
     "defaultSort": [
       { "field": "created_at", "order": "desc" }
     ],
     "defaultFilters": [
       { "field": "status", "operator": "in", "value": ["new", "open", "in_progress"] }
     ],
     "rowActions": ["view", "edit", "delete"],
     "bulkActions": ["delete", "export"]
   }
   ```

3. **Form Configuration:**
   ```json
   {
     "layout": "tabs",
     "tabs": [
       {
         "name": "basic_info",
         "label": "Basic Information",
         "fields": [
           { "field": "ticket_number", "readonly": true, "autogenerate": true },
           { "field": "subject", "required": true },
           { "field": "description", "widget": "textarea", "rows": 4 },
           { "field": "priority", "widget": "select", "lookup": "ticket_priority" },
           { "field": "status", "widget": "select", "lookup": "ticket_status" },
           { "field": "category_id", "widget": "lookup", "lookup": "ticket_categories" }
         ]
       },
       {
         "name": "customer_info",
         "label": "Customer Information",
         "fields": [
           { "field": "customer_name", "required": true },
           { "field": "customer_email", "required": true, "validation": "email" },
           { "field": "customer_phone", "validation": "phone" }
         ]
       },
       {
         "name": "assignment",
         "label": "Assignment & SLA",
         "fields": [
           { "field": "assigned_to", "widget": "user-select" },
           { "field": "assigned_team", "widget": "select", "lookup": "support_teams" },
           { "field": "sla_due_date", "widget": "datetime" },
           { "field": "estimated_hours" },
           { "field": "actual_hours" }
         ]
       },
       {
         "name": "resolution",
         "label": "Resolution",
         "fields": [
           { "field": "resolution_notes", "widget": "textarea", "rows": 4 }
         ]
       }
     ]
   }
   ```

4. **Click "Save"**

5. **Refresh the UI** - Navigate back to Support Tickets list to see changes

**✅ Checkpoint:** Your CRUD UI should be fully functional with custom layouts.

---

### Phase 6: Reports (30 minutes)

**Navigation:** No-Code Platform > Reports & Dashboards > Report Designer

#### Step 6.1: Create Ticket Analytics Report

1. **Click "Create New Report"**

2. **Step 1: Data Source**
   - **Report Name:** `Ticket Analytics Report`
   - **Description:** `Comprehensive ticket analytics with trends`
   - **Data Source Type:** Entity
   - **Primary Entity:** `SupportTicket`
   - **Joins:**
     - LEFT JOIN `TicketCategory` ON `category_id`
     - LEFT JOIN `User` ON `assigned_to`

3. **Step 2: Select Columns**

   Drag fields from left panel to center panel:
   - `ticket_number`
   - `subject`
   - `priority`
   - `status`
   - `category_id.name` (from join) AS `Category`
   - `customer_name`
   - `customer_email`
   - `assigned_to.name` (from join) AS `Assigned To`
   - `assigned_team`
   - `sla_due_date`
   - `created_at`
   - `updated_at`

4. **Step 3: Parameters**

   Add parameters for dynamic filtering:

   **Parameter 1:**
   - Name: `date_from`
   - Label: `From Date`
   - Type: Date
   - Required: No
   - Default: `NOW() - INTERVAL '30 days'`

   **Parameter 2:**
   - Name: `date_to`
   - Label: `To Date`
   - Type: Date
   - Required: No
   - Default: `NOW()`

   **Parameter 3:**
   - Name: `status_filter`
   - Label: `Status`
   - Type: Multi-Select
   - Options: From lookup `ticket_status`
   - Required: No

   **Parameter 4:**
   - Name: `priority_filter`
   - Label: `Priority`
   - Type: Multi-Select
   - Options: From lookup `ticket_priority`
   - Required: No

5. **Step 4: Formatting & Filters**

   **Apply Filters:**
   ```
   AND Group:
   - created_at >= {date_from}
   - created_at <= {date_to}
   - status IN {status_filter} (if provided)
   - priority IN {priority_filter} (if provided)
   ```

   **Column Formatting:**
   - `priority`: Badge with color mapping
   - `status`: Badge with color mapping
   - `sla_due_date`: Highlight red if < NOW()
   - `created_at`: DateTime format

   **Sorting:**
   - Default: `created_at DESC`
   - Allow user sorting: Yes

   **Grouping:**
   - Enable grouping by: `status`, `priority`, `category`

6. **Step 5: Preview & Save**
   - Click "Preview with Sample Data"
   - Verify data appears correctly
   - Test parameters
   - Click "Save Report"

7. **Configure Export Options:**
   - PDF: Enabled (landscape, A4)
   - Excel: Enabled
   - CSV: Enabled
   - JSON: Enabled

8. **Set Permissions:**
   - Viewable by: Support Team, Managers
   - Exportable by: Managers only

**✅ Checkpoint:** Report should be saved and accessible from Reports List.

---

#### Step 6.2: Create SLA Performance Report

1. **Click "Create New Report"**

2. **Step 1: Data Source**
   - **Report Name:** `SLA Performance Report`
   - **Description:** `SLA compliance and violations analysis`
   - **Data Source Type:** Entity
   - **Primary Entity:** `SupportTicket`

3. **Step 2: Columns with Aggregations**

   Add these calculated fields:
   - `priority` (GROUP BY)
   - `status` (GROUP BY)
   - `COUNT(*) AS total_tickets`
   - `COUNT(*) WHERE sla_due_date < NOW() AND status NOT IN ('resolved', 'closed') AS violations`
   - `COUNT(*) WHERE status IN ('resolved', 'closed') AS completed`
   - `AVG(actual_hours) AS avg_resolution_hours`
   - `MIN(created_at) AS first_ticket`
   - `MAX(created_at) AS last_ticket`

4. **Step 3: Parameters**
   - Same as previous report (date range, status, priority)

5. **Step 4: Add Chart Visualization**

   **Chart 1: SLA Compliance by Priority**
   - Type: Bar Chart
   - X-Axis: `priority`
   - Y-Axis: `total_tickets`, `violations`
   - Series: Group by field
   - Colors: Auto from priority colors

   **Chart 2: Ticket Status Distribution**
   - Type: Donut Chart
   - Values: `total_tickets`
   - Labels: `status`
   - Colors: Auto from status colors

6. **Click "Save Report"**

---

#### Step 6.3: Create Quick Stats Report (KPI Report)

1. **Create Report:**
   - Name: `Support Ticket KPIs`
   - Type: Summary/KPI Report

2. **Add KPI Metrics:**

   **KPI 1: Total Open Tickets**
   ```sql
   SELECT COUNT(*)
   FROM support_tickets
   WHERE status IN ('new', 'open', 'in_progress')
   ```

   **KPI 2: SLA Violations**
   ```sql
   SELECT COUNT(*)
   FROM support_tickets
   WHERE sla_due_date < NOW()
   AND status NOT IN ('resolved', 'closed')
   ```

   **KPI 3: Avg Resolution Time**
   ```sql
   SELECT AVG(actual_hours)
   FROM support_tickets
   WHERE status = 'resolved'
   AND created_at >= NOW() - INTERVAL '30 days'
   ```

   **KPI 4: Customer Satisfaction**
   ```sql
   SELECT AVG(rating)
   FROM support_tickets
   WHERE status = 'closed'
   AND rating IS NOT NULL
   ```

3. **KPI Display Settings:**
   - Show trend arrows (compare to previous period)
   - Color coding (red/yellow/green thresholds)
   - Large number display

**✅ Checkpoint:** You should have 3 reports created and ready for dashboards.

---

### Phase 7: Dashboard (30 minutes)

**Navigation:** No-Code Platform > Reports & Dashboards > Dashboard Designer

#### Step 7.1: Create Support Metrics Dashboard

1. **Click "Create New Dashboard"**

2. **Dashboard Details (Step 1):**
   - **Name:** `Support Team Dashboard`
   - **Description:** `Real-time support metrics and KPIs`
   - **Theme:** Light (or Dark if preferred)
   - **Refresh Rate:** 5 minutes
   - **Shared:** Yes (with Support Team role)

3. **Dashboard Pages (Step 2):**

   Create 2 pages:
   - **Page 1:** `Overview` (default page)
   - **Page 2:** `Detailed Analytics`

4. **Add Widgets to Overview Page (Step 3):**

   **Switch to Visual Canvas Mode**

   **Widget 1: KPI Cards (Top Row)**
   - Drag "KPI Card" from Widget Library (4 times)
   - Position: Top row, 4 columns
   - Size: 3 cols x 2 rows each

   Configure each:
   - **KPI 1:** Total Open Tickets
     - Report: `Support Ticket KPIs`
     - Metric: Total Open
     - Icon: `folder-open`
     - Color: Blue

   - **KPI 2:** SLA Violations
     - Report: `Support Ticket KPIs`
     - Metric: SLA Violations
     - Icon: `warning`
     - Color: Red

   - **KPI 3:** Avg Resolution Time
     - Report: `Support Ticket KPIs`
     - Metric: Avg Resolution Time
     - Icon: `clock`
     - Color: Green
     - Suffix: " hours"

   - **KPI 4:** Today's Resolved
     - Report: `Support Ticket KPIs`
     - Metric: Today Resolved
     - Icon: `check-circle`
     - Color: Green

   **Widget 2: Status Distribution Chart**
   - Type: Donut Chart
   - Position: Row 2, Left (6 cols x 4 rows)
   - Report: `SLA Performance Report`
   - Chart Type: Donut
   - Title: "Tickets by Status"

   **Widget 3: Priority Distribution Chart**
   - Type: Bar Chart
   - Position: Row 2, Right (6 cols x 4 rows)
   - Report: `SLA Performance Report`
   - Chart Type: Bar (Vertical)
   - Title: "Tickets by Priority"

   **Widget 4: Recent Tickets Table**
   - Type: Data Grid
   - Position: Row 3, Full Width (12 cols x 5 rows)
   - Report: `Ticket Analytics Report`
   - Title: "Recent Tickets"
   - Max Rows: 10
   - Show: ticket_number, subject, priority, status, assigned_to, created_at

5. **Add Widgets to Detailed Analytics Page:**

   **Widget 1: SLA Compliance Chart**
   - Type: Bar Chart
   - Report: `SLA Performance Report`
   - Chart: SLA Compliance by Priority
   - Size: Full width x 5 rows

   **Widget 2: Trend Chart**
   - Type: Line Chart
   - Report: Custom query for trend data
   - Title: "Ticket Volume Trend (30 Days)"
   - Size: Full width x 5 rows

   **Widget 3: Category Breakdown**
   - Type: Pie Chart
   - Report: Query grouped by category
   - Size: Half width x 4 rows

   **Widget 4: Team Performance**
   - Type: Data Grid
   - Report: Query grouped by team
   - Columns: Team, Total, Resolved, Avg Time
   - Size: Half width x 4 rows

6. **Configure Interactive Features:**
   - Enable drill-down: Click chart to see filtered table
   - Enable cross-filtering: Click category to filter all widgets
   - Enable export: PDF, PNG, Excel

7. **Preview Dashboard:**
   - Switch between Desktop/Tablet/Mobile views
   - Test with real data
   - Verify all widgets load correctly

8. **Save & Publish Dashboard**

**✅ Checkpoint:** Dashboard should be live and accessible from Dashboards List.

---

### Phase 8: Menu Integration (10 minutes)

**Navigation:** No-Code Platform > Platform Configuration > Menu Management

#### Step 8.1: Create Support Module Menu Structure

1. **Click "Create Menu Item"**

2. **Parent Menu:**
   - **Title:** `Support Tickets`
   - **Icon:** `lifebuoy`
   - **Order:** 50
   - **Permissions:** `support:access:tenant`
   - **Parent:** None (top-level)

3. **Add Submenu Items:**

   **Submenu 1: Ticket List**
   - Title: `All Tickets`
   - Route: `dynamic/SupportTicket/list`
   - Icon: `list`
   - Order: 1
   - Permissions: `support:read:tenant`

   **Submenu 2: Create Ticket**
   - Title: `New Ticket`
   - Route: `dynamic/SupportTicket/create`
   - Icon: `plus-circle`
   - Order: 2
   - Permissions: `support:create:tenant`

   **Submenu 3: My Tickets**
   - Title: `My Assigned Tickets`
   - Route: `dynamic/SupportTicket/list?filter=assigned_to:{CURRENT_USER_ID}`
   - Icon: `user`
   - Order: 3

   **Submenu 4: Categories**
   - Title: `Manage Categories`
   - Route: `dynamic/TicketCategory/list`
   - Icon: `tag`
   - Order: 4
   - Permissions: `support:admin:tenant`

   **Submenu 5: SLA Policies**
   - Title: `SLA Policies`
   - Route: `dynamic/SLAPolicy/list`
   - Icon: `shield-check`
   - Order: 5
   - Permissions: `support:admin:tenant`

   **Separator**

   **Submenu 6: Reports**
   - Title: `Ticket Reports`
   - Route: `reports/view/ticket-analytics-report`
   - Icon: `chart-bar`
   - Order: 10

   **Submenu 7: Dashboard**
   - Title: `Support Dashboard`
   - Route: `dashboards/view/support-team-dashboard`
   - Icon: `gauge`
   - Order: 11

4. **Save Menu Structure**

5. **Sync Menu to Database:**
   - Navigate to: Settings > Menu Sync
   - Click "Sync Menu from Configuration"
   - Verify success message

**✅ Checkpoint:** Navigate to main menu - you should see "Support Tickets" menu with all submenus.

---

### Phase 9: Custom Pages (Optional - 45 minutes)

**Navigation:** No-Code Platform > UI & Pages > Page Designer

#### Step 9.1: Create Customer Ticket Portal

This is an optional step to create a customer-facing portal using GrapeJS Page Builder.

1. **Click "Create New Page"**

2. **Page Settings:**
   - **Page Name:** `customer_ticket_portal`
   - **Display Title:** `Submit Support Ticket`
   - **Route:** `/portal/submit-ticket`
   - **Public Access:** Yes (or require customer login)
   - **Template:** Blank (or choose a template)

3. **Design the Page using GrapeJS:**

   **Add Components:**
   - Header with logo and title
   - Form container
   - Input fields (mapped to SupportTicket fields):
     - Customer Name
     - Customer Email
     - Customer Phone
     - Subject
     - Description
     - Priority
     - Category
   - File upload for attachments
   - Submit button
   - Success/Error message area

4. **Configure Form Behavior:**

   Add custom JavaScript to handle form submission:

   ```javascript
   document.getElementById('ticket-submit-form').addEventListener('submit', async (e) => {
     e.preventDefault();

     const formData = {
       customer_name: document.getElementById('customer_name').value,
       customer_email: document.getElementById('customer_email').value,
       customer_phone: document.getElementById('customer_phone').value,
       subject: document.getElementById('subject').value,
       description: document.getElementById('description').value,
       priority: document.getElementById('priority').value,
       category_id: document.getElementById('category').value,
       status: 'new',
       ticket_number: 'AUTO' // Auto-generated by backend
     };

     try {
       const response = await apiFetch('/dynamic-data/SupportTicket/records', {
         method: 'POST',
         body: JSON.stringify(formData)
       });

       if (response.success) {
         showSuccess(`Ticket created: ${response.data.ticket_number}`);
         resetForm();
       }
     } catch (error) {
       showError('Failed to create ticket. Please try again.');
     }
   });
   ```

5. **Add Styling:**
   - Use platform's CSS framework
   - Make responsive (mobile-friendly)
   - Add validation styling

6. **Save & Publish Page**

7. **Add to Menu** (optional):
   - Add to public menu or customer portal menu

---

#### Step 9.2: Create Ticket Details View Page (Optional)

Create a custom detailed view for tickets with comments, history, and actions.

1. **Create Page:** `ticket_detail_view`
2. **Route:** `/tickets/view/{id}`
3. **Design Layout:**
   - Ticket header (number, subject, status badge)
   - Customer info card
   - Assignment info card
   - Description section
   - Comments timeline
   - Attachments list
   - Action buttons (Assign, Close, Escalate)

4. **Load Data Dynamically:**
   ```javascript
   const ticketId = getRouteParam('id');
   const ticket = await apiFetch(`/dynamic-data/SupportTicket/records/${ticketId}`);
   const comments = await apiFetch(`/dynamic-data/TicketComment/records?filter=ticket_id:${ticketId}&sort=created_at:desc`);
   ```

5. **Save & Publish**

**✅ Checkpoint:** Custom pages are live and accessible via their routes.

---

## Testing & Validation

### Test Checklist

Run through this checklist to ensure everything works:

#### 1. Data Model Tests
- [ ] Can create new SupportTicket record
- [ ] Can create TicketCategory record
- [ ] Can create TicketComment record
- [ ] Can create SLAPolicy record
- [ ] Foreign key relationships work (category_id, ticket_id)
- [ ] Required field validation works
- [ ] Unique constraints work (ticket_number)

#### 2. Lookup Tests
- [ ] Priority dropdown shows 4 options
- [ ] Status dropdown shows 6 options
- [ ] Category dropdown loads from database
- [ ] Team dropdown shows 5 options
- [ ] Lookups are cached properly

#### 3. Workflow Tests
- [ ] Create ticket with tag `refund_requested`
- [ ] Workflow instance created automatically
- [ ] Supervisor receives approval task
- [ ] Approve moves to manager
- [ ] Manager approval triggers refund task
- [ ] Rejection ends workflow correctly

#### 4. Automation Tests
- [ ] **Auto-Assign:** Create ticket with category → should auto-assign team and set SLA
- [ ] **SLA Monitoring:** Create ticket with past SLA date → should escalate on next run
- [ ] **Status Notification:** Change status to 'resolved' → should send email
- [ ] **Daily Summary:** Wait for scheduled time → should receive summary email

#### 5. UI Tests
- [ ] List view shows all tickets
- [ ] Sorting works on all columns
- [ ] Filtering works (status, priority)
- [ ] Pagination works
- [ ] Create form validates required fields
- [ ] Edit form saves changes
- [ ] Delete confirmation works
- [ ] Bulk actions work (if configured)

#### 6. Report Tests
- [ ] Ticket Analytics Report runs without errors
- [ ] Parameters filter data correctly
- [ ] Data exports to PDF successfully
- [ ] Data exports to Excel successfully
- [ ] Charts render correctly
- [ ] SLA Performance Report shows correct metrics

#### 7. Dashboard Tests
- [ ] Dashboard loads without errors
- [ ] All widgets display data
- [ ] KPI cards show correct numbers
- [ ] Charts are interactive
- [ ] Clicking chart filters other widgets
- [ ] Dashboard refreshes automatically
- [ ] Export to PDF works

#### 8. Menu Tests
- [ ] "Support Tickets" menu appears in main navigation
- [ ] All submenus are clickable
- [ ] Routes navigate correctly
- [ ] Permissions hide/show menu items correctly

#### 9. Integration Tests
- [ ] Create ticket → triggers automation → assigns team
- [ ] Update ticket status → triggers notification
- [ ] Ticket data appears in reports
- [ ] Dashboard reflects new tickets
- [ ] Workflow creates comments automatically

#### 10. Performance Tests
- [ ] List view loads < 2 seconds with 1000 records
- [ ] Report runs < 5 seconds
- [ ] Dashboard loads < 3 seconds
- [ ] Automations execute < 10 seconds

---

### Common Issues & Solutions

#### Issue 1: Entity not appearing in menu
**Solution:** Make sure entity is Published, not just Draft. Go to Data Model Designer > Select Entity > Click "Publish".

#### Issue 2: Lookup dropdown is empty
**Solution:**
- Check lookup configuration has correct entity and fields
- Verify source entity has data
- Clear lookup cache: Lookup Configuration > Select Lookup > Click "Clear Cache"

#### Issue 3: Automation not triggering
**Solution:**
- Verify automation is Active (not Draft)
- Check conditions match the trigger event
- Review automation logs: Automation Rules > Execution History

#### Issue 4: Workflow stuck in state
**Solution:**
- Check approver has correct role/permissions
- Verify transition conditions are met
- Review workflow instance: Workflow Designer > Instance Monitor > View Details

#### Issue 5: Report shows no data
**Solution:**
- Verify entity has records
- Check report filters/parameters
- Test with "Remove All Filters"
- Check entity permissions

---

## Going Live

### Pre-Launch Checklist

Before deploying to production:

#### 1. Data Cleanup
- [ ] Remove test/dummy records
- [ ] Verify production data is imported
- [ ] Run data validation scripts
- [ ] Create backup of current data

#### 2. Configuration Review
- [ ] Review all entity definitions
- [ ] Verify lookup data is complete
- [ ] Test all workflows end-to-end
- [ ] Verify automation schedules are correct
- [ ] Check email templates and recipients

#### 3. Permissions & Security
- [ ] Define roles (Support Agent, Supervisor, Manager, Customer)
- [ ] Assign permissions to each role
- [ ] Test access controls
- [ ] Verify row-level security (if configured)
- [ ] Enable audit logging

#### 4. Performance Optimization
- [ ] Add database indexes on frequently queried fields
- [ ] Enable lookup caching
- [ ] Configure report caching
- [ ] Set appropriate dashboard refresh rates
- [ ] Test with production data volume

#### 5. Documentation
- [ ] Write user guide for Support Agents
- [ ] Write admin guide for Supervisors/Managers
- [ ] Document workflow approval process
- [ ] Create SLA policy reference
- [ ] Document escalation procedures

#### 6. Training
- [ ] Train support agents on ticket creation/management
- [ ] Train supervisors on workflow approvals
- [ ] Train managers on reports/dashboards
- [ ] Conduct Q&A sessions

#### 7. Monitoring Setup
- [ ] Set up automation failure alerts
- [ ] Monitor workflow SLA violations
- [ ] Track system performance metrics
- [ ] Set up dashboard for ops team

---

### Deployment Steps

1. **Export Configuration (from staging):**
   ```bash
   # Export entities
   POST /api/v1/data-model/export

   # Export workflows
   POST /api/v1/workflows/export

   # Export automations
   POST /api/v1/automations/export
   ```

2. **Import to Production:**
   ```bash
   # Import entities
   POST /api/v1/data-model/import

   # Run migrations
   POST /api/v1/data-model/{entity}/migrations/run

   # Import workflows
   POST /api/v1/workflows/import

   # Import automations
   POST /api/v1/automations/import
   ```

3. **Activate Features:**
   - Publish all entities
   - Activate all workflows
   - Enable all automations
   - Sync menu to production

4. **Load Initial Data:**
   - Import TicketCategories
   - Import SLAPolicies
   - Import user assignments

5. **Verify Production:**
   - Run through test checklist
   - Create test ticket end-to-end
   - Verify emails are sent
   - Check dashboard displays correctly

6. **Go Live:**
   - Announce to users
   - Monitor first day closely
   - Be ready for quick fixes

---

## Appendix

### A. Entity Field Reference

#### SupportTicket Fields
| Field | Type | Purpose | Validation |
|-------|------|---------|------------|
| ticket_number | String | Unique identifier | Auto-generated, unique |
| subject | String | Brief description | Required, max 200 chars |
| description | Text | Full description | Required |
| priority | Select | Urgency level | Required, from lookup |
| status | Select | Current state | Required, from lookup |
| category_id | Reference | Ticket category | Optional, FK to TicketCategory |
| customer_name | String | Customer contact | Required |
| customer_email | Email | Email contact | Required, validated |
| assigned_to | Reference | User assigned | Optional, FK to User |
| assigned_team | String | Team assigned | Optional |
| sla_due_date | DateTime | SLA deadline | Auto-calculated |
| resolution_notes | Text | Resolution summary | Optional |
| tags | JSON | Custom tags | Optional |

### B. Automation Trigger Reference

| Trigger Type | When It Fires | Use Cases |
|--------------|---------------|-----------|
| onCreate | After new record created | Auto-assignment, welcome emails |
| onUpdate | After record updated | Status change notifications |
| onDelete | Before record deleted | Cleanup, archival |
| Scheduled | Based on cron expression | SLA monitoring, daily reports |
| Manual | User clicks button | Ad-hoc processing |
| Webhook | External API call received | Integration triggers |

### C. Workflow State Types

| State Type | Purpose | Configuration |
|------------|---------|---------------|
| Start | Entry point | Auto-starts workflow |
| Approval | Requires approval | Approver, SLA, actions |
| Task | Assigned work | Assignee, due date, actions |
| Condition | Branch logic | Conditions, true/false paths |
| End | Completion | Final actions |

### D. Report Chart Types

| Chart Type | Best For | Data Requirements |
|------------|----------|-------------------|
| Bar | Comparing categories | 1+ dimensions, 1+ measures |
| Line | Trends over time | Time dimension, 1+ measures |
| Pie | Part-to-whole | 1 dimension, 1 measure |
| Donut | Part-to-whole (with center text) | 1 dimension, 1 measure |
| Area | Cumulative trends | Time dimension, 1+ measures |
| Scatter | Correlation analysis | 2 continuous measures |
| Radar | Multi-dimensional comparison | 3+ measures |

### E. Useful API Endpoints

```
# Dynamic Data CRUD
GET    /api/v1/dynamic-data/{entity}/records
POST   /api/v1/dynamic-data/{entity}/records
GET    /api/v1/dynamic-data/{entity}/records/{id}
PUT    /api/v1/dynamic-data/{entity}/records/{id}
DELETE /api/v1/dynamic-data/{entity}/records/{id}

# Lookups
GET    /api/v1/lookups/{lookup_name}/values
POST   /api/v1/lookups/{lookup_name}/refresh

# Workflows
POST   /api/v1/workflows/{workflow_id}/instances
GET    /api/v1/workflows/instances/{instance_id}
POST   /api/v1/workflows/instances/{instance_id}/approve
POST   /api/v1/workflows/instances/{instance_id}/reject

# Reports
POST   /api/v1/reports/{report_id}/execute
GET    /api/v1/reports/{report_id}/export/{format}

# Dashboards
GET    /api/v1/dashboards/{dashboard_id}
GET    /api/v1/dashboards/{dashboard_id}/widgets/{widget_id}/data
```

### F. JavaScript Helper Functions

```javascript
// Fetch data from dynamic entity
async function fetchTickets(filters = {}) {
  const queryString = new URLSearchParams(filters).toString();
  return await apiFetch(`/dynamic-data/SupportTicket/records?${queryString}`);
}

// Create new ticket
async function createTicket(ticketData) {
  return await apiFetch('/dynamic-data/SupportTicket/records', {
    method: 'POST',
    body: JSON.stringify(ticketData)
  });
}

// Get lookup values
async function getLookupValues(lookupName) {
  return await apiFetch(`/lookups/${lookupName}/values`);
}

// Trigger workflow
async function triggerWorkflow(workflowId, entityId) {
  return await apiFetch(`/workflows/${workflowId}/instances`, {
    method: 'POST',
    body: JSON.stringify({ entity_id: entityId })
  });
}
```

---

## Advanced: Module Extensions

**New in Phase 4!** Learn how to extend other modules with your own custom fields, UI components, and menu items.

### Use Case: Link Support Tickets to HR Employees

Imagine you have an HR module with an Employee entity. You want to track support tickets raised by each employee directly on their employee record.

Instead of modifying the HR module directly, you can **extend** it from your Support module!

---

### Extension 1: Add Support Fields to HR Employee Entity

**API Endpoint:** `POST /api/v1/module-extensions/entity`

**Request:**
```json
{
  "extending_module_id": "support_module_uuid",
  "target_entity_id": "hr_employees_entity_uuid",
  "extension_fields": [
    {
      "name": "total_tickets",
      "type": "integer",
      "label": "Total Support Tickets",
      "description": "Total number of support tickets raised by this employee",
      "required": false,
      "default_value": 0
    },
    {
      "name": "avg_resolution_time",
      "type": "decimal",
      "precision": 10,
      "scale": 2,
      "label": "Avg Resolution Time (hours)",
      "description": "Average time to resolve tickets raised by this employee",
      "required": false
    },
    {
      "name": "last_ticket_date",
      "type": "datetime",
      "label": "Last Ticket Date",
      "description": "Date of last ticket raised",
      "required": false
    }
  ]
}
```

**What happens:**
1. System creates extension table: `support_hr_employees_ext`
2. Table has foreign key to `hr_employees.id`
3. Extension fields are added to the extension table
4. When querying an employee, extension data is automatically joined

**Query Employee with Extensions:**
```bash
GET /api/v1/module-extensions/entity/Employee/records/{employee_id}
```

**Response:**
```json
{
  "id": "employee-123",
  "name": "John Doe",
  "email": "john@company.com",
  "department": "Engineering",

  "support_ext": {
    "total_tickets": 15,
    "avg_resolution_time": 4.5,
    "last_ticket_date": "2026-01-20T10:30:00Z"
  }
}
```

---

### Extension 2: Add "Support Tickets" Tab to Employee Detail Screen

**API Endpoint:** `POST /api/v1/module-extensions/screen`

**Request:**
```json
{
  "extending_module_id": "support_module_uuid",
  "target_module_id": "hr_module_uuid",
  "target_screen": "employee_detail",
  "extension_type": "tab",
  "extension_config": {
    "label": "Support Tickets",
    "icon": "headset",
    "component_path": "/modules/support/components/employee-tickets-tab.js"
  },
  "position": 10,
  "required_permission": "support:tickets:read"
}
```

**Result:**
When viewing an employee's detail page in the HR module, a new "Support Tickets" tab appears showing all tickets raised by that employee.

**Tab Content (employee-tickets-tab.js):**
```javascript
class EmployeeTicketsTab {
  async render(employeeId) {
    // Fetch tickets for this employee
    const tickets = await apiFetch(
      `/dynamic-data/SupportTicket/records?filters={"created_by":"${employeeId}"}`
    );

    return `
      <div class="employee-tickets">
        <h3>Support Tickets (${tickets.length})</h3>
        <table class="data-table">
          <thead>
            <tr>
              <th>Ticket #</th>
              <th>Subject</th>
              <th>Status</th>
              <th>Priority</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            ${tickets.map(ticket => `
              <tr onclick="window.location='/tickets/${ticket.id}'">
                <td>${ticket.ticket_number}</td>
                <td>${ticket.subject}</td>
                <td><span class="badge badge-${ticket.status}">${ticket.status}</span></td>
                <td>${ticket.priority}</td>
                <td>${formatDate(ticket.created_at)}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    `;
  }
}
```

---

### Extension 3: Add "Support" Submenu to HR Management Menu

**API Endpoint:** `POST /api/v1/module-extensions/menu`

**Request:**
```json
{
  "extending_module_id": "support_module_uuid",
  "target_module_id": "hr_module_uuid",
  "target_menu_item": "hr_management",
  "menu_config": {
    "type": "submenu",
    "label": "Employee Support",
    "icon": "headset",
    "items": [
      {
        "label": "Employee Tickets",
        "route": "support/employee-tickets",
        "icon": "ticket",
        "permission": "support:tickets:read"
      },
      {
        "label": "Support Analytics",
        "route": "support/employee-analytics",
        "icon": "chart-bar",
        "permission": "support:reports:read"
      }
    ]
  },
  "position": 20
}
```

**Result:**
The HR Management menu now has an "Employee Support" submenu with links to view support tickets and analytics for employees.

**Menu Structure:**
```
HR Management
  ├── Employees
  ├── Departments
  ├── Leave Requests
  ├── Employee Support (⬅️ Extension from Support module)
  │   ├── Employee Tickets
  │   └── Support Analytics
  └── Payroll
```

---

### Extension Benefits

✅ **Non-invasive:** Don't modify the HR module's code
✅ **Modular:** Support module can be removed without breaking HR
✅ **Permission-aware:** Extensions respect user permissions
✅ **Versioned:** Extensions are tied to module versions
✅ **Maintainable:** Each module manages its own extensions

### When to Use Extensions

Use entity extensions when:
- ✅ You need to add fields to entities from another module
- ✅ You want to track relationships across modules
- ✅ You need module-specific data on shared entities

Use screen extensions when:
- ✅ You want to display your module's data on another module's screens
- ✅ You need to add actions/buttons to existing screens
- ✅ You want to enhance user workflows across modules

Use menu extensions when:
- ✅ Your module's features are related to another module
- ✅ You want to organize navigation by business domain
- ✅ You need quick access to cross-module features

---

## Publishing Your Module

Once you've finished building and testing your module, it's time to publish it!

### Step 1: Review Module Components

Check that all components are complete:
- ✅ All entities published
- ✅ All workflows tested
- ✅ All automations working
- ✅ All reports generating correctly
- ✅ Dashboard widgets displaying data
- ✅ Menu items configured

### Step 2: Publish Module

**API Endpoint:** `POST /api/v1/nocode-modules/{module_id}/publish`

**Request:**
```json
{
  "release_notes": "Initial release of Support Management module with ticket tracking, SLA monitoring, and automated workflows."
}
```

**Result:**
- Module status changes from **Draft** → **Active**
- Version remains: **1.0.0**
- All components become visible to users with appropriate permissions
- Module is now available for use across the tenant

### Step 3: Version Management

When you make changes to an active module:

**Patch Version (1.0.0 → 1.0.1):**
- Bug fixes
- Minor text changes
- Performance improvements

**Minor Version (1.0.1 → 1.1.0):**
- New fields added
- New features added
- Backward compatible changes

**Major Version (1.1.0 → 2.0.0):**
- Breaking changes
- Entity schema changes
- Workflow logic changes
- Not backward compatible

**API Endpoint:** `POST /api/v1/nocode-modules/{module_id}/versions`

**Request:**
```json
{
  "change_type": "minor",
  "change_description": "Added SLA escalation automation and ticket priority field",
  "breaking_changes": false
}
```

---

## Summary

Congratulations! You've successfully created a complete **Customer Support Ticket System** using ONLY the No-Code Platform with Phase 4 Module System!

### What You Built:
✅ **1 organized module** with semantic versioning
✅ 4 database entities with relationships (all within module)
✅ 4 dynamic lookup configurations
✅ 1 approval workflow
✅ 4 automation rules
✅ Auto-generated CRUD UI
✅ 3 analytical reports
✅ 1 interactive dashboard
✅ Complete menu navigation
✅ Optional custom portal pages
✅ **Optional entity extensions** to HR module
✅ **Optional screen extensions** with custom tabs
✅ **Optional menu extensions** for cross-module navigation

### Skills You Learned:
- **Module creation and management** (Phase 4)
- **Table prefix configuration** (Phase 4)
- **Module publishing and versioning** (Phase 4)
- Data modeling with entity relationships
- Dynamic lookup configuration
- Visual workflow design
- Event-based automation
- Report creation with parameters
- Dashboard design with interactive widgets
- Menu management
- Page building with GrapeJS
- **Entity extension creation** (Phase 4)
- **Screen extension creation** (Phase 4)
- **Menu extension creation** (Phase 4)

### Next Steps:
1. **Enhance the module:**
   - Add customer satisfaction rating
   - Implement ticket merging
   - Add knowledge base integration
   - Create customer self-service portal
   - Version and publish updates (1.1.0, 1.2.0, etc.)

2. **Build another module:**
   - Inventory Management System
   - Employee Onboarding System
   - Project Management System
   - CRM System
   - Create dependencies between modules

3. **Explore advanced features:**
   - Custom calculated fields
   - Complex validation rules
   - External API integrations
   - Mobile app configuration
   - **Cross-module service calls** (Phase 4)
   - **Module packaging and export** (Phase 6)

### Module System Benefits:
✅ **Organization:** All components grouped by business domain
✅ **Versioning:** Track changes with semantic versioning
✅ **Dependencies:** Modules can depend on other modules
✅ **Extensions:** Enhance other modules without modifying them
✅ **Reusability:** Export and import modules across tenants
✅ **Isolation:** Modules are independent and self-contained

### Need Help?
- Check documentation: [NO-CODE-PLATFORM-DESIGN.md](NO-CODE-PLATFORM-DESIGN.md)
- Review phase docs: [NO-CODE-PHASE4.md](NO-CODE-PHASE4.md)
- Module system examples: [backend/app/services/examples/](backend/app/services/examples/)
- Contact platform admin for support

---

**Document Version:** 2.0 (Updated for Phase 4)
**Last Updated:** 2026-01-21
**Author:** Platform Team
**Next Review:** After first user feedback
