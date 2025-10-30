# Migration Guide

This guide helps you migrate from other UI libraries and frameworks to the Flex Component Library.

## Table of Contents

- [From Bootstrap](#from-bootstrap)
- [From Tailwind UI](#from-tailwind-ui)
- [From Material-UI (MUI)](#from-material-ui-mui)
- [From Ant Design](#from-ant-design)
- [From Foundation](#from-foundation)
- [From jQuery UI](#from-jquery-ui)
- [General Migration Strategy](#general-migration-strategy)
- [Common Patterns](#common-patterns)

## From Bootstrap

### Grid System

**Bootstrap:**
```html
<div class="container">
    <div class="row">
        <div class="col-md-4">Column 1</div>
        <div class="col-md-4">Column 2</div>
        <div class="col-md-4">Column 3</div>
    </div>
</div>
```

**Flex:**
```javascript
import { FlexGrid } from './layout/flex-grid.js';
import FlexContainer from './layout/flex-container.js';

// Container
const container = new FlexContainer('#app', {
    preset: 'standard'
});

// Grid
const grid = new FlexGrid('#grid', {
    columns: { xs: 1, md: 3 },
    gap: 4,
    items: [
        { id: '1', content: '<div>Column 1</div>' },
        { id: '2', content: '<div>Column 2</div>' },
        { id: '3', content: '<div>Column 3</div>' }
    ]
});
```

### Cards

**Bootstrap:**
```html
<div class="card">
    <div class="card-header">
        Card Title
    </div>
    <div class="card-body">
        <p class="card-text">Card content</p>
    </div>
    <div class="card-footer">
        <button class="btn btn-primary">Action</button>
    </div>
</div>
```

**Flex:**
```javascript
import { FlexCard } from './components/flex-card.js';

const card = new FlexCard('#card', {
    title: 'Card Title',
    content: '<p>Card content</p>',
    footerActions: [
        {
            label: 'Action',
            variant: 'primary',
            onClick: () => console.log('Clicked')
        }
    ]
});
```

### Modals

**Bootstrap:**
```html
<!-- HTML -->
<div class="modal fade" id="myModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Modal title</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <p>Modal content</p>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                <button type="button" class="btn btn-primary">Save</button>
            </div>
        </div>
    </div>
</div>

<!-- JavaScript -->
<script>
var modal = new bootstrap.Modal(document.getElementById('myModal'));
modal.show();
</script>
```

**Flex:**
```javascript
import { FlexModal } from './components/flex-modal.js';

const modal = new FlexModal({
    title: 'Modal title',
    content: '<p>Modal content</p>',
    footerActions: [
        {
            label: 'Close',
            variant: 'ghost',
            onClick: (e, modal) => modal.hide()
        },
        {
            label: 'Save',
            variant: 'primary',
            onClick: (e, modal) => {
                // Save logic
                modal.hide();
            }
        }
    ]
});

modal.show();
```

### Navbars

**Bootstrap:**
```html
<nav class="navbar navbar-expand-lg navbar-light bg-light">
    <div class="container-fluid">
        <a class="navbar-brand" href="#">Brand</a>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse">
            <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse">
            <ul class="navbar-nav ms-auto">
                <li class="nav-item"><a class="nav-link" href="#">Home</a></li>
                <li class="nav-item"><a class="nav-link" href="#">About</a></li>
            </ul>
        </div>
    </div>
</nav>
```

**Flex:**
```javascript
import FlexToolbar from './layout/flex-toolbar.js';

const navbar = new FlexToolbar('#navbar', {
    position: 'top',
    sticky: true,
    theme: 'light',
    elevation: 1,
    actions: {
        left: [
            {
                id: 'brand',
                content: '<a href="#" class="font-bold text-xl">Brand</a>'
            }
        ],
        right: [
            {
                id: 'home',
                content: '<a href="#">Home</a>'
            },
            {
                id: 'about',
                content: '<a href="#">About</a>'
            }
        ]
    }
});
```

## From Tailwind UI

### Stack Component

**Tailwind UI:**
```html
<div class="space-y-4">
    <div class="p-4 bg-white rounded-lg shadow">Item 1</div>
    <div class="p-4 bg-white rounded-lg shadow">Item 2</div>
    <div class="p-4 bg-white rounded-lg shadow">Item 3</div>
</div>
```

**Flex:**
```javascript
import { FlexStack } from './layout/flex-stack.js';

const stack = new FlexStack('#stack', {
    direction: 'vertical',
    gap: 4,
    items: [
        { content: '<div class="p-4 bg-white rounded-lg shadow">Item 1</div>' },
        { content: '<div class="p-4 bg-white rounded-lg shadow">Item 2</div>' },
        { content: '<div class="p-4 bg-white rounded-lg shadow">Item 3</div>' }
    ]
});
```

### Container

**Tailwind UI:**
```html
<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <!-- Content -->
</div>
```

**Flex:**
```javascript
import FlexContainer from './layout/flex-container.js';

const container = new FlexContainer('#app', {
    preset: 'standard',  // max-w-7xl equivalent
    align: 'center',
    padding: { xs: 4, sm: 6, lg: 8 }
});
```

## From Material-UI (MUI)

### Grid

**MUI:**
```jsx
import Grid from '@mui/material/Grid';

<Grid container spacing={2}>
    <Grid item xs={12} md={4}>
        <div>Item 1</div>
    </Grid>
    <Grid item xs={12} md={4}>
        <div>Item 2</div>
    </Grid>
    <Grid item xs={12} md={4}>
        <div>Item 3</div>
    </Grid>
</Grid>
```

**Flex:**
```javascript
import { FlexGrid } from './layout/flex-grid.js';

const grid = new FlexGrid('#grid', {
    columns: { xs: 1, md: 3 },
    gap: 2,  // MUI spacing(2) equivalent
    items: [
        { id: '1', content: '<div>Item 1</div>' },
        { id: '2', content: '<div>Item 2</div>' },
        { id: '3', content: '<div>Item 3</div>' }
    ]
});
```

### Card

**MUI:**
```jsx
import Card from '@mui/material/Card';
import CardHeader from '@mui/material/CardHeader';
import CardContent from '@mui/material/CardContent';
import CardActions from '@mui/material/CardActions';

<Card>
    <CardHeader title="Card Title" subheader="Subtitle" />
    <CardContent>
        <p>Content</p>
    </CardContent>
    <CardActions>
        <Button>Action</Button>
    </CardActions>
</Card>
```

**Flex:**
```javascript
import { FlexCard } from './components/flex-card.js';

const card = new FlexCard('#card', {
    title: 'Card Title',
    subtitle: 'Subtitle',
    content: '<p>Content</p>',
    footerActions: [
        {
            label: 'Action',
            onClick: () => console.log('Clicked')
        }
    ]
});
```

### Drawer

**MUI:**
```jsx
import Drawer from '@mui/material/Drawer';

<Drawer
    anchor="left"
    open={open}
    onClose={handleClose}
    variant="temporary"
>
    <div>Drawer content</div>
</Drawer>
```

**Flex:**
```javascript
import FlexSidebar from './layout/flex-sidebar.js';

const drawer = new FlexSidebar('#app', {
    position: 'left',
    mobileMode: 'overlay',
    desktopMode: 'overlay',
    defaultOpen: false,
    content: {
        sidebar: '<div>Drawer content</div>',
        main: '<div>Main content</div>'
    }
});

// Open/close
drawer.open();
drawer.close();
```

### Tabs

**MUI:**
```jsx
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';

<Tabs value={value} onChange={handleChange}>
    <Tab label="Tab 1" />
    <Tab label="Tab 2" />
    <Tab label="Tab 3" />
</Tabs>
<TabPanel value={value} index={0}>
    Content 1
</TabPanel>
<TabPanel value={value} index={1}>
    Content 2
</TabPanel>
<TabPanel value={value} index={2}>
    Content 3
</TabPanel>
```

**Flex:**
```javascript
import { FlexTabs } from './components/flex-tabs.js';

const tabs = new FlexTabs('#tabs', {
    variant: 'underline',
    tabs: [
        { id: 'tab1', label: 'Tab 1', content: '<div>Content 1</div>' },
        { id: 'tab2', label: 'Tab 2', content: '<div>Content 2</div>' },
        { id: 'tab3', label: 'Tab 3', content: '<div>Content 3</div>' }
    ]
});

// Listen to changes
tabs.on('tab-change', (data) => {
    console.log('Changed from', data.from, 'to', data.to);
});
```

## From Ant Design

### Layout

**Ant Design:**
```jsx
import { Layout } from 'antd';
const { Header, Sider, Content } = Layout;

<Layout>
    <Sider width={200}>Sidebar</Sider>
    <Layout>
        <Header>Header</Header>
        <Content>Content</Content>
    </Layout>
</Layout>
```

**Flex:**
```javascript
import FlexSidebar from './layout/flex-sidebar.js';
import FlexToolbar from './layout/flex-toolbar.js';

// Create layout with sidebar
const layout = new FlexSidebar('#app', {
    position: 'left',
    width: '200px',
    content: {
        sidebar: '<div>Sidebar</div>',
        main: `
            <div id="toolbar"></div>
            <div id="content">Content</div>
        `
    }
});

// Add toolbar
const toolbar = new FlexToolbar('#toolbar', {
    position: 'top',
    sticky: true,
    actions: {
        left: [{ content: '<div>Header</div>' }]
    }
});
```

### Space

**Ant Design:**
```jsx
import { Space } from 'antd';

<Space direction="vertical" size="large">
    <div>Item 1</div>
    <div>Item 2</div>
    <div>Item 3</div>
</Space>
```

**Flex:**
```javascript
import { FlexStack } from './layout/flex-stack.js';

const space = new FlexStack('#space', {
    direction: 'vertical',
    gap: 6,  // 'large' spacing
    items: [
        { content: '<div>Item 1</div>' },
        { content: '<div>Item 2</div>' },
        { content: '<div>Item 3</div>' }
    ]
});
```

### Modal

**Ant Design:**
```jsx
import { Modal } from 'antd';

Modal.confirm({
    title: 'Confirm',
    content: 'Are you sure?',
    onOk() {
        console.log('OK');
    },
    onCancel() {
        console.log('Cancel');
    }
});
```

**Flex:**
```javascript
import { FlexModal } from './components/flex-modal.js';

const modal = new FlexModal({
    title: 'Confirm',
    content: '<p>Are you sure?</p>',
    footerActions: [
        {
            label: 'Cancel',
            variant: 'ghost',
            onClick: (e, modal) => {
                console.log('Cancel');
                modal.hide();
            }
        },
        {
            label: 'OK',
            variant: 'primary',
            onClick: (e, modal) => {
                console.log('OK');
                modal.hide();
            }
        }
    ]
});

modal.show();
```

## From Foundation

### Grid

**Foundation:**
```html
<div class="grid-container">
    <div class="grid-x grid-margin-x">
        <div class="cell medium-4">Cell 1</div>
        <div class="cell medium-4">Cell 2</div>
        <div class="cell medium-4">Cell 3</div>
    </div>
</div>
```

**Flex:**
```javascript
import { FlexGrid } from './layout/flex-grid.js';
import FlexContainer from './layout/flex-container.js';

const container = new FlexContainer('#app', {
    preset: 'standard'
});

const grid = new FlexGrid('#grid', {
    columns: { xs: 1, md: 3 },
    gap: 5,  // grid-margin-x equivalent
    items: [
        { id: '1', content: '<div>Cell 1</div>' },
        { id: '2', content: '<div>Cell 2</div>' },
        { id: '3', content: '<div>Cell 3</div>' }
    ]
});
```

### Off-canvas

**Foundation:**
```html
<div class="off-canvas position-left" id="offCanvas" data-off-canvas>
    <button class="close-button" data-close>×</button>
    <!-- Off-canvas content -->
</div>
```

**Flex:**
```javascript
import FlexSidebar from './layout/flex-sidebar.js';

const offCanvas = new FlexSidebar('#app', {
    position: 'left',
    mobileMode: 'overlay',
    defaultOpen: false,
    content: {
        sidebar: `
            <button onclick="sidebar.close()">×</button>
            <!-- Off-canvas content -->
        `,
        main: '<div>Main content</div>'
    }
});
```

## From jQuery UI

### Tabs

**jQuery UI:**
```html
<div id="tabs">
    <ul>
        <li><a href="#tabs-1">Tab 1</a></li>
        <li><a href="#tabs-2">Tab 2</a></li>
    </ul>
    <div id="tabs-1">Content 1</div>
    <div id="tabs-2">Content 2</div>
</div>

<script>
$('#tabs').tabs();
</script>
```

**Flex:**
```javascript
import { FlexTabs } from './components/flex-tabs.js';

const tabs = new FlexTabs('#tabs', {
    variant: 'underline',
    tabs: [
        { id: 'tab1', label: 'Tab 1', content: '<div>Content 1</div>' },
        { id: 'tab2', label: 'Tab 2', content: '<div>Content 2</div>' }
    ]
});
```

### Dialog

**jQuery UI:**
```html
<div id="dialog" title="Dialog Title">
    <p>Dialog content</p>
</div>

<script>
$('#dialog').dialog({
    modal: true,
    buttons: {
        "OK": function() {
            $(this).dialog("close");
        }
    }
});
</script>
```

**Flex:**
```javascript
import { FlexModal } from './components/flex-modal.js';

const dialog = new FlexModal({
    title: 'Dialog Title',
    content: '<p>Dialog content</p>',
    footerActions: [
        {
            label: 'OK',
            variant: 'primary',
            onClick: (e, modal) => modal.hide()
        }
    ]
});

dialog.show();
```

### Resizable

**jQuery UI:**
```html
<div id="resizable" class="ui-widget-content">
    <p>Resizable content</p>
</div>

<script>
$('#resizable').resizable();
</script>
```

**Flex:**
```javascript
import FlexSplitPane from './layout/flex-split-pane.js';

// Create resizable split pane
const resizable = new FlexSplitPane('#container', {
    direction: 'horizontal',
    panes: [
        {
            id: 'left',
            content: '<p>Resizable content</p>',
            size: '50%',
            minSize: '100px'
        },
        {
            id: 'right',
            content: '<div>Other content</div>',
            size: '50%'
        }
    ]
});
```

## General Migration Strategy

### 1. Identify Components

Map your existing components to Flex equivalents:

| Your Library | Flex Component |
|-------------|----------------|
| Grid/Row/Column | FlexGrid |
| Container | FlexContainer |
| Stack/Space | FlexStack |
| Card | FlexCard |
| Modal/Dialog | FlexModal |
| Tabs | FlexTabs |
| Sidebar/Drawer | FlexSidebar |
| Navbar/AppBar | FlexToolbar |
| Masonry | FlexMasonry |
| Split/Resizable | FlexSplitPane |
| Cluster/Group | FlexCluster |
| Section | FlexSection |

### 2. Update Dependencies

**Before:**
```html
<!-- Bootstrap -->
<link rel="stylesheet" href="bootstrap.css">
<script src="bootstrap.js"></script>

<!-- or React/MUI -->
<script src="react.js"></script>
<script src="mui.js"></script>
```

**After:**
```html
<!-- Tailwind (recommended) -->
<script src="https://cdn.tailwindcss.com"></script>

<!-- Phosphor Icons (recommended) -->
<script src="https://unpkg.com/@phosphor-icons/web"></script>

<!-- Your components (ES6 modules) -->
<script type="module" src="./js/app.js"></script>
```

### 3. Convert Markup to JavaScript

**Before (HTML-based):**
```html
<div class="row">
    <div class="col-md-4">
        <div class="card">
            <div class="card-body">Content</div>
        </div>
    </div>
</div>
```

**After (JavaScript-based):**
```javascript
import { FlexGrid } from './layout/flex-grid.js';
import { FlexCard } from './components/flex-card.js';

const grid = new FlexGrid('#app', {
    columns: { xs: 1, md: 3 }
});

const card = new FlexCard(document.createElement('div'), {
    content: 'Content'
});

grid.addItem({
    id: 'card1',
    content: card.getElement()
});
```

### 4. Update Event Handlers

**Before (jQuery/Bootstrap):**
```javascript
$('#myModal').on('show.bs.modal', function() {
    console.log('Modal shown');
});
```

**After (Flex):**
```javascript
modal.on('show', () => {
    console.log('Modal shown');
});
```

### 5. Migrate Responsive Breakpoints

Map your breakpoints to Flex:

| Bootstrap | Tailwind | Flex |
|-----------|----------|------|
| xs (< 576px) | xs (< 640px) | xs (0-639px) |
| sm (≥ 576px) | sm (≥ 640px) | sm (≥ 640px) |
| md (≥ 768px) | md (≥ 768px) | md (≥ 768px) |
| lg (≥ 992px) | lg (≥ 1024px) | lg (≥ 1024px) |
| xl (≥ 1200px) | xl (≥ 1280px) | xl (≥ 1280px) |

### 6. Update Styling

**Before (Bootstrap classes):**
```html
<div class="card shadow-lg p-3 mb-5 bg-white rounded">
```

**After (Tailwind classes):**
```html
<div class="bg-white rounded-lg shadow-lg p-3 mb-5">
```

Or use Flex component options:
```javascript
const card = new FlexCard('#card', {
    variant: 'shadowed',
    classes: ['p-3', 'mb-5']
});
```

## Common Patterns

### Pattern 1: Dashboard Layout

**Before (Bootstrap):**
```html
<div class="container-fluid">
    <div class="row">
        <nav class="col-md-2 sidebar">Sidebar</nav>
        <main class="col-md-10">
            <nav class="navbar">Header</nav>
            <div class="content">Content</div>
        </main>
    </div>
</div>
```

**After (Flex):**
```javascript
import FlexSidebar from './layout/flex-sidebar.js';
import FlexToolbar from './layout/flex-toolbar.js';

const dashboard = new FlexSidebar('#app', {
    position: 'left',
    width: '16.666%',  // 2/12 columns
    content: {
        sidebar: 'Sidebar',
        main: `
            <div id="header"></div>
            <div id="content">Content</div>
        `
    }
});

const header = new FlexToolbar('#header', {
    position: 'top',
    sticky: true
});
```

### Pattern 2: Card Grid

**Before (Material-UI):**
```jsx
<Grid container spacing={3}>
    {items.map(item => (
        <Grid item xs={12} md={4} key={item.id}>
            <Card>
                <CardContent>{item.content}</CardContent>
            </Card>
        </Grid>
    ))}
</Grid>
```

**After (Flex):**
```javascript
import { FlexGrid } from './layout/flex-grid.js';
import { FlexCard } from './components/flex-card.js';

const grid = new FlexGrid('#grid', {
    columns: { xs: 1, md: 3 },
    gap: 3
});

items.forEach(item => {
    const card = new FlexCard(document.createElement('div'), {
        content: item.content
    });

    grid.addItem({
        id: item.id,
        content: card.getElement()
    });
});
```

### Pattern 3: Modal Forms

**Before (Ant Design):**
```jsx
<Modal
    title="Create New Item"
    visible={visible}
    onOk={handleOk}
    onCancel={handleCancel}
>
    <Form>
        <Form.Item label="Name">
            <Input />
        </Form.Item>
    </Form>
</Modal>
```

**After (Flex):**
```javascript
import { FlexModal } from './components/flex-modal.js';

const modal = new FlexModal({
    title: 'Create New Item',
    content: `
        <form id="item-form">
            <div class="mb-4">
                <label class="block mb-2">Name</label>
                <input type="text" class="w-full p-2 border rounded" />
            </div>
        </form>
    `,
    footerActions: [
        {
            label: 'Cancel',
            variant: 'ghost',
            onClick: (e, modal) => modal.hide()
        },
        {
            label: 'OK',
            variant: 'primary',
            onClick: (e, modal) => {
                // Handle form submission
                const form = document.getElementById('item-form');
                // Process form...
                modal.hide();
            }
        }
    ]
});

modal.show();
```

## Tips for Successful Migration

1. **Start Small**: Migrate one component type at a time
2. **Test Thoroughly**: Test each migrated component before moving on
3. **Keep Old Code**: Comment out old code instead of deleting immediately
4. **Use Both**: You can use Flex alongside your existing library during migration
5. **Document Changes**: Keep notes on what you've changed for team members
6. **Leverage Events**: Use Flex's event system instead of callbacks where possible
7. **Responsive First**: Take advantage of Flex's built-in responsive system
8. **Clean Up**: Remove old library dependencies once migration is complete

## Need Help?

- [Component Documentation](./components/)
- [Architecture Guide](./ARCHITECTURE.md)
- [Examples Showcase](../frontend/assets/templates/components-showcase.html)
- [GitHub Issues](https://github.com/your-org/app-buildify/issues)

---

**Ready to migrate? Start with our [Quick Start Guide](./guides/quick-start.md)!**
