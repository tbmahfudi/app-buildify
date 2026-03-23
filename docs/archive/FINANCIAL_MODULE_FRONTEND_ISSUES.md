# Financial Module - Frontend Issues & Required Functionality

## 🔴 Critical Issues Found

### 1. **Icons Not Displaying in Sidebar**
**Problem**: Icon classes in manifest.json may not be rendered properly by the menu system.

**Root Cause**: The menu loader expects icons in a specific format, and module icons might not be getting passed through correctly.

**Solution Needed**:
- Check browser console for icon loading errors
- Verify Phosphor icons CSS is loaded
- Ensure module menu items are being registered with icon classes

---

### 2. **Accounts Page Shows No Data**
**Problem**: Sample data created for FASHIONHUB but accounts page is empty.

**Root Causes**:
1. **Missing API Parameters**: Accounts page calls `/financial/accounts` without `tenant_id` and `company_id` parameters
   ```javascript
   // Current (line 134):
   const response = await apiFetch('/financial/accounts');

   // Should be:
   const response = await apiFetch('/financial/accounts?tenant_id=XXX&company_id=YYY');
   ```

2. **Template Path Issue**: Fetches template from `/modules/financial/frontend/pages/accounts.html`
   - Web server might not serve this path correctly
   - Need to verify web server configuration serves `/modules/` directory

3. **No User Context**: Pages don't retrieve current user's tenant_id/company_id from session/localStorage

4. **API Endpoint Mismatch**:
   - Frontend calls: `/financial/accounts`
   - Backend expects: `/api/v1/accounts` with query params

---

### 3. **Module Loading Issues**
**Problem**: Standalone module.js has different routing than manifest.json

**Issues**:
- `manifest.json` defines routes with components
- `module.js` has its own hardcoded routes
- Conflict between two routing systems

---

## ✅ Financial Module Frontend Functionality

### **Available Pages** (7 Total)

#### 1. **Accounts** (`pages/accounts.js` + `accounts.html`)
- **Features**:
  - Tree view of chart of accounts
  - List view with sortable table
  - Create/Edit/Delete accounts
  - Account type filtering (Asset, Liability, Equity, Revenue, Expense)
  - Active/Inactive status filtering
  - Hierarchical account structure
  - Account balance display
  - Expand/collapse all functionality
- **Components**: DataTable, FormBuilder
- **Lines of Code**: 741 LOC

#### 2. **Customers** (`pages/customers.js` + `customers.html`)
- **Features**:
  - Customer list with search
  - Create/Edit/Delete customers
  - Customer statistics dashboard
  - Credit limit tracking
  - Payment terms management
  - Contact information management
  - Invoice history per customer
  - Customer status (active/inactive)
- **Components**: DataTable, FormBuilder
- **Lines of Code**: 553 LOC

#### 3. **Invoices** (`pages/invoices.js` + `invoices.html`)
- **Features**:
  - Invoice list with filtering
  - Create/Edit invoices
  - Line item management
  - Tax calculations
  - Status tracking (Draft, Sent, Paid, Overdue)
  - Due date management
  - PDF generation (planned)
  - Invoice numbering system
- **Components**: DataTable
- **Lines of Code**: 299 LOC

#### 4. **Payments** (`pages/payments.js` + `payments.html`)
- **Features**:
  - Payment recording
  - Payment allocation to invoices
  - Payment methods (Cash, Check, Credit Card, Bank Transfer)
  - Payment status tracking
  - Reference number tracking
  - Unallocated amount handling
  - Payment history
- **Components**: DataTable, FormBuilder
- **Lines of Code**: 264 LOC

#### 5. **Journal Entries** (`pages/journal-entries.js` + `journal-entries.html`)
- **Features**:
  - Manual journal entry creation
  - Debit/Credit line items
  - Entry posting/unposting
  - Entry status (Draft, Posted)
  - Date filtering
  - Entry numbering
  - Balance validation
- **Components**: DataTable
- **Lines of Code**: 251 LOC

