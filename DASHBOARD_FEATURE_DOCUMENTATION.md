## Dashboard Visualization Feature Documentation

### Overview

The Dashboard Visualization system provides a comprehensive, configurable multi-page dashboard platform that **reuses the existing Report infrastructure** to display data visualizations, KPI cards, charts, and more. This feature allows users to create interactive dashboards with multiple pages and widgets, all backed by the robust reporting system.

### Table of Contents

1. [Key Features](#key-features)
2. [Architecture & Report Integration](#architecture--report-integration)
3. [How It Reuses Report Code](#how-it-reuses-report-code)
4. [Database Schema](#database-schema)
5. [API Endpoints](#api-endpoints)
6. [Frontend Components](#frontend-components)
7. [Widget Types](#widget-types)
8. [Usage Examples](#usage-examples)
9. [Integration Points](#integration-points)

---

## Key Features

### Core Features

1. **Multi-Page Dashboards**
   - Create dashboards with unlimited pages
   - Tab-based navigation between pages
   - Icon and slug support for pages
   - Default landing page configuration

2. **Multiple Widget Types**
   - Report Table (reuses report infrastructure)
   - Charts (bar, line, pie, donut, area, scatter, gauge, funnel, heatmap)
   - KPI Cards (single metric display)
   - Metrics (simple number displays)
   - Text widgets (rich content)
   - Iframe embeds
   - Image displays
   - Filter panels

3. **Grid-Based Layout**
   - Flexible grid system (default 12 columns)
   - Drag-and-drop widget positioning
   - Customizable row heights and margins
   - Responsive layout support

4. **Global Parameters** ⭐ **REUSES REPORT PARAMETERS**
   - Dashboard-level parameters shared across all widgets
   - **Same parameter types as reports** (string, integer, date, lookup, etc.)
   - **Same auto-detecting input components**
   - **Same validation rules**
   - Parameter filtering cascades to all widgets

5. **Auto-Refresh**
   - Per-widget refresh intervals
   - Dashboard-wide refresh intervals
   - Multiple interval options (30s, 1m, 5m, 15m, 30m, 1h)
   - Manual refresh capability

6. **Data Caching**
   - Widget-level caching with TTL
   - Cache hit tracking
   - Optional cache bypass
   - Performance optimization

7. **Sharing & Collaboration**
   - Share dashboards with users or roles
   - Public/private dashboards
   - Permission levels (view, edit, share)
   - Temporary share links with expiration

8. **Dashboard Snapshots**
   - Save dashboard state at a point in time
   - Capture parameter values
   - Historical reference

---

## Architecture & Report Integration

### System Diagram

```
┌─────────────────────┐
│   Dashboard         │
│   (Container)       │
└──────┬──────────────┘
       │
       ├──> Pages (1 to N)
       │      │
       │      └──> Widgets (1 to N)
       │             │
       │             ├──> Report Table Widget ──────┐
       │             ├──> Chart Widget ────────────┐│
       │             ├──> KPI Card Widget ────────┐││
       │             └──> Other Widget Types      │││
       │                                           │││
       └──> Global Parameters ───────────────────┐│││
                (REUSES Report Parameters)        ││││
                                                  ││││
                    ┌─────────────────────────────┘│││
                    │  ┌───────────────────────────┘││
                    │  │  ┌───────────────────────────┘│
                    ▼  ▼  ▼                             ▼
          ┌──────────────────────────────────────────────┐
          │          REPORT SERVICE                       │
          │  (Existing Report Infrastructure)             │
          │                                              │
          │  • ReportService.execute_report()            │
          │  • ReportService._build_and_execute_query()  │
          │  • ReportService.get_report_definition()     │
          │  • Report parameter validation                │
          │  • Report caching                             │
          │  • Report filtering                           │
          └──────────────────────────────────────────────┘
```

### How Dashboards Layer on Reports

**Dashboards are a visualization layer** built on top of the existing report system:

1. **Widgets reference Reports** - Each widget can link to a `ReportDefinition`
2. **Widget data fetching delegates to ReportService** - No duplicate query logic
3. **Global parameters map to report parameters** - Same validation, same inputs
4. **Caching reuses report caching** - Performance benefits
5. **Permissions leverage report permissions** - Same security model

---

## How It Reuses Report Code

### 1. Widget Data Fetching (Backend)

**File:** `backend/app/services/dashboard_service.py`

```python
@staticmethod
def get_widget_data(...):
    """
    Get data for a widget - REUSES ReportService for report-based widgets.
    """
    widget = db.query(DashboardWidget).filter(...).first()

    if widget.widget_type == WidgetType.REPORT_TABLE and widget.report_definition_id:
        # ⭐ REUSE ReportService for report-based widgets
        execution_request = ReportExecutionRequest(
            report_definition_id=widget.report_definition_id,
            parameters=parameters or {},
            use_cache=use_cache
        )
        execution = ReportService.execute_report(db, tenant_id, user_id, execution_request)

        # Fetch data using report infrastructure
        query_result = ReportService._build_and_execute_query(
            db, tenant_id,
            ReportService.get_report_definition(db, tenant_id, widget.report_definition_id, user_id),
            parameters or {}
        )
        data = query_result['data']

    elif widget.widget_type == WidgetType.CHART and widget.report_definition_id:
        # ⭐ REUSE ReportService for chart data
        report_def = ReportService.get_report_definition(db, tenant_id, widget.report_definition_id, user_id)
        if report_def:
            query_result = ReportService._build_and_execute_query(
                db, tenant_id, report_def, parameters or {}
            )
            # Transform for chart display
            data = DashboardService._transform_data_for_chart(query_result['data'], widget.chart_config)

    elif widget.widget_type == WidgetType.KPI_CARD:
        # ⭐ REUSE ReportService for KPI data
        if widget.report_definition_id:
            report_def = ReportService.get_report_definition(db, tenant_id, widget.report_definition_id, user_id)
            query_result = ReportService._build_and_execute_query(db, tenant_id, report_def, parameters or {})
            data = DashboardService._transform_data_for_kpi(query_result['data'], widget.widget_config)
```

**Key Points:**
- ✅ No duplicate query building logic
- ✅ Report definitions are **single source of truth** for data
- ✅ Report execution, caching, and permissions all apply
- ✅ Transformations adapt report data to widget visualization needs

### 2. Global Parameters (Frontend)

**File:** `frontend/components/dashboard-viewer.js`

```javascript
async _renderGlobalParameters() {
    const container = document.getElementById('global-parameters-container');

    // ⭐ REUSE ReportParameterInput component for dashboard parameters
    this.parameterInput = new ReportParameterInput(
        container,
        this.dashboard.global_parameters,  // Same format as report parameters!
        (values) => this._onGlobalParametersApplied(values)
    );
    await this.parameterInput.render();
}
```

**Benefits:**
- ✅ Same auto-detecting input components (text, number, date, lookup, etc.)
- ✅ Same validation rules
- ✅ Same lookup data fetching from tables
- ✅ Same cascading parameter logic
- ✅ **Zero duplicate code**

### 3. Widget Data Fetching (Frontend)

**File:** `frontend/components/dashboard-widget.js`

```javascript
async loadData(useCache = true) {
    // Merge global parameters with widget-specific parameters
    const parameters = { ...this.globalParameters };

    // ⭐ Fetch widget data (backend delegates to ReportService)
    const result = await dashboardService.getWidgetData(
        this.widgetConfig.id,
        parameters,
        useCache
    );

    this.data = result.data;
    await this._renderWidgetContent(bodyContainer);
}
```

### 4. Shared Data Models

**Global Parameters Definition:**
```python
# Dashboard (backend/app/models/dashboard.py)
global_parameters = Column(JSON, nullable=True)  # List of parameter definitions

# Report (backend/app/models/report.py)
parameters = Column(JSON, nullable=True)  # Same structure!
```

**Both use the exact same parameter schema:**
```json
{
  "name": "start_date",
  "label": "Start Date",
  "parameter_type": "date",
  "required": true,
  "default_value": "2024-01-01",
  "validation_rules": [...],
  "lookup_config": {...}
}
```

---

## Database Schema

### Dashboards Table
| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| tenant_id | Integer | Multi-tenant isolation |
| name | String(255) | Dashboard name |
| description | Text | Dashboard description |
| category | String(100) | Category for grouping |
| tags | JSON | Array of tags |
| layout_type | Enum | grid/freeform/responsive |
| theme | String(50) | light/dark/custom |
| **global_parameters** | **JSON** | **Global parameters (same as report parameters)** |
| global_filters | JSON | Global filter configuration |
| refresh_interval | Enum | Auto-refresh interval |
| is_public | Boolean | Public visibility |
| allowed_roles | JSON | RBAC roles |
| allowed_users | JSON | RBAC users |
| created_by | Integer | Creator user ID |
| created_at | DateTime | Creation timestamp |
| is_active | Boolean | Soft delete flag |
| is_favorite | Boolean | Favorite flag |

### Dashboard Pages Table
| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| dashboard_id | Integer | FK to dashboards |
| tenant_id | Integer | Multi-tenant isolation |
| name | String(255) | Page name |
| slug | String(100) | URL-friendly identifier |
| icon | String(50) | Page icon |
| layout_config | JSON | Grid configuration |
| order | Integer | Display order |
| is_default | Boolean | Default landing page |

### Dashboard Widgets Table
| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| page_id | Integer | FK to dashboard_pages |
| tenant_id | Integer | Multi-tenant isolation |
| title | String(255) | Widget title |
| widget_type | Enum | report_table/chart/kpi_card/etc. |
| **report_definition_id** | **Integer** | **FK to report_definitions (Integration Point!)** |
| data_source_config | JSON | Custom data source config |
| widget_config | JSON | Widget-specific settings |
| chart_config | JSON | Chart configuration |
| filter_mapping | JSON | Map global params to widget params |
| position | JSON | {x, y, w, h} for grid |
| refresh_interval | Enum | Widget refresh interval |

---

## API Endpoints

### Dashboard Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/dashboards` | Create dashboard |
| GET | `/api/v1/dashboards` | List dashboards |
| GET | `/api/v1/dashboards/{id}` | Get dashboard with pages & widgets |
| PUT | `/api/v1/dashboards/{id}` | Update dashboard |
| DELETE | `/api/v1/dashboards/{id}` | Delete dashboard |
| POST | `/api/v1/dashboards/{id}/clone` | Clone dashboard |

### Page Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/dashboards/pages` | Create page |
| PUT | `/api/v1/dashboards/pages/{id}` | Update page |
| DELETE | `/api/v1/dashboards/pages/{id}` | Delete page |

### Widget Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/dashboards/widgets` | Create widget |
| PUT | `/api/v1/dashboards/widgets/{id}` | Update widget |
| DELETE | `/api/v1/dashboards/widgets/{id}` | Delete widget |
| POST | `/api/v1/dashboards/widgets/bulk-update` | Bulk update positions |
| **POST** | **`/api/v1/dashboards/widgets/data`** | **Get widget data (uses ReportService)** |

### Other Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/dashboards/shares` | Share dashboard |
| POST | `/api/v1/dashboards/snapshots` | Create snapshot |

**Total: 16 endpoints**

---

## Frontend Components

### 1. DashboardService (`dashboard-service.js`)
- API client for dashboard operations
- Helper methods for widget types, positions, chart types
- Reuses report infrastructure on backend

### 2. DashboardWidget (`dashboard-widget.js`)
- Renders individual widgets
- Auto-refresh support
- **Fetches data via ReportService on backend**
- Multiple widget type renderers

### 3. DashboardViewer (`dashboard-viewer.js`)
- Displays complete dashboards
- Multi-page navigation
- Global parameters (reuses `ReportParameterInput`)
- Grid layout rendering

---

## Widget Types

| Type | Description | Uses Report? | Notes |
|------|-------------|--------------|-------|
| **report_table** | Tabular data display | ✅ Yes | Direct report execution |
| **chart** | Chart visualization | ✅ Yes | Report data + chart transform |
| **kpi_card** | Single metric card | ✅ Yes | Report data aggregated |
| **metric** | Simple number | ⚠️ Optional | Can use report or static |
| **text** | Rich text/HTML | ❌ No | Static content |
| **iframe** | Embedded page | ❌ No | External URL |
| **image** | Image display | ❌ No | Image URL |
| **filter_panel** | Global filters | ❌ No | Filter controls |

---

## Usage Examples

### Example 1: Create Dashboard with Report-Based Widget

```python
# Backend: Create dashboard
dashboard = DashboardService.create_dashboard(
    db=db,
    tenant_id=1,
    user_id=1,
    dashboard_data=DashboardCreate(
        name="Sales Dashboard",
        description="Real-time sales metrics",
        global_parameters=[
            {
                "name": "date_range",
                "label": "Date Range",
                "parameter_type": "date",
                "required": True
            }
        ]
    )
)

# Create page
page = DashboardService.create_page(
    db=db,
    tenant_id=1,
    page_data=DashboardPageCreate(
        dashboard_id=dashboard.id,
        name="Overview"
    )
)

# Create widget linked to existing report
widget = DashboardService.create_widget(
    db=db,
    tenant_id=1,
    widget_data=DashboardWidgetCreate(
        page_id=page.id,
        title="Sales by Region",
        widget_type="report_table",
        report_definition_id=5,  # ⭐ Links to existing report!
        position={"x": 0, "y": 0, "w": 6, "h": 4}
    )
)
```

### Example 2: Fetch Widget Data (Reuses Report)

```python
# This calls ReportService.execute_report() internally!
widget_data = DashboardService.get_widget_data(
    db=db,
    tenant_id=1,
    user_id=1,
    widget_id=widget.id,
    parameters={"date_range": "2024-01-01"}
)
```

### Example 3: Frontend - Display Dashboard

```javascript
import { DashboardViewer } from './components/dashboard-viewer.js';

const container = document.getElementById('dashboard-container');
const viewer = new DashboardViewer(container, dashboardId);
await viewer.render();

// The viewer automatically:
// 1. Renders global parameters using ReportParameterInput
// 2. Fetches widget data via ReportService
// 3. Applies caching and refresh
```

---

## Integration Points

### Where Dashboards Use Report Code

1. **Data Fetching**
   - `DashboardService.get_widget_data()` → `ReportService.execute_report()`
   - `DashboardService.get_widget_data()` → `ReportService._build_and_execute_query()`

2. **Parameters**
   - `Dashboard.global_parameters` → Same schema as `ReportDefinition.parameters`
   - `ReportParameterInput` component → Reused for dashboard parameters

3. **Validation**
   - Report parameter validation → Applied to dashboard parameters
   - Report permissions → Applied to widgets linking to reports

4. **Caching**
   - Widget caching → Similar logic to report caching
   - Cache key generation → Same pattern

5. **Data Models**
   - `DashboardWidget.report_definition_id` → FK to `report_definitions`
   - Parameter schemas → Shared between reports and dashboards

### Benefits of Reuse

✅ **No Duplicate Code** - All query logic in one place (ReportService)
✅ **Consistency** - Same behavior for reports and dashboards
✅ **Maintainability** - Fix bugs in one place
✅ **Performance** - Shared caching infrastructure
✅ **Security** - Shared permission model
✅ **DRY Principle** - Don't Repeat Yourself

---

## File Locations

### Backend Files
- Models: `/home/user/app-buildify/backend/app/models/dashboard.py`
- Schemas: `/home/user/app-buildify/backend/app/schemas/dashboard.py`
- Service: `/home/user/app-buildify/backend/app/services/dashboard_service.py`
- Router: `/home/user/app-buildify/backend/app/routers/dashboards.py`
- Migration: `/home/user/app-buildify/backend/alembic/versions/add_dashboard_tables.py`

### Frontend Files
- Service: `/home/user/app-buildify/frontend/assets/js/dashboard-service.js`
- Widget Component: `/home/user/app-buildify/frontend/components/dashboard-widget.js`
- Viewer Component: `/home/user/app-buildify/frontend/components/dashboard-viewer.js`

---

## Summary

The Dashboard Visualization feature provides a **powerful, multi-page dashboard system** that intelligently **reuses the existing Report infrastructure**:

### Key Achievements:
- ✅ Multi-page dashboards with unlimited widgets
- ✅ 8 widget types (report table, chart, KPI, metric, text, iframe, image, filter)
- ✅ **Complete integration with Report system** - zero duplicate query logic
- ✅ **Reuses ReportParameterInput** for global parameters
- ✅ **Reuses ReportService** for all data fetching
- ✅ Grid-based layout with drag-drop
- ✅ Auto-refresh and caching
- ✅ Sharing and snapshots
- ✅ 16 API endpoints
- ✅ 3 reusable frontend components
- ✅ Complete database schema with foreign key to reports
- ✅ Multi-tenant and RBAC ready

### Architecture Highlights:
- **Layered Design** - Dashboards sit on top of reports
- **Single Source of Truth** - Report definitions drive widget data
- **Code Reuse** - Extensive reuse of report infrastructure
- **Maintainability** - Changes to reports automatically benefit dashboards
- **Performance** - Shared caching and optimization
- **Consistency** - Same behavior across reports and dashboards

This design ensures that dashboards and reports work together seamlessly while maximizing code reuse and maintainability!
