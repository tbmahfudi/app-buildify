# API Integration Demo - GrapeJS Sample Page

## Overview

This implementation adds **API-integrated components** to the GrapeJS builder, enabling pages to interact with backend APIs in real-time. A sample page creation tool has been developed to demonstrate these capabilities.

## What Was Created

### 1. API-Enabled Components (`frontend/assets/js/components/api-components.js`)

Three new GrapeJS components that can interact with backend APIs:

#### **API Data Table**
- **Purpose**: Display data from backend API with pagination and search
- **Features**:
  - Live data loading from `/api/v1/data/{entity}/list`
  - Search functionality with debouncing
  - Pagination (Previous/Next)
  - Automatic table rendering based on data structure
  - Error handling and loading states
- **Configurable**:
  - Entity type (companies, branches, departments, users)
  - Custom API endpoint
  - Page size and filters

#### **API Form**
- **Purpose**: Submit data to backend API
- **Features**:
  - POST/PUT/PATCH support
  - Form validation
  - Success/error message display
  - Auto-reset after successful submission
  - Authentication token handling
- **Configurable**:
  - API endpoint
  - HTTP method
  - Form fields (customizable in component HTML)

#### **API Button**
- **Purpose**: Trigger custom API calls on demand
- **Features**:
  - Supports GET/POST/PUT/DELETE methods
  - Loading state with button text change
  - Optional result container for displaying response
  - Console logging of API responses
  - Alert feedback for users
- **Configurable**:
  - Button text
  - API endpoint
  - HTTP method
  - Result container selector

### 2. Sample Page Creator (`frontend/assets/js/create-sample-page.js`)

A programmatic page builder that:
- Creates a complete GrapeJS page structure
- Includes all three API components
- Generates HTML and CSS output
- Saves to backend via `/api/v1/builder/pages/` API
- Publishes the page automatically
- Handles authentication and error cases

### 3. UI for Page Creation (`frontend/create-api-demo.html`)

A standalone HTML page that:
- Provides a user-friendly interface to create the demo page
- Shows page details before creation
- Displays creation status and results
- Handles authentication checks
- Provides navigation to the UI Builder

## File Structure

```
frontend/
├── assets/js/
│   ├── components/
│   │   ├── api-components.js          # NEW: API-enabled components
│   │   └── builder-component-registry.js  # MODIFIED: Import API components
│   └── create-sample-page.js          # NEW: Programmatic page builder
└── create-api-demo.html               # NEW: UI for creating demo page
```

## How to Use

### Method 1: Using the UI (Recommended)

1. **Access the creation page**:
   ```
   http://localhost:8080/frontend/create-api-demo.html
   ```

2. **Make sure you're logged in** (the page will warn you if not)

3. **Click "Create & Publish Page"**

4. **Wait for success** - the page will be created and published

5. **View the demo page** at `/api-demo` route

### Method 2: Using JavaScript Console

```javascript
import { createSampleAPIPage } from './assets/js/create-sample-page.js';

// Create and publish the page
await createSampleAPIPage();
```

### Method 3: Using the GrapeJS Builder

1. Go to the **UI Builder** (`/#builder`)

2. You'll see a new category **"API Components"** in the blocks panel:
   - 🗄️ API Table
   - 📤 API Form
   - ⚡ API Button

3. **Drag and drop** these components onto your page

4. **Configure** each component using the Settings panel:
   - Set API endpoints
   - Choose HTTP methods
   - Customize entity types

5. **Save and Publish** your page

## Backend API Integration

The components integrate with these backend endpoints:

### Data API (`/api/v1/data/`)

```
POST /api/v1/data/{entity}/list    # List/search data
GET  /api/v1/data/{entity}/{id}    # Get single record
POST /api/v1/data/{entity}         # Create record
PUT  /api/v1/data/{entity}/{id}    # Update record
DELETE /api/v1/data/{entity}/{id}  # Delete record
POST /api/v1/data/{entity}/bulk    # Bulk operations
```

**Supported entities**:
- `companies`
- `branches`
- `departments`
- `users`

### Builder Pages API (`/api/v1/builder/pages/`)

```
POST /api/v1/builder/pages/                    # Create page
GET  /api/v1/builder/pages/                    # List pages
GET  /api/v1/builder/pages/{page_id}           # Get page
PUT  /api/v1/builder/pages/{page_id}           # Update page
DELETE /api/v1/builder/pages/{page_id}         # Delete page
POST /api/v1/builder/pages/{page_id}/publish   # Publish page
```

## Authentication

