# Complete No-Code Module Creation Guide

**Date:** 2026-01-19
**Purpose:** Step-by-step guide to create a fully functional module using only the No-Code Platform
**Example Module:** Customer Support Ticket System
**Estimated Time:** 2-3 hours

---

## Table of Contents

1. [Introduction](#introduction)
2. [Module Overview](#module-overview)
3. [Prerequisites](#prerequisites)
4. [Step-by-Step Implementation](#step-by-step-implementation)
5. [Testing & Validation](#testing--validation)
6. [Going Live](#going-live)
7. [Appendix](#appendix)

---

## Introduction

This guide demonstrates how to build a complete, production-ready **Customer Support Ticket System** using ONLY the No-Code Platform features. No backend coding required!

### What You'll Build

A complete support ticket system with:
- Custom data models (Tickets, Categories, SLA Policies)
- Automated workflows (ticket assignment, escalation)
- Business automation (SLA monitoring, notifications)
- Dynamic lookups (priority, status, categories)
- Auto-generated CRUD UI
- Reports and dashboards
- Custom pages for end-users

### Features You'll Use

✅ **Data Model Designer** - Create 4 entities
✅ **Lookup Configuration** - Configure dropdowns
✅ **Workflow Designer** - Ticket approval workflow
✅ **Automation System** - Auto-assignment & SLA alerts
✅ **Auto-Generated UI** - Instant CRUD interfaces
✅ **Report Designer** - Ticket analytics
✅ **Dashboard Designer** - Support metrics dashboard
✅ **Menu Management** - Navigation structure
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

### Module Architecture

```
┌─────────────────────────────────────────────────────────┐
│  DATA LAYER (4 Entities)                                │
│  ├── SupportTicket (main entity)                        │
│  ├── TicketCategory (lookup data)                       │
│  ├── TicketComment (related records)                    │
│  └── SLAPolicy (configuration data)                     │
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
```

---

## Prerequisites

### Required Permissions

Ensure you have these permissions:
- `data-model:create:tenant` - Create entities
- `workflows:create:tenant` - Create workflows
- `automations:create:tenant` - Create automation rules
- `lookups:create:tenant` - Configure lookups
- `reports:create:tenant` - Create reports
- `dashboards:create:tenant` - Create dashboards
- `menu:manage:tenant` - Manage menu items

### Platform Status Check

Before starting, verify:
1. ✅ Phase 1 Complete (Data Model, Workflow, Automation, Lookups)
2. ✅ Phase 2 Complete (Runtime CRUD, Auto-UI, Integration)
3. ✅ Phase 3 Priority 1-3 Complete (Menu, Report/Dashboard Designers)

You can verify by checking the "No-Code Platform" menu exists and contains all submenus.

---

## Step-by-Step Implementation

### Phase 1: Data Model Design (30 minutes)

#### Step 1.1: Create SupportTicket Entity

**Navigation:** No-Code Platform > Data & Schema > Data Model Designer

1. **Click "Create New Entity"**

2. **Basic Information:**
   - **Entity Name:** `SupportTicket`
   - **Display Name:** `Support Ticket`
   - **Table Name:** `support_tickets`
   - **Description:** `Customer support ticket with SLA tracking`
   - **Icon:** `ticket` (or choose from Phosphor icons)

3. **Add Fields:** Click "Add Field" for each field below

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
   - Click "Add Relationship"
   - **Name:** `comments`
   - **Type:** One-to-Many
   - **Target Entity:** `TicketComment` (will create later)
   - **Foreign Key:** `ticket_id`

5. **Add Indexes:**
   - Click "Add Index"
   - **Name:** `idx_ticket_status_priority`
   - **Columns:** `status`, `priority`
   - **Type:** B-Tree

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
   - **Repeat for:** `SLAPolicy`, `TicketComment`, `SupportTicket` (in this order due to dependencies)

3. **Run Migrations:**
   - Click "Migration History" tab
   - Select each pending migration
   - Click "Run Migration"
   - Verify success message

4. **Publish All Entities:**
   - Select each entity
   - Click "Publish"
   - This makes them available for runtime CRUD operations

**✅ Checkpoint:** You should now have 4 database tables created and visible in the Data Model Designer.

---

### Phase 2: Lookup Configuration (15 minutes)

**Navigation:** No-Code Platform > Business Logic > Lookup Configuration

#### Step 2.1: Create Priority Lookup

1. **Click "Create Lookup"**

2. **Basic Information:**
   - **Name:** `ticket_priority`
   - **Display Name:** `Ticket Priority`
   - **Description:** `Priority levels for tickets`
   - **Source Type:** Static List

3. **Static Options:**
   ```json
   [
     { "value": "low", "label": "Low", "color": "#10b981" },
     { "value": "medium", "label": "Medium", "color": "#f59e0b" },
     { "value": "high", "label": "High", "color": "#ef4444" },
     { "value": "critical", "label": "Critical", "color": "#dc2626" }
   ]
   ```

4. **Settings:**
   - **Cacheable:** Yes
   - **Cache TTL:** 3600 seconds
   - **Searchable:** Yes

5. **Click "Save"**

---

#### Step 2.2: Create Status Lookup

1. **Click "Create Lookup"**

2. **Basic Information:**
   - **Name:** `ticket_status`
   - **Display Name:** `Ticket Status`
   - **Source Type:** Static List

3. **Static Options:**
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

4. **Click "Save"**

---

#### Step 2.3: Create Category Lookup (Dynamic)

1. **Click "Create Lookup"**

2. **Basic Information:**
   - **Name:** `ticket_categories`
   - **Display Name:** `Ticket Categories`
   - **Source Type:** Entity

3. **Entity Configuration:**
   - **Entity:** `TicketCategory`
   - **Value Field:** `id`
   - **Label Field:** `name`
   - **Filter:** `is_active = true`
   - **Sort By:** `name ASC`

4. **Additional Fields to Return:**
   - `description`
   - `default_sla_hours`
   - `assigned_team`
   - `color_code`

5. **Settings:**
   - **Cacheable:** Yes
   - **Cache TTL:** 1800 seconds
   - **Searchable:** Yes
   - **Allow Refresh:** Yes

6. **Click "Save"**

---

#### Step 2.4: Create Team Lookup

1. **Click "Create Lookup"**

2. **Basic Information:**
   - **Name:** `support_teams`
   - **Display Name:** `Support Teams`
   - **Source Type:** Static List

3. **Static Options:**
   ```json
   [
     { "value": "tier1", "label": "Tier 1 Support" },
     { "value": "tier2", "label": "Tier 2 Support" },
     { "value": "technical", "label": "Technical Team" },
     { "value": "billing", "label": "Billing Team" },
     { "value": "management", "label": "Management" }
   ]
   ```

4. **Click "Save"**

**✅ Checkpoint:** You should have 4 lookups configured. Test by opening any lookup and clicking "Preview Data".

---

### Phase 3: Workflow Design (30 minutes)

**Navigation:** No-Code Platform > Business Logic > Workflow Designer

#### Step 3.1: Create Refund Approval Workflow

1. **Click "Create Workflow"**

2. **Basic Information:**
   - **Name:** `ticket_refund_approval`
   - **Display Name:** `Ticket Refund Approval`
   - **Description:** `Approval process for ticket refunds`
   - **Entity:** `SupportTicket`
   - **Start Condition:** `tags contains 'refund_requested'`

3. **Design Workflow States:**

   Click "Open Designer" to access the visual canvas.

   **State 1: Start**
   - Type: Start
   - Position: (100, 100)
   - No configuration needed

   **State 2: Supervisor Review**
   - Type: Approval
   - Position: (300, 100)
   - **Approver Type:** Role
   - **Role:** `Support Supervisor`
   - **Approval Type:** Sequential
   - **SLA Hours:** 4
   - **Actions on Approval:**
     - Update `status` to `'pending_manager'`
   - **Actions on Rejection:**
     - Update `status` to `'closed'`
     - Add comment: "Refund request rejected by supervisor"

   **State 3: Manager Approval**
   - Type: Approval
   - Position: (500, 100)
   - **Approver Type:** Role
   - **Role:** `Support Manager`
   - **SLA Hours:** 8
   - **Actions on Approval:**
     - Update `status` to `'approved'`
     - Update `tags` to add `'refund_approved'`
   - **Actions on Rejection:**
     - Update `status` to `'closed'`
     - Add comment: "Refund request rejected by manager"

   **State 4: Process Refund**
   - Type: Task
   - Position: (700, 100)
   - **Assigned Role:** `Billing Team`
   - **Task Description:** "Process refund for ticket"
   - **Actions on Complete:**
     - Update `status` to `'closed'`
     - Add comment: "Refund processed successfully"

   **State 5: End**
   - Type: End
   - Position: (900, 100)

4. **Create Transitions:**
   - Start → Supervisor Review (automatic)
   - Supervisor Review → Manager Approval (on approval)
   - Supervisor Review → End (on rejection)
   - Manager Approval → Process Refund (on approval)
   - Manager Approval → End (on rejection)
   - Process Refund → End (on completion)

5. **Save Workflow**

6. **Test Workflow:**
   - Click "Simulate"
   - Enter test data (ticket with `refund_requested` tag)
   - Step through the workflow
   - Verify state transitions

7. **Activate Workflow:**
   - Click "Activate"
   - Confirm activation

**✅ Checkpoint:** Workflow should be active and visible in the Workflow List.

---

### Phase 4: Automation Rules (45 minutes)

**Navigation:** No-Code Platform > Business Logic > Automation Rules

#### Step 4.1: Auto-Assign New Tickets

1. **Click "Create Automation"**

2. **Basic Information:**
   - **Name:** `auto_assign_new_tickets`
   - **Display Name:** `Auto-Assign New Tickets`
   - **Description:** `Automatically assign tickets based on category`

3. **Trigger Configuration:**
   - **Trigger Type:** Database Event
   - **Event:** onCreate
   - **Entity:** `SupportTicket`

4. **Conditions:**
   ```
   AND Group 1:
   - Field: status
   - Operator: equals
   - Value: 'new'

   AND:
   - Field: category_id
   - Operator: is not null
   ```

5. **Actions:**

   **Action 1: Lookup Category Details**
   - Type: Query Data
   - Entity: `TicketCategory`
   - Filter: `id = {category_id}`
   - Store Result As: `category`

   **Action 2: Update Ticket Team**
   - Type: Update Record
   - Entity: `SupportTicket`
   - Record ID: `{id}`
   - Fields to Update:
     - `assigned_team` = `{category.assigned_team}`
     - `sla_due_date` = `NOW() + {category.default_sla_hours} HOURS`
     - `status` = `'open'`

   **Action 3: Create Comment**
   - Type: Create Record
   - Entity: `TicketComment`
   - Fields:
     - `ticket_id` = `{id}`
     - `comment_text` = `"Ticket auto-assigned to {category.assigned_team}"`
     - `comment_type` = `'Status Update'`
     - `is_public` = `false`

6. **Execution Settings:**
   - **Enabled:** Yes
   - **Run Asynchronously:** Yes
   - **Max Retry:** 3
   - **Timeout:** 30 seconds

7. **Click "Save & Activate"**

---

#### Step 4.2: SLA Monitoring & Escalation

1. **Click "Create Automation"**

2. **Basic Information:**
   - **Name:** `sla_monitoring_escalation`
   - **Display Name:** `SLA Monitoring & Escalation`
   - **Description:** `Monitor SLA violations and escalate tickets`

3. **Trigger Configuration:**
   - **Trigger Type:** Scheduled
   - **Schedule:** Every 1 hour
   - **Cron Expression:** `0 * * * *` (every hour at minute 0)

4. **Conditions:**
   ```
   AND Group 1:
   - Field: status
   - Operator: in
   - Value: ['open', 'in_progress', 'pending']

   AND:
   - Field: sla_due_date
   - Operator: less than
   - Value: NOW()

   AND:
   - Field: tags
   - Operator: does not contain
   - Value: 'escalated'
   ```

5. **Actions:**

   **Action 1: Update Priority**
   - Type: Update Record
   - Entity: `SupportTicket`
   - Filter: (conditions above)
   - Fields to Update:
     - `priority` = `'critical'`
     - `tags` = ARRAY_APPEND(`tags`, `'escalated'`)

   **Action 2: Create Alert Comment**
   - Type: Create Record (Bulk)
   - Entity: `TicketComment`
   - For Each Record From: Query Results
   - Fields:
     - `ticket_id` = `{id}`
     - `comment_text` = `"⚠️ SLA VIOLATION: Ticket escalated due to missed SLA"`
     - `comment_type` = `'Status Update'`
     - `is_public` = `false`

   **Action 3: Send Email Notification**
   - Type: Send Email
   - Recipients: `{assigned_to.email}, support-manager@company.com`
   - Subject: `"SLA Violation - Ticket #{ticket_number}"`
   - Body Template:
     ```
     Ticket #{ticket_number} has exceeded its SLA deadline.

     Subject: {subject}
     Priority: {priority}
     SLA Due: {sla_due_date}
     Assigned To: {assigned_to.name}

     Please take immediate action.
     ```

6. **Click "Save & Activate"**

---

#### Step 4.3: Status Change Notification

1. **Click "Create Automation"**

2. **Basic Information:**
   - **Name:** `ticket_status_notification`
   - **Display Name:** `Ticket Status Change Notification`
   - **Description:** `Notify customer when ticket status changes`

3. **Trigger Configuration:**
   - **Trigger Type:** Database Event
   - **Event:** onUpdate
   - **Entity:** `SupportTicket`
   - **Watch Fields:** `status`

4. **Conditions:**
   ```
   AND Group 1:
   - Field: status
   - Operator: in
   - Value: ['resolved', 'closed']
   ```

5. **Actions:**

   **Action 1: Create Public Comment**
   - Type: Create Record
   - Entity: `TicketComment`
   - Fields:
     - `ticket_id` = `{id}`
     - `comment_text` = `"Your ticket has been {status}. Resolution: {resolution_notes}"`
     - `comment_type` = `'Status Update'`
     - `is_public` = `true`

   **Action 2: Send Email to Customer**
   - Type: Send Email
   - Recipients: `{customer_email}`
   - Subject: `"Your Support Ticket #{ticket_number} - {status}"`
   - Body Template:
     ```
     Dear {customer_name},

     Your support ticket has been updated:

     Ticket Number: {ticket_number}
     Subject: {subject}
     Status: {status}

     Resolution Notes:
     {resolution_notes}

     If you have any questions, please reply to this email.

     Thank you,
     Support Team
     ```

6. **Click "Save & Activate"**

---

#### Step 4.4: Daily Ticket Summary Report

1. **Click "Create Automation"**

2. **Basic Information:**
   - **Name:** `daily_ticket_summary`
   - **Display Name:** `Daily Ticket Summary Email`
   - **Description:** `Send daily summary of ticket metrics to management`

3. **Trigger Configuration:**
   - **Trigger Type:** Scheduled
   - **Schedule:** Daily at 8:00 AM
   - **Cron Expression:** `0 8 * * *`

4. **Conditions:** (None - runs always)

5. **Actions:**

   **Action 1: Query Ticket Metrics**
   - Type: Query Data
   - Entity: `SupportTicket`
   - Aggregations:
     - COUNT(*) as total_tickets
     - COUNT(*) WHERE status='new' as new_tickets
     - COUNT(*) WHERE status='open' as open_tickets
     - COUNT(*) WHERE status='resolved' as resolved_today
     - COUNT(*) WHERE sla_due_date < NOW() as sla_violations
   - Filter: `created_at >= NOW() - INTERVAL '24 hours'`
   - Store Result As: `metrics`

   **Action 2: Send Summary Email**
   - Type: Send Email
   - Recipients: `support-manager@company.com`
   - Subject: `"Daily Support Ticket Summary - {TODAY}"`
   - Body Template:
     ```
     Daily Support Ticket Summary
     Date: {TODAY}

     📊 Metrics (Last 24 Hours):
     - Total Tickets: {metrics.total_tickets}
     - New Tickets: {metrics.new_tickets}
     - Open Tickets: {metrics.open_tickets}
     - Resolved Today: {metrics.resolved_today}
     - SLA Violations: {metrics.sla_violations}

     View full dashboard: [Dashboard Link]
     ```

6. **Click "Save & Activate"**

**✅ Checkpoint:** You should have 4 active automation rules. Check the Automation Dashboard to see execution history.

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

## Summary

Congratulations! You've successfully created a complete **Customer Support Ticket System** using ONLY the No-Code Platform.

### What You Built:
✅ 4 database entities with relationships
✅ 4 dynamic lookup configurations
✅ 1 approval workflow
✅ 4 automation rules
✅ Auto-generated CRUD UI
✅ 3 analytical reports
✅ 1 interactive dashboard
✅ Complete menu navigation
✅ Optional custom portal pages

### Skills You Learned:
- Data modeling with entity relationships
- Dynamic lookup configuration
- Visual workflow design
- Event-based automation
- Report creation with parameters
- Dashboard design with interactive widgets
- Menu management
- Page building with GrapeJS

### Next Steps:
1. **Enhance the module:**
   - Add customer satisfaction rating
   - Implement ticket merging
   - Add knowledge base integration
   - Create customer self-service portal

2. **Build another module:**
   - Inventory Management System
   - Employee Onboarding System
   - Project Management System
   - CRM System

3. **Explore advanced features:**
   - Custom calculated fields
   - Complex validation rules
   - External API integrations
   - Mobile app configuration

### Need Help?
- Check documentation: [NO-CODE-PLATFORM-DESIGN.md](NO-CODE-PLATFORM-DESIGN.md)
- Review phase docs: [NO-CODE-PHASE1.md](NO-CODE-PHASE1.md), [NO-CODE-PHASE2.md](NO-CODE-PHASE2.md)
- Contact platform admin for support

---

**Document Version:** 1.0
**Last Updated:** 2026-01-19
**Author:** Platform Team
**Next Review:** After first user feedback
