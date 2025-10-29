# FlexContainer Component Guide

## Overview

**FlexContainer** is a responsive container component for controlling content width, alignment, and horizontal padding (gutters). It provides preset width configurations and custom breakpoint-based max-widths, making it easy to create consistent, responsive layouts.

## Why FlexContainer?

- **Consistent Width Control**: Preset configurations ensure consistent max-widths across your application
- **Responsive Gutters**: Automatic horizontal padding that adapts to screen size
- **Flexible Alignment**: Left, center, or right alignment with automatic margins
- **Breakout Support**: Allow specific children to escape container constraints
- **Zero Dependencies**: Works standalone or integrates with other components
- **Lightweight**: Simple, focused API with no bloat

## Basic Usage

### Simple Preset-Based Container

```javascript
import FlexContainer from './layout/flex-container.js';

// Standard container (1280px max-width)
const container = new FlexContainer('#content', {
  preset: 'standard',
  align: 'center',
  gutter: true
});
```

### Custom Width Configuration

```javascript
// Custom responsive widths
const container = new FlexContainer('#content', {
  maxWidth: {
    xs: '100%',
    sm: '640px',
    md: '768px',
    lg: '1024px',
    xl: '1280px',
    '2xl': '1400px'
  },
  padding: { xs: 4, md: 6, lg: 8 },
  align: 'center'
});
```

## Configuration Options

### Presets

FlexContainer provides four built-in presets:

| Preset | Max-Width | Use Case |
|--------|-----------|----------|
| **narrow** | 768px | Articles, blog posts, reading content |
| **standard** | 1280px | General page content, default layouts |
| **wide** | 1536px (1600px on 2xl) | Dashboards, data-heavy interfaces |
| **full** | 100% | Full-width layouts, no constraints |

```javascript
// Narrow container for reading
const article = new FlexContainer('#article', {
  preset: 'narrow',
  align: 'center',
  gutter: true
});

// Wide container for dashboards
const dashboard = new FlexContainer('#dashboard', {
  preset: 'wide',
  gutter: { xs: 4, lg: 6 }
});
```

### Width Control

```javascript
{
  // Option 1: Use preset
  preset: 'standard',  // narrow | standard | wide | full

  // Option 2: Custom max-width (string)
  maxWidth: '1200px',

  // Option 3: Responsive max-width (object)
  maxWidth: {
    xs: '100%',
    lg: '1200px',
    xl: '1400px'
  }
}
```

**Priority**: Custom `maxWidth` overrides `preset`.

### Alignment

Controls horizontal alignment of the container:

```javascript
{
  align: 'center'  // left | center | right
}
```

- **center**: `margin-left: auto; margin-right: auto` (default)
- **left**: `margin-right: auto`
- **right**: `margin-left: auto`

### Gutters (Horizontal Padding)

```javascript
{
  // Option 1: Default responsive gutters
  gutter: true,  // Uses built-in responsive scale

  // Option 2: Custom responsive gutters
  gutter: {
    xs: 4,   // 1rem (16px)
    md: 6,   // 1.5rem (24px)
    lg: 8    // 2rem (32px)
  },

  // Option 3: Uniform gutter
  padding: 6,

  // Option 4: Responsive padding
  padding: {
    xs: 4,
    lg: 10
  }
}
```

**Default Gutter Scale**:
- Mobile (xs): 4 (1rem / 16px)
- Tablet (md): 6 (1.5rem / 24px)
- Desktop (lg): 8 (2rem / 32px)

### Breakout Support

Allow specific children to escape the container's width constraints:

```javascript
{
  allowBreakout: true
}
```

When enabled, children can use negative margins to break out:

```html
<div id="container">
  <div>Contained content</div>
  <div class="-mx-4">Full-width breakout</div>
  <div>Back to contained</div>
</div>
```

## Public API

### Methods

#### `setPreset(preset)`
Change the container preset.

```javascript
container.setPreset('wide');  // narrow | standard | wide | full
```

#### `setAlign(align)`
Change the alignment.

```javascript
container.setAlign('left');  // left | center | right
```

#### `updatePadding(padding)`
Update gutters/padding.

```javascript
// Single value
container.updatePadding(8);

// Responsive
container.updatePadding({ xs: 4, lg: 10 });
```

#### `updateMaxWidth(maxWidth)`
Update max-width configuration.

```javascript
// String
container.updateMaxWidth('1200px');

// Responsive
container.updateMaxWidth({ xs: '100%', xl: '1400px' });
```

#### `enableBreakout(enabled)`
Enable or disable breakout support.

```javascript
container.enableBreakout(true);
```

#### `getComputedWidth()`
Get the actual width in pixels.

```javascript
const width = container.getComputedWidth();  // e.g., 1280
```

