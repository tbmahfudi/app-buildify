# FlexSidebar Component Guide

## Overview

**FlexSidebar** is a comprehensive sidebar layout component with automatic mobile/desktop behavior, multiple display modes, and advanced features like resizing, backdrop overlays, and keyboard navigation.

## Why FlexSidebar?

- **Responsive by Default**: Automatic mobile/desktop behavior based on breakpoints
- **Multiple Display Modes**: Overlay, push, reveal, and drawer modes
- **Resizable Sidebars**: Drag handles with min/max constraints
- **Dual Sidebar Support**: Left, right, or both sidebars simultaneously
- **Rich Interactions**: Backdrop overlay, keyboard navigation (Escape key)
- **Flexible Configuration**: Extensive options for customization
- **Zero Dependencies**: Works standalone or with other Flex components

## Basic Usage

### Simple Left Sidebar

```javascript
import FlexSidebar from './layout/flex-sidebar.js';

const layout = new FlexSidebar('#app', {
  position: 'left',
  width: { xs: '100%', md: '280px' },
  collapsible: true,
  content: {
    sidebar: document.querySelector('#nav'),
    main: document.querySelector('#content')
  }
});
```

### Admin Dashboard

```javascript
const dashboard = new FlexSidebar('#dashboard', {
  position: 'left',
  width: { md: '280px' },
  minWidth: '240px',
  maxWidth: '400px',
  resizable: true,
  sticky: true,
  mobileMode: 'overlay',
  desktopMode: 'push',
  content: {
    sidebar: navigationElement,
    main: contentElement
  }
});
```

## Configuration Options

### Positioning

```javascript
{
  position: 'left'  // left | right | both
}
```

For **both** sidebars:

```javascript
{
  position: 'both',
  sidebars: {
    left: {
      width: { md: '280px' },
      content: leftSidebarContent
    },
    right: {
      width: { lg: '240px' },
      content: rightSidebarContent,
      collapsible: true
    }
  }
}
```

### Width Control

```javascript
{
  // Responsive width
  width: {
    xs: '100%',   // Full width on mobile
    md: '280px',  // Fixed width on tablet+
    lg: '320px'   // Wider on desktop
  },

  // Min/max constraints
  minWidth: '240px',
  maxWidth: '400px'
}
```

### Display Modes

```javascript
{
  mobileMode: 'overlay',   // overlay | push | drawer
  desktopMode: 'push',     // push | overlay | reveal
  collapseBreakpoint: 'md' // Breakpoint where mobile mode activates
}
```

**Mode Descriptions**:
- **overlay**: Sidebar floats over content, uses backdrop
- **push**: Sidebar pushes content aside
- **reveal**: Content slides away to reveal fixed sidebar
- **drawer**: Like overlay but with scale animation on main content

### Responsive Behavior

```javascript
{
  collapsible: true,
  collapseBreakpoint: 'md',  // Below this: mobile mode, above: desktop mode
  defaultOpen: {
    xs: false,  // Closed on mobile
    md: true    // Open on desktop
  }
}
```

### Backdrop

```javascript
{
  backdrop: true,
  backdropColor: 'black',
  backdropOpacity: 0.5,
  closeOnBackdropClick: true,
  closeOnEscape: true
}
```

### Resizing

```javascript
{
  resizable: true,
  resizeHandle: true  // Show visual resize handle
}
```

### Sticky & Scrolling

```javascript
{
  sticky: true,
  stickyOffset: 0,      // Offset from top (e.g., for fixed header)
  scrollable: true,
  maxHeight: '100vh'
}
```

### Animation

```javascript
{
  animated: true,
  animationDuration: 300,  // milliseconds
  animations: {
    slide: true,   // Slide sidebar in/out
    fade: true,    // Fade backdrop
    scale: false   // Scale main content (drawer mode)
  }
}
```

### Content

```javascript
{
  content: {
    sidebar: element | html,
    main: element | html
  }
}
```

## Public API

### Methods

#### `open()`
Open the sidebar.

```javascript
layout.open();
```

#### `close()`
Close the sidebar.

