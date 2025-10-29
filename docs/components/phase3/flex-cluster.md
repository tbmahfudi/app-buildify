# FlexCluster Component

Horizontal grouping component with flexible spacing and wrapping, ideal for toolbars, tag lists, button groups, and chip collections.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Basic Usage](#basic-usage)
- [Configuration Options](#configuration-options)
- [Examples](#examples)
- [API Reference](#api-reference)
- [Events](#events)
- [Best Practices](#best-practices)
- [Accessibility](#accessibility)

## Overview

FlexCluster provides a flexible way to group items horizontally with automatic wrapping, consistent spacing, and powerful alignment options. It's perfect for creating tag clouds, button toolbars, filter chips, and other horizontal collections where items need to flow naturally.

### Key Capabilities

- **Auto-wrap**: Items automatically wrap to new lines when space runs out
- **Flexible alignment**: Control horizontal and vertical positioning
- **Priority ordering**: Items can be sorted by priority for consistent display
- **Dynamic management**: Add, remove, and update items programmatically
- **Responsive spacing**: Gap adjusts to different screen sizes
- **Item types**: Support for buttons, tags, chips, and custom content

## Features

- ✅ Auto-wrap items to new lines
- ✅ Flexible justify and align options
- ✅ Consistent gap spacing
- ✅ Responsive sizing and behavior
- ✅ Priority-based item ordering
- ✅ Dynamic item management (add, remove, update)
- ✅ Support for different item types
- ✅ Animation support
- ✅ Event-driven architecture
- ✅ Extends BaseComponent for lifecycle management

## Installation

```javascript
import FlexCluster from './layout/flex-cluster.js';
```

## Basic Usage

### Minimal Example

```javascript
const tagCloud = new FlexCluster('#tags', {
    items: [
        { id: 'tag1', content: '<span class="tag">JavaScript</span>' },
        { id: 'tag2', content: '<span class="tag">React</span>' },
        { id: 'tag3', content: '<span class="tag">CSS</span>' }
    ]
});
```

### HTML Structure Required

```html
<div id="tags"></div>
```

The component will render the items inside the container.

## Configuration Options

### Default Configuration

```javascript
{
    gap: 2,                 // Gap between items (spacing scale)
    justify: 'start',       // Horizontal alignment
    align: 'center',        // Vertical alignment
    wrap: true,             // Whether items should wrap
    responsive: null,       // Responsive configuration
    items: [],             // Array of item objects
    animated: false,       // Enable fade-in animations
    tag: 'div',            // HTML tag for container
    classes: []            // Additional CSS classes
}
```

### Option Details

#### `gap` (Number|String)

Spacing between items. Can be a spacing scale number (0-12) or a custom CSS value.

```javascript
gap: 2        // 0.5rem (spacing scale)
gap: 4        // 1rem
gap: '20px'   // Custom value
```

#### `justify` (String)

Horizontal alignment of items. Options:
- `'start'` - Align to the start (default)
- `'center'` - Center items
- `'end'` - Align to the end
- `'between'` - Space between items
- `'around'` - Space around items
- `'evenly'` - Even spacing

```javascript
justify: 'center'  // Center all items
```

#### `align` (String)

Vertical alignment of items. Options:
- `'start'` - Align to the top
- `'center'` - Center vertically (default)
- `'end'` - Align to the bottom
- `'stretch'` - Stretch to fill height
- `'baseline'` - Align to text baseline

```javascript
align: 'center'  // Center items vertically
```

#### `wrap` (Boolean)

Whether items should wrap to new lines.

```javascript
wrap: true   // Items wrap (default)
wrap: false  // Single line, may overflow
```

#### `items` (Array)

Array of item objects. Each item can have:

```javascript
{
    id: 'unique-id',           // Required for identification
    content: '<div>...</div>',  // HTML string, element, or component
    classes: ['custom-class'],  // Additional CSS classes
    style: { color: 'red' },    // Inline styles
    priority: 1                 // Higher priority = displayed first
}
```

#### `animated` (Boolean)

Enable fade-in animations for items.

```javascript
animated: true  // Enable animations
```

#### `responsive` (Object)

Responsive configuration for different breakpoints.

```javascript
responsive: {
    gap: { xs: 2, md: 4, lg: 6 },      // Responsive gap
    justify: { xs: 'center', md: 'start' },  // Responsive justify
    wrap: { xs: true, md: false }       // Responsive wrap
}
```

## Examples

### Example 1: Tag Cloud

```javascript
const tagCloud = new FlexCluster('#tag-cloud', {
    gap: 2,
    justify: 'start',
    wrap: true,
    items: [
        {
            id: 'js',
            content: '<span class="tag tag-blue">JavaScript</span>'
        },
        {
            id: 'react',
            content: '<span class="tag tag-cyan">React</span>'
        },
        {
            id: 'vue',
            content: '<span class="tag tag-green">Vue.js</span>'
        },
        {
            id: 'css',
            content: '<span class="tag tag-purple">CSS</span>'
        }
    ]
});
```

### Example 2: Button Toolbar with Priority

```javascript
const toolbar = new FlexCluster('#toolbar', {
    gap: 2,
    justify: 'between',
    align: 'center',
    wrap: false,
    items: [
        {
            id: 'new',
            content: '<button class="btn btn-primary">New</button>',
            priority: 3  // Highest priority
        },
        {
            id: 'save',
            content: '<button class="btn btn-success">Save</button>',
            priority: 2
        },
        {
            id: 'edit',
            content: '<button class="btn">Edit</button>',
            priority: 1
        },
        {
            id: 'delete',
            content: '<button class="btn btn-danger">Delete</button>',
            priority: 0
        }
    ]
});
```

### Example 3: Filter Chips

```javascript
const filters = new FlexCluster('#filters', {
    gap: 2,
    justify: 'start',
    wrap: true,
    items: [
        {
            id: 'all',
            content: '<button class="chip chip-active">All</button>'
        },
        {
            id: 'active',
            content: '<button class="chip">Active</button>'
        },
        {
            id: 'pending',
            content: '<button class="chip">Pending</button>'
        },
        {
            id: 'archived',
            content: '<button class="chip">Archived</button>'
        }
    ]
});

// Add click handlers
document.querySelectorAll('.chip').forEach(chip => {
    chip.addEventListener('click', (e) => {
        document.querySelectorAll('.chip').forEach(c =>
            c.classList.remove('chip-active')
        );
        e.target.classList.add('chip-active');
    });
});
```

### Example 4: Social Share Buttons

```javascript
const socialShare = new FlexCluster('#social-share', {
    gap: 3,
    justify: 'center',
    align: 'center',
    wrap: false,
    items: [
        {
            id: 'twitter',
            content: '<button class="social-btn btn-twitter"><i class="icon-twitter"></i></button>'
        },
        {
            id: 'facebook',
            content: '<button class="social-btn btn-facebook"><i class="icon-facebook"></i></button>'
        },
        {
            id: 'linkedin',
            content: '<button class="social-btn btn-linkedin"><i class="icon-linkedin"></i></button>'
        }
    ]
});
```

### Example 5: Responsive Behavior

```javascript
const responsiveCluster = new FlexCluster('#responsive', {
    responsive: {
        gap: { xs: 2, md: 4, lg: 6 },
        justify: { xs: 'center', md: 'start', lg: 'between' },
        wrap: { xs: true, md: true, lg: false }
    },
    items: [
        { id: '1', content: '<button>Button 1</button>' },
        { id: '2', content: '<button>Button 2</button>' },
        { id: '3', content: '<button>Button 3</button>' }
    ]
});
```

## API Reference

### Methods

#### `addItem(item, index)`

Add a new item to the cluster.

```javascript
cluster.addItem({
    id: 'new-tag',
    content: '<span class="tag">New Tag</span>'
});

// Insert at specific index
cluster.addItem(item, 2);
```

**Parameters:**
- `item` (Object): Item configuration
- `index` (Number, optional): Position to insert (default: append)

**Returns:** void

#### `removeItem(itemId)`

Remove an item by ID.

```javascript
cluster.removeItem('tag1');
```

**Parameters:**
- `itemId` (String): ID of item to remove

**Returns:** void

#### `updateItem(itemId, updates)`

Update an existing item.

```javascript
cluster.updateItem('tag1', {
    content: '<span class="tag tag-active">JavaScript</span>',
    priority: 5
});
```

**Parameters:**
- `itemId` (String): ID of item to update
- `updates` (Object): Properties to update

**Returns:** void

#### `clearItems()`

Remove all items.

```javascript
cluster.clearItems();
```

**Returns:** void

#### `setGap(gap)`

Update gap spacing.

```javascript
cluster.setGap(4);
```

**Parameters:**
- `gap` (Number|String): New gap value

**Returns:** void

#### `setJustify(justify)`

Update horizontal alignment.

```javascript
cluster.setJustify('center');
```

**Parameters:**
- `justify` (String): New justify value

**Returns:** void

#### `setAlign(align)`

Update vertical alignment.

```javascript
cluster.setAlign('end');
```

**Parameters:**
- `align` (String): New align value

**Returns:** void

#### `setWrap(wrap)`

Update wrap behavior.

```javascript
cluster.setWrap(false);
```

**Parameters:**
- `wrap` (Boolean): Whether items should wrap

**Returns:** void

#### `getItems()`

Get all items.

```javascript
const items = cluster.getItems();
```

**Returns:** Array - Copy of items array

#### `getItem(itemId)`

Get item by ID.

```javascript
const item = cluster.getItem('tag1');
```

**Parameters:**
- `itemId` (String): ID of item

**Returns:** Object|null - Item object or null if not found

#### `getItemElement(itemId)`

Get item's DOM element.

```javascript
const element = cluster.getItemElement('tag1');
```

**Parameters:**
- `itemId` (String): ID of item

**Returns:** HTMLElement|null - DOM element or null

#### `getElement()`

Get cluster container element.

```javascript
const container = cluster.getElement();
```

**Returns:** HTMLElement - Cluster container

#### `destroy()`

Clean up and remove cluster.

```javascript
cluster.destroy();
```

**Returns:** void

## Events

FlexCluster emits events through the BaseComponent event system:

### Available Events

#### `init`

Fired when component is initialized.

```javascript
cluster.on('init', () => {
    console.log('Cluster initialized');
});
```

#### `render`

Fired when component is rendered.

```javascript
cluster.on('render', () => {
    console.log('Cluster rendered');
});
```

#### `item:add`

Fired when item is added.

```javascript
cluster.on('item:add', (data) => {
    console.log('Item added:', data.item);
});
```

#### `item:remove`

Fired when item is removed.

```javascript
cluster.on('item:remove', (data) => {
    console.log('Item removed:', data.item);
});
```

#### `item:update`

Fired when item is updated.

```javascript
cluster.on('item:update', (data) => {
    console.log('Item updated:', data.itemId, data.updates);
});
```

#### `update`

Fired when configuration is updated.

```javascript
cluster.on('update', (data) => {
    console.log('Configuration updated:', data);
});
```

#### `clear`

Fired when all items are cleared.

```javascript
cluster.on('clear', () => {
    console.log('All items cleared');
});
```

#### `destroy`

Fired when component is destroyed.

```javascript
cluster.on('destroy', () => {
    console.log('Cluster destroyed');
});
```

## Best Practices

### 1. Use Semantic Item IDs

```javascript
// Good
{ id: 'filter-active', content: '...' }

// Avoid
{ id: 'item1', content: '...' }
```

### 2. Leverage Priority for Important Items

```javascript
items: [
    { id: 'save', content: '...', priority: 10 },  // Always first
    { id: 'cancel', content: '...', priority: 5 },
    { id: 'help', content: '...', priority: 1 }
]
```

### 3. Use Responsive Configuration for Better UX

```javascript
responsive: {
    gap: { xs: 2, lg: 4 },      // Smaller gap on mobile
    justify: { xs: 'center', md: 'start' },  // Center on mobile
    wrap: { xs: true, md: false }  // Wrap on mobile, single line on desktop
}
```

### 4. Clean Up When Done

```javascript
// When removing from DOM
cluster.destroy();
```

### 5. Use Event Handlers for Dynamic Behavior

```javascript
cluster.on('item:add', (data) => {
    // Attach event handlers to new items
    const element = cluster.getItemElement(data.item.id);
    element.querySelector('button')?.addEventListener('click', handleClick);
});
```

## Accessibility

### Keyboard Navigation

Ensure items are keyboard accessible:

```javascript
items: [
    {
        id: 'btn1',
        content: '<button tabindex="0">Action</button>'
    }
]
```

### ARIA Labels

Add appropriate ARIA attributes:

```javascript
items: [
    {
        id: 'close',
        content: '<button aria-label="Close dialog"><i class="icon-close"></i></button>'
    }
]
```

### Focus Management

Manage focus when items are added/removed:

```javascript
cluster.on('item:add', (data) => {
    const element = cluster.getItemElement(data.item.id);
    // Focus new item if needed
    element.querySelector('button')?.focus();
});
```

## Browser Support

FlexCluster uses modern JavaScript features and CSS Flexbox:

- Chrome/Edge: Latest 2 versions
- Firefox: Latest 2 versions
- Safari: Latest 2 versions
- iOS Safari: Latest 2 versions

## Performance Considerations

1. **Large Item Counts**: For 100+ items, consider virtualization or pagination
2. **Complex Content**: Keep item content simple for better performance
3. **Animations**: Use sparingly with many items
4. **Responsive Updates**: Debounced automatically for resize events

## Related Components

- **FlexStack**: For vertical or horizontal stacking with dividers
- **FlexGrid**: For multi-column grid layouts
- **FlexToolbar**: For header/footer toolbars with action groups

## See Also

- [FlexToolbar Documentation](./flex-toolbar.md)
- [Phase 3 Components Overview](../phase3-overview.md)
- [Component Architecture](../../architecture.md)