#### `getCurrentMaxWidth()`
Get max-width for the current breakpoint.

```javascript
const maxWidth = container.getCurrentMaxWidth();  // e.g., '1280px'
```

#### `getCurrentPadding()`
Get padding for the current breakpoint.

```javascript
const padding = container.getCurrentPadding();  // e.g., 6
```

#### `getElement()`
Get the container DOM element.

```javascript
const element = container.getElement();
```

#### `destroy()`
Clean up and remove all container functionality.

```javascript
container.destroy();
```

### Events

FlexContainer emits events through the BaseComponent event system:

```javascript
// Initialization
container.on('init', () => {
  console.log('Container initialized');
});

// Rendering complete
container.on('render', () => {
  console.log('Container rendered');
});

// Updates (breakpoint changes, configuration changes)
container.on('update', (detail) => {
  console.log('Container updated:', detail);
  // detail: { breakpoint, width, preset, align, padding, etc. }
});

// Destruction
container.on('destroy', () => {
  console.log('Container destroyed');
});
```

## Common Patterns

### Standard Page Content

```javascript
// Most common pattern: centered container with responsive gutters
const main = new FlexContainer('#main-content', {
  preset: 'standard',
  align: 'center',
  gutter: true
});
```

### Article/Blog Post

```javascript
// Narrow container for optimal reading experience
const article = new FlexContainer('#article', {
  preset: 'narrow',
  align: 'center',
  padding: { xs: 6, lg: 12 }  // Extra padding for readability
});
```

### Dashboard Layout

```javascript
// Wide container for data-heavy interfaces
const dashboard = new FlexContainer('#dashboard', {
  preset: 'wide',
  padding: { xs: 4, lg: 6 }
});
```

### Asymmetric Layout

```javascript
// Left-aligned container (uncommon but useful)
const sidebar = new FlexContainer('#sidebar-content', {
  preset: 'standard',
  align: 'left',
  gutter: false
});
```

### Breakout Sections

```javascript
// Container with full-width breakout sections
const content = new FlexContainer('#content', {
  preset: 'narrow',
  allowBreakout: true,
  gutter: true
});

// In HTML:
// <div id="content">
//   <div>Normal contained content</div>
//   <div class="-mx-4 bg-blue-600">Full-width section</div>
//   <div>Back to contained</div>
// </div>
```

### Responsive Width Changes

```javascript
// Different max-widths at different breakpoints
const container = new FlexContainer('#content', {
  maxWidth: {
    xs: '100%',       // Full width on mobile
    md: '768px',      // Narrow on tablet
    lg: '1024px',     // Medium on desktop
    xl: '1280px',     // Wide on large desktop
    '2xl': '1400px'   // Extra wide on 2xl
  },
  align: 'center',
  gutter: true
});
```

## Integration with Other Components

### With FlexSection

FlexSection can use FlexContainer internally for width control:

```javascript
import FlexSection from './layout/flex-section.js';

const section = new FlexSection('#hero', {
  variant: 'hero',
  width: 'contained',  // Uses FlexContainer internally
  slots: {
    body: { content: heroContent }
  }
});
```

### With FlexGrid

Wrap FlexGrid with FlexContainer for responsive width:

```javascript
import FlexContainer from './layout/flex-container.js';
import { FlexGrid } from './layout/flex-grid.js';

const container = new FlexContainer('#grid-wrapper', {
  preset: 'standard',
  align: 'center',
  gutter: true
});

const grid = new FlexGrid('#grid', {
  columns: { xs: 1, md: 2, lg: 3 },
  gap: 6,
  items: gridItems
});
```

### With FlexSidebar

Use FlexContainer in the main content area:

```javascript
import FlexSidebar from './layout/flex-sidebar.js';

const layout = new FlexSidebar('#app', {
  position: 'left',
  content: {
    sidebar: navContent,
    main: document.querySelector('#main')
  }
});

// Then wrap sections in the main area
const main = new FlexContainer('#main', {
  preset: 'standard',
  gutter: true
});
```

## Advanced Techniques

### Dynamic Preset Switching

```javascript
const container = new FlexContainer('#content', {
  preset: 'standard',
  align: 'center'
});

// Switch based on user preference
document.querySelector('#wide-mode-toggle').addEventListener('change', (e) => {
  container.setPreset(e.target.checked ? 'wide' : 'standard');
});
```

### Responsive Alignment

```javascript
// Different alignment at different breakpoints
// (Note: FlexContainer doesn't support responsive align directly,
// but you can achieve it with responsive utilities)

const container = new FlexContainer('#content', {
  preset: 'narrow',
  align: 'left'  // Default to left
});

// Use FlexResponsive to change alignment on breakpoint
import { getResponsive } from './utilities/flex-responsive.js';

const responsive = getResponsive();
responsive.onBreakpointChange((breakpoint) => {
  if (responsive.isAtLeast('md')) {
    container.setAlign('center');
  } else {
    container.setAlign('left');
  }
});
```

