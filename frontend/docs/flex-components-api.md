# Flex Components API Documentation

Complete API reference and usage guide for all Flex components in the application.

## Table of Contents

1. [Form Components](#form-components)
   - [FlexInput](#flexinput)
   - [FlexTextarea](#flextextarea)
   - [FlexSelect](#flexselect)
   - [FlexCheckbox](#flexcheckbox)
   - [FlexRadio](#flexradio)

2. [UI Components](#ui-components)
   - [FlexButton](#flexbutton)
   - [FlexCard](#flexcard)
   - [FlexModal](#flexmodal)
   - [FlexTabs](#flextabs)
   - [FlexAccordion](#flexaccordion)
   - [FlexBreadcrumb](#flexbreadcrumb)

3. [Feedback Components](#feedback-components)
   - [FlexAlert](#flexalert)
   - [FlexBadge](#flexbadge)
   - [FlexTooltip](#flextooltip)
   - [FlexSpinner](#flexspinner)

4. [Navigation Components](#navigation-components)
   - [FlexDropdown](#flexdropdown)

5. [Data Display Components](#data-display-components)
   - [FlexTable](#flextable)
   - [FlexDataGrid](#flexdatagrid)
   - [FlexPagination](#flexpagination)

6. [Layout Components](#layout-components)
   - [FlexDrawer](#flexdrawer)
   - [FlexStepper](#flexstepper)

---

## Form Components

### FlexInput

A versatile input field component with validation, character counting, and various styling options.

#### Options

```javascript
{
  type: 'text',              // Input type: text, email, password, number, tel, url, search, date, time
  label: '',                 // Label text
  value: '',                 // Initial value
  placeholder: '',           // Placeholder text
  required: false,           // Mark as required
  disabled: false,           // Disable input
  readonly: false,           // Make read-only
  helperText: '',            // Helper text below input
  errorText: '',             // Error message
  maxLength: null,           // Maximum character length
  minLength: null,           // Minimum character length
  pattern: null,             // Validation pattern (regex)
  min: null,                 // Minimum value (for number/date)
  max: null,                 // Maximum value (for number/date)
  step: null,                // Step value (for number)
  showCharCount: false,      // Show character counter
  variant: 'outlined',       // Style variant: outlined, filled, underlined
  size: 'md',                // Size: sm, md, lg
  fullWidth: false,          // Full width
  icon: null,                // Icon HTML
  iconPosition: 'left',      // Icon position: left, right
  autocomplete: 'off',       // Autocomplete attribute
  classes: '',               // Additional CSS classes
  permission: null           // RBAC permission required
}
```

#### Events

- `change` - Fired when value changes
- `input` - Fired on input
- `focus` - Fired when focused
- `blur` - Fired when blurred
- `validate` - Fired on validation

#### Methods

- `getValue()` - Get current value
- `setValue(value)` - Set value programmatically
- `validate()` - Validate input and return boolean
- `focus()` - Focus the input
- `disable()` - Disable the input
- `enable()` - Enable the input
- `setError(message)` - Set error message
- `clearError()` - Clear error message

#### Sample Code

```javascript
import FlexInput from './components/flex-input.js';

// Basic usage
const container = document.getElementById('input-container');
const input = new FlexInput(container, {
  label: 'Email Address',
  type: 'email',
  placeholder: 'Enter your email',
  required: true,
  helperText: 'We\'ll never share your email'
});

// Listen to changes
input.on('change', (value) => {
  console.log('Email changed:', value);
});

// Validate
if (input.validate()) {
  const email = input.getValue();
  console.log('Valid email:', email);
}

// Advanced usage with character counter
const bioInput = new FlexInput(container, {
  label: 'Bio',
  type: 'text',
  maxLength: 160,
  showCharCount: true,
  variant: 'outlined',
  size: 'lg',
  helperText: 'Tell us about yourself'
});

// Password with validation pattern
const passwordInput = new FlexInput(container, {
  label: 'Password',
  type: 'password',
  required: true,
  minLength: 8,
  pattern: '^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d).+$',
  helperText: 'Must contain uppercase, lowercase, and number',
  icon: '<i class="ph-duotone ph-lock"></i>',
  iconPosition: 'left'
});

// Set error programmatically
input.setError('This email is already taken');
```

---

### FlexTextarea

Multi-line text input with auto-resize and character counting.

#### Options

```javascript
{
  label: '',                 // Label text
  value: '',                 // Initial value
  placeholder: '',           // Placeholder text
  rows: 3,                   // Initial number of rows
  maxLength: null,           // Maximum character length
  required: false,           // Mark as required
  disabled: false,           // Disable textarea
  readonly: false,           // Make read-only
  helperText: '',            // Helper text
  errorText: '',             // Error message
  showCharCount: false,      // Show character counter
  autoResize: true,          // Auto-resize based on content
  variant: 'outlined',       // Style variant
  size: 'md',                // Size: sm, md, lg
  fullWidth: false,          // Full width
  classes: '',               // Additional CSS classes
  permission: null           // RBAC permission required
}
```

#### Sample Code

```javascript
import FlexTextarea from './components/flex-textarea.js';

const textarea = new FlexTextarea(container, {
  label: 'Description',
  placeholder: 'Enter a detailed description',
  rows: 5,
  maxLength: 500,
  showCharCount: true,
  autoResize: true,
  required: true,
  helperText: 'Provide as much detail as possible'
});

// Get value
const description = textarea.getValue();

// Set value
textarea.setValue('New description text');
```

---

### FlexSelect

Dropdown select component with search and multi-select support.

#### Options

```javascript
{
  label: '',                 // Label text
  value: '',                 // Initial value (or array for multi-select)
  placeholder: 'Select...',  // Placeholder text
  options: [],               // Array of {value, label, disabled?} objects
  required: false,           // Mark as required
  disabled: false,           // Disable select
  helperText: '',            // Helper text
  errorText: '',             // Error message
  searchable: false,         // Enable search
  multiple: false,           // Multi-select mode
  clearable: false,          // Show clear button
  variant: 'outlined',       // Style variant
  size: 'md',                // Size: sm, md, lg
  fullWidth: false,          // Full width
  classes: '',               // Additional CSS classes
  permission: null           // RBAC permission required
}
```

#### Sample Code

```javascript
import FlexSelect from './components/flex-select.js';

// Basic select
const countrySelect = new FlexSelect(container, {
  label: 'Country',
  placeholder: 'Select your country',
  required: true,
  searchable: true,
  options: [
    { value: 'us', label: 'United States' },
    { value: 'uk', label: 'United Kingdom' },
    { value: 'ca', label: 'Canada' },
    { value: 'au', label: 'Australia' }
  ]
});

// Multi-select with clearable
const tagsSelect = new FlexSelect(container, {
  label: 'Tags',
  multiple: true,
  clearable: true,
  searchable: true,
  options: [
    { value: 'javascript', label: 'JavaScript' },
    { value: 'python', label: 'Python' },
    { value: 'java', label: 'Java' },
    { value: 'csharp', label: 'C#' }
  ]
});

// Listen to changes
countrySelect.on('change', (value) => {
  console.log('Selected country:', value);
});

// Get selected value(s)
const country = countrySelect.getValue();
const tags = tagsSelect.getValue(); // Array for multi-select
```

---

### FlexCheckbox

Checkbox component with support for indeterminate state.

#### Options

```javascript
{
  label: '',                 // Label text
  checked: false,            // Initial checked state
  value: '',                 // Checkbox value
  disabled: false,           // Disable checkbox
  indeterminate: false,      // Indeterminate state
  required: false,           // Mark as required
  helperText: '',            // Helper text
  size: 'md',                // Size: sm, md, lg
  classes: '',               // Additional CSS classes
  permission: null           // RBAC permission required
}
```

#### Sample Code

```javascript
import FlexCheckbox from './components/flex-checkbox.js';

// Simple checkbox
const termsCheckbox = new FlexCheckbox(container, {
  label: 'I agree to the terms and conditions',
  required: true,
  value: 'agreed'
});

// Listen to changes
termsCheckbox.on('change', (checked) => {
  console.log('Agreed to terms:', checked);
});

// Checkbox with helper text
const newsletterCheckbox = new FlexCheckbox(container, {
  label: 'Subscribe to newsletter',
  helperText: 'Receive weekly updates and promotions',
  checked: true
});

// Indeterminate checkbox (for "select all" scenarios)
const selectAllCheckbox = new FlexCheckbox(container, {
  label: 'Select All',
  indeterminate: true
});

// Get checked state
const isChecked = termsCheckbox.getValue();
```

---

### FlexRadio

Radio button component with group support.

#### Options

```javascript
{
  name: '',                  // Radio group name
  label: '',                 // Label text
  value: '',                 // Radio value
  checked: false,            // Initial checked state
  disabled: false,           // Disable radio
  required: false,           // Mark as required
  helperText: '',            // Helper text
  size: 'md',                // Size: sm, md, lg
  classes: '',               // Additional CSS classes
  permission: null           // RBAC permission required
}
```

#### Sample Code

```javascript
import FlexRadio from './components/flex-radio.js';

// Radio group
const container = document.getElementById('payment-method');

const creditCardRadio = new FlexRadio(container, {
  name: 'payment',
  label: 'Credit Card',
  value: 'credit',
  checked: true
});

const paypalRadio = new FlexRadio(container, {
  name: 'payment',
  label: 'PayPal',
  value: 'paypal'
});

const bankRadio = new FlexRadio(container, {
  name: 'payment',
  label: 'Bank Transfer',
  value: 'bank'
});

// Listen to changes
creditCardRadio.on('change', (value) => {
  console.log('Payment method:', value);
});

// Get selected value
const paymentMethod = creditCardRadio.getValue();
```

---

## UI Components

### FlexButton

Button component with loading states, icons, and variants.

#### Options

```javascript
{
  text: '',                  // Button text
  type: 'button',            // Button type: button, submit, reset
  variant: 'primary',        // Variant: primary, secondary, success, danger, warning, ghost
  size: 'md',                // Size: sm, md, lg
  icon: null,                // Icon HTML
  iconPosition: 'left',      // Icon position: left, right
  disabled: false,           // Disable button
  loading: false,            // Loading state
  fullWidth: false,          // Full width
  outline: false,            // Outlined style
  rounded: false,            // Fully rounded
  classes: '',               // Additional CSS classes
  onClick: null,             // Click handler
  permission: null           // RBAC permission required
}
```

#### Methods

- `setLoading(isLoading)` - Set loading state
- `disable()` - Disable button
- `enable()` - Enable button
- `setText(text)` - Change button text

#### Sample Code

```javascript
import FlexButton from './components/flex-button.js';

// Basic button
const saveBtn = new FlexButton(container, {
  text: 'Save Changes',
  variant: 'primary',
  icon: '<i class="ph-duotone ph-floppy-disk"></i>',
  onClick: async () => {
    saveBtn.setLoading(true);
    try {
      await saveData();
      console.log('Saved!');
    } finally {
      saveBtn.setLoading(false);
    }
  }
});

// Danger button
const deleteBtn = new FlexButton(container, {
  text: 'Delete',
  variant: 'danger',
  icon: '<i class="ph-duotone ph-trash"></i>',
  onClick: () => {
    if (confirm('Are you sure?')) {
      deleteRecord();
    }
  }
});

// Ghost button with right icon
const exportBtn = new FlexButton(container, {
  text: 'Export',
  variant: 'ghost',
  icon: '<i class="ph-duotone ph-download"></i>',
  iconPosition: 'right',
  size: 'sm'
});

// Full width button
const submitBtn = new FlexButton(container, {
  text: 'Submit Form',
  type: 'submit',
  variant: 'success',
  fullWidth: true,
  size: 'lg'
});

// With RBAC permission
const adminBtn = new FlexButton(container, {
  text: 'Admin Settings',
  permission: 'admin:settings:manage'
});
```

---

### FlexCard

Card container component with header, body, and footer sections.

#### Options

```javascript
{
  title: '',                 // Card title
  subtitle: '',              // Card subtitle
  headerActions: [],         // Array of action buttons in header
  footer: null,              // Footer content (HTML or element)
  bordered: true,            // Show border
  shadow: true,              // Show shadow
  hoverable: false,          // Hover effect
  padding: 'md',             // Padding size: sm, md, lg
  classes: '',               // Additional CSS classes
  permission: null           // RBAC permission required
}
```

#### Sample Code

```javascript
import FlexCard from './components/flex-card.js';

// Basic card
const card = new FlexCard(container, {
  title: 'User Profile',
  subtitle: 'Manage your profile information',
  bordered: true,
  shadow: true
});

// Add content to card body
const cardBody = card.getBodyElement();
cardBody.innerHTML = `
  <div class="space-y-4">
    <p>Name: John Doe</p>
    <p>Email: john@example.com</p>
  </div>
`;

// Card with header actions
const dashboardCard = new FlexCard(container, {
  title: 'Sales Overview',
  headerActions: [
    { text: 'Refresh', icon: '<i class="ph-duotone ph-arrow-clockwise"></i>', onClick: refresh },
    { text: 'Export', icon: '<i class="ph-duotone ph-download"></i>', onClick: exportData }
  ],
  shadow: true
});

// Card with footer
const formCard = new FlexCard(container, {
  title: 'Create Account',
  footer: `
    <div class="flex justify-end gap-2">
      <button class="px-4 py-2 text-gray-700">Cancel</button>
      <button class="px-4 py-2 bg-blue-600 text-white rounded">Submit</button>
    </div>
  `
});
```

---

### FlexModal

Modal dialog component with customizable size, actions, and backdrop.

#### Options

```javascript
{
  title: '',                 // Modal title
  content: null,             // Content (HTML string or element)
  size: 'md',                // Size: sm, md, lg, xl, full
  actions: [],               // Array of action buttons
  closeButton: true,         // Show close button
  closeOnBackdrop: true,     // Close on backdrop click
  closeOnEscape: true,       // Close on ESC key
  backdrop: true,            // Show backdrop
  scrollable: true,          // Scrollable content
  centered: true,            // Center vertically
  classes: '',               // Additional CSS classes
  onOpen: null,              // Callback when opened
  onClose: null,             // Callback when closed
  permission: null           // RBAC permission required
}
```

#### Methods

- `open()` - Open modal
- `close()` - Close modal
- `setTitle(title)` - Change title
- `setContent(content)` - Change content
- `setLoading(isLoading)` - Set loading state on actions

#### Sample Code

```javascript
import FlexModal from './components/flex-modal.js';

// Basic modal
const container = document.createElement('div');
document.body.appendChild(container);

const modal = new FlexModal(container, {
  title: 'Confirm Delete',
  content: '<p>Are you sure you want to delete this item?</p>',
  size: 'sm',
  actions: [
    {
      label: 'Cancel',
      variant: 'secondary',
      onClick: () => modal.close()
    },
    {
      label: 'Delete',
      variant: 'danger',
      onClick: async () => {
        modal.setLoading(true);
        await deleteItem();
        modal.close();
      }
    }
  ]
});

modal.open();

// Form modal
const formContainer = document.createElement('div');
formContainer.innerHTML = `
  <form id="user-form">
    <input type="text" name="name" placeholder="Name" class="input mb-3" />
    <input type="email" name="email" placeholder="Email" class="input mb-3" />
  </form>
`;

const formModal = new FlexModal(document.body, {
  title: 'Add User',
  content: formContainer,
  size: 'md',
  closeOnBackdrop: false,
  actions: [
    { label: 'Cancel', variant: 'secondary', onClick: () => formModal.close() },
    {
      label: 'Save',
      variant: 'primary',
      onClick: () => {
        const formData = new FormData(document.getElementById('user-form'));
        saveUser(Object.fromEntries(formData));
        formModal.close();
      }
    }
  ],
  onClose: () => {
    console.log('Modal closed');
  }
});

// Large scrollable modal
const largeModal = new FlexModal(document.body, {
  title: 'Terms and Conditions',
  content: '<div style="height: 800px;">Long content...</div>',
  size: 'lg',
  scrollable: true,
  actions: [
    { label: 'I Agree', variant: 'primary', onClick: () => largeModal.close() }
  ]
});
```

---

### FlexTabs

Tab navigation component with keyboard support.

#### Options

```javascript
{
  tabs: [],                  // Array of {id, label, content, disabled?, permission?}
  activeTab: null,           // Initial active tab ID
  variant: 'default',        // Variant: default, pills, underlined
  orientation: 'horizontal', // Orientation: horizontal, vertical
  classes: '',               // Additional CSS classes
  onChange: null             // Tab change callback
}
```

#### Sample Code

```javascript
import FlexTabs from './components/flex-tabs.js';

const tabs = new FlexTabs(container, {
  tabs: [
    {
      id: 'profile',
      label: 'Profile',
      content: '<div>Profile content...</div>'
    },
    {
      id: 'settings',
      label: 'Settings',
      content: '<div>Settings content...</div>'
    },
    {
      id: 'billing',
      label: 'Billing',
      content: '<div>Billing content...</div>',
      permission: 'billing:view'
    }
  ],
  activeTab: 'profile',
  variant: 'underlined',
  onChange: (tabId) => {
    console.log('Active tab:', tabId);
  }
});

// Change tab programmatically
tabs.setActiveTab('settings');

// Vertical tabs
const verticalTabs = new FlexTabs(container, {
  orientation: 'vertical',
  variant: 'pills',
  tabs: [/* ... */]
});
```

---

### FlexAccordion

Collapsible accordion component.

#### Options

```javascript
{
  items: [],                 // Array of {id, title, content, open?, disabled?}
  allowMultiple: false,      // Allow multiple items open
  classes: '',               // Additional CSS classes
  onChange: null             // Change callback
}
```

#### Sample Code

```javascript
import FlexAccordion from './components/flex-accordion.js';

const accordion = new FlexAccordion(container, {
  items: [
    {
      id: 'faq1',
      title: 'What is your return policy?',
      content: '<p>We offer 30-day returns on all items...</p>',
      open: true
    },
    {
      id: 'faq2',
      title: 'How long does shipping take?',
      content: '<p>Shipping typically takes 3-5 business days...</p>'
    },
    {
      id: 'faq3',
      title: 'Do you ship internationally?',
      content: '<p>Yes, we ship to over 100 countries...</p>'
    }
  ],
  allowMultiple: false,
  onChange: (openItems) => {
    console.log('Open items:', openItems);
  }
});

// Toggle item programmatically
accordion.toggle('faq2');

// Open specific item
accordion.open('faq3');

// Close all
accordion.closeAll();
```

---

### FlexBreadcrumb

Breadcrumb navigation component.

#### Options

```javascript
{
  items: [],                 // Array of {label, href?, onClick?, active?}
  separator: '/',            // Separator character
  classes: ''                // Additional CSS classes
}
```

#### Sample Code

```javascript
import FlexBreadcrumb from './components/flex-breadcrumb.js';

const breadcrumb = new FlexBreadcrumb(container, {
  items: [
    { label: 'Home', href: '/' },
    { label: 'Products', href: '/products' },
    { label: 'Electronics', href: '/products/electronics' },
    { label: 'Laptops', active: true }
  ],
  separator: '>'
});

// With click handlers instead of href
const breadcrumbWithHandlers = new FlexBreadcrumb(container, {
  items: [
    { label: 'Dashboard', onClick: () => navigateTo('dashboard') },
    { label: 'Reports', onClick: () => navigateTo('reports') },
    { label: 'Sales Report', active: true }
  ]
});
```

---

## Feedback Components

### FlexAlert

Alert/notification component with auto-dismiss and actions.

#### Options

```javascript
{
  message: '',               // Alert message
  variant: 'info',           // Variant: success, info, warning, danger
  dismissible: true,         // Show dismiss button
  icon: true,                // Show icon
  autoDismiss: false,        // Auto-dismiss after delay
  dismissDelay: 5000,        // Delay in ms before auto-dismiss
  actions: [],               // Array of action buttons
  classes: '',               // Additional CSS classes
  onDismiss: null            // Dismiss callback
}
```

#### Sample Code

```javascript
import FlexAlert from './components/flex-alert.js';

// Success alert
const successAlert = new FlexAlert(container, {
  message: 'Your changes have been saved successfully!',
  variant: 'success',
  dismissible: true,
  autoDismiss: true,
  dismissDelay: 3000
});

// Error alert with actions
const errorAlert = new FlexAlert(container, {
  message: 'Failed to save changes. Please try again.',
  variant: 'danger',
  dismissible: true,
  actions: [
    {
      label: 'Retry',
      onClick: () => {
        retryOperation();
        errorAlert.dismiss();
      }
    },
    {
      label: 'View Details',
      onClick: () => showErrorDetails()
    }
  ]
});

// Warning without icon
const warningAlert = new FlexAlert(container, {
  message: 'Your session will expire in 5 minutes',
  variant: 'warning',
  icon: false,
  onDismiss: () => {
    console.log('Alert dismissed');
  }
});

// Info alert
const infoAlert = new FlexAlert(container, {
  message: 'New features are available. Check out the changelog.',
  variant: 'info',
  dismissible: true
});
```

---

### FlexBadge

Badge component for status indicators and counts.

#### Options

```javascript
{
  text: '',                  // Badge text
  variant: 'default',        // Variant: default, primary, success, danger, warning, info
  size: 'md',                // Size: sm, md, lg
  dot: false,                // Show dot indicator
  outline: false,            // Outlined style
  dismissible: false,        // Show dismiss button
  rounded: true,             // Rounded style
  classes: '',               // Additional CSS classes
  onDismiss: null            // Dismiss callback
}
```

#### Sample Code

```javascript
import FlexBadge from './components/flex-badge.js';

// Status badge
const activeBadge = new FlexBadge(container, {
  text: 'Active',
  variant: 'success',
  size: 'sm'
});

// Count badge
const notificationBadge = new FlexBadge(container, {
  text: '23',
  variant: 'danger',
  size: 'sm',
  rounded: true
});

// Dot indicator
const statusDot = new FlexBadge(container, {
  text: 'Online',
  variant: 'success',
  dot: true
});

// Dismissible tag badges
const tag1 = new FlexBadge(container, {
  text: 'JavaScript',
  variant: 'primary',
  dismissible: true,
  outline: true,
  onDismiss: () => {
    console.log('Tag removed');
  }
});

// Large outline badge
const categoryBadge = new FlexBadge(container, {
  text: 'Premium',
  variant: 'warning',
  size: 'lg',
  outline: true
});
```

---

### FlexTooltip

Tooltip component with positioning and triggers.

#### Options

```javascript
{
  content: '',               // Tooltip content
  position: 'top',           // Position: top, bottom, left, right
  trigger: 'hover',          // Trigger: hover, click, focus
  delay: 200,                // Show delay in ms
  arrow: true,               // Show arrow
  classes: ''                // Additional CSS classes
}
```

#### Methods

- `show()` - Show tooltip
- `hide()` - Hide tooltip
- `toggle()` - Toggle tooltip

#### Sample Code

```javascript
import FlexTooltip from './components/flex-tooltip.js';

// Basic tooltip on button
const button = document.createElement('button');
button.textContent = 'Hover me';
container.appendChild(button);

const tooltip = new FlexTooltip(button, {
  content: 'This is a helpful tooltip',
  position: 'top'
});

// Tooltip with HTML content
const infoIcon = document.createElement('i');
infoIcon.className = 'ph-duotone ph-info';
container.appendChild(infoIcon);

const infoTooltip = new FlexTooltip(infoIcon, {
  content: '<strong>Info:</strong> Click for more details',
  position: 'right',
  trigger: 'hover'
});

// Click trigger tooltip
const clickableElement = document.getElementById('clickable');
const clickTooltip = new FlexTooltip(clickableElement, {
  content: 'Click to copy',
  trigger: 'click',
  position: 'bottom'
});

// Show/hide programmatically
tooltip.show();
setTimeout(() => tooltip.hide(), 3000);
```

---

### FlexSpinner

Loading spinner component with variants and sizes.

#### Options

```javascript
{
  variant: 'border',         // Variant: border, dots, pulse, bars
  size: 'md',                // Size: sm, md, lg, xl
  color: 'primary',          // Color: primary, secondary, white
  overlay: false,            // Show as overlay
  text: '',                  // Loading text
  fullscreen: false,         // Fullscreen overlay
  classes: ''                // Additional CSS classes
}
```

#### Methods

- `show()` - Show spinner
- `hide()` - Hide spinner

#### Sample Code

```javascript
import FlexSpinner from './components/flex-spinner.js';

// Basic spinner
const spinner = new FlexSpinner(container, {
  variant: 'border',
  size: 'md',
  color: 'primary'
});

// Spinner with text
const loadingSpinner = new FlexSpinner(container, {
  variant: 'dots',
  size: 'lg',
  text: 'Loading...',
  color: 'primary'
});

// Overlay spinner
const overlaySpinner = new FlexSpinner(document.body, {
  overlay: true,
  text: 'Processing your request...',
  size: 'xl'
});

// Show during async operation
overlaySpinner.show();
try {
  await fetchData();
} finally {
  overlaySpinner.hide();
}

// Fullscreen spinner
const fullscreenSpinner = new FlexSpinner(document.body, {
  fullscreen: true,
  variant: 'pulse',
  text: 'Please wait...',
  size: 'xl'
});

// Different variants
const dotsSpinner = new FlexSpinner(container, { variant: 'dots' });
const pulseSpinner = new FlexSpinner(container, { variant: 'pulse' });
const barsSpinner = new FlexSpinner(container, { variant: 'bars' });
```

---

## Navigation Components

### FlexDropdown

Dropdown menu component with RBAC and search.

#### Options

```javascript
{
  trigger: null,             // Trigger element
  items: [],                 // Array of {label, value, icon?, divider?, header?, permission?, onClick?}
  position: 'bottom-start',  // Position: bottom-start, bottom-end, top-start, top-end
  searchable: false,         // Enable search
  closeOnSelect: true,       // Close on item select
  maxHeight: '300px',        // Max height
  classes: '',               // Additional CSS classes
  onSelect: null             // Select callback
}
```

#### Sample Code

```javascript
import FlexDropdown from './components/flex-dropdown.js';

// Basic dropdown
const triggerBtn = document.getElementById('menu-button');

const dropdown = new FlexDropdown(container, {
  trigger: triggerBtn,
  items: [
    {
      label: 'Edit',
      icon: '<i class="ph-duotone ph-pencil"></i>',
      onClick: () => editItem()
    },
    {
      label: 'Duplicate',
      icon: '<i class="ph-duotone ph-copy"></i>',
      onClick: () => duplicateItem()
    },
    { divider: true },
    {
      label: 'Delete',
      icon: '<i class="ph-duotone ph-trash"></i>',
      onClick: () => deleteItem()
    }
  ],
  position: 'bottom-start'
});

// Dropdown with sections and RBAC
const advancedDropdown = new FlexDropdown(container, {
  trigger: document.getElementById('actions-btn'),
  searchable: true,
  items: [
    { header: 'View Options' },
    { label: 'Grid View', icon: '<i class="ph-duotone ph-grid"></i>', value: 'grid' },
    { label: 'List View', icon: '<i class="ph-duotone ph-list"></i>', value: 'list' },
    { divider: true },
    { header: 'Actions' },
    { label: 'Export', icon: '<i class="ph-duotone ph-download"></i>', value: 'export' },
    { label: 'Settings', icon: '<i class="ph-duotone ph-gear"></i>', value: 'settings', permission: 'settings:manage' }
  ],
  onSelect: (item) => {
    console.log('Selected:', item.value);
  }
});

// User menu dropdown
const userMenuDropdown = new FlexDropdown(container, {
  trigger: document.getElementById('user-avatar'),
  position: 'bottom-end',
  items: [
    { header: 'John Doe' },
    { label: 'Profile', icon: '<i class="ph-duotone ph-user"></i>' },
    { label: 'Settings', icon: '<i class="ph-duotone ph-gear"></i>' },
    { divider: true },
    { label: 'Logout', icon: '<i class="ph-duotone ph-sign-out"></i>' }
  ]
});
```

---

## Data Display Components

### FlexTable

Advanced data table with sorting, filtering, pagination, and row actions.

#### Options

```javascript
{
  columns: [],               // Array of column definitions
  data: [],                  // Initial data array
  sortable: true,            // Enable sorting
  filterable: true,          // Enable column filtering
  searchable: true,          // Enable global search
  paginated: true,           // Enable pagination
  pageSize: 10,              // Items per page
  selectable: false,         // Enable row selection
  singleSelect: false,       // Single row selection mode
  rowActions: [],            // Row action buttons
  bulkActions: [],           // Bulk action buttons
  emptyMessage: 'No data',   // Empty state message
  loading: false,            // Loading state
  classes: '',               // Additional CSS classes
  onRowClick: null,          // Row click handler
  onSort: null,              // Sort callback
  onFilter: null,            // Filter callback
  onSearch: null,            // Search callback
  onPageChange: null,        // Page change callback
  onSelectionChange: null    // Selection change callback
}
```

#### Column Definition

```javascript
{
  field: '',                 // Data field key
  title: '',                 // Column title
  sortable: true,            // Sortable column
  filterable: true,          // Filterable column
  searchable: true,          // Include in search
  width: null,               // Column width
  minWidth: null,            // Min width
  align: 'left',             // Alignment: left, center, right
  render: null,              // Custom render function
  permission: null           // RBAC permission
}
```

#### Methods

- `refresh()` - Refresh table data
- `setData(data)` - Set new data
- `getSelectedRows()` - Get selected rows
- `clearSelection()` - Clear selection
- `setLoading(isLoading)` - Set loading state
- `exportToCSV(filename)` - Export to CSV

#### Sample Code

```javascript
import FlexTable from './components/flex-table.js';

// Basic table
const table = new FlexTable(container, {
  columns: [
    { field: 'id', title: 'ID', width: '80px', sortable: true },
    { field: 'name', title: 'Name', sortable: true, searchable: true },
    { field: 'email', title: 'Email', sortable: true, searchable: true },
    {
      field: 'status',
      title: 'Status',
      render: (value, row) => {
        const colors = { active: 'green', inactive: 'gray', pending: 'yellow' };
        return `<span class="px-2 py-1 bg-${colors[value]}-100 text-${colors[value]}-700 rounded">${value}</span>`;
      }
    },
    { field: 'created_at', title: 'Created', sortable: true }
  ],
  data: [
    { id: 1, name: 'John Doe', email: 'john@example.com', status: 'active', created_at: '2024-01-15' },
    { id: 2, name: 'Jane Smith', email: 'jane@example.com', status: 'inactive', created_at: '2024-01-16' }
  ],
  sortable: true,
  searchable: true,
  paginated: true,
  pageSize: 10
});

// Table with row actions and selection
const advancedTable = new FlexTable(container, {
  columns: [
    { field: 'name', title: 'Product Name' },
    { field: 'price', title: 'Price', align: 'right' },
    { field: 'stock', title: 'Stock', align: 'center' }
  ],
  data: products,
  selectable: true,
  rowActions: [
    {
      label: 'Edit',
      icon: '<i class="ph-duotone ph-pencil"></i>',
      permission: 'products:edit',
      onClick: (row) => editProduct(row)
    },
    {
      label: 'Delete',
      icon: '<i class="ph-duotone ph-trash"></i>',
      permission: 'products:delete',
      onClick: (row) => deleteProduct(row)
    }
  ],
  bulkActions: [
    {
      label: 'Delete Selected',
      variant: 'danger',
      onClick: (selectedRows) => {
        deleteProducts(selectedRows.map(r => r.id));
      }
    },
    {
      label: 'Export Selected',
      onClick: (selectedRows) => {
        exportProducts(selectedRows);
      }
    }
  ],
  onSelectionChange: (selectedRows) => {
    console.log('Selected:', selectedRows.length);
  }
});

// Listen to events
table.on('sort', ({ field, direction }) => {
  console.log(`Sorted by ${field} ${direction}`);
});

table.on('search', (searchTerm) => {
  console.log('Search:', searchTerm);
});

// Programmatic control
table.setLoading(true);
const data = await fetchData();
table.setData(data);
table.setLoading(false);

// Export
table.exportToCSV('products.csv');
```

---

### FlexDataGrid

Excel-like data grid with inline editing and advanced features.

#### Options

```javascript
{
  columns: [],               // Column definitions
  data: [],                  // Initial data
  editable: true,            // Enable editing
  resizable: true,           // Resizable columns
  reorderable: true,         // Reorderable columns
  frozenColumns: 0,          // Number of frozen columns
  virtualScroll: true,       // Virtual scrolling
  rowHeight: 40,             // Row height in pixels
  minColumnWidth: 80,        // Min column width
  classes: '',               // Additional CSS classes
  onCellEdit: null,          // Cell edit callback
  onColumnResize: null,      // Column resize callback
  onColumnReorder: null      // Column reorder callback
}
```

#### Methods

- `setData(data)` - Set new data
- `getData()` - Get all data
- `getCellValue(row, col)` - Get cell value
- `setCellValue(row, col, value)` - Set cell value
- `addRow(data)` - Add new row
- `deleteRow(rowIndex)` - Delete row
- `exportToExcel(filename)` - Export to Excel

#### Sample Code

```javascript
import FlexDataGrid from './components/flex-datagrid.js';

// Basic data grid
const grid = new FlexDataGrid(container, {
  columns: [
    { field: 'id', title: 'ID', width: 80, editable: false },
    { field: 'product', title: 'Product Name', width: 200 },
    { field: 'quantity', title: 'Quantity', width: 100, type: 'number' },
    { field: 'price', title: 'Price', width: 120, type: 'number', format: 'currency' },
    { field: 'total', title: 'Total', width: 120, editable: false,
      compute: (row) => row.quantity * row.price }
  ],
  data: [
    { id: 1, product: 'Laptop', quantity: 2, price: 999 },
    { id: 2, product: 'Mouse', quantity: 5, price: 29 }
  ],
  editable: true,
  resizable: true
});

// Advanced grid with frozen columns
const inventoryGrid = new FlexDataGrid(container, {
  columns: [
    { field: 'sku', title: 'SKU', width: 100, frozen: true },
    { field: 'name', title: 'Product Name', width: 200 },
    { field: 'category', title: 'Category', width: 150, type: 'select',
      options: ['Electronics', 'Clothing', 'Food'] },
    { field: 'stock', title: 'Stock', width: 100, type: 'number' },
    { field: 'reorder_point', title: 'Reorder Point', width: 120, type: 'number' },
    { field: 'last_ordered', title: 'Last Ordered', width: 150, type: 'date' }
  ],
  data: inventory,
  frozenColumns: 1,
  virtualScroll: true,
  rowHeight: 50,
  onCellEdit: (row, col, oldValue, newValue) => {
    console.log(`Cell [${row}, ${col}] changed from ${oldValue} to ${newValue}`);
    saveToBackend(row, col, newValue);
  }
});

// Listen to keyboard events
grid.on('keydown', (event) => {
  if (event.key === 'Delete') {
    const { row, col } = grid.getSelectedCell();
    grid.setCellValue(row, col, '');
  }
});

// Add row programmatically
grid.addRow({ id: 3, product: 'Keyboard', quantity: 3, price: 79 });

// Export to Excel
grid.exportToExcel('inventory.xlsx');

// Get all data
const allData = grid.getData();
console.log('Grid data:', allData);
```

---

### FlexPagination

Pagination component with page size selector and keyboard navigation.

#### Options

```javascript
{
  totalItems: 0,             // Total number of items
  itemsPerPage: 10,          // Items per page
  currentPage: 1,            // Current page number
  maxButtons: 5,             // Max page buttons to show
  showFirstLast: true,       // Show first/last buttons
  showPrevNext: true,        // Show prev/next buttons
  showPageSize: true,        // Show page size selector
  pageSizeOptions: [10, 25, 50, 100], // Page size options
  showInfo: true,            // Show "Showing X-Y of Z"
  classes: '',               // Additional CSS classes
  onChange: null             // Page change callback
}
```

#### Methods

- `setPage(page)` - Go to specific page
- `nextPage()` - Go to next page
- `prevPage()` - Go to previous page
- `setPageSize(size)` - Change page size
- `getTotalPages()` - Get total pages

#### Sample Code

```javascript
import FlexPagination from './components/flex-pagination.js';

// Basic pagination
const pagination = new FlexPagination(container, {
  totalItems: 234,
  itemsPerPage: 10,
  currentPage: 1,
  onChange: ({ page, pageSize }) => {
    console.log(`Page ${page}, showing ${pageSize} items`);
    loadData(page, pageSize);
  }
});

// Pagination with custom options
const customPagination = new FlexPagination(container, {
  totalItems: 1000,
  itemsPerPage: 25,
  currentPage: 1,
  maxButtons: 7,
  pageSizeOptions: [25, 50, 100, 250],
  showFirstLast: true,
  showInfo: true,
  onChange: ({ page, pageSize, totalPages }) => {
    fetchProducts(page, pageSize);
  }
});

// Programmatic control
pagination.setPage(5);
pagination.setPageSize(25);

// Keyboard navigation
pagination.on('keydown', (event) => {
  if (event.key === 'ArrowRight') pagination.nextPage();
  if (event.key === 'ArrowLeft') pagination.prevPage();
});

// Compact pagination
const compactPagination = new FlexPagination(container, {
  totalItems: 100,
  itemsPerPage: 10,
  showFirstLast: false,
  showPageSize: false,
  showInfo: false,
  maxButtons: 3
});
```

---

## Layout Components

### FlexDrawer

Slide-out panel component for quick actions and details.

#### Options

```javascript
{
  position: 'right',         // Position: left, right, top, bottom
  size: 'md',                // Size: sm, md, lg (px values)
  title: '',                 // Drawer title
  content: null,             // Content (HTML or element)
  backdrop: true,            // Show backdrop
  closeButton: true,         // Show close button
  closeOnBackdrop: true,     // Close on backdrop click
  closeOnEscape: true,       // Close on ESC key
  trapFocus: true,           // Trap focus in drawer
  footer: null,              // Footer content
  classes: '',               // Additional CSS classes
  onOpen: null,              // Open callback
  onClose: null              // Close callback
}
```

#### Methods

- `open()` - Open drawer
- `close()` - Close drawer
- `toggle()` - Toggle drawer
- `setContent(content)` - Update content

#### Sample Code

```javascript
import FlexDrawer from './components/flex-drawer.js';

// Right sidebar drawer
const detailsDrawer = new FlexDrawer(document.body, {
  position: 'right',
  size: 'md',
  title: 'Product Details',
  backdrop: true,
  closeOnEscape: true,
  footer: `
    <div class="flex justify-end gap-2">
      <button class="px-4 py-2 text-gray-700">Cancel</button>
      <button class="px-4 py-2 bg-blue-600 text-white rounded">Save</button>
    </div>
  `
});

// Set content
const productDetails = document.createElement('div');
productDetails.innerHTML = `
  <div class="space-y-4">
    <img src="product.jpg" class="w-full rounded" />
    <h3 class="text-xl font-bold">Product Name</h3>
    <p class="text-gray-600">Description...</p>
  </div>
`;
detailsDrawer.setContent(productDetails);

// Open drawer
document.getElementById('view-details-btn').addEventListener('click', () => {
  detailsDrawer.open();
});

// Left navigation drawer
const navDrawer = new FlexDrawer(document.body, {
  position: 'left',
  size: 'sm',
  title: 'Navigation',
  content: `
    <nav class="space-y-2">
      <a href="#" class="block px-4 py-2 hover:bg-gray-100 rounded">Dashboard</a>
      <a href="#" class="block px-4 py-2 hover:bg-gray-100 rounded">Products</a>
      <a href="#" class="block px-4 py-2 hover:bg-gray-100 rounded">Orders</a>
      <a href="#" class="block px-4 py-2 hover:bg-gray-100 rounded">Settings</a>
    </nav>
  `,
  backdrop: false
});

// Bottom drawer
const filtersDrawer = new FlexDrawer(document.body, {
  position: 'bottom',
  size: 'lg',
  title: 'Filters',
  content: document.getElementById('filters-form'),
  onClose: () => {
    applyFilters();
  }
});

// Listen to events
detailsDrawer.on('open', () => {
  console.log('Drawer opened');
  loadProductDetails();
});

detailsDrawer.on('close', () => {
  console.log('Drawer closed');
});
```

---

### FlexStepper

Multi-step wizard component with validation and RBAC.

#### Options

```javascript
{
  steps: [],                 // Array of step definitions
  currentStep: 0,            // Initial step index
  linear: true,              // Linear navigation (must complete in order)
  showProgress: true,        // Show progress bar
  showStepNumbers: true,     // Show step numbers
  orientation: 'horizontal', // Orientation: horizontal, vertical
  classes: '',               // Additional CSS classes
  onStepChange: null,        // Step change callback
  onComplete: null           // Completion callback
}
```

#### Step Definition

```javascript
{
  id: '',                    // Step ID
  label: '',                 // Step label
  description: '',           // Step description
  icon: null,                // Step icon
  content: null,             // Step content
  validate: null,            // Validation function (async)
  permission: null,          // RBAC permission
  optional: false,           // Optional step
  disabled: false            // Disabled step
}
```

#### Methods

- `nextStep()` - Go to next step
- `prevStep()` - Go to previous step
- `goToStep(index)` - Go to specific step
- `getCurrentStep()` - Get current step index
- `isStepValid(index)` - Check if step is valid
- `complete()` - Mark wizard as complete

#### Sample Code

```javascript
import FlexStepper from './components/flex-stepper.js';

// Basic stepper
const stepper = new FlexStepper(container, {
  steps: [
    {
      id: 'account',
      label: 'Account Information',
      content: document.getElementById('account-form'),
      validate: async () => {
        const form = document.getElementById('account-form');
        return form.checkValidity();
      }
    },
    {
      id: 'profile',
      label: 'Profile Details',
      content: document.getElementById('profile-form'),
      validate: async () => {
        // Custom validation
        const name = document.getElementById('name').value;
        return name.length >= 3;
      }
    },
    {
      id: 'preferences',
      label: 'Preferences',
      optional: true,
      content: document.getElementById('preferences-form')
    },
    {
      id: 'review',
      label: 'Review & Submit',
      content: document.getElementById('review-section')
    }
  ],
  linear: true,
  showProgress: true,
  onStepChange: ({ from, to, step }) => {
    console.log(`Step changed from ${from} to ${to}`);
    loadStepData(step);
  },
  onComplete: async (data) => {
    console.log('Wizard completed:', data);
    await submitForm(data);
  }
});

// Complex invoice wizard
const invoiceStepper = new FlexStepper(container, {
  steps: [
    {
      id: 'customer',
      label: 'Customer',
      icon: '<i class="ph-duotone ph-user"></i>',
      description: 'Select or add customer',
      content: customerForm,
      validate: async () => {
        return selectedCustomer !== null;
      }
    },
    {
      id: 'items',
      label: 'Line Items',
      icon: '<i class="ph-duotone ph-shopping-cart"></i>',
      description: 'Add products and services',
      content: itemsGrid,
      validate: async () => {
        return items.length > 0;
      }
    },
    {
      id: 'payment',
      label: 'Payment Terms',
      icon: '<i class="ph-duotone ph-credit-card"></i>',
      description: 'Set payment terms',
      content: paymentForm,
      optional: true
    },
    {
      id: 'preview',
      label: 'Preview',
      icon: '<i class="ph-duotone ph-file-text"></i>',
      description: 'Review invoice',
      content: previewSection
    }
  ],
  orientation: 'horizontal',
  linear: true,
  showProgress: true
});

// Vertical stepper
const verticalStepper = new FlexStepper(container, {
  orientation: 'vertical',
  steps: [/* ... */],
  linear: false // Allow jumping between steps
});

// Listen to events
stepper.on('step-complete', (stepId) => {
  console.log('Step completed:', stepId);
  saveProgress(stepId);
});

// Programmatic control
stepper.goToStep(2); // Jump to step 3
stepper.nextStep();  // Go to next step
stepper.prevStep();  // Go back

// Non-linear with RBAC
const adminStepper = new FlexStepper(container, {
  linear: false,
  steps: [
    { id: 'basic', label: 'Basic Info', content: basicForm },
    { id: 'advanced', label: 'Advanced', content: advancedForm, permission: 'admin:advanced:access' },
    { id: 'security', label: 'Security', content: securityForm, permission: 'admin:security:manage' }
  ]
});
```

---

## Common Patterns

### Form with Validation

```javascript
import { FlexInput, FlexSelect, FlexButton } from './components/index.js';

// Create form container
const formContainer = document.getElementById('user-form');

// Add fields
const nameInput = new FlexInput(formContainer, {
  label: 'Full Name',
  required: true,
  minLength: 3,
  placeholder: 'Enter your name'
});

const emailInput = new FlexInput(formContainer, {
  label: 'Email',
  type: 'email',
  required: true,
  placeholder: 'your@email.com'
});

const countrySelect = new FlexSelect(formContainer, {
  label: 'Country',
  required: true,
  searchable: true,
  options: countries
});

// Submit button
const submitBtn = new FlexButton(formContainer, {
  text: 'Submit',
  type: 'submit',
  variant: 'primary',
  fullWidth: true,
  onClick: async () => {
    // Validate all fields
    const isValid = [nameInput, emailInput, countrySelect]
      .every(field => field.validate());

    if (!isValid) {
      return;
    }

    // Submit
    submitBtn.setLoading(true);
    try {
      const data = {
        name: nameInput.getValue(),
        email: emailInput.getValue(),
        country: countrySelect.getValue()
      };
      await submitForm(data);
      showSuccessMessage();
    } catch (error) {
      emailInput.setError(error.message);
    } finally {
      submitBtn.setLoading(false);
    }
  }
});
```

### CRUD Table

```javascript
import { FlexTable, FlexModal, FlexButton } from './components/index.js';

// Create table
const table = new FlexTable(container, {
  columns: [
    { field: 'id', title: 'ID', width: '80px' },
    { field: 'name', title: 'Name', sortable: true },
    { field: 'email', title: 'Email', sortable: true },
    { field: 'status', title: 'Status' }
  ],
  data: users,
  selectable: true,
  rowActions: [
    {
      label: 'Edit',
      icon: '<i class="ph-duotone ph-pencil"></i>',
      permission: 'users:edit',
      onClick: (row) => showEditModal(row)
    },
    {
      label: 'Delete',
      icon: '<i class="ph-duotone ph-trash"></i>',
      permission: 'users:delete',
      onClick: async (row) => {
        if (confirm('Delete user?')) {
          await deleteUser(row.id);
          table.refresh();
        }
      }
    }
  ],
  bulkActions: [
    {
      label: 'Delete Selected',
      variant: 'danger',
      onClick: async (rows) => {
        await deleteUsers(rows.map(r => r.id));
        table.refresh();
      }
    }
  ]
});

// Edit modal
function showEditModal(user) {
  const modalContainer = document.createElement('div');
  document.body.appendChild(modalContainer);

  const formContent = document.createElement('div');
  // Add form fields...

  const modal = new FlexModal(modalContainer, {
    title: 'Edit User',
    content: formContent,
    size: 'md',
    actions: [
      { label: 'Cancel', variant: 'secondary', onClick: () => modal.close() },
      {
        label: 'Save',
        variant: 'primary',
        onClick: async () => {
          modal.setLoading(true);
          await updateUser(user.id, formData);
          modal.close();
          table.refresh();
        }
      }
    ]
  });

  modal.open();
}
```

### Notification System

```javascript
import FlexAlert from './components/flex-alert.js';

class NotificationManager {
  constructor() {
    this.container = document.createElement('div');
    this.container.className = 'fixed top-4 right-4 z-50 space-y-2';
    document.body.appendChild(this.container);
  }

  show(message, variant = 'info', duration = 5000) {
    const alertContainer = document.createElement('div');
    this.container.appendChild(alertContainer);

    const alert = new FlexAlert(alertContainer, {
      message,
      variant,
      dismissible: true,
      autoDismiss: true,
      dismissDelay: duration,
      onDismiss: () => {
        alertContainer.remove();
      }
    });
  }

  success(message) { this.show(message, 'success'); }
  error(message) { this.show(message, 'danger'); }
  warning(message) { this.show(message, 'warning'); }
  info(message) { this.show(message, 'info'); }
}

// Usage
const notify = new NotificationManager();
notify.success('Data saved successfully!');
notify.error('Failed to load data');
notify.warning('Session expires in 5 minutes');
```

---

## RBAC Integration

All components support RBAC through the `permission` option:

```javascript
// Component will only render if user has permission
const adminButton = new FlexButton(container, {
  text: 'Admin Panel',
  permission: 'admin:panel:access',
  onClick: () => navigateToAdmin()
});

// Table with RBAC row actions
const table = new FlexTable(container, {
  columns: [...],
  rowActions: [
    {
      label: 'Edit',
      permission: 'records:edit',
      onClick: (row) => edit(row)
    },
    {
      label: 'Delete',
      permission: 'records:delete',
      onClick: (row) => deleteRecord(row)
    }
  ]
});

// Tabs with permissions
const tabs = new FlexTabs(container, {
  tabs: [
    { id: 'view', label: 'View', content: viewContent },
    { id: 'edit', label: 'Edit', content: editContent, permission: 'edit:access' },
    { id: 'admin', label: 'Admin', content: adminContent, permission: 'admin:access' }
  ]
});

// Stepper with restricted steps
const stepper = new FlexStepper(container, {
  steps: [
    { id: 'basic', label: 'Basic', content: basicForm },
    { id: 'advanced', label: 'Advanced', content: advForm, permission: 'advanced:access' }
  ]
});
```

---

## Event System

All components inherit from `BaseComponent` and support events:

```javascript
// Listen to events
component.on('eventName', (data) => {
  console.log('Event fired:', data);
});

// Remove listener
component.off('eventName', handler);

// Emit custom events
component.emit('customEvent', { data: 'value' });

// Common events
input.on('change', (value) => console.log('Changed:', value));
modal.on('close', () => console.log('Modal closed'));
table.on('sort', ({ field, direction }) => console.log('Sorted'));
stepper.on('step-complete', (stepId) => console.log('Step done'));
```

---

## Lifecycle Methods

```javascript
// Initialize component
const component = new FlexComponent(container, options);

// Destroy component (cleanup)
component.destroy();

// Check if destroyed
if (component.isDestroyed) {
  console.log('Component destroyed');
}
```

---

## Styling and Customization

All components use Tailwind CSS and support custom classes:

```javascript
const button = new FlexButton(container, {
  text: 'Custom Button',
  classes: 'shadow-lg hover:shadow-xl custom-animation'
});

const modal = new FlexModal(container, {
  title: 'Custom Modal',
  classes: 'custom-modal-styles',
  // Modal will have both default and custom classes
});
```

---

## Best Practices

1. **Always validate** - Use built-in validation before submitting forms
2. **Handle errors** - Use try/catch and show error messages
3. **Clean up** - Call `destroy()` when removing components
4. **Use RBAC** - Leverage permission checks for security
5. **Listen to events** - React to user interactions
6. **Loading states** - Show feedback during async operations
7. **Accessibility** - Components have ARIA labels and keyboard support
8. **Mobile-first** - All components are responsive

---

## Browser Support

- Chrome/Edge: Latest 2 versions
- Firefox: Latest 2 versions
- Safari: Latest 2 versions
- Mobile browsers: iOS Safari 12+, Chrome Android latest

---

## Support

For issues and questions:
- GitHub Issues: [Report bugs](https://github.com/yourrepo/issues)
- Documentation: See `/frontend/docs/`
- Examples: See `/frontend/examples/`