```javascript
layout.close();
```

#### `toggle()`
Toggle sidebar state.

```javascript
layout.toggle();
```

#### `isOpen()`
Check if sidebar is currently open.

```javascript
if (layout.isOpen()) {
  console.log('Sidebar is open');
}
```

#### `setWidth(width, position)`
Change sidebar width.

```javascript
layout.setWidth('320px');

// For both sidebars
layout.setWidth('240px', 'left');
layout.setWidth('200px', 'right');
```

#### `setPosition(position)`
Change sidebar position.

```javascript
layout.setPosition('right');  // left | right
```

#### `setMode(mode)`
Change display mode for current breakpoint.

```javascript
layout.setMode('overlay');  // overlay | push | reveal | drawer
```

#### `updateContent(config)`
Update sidebar or main content.

```javascript
layout.updateContent({
  sidebar: newSidebarElement,
  main: newMainElement,
  position: 'left'  // For both sidebars mode
});
```

#### `enableResize(enabled)`
Enable or disable resize functionality.

```javascript
layout.enableResize(true);
```

#### `getElement()`
Get the layout DOM element.

```javascript
const element = layout.getElement();
```

#### `getSidebar(position)`
Get sidebar DOM element.

```javascript
const sidebar = layout.getSidebar('left');
```

#### `getMain()`
Get main content DOM element.

```javascript
const main = layout.getMain();
```

#### `destroy()`
Clean up and remove sidebar functionality.

```javascript
layout.destroy();
```

### Events

```javascript
// Sidebar opened
layout.on('open', () => {
  console.log('Sidebar opened');
});

// Sidebar closed
layout.on('close', () => {
  console.log('Sidebar closed');
});

// Resize started
layout.on('resize:start', (detail) => {
  console.log('Resize started:', detail.width);
});

// Resizing
layout.on('resize', (detail) => {
  console.log('Resizing:', detail.width);
});

// Resize ended
layout.on('resize:end', (detail) => {
  console.log('Resize ended:', detail.width);
});

// Updates (breakpoint changes, mode changes)
layout.on('update', (detail) => {
  console.log('Layout updated:', detail);
});
```

## Common Patterns

### Admin Dashboard

```javascript
const dashboard = new FlexSidebar('#admin-dashboard', {
  position: 'left',
  width: { xs: '100%', md: '280px', lg: '320px' },
  minWidth: '240px',
  maxWidth: '400px',
  resizable: true,
  collapsible: true,
  mobileMode: 'overlay',
  desktopMode: 'push',
  defaultOpen: { xs: false, md: true },
  backdrop: true,
  content: {
    sidebar: `
      <div class="h-full bg-gray-900 text-white">
        <div class="p-4 border-b border-gray-700">
          <h1 class="text-xl font-bold">Admin Panel</h1>
        </div>
        <nav class="p-4">
          <!-- Navigation items -->
        </nav>
      </div>
    `,
    main: document.querySelector('#dashboard-content')
  }
});

// Toggle button
document.querySelector('#menu-button').addEventListener('click', () => {
  dashboard.toggle();
});
```

### Documentation Site

```javascript
const docs = new FlexSidebar('#docs-layout', {
  position: 'left',
  width: { md: '280px', lg: '320px' },
  sticky: true,
  stickyOffset: 64,  // Account for fixed header
  scrollable: true,
  mobileMode: 'overlay',
  desktopMode: 'push',
  defaultOpen: { xs: false, lg: true },
  content: {
    sidebar: `
      <nav class="h-full bg-white border-r border-gray-200 p-6">
        <h2 class="font-bold text-lg mb-4">Documentation</h2>
        <ul class="space-y-2">
          <li><a href="#getting-started">Getting Started</a></li>
          <li><a href="#components">Components</a></li>
          <li><a href="#api">API Reference</a></li>
        </ul>
      </nav>
    `,
    main: document.querySelector('#docs-content')
  }
});
```

### E-commerce Filters