#### 6. **Reports** (`pages/reports.js` + `reports.html`)
- **Features**:
  - **Trial Balance Report**
  - **Balance Sheet Report**
  - **Income Statement (P&L)**
  - **Cash Flow Statement**
  - **General Ledger**
  - **Accounts Receivable Aging**
  - Date range selection
  - Export to PDF/Excel (planned)
  - Print functionality
- **Lines of Code**: 487 LOC

---

### **Shared Components**

#### 1. **DataTable** (`components/data-table.js`)
- Sortable columns
- Pagination
- Search/filtering
- Row selection
- Custom column rendering
- Action buttons per row
- **Lines of Code**: 529 LOC

#### 2. **FormBuilder** (`components/form-builder.js`)
- Dynamic form generation
- Field validation
- Multiple input types (text, number, select, textarea, date)
- Required field handling
- Form submission
- **Lines of Code**: 490 LOC

---

### **Module System** (`module.js`)
- Route registration
- Menu item registration
- Module initialization
- Configuration loading from backend
- Permission-based access
- **Lines of Code**: 240 LOC

---

### **Custom Styles** (`styles/financial.css`)
- Financial-specific styling
- Table layouts
- Form styling
- Modal designs

---

## 🔧 Fixes Needed

### **Priority 1: Fix Data Loading**

**File**: `modules/financial/frontend/pages/accounts.js` (and all other pages)

**Changes Needed**:
```javascript
// Add at top of each page class
async getTenantContext() {
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    return {
        tenant_id: user.tenant_id,
        company_id: user.company_id
    };
}

// Update loadAccounts method (line 134)
async loadAccounts() {
    try {
        const context = await this.getTenantContext();
        const queryParams = new URLSearchParams({
            tenant_id: context.tenant_id,
            company_id: context.company_id,
            ...this.filters
        });

        const response = await apiFetch(`/financial/accounts?${queryParams.toString()}`);

        if (response.ok) {
            this.accounts = await response.json();
            this.filterAccounts();
        }
    } catch (error) {
        console.error('Failed to load accounts:', error);
        this.showError('Failed to load accounts');
    }
}
```

**Apply to all pages**:
- ✅ accounts.js
- ✅ customers.js
- ✅ invoices.js
- ✅ payments.js
- ✅ journal-entries.js
- ✅ reports.js

---

### **Priority 2: Fix Template Loading**

**Issue**: Pages fetch HTML from `/modules/financial/frontend/pages/*.html`

**Possible Solutions**:
1. Configure web server to serve `/modules/` directory
2. Copy HTML templates to `/frontend/modules/financial/pages/`
3. Inline templates in JS files

---

### **Priority 3: Fix API Endpoints**

**Current**: Frontend calls `/financial/accounts`
**Should be**: `/api/v1/accounts` (or configure API prefix in module config)

**Check**: `apiFetch` function might already handle the `/api/v1` prefix

---

### **Priority 4: Fix Icon Rendering**

**Check**:
1. Browser console for CSS loading errors
2. Verify Phosphor icons CSS is included in index.html
3. Check if menu items from modules are rendered differently

---

## 📝 Summary

### What Works ✅
- ✅ Module structure is correct
- ✅ All 6 page files exist
- ✅ Component files exist
- ✅ Manifest.json has correct routes
- ✅ Icons are properly defined in manifest
- ✅ Backend sample data created successfully

### What's Broken ❌
- ❌ No tenant_id/company_id in API calls
- ❌ Template paths may not be served correctly
- ❌ Icons not showing in sidebar menu
- ❌ Module routing conflict (manifest vs module.js)

### Required Changes
1. Add tenant/company context to all API calls
2. Verify web server serves /modules/ directory
3. Update all 6 pages to include context in API calls
4. Debug icon rendering in menu system
5. Resolve routing conflict

---

## 🎯 Next Steps

1. **Immediate**: Fix tenant_id/company_id in API calls
2. **Then**: Test if data loads on accounts page
3. **Finally**: Fix icon display issue

Would you like me to create the fixes for these issues?
