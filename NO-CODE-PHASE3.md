# No-Code Platform - Phase 3: Visual Designer Enhancement & Menu Consolidation

**Date:** 2026-01-15
**Last Updated:** 2026-01-18
**Project:** App-Buildify
**Phase:** 3 - Visual Designer Enhancement & Menu Consolidation
**Status:** ✅ **PRIORITY 3 COMPLETED** - Implementation: Option C (Priorities 1-3)

**Parent Document:** [NO-CODE-PLATFORM-DESIGN.md](NO-CODE-PLATFORM-DESIGN.md)
**Prerequisites:** Phase 1 and Phase 2 must be 100% complete ✅

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Phase 3 Objectives](#phase-3-objectives)
3. [Priority 1: Menu Consolidation & Designer Activation](#priority-1-menu-consolidation--designer-activation)
4. [Priority 2: Visual Report Designer Enhancement](#priority-2-visual-report-designer-enhancement)
5. [Priority 3: Visual Dashboard Designer Enhancement](#priority-3-visual-dashboard-designer-enhancement)
6. [Priority 4: Developer Tools Enhancement](#priority-4-developer-tools-enhancement)
7. [Implementation Roadmap](#implementation-roadmap)
8. [Testing Strategy](#testing-strategy)
9. [Success Metrics](#success-metrics)
10. [Rollback Plan](#rollback-plan)

---

## Executive Summary

**Goal:** Transform the No-Code Platform into a unified, visually intuitive system by consolidating menus, enabling existing designers, and creating best-in-class drag-and-drop experiences for reports and dashboards.

**Critical Discovery:**
- Report Designer (843 lines) and Dashboard Designer (709 lines) exist but are **NOT accessible from any menu**
- UI Builder, Menu Management, and Module Management are scattered across different menu sections
- Current designers use form-based configuration, not fully visual drag-and-drop

**Phase 3 Delivers:**
1. **Unified No-Code Platform Menu** - Single location for all configuration tools
2. **Enabled Report & Dashboard Designers** - Unlock 1,552 lines of existing code
3. **Visual Report Designer** - Drag-and-drop report creation with live preview
4. **Visual Dashboard Designer** - Canvas-based dashboard builder with widget palette
5. **Developer Tools Specifications** - Detailed feature definitions for future tools

**Implementation Decision:** **Option C** - Priorities 1-3 (8-10 weeks)
- Priority 1: Menu Consolidation & Designer Activation (1-2 weeks)
- Priority 2: Visual Report Designer Enhancement (3-4 weeks)
- Priority 3: Visual Dashboard Designer Enhancement (3-4 weeks)
- Priority 4: Documentation only - stakeholder review pending

**Duration:** 8-10 weeks
**Complexity:** Medium-High
**Team:** Frontend (2 developers), UX Designer, QA

---

## Phase 3 Objectives

### Primary Objectives

1. **Menu Consolidation** - Create unified No-Code Platform menu structure
2. **Designer Activation** - Make Report & Dashboard designers accessible
3. **Visual Enhancement** - Transform text-based to drag-and-drop interfaces
4. **User Experience** - 50-60% reduction in creation time
5. **Feature Documentation** - Detailed specifications for future tools

### Success Criteria

✅ **User Can:**
1. Access all no-code tools from single unified menu
2. Create reports using drag-and-drop interface with live preview
3. Build dashboards using canvas-based designer with widget palette
4. Complete report creation 50% faster than current process
5. Complete dashboard creation 60% faster than current process

✅ **System Has:**
1. Consolidated menu with logical groupings (Data, UI, Reports, Business Logic, Platform Config)
2. Fully functional Menu Sync UI
3. Cross-feature quick actions (Create Report, Add to Dashboard, etc.)
4. Template libraries (10+ report templates, 5+ dashboard templates)
5. Multi-device preview for dashboards

---

## Priority 1: Menu Consolidation & Designer Activation

**Duration:** 1-2 weeks
**Complexity:** Low-Medium
**Status:** 🚀 Starting First

### Overview

Reorganize the platform menu to consolidate all no-code configuration tools under a unified structure, enable existing but inaccessible Report & Dashboard designers, and complete the menu management workflow.

### Current State Analysis

**Existing Menu Structure:**
```
🔧 No-Code Platform (Current)
├── 🗄️ Data Model Designer
├── 🔄 Workflow Designer
├── 🤖 Automation Rules
└── 🔍 Lookup Configuration

👨‍💻 Developer Tools (Current)
├── 🖌️ Page Designer (UI Builder)
├── 📄 Manage Pages
├── 📦 Sample Reports & Dashboards
├── 🧩 Components Showcase
├── 🗂️ Schema Designer (placeholder - not implemented)
├── 🔌 API Playground (placeholder - not implemented)
└── ⚙️ Code Generator (placeholder - not implemented)

⚙️ System Management → System Settings (Current)
├── 📑 Menu Management
└── 🔄 Menu Sync (UI placeholder)

⚙️ System Management (Current)
└── 📦 Module Management

❌ Missing from Menu:
├── 📈 Report Designer (exists at 843 lines, no route registered)
├── 📊 Dashboard Designer (exists at 709 lines, no route registered)
├── 📋 Reports List (doesn't exist)
└── 🎯 Dashboards List (doesn't exist)
```

**Problems:**
1. UI Builder scattered in Developer Tools (should be in No-Code Platform)
2. System management tools separated from platform configuration
3. Report & Dashboard designers completely inaccessible
4. Placeholder items cluttering Developer Tools menu
5. No logical grouping of related features

---

### New Menu Structure (Fully Integrated)

```
🔧 No-Code Platform (NEW - CONSOLIDATED)
│
├── 📊 Data & Schema
│   ├── 🗄️ Data Model Designer
│   │   └── Quick Actions: [Create Report] [Create Page] [Add to Menu]
│   └── 🔍 Lookup Configuration
│
├── 🎨 UI & Pages
│   ├── 🖌️ Page Designer
│   │   └── Quick Actions: [Add to Menu] [Set Permissions]
│   ├── 📄 Manage Pages
│   └── 🧩 Components Showcase
│
├── 📈 Reports & Dashboards (NEW SECTION)
│   ├── ➕ Create Report (NEW - links to report-designer)
│   ├── 📋 My Reports (NEW - reports-list page)
│   ├── ➕ Create Dashboard (NEW - links to dashboard-designer)
│   ├── 🎯 My Dashboards (NEW - dashboards-list page)
│   └── 📦 Report Templates
│
├── ⚙️ Business Logic
│   ├── 🔄 Workflow Designer
│   │   └── Quick Actions: [Create Automation] [Add to Menu]
│   └── 🤖 Automation Rules
│       └── Quick Actions: [Schedule Report] [Trigger Workflow]
│
└── 🎛️ Platform Configuration (NEW SECTION)
    ├── 📑 Menu Management
    ├── 🔄 Menu Sync (NEW - functional UI)
    └── 📦 Module Management

👨‍💻 Developer Tools (CLEANED UP)
└── 📚 Sample Reports & Dashboards
    (Schema Designer, API Playground, Code Generator removed - pending implementation decision)
```

---

### Sub-Task 1: Menu Restructuring

#### 1.1 Update menu.json

**File:** `/frontend/config/menu.json`

**Action:** Replace existing No-Code Platform and Developer Tools sections

```json
{
  "menu": [
    {
      "code": "nocode-platform",
      "title": "No-Code Platform",
      "icon": "ph-duotone ph-stack",
      "iconColor": "text-purple-600",
      "permission": null,
      "children": [
        {
          "header": "Data & Schema",
          "headerClass": "text-xs font-semibold text-gray-500 uppercase tracking-wider px-4 py-2 mt-4"
        },
        {
          "title": "Data Model Designer",
          "route": "nocode-data-model",
          "icon": "ph-duotone ph-database",
          "iconColor": "text-blue-600",
          "permission": "data-model:read:tenant"
        },
        {
          "title": "Lookup Configuration",
          "route": "nocode-lookups",
          "icon": "ph-duotone ph-list-magnifying-glass",
          "iconColor": "text-green-600",
          "permission": "lookups:read:tenant"
        },
        {
          "header": "UI & Pages",
          "headerClass": "text-xs font-semibold text-gray-500 uppercase tracking-wider px-4 py-2 mt-4"
        },
        {
          "title": "Page Designer",
          "route": "builder",
          "icon": "ph-duotone ph-layout",
          "iconColor": "text-indigo-600",
          "permission": "builder:read:tenant"
        },
        {
          "title": "Manage Pages",
          "route": "builder-pages",
          "icon": "ph-duotone ph-files",
          "iconColor": "text-indigo-500",
          "permission": "builder:read:tenant"
        },
        {
          "title": "Components Showcase",
          "route": "components-showcase",
          "icon": "ph-duotone ph-squares-four",
          "iconColor": "text-cyan-600",
          "permission": null
        },
        {
          "header": "Reports & Dashboards",
          "headerClass": "text-xs font-semibold text-gray-500 uppercase tracking-wider px-4 py-2 mt-4"
        },
        {
          "title": "Create Report",
          "route": "report-designer",
          "icon": "ph-duotone ph-file-plus",
          "iconColor": "text-emerald-600",
          "permission": "reports:create:tenant",
          "badge": "NEW",
          "badgeColor": "bg-green-500"
        },
        {
          "title": "My Reports",
          "route": "reports-list",
          "icon": "ph-duotone ph-files",
          "iconColor": "text-emerald-500",
          "permission": "reports:read:tenant",
          "badge": "NEW",
          "badgeColor": "bg-green-500"
        },
        {
          "title": "Create Dashboard",
          "route": "dashboard-designer",
          "icon": "ph-duotone ph-squares-four",
          "iconColor": "text-violet-600",
          "permission": "dashboards:create:tenant",
          "badge": "NEW",
          "badgeColor": "bg-green-500"
        },
        {
          "title": "My Dashboards",
          "route": "dashboards-list",
          "icon": "ph-duotone ph-layout",
          "iconColor": "text-violet-500",
          "permission": "dashboards:read:tenant",
          "badge": "NEW",
          "badgeColor": "bg-green-500"
        },
        {
          "header": "Business Logic",
          "headerClass": "text-xs font-semibold text-gray-500 uppercase tracking-wider px-4 py-2 mt-4"
        },
        {
          "title": "Workflow Designer",
          "route": "nocode-workflows",
          "icon": "ph-duotone ph-flow-arrow",
          "iconColor": "text-orange-600",
          "permission": "workflows:read:tenant"
        },
        {
          "title": "Automation Rules",
          "route": "nocode-automations",
          "icon": "ph-duotone ph-lightning",
          "iconColor": "text-yellow-600",
          "permission": "automations:read:tenant"
        },
        {
          "header": "Platform Configuration",
          "headerClass": "text-xs font-semibold text-gray-500 uppercase tracking-wider px-4 py-2 mt-4"
        },
        {
          "title": "Menu Management",
          "route": "menu-management",
          "icon": "ph-duotone ph-list",
          "iconColor": "text-pink-600",
          "permission": "menu:manage:tenant"
        },
        {
          "title": "Menu Sync",
          "route": "settings-menu-sync",
          "icon": "ph-duotone ph-arrows-clockwise",
          "iconColor": "text-pink-500",
          "permission": "menu:manage:tenant"
        },
        {
          "title": "Module Management",
          "route": "modules",
          "icon": "ph-duotone ph-package",
          "iconColor": "text-red-600",
          "permission": "modules:manage:tenant"
        }
      ]
    },
    {
      "code": "developer-tools",
      "title": "Developer Tools",
      "icon": "ph-duotone ph-code",
      "iconColor": "text-gray-600",
      "permission": null,
      "children": [
        {
          "title": "Sample Reports & Dashboards",
          "route": "sample-reports-dashboards",
          "icon": "ph-duotone ph-presentation-chart",
          "iconColor": "text-blue-600",
          "permission": null
        }
      ]
    }
  ]
}
```

**Changes:**
- Added "Reports & Dashboards" section with 4 new items
- Moved Page Designer and Manage Pages from Developer Tools to No-Code Platform
- Added "Platform Configuration" section with Menu Management, Menu Sync, Module Management
- Removed placeholder items (Schema Designer, API Playground, Code Generator)
- Added "NEW" badges to report/dashboard items
- Added header sections for better organization

---

#### 1.2 Update i18n Translations

**Files to Update:**
- `/frontend/assets/i18n/en/menu.json`
- `/frontend/assets/i18n/de/menu.json`
- `/frontend/assets/i18n/es/menu.json`
- `/frontend/assets/i18n/fr/menu.json`
- `/frontend/assets/i18n/id/menu.json`

**English (en/menu.json):**
```json
{
  "nocode-platform": "No-Code Platform",
  "data-schema": "Data & Schema",
  "ui-pages": "UI & Pages",
  "reports-dashboards": "Reports & Dashboards",
  "business-logic": "Business Logic",
  "platform-configuration": "Platform Configuration",
  "create-report": "Create Report",
  "my-reports": "My Reports",
  "create-dashboard": "Create Dashboard",
  "my-dashboards": "My Dashboards",
  "page-designer": "Page Designer",
  "menu-sync": "Menu Sync"
}
```

**Similar translations for other languages...**

---

### Sub-Task 2: Enable Report & Dashboard Designers

#### 2.1 Register Routes in app.js

**File:** `/frontend/assets/js/app.js`

**Find the route handler section and add:**

```javascript
// Report Designer
if (route === 'report-designer') {
    document.title = 'Report Designer - App Buildify';

    // Load template and script
    await loadTemplate('report-designer.html');

    // Initialize report designer page
    if (typeof window.ReportDesignerPage !== 'undefined') {
        new window.ReportDesignerPage();
    } else {
        // Dynamically load script if not already loaded
        await loadScript('/frontend/assets/js/report-designer-page.js');
        new window.ReportDesignerPage();
    }
}

// Reports List
if (route === 'reports-list') {
    document.title = 'My Reports - App Buildify';

    await loadTemplate('reports-list.html');
    await loadScript('/frontend/assets/js/reports-list-page.js');
    new window.ReportsListPage();
}

// Dashboard Designer
if (route === 'dashboard-designer') {
    document.title = 'Dashboard Designer - App Buildify';

    await loadTemplate('dashboard-designer.html');
    await loadScript('/frontend/assets/js/dashboard-designer-page.js');
    new window.DashboardDesignerPage();
}

// Dashboards List
if (route === 'dashboards-list') {
    document.title = 'My Dashboards - App Buildify';

    await loadTemplate('dashboards-list.html');
    await loadScript('/frontend/assets/js/dashboards-list-page.js');
    new window.DashboardsListPage();
}
```

**Helper function to add (if not exists):**
```javascript
async function loadScript(src) {
    return new Promise((resolve, reject) => {
        // Check if already loaded
        if (document.querySelector(`script[src="${src}"]`)) {
            resolve();
            return;
        }

        const script = document.createElement('script');
        script.src = src;
        script.onload = resolve;
        script.onerror = reject;
        document.head.appendChild(script);
    });
}
```

---

#### 2.2 Create Reports List Page

**Create File:** `/frontend/assets/templates/reports-list.html`

```html
<div class="container mx-auto p-6">
    <!-- Header -->
    <div class="flex justify-between items-center mb-6">
        <div>
            <h1 class="text-2xl font-bold text-gray-900">My Reports</h1>
            <p class="text-sm text-gray-600 mt-1">Create, manage, and execute custom reports</p>
        </div>
        <button id="create-report-btn" class="btn btn-primary">
            <i class="ph-duotone ph-plus mr-2"></i>
            Create Report
        </button>
    </div>

    <!-- Filters -->
    <div class="card p-4 mb-6">
        <div class="flex gap-4 items-end">
            <div class="flex-1">
                <label class="block text-sm font-medium text-gray-700 mb-1">Search Reports</label>
                <input
                    type="text"
                    id="search-reports"
                    class="form-input"
                    placeholder="Search by name or description..."
                />
            </div>
            <div class="w-48">
                <label class="block text-sm font-medium text-gray-700 mb-1">Category</label>
                <select id="filter-category" class="form-select">
                    <option value="">All Categories</option>
                    <option value="sales">Sales</option>
                    <option value="financial">Financial</option>
                    <option value="operational">Operational</option>
                    <option value="custom">Custom</option>
                </select>
            </div>
            <button id="clear-filters-btn" class="btn btn-secondary">
                Clear Filters
            </button>
        </div>
    </div>

    <!-- Reports Table -->
    <div class="card">
        <div id="reports-table-container"></div>
    </div>
</div>
```

**Create File:** `/frontend/assets/js/reports-list-page.js`

```javascript
class ReportsListPage {
    constructor() {
        this.table = null;
        this.init();
    }

    async init() {
        // Create button handler
        document.getElementById('create-report-btn').addEventListener('click', () => {
            window.location.hash = '#/report-designer';
        });

        // Search handler
        document.getElementById('search-reports').addEventListener('input', (e) => {
            this.table.search(e.target.value);
        });

        // Filter handler
        document.getElementById('filter-category').addEventListener('change', (e) => {
            if (e.target.value) {
                this.table.filter({ category: e.target.value });
            } else {
                this.table.clearFilters();
            }
        });

        // Clear filters handler
        document.getElementById('clear-filters-btn').addEventListener('click', () => {
            document.getElementById('search-reports').value = '';
            document.getElementById('filter-category').value = '';
            this.table.clearFilters();
            this.table.search('');
        });

        // Initialize table
        this.initTable();
    }

    async initTable() {
        const container = document.getElementById('reports-table-container');

        this.table = new DynamicTable(container, {
            entity: 'report_definitions',
            apiEndpoint: '/api/v1/reports/definitions',
            config: {
                columns: [
                    {
                        name: 'name',
                        label: 'Report Name',
                        sortable: true,
                        render: (value, row) => {
                            return `
                                <div>
                                    <div class="font-medium text-gray-900">${value}</div>
                                    <div class="text-sm text-gray-500">${row.description || ''}</div>
                                </div>
                            `;
                        }
                    },
                    {
                        name: 'category',
                        label: 'Category',
                        sortable: true,
                        render: (value) => {
                            const colors = {
                                'sales': 'bg-blue-100 text-blue-800',
                                'financial': 'bg-green-100 text-green-800',
                                'operational': 'bg-orange-100 text-orange-800',
                                'custom': 'bg-purple-100 text-purple-800'
                            };
                            const color = colors[value] || 'bg-gray-100 text-gray-800';
                            return `<span class="px-2 py-1 text-xs font-medium rounded ${color}">${value || 'Uncategorized'}</span>`;
                        }
                    },
                    {
                        name: 'data_source',
                        label: 'Data Source',
                        sortable: true
                    },
                    {
                        name: 'created_by_name',
                        label: 'Created By',
                        sortable: false
                    },
                    {
                        name: 'created_at',
                        label: 'Created',
                        type: 'datetime',
                        sortable: true
                    },
                    {
                        name: 'updated_at',
                        label: 'Modified',
                        type: 'datetime',
                        sortable: true
                    }
                ],
                defaultSort: { column: 'updated_at', direction: 'desc' },
                pageSize: 25
            },
            actions: {
                view: {
                    label: 'Run Report',
                    icon: 'ph-play',
                    handler: (row) => {
                        window.location.hash = `#/report-viewer/${row.id}`;
                    }
                },
                edit: {
                    label: 'Edit',
                    icon: 'ph-pencil',
                    handler: (row) => {
                        window.location.hash = `#/report-designer?id=${row.id}`;
                    }
                },
                duplicate: {
                    label: 'Duplicate',
                    icon: 'ph-copy',
                    handler: async (row) => {
                        if (confirm(`Duplicate report "${row.name}"?`)) {
                            try {
                                const response = await apiFetch(`/api/v1/reports/definitions/${row.id}/duplicate`, {
                                    method: 'POST'
                                });
                                showNotification('Report duplicated successfully', 'success');
                                this.table.refresh();
                            } catch (error) {
                                showNotification('Failed to duplicate report: ' + error.message, 'error');
                            }
                        }
                    }
                },
                addToDashboard: {
                    label: 'Add to Dashboard',
                    icon: 'ph-squares-four',
                    handler: (row) => {
                        // Open dashboard selector modal
                        this.showAddToDashboardModal(row);
                    }
                },
                delete: {
                    label: 'Delete',
                    icon: 'ph-trash',
                    className: 'text-red-600 hover:text-red-800',
                    handler: async (row) => {
                        if (confirm(`Delete report "${row.name}"? This action cannot be undone.`)) {
                            try {
                                await apiFetch(`/api/v1/reports/definitions/${row.id}`, {
                                    method: 'DELETE'
                                });
                                showNotification('Report deleted successfully', 'success');
                                this.table.refresh();
                            } catch (error) {
                                showNotification('Failed to delete report: ' + error.message, 'error');
                            }
                        }
                    }
                }
            }
        });

        this.table.render();
    }

    showAddToDashboardModal(report) {
        // TODO: Implement dashboard selector modal
        // For now, just navigate to dashboard designer
        const confirmed = confirm(`Add "${report.name}" to a dashboard?\n\nYou'll be redirected to select or create a dashboard.`);
        if (confirmed) {
            window.location.hash = `#/dashboard-designer?addReport=${report.id}`;
        }
    }
}

// Export to global scope
window.ReportsListPage = ReportsListPage;
```

---

#### 2.3 Create Dashboards List Page

**Create File:** `/frontend/assets/templates/dashboards-list.html`

```html
<div class="container mx-auto p-6">
    <!-- Header -->
    <div class="flex justify-between items-center mb-6">
        <div>
            <h1 class="text-2xl font-bold text-gray-900">My Dashboards</h1>
            <p class="text-sm text-gray-600 mt-1">Create and manage interactive dashboards</p>
        </div>
        <button id="create-dashboard-btn" class="btn btn-primary">
            <i class="ph-duotone ph-plus mr-2"></i>
            Create Dashboard
        </button>
    </div>

    <!-- View Toggle -->
    <div class="flex justify-between items-center mb-6">
        <div class="flex gap-2">
            <button id="view-grid-btn" class="btn btn-secondary active">
                <i class="ph-duotone ph-grid-four"></i>
                Grid
            </button>
            <button id="view-list-btn" class="btn btn-secondary">
                <i class="ph-duotone ph-list"></i>
                List
            </button>
        </div>

        <div class="flex gap-4">
            <input
                type="text"
                id="search-dashboards"
                class="form-input w-64"
                placeholder="Search dashboards..."
            />
        </div>
    </div>

    <!-- Grid View (Default) -->
    <div id="dashboards-grid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <!-- Dashboard cards will be rendered here -->
    </div>

    <!-- List View (Hidden by default) -->
    <div id="dashboards-list" class="card hidden">
        <div id="dashboards-table-container"></div>
    </div>
</div>
```

**Create File:** `/frontend/assets/js/dashboards-list-page.js`

```javascript
class DashboardsListPage {
    constructor() {
        this.dashboards = [];
        this.viewMode = 'grid'; // 'grid' or 'list'
        this.table = null;
        this.init();
    }

    async init() {
        // Create button handler
        document.getElementById('create-dashboard-btn').addEventListener('click', () => {
            window.location.hash = '#/dashboard-designer';
        });

        // View toggle handlers
        document.getElementById('view-grid-btn').addEventListener('click', () => {
            this.switchView('grid');
        });

        document.getElementById('view-list-btn').addEventListener('click', () => {
            this.switchView('list');
        });

        // Search handler
        document.getElementById('search-dashboards').addEventListener('input', (e) => {
            if (this.viewMode === 'grid') {
                this.filterGrid(e.target.value);
            } else {
                this.table.search(e.target.value);
            }
        });

        // Load dashboards
        await this.loadDashboards();
        this.renderGrid();
    }

    async loadDashboards() {
        try {
            const response = await apiFetch('/api/v1/dashboards');
            this.dashboards = response.items || response;
        } catch (error) {
            showNotification('Failed to load dashboards: ' + error.message, 'error');
            this.dashboards = [];
        }
    }

    switchView(mode) {
        this.viewMode = mode;

        // Update button states
        document.getElementById('view-grid-btn').classList.toggle('active', mode === 'grid');
        document.getElementById('view-list-btn').classList.toggle('active', mode === 'list');

        // Show/hide views
        document.getElementById('dashboards-grid').classList.toggle('hidden', mode === 'list');
        document.getElementById('dashboards-list').classList.toggle('hidden', mode === 'grid');

        if (mode === 'list' && !this.table) {
            this.initTable();
        }
    }

    renderGrid() {
        const container = document.getElementById('dashboards-grid');

        if (this.dashboards.length === 0) {
            container.innerHTML = `
                <div class="col-span-full text-center py-12">
                    <i class="ph-duotone ph-squares-four text-6xl text-gray-300 mb-4"></i>
                    <p class="text-gray-500 mb-4">No dashboards yet</p>
                    <button onclick="window.location.hash='#/dashboard-designer'" class="btn btn-primary">
                        Create Your First Dashboard
                    </button>
                </div>
            `;
            return;
        }

        container.innerHTML = this.dashboards.map(dashboard => `
            <div class="card hover:shadow-lg transition-shadow cursor-pointer dashboard-card" data-id="${dashboard.id}">
                <div class="p-6">
                    <!-- Thumbnail/Preview -->
                    <div class="w-full h-48 bg-gradient-to-br from-blue-50 to-purple-50 rounded-lg mb-4 flex items-center justify-center">
                        ${dashboard.thumbnail_url ?
                            `<img src="${dashboard.thumbnail_url}" alt="${dashboard.name}" class="w-full h-full object-cover rounded-lg" />` :
                            `<i class="ph-duotone ph-squares-four text-6xl text-gray-300"></i>`
                        }
                    </div>

                    <!-- Dashboard Info -->
                    <h3 class="text-lg font-semibold text-gray-900 mb-2">${dashboard.name}</h3>
                    <p class="text-sm text-gray-600 mb-4 line-clamp-2">${dashboard.description || 'No description'}</p>

                    <!-- Meta Info -->
                    <div class="flex items-center justify-between text-xs text-gray-500 mb-4">
                        <span>${dashboard.pages_count || 0} pages</span>
                        <span>${dashboard.widgets_count || 0} widgets</span>
                        <span>Updated ${this.formatDate(dashboard.updated_at)}</span>
                    </div>

                    <!-- Actions -->
                    <div class="flex gap-2">
                        <button
                            onclick="window.location.hash='#/dashboard-viewer/${dashboard.id}'"
                            class="btn btn-primary flex-1 text-sm"
                        >
                            <i class="ph-duotone ph-eye mr-1"></i>
                            View
                        </button>
                        <button
                            onclick="window.location.hash='#/dashboard-designer?id=${dashboard.id}'"
                            class="btn btn-secondary text-sm"
                        >
                            <i class="ph-duotone ph-pencil"></i>
                        </button>
                        <button
                            onclick="window.dashboardsListPage.deleteDashboard('${dashboard.id}', '${dashboard.name}')"
                            class="btn btn-secondary text-sm text-red-600 hover:text-red-800"
                        >
                            <i class="ph-duotone ph-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `).join('');

        // Add click handlers to cards
        container.querySelectorAll('.dashboard-card').forEach(card => {
            card.addEventListener('click', (e) => {
                // Only navigate if clicking on card background, not buttons
                if (e.target === card || e.target.closest('.card') === card) {
                    const dashboardId = card.dataset.id;
                    window.location.hash = `#/dashboard-viewer/${dashboardId}`;
                }
            });
        });
    }

    filterGrid(searchTerm) {
        const cards = document.querySelectorAll('.dashboard-card');
        const term = searchTerm.toLowerCase();

        cards.forEach(card => {
            const dashboard = this.dashboards.find(d => d.id === card.dataset.id);
            const matches = dashboard.name.toLowerCase().includes(term) ||
                          (dashboard.description || '').toLowerCase().includes(term);
            card.classList.toggle('hidden', !matches);
        });
    }

    async initTable() {
        const container = document.getElementById('dashboards-table-container');

        this.table = new DynamicTable(container, {
            entity: 'dashboards',
            apiEndpoint: '/api/v1/dashboards',
            config: {
                columns: [
                    {
                        name: 'name',
                        label: 'Dashboard Name',
                        sortable: true,
                        render: (value, row) => {
                            return `
                                <div>
                                    <div class="font-medium text-gray-900">${value}</div>
                                    <div class="text-sm text-gray-500">${row.description || ''}</div>
                                </div>
                            `;
                        }
                    },
                    {
                        name: 'pages_count',
                        label: 'Pages',
                        sortable: true
                    },
                    {
                        name: 'widgets_count',
                        label: 'Widgets',
                        sortable: true
                    },
                    {
                        name: 'theme',
                        label: 'Theme',
                        sortable: true
                    },
                    {
                        name: 'is_public',
                        label: 'Public',
                        type: 'boolean',
                        sortable: true
                    },
                    {
                        name: 'updated_at',
                        label: 'Last Modified',
                        type: 'datetime',
                        sortable: true
                    }
                ],
                defaultSort: { column: 'updated_at', direction: 'desc' },
                pageSize: 25
            },
            actions: {
                view: {
                    label: 'View',
                    icon: 'ph-eye',
                    handler: (row) => {
                        window.location.hash = `#/dashboard-viewer/${row.id}`;
                    }
                },
                edit: {
                    label: 'Edit',
                    icon: 'ph-pencil',
                    handler: (row) => {
                        window.location.hash = `#/dashboard-designer?id=${row.id}`;
                    }
                },
                duplicate: {
                    label: 'Duplicate',
                    icon: 'ph-copy',
                    handler: async (row) => {
                        if (confirm(`Duplicate dashboard "${row.name}"?`)) {
                            try {
                                const response = await apiFetch(`/api/v1/dashboards/${row.id}/clone`, {
                                    method: 'POST'
                                });
                                showNotification('Dashboard duplicated successfully', 'success');
                                this.table.refresh();
                            } catch (error) {
                                showNotification('Failed to duplicate dashboard: ' + error.message, 'error');
                            }
                        }
                    }
                },
                share: {
                    label: 'Share',
                    icon: 'ph-share-network',
                    handler: (row) => {
                        this.showShareModal(row);
                    }
                },
                delete: {
                    label: 'Delete',
                    icon: 'ph-trash',
                    className: 'text-red-600 hover:text-red-800',
                    handler: async (row) => {
                        await this.deleteDashboard(row.id, row.name);
                    }
                }
            }
        });

        this.table.render();
    }

    async deleteDashboard(id, name) {
        if (confirm(`Delete dashboard "${name}"? This action cannot be undone.`)) {
            try {
                await apiFetch(`/api/v1/dashboards/${id}`, { method: 'DELETE' });
                showNotification('Dashboard deleted successfully', 'success');

                // Reload and refresh view
                await this.loadDashboards();
                if (this.viewMode === 'grid') {
                    this.renderGrid();
                } else {
                    this.table.refresh();
                }
            } catch (error) {
                showNotification('Failed to delete dashboard: ' + error.message, 'error');
            }
        }
    }

    showShareModal(dashboard) {
        // TODO: Implement share modal
        alert('Share functionality coming soon!');
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

        if (diffDays === 0) return 'Today';
        if (diffDays === 1) return 'Yesterday';
        if (diffDays < 7) return `${diffDays} days ago`;
        if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
        if (diffDays < 365) return `${Math.floor(diffDays / 30)} months ago`;
        return date.toLocaleDateString();
    }
}

// Export to global scope
window.DashboardsListPage = DashboardsListPage;
window.dashboardsListPage = null;

// Initialize when route loads
document.addEventListener('route:loaded', () => {
    if (window.location.hash.includes('dashboards-list')) {
        window.dashboardsListPage = new DashboardsListPage();
    }
});
```

---

### Sub-Task 3: Menu Sync UI Implementation

**Update File:** `/frontend/assets/templates/settings-menu-sync.html`

Replace placeholder content with functional UI:

```html
<div class="container mx-auto p-6 max-w-5xl">
    <!-- Header -->
    <div class="mb-6">
        <h1 class="text-2xl font-bold text-gray-900 mb-2">Menu Sync</h1>
        <p class="text-sm text-gray-600">
            Synchronize menu configuration from menu.json to database.
            This imports the menu structure defined in <code class="bg-gray-100 px-1 py-0.5 rounded">frontend/config/menu.json</code> into the database.
        </p>
    </div>

    <!-- Sync Configuration Card -->
    <div class="card p-6 mb-6">
        <h3 class="text-lg font-semibold text-gray-900 mb-4">
            <i class="ph-duotone ph-gear mr-2"></i>
            Sync Configuration
        </h3>

        <div class="space-y-4">
            <!-- Clear Existing Checkbox -->
            <div class="flex items-start">
                <input
                    type="checkbox"
                    id="clear-existing-checkbox"
                    class="checkbox mt-1"
                />
                <div class="ml-3">
                    <label for="clear-existing-checkbox" class="text-sm font-medium text-gray-700">
                        Clear existing menu items before sync
                    </label>
                    <p class="text-sm text-gray-500 mt-1">
                        <i class="ph ph-warning text-orange-500 mr-1"></i>
                        Warning: This will remove all custom menu items and dynamic menu entries (from modules, builder pages, etc.)
                    </p>
                </div>
            </div>

            <!-- Current Menu Info -->
            <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div class="flex items-start">
                    <i class="ph-duotone ph-info text-blue-600 text-xl mr-3 mt-0.5"></i>
                    <div>
                        <p class="text-sm font-medium text-blue-900 mb-2">Current Menu Status</p>
                        <div id="menu-status-info" class="text-sm text-blue-800 space-y-1">
                            <div><span class="font-medium">Total Menu Items:</span> <span id="total-menu-items">Loading...</span></div>
                            <div><span class="font-medium">System Menus:</span> <span id="system-menu-items">Loading...</span></div>
                            <div><span class="font-medium">Tenant Menus:</span> <span id="tenant-menu-items">Loading...</span></div>
                            <div><span class="font-medium">Module Menus:</span> <span id="module-menu-items">Loading...</span></div>
                            <div><span class="font-medium">Builder Page Menus:</span> <span id="builder-menu-items">Loading...</span></div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Sync Button -->
            <div class="flex gap-3">
                <button id="sync-menu-btn" class="btn btn-primary">
                    <i class="ph-duotone ph-arrows-clockwise mr-2"></i>
                    Sync Menu Now
                </button>
                <button id="preview-sync-btn" class="btn btn-secondary">
                    <i class="ph-duotone ph-eye mr-2"></i>
                    Preview Changes
                </button>
            </div>
        </div>
    </div>

    <!-- Sync Progress (Hidden initially) -->
    <div id="sync-progress-card" class="card p-6 mb-6 hidden">
        <h3 class="text-lg font-semibold text-gray-900 mb-4">
            <i class="ph-duotone ph-spinner-gap animate-spin mr-2"></i>
            Synchronizing...
        </h3>
        <div class="space-y-2">
            <div class="w-full bg-gray-200 rounded-full h-2">
                <div id="sync-progress-bar" class="bg-blue-600 h-2 rounded-full transition-all" style="width: 0%"></div>
            </div>
            <p id="sync-progress-text" class="text-sm text-gray-600">Initializing...</p>
        </div>
    </div>

    <!-- Sync Result (Hidden initially) -->
    <div id="sync-result-card" class="card p-6 mb-6 hidden">
        <h3 class="text-lg font-semibold text-gray-900 mb-4">
            <i id="sync-result-icon" class="ph-duotone ph-check-circle text-green-600 mr-2"></i>
            <span id="sync-result-title">Sync Complete</span>
        </h3>
        <div id="sync-result-content" class="space-y-2 text-sm">
            <!-- Result details will be populated here -->
        </div>
    </div>

    <!-- Sync History Card -->
    <div class="card p-6">
        <div class="flex justify-between items-center mb-4">
            <h3 class="text-lg font-semibold text-gray-900">
                <i class="ph-duotone ph-clock-clockwise mr-2"></i>
                Sync History
            </h3>
            <button id="refresh-history-btn" class="btn btn-sm btn-secondary">
                <i class="ph-duotone ph-arrows-clockwise mr-1"></i>
                Refresh
            </button>
        </div>

        <div id="sync-history-container">
            <!-- History table will be rendered here -->
        </div>
    </div>
</div>
```

**Create File:** `/frontend/assets/js/settings-menu-sync-page.js`

```javascript
class MenuSyncPage {
    constructor() {
        this.init();
    }

    async init() {
        // Load current menu status
        await this.loadMenuStatus();

        // Event listeners
        document.getElementById('sync-menu-btn').addEventListener('click', () => {
            this.syncMenu();
        });

        document.getElementById('preview-sync-btn').addEventListener('click', () => {
            this.previewSync();
        });

        document.getElementById('refresh-history-btn').addEventListener('click', () => {
            this.loadSyncHistory();
        });

        // Load sync history
        await this.loadSyncHistory();
    }

    async loadMenuStatus() {
        try {
            const response = await apiFetch('/api/v1/menu/admin');
            const menus = response.items || response;

            // Calculate statistics
            const stats = {
                total: menus.length,
                system: menus.filter(m => !m.tenant_id).length,
                tenant: menus.filter(m => m.tenant_id && !m.module_code && !m.is_builder_page).length,
                module: menus.filter(m => m.module_code).length,
                builder: menus.filter(m => m.is_builder_page).length
            };

            // Update UI
            document.getElementById('total-menu-items').textContent = stats.total;
            document.getElementById('system-menu-items').textContent = stats.system;
            document.getElementById('tenant-menu-items').textContent = stats.tenant;
            document.getElementById('module-menu-items').textContent = stats.module;
            document.getElementById('builder-menu-items').textContent = stats.builder;
        } catch (error) {
            console.error('Failed to load menu status:', error);
            document.getElementById('total-menu-items').textContent = 'Error';
        }
    }

    async previewSync() {
        // TODO: Implement preview functionality
        // This would show a diff of what would change
        alert('Preview functionality coming soon!\n\nThis will show:\n- Menu items to be added\n- Menu items to be updated\n- Menu items to be removed (if clear existing is checked)');
    }

    async syncMenu() {
        const clearExisting = document.getElementById('clear-existing-checkbox').checked;

        // Confirm if clearing existing
        if (clearExisting) {
            const confirmed = confirm(
                'Are you sure you want to clear all existing menu items?\n\n' +
                'This will remove:\n' +
                '• All custom menu items\n' +
                '• All module-generated menus\n' +
                '• All builder page menus\n\n' +
                'This action cannot be undone!'
            );
            if (!confirmed) return;
        }

        // Show progress card
        document.getElementById('sync-progress-card').classList.remove('hidden');
        document.getElementById('sync-result-card').classList.add('hidden');
        document.getElementById('sync-menu-btn').disabled = true;

        try {
            // Update progress
            this.updateProgress(20, 'Reading menu.json...');
            await this.delay(500);

            // Call sync API
            this.updateProgress(50, 'Synchronizing menu items...');
            const response = await apiFetch('/api/v1/menu/sync', {
                method: 'POST',
                body: JSON.stringify({ clear_existing: clearExisting })
            });

            this.updateProgress(80, 'Finalizing...');
            await this.delay(500);

            this.updateProgress(100, 'Complete!');
            await this.delay(500);

            // Hide progress, show result
            document.getElementById('sync-progress-card').classList.add('hidden');
            this.showSyncResult(true, response);

            // Reload menu status and history
            await this.loadMenuStatus();
            await this.loadSyncHistory();

            // Reload page menu (force menu refresh)
            if (window.menuService) {
                await window.menuService.loadMenu();
            }

        } catch (error) {
            console.error('Sync failed:', error);
            document.getElementById('sync-progress-card').classList.add('hidden');
            this.showSyncResult(false, { error: error.message });
        } finally {
            document.getElementById('sync-menu-btn').disabled = false;
        }
    }

    updateProgress(percent, text) {
        document.getElementById('sync-progress-bar').style.width = `${percent}%`;
        document.getElementById('sync-progress-text').textContent = text;
    }

    showSyncResult(success, data) {
        const resultCard = document.getElementById('sync-result-card');
        const resultIcon = document.getElementById('sync-result-icon');
        const resultTitle = document.getElementById('sync-result-title');
        const resultContent = document.getElementById('sync-result-content');

        resultCard.classList.remove('hidden');

        if (success) {
            resultIcon.className = 'ph-duotone ph-check-circle text-green-600 mr-2';
            resultTitle.textContent = 'Sync Complete';
            resultContent.innerHTML = `
                <div class="text-green-800">
                    <p class="font-medium mb-2">Menu synchronization completed successfully!</p>
                    <ul class="list-disc list-inside space-y-1">
                        <li>Menu items synced: ${data.items_synced || 0}</li>
                        <li>Items created: ${data.items_created || 0}</li>
                        <li>Items updated: ${data.items_updated || 0}</li>
                        ${data.items_deleted ? `<li>Items deleted: ${data.items_deleted}</li>` : ''}
                    </ul>
                    <p class="mt-3 text-sm">
                        <i class="ph-duotone ph-info mr-1"></i>
                        The menu will be automatically refreshed.
                    </p>
                </div>
            `;
        } else {
            resultIcon.className = 'ph-duotone ph-x-circle text-red-600 mr-2';
            resultTitle.textContent = 'Sync Failed';
            resultContent.innerHTML = `
                <div class="text-red-800">
                    <p class="font-medium mb-2">Menu synchronization failed</p>
                    <p class="text-sm">${data.error || 'Unknown error occurred'}</p>
                </div>
            `;
        }
    }

    async loadSyncHistory() {
        const container = document.getElementById('sync-history-container');

        try {
            // Get audit logs for menu sync operations
            const response = await apiFetch('/api/v1/audit/logs?entity_type=menu&action=sync&limit=10');
            const logs = response.items || response;

            if (logs.length === 0) {
                container.innerHTML = `
                    <div class="text-center py-8 text-gray-500">
                        <i class="ph-duotone ph-clock-clockwise text-4xl mb-2"></i>
                        <p>No sync history yet</p>
                    </div>
                `;
                return;
            }

            // Render history table
            container.innerHTML = `
                <div class="overflow-x-auto">
                    <table class="min-w-full divide-y divide-gray-200">
                        <thead class="bg-gray-50">
                            <tr>
                                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">User</th>
                                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Clear Existing</th>
                                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Items Synced</th>
                                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                            </tr>
                        </thead>
                        <tbody class="bg-white divide-y divide-gray-200">
                            ${logs.map(log => `
                                <tr>
                                    <td class="px-4 py-3 text-sm text-gray-900">
                                        ${new Date(log.created_at).toLocaleString()}
                                    </td>
                                    <td class="px-4 py-3 text-sm text-gray-900">
                                        ${log.user_name || 'System'}
                                    </td>
                                    <td class="px-4 py-3 text-sm">
                                        ${log.changes?.clear_existing ?
                                            '<span class="text-orange-600">Yes</span>' :
                                            '<span class="text-gray-600">No</span>'}
                                    </td>
                                    <td class="px-4 py-3 text-sm text-gray-900">
                                        ${log.changes?.items_synced || 0}
                                    </td>
                                    <td class="px-4 py-3 text-sm">
                                        ${log.status === 'success' ?
                                            '<span class="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded">Success</span>' :
                                            '<span class="px-2 py-1 text-xs font-medium bg-red-100 text-red-800 rounded">Failed</span>'}
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `;
        } catch (error) {
            console.error('Failed to load sync history:', error);
            container.innerHTML = `
                <div class="text-center py-8 text-red-500">
                    <i class="ph-duotone ph-warning text-4xl mb-2"></i>
                    <p>Failed to load sync history</p>
                </div>
            `;
        }
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Export to global scope
window.MenuSyncPage = MenuSyncPage;

// Initialize when route loads
document.addEventListener('route:loaded', () => {
    if (window.location.hash.includes('settings-menu-sync')) {
        new MenuSyncPage();
    }
});
```

---

### Sub-Task 4: Cross-Feature Quick Actions

Add quick action buttons to existing pages to improve workflow efficiency.

#### 4.1 Data Model Designer Quick Actions

**File:** `/frontend/assets/js/nocode-data-model.js`

Find the entity actions section and add quick action buttons:

```javascript
// Add to entity list actions
renderEntityActions(entity) {
    return `
        <div class="flex gap-2">
            <button
                onclick="editEntity('${entity.id}')"
                class="btn btn-sm btn-secondary"
                title="Edit Entity"
            >
                <i class="ph-duotone ph-pencil"></i>
            </button>

            <!-- NEW: Create Report Quick Action -->
            <button
                onclick="createReportForEntity('${entity.id}', '${entity.name}')"
                class="btn btn-sm btn-secondary"
                title="Create Report on this Entity"
            >
                <i class="ph-duotone ph-chart-bar text-emerald-600"></i>
            </button>

            <!-- NEW: Create Page Quick Action -->
            <button
                onclick="createPageForEntity('${entity.id}', '${entity.name}')"
                class="btn btn-sm btn-secondary"
                title="Create Page for this Entity"
            >
                <i class="ph-duotone ph-layout text-indigo-600"></i>
            </button>

            <!-- NEW: Add to Menu Quick Action -->
            <button
                onclick="addEntityToMenu('${entity.id}', '${entity.name}')"
                class="btn btn-sm btn-secondary"
                title="Add to Menu"
            >
                <i class="ph-duotone ph-list text-pink-600"></i>
            </button>

            <button
                onclick="deleteEntity('${entity.id}')"
                class="btn btn-sm btn-secondary text-red-600"
                title="Delete Entity"
            >
                <i class="ph-duotone ph-trash"></i>
            </button>
        </div>
    `;
}

// NEW: Quick action handlers
function createReportForEntity(entityId, entityName) {
    // Navigate to report designer with entity pre-selected
    window.location.hash = `#/report-designer?entity=${entityName}`;
}

function createPageForEntity(entityId, entityName) {
    // Navigate to page designer with entity pre-selected
    window.location.hash = `#/builder?entity=${entityName}`;
}

function addEntityToMenu(entityId, entityName) {
    // Navigate to menu management with add dialog
    window.location.hash = `#/menu-management?addEntity=${entityName}`;
}
```

---

#### 4.2 Report Designer Quick Actions

**File:** `/frontend/components/report-designer.js`

Add "Add to Dashboard" button in the preview step:

```javascript
// In renderPreviewStep() method, add button after report preview
renderPreviewStep() {
    return `
        <div class="space-y-6">
            <!-- Existing preview content -->
            <div id="report-preview-container">
                <!-- Report preview renders here -->
            </div>

            <!-- NEW: Quick Actions -->
            <div class="flex gap-3 justify-end">
                <button
                    id="add-to-dashboard-btn"
                    class="btn btn-secondary"
                >
                    <i class="ph-duotone ph-squares-four mr-2"></i>
                    Add to Dashboard
                </button>

                <button
                    id="create-automation-btn"
                    class="btn btn-secondary"
                >
                    <i class="ph-duotone ph-lightning mr-2"></i>
                    Create Automation
                </button>

                <button
                    id="save-report-btn"
                    class="btn btn-primary"
                >
                    <i class="ph-duotone ph-floppy-disk mr-2"></i>
                    Save Report
                </button>
            </div>
        </div>
    `;
}

// NEW: Quick action handlers
initQuickActions() {
    document.getElementById('add-to-dashboard-btn')?.addEventListener('click', async () => {
        // Save report first
        const reportId = await this.saveReport();

        // Navigate to dashboard designer with report pre-selected
        window.location.hash = `#/dashboard-designer?addReport=${reportId}`;
    });

    document.getElementById('create-automation-btn')?.addEventListener('click', async () => {
        // Save report first
        const reportId = await this.saveReport();

        // Navigate to automation designer with report trigger
        window.location.hash = `#/nocode-automations?reportId=${reportId}`;
    });
}
```

---

#### 4.3 Dashboard Designer Quick Actions

**File:** `/frontend/components/dashboard-designer.js`

Add "Add to Menu" and "Schedule Delivery" buttons:

```javascript
// In render() method, add quick actions to the header
renderHeader() {
    return `
        <div class="flex justify-between items-center mb-6">
            <div>
                <h1 class="text-2xl font-bold">Dashboard Designer</h1>
                <p class="text-sm text-gray-600">Create interactive dashboards</p>
            </div>

            <div class="flex gap-2">
                <!-- NEW: Quick Actions -->
                <button
                    id="add-to-menu-btn"
                    class="btn btn-secondary"
                >
                    <i class="ph-duotone ph-list mr-2"></i>
                    Add to Menu
                </button>

                <button
                    id="schedule-delivery-btn"
                    class="btn btn-secondary"
                >
                    <i class="ph-duotone ph-calendar-clock mr-2"></i>
                    Schedule Delivery
                </button>

                <button
                    id="save-dashboard-btn"
                    class="btn btn-primary"
                >
                    <i class="ph-duotone ph-floppy-disk mr-2"></i>
                    Save Dashboard
                </button>
            </div>
        </div>
    `;
}

// NEW: Quick action handlers
initQuickActions() {
    document.getElementById('add-to-menu-btn')?.addEventListener('click', async () => {
        const dashboardId = await this.saveDashboard();
        window.location.hash = `#/menu-management?addDashboard=${dashboardId}`;
    });

    document.getElementById('schedule-delivery-btn')?.addEventListener('click', async () => {
        const dashboardId = await this.saveDashboard();
        // Open schedule modal or navigate to automation
        this.showScheduleModal(dashboardId);
    });
}
```

---

### Priority 1 Deliverables

**Files Created:**
1. `/frontend/assets/templates/reports-list.html` (new)
2. `/frontend/assets/js/reports-list-page.js` (new)
3. `/frontend/assets/templates/dashboards-list.html` (new)
4. `/frontend/assets/js/dashboards-list-page.js` (new)
5. `/frontend/assets/js/settings-menu-sync-page.js` (new)

**Files Modified:**
1. `/frontend/config/menu.json` (restructured)
2. `/frontend/assets/i18n/*/menu.json` (5 files - translations)
3. `/frontend/assets/js/app.js` (added 4 routes)
4. `/frontend/assets/templates/settings-menu-sync.html` (replaced placeholder)
5. `/frontend/assets/js/nocode-data-model.js` (added quick actions)
6. `/frontend/components/report-designer.js` (added quick actions)
7. `/frontend/components/dashboard-designer.js` (added quick actions)

**Total:**
- 5 new files (~800 lines)
- 7 modified files (~150 lines changed)

**Testing Checklist:**
- [ ] Menu structure loads correctly
- [ ] All menu items accessible
- [ ] Report Designer loads from menu
- [ ] Dashboard Designer loads from menu
- [ ] Reports List displays correctly
- [ ] Dashboards List displays correctly (grid and list views)
- [ ] Menu Sync UI functional
- [ ] Quick actions work in Data Model Designer
- [ ] Quick actions work in Report Designer
- [ ] Quick actions work in Dashboard Designer
- [ ] i18n translations display correctly
- [ ] All permissions enforced

---

## Priority 2: Visual Report Designer Enhancement

**Duration:** 3-4 weeks
**Complexity:** High
**Status:** After Priority 1

### Overview

Transform the existing form-based report configuration into a fully visual drag-and-drop experience with live preview, making report creation 50% faster and more intuitive.

### Current Report Designer Analysis

**Existing File:** `/frontend/components/report-designer.js` (843 lines)

**Current Architecture:**
```javascript
class ReportDesigner {
    constructor(container) {
        this.currentStep = 1;
        this.totalSteps = 5;
        this.reportData = {
            name: '',
            description: '',
            data_source: '',
            columns: [],
            parameters: [],
            formatting: {},
            visualization_config: {}
        };
    }

    // Current steps (form-based)
    steps = [
        { id: 1, title: 'Data Source', render: this.renderDataSourceStep },
        { id: 2, title: 'Columns', render: this.renderColumnsStep },
        { id: 3, title: 'Parameters', render: this.renderParametersStep },
        { id: 4, title: 'Formatting', render: this.renderFormattingStep },
        { id: 5, title: 'Preview', render: this.renderPreviewStep }
    ];
}
```

**Current Features:**
- ✅ 5-step wizard
- ✅ NoCode entity support
- ✅ Export formats (PDF, Excel, CSV, JSON, HTML)
- ✅ Scheduling and caching
- ✅ Parameter support
- ❌ Text-based configuration (dropdowns, text inputs)
- ❌ No visual data source builder
- ❌ No drag-and-drop column designer
- ❌ No live preview
- ❌ No template library

---

### Enhancement 1: Visual Data Source Builder (Week 1)

**Goal:** Replace dropdown data source selection with interactive entity relationship diagram

#### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Visual Data Source Builder                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────┐        ┌──────────────────┐         │
│  │  Entity Palette  │        │  Canvas Area     │         │
│  │                  │        │                  │         │
│  │  ┌────────┐      │        │  ┌─────────┐    │         │
│  │  │Customer│      │───────>│  │Customer │    │         │
│  │  └────────┘      │        │  └────┬────┘    │         │
│  │                  │        │       │          │         │
│  │  ┌────────┐      │        │  ┌────▼────┐    │         │
│  │  │ Order  │      │        │  │ Order   │    │         │
│  │  └────────┘      │        │  └─────────┘    │         │
│  │                  │        │                  │         │
│  └──────────────────┘        └──────────────────┘         │
│                                                             │
│  Filter Builder: [Add Filter] [AND] [OR]                   │
│  Preview Data: [Show Sample Data (10 rows)]                │
└─────────────────────────────────────────────────────────────┘
```

#### Implementation

**Create Component:** `/frontend/components/visual-data-source-builder.js`

```javascript
class VisualDataSourceBuilder {
    constructor(container, options = {}) {
        this.container = container;
        this.options = options;
        this.entities = [];
        this.selectedEntities = [];
        this.joins = [];
        this.filters = [];
        this.cy = null; // Cytoscape instance

        this.init();
    }

    async init() {
        await this.loadEntities();
        this.render();
        this.initCytoscape();
    }

    async loadEntities() {
        try {
            // Load both system and nocode entities
            const [systemEntities, nocodeEntities] = await Promise.all([
                apiFetch('/api/v1/metadata/entities'),
                apiFetch('/api/v1/data-model/entities?status=published')
            ]);

            this.entities = [
                ...systemEntities.map(e => ({ ...e, type: 'system' })),
                ...nocodeEntities.map(e => ({
                    entity_name: e.name,
                    display_name: e.label,
                    fields: e.fields,
                    type: 'nocode'
                }))
            ];
        } catch (error) {
            console.error('Failed to load entities:', error);
            this.entities = [];
        }
    }

    render() {
        this.container.innerHTML = `
            <div class="visual-data-source-builder h-full flex">
                <!-- Left Panel: Entity Palette -->
                <div class="w-64 border-r border-gray-200 bg-gray-50 p-4 overflow-y-auto">
                    <div class="mb-4">
                        <input
                            type="text"
                            id="entity-search"
                            class="form-input w-full text-sm"
                            placeholder="Search entities..."
                        />
                    </div>

                    <div class="space-y-2" id="entity-palette">
                        ${this.renderEntityPalette()}
                    </div>
                </div>

                <!-- Center: Canvas -->
                <div class="flex-1 flex flex-col">
                    <!-- Toolbar -->
                    <div class="border-b border-gray-200 p-3 flex justify-between items-center bg-white">
                        <div class="flex gap-2">
                            <button id="clear-canvas-btn" class="btn btn-sm btn-secondary">
                                <i class="ph-duotone ph-trash mr-1"></i>
                                Clear
                            </button>
                            <button id="auto-layout-btn" class="btn btn-sm btn-secondary">
                                <i class="ph-duotone ph-chart-scatter mr-1"></i>
                                Auto Layout
                            </button>
                        </div>
                        <div class="flex gap-2">
                            <button id="zoom-in-btn" class="btn btn-sm btn-secondary">
                                <i class="ph-duotone ph-magnifying-glass-plus"></i>
                            </button>
                            <button id="zoom-out-btn" class="btn btn-sm btn-secondary">
                                <i class="ph-duotone ph-magnifying-glass-minus"></i>
                            </button>
                            <button id="fit-btn" class="btn btn-sm btn-secondary">
                                <i class="ph-duotone ph-arrows-out"></i>
                            </button>
                        </div>
                    </div>

                    <!-- Cytoscape Canvas -->
                    <div id="cytoscape-canvas" class="flex-1 bg-white"></div>

                    <!-- Bottom Panel: Preview Data -->
                    <div class="border-t border-gray-200 bg-white">
                        <button
                            id="toggle-preview-btn"
                            class="w-full p-3 text-left font-medium text-gray-700 hover:bg-gray-50 flex justify-between items-center"
                        >
                            <span>
                                <i class="ph-duotone ph-table mr-2"></i>
                                Preview Data (10 rows)
                            </span>
                            <i class="ph ph-caret-up" id="preview-caret"></i>
                        </button>
                        <div id="preview-data-container" class="p-4 max-h-64 overflow-auto hidden">
                            <!-- Data preview table will be rendered here -->
                        </div>
                    </div>
                </div>

                <!-- Right Panel: Properties -->
                <div class="w-80 border-l border-gray-200 bg-gray-50 p-4 overflow-y-auto">
                    <h3 class="font-semibold text-gray-900 mb-4">Properties</h3>

                    <!-- Selected Entities -->
                    <div class="mb-6">
                        <h4 class="text-sm font-medium text-gray-700 mb-2">Selected Entities</h4>
                        <div id="selected-entities-list" class="space-y-2">
                            ${this.renderSelectedEntities()}
                        </div>
                    </div>

                    <!-- Joins -->
                    <div class="mb-6">
                        <div class="flex justify-between items-center mb-2">
                            <h4 class="text-sm font-medium text-gray-700">Joins</h4>
                            <button id="add-join-btn" class="btn btn-xs btn-secondary">
                                <i class="ph-duotone ph-plus"></i>
                            </button>
                        </div>
                        <div id="joins-list" class="space-y-2">
                            ${this.renderJoins()}
                        </div>
                    </div>

                    <!-- Filters -->
                    <div>
                        <div class="flex justify-between items-center mb-2">
                            <h4 class="text-sm font-medium text-gray-700">Filters</h4>
                            <button id="add-filter-btn" class="btn btn-xs btn-secondary">
                                <i class="ph-duotone ph-plus"></i>
                            </button>
                        </div>
                        <div id="filters-list" class="space-y-2">
                            ${this.renderFilters()}
                        </div>
                    </div>
                </div>
            </div>
        `;

        this.attachEventListeners();
    }

    renderEntityPalette() {
        if (this.entities.length === 0) {
            return '<p class="text-sm text-gray-500">No entities available</p>';
        }

        return this.entities.map(entity => `
            <div
                class="entity-palette-item p-3 bg-white border border-gray-200 rounded cursor-move hover:border-blue-500 hover:shadow transition-all"
                draggable="true"
                data-entity="${entity.entity_name}"
            >
                <div class="flex items-center">
                    <i class="ph-duotone ph-database text-blue-600 mr-2"></i>
                    <div class="flex-1">
                        <div class="text-sm font-medium text-gray-900">${entity.display_name}</div>
                        <div class="text-xs text-gray-500">${entity.type}</div>
                    </div>
                </div>
            </div>
        `).join('');
    }

    renderSelectedEntities() {
        if (this.selectedEntities.length === 0) {
            return '<p class="text-xs text-gray-500">Drag entities from left</p>';
        }

        return this.selectedEntities.map(entity => `
            <div class="p-2 bg-white border border-gray-200 rounded flex justify-between items-center">
                <span class="text-sm text-gray-900">${entity.display_name}</span>
                <button
                    onclick="visualDataSourceBuilder.removeEntity('${entity.entity_name}')"
                    class="text-red-600 hover:text-red-800"
                >
                    <i class="ph ph-x"></i>
                </button>
            </div>
        `).join('');
    }

    renderJoins() {
        if (this.joins.length === 0) {
            return '<p class="text-xs text-gray-500">No joins defined</p>';
        }

        return this.joins.map((join, index) => `
            <div class="p-2 bg-white border border-gray-200 rounded">
                <div class="flex justify-between items-start mb-2">
                    <span class="text-xs font-medium text-gray-700">${join.type}</span>
                    <button
                        onclick="visualDataSourceBuilder.removeJoin(${index})"
                        class="text-red-600 hover:text-red-800"
                    >
                        <i class="ph ph-x text-xs"></i>
                    </button>
                </div>
                <div class="text-xs text-gray-600">
                    ${join.from_entity}.${join.from_field} = ${join.to_entity}.${join.to_field}
                </div>
            </div>
        `).join('');
    }

    renderFilters() {
        if (this.filters.length === 0) {
            return '<p class="text-xs text-gray-500">No filters defined</p>';
        }

        return this.filters.map((filter, index) => `
            <div class="p-2 bg-white border border-gray-200 rounded">
                <div class="flex justify-between items-start mb-2">
                    <span class="text-xs font-medium text-gray-700">${filter.field}</span>
                    <button
                        onclick="visualDataSourceBuilder.removeFilter(${index})"
                        class="text-red-600 hover:text-red-800"
                    >
                        <i class="ph ph-x text-xs"></i>
                    </button>
                </div>
                <div class="text-xs text-gray-600">
                    ${filter.operator} ${filter.value}
                </div>
            </div>
        `).join('');
    }

    initCytoscape() {
        // Initialize Cytoscape.js for graph visualization
        // Load Cytoscape.js library dynamically if not loaded
        if (typeof cytoscape === 'undefined') {
            this.loadCytoscapeLibrary().then(() => {
                this.createCytoscapeInstance();
            });
        } else {
            this.createCytoscapeInstance();
        }
    }

    async loadCytoscapeLibrary() {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = 'https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.26.0/cytoscape.min.js';
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }

    createCytoscapeInstance() {
        const container = document.getElementById('cytoscape-canvas');

        this.cy = cytoscape({
            container: container,
            elements: [],
            style: [
                {
                    selector: 'node',
                    style: {
                        'label': 'data(label)',
                        'text-valign': 'center',
                        'text-halign': 'center',
                        'background-color': '#3B82F6',
                        'color': '#fff',
                        'font-size': '12px',
                        'width': '120px',
                        'height': '60px',
                        'shape': 'roundrectangle'
                    }
                },
                {
                    selector: 'edge',
                    style: {
                        'width': 2,
                        'line-color': '#9CA3AF',
                        'target-arrow-color': '#9CA3AF',
                        'target-arrow-shape': 'triangle',
                        'curve-style': 'bezier',
                        'label': 'data(label)',
                        'font-size': '10px',
                        'text-rotation': 'autorotate',
                        'text-margin-y': -10
                    }
                }
            ],
            layout: {
                name: 'grid',
                padding: 50
            }
        });

        // Enable panning and zooming
        this.cy.userPanningEnabled(true);
        this.cy.userZoomingEnabled(true);
    }

    attachEventListeners() {
        // Entity palette drag
        document.querySelectorAll('.entity-palette-item').forEach(item => {
            item.addEventListener('dragstart', (e) => {
                e.dataTransfer.setData('entity', e.target.dataset.entity);
            });
        });

        // Canvas drop
        const canvas = document.getElementById('cytoscape-canvas');
        canvas.addEventListener('dragover', (e) => {
            e.preventDefault();
        });

        canvas.addEventListener('drop', (e) => {
            e.preventDefault();
            const entityName = e.dataTransfer.getData('entity');
            this.addEntityToCanvas(entityName);
        });

        // Toolbar buttons
        document.getElementById('clear-canvas-btn')?.addEventListener('click', () => {
            this.clearCanvas();
        });

        document.getElementById('auto-layout-btn')?.addEventListener('click', () => {
            this.autoLayout();
        });

        document.getElementById('zoom-in-btn')?.addEventListener('click', () => {
            this.cy.zoom(this.cy.zoom() * 1.2);
        });

        document.getElementById('zoom-out-btn')?.addEventListener('click', () => {
            this.cy.zoom(this.cy.zoom() * 0.8);
        });

        document.getElementById('fit-btn')?.addEventListener('click', () => {
            this.cy.fit(50);
        });

        // Preview toggle
        document.getElementById('toggle-preview-btn')?.addEventListener('click', () => {
            const container = document.getElementById('preview-data-container');
            const caret = document.getElementById('preview-caret');
            container.classList.toggle('hidden');
            caret.classList.toggle('ph-caret-up');
            caret.classList.toggle('ph-caret-down');

            if (!container.classList.contains('hidden')) {
                this.loadPreviewData();
            }
        });

        // Add join/filter buttons
        document.getElementById('add-join-btn')?.addEventListener('click', () => {
            this.showAddJoinDialog();
        });

        document.getElementById('add-filter-btn')?.addEventListener('click', () => {
            this.showAddFilterDialog();
        });

        // Entity search
        document.getElementById('entity-search')?.addEventListener('input', (e) => {
            this.filterEntityPalette(e.target.value);
        });
    }

    addEntityToCanvas(entityName) {
        const entity = this.entities.find(e => e.entity_name === entityName);
        if (!entity) return;

        // Check if already added
        if (this.selectedEntities.find(e => e.entity_name === entityName)) {
            showNotification('Entity already added', 'warning');
            return;
        }

        // Add to selected entities
        this.selectedEntities.push(entity);

        // Add node to Cytoscape
        this.cy.add({
            group: 'nodes',
            data: {
                id: entityName,
                label: entity.display_name
            }
        });

        // Auto layout
        this.autoLayout();

        // Refresh UI
        document.getElementById('selected-entities-list').innerHTML = this.renderSelectedEntities();
    }

    removeEntity(entityName) {
        // Remove from selected entities
        this.selectedEntities = this.selectedEntities.filter(e => e.entity_name !== entityName);

        // Remove node from Cytoscape
        this.cy.getElementById(entityName).remove();

        // Remove related joins
        this.joins = this.joins.filter(j => j.from_entity !== entityName && j.to_entity !== entityName);

        // Refresh UI
        document.getElementById('selected-entities-list').innerHTML = this.renderSelectedEntities();
        document.getElementById('joins-list').innerHTML = this.renderJoins();
    }

    clearCanvas() {
        this.selectedEntities = [];
        this.joins = [];
        this.filters = [];
        this.cy.elements().remove();

        document.getElementById('selected-entities-list').innerHTML = this.renderSelectedEntities();
        document.getElementById('joins-list').innerHTML = this.renderJoins();
        document.getElementById('filters-list').innerHTML = this.renderFilters();
    }

    autoLayout() {
        this.cy.layout({
            name: 'breadthfirst',
            directed: true,
            padding: 50,
            spacingFactor: 1.5
        }).run();
    }

    showAddJoinDialog() {
        if (this.selectedEntities.length < 2) {
            showNotification('Add at least 2 entities first', 'warning');
            return;
        }

        // TODO: Implement join dialog
        // For now, show simple modal
        alert('Join dialog coming soon!');
    }

    showAddFilterDialog() {
        if (this.selectedEntities.length === 0) {
            showNotification('Add at least 1 entity first', 'warning');
            return;
        }

        // TODO: Implement filter dialog (use existing visual filter builder from Automation Rules)
        alert('Filter dialog coming soon!');
    }

    async loadPreviewData() {
        const container = document.getElementById('preview-data-container');
        container.innerHTML = '<p class="text-sm text-gray-500">Loading preview data...</p>';

        try {
            // Build query from selected entities, joins, filters
            const query = this.buildQuery();

            // Execute query and get preview data
            const response = await apiFetch('/api/v1/reports/preview', {
                method: 'POST',
                body: JSON.stringify({
                    query: query,
                    limit: 10
                })
            });

            // Render data table
            container.innerHTML = this.renderDataTable(response.data, response.columns);
        } catch (error) {
            console.error('Failed to load preview data:', error);
            container.innerHTML = '<p class="text-sm text-red-500">Failed to load preview data</p>';
        }
    }

    renderDataTable(data, columns) {
        if (!data || data.length === 0) {
            return '<p class="text-sm text-gray-500">No data available</p>';
        }

        return `
            <table class="min-w-full divide-y divide-gray-200 text-sm">
                <thead class="bg-gray-50">
                    <tr>
                        ${columns.map(col => `
                            <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">${col}</th>
                        `).join('')}
                    </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                    ${data.map(row => `
                        <tr>
                            ${columns.map(col => `
                                <td class="px-3 py-2 whitespace-nowrap text-gray-900">${row[col] || '-'}</td>
                            `).join('')}
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    }

    filterEntityPalette(searchTerm) {
        const term = searchTerm.toLowerCase();
        document.querySelectorAll('.entity-palette-item').forEach(item => {
            const entityName = item.dataset.entity;
            const entity = this.entities.find(e => e.entity_name === entityName);
            const matches = entity.display_name.toLowerCase().includes(term) ||
                          entity.entity_name.toLowerCase().includes(term);
            item.style.display = matches ? 'block' : 'none';
        });
    }

    buildQuery() {
        // Build SQL-like query from visual configuration
        // This will be used by the backend to execute the report
        return {
            entities: this.selectedEntities.map(e => e.entity_name),
            joins: this.joins,
            filters: this.filters
        };
    }

    getConfiguration() {
        return {
            entities: this.selectedEntities,
            joins: this.joins,
            filters: this.filters,
            query: this.buildQuery()
        };
    }
}

// Export to global scope
window.VisualDataSourceBuilder = VisualDataSourceBuilder;
```

**Integration with Report Designer:**

Modify `/frontend/components/report-designer.js`:

```javascript
renderDataSourceStep() {
    return `
        <div class="space-y-6">
            <div class="flex justify-between items-center">
                <h3 class="text-lg font-semibold">Select Data Source</h3>
                <div class="flex gap-2">
                    <button
                        id="toggle-visual-mode-btn"
                        class="btn btn-sm btn-secondary"
                    >
                        <i class="ph-duotone ph-chart-scatter mr-1"></i>
                        Visual Mode
                    </button>
                </div>
            </div>

            <!-- Traditional dropdown (default) -->
            <div id="traditional-data-source" class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Entity</label>
                    <select id="data-source-select" class="form-select">
                        <option value="">Select an entity...</option>
                        <!-- Options populated dynamically -->
                    </select>
                </div>
            </div>

            <!-- Visual Data Source Builder (hidden by default) -->
            <div id="visual-data-source" class="hidden" style="height: 600px;">
                <!-- VisualDataSourceBuilder renders here -->
            </div>
        </div>
    `;
}

// Toggle between traditional and visual mode
toggleDataSourceMode() {
    const traditional = document.getElementById('traditional-data-source');
    const visual = document.getElementById('visual-data-source');
    const btn = document.getElementById('toggle-visual-mode-btn');

    if (visual.classList.contains('hidden')) {
        // Switch to visual mode
        traditional.classList.add('hidden');
        visual.classList.remove('hidden');
        btn.innerHTML = '<i class="ph-duotone ph-list mr-1"></i> Traditional Mode';

        // Initialize visual builder if not already
        if (!this.visualDataSourceBuilder) {
            this.visualDataSourceBuilder = new VisualDataSourceBuilder(visual);
        }
    } else {
        // Switch to traditional mode
        visual.classList.add('hidden');
        traditional.classList.remove('hidden');
        btn.innerHTML = '<i class="ph-duotone ph-chart-scatter mr-1"></i> Visual Mode';
    }
}
```

---

### Enhancement 2: Drag-and-Drop Column Designer (Week 1)

**Goal:** Replace form-based column selection with visual drag-and-drop interface

#### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Drag-and-Drop Column Designer                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐  ┌────────────────┐  ┌────────────────┐     │
│  │Available │  │    Selected    │  │   Properties   │     │
│  │  Fields  │  │    Columns     │  │                │     │
│  │          │  │                │  │  Name: ....    │     │
│  │ [Drag me]│──>│  [Col 1]      │  │  Format: ...   │     │
│  │ [Field2] │  │  [Col 2]      │  │  Aggregate:... │     │
│  │ [Field3] │  │  [Col 3]      │  │  Alias: ...    │     │
│  │   ...    │  │                │  │                │     │
│  └──────────┘  └────────────────┘  └────────────────┘     │
│                                                             │
│  Quick Actions: [Add All] [Clear All] [Group by Entity]    │
└─────────────────────────────────────────────────────────────┘
```

#### Implementation

**Create Component:** `/frontend/components/drag-drop-column-designer.js`

```javascript
class DragDropColumnDesigner {
    constructor(container, options = {}) {
        this.container = container;
        this.options = options;
        this.availableFields = [];
        this.selectedColumns = [];
        this.currentColumn = null;

        this.init();
    }

    async init() {
        await this.loadAvailableFields();
        this.render();
        this.attachEventListeners();
    }

    async loadAvailableFields() {
        // Get available fields from selected entities
        const entities = this.options.entities || [];

        this.availableFields = [];
        for (const entity of entities) {
            try {
                const metadata = await apiFetch(`/api/v1/metadata/entities/${entity}`);
                const fields = metadata.fields || [];

                fields.forEach(field => {
                    this.availableFields.push({
                        entity: entity,
                        name: field.name,
                        label: field.label,
                        type: field.type,
                        displayName: `${entity}.${field.name}`
                    });
                });
            } catch (error) {
                console.error(`Failed to load fields for ${entity}:`, error);
            }
        }
    }

    render() {
        this.container.innerHTML = `
            <div class="drag-drop-column-designer flex gap-4 h-full">
                <!-- Left Panel: Available Fields -->
                <div class="w-80 border border-gray-200 rounded-lg bg-white">
                    <div class="border-b border-gray-200 p-4">
                        <h3 class="font-semibold text-gray-900 mb-3">Available Fields</h3>
                        <input
                            type="text"
                            id="field-search"
                            class="form-input w-full text-sm"
                            placeholder="Search fields..."
                        />
                    </div>
                    <div class="p-4 overflow-y-auto" style="max-height: 500px;" id="available-fields-list">
                        ${this.renderAvailableFields()}
                    </div>
                </div>

                <!-- Center Panel: Selected Columns -->
                <div class="flex-1 border border-gray-200 rounded-lg bg-white">
                    <div class="border-b border-gray-200 p-4 flex justify-between items-center">
                        <h3 class="font-semibold text-gray-900">Selected Columns</h3>
                        <div class="flex gap-2">
                            <button id="add-all-btn" class="btn btn-xs btn-secondary">
                                <i class="ph-duotone ph-plus mr-1"></i>
                                Add All
                            </button>
                            <button id="clear-all-btn" class="btn btn-xs btn-secondary">
                                <i class="ph-duotone ph-trash mr-1"></i>
                                Clear All
                            </button>
                        </div>
                    </div>
                    <div class="p-4" id="selected-columns-list">
                        ${this.renderSelectedColumns()}
                    </div>
                </div>

                <!-- Right Panel: Column Properties -->
                <div class="w-96 border border-gray-200 rounded-lg bg-white">
                    <div class="border-b border-gray-200 p-4">
                        <h3 class="font-semibold text-gray-900">Column Properties</h3>
                    </div>
                    <div class="p-4 overflow-y-auto" style="max-height: 500px;" id="column-properties">
                        ${this.renderColumnProperties()}
                    </div>
                </div>
            </div>
        `;

        this.attachEventListeners();
    }

    renderAvailableFields() {
        if (this.availableFields.length === 0) {
            return '<p class="text-sm text-gray-500">No fields available. Select a data source first.</p>';
        }

        // Group by entity
        const groupedFields = {};
        this.availableFields.forEach(field => {
            if (!groupedFields[field.entity]) {
                groupedFields[field.entity] = [];
            }
            groupedFields[field.entity].push(field);
        });

        return Object.entries(groupedFields).map(([entity, fields]) => `
            <div class="mb-4">
                <h4 class="text-xs font-semibold text-gray-700 uppercase mb-2">${entity}</h4>
                <div class="space-y-1">
                    ${fields.map(field => `
                        <div
                            class="field-item p-2 bg-gray-50 border border-gray-200 rounded cursor-move hover:border-blue-500 hover:bg-blue-50 transition-all"
                            draggable="true"
                            data-field='${JSON.stringify(field)}'
                        >
                            <div class="flex items-center justify-between">
                                <div class="flex items-center">
                                    <i class="ph-duotone ph-database text-gray-400 mr-2 text-sm"></i>
                                    <span class="text-sm text-gray-900">${field.label}</span>
                                </div>
                                <button
                                    class="add-field-btn text-blue-600 hover:text-blue-800"
                                    data-field='${JSON.stringify(field)}'
                                >
                                    <i class="ph-duotone ph-plus text-sm"></i>
                                </button>
                            </div>
                            <div class="text-xs text-gray-500 mt-1">${field.type}</div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `).join('');
    }

    renderSelectedColumns() {
        if (this.selectedColumns.length === 0) {
            return `
                <div class="text-center py-12">
                    <i class="ph-duotone ph-arrow-left text-4xl text-gray-300 mb-2"></i>
                    <p class="text-sm text-gray-500">Drag fields here or click + to add</p>
                </div>
            `;
        }

        return `
            <div class="space-y-2" id="sortable-columns">
                ${this.selectedColumns.map((column, index) => `
                    <div
                        class="column-item p-3 bg-gray-50 border border-gray-200 rounded cursor-move hover:border-blue-500 transition-all ${this.currentColumn === index ? 'border-blue-500 bg-blue-50' : ''}"
                        draggable="true"
                        data-index="${index}"
                        onclick="dragDropColumnDesigner.selectColumn(${index})"
                    >
                        <div class="flex items-center justify-between">
                            <div class="flex items-center flex-1">
                                <i class="ph-duotone ph-dots-six-vertical text-gray-400 mr-2 cursor-move"></i>
                                <div class="flex-1">
                                    <div class="text-sm font-medium text-gray-900">${column.alias || column.label}</div>
                                    <div class="text-xs text-gray-500">${column.displayName}</div>
                                </div>
                            </div>
                            <div class="flex items-center gap-2">
                                ${column.aggregate ? `<span class="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">${column.aggregate}</span>` : ''}
                                ${column.format ? `<span class="px-2 py-1 text-xs bg-green-100 text-green-800 rounded">${column.format}</span>` : ''}
                                <button
                                    class="text-red-600 hover:text-red-800"
                                    onclick="dragDropColumnDesigner.removeColumn(${index}); event.stopPropagation();"
                                >
                                    <i class="ph ph-x"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    renderColumnProperties() {
        if (this.currentColumn === null || !this.selectedColumns[this.currentColumn]) {
            return '<p class="text-sm text-gray-500">Select a column to edit properties</p>';
        }

        const column = this.selectedColumns[this.currentColumn];

        return `
            <div class="space-y-4">
                <!-- Column Name -->
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Column Name</label>
                    <input
                        type="text"
                        id="column-alias"
                        class="form-input w-full"
                        value="${column.alias || column.label}"
                        placeholder="Column display name"
                    />
                </div>

                <!-- Original Field -->
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Original Field</label>
                    <input
                        type="text"
                        class="form-input w-full bg-gray-50"
                        value="${column.displayName}"
                        readonly
                    />
                </div>

                <!-- Data Type -->
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Data Type</label>
                    <input
                        type="text"
                        class="form-input w-full bg-gray-50"
                        value="${column.type}"
                        readonly
                    />
                </div>

                <!-- Aggregate Function -->
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Aggregate</label>
                    <select id="column-aggregate" class="form-select w-full">
                        <option value="">None</option>
                        <option value="SUM" ${column.aggregate === 'SUM' ? 'selected' : ''}>SUM</option>
                        <option value="AVG" ${column.aggregate === 'AVG' ? 'selected' : ''}>AVG</option>
                        <option value="COUNT" ${column.aggregate === 'COUNT' ? 'selected' : ''}>COUNT</option>
                        <option value="MIN" ${column.aggregate === 'MIN' ? 'selected' : ''}>MIN</option>
                        <option value="MAX" ${column.aggregate === 'MAX' ? 'selected' : ''}>MAX</option>
                    </select>
                </div>

                <!-- Format -->
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Format</label>
                    <select id="column-format" class="form-select w-full">
                        <option value="">Default</option>
                        <option value="currency" ${column.format === 'currency' ? 'selected' : ''}>Currency</option>
                        <option value="percent" ${column.format === 'percent' ? 'selected' : ''}>Percent</option>
                        <option value="number" ${column.format === 'number' ? 'selected' : ''}>Number (1,000)</option>
                        <option value="date" ${column.format === 'date' ? 'selected' : ''}>Date (MM/DD/YYYY)</option>
                        <option value="datetime" ${column.format === 'datetime' ? 'selected' : ''}>Date Time</option>
                        <option value="boolean" ${column.format === 'boolean' ? 'selected' : ''}>Boolean (Yes/No)</option>
                    </select>
                </div>

                <!-- Sortable -->
                <div class="flex items-center">
                    <input
                        type="checkbox"
                        id="column-sortable"
                        class="checkbox mr-2"
                        ${column.sortable !== false ? 'checked' : ''}
                    />
                    <label for="column-sortable" class="text-sm text-gray-700">Allow sorting</label>
                </div>

                <!-- Width -->
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Column Width (optional)</label>
                    <input
                        type="text"
                        id="column-width"
                        class="form-input w-full"
                        value="${column.width || ''}"
                        placeholder="e.g., 200px or 20%"
                    />
                </div>

                <!-- Visual Preview -->
                <div class="border-t border-gray-200 pt-4">
                    <h4 class="text-sm font-medium text-gray-700 mb-2">Preview</h4>
                    <div class="bg-gray-50 border border-gray-200 rounded p-3">
                        <div class="text-sm font-medium text-gray-900 mb-1">${column.alias || column.label}</div>
                        <div class="text-xs text-gray-600">${this.getFormatPreview(column)}</div>
                    </div>
                </div>
            </div>
        `;
    }

    getFormatPreview(column) {
        const sampleValues = {
            'string': 'Sample Text',
            'integer': column.format === 'currency' ? '$1,234.56' :
                      column.format === 'percent' ? '75%' :
                      column.format === 'number' ? '1,234' : '1234',
            'decimal': column.format === 'currency' ? '$1,234.56' : '1234.56',
            'date': column.format === 'date' ? '01/15/2026' : '2026-01-15',
            'datetime': column.format === 'datetime' ? '01/15/2026 10:30 AM' : '2026-01-15 10:30:00',
            'boolean': column.format === 'boolean' ? 'Yes' : 'true'
        };

        return sampleValues[column.type] || 'Sample Value';
    }

    attachEventListeners() {
        // Field search
        document.getElementById('field-search')?.addEventListener('input', (e) => {
            this.filterAvailableFields(e.target.value);
        });

        // Add all / Clear all
        document.getElementById('add-all-btn')?.addEventListener('click', () => {
            this.addAllFields();
        });

        document.getElementById('clear-all-btn')?.addEventListener('click', () => {
            this.clearAllColumns();
        });

        // Drag and drop for available fields
        document.querySelectorAll('.field-item').forEach(item => {
            item.addEventListener('dragstart', (e) => {
                e.dataTransfer.setData('field', item.dataset.field);
            });
        });

        // Add field buttons
        document.querySelectorAll('.add-field-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const field = JSON.parse(btn.dataset.field);
                this.addColumn(field);
            });
        });

        // Drop zone for selected columns
        const dropZone = document.getElementById('selected-columns-list');
        dropZone?.addEventListener('dragover', (e) => {
            e.preventDefault();
        });

        dropZone?.addEventListener('drop', (e) => {
            e.preventDefault();
            const fieldData = e.dataTransfer.getData('field');
            if (fieldData) {
                const field = JSON.parse(fieldData);
                this.addColumn(field);
            }
        });

        // Sortable columns (drag to reorder)
        document.querySelectorAll('.column-item').forEach(item => {
            item.addEventListener('dragstart', (e) => {
                e.dataTransfer.setData('columnIndex', item.dataset.index);
            });

            item.addEventListener('dragover', (e) => {
                e.preventDefault();
            });

            item.addEventListener('drop', (e) => {
                e.preventDefault();
                const fromIndex = parseInt(e.dataTransfer.getData('columnIndex'));
                const toIndex = parseInt(item.dataset.index);
                this.reorderColumn(fromIndex, toIndex);
            });
        });

        // Column properties inputs
        document.getElementById('column-alias')?.addEventListener('input', (e) => {
            if (this.currentColumn !== null) {
                this.selectedColumns[this.currentColumn].alias = e.target.value;
                this.refreshSelectedColumns();
            }
        });

        document.getElementById('column-aggregate')?.addEventListener('change', (e) => {
            if (this.currentColumn !== null) {
                this.selectedColumns[this.currentColumn].aggregate = e.target.value;
                this.refreshSelectedColumns();
            }
        });

        document.getElementById('column-format')?.addEventListener('change', (e) => {
            if (this.currentColumn !== null) {
                this.selectedColumns[this.currentColumn].format = e.target.value;
                this.refreshColumnProperties();
            }
        });

        document.getElementById('column-sortable')?.addEventListener('change', (e) => {
            if (this.currentColumn !== null) {
                this.selectedColumns[this.currentColumn].sortable = e.target.checked;
            }
        });

        document.getElementById('column-width')?.addEventListener('input', (e) => {
            if (this.currentColumn !== null) {
                this.selectedColumns[this.currentColumn].width = e.target.value;
            }
        });
    }

    addColumn(field) {
        // Check if already added
        if (this.selectedColumns.find(c => c.displayName === field.displayName)) {
            showNotification('Column already added', 'warning');
            return;
        }

        this.selectedColumns.push({
            ...field,
            sortable: true,
            alias: field.label
        });

        this.refreshSelectedColumns();
    }

    removeColumn(index) {
        this.selectedColumns.splice(index, 1);
        if (this.currentColumn === index) {
            this.currentColumn = null;
        } else if (this.currentColumn > index) {
            this.currentColumn--;
        }
        this.refreshSelectedColumns();
        this.refreshColumnProperties();
    }

    selectColumn(index) {
        this.currentColumn = index;
        this.refreshSelectedColumns();
        this.refreshColumnProperties();
    }

    reorderColumn(fromIndex, toIndex) {
        if (fromIndex === toIndex) return;

        const [moved] = this.selectedColumns.splice(fromIndex, 1);
        this.selectedColumns.splice(toIndex, 0, moved);

        // Update currentColumn if needed
        if (this.currentColumn === fromIndex) {
            this.currentColumn = toIndex;
        } else if (this.currentColumn > fromIndex && this.currentColumn <= toIndex) {
            this.currentColumn--;
        } else if (this.currentColumn < fromIndex && this.currentColumn >= toIndex) {
            this.currentColumn++;
        }

        this.refreshSelectedColumns();
    }

    addAllFields() {
        this.availableFields.forEach(field => {
            if (!this.selectedColumns.find(c => c.displayName === field.displayName)) {
                this.selectedColumns.push({
                    ...field,
                    sortable: true,
                    alias: field.label
                });
            }
        });
        this.refreshSelectedColumns();
    }

    clearAllColumns() {
        if (confirm('Remove all selected columns?')) {
            this.selectedColumns = [];
            this.currentColumn = null;
            this.refreshSelectedColumns();
            this.refreshColumnProperties();
        }
    }

    filterAvailableFields(searchTerm) {
        const term = searchTerm.toLowerCase();
        document.querySelectorAll('.field-item').forEach(item => {
            const field = JSON.parse(item.dataset.field);
            const matches = field.label.toLowerCase().includes(term) ||
                          field.name.toLowerCase().includes(term) ||
                          field.entity.toLowerCase().includes(term);
            item.style.display = matches ? 'block' : 'none';
        });
    }

    refreshSelectedColumns() {
        document.getElementById('selected-columns-list').innerHTML = this.renderSelectedColumns();
        this.attachEventListeners();
    }

    refreshColumnProperties() {
        document.getElementById('column-properties').innerHTML = this.renderColumnProperties();
        this.attachEventListeners();
    }

    getColumns() {
        return this.selectedColumns;
    }
}

// Export to global scope
window.DragDropColumnDesigner = DragDropColumnDesigner;
window.dragDropColumnDesigner = null;
```


### Enhancement 3: Visual Chart Builder (Week 2)

**Goal:** Transform text-based chart configuration into visual drag-and-drop interface

**Implementation Summary:**
- Create `/frontend/components/visual-chart-builder.js`
- Chart type selector with live thumbnails (9 chart types)
- Drag-and-drop axis configuration
- Color scheme designer with Material, Tailwind, Bootstrap presets
- Live preview with sample data
- Integration with Report Designer step 4 (Formatting)

**Key Features:**
- Visual chart type picker with preview cards
- Drag fields to axes (X, Y, Series, Filters)
- Real-time chart rendering using Chart.js
- Color palette designer with gradients
- Chart customization: titles, legends, tooltips, axis labels

---

### Enhancement 4: Split-Pane Live Preview (Week 2)

**Goal:** Add live data preview alongside configuration

**Implementation:**
- Split-pane layout (60% config / 40% preview)
- Toggle between Table View and Chart View
- Auto-refresh on configuration changes (debounced 500ms)
- Performance metrics display (query time, row count)
- Sample data fetch from `/api/v1/reports/preview`

**Benefits:**
- Immediate visual feedback
- Faster iteration
- Reduced errors
- Better user confidence

---

### Enhancement 5: Enhanced Parameter UI (Week 3)

**Goal:** Visual parameter builder with dependency rules

**Features:**
- Visual input type selector (text, number, date, dropdown, checkbox)
- Default value configuration
- Cascading parameter dependencies
- Test mode for parameter values
- Parameter validation rules

---

### Enhancement 6: Template Library (Week 3-4)

**Goal:** Pre-built report templates for quick start

**Templates to Create:**
1. Sales Report (revenue by period, top products, customer analysis)
2. Inventory Report (stock levels, reorder points, movement)
3. Financial Report (P&L, balance sheet, cash flow)
4. Customer Analytics (acquisition, retention, lifetime value)
5. Operational Metrics (capacity, efficiency, downtime)
6. HR Report (headcount, turnover, compensation)
7. Marketing Report (campaigns, ROI, conversion rates)
8. Project Status (timeline, budget, resources)
9. Service Desk Report (tickets, SLA, resolution time)
10. System Performance (uptime, response time, errors)

**Implementation:**
- Store templates in database (report_templates table)
- Template gallery UI with screenshots
- Clone functionality
- Customization wizard
- Category filtering

---

## Priority 3: Visual Dashboard Designer Enhancement

**Duration:** 3-4 weeks
**Complexity:** High
**Status:** ✅ **COMPLETED** (2026-01-18)

### Overview

Transform existing form-based dashboard designer into a fully visual drag-and-drop canvas, similar to modern dashboard builders like Grafana, Tableau, or Power BI.

### Implementation Summary

**Completed:** 2026-01-18

**Deliverables:**
- ✅ **Enhancement 1:** Visual Dashboard Canvas (GridStack.js integration) - `/frontend/components/visual-dashboard-canvas.js` (~500 lines)
- ✅ **Enhancement 2:** Widget Library Palette (26 widget types) - `/frontend/components/widget-library-palette.js` (~850 lines)
- ✅ **Enhancement 3:** Live Dashboard Preview - `/frontend/components/live-dashboard-preview.js` (~500 lines)
- ✅ **Enhancement 4:** Enhanced Widget Configuration - `/frontend/components/enhanced-widget-config.js` (~800 lines)
- ✅ **Enhancement 5:** Dashboard Template Library - `/frontend/components/dashboard-template-library.js` (~400 lines)
- ✅ **Enhancement 6:** Interactive Features - `/frontend/components/dashboard-interactive-features.js` (~600 lines)
- ✅ **Page Template:** Dashboard Designer UI - `/frontend/assets/templates/dashboard-designer.html` (~250 lines)
- ✅ **Menu Update:** Restructured No-Code Platform menu with nested submenus

**Total:** 6 new components + 1 page template + menu restructure = ~3,900 lines of code

**Key Features Implemented:**
- Drag-and-drop dashboard canvas with GridStack.js
- 26 widget types across 6 categories (Charts, Metrics, Tables, Text, Media, Actions)
- Multi-device preview (Desktop, Tablet, Mobile)
- Theme switching (Light, Dark, Custom)
- Live vs Mock data toggle
- Visual widget configuration with 4 panels (General, Data, Appearance, Advanced)
- 5 pre-built dashboard templates
- Widget drill-down and cross-filtering
- Export functionality (PDF, PNG, HTML, Excel)
- Share and embed capabilities
- Menu hierarchy matching System Management pattern

### Current Dashboard Designer Analysis

**Existing File:** `/frontend/components/dashboard-designer.js` (709 lines)

**Current Features:**
- ✅ 4-step wizard
- ✅ Multi-page dashboards
- ✅ 9 chart types + metric widgets
- ✅ Theme support (light/dark)
- ❌ Form-based widget configuration
- ❌ No visual layout canvas
- ❌ No drag-and-drop positioning

### Enhancement 1: Visual Layout Canvas (GrapeJS-style) - Week 1-2

**Architecture:**
```
┌──────────────────────────────────────────────────────┐
│  Dashboard Canvas Builder                            │
├──────────────────────────────────────────────────────┤
│                                                      │
│  Palette   │         Canvas         │  Properties   │
│            │                        │               │
│  [Widget1] │  ┌─────────┬────────┐ │  Widget:      │
│  [Widget2] │  │ Widget  │ Widget │ │  - Size       │
│  [Widget3] │  │         │        │ │  - Position   │
│     ...    │  ├─────────┴────────┤ │  - Data       │
│            │  │  Wide Widget     │ │  - Style      │
│            │  └──────────────────┘ │               │
│            │                        │               │
└──────────────────────────────────────────────────────┘
```

**Implementation:**
- Use CSS Grid (12-column responsive grid)
- GridStack.js for drag-and-drop layout
- Visual resize handles
- Snap-to-grid alignment
- Copy/paste/duplicate widgets
- Undo/redo stack

**File:** `/frontend/components/visual-dashboard-canvas.js` (~500 lines)

---

### Enhancement 2: Widget Library with Visual Previews - Week 2

**Widget Categories:**

**📊 Charts (9 types):**
- Bar Chart, Line Chart, Pie Chart, Donut Chart
- Area Chart, Scatter Plot, Radar Chart, Polar Chart, Bubble Chart

**📈 Metrics (5 types):**
- KPI Card, Gauge, Progress Bar, Stat Card, Number Counter

**📋 Tables (3 types):**
- Data Grid, Summary Table, Pivot Table

**📝 Text (3 types):**
- Header (H1-H6), Paragraph, Rich Text

**🖼️ Media (3 types):**
- Image, Video, Iframe Embed

**🔗 Actions (3 types):**
- Button, Link, Filter Panel

**Total: 26 widget types**

**Features:**
- Visual widget palette with thumbnails
- Live preview on hover
- Drag from palette to canvas
- Widget search and favorites
- Recent widgets quick access

---

### Enhancement 3: Live Dashboard Preview - Week 2-3

**Features:**
- Multi-device preview modes (Desktop, Tablet, Mobile)
- Theme switcher (Light, Dark, Custom)
- Live data vs Mock data toggle
- Performance metrics overlay
- Refresh rate configuration
- Auto-save with version history

**Implementation:**
- Responsive preview frame with device presets
- CSS media query simulation
- Real-time data fetching
- WebSocket support for live updates

---

### Enhancement 4: Enhanced Widget Configuration - Week 3

**Visual Configuration Panels:**
- Report selector with search/filter/preview
- Chart type visual picker
- Color scheme designer
- Spacing editor (padding, margin visual)
- Border and shadow designer
- Conditional formatting rules

---

### Enhancement 5: Dashboard Templates - Week 4

**Pre-built Templates:**
1. Executive Dashboard (KPIs, trends, alerts)
2. Sales Dashboard (revenue, pipeline, conversion)
3. Operations Dashboard (capacity, efficiency, SLA)
4. Analytics Dashboard (traffic, engagement, behavior)
5. Financial Dashboard (P&L, cash flow, budget)

**Features:**
- Template gallery with screenshots
- One-click clone and customize
- Industry-specific templates
- Template marketplace (future)

---

### Enhancement 6: Interactive Features - Week 4

**Features:**
- Widget drill-down (click chart → details)
- Cross-widget filtering
- Widget linking and communication
- Real-time data refresh
- Export dashboard (PDF, PNG, HTML)
- Dashboard sharing and embedding

---

## Priority 4: Developer Tools Enhancement

**Status:** Documentation Only - Implementation Decision Pending

### Detailed Feature Specifications

#### 1. Schema Designer

**UI Components:**
- Main canvas with Cytoscape.js graph
- Entity palette (searchable)
- Detail panel (columns, indexes, relationships)
- Export toolbar (PNG, SVG, PDF, Markdown)
- Schema comparison tool

**Key Functions:**
- `loadSchema()` - Fetch all entities from Data Model Designer
- `renderGraph()` - Visualize ER diagram
- `showEntityDetails()` - Display entity properties
- `compareSchemas()` - Diff between tenants/environments
- `exportSchema()` - Generate documentation

**API Endpoints Required:**
- `GET /api/v1/data-model/schema` - Full schema
- `GET /api/v1/data-model/schema/compare` - Compare schemas

**Estimated Effort:** 2-3 weeks

---

#### 2. API Playground

**UI Components:**
- API endpoint tree (from OpenAPI spec)
- Request builder (method, URL, headers, body)
- Response viewer (syntax highlighted)
- History sidebar
- Code snippet generator
- Environment selector

**Key Features:**
- Auto-load FastAPI OpenAPI spec
- JWT token injection
- Request/response history
- Favorites and collections
- WebSocket testing
- Mock server integration

**Technical Stack:**
- Monaco Editor for code editing
- Prism.js for syntax highlighting
- WebSocket client for real-time APIs

**API Endpoints Required:**
- `GET /api/v1/openapi.json` - OpenAPI spec
- `POST /api/v1/playground/execute` - Proxy requests

**Estimated Effort:** 3-4 weeks

---

#### 3. Code Generator

**Templates to Generate:**

**Backend (Python/FastAPI):**
- SQLAlchemy models
- Pydantic schemas (request/response)
- FastAPI routers (CRUD endpoints)
- Service layer
- Unit tests (pytest)

**Frontend (JavaScript):**
- HTML templates
- JavaScript classes
- Form components
- Table components
- Unit tests (Jest)

**Documentation:**
- API documentation (Markdown)
- README files
- Setup instructions

**Key Functions:**
- `generateModel()` - SQLAlchemy from EntityDefinition
- `generateSchema()` - Pydantic from EntityDefinition
- `generateRouter()` - FastAPI endpoints
- `generateFrontend()` - HTML/JS components
- `generateTests()` - Test files

**Template Engine:** Jinja2

**Export Formats:**
- ZIP archive
- Git repository (optional)
- Direct file download

**Estimated Effort:** 4-6 weeks

---

## Implementation Roadmap

### Phase 3 - Option C: Priorities 1-3 (8-10 weeks)

#### Week 1-2: Priority 1 - Menu Consolidation & Designer Activation

**Week 1:**
- [ ] Day 1-2: Update menu.json and i18n translations
- [ ] Day 3: Create reports-list.html and reports-list-page.js
- [ ] Day 4: Create dashboards-list.html and dashboards-list-page.js
- [ ] Day 5: Register routes in app.js

**Week 2:**
- [ ] Day 1-2: Implement Menu Sync UI (settings-menu-sync-page.js)
- [ ] Day 3-4: Add quick actions to existing designers
- [ ] Day 5: Testing and bug fixes

**Deliverable:** Unified menu, accessible designers, functional Menu Sync UI

---

#### Week 3-6: Priority 2 - Visual Report Designer Enhancement

**Week 3:**
- [ ] Day 1-3: Visual Data Source Builder (Cytoscape.js integration)
- [ ] Day 4-5: Drag-and-Drop Column Designer (left-center-right panels)

**Week 4:**
- [ ] Day 1-3: Visual Chart Builder (chart type picker, axis config)
- [ ] Day 4-5: Split-Pane Live Preview (layout and data fetching)

**Week 5:**
- [ ] Day 1-3: Enhanced Parameter UI (visual builder, dependencies)
- [ ] Day 4-5: Template Library setup (database, UI gallery)

**Week 6:**
- [ ] Day 1-3: Create 10 report templates
- [ ] Day 4-5: Integration testing, bug fixes, documentation

**Deliverable:** Fully visual report designer with templates

---

#### Week 7-10: Priority 3 - Visual Dashboard Designer Enhancement

**Week 7:**
- [ ] Day 1-3: Visual Layout Canvas (GridStack.js, 12-column grid)
- [ ] Day 4-5: Drag-and-drop functionality and resize handles

**Week 8:**
- [ ] Day 1-3: Widget Library (26 widget types with thumbnails)
- [ ] Day 4-5: Live Dashboard Preview (multi-device modes)

**Week 9:**
- [ ] Day 1-3: Enhanced Widget Configuration (visual panels)
- [ ] Day 4-5: Dashboard Templates (create 5 templates)

**Week 10:**
- [ ] Day 1-3: Interactive Features (drill-down, filtering, export)
- [ ] Day 4-5: Integration testing, bug fixes, documentation

**Deliverable:** Fully visual dashboard designer with templates

---

## Testing Strategy

### Unit Tests

**Frontend Components:**
- Visual Data Source Builder (30 tests)
- Drag-Drop Column Designer (25 tests)
- Visual Chart Builder (20 tests)
- Dashboard Canvas (35 tests)
- Widget Library (15 tests)

**Test Coverage Target:** >80%

**Tools:** Jest, Testing Library

---

### Integration Tests

**Scenarios:**
1. Create report with visual designer → Save → Run → Export
2. Create dashboard with canvas → Add widgets → Preview → Publish
3. Use template → Customize → Save as new
4. Cross-feature workflow: Entity → Report → Dashboard → Menu

**Tools:** Playwright, Cypress

---

### User Acceptance Testing

**Test Groups:**
- Power users (5 users)
- System admins (3 users)
- Developers (2 users)

**Test Duration:** 1 week

**Feedback Collection:**
- Usability questionnaire
- Performance metrics
- Feature requests

---

### Performance Tests

**Metrics:**
- Report creation time: Target <5 min (vs current 10 min)
- Dashboard creation time: Target <7 min (vs current 15 min)
- Page load time: <2 seconds
- Widget rendering: <500ms per widget

**Tools:** Lighthouse, Chrome DevTools

---

## Success Metrics

### Quantitative Metrics

**Usage:**
- ✅ 80%+ of users create custom reports within 1 month
- ✅ 70%+ of users create custom dashboards within 1 month
- ✅ 50%+ reduction in report creation time
- ✅ 60%+ reduction in dashboard creation time

**Quality:**
- ✅ >4.5/5 user satisfaction rating
- ✅ <5% error rate in designer
- ✅ <10 support tickets per month related to designers

**Adoption:**
- ✅ 100+ reports created in first 3 months
- ✅ 50+ dashboards created in first 3 months
- ✅ 30%+ of reports use templates

---

### Qualitative Metrics

**User Feedback:**
- Ease of use ratings
- Feature request analysis
- Pain point identification
- Competitive comparison

**System Health:**
- Error logs analysis
- Performance monitoring
- Resource utilization
- Scalability assessment

---

## Rollback Plan

### Priority 1 Rollback

**Scenario:** Menu consolidation causes navigation issues

**Steps:**
1. Revert menu.json to previous version
2. Keep new list pages but make inaccessible
3. No data loss - only UI changes
4. Rollback time: <1 hour

**Risk:** Low - UI changes only

---

### Priority 2 Rollback

**Scenario:** Visual report designer has critical bugs

**Steps:**
1. Add toggle to switch between classic and visual mode
2. Default to classic mode
3. Fix bugs in visual mode offline
4. Re-enable when stable

**Risk:** Medium - New complex UI

**Mitigation:**
- Feature flag for visual mode
- Extensive testing before release
- Gradual rollout (10% → 50% → 100%)

---

### Priority 3 Rollback

**Scenario:** Visual dashboard designer performance issues

**Steps:**
1. Same as Priority 2 - toggle between modes
2. Optimize performance offline
3. Re-enable incrementally

**Risk:** Medium - Complex canvas rendering

**Mitigation:**
- Performance testing with large dashboards
- Lazy loading for widgets
- Throttled rendering

---

## Dependencies and Prerequisites

### External Libraries Required

**Frontend:**
- Cytoscape.js v3.26+ (graph visualization)
- GridStack.js v8.0+ (dashboard grid layout)
- Chart.js v4.0+ (already exists)
- SortableJS v1.15+ (drag-and-drop)

**Load Strategy:**
- CDN links with fallback to local
- Lazy loading when component used
- Bundle size monitoring

---

### Browser Compatibility

**Minimum Requirements:**
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

**Features Used:**
- CSS Grid
- ES6 modules
- Drag and Drop API
- Canvas API

---

### Backend API Enhancements

**New Endpoints Required:**

```
POST /api/v1/reports/preview
- Execute report query and return sample data (10 rows)
- Used by live preview feature

GET /api/v1/reports/templates
- List available report templates
- Category filtering

POST /api/v1/reports/templates/{id}/clone
- Clone template as new report
- Customize and save

GET /api/v1/dashboards/templates
- List available dashboard templates

POST /api/v1/dashboards/{id}/snapshot
- Create dashboard snapshot (thumbnail)
- Used in gallery view
```

**Estimated Backend Effort:** 3-5 days

---

## Risk Assessment

### High Risk Items

1. **Visual Data Source Builder Complexity**
   - Risk: Graph rendering performance with many entities
   - Mitigation: Pagination, lazy loading, canvas virtualization

2. **Dashboard Canvas Responsiveness**
   - Risk: Layout breaking on different screen sizes
   - Mitigation: Thorough responsive testing, grid constraints

3. **Browser Compatibility**
   - Risk: Advanced features not supported in older browsers
   - Mitigation: Progressive enhancement, feature detection

---

### Medium Risk Items

1. **User Learning Curve**
   - Risk: Users confused by new visual interfaces
   - Mitigation: Tooltips, guided tours, video tutorials

2. **Data Volume Performance**
   - Risk: Slow rendering with large datasets
   - Mitigation: Pagination, virtual scrolling, data limits

---

### Low Risk Items

1. **Menu Consolidation**
   - Risk: Users can't find relocated items
   - Mitigation: Clear communication, search functionality

2. **Template Quality**
   - Risk: Templates don't meet user needs
   - Mitigation: User feedback, iterative improvement

---

## Communication Plan

### Stakeholder Updates

**Weekly:**
- Progress report to project manager
- Demo of completed features
- Blocker escalation

**Bi-weekly:**
- Stakeholder demo
- Feature walkthrough
- Feedback collection

---

### User Communication

**Pre-Launch:**
- Announcement of upcoming features
- Beta testing invitation
- Video sneak peeks

**Launch:**
- Feature announcement
- Tutorial videos
- Documentation release
- Office hours / Q&A sessions

**Post-Launch:**
- Usage metrics sharing
- Success stories
- Feature enhancement roadmap

---

## Documentation Requirements

### User Documentation

**Required Documents:**
1. Report Designer User Guide (15-20 pages)
2. Dashboard Designer User Guide (15-20 pages)
3. Template Library Guide (5 pages)
4. Quick Start Guides (1-2 pages each)
5. Video Tutorials (5-10 videos, 5-10 min each)

---

### Developer Documentation

**Required Documents:**
1. Component API Documentation
2. Integration Guide
3. Customization Guide
4. Troubleshooting Guide
5. Architecture Overview

---

## Maintenance Plan

### Post-Launch Support

**Week 1-2:** Intensive support
- Monitor error logs
- Rapid bug fixes
- User support tickets
- Performance monitoring

**Month 1-3:** Regular support
- Bug fix releases
- Feature refinements
- Documentation updates
- Template additions

**Month 3+:** Ongoing maintenance
- Quarterly feature updates
- Annual major version
- Community feedback integration

---

## Related Documents

- [NO-CODE-PLATFORM-DESIGN.md](NO-CODE-PLATFORM-DESIGN.md) - Parent design document
- [NO-CODE-PHASE1.md](NO-CODE-PHASE1.md) - Phase 1 completed specs
- [NO-CODE-PHASE2.md](NO-CODE-PHASE2.md) - Phase 2 completed specs

---

**Document Version:** 1.0
**Last Updated:** 2026-01-15
**Next Review:** Upon Phase 3 Implementation Start
**Status:** Ready for Implementation (Option C: Priorities 1-3)

