# Flex Component Library

## Overview

The Flex Component Library is a **zero-dependency, vanilla JavaScript** UI framework built for App-Buildify. All components extend a common `BaseComponent` class, follow an event-driven communication model, and support responsive breakpoints out of the box.

---

## BaseComponent

All components extend `BaseComponent` (`core/base-component.js`):

```javascript
class BaseComponent extends HTMLElement {
  // Lifecycle
  connectedCallback()    // Component mounted to DOM
  disconnectedCallback() // Component removed from DOM
  attributeChangedCallback(name, old, newVal) // Attribute changed

  // Events
  emit(eventName, detail)         // Dispatch custom event
  on(eventName, handler)          // Subscribe to event

  // Rendering
  render()                        // Subclass implements this

  // Utilities
  $(selector)                     // querySelector within component
  $$(selector)                    // querySelectorAll within component
}
```

---

## FlexResponsive

Singleton for breakpoint detection (`core/flex-responsive.js`):

```javascript
const responsive = FlexResponsive.getInstance()

responsive.breakpoint       // 'xs' | 'sm' | 'md' | 'lg' | 'xl'
responsive.isMobile()       // true if xs or sm
responsive.isTablet()       // true if md
responsive.isDesktop()      // true if lg or xl

responsive.on('breakpoint-change', ({ detail }) => {
  console.log(detail.breakpoint)
})
```

| Breakpoint | Min Width |
|-----------|-----------|
| `xs` | 0px |
| `sm` | 640px |
| `md` | 768px |
| `lg` | 1024px |
| `xl` | 1280px |

---

## Layout Components

### FlexStack

Vertical or horizontal linear layout with gap control.

**File**: `layout/flex-stack.js`

```html
<flex-stack direction="vertical" gap="4" align="start" justify="between">
  <div>Item 1</div>
  <div>Item 2</div>
</flex-stack>
```

| Attribute | Values | Default | Description |
|-----------|--------|---------|-------------|
| `direction` | `vertical` \| `horizontal` | `vertical` | Stack direction |
| `gap` | Tailwind gap unit | `4` | Space between items |
| `align` | `start` \| `center` \| `end` \| `stretch` | `stretch` | Cross-axis alignment |
| `justify` | `start` \| `center` \| `end` \| `between` \| `around` | `start` | Main-axis alignment |

---

### FlexGrid

Responsive column grid.

**File**: `layout/flex-grid.js`

```html
<flex-grid cols="3" cols-md="2" cols-sm="1" gap="6">
  <div>Card 1</div>
  <div>Card 2</div>
  <div>Card 3</div>
</flex-grid>
```

| Attribute | Description |
|-----------|-------------|
| `cols` | Default column count |
| `cols-xl` / `cols-lg` / `cols-md` / `cols-sm` | Responsive overrides |
| `gap` | Grid gap (Tailwind unit) |

---

### FlexContainer

Centered max-width wrapper.

```html
<flex-container max-width="7xl" padding="6">
  <p>Constrained content</p>
</flex-container>
```

---

### FlexSection

Full-width page section with background support.

```html
<flex-section bg="gray-50" padding="8">
  <h2>Section Title</h2>
</flex-section>
```

---

### FlexSidebar

Collapsible navigation sidebar.

```html
<flex-sidebar width="64" collapsed="false" position="left">
  <nav>...</nav>
</flex-sidebar>
```

| Attribute | Description |
|-----------|-------------|
| `width` | Sidebar width (Tailwind unit) |
| `collapsed` | `true` / `false` |
| `position` | `left` \| `right` |

**Events**: `sidebar-toggle`, `sidebar-collapsed`, `sidebar-expanded`

---

### FlexCluster

Horizontal wrapping group (inline-flex with wrap).

```html
<flex-cluster gap="2" align="center">
  <flex-badge>Tag 1</flex-badge>
  <flex-badge>Tag 2</flex-badge>
</flex-cluster>
```

---

### FlexToolbar

Fixed or sticky toolbar for page headers/footers.

```html
<flex-toolbar position="top" sticky="true">
  <span>Title</span>
  <flex-cluster>
    <button>Action</button>
  </flex-cluster>
</flex-toolbar>
```

---

### FlexMasonry

Pinterest-style masonry grid.

```html
<flex-masonry columns="3" gap="4">
  <div>Item 1</div>
  <div>Item 2</div>
</flex-masonry>
```

---

### FlexSplitPane

Resizable split panel layout.

```html
<flex-split-pane direction="horizontal" initial-split="30">
  <div slot="start">Left panel</div>
  <div slot="end">Right panel</div>
</flex-split-pane>
```