All API calls use **Bearer token authentication**:

```javascript
const token = localStorage.getItem('token');

fetch(endpoint, {
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    }
})
```

Make sure users are logged in before using API components.

## Sample Page Structure

The created demo page includes:

```
┌─────────────────────────────────────┐
│     API Integration Demo            │
│  (Hero section with title)          │
├─────────────┬───────────────────────┤
│  API Data   │   API Form            │
│  Table      │   (Create Company)    │
│  (Companies)│                       │
├─────────────┴───────────────────────┤
│     API Button (Fetch Users)        │
│     [Result Display Area]           │
└─────────────────────────────────────┘
```

## Component Configuration Examples

### API Data Table

```javascript
{
    type: 'api-datatable',
    attributes: {
        'data-api-entity': 'companies',
        'data-api-endpoint': '/api/v1/data/companies/list'
    }
}
```

### API Form

```javascript
{
    type: 'api-form',
    attributes: {
        'data-api-endpoint': '/api/v1/data/companies',
        'data-api-method': 'POST'
    }
}
```

### API Button

```javascript
{
    type: 'api-button',
    attributes: {
        'data-button-text': 'Fetch Users',
        'data-api-endpoint': '/api/v1/data/users/list',
        'data-api-method': 'POST',
        'data-result-container': '#result-div'
    },
    content: 'Fetch Users'
}
```

## Error Handling

All components include comprehensive error handling:

- **Network errors**: Displayed in UI with error messages
- **Authentication errors**: Checks for token presence
- **API errors**: Shows HTTP status and error details
- **Validation errors**: Form validation before submission
- **Loading states**: Visual feedback during API calls

## Features

### Data Table Features
- ✅ Real-time data loading
- ✅ Search with 300ms debounce
- ✅ Pagination (configurable page size)
- ✅ Dynamic column rendering
- ✅ Dark mode support
- ✅ Responsive design

### Form Features
- ✅ Dynamic field collection
- ✅ Success/error messages
- ✅ Auto-reset on success
- ✅ Form validation
- ✅ Multiple HTTP methods

### Button Features
- ✅ Custom API calls
- ✅ Loading states
- ✅ Result display
- ✅ Console logging
- ✅ User feedback (alerts)

## Testing the Demo

1. **Create the page** using `create-api-demo.html`

2. **Navigate to** `/api-demo` route

3. **Test the Data Table**:
   - Should load companies automatically
   - Try searching for company names
   - Use pagination buttons

4. **Test the Form**:
   - Fill in Name, Code, Description
   - Submit the form
   - Should see success message
   - Table should refresh with new data

5. **Test the API Button**:
   - Click "Fetch Users"
   - Should see alert with count
   - Check console for full response

## Extending the Components

### Adding New Entities

1. Update `ENTITY_REGISTRY` in `backend/app/routers/data.py`
2. Add entity to component options in `api-components.js`

### Customizing Form Fields

Edit the `components` array in `registerAPIForm()`:

```javascript
components: `
    <div>
        <label>Custom Field</label>
        <input type="text" name="custom_field" />
    </div>
`
```

### Adding Custom API Components

Follow the pattern in `api-components.js`:

```javascript
function registerCustomComponent(editor) {
    editor.BlockManager.add('custom-api', {
        label: 'Custom API Component',
        category: 'API Components',
        content: { type: 'custom-api' }
    });

    editor.DomComponents.addType('custom-api', {
        model: {
            defaults: {
                script: function() {
                    // Your API logic here
                }
            }
        }
    });
}
```

## Troubleshooting

### Components not showing in Builder
- Check browser console for import errors
- Verify `registerAPIComponents()` is called in `builder-component-registry.js`

### API calls failing
- Verify authentication token exists: `localStorage.getItem('token')`
- Check backend server is running
- Verify API endpoints in backend router

### Page creation fails
- Ensure you're logged in
- Check for duplicate slug/route conflicts
- Verify backend database is accessible

## Next Steps

1. **Customize the demo page** with your own layout
2. **Add more API components** for specific use cases
3. **Create forms** for other entities (branches, departments)
4. **Build dashboards** using API data tables
5. **Implement charts** using API data

## Summary

This implementation demonstrates:
- ✅ Full GrapeJS ↔ Backend API integration
- ✅ Real-time data loading and submission
- ✅ Reusable API-enabled components
- ✅ Programmatic page creation
- ✅ Production-ready error handling
- ✅ Authentication support

**All code is committed and pushed to branch**: `claude/compare-grapesjs-formio-xsL8F`
