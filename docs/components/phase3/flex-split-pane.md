# FlexSplitPane Component

Resizable split layouts with drag handles, min/max constraints, and persistence. Perfect for IDE-style layouts, compare views, and dashboard panels.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Basic Usage](#basic-usage)
- [Configuration Options](#configuration-options)
- [Examples](#examples)
- [API Reference](#api-reference)
- [Events](#events)
- [Persistence](#persistence)
- [Best Practices](#best-practices)
- [Accessibility](#accessibility)

## Overview

FlexSplitPane creates resizable split layouts where users can drag dividers to adjust pane sizes. It supports horizontal/vertical splits, multiple panes, min/max constraints, and automatic persistence to localStorage. Perfect for creating IDE-like interfaces, comparison views, and flexible dashboards.

### Key Capabilities

- **Drag Resizing**: Users can drag dividers to resize adjacent panes
- **Multiple Panes**: Support for 2+ panes with multiple dividers
- **Min/Max Constraints**: Prevent panes from becoming too small/large
- **Persistence**: Save/restore sizes across sessions
- **Horizontal/Vertical**: Support both split directions
- **Touch Support**: Works on touch devices
- **Keyboard Accessible**: Resize with keyboard

## Features

- ✅ Horizontal and vertical split directions
- ✅ Multiple panes (2+) with multiple dividers
- ✅ Drag handles for resizing
- ✅ Min/max size constraints
- ✅ localStorage persistence
- ✅ Touch device support
- ✅ Keyboard accessibility
- ✅ Customizable handle appearance
- ✅ Real-time resize events
- ✅ Dynamic pane management
- ✅ Extends BaseComponent

## Installation

```javascript
import FlexSplitPane from './layout/flex-split-pane.js';
```

## Basic Usage

### Minimal Example

```javascript
const split = new FlexSplitPane('#split-container', {
    direction: 'horizontal',
    panes: [
        {
            id: 'left',
            content: '<div>Left Pane</div>',
            size: '50%'
        },
        {
            id: 'right',
            content: '<div>Right Pane</div>',
            size: '50%'
        }
    ]
});
```

### HTML Structure Required

```html
<div id="split-container" style="height: 500px;"></div>
```

**Important:** Container must have explicit height for vertical content.

## Configuration Options

### Default Configuration

```javascript
{
    direction: 'horizontal',    // horizontal | vertical
    panes: [],                 // Array of pane configurations
    handleSize: 8,             // Handle width/height in pixels
    handleColor: 'gray-300',   // Tailwind color class
    handleHoverColor: 'gray-400',  // Hover state color
    persist: false,            // Save sizes to localStorage
    persistKey: 'split-pane-layout',  // localStorage key
    onResize: null,            // Resize callback
    tag: 'div',                // HTML tag
    classes: []                // Additional CSS classes
}
```

### Option Details

#### `direction` (String)

Split direction. Options:
- `'horizontal'` - Left/right split (default)
- `'vertical'` - Top/bottom split

```javascript
direction: 'horizontal'  // Left and right panes
direction: 'vertical'    // Top and bottom panes
```

#### `panes` (Array)

Array of pane configurations. Minimum 2 panes required.

```javascript
panes: [
    {
        id: 'pane1',              // Required: Unique identifier
        content: '<div>...</div>', // Required: HTML string, element, or component
        size: '50%',              // Initial size (%, px, or number)
        minSize: '200px',         // Minimum size constraint
        maxSize: '800px',         // Maximum size constraint
        classes: ['custom'],      // Additional CSS classes
        style: { /* styles */ }   // Inline styles
    },
    // ... more panes
]
```

**Size Units:**
- Percentage: `'50%'`
- Pixels: `'300px'` or `300`
- Flex: Remaining space distributed proportionally

#### `handleSize` (Number)

Width (horizontal) or height (vertical) of drag handles in pixels.

```javascript
handleSize: 8   // 8px wide/tall (default)
handleSize: 12  // Thicker handle
```

#### `handleColor` (String)

Tailwind color class for handles.

```javascript
handleColor: 'gray-300'     // Light gray
handleColor: 'indigo-600'   // Indigo
```

#### `handleHoverColor` (String)

Tailwind color class for handle hover state.

```javascript
handleHoverColor: 'gray-400'   // Darker on hover
```

#### `persist` (Boolean)

Save pane sizes to localStorage and restore on page load.

```javascript
persist: true  // Enable persistence
```

#### `persistKey` (String)

localStorage key for persisting sizes. Required if `persist: true`.

```javascript
persistKey: 'my-layout'  // Unique key per layout
```

#### `onResize` (Function)

Callback fired during resize operations.

```javascript
onResize: (sizes) => {
    console.log('New sizes:', sizes);
}
```

**Parameters:**
- `sizes` (Array): Array of current pane sizes in pixels

## Examples

### Example 1: Horizontal Split (IDE Layout)

```javascript
const ide = new FlexSplitPane('#ide', {
    direction: 'horizontal',
    panes: [
        {
            id: 'sidebar',
            content: `
                <div class="sidebar">
                    <h3>File Explorer</h3>
                    <ul>
                        <li>src/</li>
                        <li>components/</li>
                        <li>assets/</li>
                    </ul>
                </div>
            `,
            size: '250px',
            minSize: '200px',
            maxSize: '400px'
        },
        {
            id: 'editor',
            content: `
                <div class="editor">
                    <textarea placeholder="Write code here..."></textarea>
                </div>
            `,
            size: '60%',
            minSize: '400px'
        },
        {
            id: 'preview',
            content: `
                <div class="preview">
                    <h3>Preview</h3>
                    <iframe src="preview.html"></iframe>
                </div>
            `,
            size: '40%',
            minSize: '300px'
        }
    ],
    handleSize: 6,
    handleColor: 'gray-400',
    persist: true,
    persistKey: 'ide-layout'
});
```

### Example 2: Vertical Split (Dashboard)

```javascript
const dashboard = new FlexSplitPane('#dashboard', {
    direction: 'vertical',
    panes: [
        {
            id: 'charts',
            content: `
                <div class="charts-section">
                    <h2>Analytics</h2>
                    <div id="chart-container"></div>
                </div>
            `,
            size: '60%',
            minSize: '200px'
        },
        {
            id: 'data',
            content: `
                <div class="data-section">
                    <h2>Data Table</h2>
                    <table id="data-table"></table>
                </div>
            `,
            size: '40%',
            minSize: '150px'
        }
    ],
    handleSize: 8,
    handleColor: 'blue-400',
    persist: true,
    persistKey: 'dashboard-split'
});
```

### Example 3: Compare View

```javascript
const compare = new FlexSplitPane('#compare', {
    direction: 'horizontal',
    panes: [
        {
            id: 'before',
            content: `
                <div class="compare-pane">
                    <h3>Before</h3>
                    <img src="before.jpg" alt="Before" />
                </div>
            `,
            size: '50%',
            minSize: '200px'
        },
        {
            id: 'after',
            content: `
                <div class="compare-pane">
                    <h3>After</h3>
                    <img src="after.jpg" alt="After" />
                </div>
            `,
            size: '50%',
            minSize: '200px'
        }
    ],
    handleSize: 10,
    handleColor: 'purple-500',
    handleHoverColor: 'purple-600'
});
```

### Example 4: Nested Splits

```javascript
// Create horizontal split
const outer = new FlexSplitPane('#outer', {
    direction: 'horizontal',
    panes: [
        {
            id: 'left',
            content: '<div class="panel">Left Panel</div>',
            size: '30%'
        },
        {
            id: 'middle',
            content: '<div id="inner-split"></div>',  // Nested split here
            size: '70%'
        }
    ]
});

// Create nested vertical split
setTimeout(() => {
    new FlexSplitPane('#inner-split', {
        direction: 'vertical',
        panes: [
            {
                id: 'top',
                content: '<div class="panel">Top Panel</div>',
                size: '50%'
            },
            {
                id: 'bottom',
                content: '<div class="panel">Bottom Panel</div>',
                size: '50%'
            }
        ]
    });
}, 100);
```

### Example 5: Dynamic Content

```javascript
const split = new FlexSplitPane('#split', {
    direction: 'horizontal',
    panes: [
        {
            id: 'list',
            content: '<div id="item-list"></div>',
            size: '300px',
            minSize: '200px',
            maxSize: '500px'
        },
        {
            id: 'detail',
            content: '<div id="item-detail">Select an item</div>',
            size: '70%'
        }
    ],
    persist: true,
    persistKey: 'master-detail'
});

// Listen for list item clicks
document.addEventListener('click', (e) => {
    if (e.target.matches('.list-item')) {
        const detail = split.getPaneElement('detail');
        detail.innerHTML = `<div>Details for ${e.target.textContent}</div>`;
    }
});
```

## API Reference

### Methods

#### `addPane(pane, index)`

Add a pane at specified index.

```javascript
split.addPane({
    id: 'new-pane',
    content: '<div>New Pane</div>',
    size: '25%'
}, 1);  // Insert at index 1
```

**Parameters:**
- `pane` (Object): Pane configuration
- `index` (Number): Position to insert

**Returns:** void

**Note:** Triggers rerender and creates new handle

#### `removePane(paneId)`

Remove a pane by ID.

```javascript
split.removePane('sidebar');
```

**Parameters:**
- `paneId` (String): ID of pane to remove

**Returns:** void

**Note:** Triggers rerender, removes associated handle

#### `updatePane(paneId, updates)`

Update existing pane.

```javascript
split.updatePane('editor', {
    content: '<div>Updated content</div>',
    size: '500px'
});
```

**Parameters:**
- `paneId` (String): ID of pane to update
- `updates` (Object): Properties to update

**Returns:** void

#### `setSize(paneId, size)`

Set pane size.

```javascript
split.setSize('sidebar', '300px');
```

**Parameters:**
- `paneId` (String): ID of pane
- `size` (String|Number): New size

**Returns:** void

#### `getSizes()`

Get current sizes of all panes.

```javascript
const sizes = split.getSizes();
// Returns: [250, 450, 300]
```

**Returns:** Array - Pane sizes in pixels

#### `setSizes(sizes)`

Set all pane sizes at once.

```javascript
split.setSizes([200, 500, 300]);
```

**Parameters:**
- `sizes` (Array): Array of sizes in pixels

**Returns:** void

#### `resetSizes()`

Reset to initial sizes.

```javascript
split.resetSizes();
```

**Returns:** void

**Note:** Clears persisted sizes if persistence enabled

#### `getPaneElement(paneId)`

Get pane's DOM element.

```javascript
const element = split.getPaneElement('editor');
```

**Parameters:**
- `paneId` (String): ID of pane

**Returns:** HTMLElement|null

#### `getElement()`

Get split container element.

```javascript
const container = split.getElement();
```

**Returns:** HTMLElement

#### `destroy()`

Clean up and remove split pane.

```javascript
split.destroy();
```

**Returns:** void

**Note:** Removes event listeners and clears DOM

## Events

### Available Events

#### `init`

Fired when split pane is initialized.

```javascript
split.on('init', () => {
    console.log('Split pane initialized');
});
```

#### `render`

Fired when split pane is rendered.

```javascript
split.on('render', () => {
    console.log('Split pane rendered');
});
```

#### `resize:start`

Fired when user starts resizing.

```javascript
split.on('resize:start', (data) => {
    console.log('Resize started:', data.handleIndex);
});
```

**Data:**
- `handleIndex` (Number): Index of handle being dragged

#### `resize`

Fired during resize (throttled).

```javascript
split.on('resize', (data) => {
    console.log('Resizing:', data.sizes);
});
```

**Data:**
- `sizes` (Array): Current pane sizes in pixels

#### `resize:end`

Fired when resize completes.

```javascript
split.on('resize:end', (data) => {
    console.log('Resize ended:', data.sizes);
});
```

**Data:**
- `sizes` (Array): Final pane sizes in pixels

#### `pane:add`

Fired when pane is added.

```javascript
split.on('pane:add', (data) => {
    console.log('Pane added:', data.pane);
});
```

#### `pane:remove`

Fired when pane is removed.

```javascript
split.on('pane:remove', (data) => {
    console.log('Pane removed:', data.paneId);
});
```

#### `pane:update`

Fired when pane is updated.

```javascript
split.on('pane:update', (data) => {
    console.log('Pane updated:', data.paneId, data.updates);
});
```

#### `destroy`

Fired when split pane is destroyed.

```javascript
split.on('destroy', () => {
    console.log('Split pane destroyed');
});
```

## Persistence

### Enabling Persistence

```javascript
const split = new FlexSplitPane('#split', {
    persist: true,
    persistKey: 'my-layout',
    panes: [/* ... */]
});
```

### How It Works

1. **Save**: Sizes saved to localStorage on resize end
2. **Restore**: Sizes loaded from localStorage on init
3. **Clear**: Call `resetSizes()` to clear saved sizes

### Multiple Layouts

Use unique keys for different layouts:

```javascript
// Layout 1
const split1 = new FlexSplitPane('#split1', {
    persist: true,
    persistKey: 'layout-1',
    // ...
});

// Layout 2
const split2 = new FlexSplitPane('#split2', {
    persist: true,
    persistKey: 'layout-2',
    // ...
});
```

### Manual Persistence

```javascript
// Save sizes manually
const sizes = split.getSizes();
localStorage.setItem('custom-key', JSON.stringify(sizes));

// Restore later
const saved = JSON.parse(localStorage.getItem('custom-key'));
if (saved) {
    split.setSizes(saved);
}
```

## Best Practices

### 1. Set Appropriate Constraints

```javascript
panes: [
    {
        id: 'sidebar',
        size: '250px',
        minSize: '150px',   // Prevent too small
        maxSize: '500px'    // Prevent too large
    }
]
```

### 2. Provide Explicit Container Height

```html
<!-- Good -->
<div id="split" style="height: 600px;"></div>

<!-- Or -->
<style>
#split { height: 100vh; }
</style>
```

### 3. Use Percentage for Flexible Panes

```javascript
panes: [
    { id: 'sidebar', size: '250px', minSize: '200px' },  // Fixed
    { id: 'main', size: '100%', minSize: '400px' }       // Flexible
]
```

### 4. Unique Persist Keys

```javascript
// Good - descriptive and unique
persistKey: 'ide-editor-layout'

// Avoid - too generic
persistKey: 'split'
```

### 5. Handle Resize Events

```javascript
split.on('resize', (data) => {
    // Trigger chart redraws, etc.
    updateCharts();
});
```

### 6. Clean Up When Done

```javascript
// When component unmounts
split.destroy();
```

## Accessibility

### Keyboard Support

Handles support keyboard navigation:
- **Arrow Keys**: Resize (5px increments)
- **Shift + Arrow**: Resize (20px increments)
- **Home**: Reset to min size
- **End**: Expand to max size

### ARIA Attributes

Handles include appropriate ARIA:

```html
<div
    role="separator"
    aria-orientation="horizontal"
    aria-valuenow="250"
    aria-valuemin="200"
    aria-valuemax="500"
    tabindex="0"
></div>
```

### Screen Reader Support

Add labels to panes:

```javascript
panes: [
    {
        id: 'sidebar',
        content: '<div aria-label="Sidebar navigation">...</div>',
        // ...
    }
]
```

### Focus Management

```javascript
split.on('resize:start', () => {
    // Optional: Show visual feedback
    document.body.classList.add('resizing');
});

split.on('resize:end', () => {
    document.body.classList.remove('resizing');
});
```

## Browser Support

FlexSplitPane uses modern JavaScript and CSS:

- Chrome/Edge: Latest 2 versions
- Firefox: Latest 2 versions
- Safari: Latest 2 versions
- iOS Safari: Latest 2 versions (with touch support)

### Touch Support

Drag handles work on touch devices:
- `touchstart`
- `touchmove`
- `touchend`

## Performance Considerations

1. **Resize Throttling**: Resize events throttled automatically
2. **DOM Updates**: Minimal reflows during resize
3. **Persistence**: Uses efficient localStorage operations
4. **Memory**: Clean up with `destroy()` when done

### Large Content

For large content in panes:

```javascript
panes: [
    {
        id: 'large-content',
        content: '<div style="overflow: auto; height: 100%;">...</div>'
    }
]
```

## Related Components

- **FlexContainer**: For constraining overall layout width
- **FlexSection**: For full-width sections around split panes
- **FlexSidebar**: For simpler sidebar layouts without resizing

## Common Patterns

### Master-Detail

```javascript
new FlexSplitPane('#master-detail', {
    direction: 'horizontal',
    panes: [
        { id: 'list', size: '30%', minSize: '200px' },
        { id: 'detail', size: '70%', minSize: '400px' }
    ]
});
```

### Three-Column Layout

```javascript
new FlexSplitPane('#three-col', {
    direction: 'horizontal',
    panes: [
        { id: 'left', size: '25%' },
        { id: 'center', size: '50%' },
        { id: 'right', size: '25%' }
    ]
});
```

### Top/Bottom Split

```javascript
new FlexSplitPane('#top-bottom', {
    direction: 'vertical',
    panes: [
        { id: 'content', size: '70%' },
        { id: 'console', size: '30%', minSize: '100px' }
    ]
});
```

## See Also

- [FlexSidebar Documentation](../../phase2/flex-sidebar.md)
- [Phase 3 Components Overview](../phase3-overview.md)
- [Layout Patterns Guide](../../guides/layout-patterns.md)