| Attribute | Description |
|-----------|-------------|
| `direction` | `horizontal` \| `vertical` |
| `initial-split` | Percentage for the start pane |
| `min-size` | Minimum size in percent |

---

## UI Components

### FlexCard

Card container with optional header, body, and footer slots.

**File**: `components/flex-card.js`

```html
<flex-card shadow="md" rounded="lg" padding="6">
  <div slot="header">Card Title</div>
  <p>Card content goes here.</p>
  <div slot="footer">
    <button>Action</button>
  </div>
</flex-card>
```

---

### FlexModal

Modal dialog with overlay.

**File**: `components/flex-modal.js`

```javascript
const modal = document.querySelector('flex-modal')
modal.open()
modal.close()
modal.on('modal-close', () => { ... })
```

```html
<flex-modal size="md" closable="true">
  <div slot="title">Confirm Delete</div>
  <p>Are you sure?</p>
  <div slot="footer">
    <button id="confirm">Yes, Delete</button>
  </div>
</flex-modal>
```

| Attribute | Values | Description |
|-----------|--------|-------------|
| `size` | `sm` \| `md` \| `lg` \| `xl` \| `full` | Modal width |
| `closable` | `true` \| `false` | Show X close button |

**Events**: `modal-open`, `modal-close`, `modal-confirm`

---

### FlexTabs

Tab navigation container.

**File**: `components/flex-tabs.js`

```html
<flex-tabs active="tab1" variant="underline">
  <div slot="tab-tab1" data-label="Overview">
    <p>Overview content</p>
  </div>
  <div slot="tab-tab2" data-label="Settings">
    <p>Settings content</p>
  </div>
</flex-tabs>
```

| Attribute | Values | Description |
|-----------|--------|-------------|
| `active` | Tab key | Initially active tab |
| `variant` | `underline` \| `pills` \| `bordered` | Visual style |

**Events**: `tab-change` — `{ detail: { tab: 'tab2' } }`

---

### FlexDataGrid

Feature-rich data table with sorting, filtering, and pagination.

**File**: `components/flex-datagrid.js`

```javascript
const grid = document.querySelector('flex-datagrid')
grid.setColumns([
  { key: 'name', label: 'Name', sortable: true },
  { key: 'email', label: 'Email', sortable: true },
  { key: 'role', label: 'Role', filterable: true }
])
grid.setData(usersArray)
grid.on('row-click', ({ detail }) => {
  console.log(detail.row)
})
```

**Features**:
- Column sorting (client-side and server-side)
- Per-column filtering
- Pagination with configurable page size
- Row selection (single/multi)
- Custom cell renderers
- Export to CSV

---

### FlexBadge

Label badge with color variants.

**File**: `components/flex-badge.js`

```html
<flex-badge variant="success">Active</flex-badge>
<flex-badge variant="danger">Inactive</flex-badge>
<flex-badge variant="warning">Pending</flex-badge>
<flex-badge variant="info">Draft</flex-badge>
```

| Variant | Color |
|---------|-------|
| `default` | Gray |
| `primary` | Blue |
| `success` | Green |
| `danger` | Red |
| `warning` | Yellow |
| `info` | Cyan |

---

### FlexStepper

Step progress indicator for multi-step flows.

**File**: `components/flex-stepper.js`

```javascript
const stepper = document.querySelector('flex-stepper')
stepper.setSteps([
  { id: 'info', label: 'Basic Info' },
  { id: 'details', label: 'Details' },
  { id: 'review', label: 'Review' }
])
stepper.goTo('details')
stepper.on('step-change', ({ detail }) => {
  console.log(detail.step)
})
```

---

## Adding a New Component

1. Create `frontend/assets/js/components/flex-my-widget.js`
2. Extend `BaseComponent`:
   ```javascript
   import { BaseComponent } from '../core/base-component.js'

   class FlexMyWidget extends BaseComponent {
     static get observedAttributes() {
       return ['title', 'variant']
     }

     render() {
       this.innerHTML = `
         <div class="flex-widget">
           <h3>${this.getAttribute('title') || ''}</h3>
           <slot></slot>
         </div>
       `
     }
   }

   customElements.define('flex-my-widget', FlexMyWidget)
   export { FlexMyWidget }
   ```
3. Import in your page or component file
4. Use in HTML: `<flex-my-widget title="Hello"><p>Content</p></flex-my-widget>`

---

## Accessibility

All Flex components target **WCAG 2.1 AA**:

- Semantic HTML elements and ARIA roles
- Keyboard navigation (Tab, Enter, Escape, Arrow keys)
- Focus management in modals (focus trap)
- Visible focus indicators
- Screen reader-friendly labels
- Color contrast ≥ 4.5:1

---

## Related Documents

- [Frontend Architecture](./README.md)
- [Internationalization](./I18N.md)
