# FlexMasonry Component

Pinterest-style masonry grid layout where items of varying heights flow naturally into columns with minimal gaps. Perfect for image galleries, card collections, and dynamic content feeds.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Basic Usage](#basic-usage)
- [Configuration Options](#configuration-options)
- [Examples](#examples)
- [API Reference](#api-reference)
- [Events](#events)
- [Algorithm](#algorithm)
- [Best Practices](#best-practices)
- [Performance](#performance)

## Overview

FlexMasonry implements a Pinterest-style masonry grid layout that automatically arranges items of varying heights into columns with minimal vertical gaps. The component uses a column balancing algorithm to distribute items evenly and supports lazy loading, animations, and responsive column counts.

### Key Capabilities

- **Column Balancing**: Intelligent algorithm distributes items to shortest column
- **Variable Heights**: Items can have different heights for natural layout
- **Responsive Columns**: Adjust column count by breakpoint
- **Lazy Loading**: Optional intersection observer for images
- **Auto Reflow**: Automatically adjusts on resize
- **Dynamic Management**: Add, remove, and update items
- **Animation Support**: Staggered fade-in animations

## Features

- ✅ Responsive column count
- ✅ Variable item heights
- ✅ Minimal gap spacing
- ✅ Lazy loading support
- ✅ Reflow on window resize
- ✅ Dynamic item management
- ✅ Animation support
- ✅ Column balancing algorithm
- ✅ ResizeObserver integration
- ✅ Event-driven architecture
- ✅ Extends BaseComponent

## Installation

```javascript
import FlexMasonry from './layout/flex-masonry.js';
```

## Basic Usage

### Minimal Example

```javascript
const gallery = new FlexMasonry('#gallery', {
    columns: { xs: 1, sm: 2, md: 3, lg: 4 },
    gap: 4,
    items: [
        { id: 'img1', content: '<img src="1.jpg" />', height: 200 },
        { id: 'img2', content: '<img src="2.jpg" />', height: 300 },
        { id: 'img3', content: '<img src="3.jpg" />', height: 250 }
    ]
});
```

### HTML Structure Required

```html
<div id="gallery"></div>
```

The component creates column structure and distributes items.

## Configuration Options

### Default Configuration

```javascript
{
    columns: { xs: 1, sm: 2, md: 3, lg: 4 },  // Responsive columns
    gap: 4,                 // Gap between items
    columnGap: null,        // Horizontal gap (overrides gap)
    rowGap: null,           // Vertical gap (overrides gap)
    items: [],             // Array of item objects
    animated: false,       // Fade-in animations
    lazyLoad: false,       // Lazy load images
    reflow: true,          // Reflow on resize
    tag: 'div',            // HTML tag
    classes: []            // Additional CSS classes
}
```

### Option Details

#### `columns` (Number|Object)

Number of columns. Can be responsive.

```javascript
columns: 3                              // Fixed 3 columns
columns: { xs: 1, sm: 2, md: 3, lg: 4 } // Responsive
```

#### `gap` (Number|String)

Gap between items (both horizontal and vertical). Uses spacing scale or custom value.

```javascript
gap: 4        // 1rem (spacing scale)
gap: '20px'   // Custom value
```

#### `columnGap` (Number|String)

Horizontal gap between columns. Overrides `gap` if specified.

```javascript
columnGap: 6   // Larger horizontal gap
```

#### `rowGap` (Number|String)

Vertical gap between items. Overrides `gap` if specified.

```javascript
rowGap: 3      // Smaller vertical gap
```

#### `items` (Array)

Array of item objects. Each item should have:

```javascript
{
    id: 'unique-id',           // Required for identification
    content: '<div>...</div>', // HTML string, element, or component
    height: 200,               // Estimated height in pixels (optional)
    classes: ['custom-class'], // Additional CSS classes
    style: { /* styles */ }    // Inline styles
}
```

**Important:** Providing `height` improves initial layout accuracy.

#### `animated` (Boolean)

Enable staggered fade-in animations for items.

```javascript
animated: true  // Enable animations
```

#### `lazyLoad` (Boolean)

Enable lazy loading for images using IntersectionObserver.

```javascript
lazyLoad: true  // Images load when visible
```

When enabled, use `data-src` instead of `src`:

```javascript
{
    content: '<img data-src="image.jpg" alt="..." />'
}
```

#### `reflow` (Boolean)

Automatically reflow layout on window resize.

```javascript
reflow: true   // Auto reflow (default)
reflow: false  // Manual reflow only
```

## Examples

### Example 1: Image Gallery

```javascript
const gallery = new FlexMasonry('#gallery', {
    columns: { xs: 1, sm: 2, md: 3, lg: 4 },
    gap: 4,
    animated: true,
    lazyLoad: true,
    items: [
        {
            id: 'img1',
            content: '<img data-src="photo1.jpg" alt="Photo 1" />',
            height: 300
        },
        {
            id: 'img2',
            content: '<img data-src="photo2.jpg" alt="Photo 2" />',
            height: 450
        },
        {
            id: 'img3',
            content: '<img data-src="photo3.jpg" alt="Photo 3" />',
            height: 250
        },
        {
            id: 'img4',
            content: '<img data-src="photo4.jpg" alt="Photo 4" />',
            height: 400
        }
    ]
});
```

### Example 2: Card Masonry

```javascript
const cards = new FlexMasonry('#cards', {
    columns: { xs: 1, md: 2, lg: 3 },
    gap: 6,
    animated: true,
    items: [
        {
            id: 'card1',
            height: 220,
            content: `
                <div class="card">
                    <h3>Card Title 1</h3>
                    <p>Short description here.</p>
                </div>
            `
        },
        {
            id: 'card2',
            height: 180,
            content: `
                <div class="card">
                    <h3>Card Title 2</h3>
                    <p>Brief text.</p>
                </div>
            `
        },
        {
            id: 'card3',
            height: 260,
            content: `
                <div class="card">
                    <h3>Card Title 3</h3>
                    <p>This card has more content and takes up more vertical space in the layout.</p>
                </div>
            `
        }
    ]
});
```

### Example 3: Pinterest-Style Feed

```javascript
const feed = new FlexMasonry('#feed', {
    columns: { xs: 2, sm: 3, md: 4, lg: 5 },
    gap: 3,
    animated: true,
    lazyLoad: true,
    items: generateFeedItems() // Function that returns array of items
});

function generateFeedItems() {
    return Array.from({ length: 50 }, (_, i) => ({
        id: `pin-${i}`,
        height: Math.floor(Math.random() * 200) + 200,  // 200-400px
        content: `
            <div class="pin">
                <img data-src="pin-${i}.jpg" alt="Pin ${i}" />
                <div class="pin-overlay">
                    <h4>Pin Title ${i}</h4>
                    <button class="save-btn">Save</button>
                </div>
            </div>
        `
    }));
}
```

### Example 4: Dynamic Content Feed

```javascript
const contentFeed = new FlexMasonry('#content-feed', {
    columns: { xs: 1, sm: 2, md: 3 },
    gap: 5,
    items: []
});

// Load initial content
loadContent();

// Infinite scroll
window.addEventListener('scroll', () => {
    if (isNearBottom()) {
        loadContent();
    }
});

function loadContent() {
    fetch('/api/content')
        .then(res => res.json())
        .then(items => {
            const newItems = items.map(item => ({
                id: item.id,
                height: item.estimatedHeight,
                content: createContentCard(item)
            }));

            contentFeed.addItems(newItems);
        });
}
```

### Example 5: Mixed Content

```javascript
const mixedGallery = new FlexMasonry('#mixed', {
    columns: { xs: 1, sm: 2, md: 3 },
    gap: 4,
    items: [
        {
            id: 'quote',
            height: 180,
            content: `
                <div class="quote-card">
                    <blockquote>"This is a quote"</blockquote>
                    <cite>— Author</cite>
                </div>
            `
        },
        {
            id: 'image',
            height: 300,
            content: '<img src="photo.jpg" alt="Photo" />'
        },
        {
            id: 'video',
            height: 250,
            content: `
                <video controls poster="thumb.jpg">
                    <source src="video.mp4" type="video/mp4">
                </video>
            `
        },
        {
            id: 'text',
            height: 200,
            content: `
                <div class="text-card">
                    <h3>Article Title</h3>
                    <p>Article excerpt...</p>
                </div>
            `
        }
    ]
});
```

## API Reference

### Methods

#### `addItem(item)`

Add a single item to the masonry.

```javascript
masonry.addItem({
    id: 'new-item',
    content: '<img src="new.jpg" />',
    height: 280
});
```

**Parameters:**
- `item` (Object): Item configuration

**Returns:** void

**Triggers:** Automatic reflow

#### `addItems(items)`

Add multiple items at once.

```javascript
masonry.addItems([
    { id: 'item1', content: '...', height: 200 },
    { id: 'item2', content: '...', height: 250 }
]);
```

**Parameters:**
- `items` (Array): Array of item configurations

**Returns:** void

**Triggers:** Automatic reflow

#### `removeItem(itemId)`

Remove item by ID.

```javascript
masonry.removeItem('item1');
```

**Parameters:**
- `itemId` (String): ID of item to remove

**Returns:** void

**Triggers:** Automatic reflow

#### `updateItem(itemId, updates)`

Update existing item.

```javascript
masonry.updateItem('item1', {
    content: '<img src="updated.jpg" />',
    height: 320
});
```

**Parameters:**
- `itemId` (String): ID of item to update
- `updates` (Object): Properties to update

**Returns:** void

**Triggers:** Automatic reflow

#### `clearItems()`

Remove all items.

```javascript
masonry.clearItems();
```

**Returns:** void

**Triggers:** Automatic reflow

#### `setColumns(columns)`

Update column count.

```javascript
masonry.setColumns(4);

// Or responsive
masonry.setColumns({ xs: 1, sm: 2, md: 3, lg: 4 });
```

**Parameters:**
- `columns` (Number|Object): Column count or responsive config

**Returns:** void

**Triggers:** Automatic reflow

#### `setGap(gap)`

Update gap spacing.

```javascript
masonry.setGap(6);
```

**Parameters:**
- `gap` (Number|String): Gap value

**Returns:** void

**Triggers:** Automatic reflow

#### `reflow()`

Manually trigger reflow.

```javascript
masonry.reflow();
```

**Returns:** void

**Note:** Called automatically on resize if `reflow: true`

#### `getItems()`

Get all items.

```javascript
const items = masonry.getItems();
```

**Returns:** Array - Copy of items array

#### `getItemElement(itemId)`

Get item's DOM element.

```javascript
const element = masonry.getItemElement('item1');
```

**Parameters:**
- `itemId` (String): ID of item

**Returns:** HTMLElement|null

#### `getElement()`

Get masonry container element.

```javascript
const container = masonry.getElement();
```

**Returns:** HTMLElement

#### `destroy()`

Clean up and remove masonry.

```javascript
masonry.destroy();
```

**Returns:** void

**Note:** Disconnects ResizeObserver and removes event listeners

## Events

### Available Events

#### `init`

Fired when masonry is initialized.

```javascript
masonry.on('init', () => {
    console.log('Masonry initialized');
});
```

#### `render`

Fired when masonry is rendered.

```javascript
masonry.on('render', () => {
    console.log('Masonry rendered');
});
```

#### `reflow`

Fired when layout is reflowed.

```javascript
masonry.on('reflow', () => {
    console.log('Layout reflowed');
});
```

#### `item:add`

Fired when item(s) added.

```javascript
masonry.on('item:add', (data) => {
    console.log('Item(s) added:', data.item || data.items);
});
```

#### `item:remove`

Fired when item is removed.

```javascript
masonry.on('item:remove', (data) => {
    console.log('Item removed:', data.item);
});
```

#### `item:update`

Fired when item is updated.

```javascript
masonry.on('item:update', (data) => {
    console.log('Item updated:', data.itemId, data.updates);
});
```

#### `update`

Fired when configuration is updated.

```javascript
masonry.on('update', (data) => {
    console.log('Configuration updated:', data);
});
```

#### `clear`

Fired when all items are cleared.

```javascript
masonry.on('clear', () => {
    console.log('All items cleared');
});
```

#### `destroy`

Fired when masonry is destroyed.

```javascript
masonry.on('destroy', () => {
    console.log('Masonry destroyed');
});
```

## Algorithm

### Column Balancing

FlexMasonry uses a greedy algorithm to distribute items:

1. **Track Column Heights**: Maintain array of current column heights
2. **Find Shortest Column**: For each item, find the column with minimum height
3. **Add to Shortest**: Place item in shortest column
4. **Update Height**: Add item's height to that column's total

```javascript
distributeItems() {
    const columnHeights = new Array(columnCount).fill(0);

    items.forEach(item => {
        // Find shortest column
        const shortestIndex = columnHeights.indexOf(
            Math.min(...columnHeights)
        );

        // Add item to shortest column
        columns[shortestIndex].appendChild(item);

        // Update column height
        columnHeights[shortestIndex] += item.height;
    });
}
```

### Height Estimation

For best results, provide item heights:

```javascript
{
    id: 'item1',
    content: '...',
    height: 280  // Actual or estimated height in pixels
}
```

If no height is provided, default estimate (200px) is used.

### Reflow Behavior

Reflow is triggered by:
- Window resize (debounced)
- Breakpoint changes
- Item additions/removals
- Manual `reflow()` call
- ResizeObserver (if item size changes)

## Best Practices

### 1. Provide Item Heights

```javascript
// Good - provides height
{ id: '1', content: '...', height: 250 }

// Works but less accurate
{ id: '1', content: '...' }  // Uses default 200px
```

### 2. Use Lazy Loading for Many Images

```javascript
const gallery = new FlexMasonry('#gallery', {
    lazyLoad: true,
    items: images.map(img => ({
        id: img.id,
        content: `<img data-src="${img.url}" alt="${img.alt}" />`,
        height: img.height
    }))
});
```

### 3. Batch Add Items

```javascript
// Good - single reflow
masonry.addItems([item1, item2, item3]);

// Avoid - multiple reflows
masonry.addItem(item1);
masonry.addItem(item2);
masonry.addItem(item3);
```

### 4. Responsive Column Counts

```javascript
columns: {
    xs: 1,   // 1 column on mobile
    sm: 2,   // 2 columns on tablet
    md: 3,   // 3 columns on desktop
    lg: 4,   // 4 columns on large screens
    xl: 5    // 5 columns on extra large
}
```

### 5. Handle Infinite Scroll Carefully

```javascript
let loading = false;

window.addEventListener('scroll', () => {
    if (loading || !isNearBottom()) return;

    loading = true;
    loadMoreItems().then(items => {
        masonry.addItems(items);
        loading = false;
    });
});
```

### 6. Clean Up When Done

```javascript
// When removing masonry from page
masonry.destroy();
```

## Performance

### Optimization Tips

1. **Provide Heights**: Reduces layout thrashing
2. **Lazy Load**: Improves initial load time
3. **Limit Items**: Consider pagination or virtual scrolling for 1000+ items
4. **Debounced Reflow**: Automatically debounced (150ms)
5. **ResizeObserver**: Only observes when items change size

### Performance Benchmarks

- **100 items**: Smooth on all devices
- **500 items**: Good performance with lazy loading
- **1000+ items**: Consider virtual scrolling

### Memory Considerations

```javascript
// Clean up when component unmounted
componentWillUnmount() {
    masonry.destroy();
}
```

### Reflow Performance

Reflow is computationally inexpensive:
- O(n) where n = number of items
- Debounced to prevent excessive calls
- Only recalculates when necessary

## Browser Support

FlexMasonry requires:

- IntersectionObserver (for lazy loading) - IE11+ with polyfill
- ResizeObserver (for auto-reflow) - Modern browsers
- Flexbox - All modern browsers

**Polyfills needed for IE11:**
```html
<script src="intersection-observer-polyfill.js"></script>
<script src="resize-observer-polyfill.js"></script>
```

## Related Components

- **FlexGrid**: For uniform grid layouts
- **FlexStack**: For simple vertical/horizontal stacking
- **FlexCluster**: For horizontally wrapping items

## See Also

- [FlexGrid Documentation](../flex-grid.md)
- [Phase 3 Components Overview](../phase3-overview.md)
- [Performance Guide](../../guides/performance.md)
- [Lazy Loading Guide](../../guides/lazy-loading.md)
