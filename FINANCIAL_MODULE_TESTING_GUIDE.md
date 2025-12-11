# Financial Module - Frontend Testing Guide

## ✅ What Has Been Done

The financial module sample data setup script has been modified to work with your existing multi-tenant organization structure. It now supports:

- **TECHSTART** - Tech Startup tenant
- **FASHIONHUB** - Retail Chain tenant
- **MEDCARE** - Healthcare tenant
- **CLOUDWORK** - Remote Tech tenant
- **FINTECH** - Financial Services tenant

## 🚀 Quick Start - Test Financial Module Frontend

### Step 1: Frontend Server is Running

The frontend is already served at:
- **URL**: http://localhost:8080

### Step 2: Login to Test the Financial Module

You can login with any of these users:

#### **TECHSTART Tenant** (Recommended for first test)

| Email | Password | Role |
|-------|----------|------|
| `ceo@techstart.com` | `password123` | CEO |
| `cto@techstart.com` | `password123` | CTO |
| `dev1@techstart.com` | `password123` | Developer |

#### **FASHIONHUB Tenant**

| Email | Password | Role |
|-------|----------|------|
| `ceo@fashionhub.com` | `password123` | CEO |
| `cfo@fashionhub.com` | `password123` | CFO |
| `hr@fashionhub.com` | `password123` | HR Director |

### Step 3: Access Financial Module Pages

After logging in, navigate to these pages:

- **Dashboard**: `#/financial/dashboard` - Overview with revenue, expenses, profit cards
- **Accounts**: `#/financial/accounts` - Chart of accounts with filtering
- **Invoices**: `#/financial/invoices` - Invoice list with status filters
- **Payments**: `#/financial/payments` - Payment tracking (placeholder)
- **Reports**: `#/financial/reports` - Financial reports UI

## 📊 Setup Financial Sample Data

To populate the financial module with sample data for testing, you have two options:

### Option 1: Run Setup Script Directly (If Backend is Running)

```bash
cd modules/financial/backend

# For TECHSTART tenant
python setup_sample_data.py TECHSTART

# For FASHIONHUB tenant
python setup_sample_data.py FASHIONHUB
```

### Option 2: Using Docker (If Services are in Docker)

```bash
# Interactive setup
docker exec -it buildify-financial bash setup_tenants.sh

# Or specific tenant
docker exec -it buildify-financial python setup_sample_data.py TECHSTART
docker exec -it buildify-financial python setup_sample_data.py FASHIONHUB
```

## 📦 What Sample Data Gets Created

For each tenant, the script creates:

| Data Type | Count | Description |
|-----------|-------|-------------|
| **Accounts** | 50 | Complete chart of accounts (Assets, Liabilities, Equity, Revenue, Expenses) |
| **Tax Rates** | 2 | VAT (20%) and Sales Tax (7.5%) |
| **Customers** | 3 | Acme Corporation, TechCorp Industries, Global Solutions Ltd |
| **Invoices** | 3 | Mix of sent and draft invoices with line items |
| **Payments** | 2 | Customer payments (cleared and pending) |
| **Journal Entries** | 1 | Opening balance entry ($100,000 capital) |

### Sample Customers Created

| Customer # | Name | Credit Limit | Payment Terms |
|------------|------|--------------|---------------|
| CUST-001 | Acme Corporation | $50,000 | 30 days |
| CUST-002 | TechCorp Industries | $75,000 | 15 days |
| CUST-003 | Global Solutions Ltd | $100,000 | 30 days |

### Sample Invoices Created

| Invoice # | Customer | Amount | Status | Due Date |
|-----------|----------|---------|--------|----------|
| INV-2025-001 | Acme Corporation | $8,031.25 | sent | Today |
| INV-2025-002 | TechCorp Industries | $10,750.00 | sent | +15 days |
| INV-2025-003 | Global Solutions Ltd | $2,148.43 | draft | +25 days |

## 🎨 Financial Module Frontend Features

### 1. Dashboard Page (`dashboard-page.js`)
- Revenue, Expenses, Net Profit summary cards
- Quick action buttons
- Recent invoices widget

### 2. Accounts Page (`accounts-page.js`)
- Full chart of accounts table
- Account type filtering (Asset, Liability, Equity, Revenue, Expense)
- Create/Edit account forms
- Current balance display

### 3. Invoices Page (`invoices-page.js`)
- Invoice list with status badges
- Status filtering (All, Draft, Sent, Paid, Overdue)
- View invoice details button
- Create invoice button

### 4. Payments Page (`payments-page.js`)
- Placeholder page with "Coming Soon" message
- Ready for implementation

### 5. Reports Page (`reports-page.js`)
- Report templates UI
- Available reports:
  - Profit & Loss Statement
  - Balance Sheet
  - Cash Flow Statement
  - Trial Balance
  - General Ledger
  - Accounts Receivable Aging

## 🔧 Technical Details

### Frontend Technology Stack
- **Framework**: Vanilla JavaScript (ES6 modules)
- **Styling**: Tailwind CSS + Custom CSS
- **Icons**: Bootstrap Icons + Phosphor Icons
- **i18n**: i18next (supports EN, ES, DE, ID, FR)
- **Routing**: Hash-based routing (#/financial/...)

### Module Configuration
Location: `/frontend/modules/financial/manifest.json`

### Required Permissions
- `financial:accounts:read:company` - View accounts/dashboard
- `financial:invoices:read:company` - View invoices
- `financial:payments:read:company` - View payments
- `financial:reports:read:company` - View reports

## 🐛 Troubleshooting

### Issue: Financial Module Not Showing in Menu

1. **Check if module is enabled** for the tenant
2. **Verify user has permissions** (financial:accounts:read:company)
3. **Use debug tool**: Open `http://localhost:8080/debug-financial-module.html`
4. **Check browser console** for JavaScript errors

### Issue: No Data Showing After Login

1. **Run the setup script** for your tenant:
   ```bash
   python setup_sample_data.py TECHSTART
   ```
2. **Verify data was created** by checking the script output
3. **Refresh the browser** and login again

### Issue: Frontend Not Loading

1. **Check if server is running**:
   ```bash
   lsof -i :8080  # or: netstat -tuln | grep 8080
   ```
2. **Start the server**:
   ```bash
   cd frontend
   python3 -m http.server 8080
   ```
3. **Check browser console** for errors

## 📝 Next Steps

1. **Login** to frontend: http://localhost:8080
2. **Use credentials**: `ceo@techstart.com` / `password123`
3. **Navigate** to `#/financial/dashboard`
4. **Test all pages** to verify frontend functionality
5. **Check API integration** (data loading from backend)

## 📚 Additional Resources

- **Setup Guide**: `modules/financial/backend/SETUP_GUIDE.md`
- **Module Documentation**: `docs/FINANCIAL_MODULE_COMPLETE.md`
- **API Documentation**: http://localhost:9001/docs (if backend is running)
- **Debug Tool**: http://localhost:8080/debug-financial-module.html

---

**Ready to test!** 🎉

Open http://localhost:8080 and login with `ceo@techstart.com` / `password123` to start testing the financial module frontend.
