# Flex Component Library

## Overview

The Flex Component Library is a **zero-dependency, vanilla JavaScript** UI framework built for App-Buildify. All components extend a common `BaseComponent` class, follow an event-driven communication model, and support responsive breakpoints out of the box.

**Current version**: 1.0.0
**Bundle size**: Core ~12KB gzipped | Full library ~38KB gzipped
**Browser support**: Chrome/Edge, Firefox, Safari (latest 2 versions)

---

## Component Index

| Component | File | Category | Status |
|-----------|------|----------|--------|
| [FlexStack](#flexstack) | `layout/flex-stack.js` | Layout | ✅ |
| [FlexGrid](#flexgrid) | `layout/flex-grid.js` | Layout | ✅ |
| [FlexContainer](#flexcontainer) | `layout/flex-container.js` | Layout | ✅ |
| [FlexSection](#flexsection) | `layout/flex-section.js` | Layout | ✅ |
| [FlexSidebar](#flexsidebar) | `layout/flex-sidebar.js` | Layout | ✅ |
| [FlexCluster](#flexcluster) | `layout/flex-cluster.js` | Layout | ✅ |
| [FlexToolbar](#flextoolbar) | `layout/flex-toolbar.js` | Layout | ✅ |
| [FlexMasonry](#flexmasonry) | `layout/flex-masonry.js` | Layout | ✅ |
| [FlexSplitPane](#flexsplitpane) | `layout/flex-split-pane.js` | Layout | ✅ |
| [FlexCard](#flexcard) | `components/flex-card.js` | UI | ✅ |
| [FlexModal](#flexmodal) | `components/flex-modal.js` | UI | ✅ |
| [FlexTabs](#flextabs) | `components/flex-tabs.js` | UI | ✅ |
| [FlexDataGrid](#flexdatagrid) | `components/flex-datagrid.js` | UI | ✅ |
| [FlexTable](#flextable) | `components/flex-table.js` | UI | ✅ |
| [FlexBadge](#flexbadge) | `components/flex-badge.js` | UI | ✅ |
| [FlexStepper](#flexstepper) | `components/flex-stepper.js` | UI | ✅ |
| [FlexAlert](#flexalert) | `components/flex-alert.js` | UI | ✅ |
| [FlexButton](#flexbutton) | `components/flex-button.js` | UI | ✅ |
| [FlexDrawer](#flexdrawer) | `components/flex-drawer.js` | UI | ✅ |
| [FlexDropdown](#flexdropdown) | `components/flex-dropdown.js` | UI | ✅ |
| [FlexSpinner](#flexspinner) | `components/flex-spinner.js` | UI | ✅ |
| [FlexAccordion](#flexaccordion) | `components/flex-accordion.js` | UI | ✅ |
| [FlexBreadcrumb](#flexbreadcrumb) | `components/flex-breadcrumb.js` | UI | ✅ |
| [FlexTooltip](#flextooltip) | `components/flex-tooltip.js` | UI | ✅ |
| [FlexPagination](#flexpagination) | `components/flex-pagination.js` | UI | ✅ |
| [FlexInput](#flexinput) | `components/flex-input.js` | Form | ✅ |
| [FlexSelect](#flexselect) | `components/flex-select.js` | Form | ✅ |
| [FlexCheckbox](#flexcheckbox) | `components/flex-checkbox.js` | Form | ✅ |
| [FlexRadio](#flexradio) | `components/flex-radio.js` | Form | ✅ |
| [FlexTextarea](#flextextarea) | `components/flex-textarea.js` | Form | ✅ |
| FlexDatepicker | — | Form | ❌ Planned |
| FlexFileUpload | — | Form | ❌ Planned |
| FlexForm | — | Form | ❌ Planned |
| FlexNotification | — | UI | ❌ Planned |
| FlexProgress | — | UI | ❌ Planned |

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
responsive.isMobile()
responsive.isTablet()
responsive.isDesktop()
responsive.on('breakpoint-change', ({ detail }) => { ... })
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

```html
<flex-stack direction="vertical" gap="4" align="start" justify="between">
  <div>Item 1</div>
  <div>Item 2</div>
</flex-stack>
```

| Attribute | Values | Default |
|-----------|--------|---------|
| `direction` | `vertical` \| `horizontal` | `vertical` |
| `gap` | Tailwind unit | `4` |
| `align` | `start` \| `center` \| `end` \| `stretch` | `stretch` |
| `justify` | `start` \| `center` \| `end` \| `between` \| `around` | `start` |

---

### FlexGrid

Responsive column grid.

```html
<flex-grid cols="3" cols-md="2" cols-sm="1" gap="6">
  <div>Card 1</div>
  <div>Card 2</div>
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
  <p>Content</p>
</flex-container>
```

---

### FlexSection

Full-width page section with background.

```html
<flex-section bg="gray-50" padding="8">
  <h2>Section</h2>
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

**Events**: `sidebar-toggle`, `sidebar-collapsed`, `sidebar-expanded`

---

### FlexCluster

Horizontal wrapping group (inline-flex wrap).

```html
<flex-cluster gap="2" align="center" justify="start" wrap="true">
  <flex-badge>Tag 1</flex-badge>
  <flex-badge>Tag 2</flex-badge>
</flex-cluster>
```

**Events**: `item:add`, `item:remove`, `item:update`

---

### FlexToolbar

Fixed or sticky toolbar for page headers/footers.

```html
<flex-toolbar position="top" sticky="true" theme="default">
  <span>Title</span>
</flex-toolbar>
```

| Attribute | Values | Description |
|-----------|--------|-------------|
| `position` | `top` \| `bottom` | Toolbar placement |
| `sticky` | `true` \| `false` | Sticky positioning |
| `theme` | `default` \| `dark` \| `transparent` | Visual theme |
| `elevation` | `none` \| `sm` \| `md` \| `lg` | Shadow level |

**Events**: action click events by action ID

---

### FlexMasonry

Pinterest-style masonry grid with column balancing.

```html
<flex-masonry columns="3" gap="4" animated="true" lazy-load="true">
  <div>Item 1</div>
  <div>Item 2</div>
</flex-masonry>
```

**Algorithm**: Greedy column balancing — each new item is placed in the shortest column.

**Events**: `item:add`, `item:remove`, `reflow`

---

### FlexSplitPane

Resizable split panel layout with persistence.

```html
<flex-split-pane direction="horizontal" initial-split="30"
                 persist="true" persist-key="ide-layout">
  <div slot="start">Left panel</div>
  <div slot="end">Right panel</div>
</flex-split-pane>
```

| Attribute | Description |
|-----------|-------------|
| `direction` | `horizontal` \| `vertical` |
| `initial-split` | Start pane percentage |
| `min-size` | Minimum pane size % |
| `persist` | Save to localStorage |
| `persist-key` | localStorage key |

**Events**: `resize`, `pane:add`, `pane:remove`

---

## UI Components

### FlexCard

Card container with named slots.

```html
<flex-card shadow="md" rounded="lg" padding="6">
  <div slot="header">Card Title</div>
  <p>Card content</p>
  <div slot="footer"><button>Action</button></div>
</flex-card>
```

---

### FlexModal

Modal dialog with overlay and focus trap.

```javascript
const modal = document.querySelector('flex-modal')
modal.open()
modal.close()
modal.on('modal-close', () => { ... })
```

| Attribute | Values | Description |
|-----------|--------|-------------|
| `size` | `sm` \| `md` \| `lg` \| `xl` \| `full` | Modal width |
| `closable` | `true` \| `false` | Show X close button |

**Events**: `modal-open`, `modal-close`, `modal-confirm`

---

### FlexTabs

Tab navigation container.

```html
<flex-tabs active="tab1" variant="underline">
  <div slot="tab-tab1" data-label="Overview">Overview content</div>
  <div slot="tab-tab2" data-label="Settings">Settings content</div>
</flex-tabs>
```

| Attribute | Values | Description |
|-----------|--------|-------------|
| `variant` | `underline` \| `pills` \| `bordered` | Visual style |

**Events**: `tab-change` — `{ detail: { tab: 'tab2' } }`

---

### FlexDataGrid

Feature-rich data table with sorting, filtering, pagination, and row selection.

```javascript
const grid = document.querySelector('flex-datagrid')
grid.setColumns([
  { key: 'name', label: 'Name', sortable: true },
  { key: 'email', label: 'Email', sortable: true }
])
grid.setData(rows)
grid.on('row-click', ({ detail }) => console.log(detail.row))
```

**Features**: column sorting, per-column filtering, pagination, multi-row selection, CSV export, custom cell renderers

---

### FlexTable

Simpler table component for static/small datasets.

```html
<flex-table striped="true" bordered="true" hover="true">
  <table>...</table>
</flex-table>
```

---

### FlexAlert

Inline alert/notification banner.

```html
<flex-alert variant="success" dismissible="true" icon="true">
  Operation completed successfully.
</flex-alert>
```

| Attribute | Values | Description |
|-----------|--------|-------------|
| `variant` | `info` \| `success` \| `warning` \| `danger` | Alert type |
| `dismissible` | `true` \| `false` | Show dismiss button |
| `icon` | `true` \| `false` | Show type icon |

**Events**: `alert-dismiss`

---

### FlexButton

Styled button component.

```html
<flex-button variant="primary" size="md" loading="false" disabled="false">
  Save Changes
</flex-button>
```

| Attribute | Values | Description |
|-----------|--------|-------------|
| `variant` | `primary` \| `secondary` \| `danger` \| `ghost` \| `link` | Visual style |
| `size` | `xs` \| `sm` \| `md` \| `lg` | Button size |
| `loading` | `true` \| `false` | Show spinner |
| `disabled` | `true` \| `false` | Disabled state |

---

### FlexDrawer

Slide-in drawer panel from any edge.

```html
<flex-drawer position="right" size="md" overlay="true">
  <div slot="header">Drawer Title</div>
  <p>Drawer content</p>
</flex-drawer>
```

| Attribute | Values | Description |
|-----------|--------|-------------|
| `position` | `left` \| `right` \| `top` \| `bottom` | Slide direction |
| `size` | `sm` \| `md` \| `lg` \| `full` | Panel width/height |
| `overlay` | `true` \| `false` | Background overlay |

**Events**: `drawer-open`, `drawer-close`

---

### FlexDropdown

Dropdown menu component.

```html
<flex-dropdown trigger="click" placement="bottom-start">
  <button slot="trigger">Actions</button>
  <div slot="menu">
    <a href="#">Edit</a>
    <a href="#">Delete</a>
  </div>
</flex-dropdown>
```

| Attribute | Values | Description |
|-----------|--------|-------------|
| `trigger` | `click` \| `hover` | Open trigger |
| `placement` | `bottom-start` \| `bottom-end` \| `top-start` etc. | Menu position |

---

### FlexSpinner

Loading spinner indicator.

```html
<flex-spinner size="md" variant="primary"></flex-spinner>
```

| Attribute | Values |
|-----------|--------|
| `size` | `xs` \| `sm` \| `md` \| `lg` |
| `variant` | `primary` \| `white` \| `gray` |

---

### FlexBadge

Label badge with color variants.

```html
<flex-badge variant="success">Active</flex-badge>
<flex-badge variant="danger">Inactive</flex-badge>
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

```javascript
const stepper = document.querySelector('flex-stepper')
stepper.setSteps([
  { id: 'info', label: 'Basic Info' },
  { id: 'details', label: 'Details' },
  { id: 'review', label: 'Review' }
])
stepper.goTo('details')
stepper.on('step-change', ({ detail }) => console.log(detail.step))
```

---

### FlexAccordion

Collapsible accordion sections.

```html
<flex-accordion multiple="false" animated="true">
  <div slot="panel-1" data-title="Section 1">Content 1</div>
  <div slot="panel-2" data-title="Section 2">Content 2</div>
</flex-accordion>
```

| Attribute | Description |
|-----------|-------------|
| `multiple` | Allow multiple open panels at once |
| `animated` | Animate open/close |

**Events**: `panel-open`, `panel-close`

---

### FlexBreadcrumb

Navigation breadcrumb trail.

```html
<flex-breadcrumb separator="/">
  <a href="#/">Home</a>
  <a href="#/users">Users</a>
  <span>Edit</span>
</flex-breadcrumb>
```

---

### FlexTooltip

Hover tooltip with configurable placement.

```html
<flex-tooltip content="Save your changes" placement="top">
  <button>Save</button>
</flex-tooltip>
```

| Attribute | Values |
|-----------|--------|
| `placement` | `top` \| `bottom` \| `left` \| `right` |
| `trigger` | `hover` \| `click` \| `focus` |

---

### FlexPagination

Pagination control component.

```javascript
const pager = document.querySelector('flex-pagination')
pager.setConfig({ total: 100, page: 1, pageSize: 20 })
pager.on('page-change', ({ detail }) => loadPage(detail.page))
```

---

## Form Components

### FlexInput

Text input with validation support.

```html
<flex-input name="email" type="email" label="Email Address"
            placeholder="user@example.com" required="true">
</flex-input>
```

| Attribute | Description |
|-----------|-------------|
| `type` | `text` \| `email` \| `password` \| `number` \| `tel` \| `url` |
| `label` | Field label |
| `placeholder` | Placeholder text |
| `required` | Mark as required |
| `error` | Error message to display |
| `hint` | Helper text below field |

---

### FlexSelect

Dropdown select with search and multi-select support.

```html
<flex-select name="role" label="Role" searchable="true" multiple="false">
  <option value="admin">Admin</option>
  <option value="user">User</option>
</flex-select>
```

---

### FlexCheckbox

Checkbox with label.

```html
<flex-checkbox name="active" label="Active" checked="true"></flex-checkbox>
```

---

### FlexRadio

Radio button group.

```html
<flex-radio name="type" label="Account Type" value="personal">
  <option value="personal">Personal</option>
  <option value="business">Business</option>
</flex-radio>
```

---

### FlexTextarea

Multi-line text input.

```html
<flex-textarea name="description" label="Description"
               rows="4" max-length="500" show-count="true">
</flex-textarea>
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
3. Register in `components/index.js`
4. Use in HTML: `<flex-my-widget title="Hello"><p>Content</p></flex-my-widget>`

---

## Accessibility

All Flex components target **WCAG 2.1 AA**:

- Semantic HTML and ARIA roles
- Full keyboard navigation (Tab, Enter, Escape, Arrow keys)
- Focus management in modals and drawers (focus trap)
- Visible focus indicators
- Screen reader-friendly labels (`aria-label`, `aria-describedby`)
- Color contrast ≥ 4.5:1

---

## Related Documents

- [Frontend Architecture](./README.md)
- [Internationalization](./I18N.md)
- [Roadmap](../platform/ROADMAP.md)