```javascript
const shop = new FlexSidebar('#shop-layout', {
  position: 'left',
  width: { xs: '100%', md: '280px' },
  mobileMode: 'overlay',
  desktopMode: 'push',
  defaultOpen: { xs: false, md: true },
  backdrop: true,
  closeOnBackdropClick: true,
  content: {
    sidebar: `
      <div class="h-full bg-white p-6">
        <h2 class="font-bold text-lg mb-4">Filters</h2>
        <div class="space-y-6">
          <!-- Filter controls -->
        </div>
      </div>
    `,
    main: document.querySelector('#product-grid')
  }
});

// Mobile filter button
document.querySelector('#filters-button').addEventListener('click', () => {
  shop.open();
});
```

### Email Client (Both Sidebars)

```javascript
const email = new FlexSidebar('#email-app', {
  position: 'both',
  sidebars: {
    left: {
      width: { md: '240px' },
      content: `
        <div class="h-full bg-gray-100 p-4">
          <h3 class="font-bold mb-4">Folders</h3>
          <ul class="space-y-2">
            <li><a href="#inbox">Inbox (24)</a></li>
            <li><a href="#sent">Sent</a></li>
            <li><a href="#drafts">Drafts</a></li>
          </ul>
        </div>
      `,
      resizable: true,
      minWidth: '200px',
      maxWidth: '320px'
    },
    right: {
      width: { lg: '300px' },
      content: `
        <div class="h-full bg-white border-l border-gray-200 p-4">
          <h3 class="font-bold mb-4">Message Preview</h3>
          <div id="message-preview">
            <!-- Message preview content -->
          </div>
        </div>
      `,
      collapsible: true,
      defaultOpen: { xs: false, lg: true }
    }
  },
  content: {
    main: document.querySelector('#message-list')
  }
});
```

### Settings Page

```javascript
const settings = new FlexSidebar('#settings-layout', {
  position: 'left',
  width: { md: '240px' },
  sticky: true,
  mobileMode: 'overlay',
  desktopMode: 'push',
  defaultOpen: { xs: false, md: true },
  content: {
    sidebar: `
      <nav class="h-full bg-white border-r border-gray-200 p-4">
        <ul class="space-y-1">
          <li><a href="#profile" class="block px-3 py-2 rounded hover:bg-gray-100">Profile</a></li>
          <li><a href="#security" class="block px-3 py-2 rounded hover:bg-gray-100">Security</a></li>
          <li><a href="#notifications" class="block px-3 py-2 rounded hover:bg-gray-100">Notifications</a></li>
          <li><a href="#billing" class="block px-3 py-2 rounded hover:bg-gray-100">Billing</a></li>
        </ul>
      </nav>
    `,
    main: document.querySelector('#settings-content')
  }
});
```

## Integration with Other Components

### With FlexSection

Main content area contains multiple sections:

```javascript
import FlexSection from './layout/flex-section.js';

const layout = new FlexSidebar('#app', {
  position: 'left',
  content: {
    sidebar: navElement,
    main: document.querySelector('#main')
  }
});

// Create sections in main area
new FlexSection('#hero', {
  variant: 'hero',
  slots: { body: { content: heroContent } }
});

new FlexSection('#content', {
  variant: 'content',
  slots: { body: { content: mainContent } }
});
```

### With FlexContainer

Use containers in main area for width control:

```javascript
import FlexContainer from './layout/flex-container.js';

const layout = new FlexSidebar('#app', {
  position: 'left',
  content: {
    sidebar: navElement,
    main: document.querySelector('#main')
  }
});

// Add container to main area
const container = new FlexContainer('#main', {
  preset: 'standard',
  gutter: true
});
```

### With FlexStack

Use stack for sidebar navigation:

```javascript
import { FlexStack } from './layout/flex-stack.js';

const nav = new FlexStack('#sidebar-nav', {
  direction: 'vertical',
  gap: 1,
  items: [
    { content: '<a href="#home">Home</a>' },
    { content: '<a href="#about">About</a>' },
    { content: '<a href="#contact">Contact</a>' }
  ]
});

const layout = new FlexSidebar('#app', {
  position: 'left',
  content: {
    sidebar: nav.getElement(),
    main: mainContent
  }
});
```