### Nested Containers

```javascript
// Outer container
const outer = new FlexContainer('#outer', {
  preset: 'wide',
  gutter: true
});

// Inner container (narrower than outer)
const inner = new FlexContainer('#inner', {
  preset: 'narrow',
  align: 'center',
  gutter: false  // No double-padding
});
```

### Container with Breakout Grid

```javascript
const container = new FlexContainer('#content', {
  preset: 'narrow',
  allowBreakout: true,
  gutter: true
});

// HTML structure:
// <div id="content">
//   <p>Article text...</p>
//
//   <!-- Full-width image gallery -->
//   <div class="-mx-4">
//     <div id="gallery-grid"></div>
//   </div>
//
//   <p>More article text...</p>
// </div>

const gallery = new FlexGrid('#gallery-grid', {
  columns: { xs: 2, md: 3, lg: 4 },
  gap: 2,
  items: images
});
```

## Accessibility

FlexContainer is a purely layout component and doesn't add ARIA attributes. However, ensure your content remains accessible:

```html
<!-- Good: Semantic structure -->
<main id="main-content">
  <article>
    <h1>Article Title</h1>
    <p>Content...</p>
  </article>
</main>

<script>
  new FlexContainer('#main-content', {
    preset: 'narrow',
    align: 'center'
  });
</script>
```

## Performance Considerations

- **Minimal DOM Manipulation**: FlexContainer only modifies the container element
- **Efficient Breakpoint Detection**: Uses FlexResponsive singleton for shared state
- **No Layout Thrashing**: Styles applied in batches, not individually
- **Debounced Resize**: Breakpoint changes are debounced by FlexResponsive

## Troubleshooting

### Container not centering

**Problem**: Container appears left-aligned despite `align: 'center'`.

**Solution**: Ensure parent has full width:
```css
#parent {
  width: 100%;
}
```

### Gutters not appearing

**Problem**: No horizontal padding visible.

**Solution**: Check if `gutter` is set and padding config is valid:
```javascript
// Wrong
{ gutter: false }

// Right
{ gutter: true }
// or
{ padding: { xs: 4, lg: 8 } }
```

### Breakout not working

**Problem**: Children with negative margins don't escape container.

**Solution**: Enable breakout and ensure negative margins match gutter:
```javascript
{ allowBreakout: true, gutter: true }

// In HTML, use matching negative margins
<div class="-mx-4">Breakout content</div>
```

### Max-width not applying

**Problem**: Container exceeds expected max-width.

**Solution**: Check if custom `maxWidth` is overriding preset:
```javascript
// Preset is ignored when maxWidth is set
{
  preset: 'narrow',    // Ignored!
  maxWidth: '1200px'   // This takes precedence
}
```

## Browser Support

FlexContainer works in all modern browsers:

- ✅ Chrome/Edge 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ iOS Safari 14+
- ✅ Android Chrome 90+

## Migration Guide

### From Bootstrap Container

```html
<!-- Bootstrap -->
<div class="container">
  Content
</div>

<!-- FlexContainer -->
<div id="content">
  Content
</div>

<script>
  new FlexContainer('#content', {
    preset: 'standard',  // Similar to Bootstrap .container
    gutter: true
  });
</script>
```

### From Tailwind Container

```html
<!-- Tailwind -->
<div class="container mx-auto px-4">
  Content
</div>

<!-- FlexContainer -->
<div id="content">
  Content
</div>

<script>
  new FlexContainer('#content', {
    preset: 'standard',
    align: 'center',  // mx-auto
    padding: 4        // px-4
  });
</script>
```

## Best Practices

1. **Use Presets First**: Start with presets, only use custom widths when needed
2. **Consistent Gutters**: Use default gutter scale for consistency
3. **Center by Default**: Most containers should be centered
4. **Breakout Sparingly**: Only use breakout when necessary for visual impact
5. **Avoid Nesting**: Multiple nested containers can cause layout issues
6. **Test Responsiveness**: Always test at multiple breakpoints

## Related Components

- **FlexSection**: Uses FlexContainer for section width control
- **FlexSidebar**: Main content area often uses FlexContainer
- **FlexGrid**: Commonly wrapped in FlexContainer
- **FlexResponsive**: Provides breakpoint detection for responsive behavior

## Further Reading

- [FlexSection Guide](./FLEX_SECTION_GUIDE.md)
- [FlexSidebar Guide](./FLEX_SIDEBAR_GUIDE.md)
- [BaseComponent Documentation](./docs/BASE_COMPONENT.md)
- [FlexResponsive Documentation](./docs/FLEX_RESPONSIVE.md)