### With FlexGrid

Dashboard with stats grid in main area:

```javascript
import { FlexGrid } from './layout/flex-grid.js';

const stats = new FlexGrid('#stats-grid', {
  columns: { xs: 1, md: 2, lg: 3 },
  gap: 6,
  items: statCards
});

const layout = new FlexSidebar('#dashboard', {
  position: 'left',
  content: {
    sidebar: navElement,
    main: stats.getElement()
  }
});
```

## Advanced Techniques

### Dynamic Mode Switching

```javascript
const layout = new FlexSidebar('#app', {
  position: 'left',
  mobileMode: 'overlay',
  desktopMode: 'push'
});

// Switch to overlay mode on desktop (e.g., for temporary navigation)
document.querySelector('#overlay-mode-button').addEventListener('click', () => {
  layout.setMode('overlay');
});
```

### Persistent Sidebar State

```javascript
const layout = new FlexSidebar('#app', {
  position: 'left',
  defaultOpen: {
    md: localStorage.getItem('sidebarOpen') === 'true'
  }
});

// Save state on changes
layout.on('open', () => {
  localStorage.setItem('sidebarOpen', 'true');
});

layout.on('close', () => {
  localStorage.setItem('sidebarOpen', 'false');
});
```

### Persistent Resize Width

```javascript
const savedWidth = localStorage.getItem('sidebarWidth') || '280px';

const layout = new FlexSidebar('#app', {
  position: 'left',
  width: { md: savedWidth },
  resizable: true
});

// Save width on resize
layout.on('resize:end', (detail) => {
  localStorage.setItem('sidebarWidth', detail.width);
});
```

### Conditional Sidebar

```javascript
// Only show sidebar for authenticated users
if (user.isAuthenticated) {
  const layout = new FlexSidebar('#app', {
    position: 'left',
    content: {
      sidebar: navElement,
      main: mainElement
    }
  });
} else {
  // Full-width layout for unauthenticated users
  document.querySelector('#main').style.width = '100%';
}
```

### Multi-Level Navigation

```javascript
const layout = new FlexSidebar('#app', {
  position: 'left',
  width: { md: '280px' },
  content: {
    sidebar: `
      <nav class="h-full overflow-y-auto">
        <div class="p-4">
          <details class="mb-2">
            <summary class="font-semibold cursor-pointer">Dashboard</summary>
            <ul class="ml-4 mt-2 space-y-1">
              <li><a href="#overview">Overview</a></li>
              <li><a href="#analytics">Analytics</a></li>
            </ul>
          </details>

          <details class="mb-2">
            <summary class="font-semibold cursor-pointer">Settings</summary>
            <ul class="ml-4 mt-2 space-y-1">
              <li><a href="#profile">Profile</a></li>
              <li><a href="#security">Security</a></li>
            </ul>
          </details>
        </div>
      </nav>
    `,
    main: mainElement
  }
});
```

## Accessibility

### Keyboard Navigation

```javascript
const layout = new FlexSidebar('#app', {
  closeOnEscape: true  // ESC key closes sidebar
});

// Trap focus in sidebar when open (overlay mode)
layout.on('open', () => {
  const sidebar = layout.getSidebar();
  const focusableElements = sidebar.querySelectorAll(
    'a, button, input, textarea, select, details, [tabindex]:not([tabindex="-1"])'
  );

  if (focusableElements.length > 0) {
    focusableElements[0].focus();
  }
});
```

### ARIA Attributes

```javascript
const layout = new FlexSidebar('#app', {
  position: 'left',
  content: {
    sidebar: navElement,
    main: mainElement
  }
});

// Add ARIA attributes
const sidebar = layout.getSidebar();
sidebar.setAttribute('role', 'navigation');
sidebar.setAttribute('aria-label', 'Main navigation');

// Update aria-expanded on toggle
layout.on('open', () => {
  sidebar.setAttribute('aria-expanded', 'true');
});

layout.on('close', () => {
  sidebar.setAttribute('aria-expanded', 'false');
});
```

### Screen Reader Announcements

```javascript
const layout = new FlexSidebar('#app');

layout.on('open', () => {
  announce('Navigation menu opened');
});

layout.on('close', () => {
  announce('Navigation menu closed');
});

function announce(message) {
  const announcement = document.createElement('div');
  announcement.setAttribute('role', 'status');
  announcement.setAttribute('aria-live', 'polite');
  announcement.className = 'sr-only';
  announcement.textContent = message;
  document.body.appendChild(announcement);

  setTimeout(() => announcement.remove(), 1000);
}
```

### Skip Links

```html
<a href="#main-content" class="skip-link">
  Skip to main content
</a>

<div id="app">
  <!-- Sidebar -->
  <!-- Main content with id="main-content" -->
</div>
```

## Performance Considerations

- **Debounced Resize**: Resize handler uses debouncing for smooth performance
- **CSS Transforms**: Animations use transforms for GPU acceleration
- **Passive Event Listeners**: Scroll and resize listeners use passive mode
- **Efficient Breakpoint Detection**: Shared FlexResponsive singleton
- **Minimal Repaints**: Batch style updates to reduce layout thrashing

## Troubleshooting

### Sidebar not appearing

**Problem**: Sidebar doesn't show up on initialization.

**Solution**: Check if container element exists and content is provided:
```javascript
// Wrong: container doesn't exist
new FlexSidebar('#nonexistent', { /* ... */ });

// Right: verify element exists
if (document.querySelector('#app')) {
  new FlexSidebar('#app', {
    content: {
      sidebar: sidebarElement,
      main: mainElement
    }
  });
}
```

### Backdrop not showing

**Problem**: Backdrop doesn't appear in overlay mode.

**Solution**: Ensure backdrop is enabled and mode is overlay/drawer:
```javascript
{
  mobileMode: 'overlay',  // or 'drawer'
  backdrop: true
}
```

### Resize not working

**Problem**: Can't resize sidebar by dragging.

**Solution**: Enable resize and ensure handle is visible:
```javascript
{
  resizable: true,
  resizeHandle: true,
  minWidth: '240px',
  maxWidth: '400px'
}
```

### Content overlapping

**Problem**: Sidebar overlaps main content in push mode.

**Solution**: Check mode configuration and parent container:
```javascript
// Ensure desktopMode is 'push' not 'overlay'
{
  desktopMode: 'push'
}
```

### Sidebar stuck open/closed

**Problem**: Toggle doesn't work.

**Solution**: Check if sidebar instance is properly stored:
```javascript
// Wrong: instance lost
new FlexSidebar('#app', { /* ... */ });

// Right: store instance
const layout = new FlexSidebar('#app', { /* ... */ });

// Later:
layout.toggle();
```

## Browser Support

FlexSidebar works in all modern browsers:

- ✅ Chrome/Edge 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ iOS Safari 14+
- ✅ Android Chrome 90+

## Best Practices

1. **Use Appropriate Modes**: Overlay for mobile, push for desktop
2. **Meaningful Content**: Sidebar should contain navigation or filters
3. **Consistent Width**: Use standard widths (240px, 280px, 320px)
4. **Responsive Defaults**: Close on mobile, open on desktop
5. **Accessible Navigation**: Proper ARIA labels and keyboard support
6. **Test Touch Devices**: Ensure gestures work on mobile
7. **Persistent State**: Save open/closed and width preferences
8. **Clear Toggle Button**: Make it easy to open/close sidebar

## Related Components

- **FlexContainer**: Used in main content area for width control
- **FlexSection**: Main area often contains multiple sections
- **FlexStack**: Commonly used for sidebar navigation
- **FlexGrid**: Dashboard grids in main content area

## Further Reading

- [FlexContainer Guide](./FLEX_CONTAINER_GUIDE.md)
- [FlexSection Guide](./FLEX_SECTION_GUIDE.md)
- [FlexStack Documentation](./docs/FLEX_STACK.md)
- [BaseComponent Documentation](./docs/BASE_COMPONENT.md)
