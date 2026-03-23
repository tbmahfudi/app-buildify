# FlexToolbar Component

Header/footer toolbar component with action groups, sticky positioning, and responsive overflow handling. Perfect for app headers, navigation bars, and action toolbars.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Basic Usage](#basic-usage)
- [Configuration Options](#configuration-options)
- [Examples](#examples)
- [API Reference](#api-reference)
- [Events](#events)
- [Theming](#theming)
- [Best Practices](#best-practices)
- [Accessibility](#accessibility)

## Overview

FlexToolbar provides a powerful way to create app headers, navigation bars, and action toolbars with consistent styling, flexible action groups, and responsive behavior. It supports light/dark themes, elevation shadows, sticky positioning, and organized action groups (left, center, right).

### Key Capabilities

- **Action Groups**: Organize actions into left, center, and right positions
- **Theme System**: Built-in light/dark themes or custom themes
- **Sticky Positioning**: Optional sticky top/bottom positioning
- **Elevation Shadows**: 6 levels of shadow depth (0-5)
- **Responsive Height**: Adjust toolbar height by breakpoint
- **Overflow Handling**: Auto, scroll, hidden, or menu modes
- **Dynamic Actions**: Add, remove, and update actions programmatically

## Features

- ✅ Position: top, bottom, or both
- ✅ Action groups: left, center, right positioning
- ✅ Sticky positioning with z-index control
- ✅ Responsive overflow handling
- ✅ Dividers between action groups
- ✅ Theming support (light, dark, custom)
- ✅ Title/branding section
- ✅ Dropdown menu integration
- ✅ Elevation/shadow support
- ✅ Event-driven architecture
- ✅ Extends BaseComponent

## Installation

```javascript
import FlexToolbar from './layout/flex-toolbar.js';
```

## Basic Usage

### Minimal Example

```javascript
const header = new FlexToolbar('#header', {
    position: 'top',
    sticky: true,
    actions: {
        left: [
            { content: '<button>Menu</button>' }
        ],
        right: [
            { content: '<button>Profile</button>' }
        ]
    }
});
```

### HTML Structure Required

```html
<header id="header"></header>
```

The component will populate the header with action groups.

## Configuration Options

### Default Configuration

```javascript
{
    position: 'top',           // top | bottom | both
    sticky: true,              // Sticky positioning
    stickyOffset: 0,           // Offset from top/bottom in px
    height: { xs: '56px', md: '64px' },  // Responsive height
    padding: { xs: 4, md: 6 }, // Responsive padding
    theme: 'light',            // light | dark | custom object
    elevation: 2,              // 0-5 (shadow depth)
    dividers: false,           // Show dividers between groups
    actions: {
        left: [],              // Left-aligned actions
        center: [],            // Center-aligned actions
        right: []              // Right-aligned actions
    },
    overflow: 'auto',          // auto | scroll | hidden | menu
    responsive: null,          // Responsive configuration
    tag: 'header',             // HTML tag
    classes: []                // Additional CSS classes
}
```

### Option Details

#### `position` (String)

Toolbar position. Options:
- `'top'` - Top of viewport (default)
- `'bottom'` - Bottom of viewport
- `'both'` - Not currently implemented

```javascript
position: 'top'
```

#### `sticky` (Boolean)

Whether toolbar should stick to position during scroll.

```javascript
sticky: true  // Sticks to top/bottom
sticky: false // Scrolls with content
```

#### `stickyOffset` (Number)

Offset from top/bottom edge in pixels when sticky.

```javascript
stickyOffset: 0    // No offset (default)
stickyOffset: 60   // 60px from edge
```

#### `height` (String|Object)

Toolbar height. Can be responsive.

```javascript
height: '64px'                     // Fixed height
height: { xs: '56px', md: '64px' } // Responsive
```

#### `padding` (Number|Object)

Horizontal padding. Can be responsive.

```javascript
padding: 6                    // Spacing scale
padding: { xs: 4, md: 6 }     // Responsive
```

#### `theme` (String|Object)

Color theme. Built-in themes or custom object.

Built-in themes:
- `'light'` - Light background, dark text
- `'dark'` - Dark background, light text

```javascript
theme: 'light'  // Use light theme

// Custom theme
theme: {
    background: '#1a202c',
    color: '#ffffff',
    border: '#2d3748'
}
```

#### `elevation` (Number)

Shadow depth level (0-5). Higher = deeper shadow.

```javascript
elevation: 0  // No shadow
elevation: 2  // Default shadow
elevation: 5  // Deep shadow
```

#### `dividers` (Boolean)

Show vertical dividers between action groups.

```javascript
dividers: true   // Show dividers
dividers: false  // No dividers (default)
```

#### `actions` (Object)

Actions organized by position (left, center, right).

```javascript
actions: {
    left: [
        {
            id: 'menu',
            content: '<button>Menu</button>',
            classes: ['custom-class'],
            style: { color: 'red' }
        }
    ],
    center: [
        { content: '<h1>Title</h1>' }
    ],
    right: [
        { content: '<button>Profile</button>' }
    ]
}
```

Action object properties:
- `id` (String): Unique identifier (auto-generated if not provided)
- `content` (String|HTMLElement|Component): Action content
- `classes` (Array): Additional CSS classes
- `style` (Object): Inline styles

#### `overflow` (String)

How to handle overflow when toolbar is too narrow. Options:
- `'auto'` - Browser default
- `'scroll'` - Horizontal scrollbar
- `'hidden'` - Hide overflow
- `'menu'` - Collapse to menu (not fully implemented)

```javascript
overflow: 'scroll'
```

#### `responsive` (Object)

Responsive configuration for different actions at different breakpoints.

```javascript
responsive: {
    actions: {
        xs: {
            left: [{ content: '<button>☰</button>' }],
            right: [{ content: '<button>👤</button>' }]
        },
        md: {
            left: [
                { content: '<button>☰</button>' },
                { content: '<h1>App</h1>' }
            ],
            right: [
                { content: '<button>Search</button>' },
                { content: '<button>Profile</button>' }
            ]
        }
    }
}
```

## Examples

### Example 1: App Header

```javascript
const header = new FlexToolbar('#app-header', {
    position: 'top',
    sticky: true,
    theme: 'light',
    elevation: 2,
    height: { xs: '56px', md: '64px' },
    actions: {
        left: [
            {
                id: 'menu',
                content: `<button class="icon-button">
                    <i class="icon-menu"></i>
                </button>`
            },
            {
                id: 'logo',
                content: `<div class="logo">
                    <img src="logo.svg" alt="App Logo" />
                    <span>MyApp</span>
                </div>`
            }
        ],
        right: [
            {
                id: 'search',
                content: `<button class="icon-button">
                    <i class="icon-search"></i>
                </button>`
            },
            {
                id: 'notifications',
                content: `<button class="icon-button">
                    <i class="icon-bell"></i>
                    <span class="badge">3</span>
                </button>`
            },
            {
                id: 'profile',
                content: `<button class="avatar">
                    <img src="avatar.jpg" alt="User" />
                </button>`
            }
        ]
    }
});
```

### Example 2: Editor Toolbar

```javascript
const editorToolbar = new FlexToolbar('#editor-toolbar', {
    position: 'top',
    sticky: false,
    theme: 'light',
    elevation: 1,
    dividers: true,
    actions: {
        left: [
            {
                id: 'bold',
                content: '<button title="Bold"><i class="icon-bold"></i></button>'
            },
            {
                id: 'italic',
                content: '<button title="Italic"><i class="icon-italic"></i></button>'
            },
            {
                id: 'underline',
                content: '<button title="Underline"><i class="icon-underline"></i></button>'
            }
        ],
        center: [
            {
                id: 'align-left',
                content: '<button><i class="icon-align-left"></i></button>'
            },
            {
                id: 'align-center',
                content: '<button><i class="icon-align-center"></i></button>'
            },
            {
                id: 'align-right',
                content: '<button><i class="icon-align-right"></i></button>'
            }
        ],
        right: [
            {
                id: 'link',
                content: '<button><i class="icon-link"></i></button>'
            },
            {
                id: 'image',
                content: '<button><i class="icon-image"></i></button>'
            }
        ]
    }
});
```

### Example 3: Bottom Action Bar

```javascript
const bottomBar = new FlexToolbar('#bottom-bar', {
    position: 'bottom',
    sticky: true,
    theme: 'dark',
    elevation: 3,
    actions: {
        center: [
            {
                id: 'cancel',
                content: '<button class="btn btn-secondary">Cancel</button>'
            },
            {
                id: 'save',
                content: `<button class="btn btn-primary">
                    <i class="icon-check"></i>
                    Save Changes
                </button>`
            }
        ]
    }
});
```

### Example 4: Mobile Bottom Navigation

```javascript
const mobileNav = new FlexToolbar('#mobile-nav', {
    position: 'bottom',
    sticky: false,
    theme: 'light',
    elevation: 2,
    height: '64px',
    actions: {
        left: [
            {
                id: 'home',
                content: `<button class="nav-item active">
                    <i class="icon-home"></i>
                    <span>Home</span>
                </button>`
            }
        ],
        center: [
            {
                id: 'search',
                content: `<button class="nav-item">
                    <i class="icon-search"></i>
                    <span>Search</span>
                </button>`
            },
            {
                id: 'favorites',
                content: `<button class="nav-item">
                    <i class="icon-heart"></i>
                    <span>Favorites</span>
                </button>`
            }
        ],
        right: [
            {
                id: 'profile',
                content: `<button class="nav-item">
                    <i class="icon-user"></i>
                    <span>Profile</span>
                </button>`
            }
        ]
    }
});
```

### Example 5: Custom Theme

```javascript
const customToolbar = new FlexToolbar('#custom-toolbar', {
    position: 'top',
    sticky: true,
    theme: {
        background: '#6366f1',  // Indigo
        color: '#ffffff',        // White
        border: '#4f46e5'        // Darker indigo
    },
    elevation: 3,
    actions: {
        left: [
            { content: '<h1 style="color: white;">Custom Theme</h1>' }
        ],
        right: [
            { content: '<button class="btn-white">Action</button>' }
        ]
    }
});
```

## API Reference

### Methods

#### `addAction(position, action, index)`

Add action to a group.

```javascript
toolbar.addAction('right', {
    id: 'settings',
    content: '<button>Settings</button>'
});

// Insert at specific index
toolbar.addAction('left', action, 0);
```

**Parameters:**
- `position` (String): 'left', 'center', or 'right'
- `action` (Object): Action configuration
- `index` (Number, optional): Position to insert

**Returns:** void

#### `removeAction(position, actionId)`

Remove action by ID.

```javascript
toolbar.removeAction('right', 'settings');
```

**Parameters:**
- `position` (String): 'left', 'center', or 'right'
- `actionId` (String): ID of action to remove

**Returns:** void

#### `updateAction(position, actionId, updates)`

Update existing action.

```javascript
toolbar.updateAction('left', 'menu', {
    content: '<button class="active">Menu</button>'
});
```

**Parameters:**
- `position` (String): 'left', 'center', or 'right'
- `actionId` (String): ID of action to update
- `updates` (Object): Properties to update

**Returns:** void

#### `setTheme(theme)`

Change toolbar theme.

```javascript
toolbar.setTheme('dark');

// Custom theme
toolbar.setTheme({
    background: '#1a202c',
    color: '#ffffff',
    border: '#2d3748'
});
```

**Parameters:**
- `theme` (String|Object): Theme name or custom theme object

**Returns:** void

#### `setElevation(elevation)`

Update shadow elevation.

```javascript
toolbar.setElevation(4);
```

**Parameters:**
- `elevation` (Number): Elevation level (0-5)

**Returns:** void

#### `setSticky(sticky)`

Toggle sticky positioning.

```javascript
toolbar.setSticky(true);
```

**Parameters:**
- `sticky` (Boolean): Whether toolbar should be sticky

**Returns:** void

#### `getActionElement(position, actionId)`

Get action's DOM element.

```javascript
const element = toolbar.getActionElement('right', 'profile');
```

**Parameters:**
- `position` (String): 'left', 'center', or 'right'
- `actionId` (String): ID of action

**Returns:** HTMLElement|null

#### `getElement()`

Get toolbar container element.

```javascript
const container = toolbar.getElement();
```

**Returns:** HTMLElement

#### `destroy()`

Clean up and remove toolbar.

```javascript
toolbar.destroy();
```

**Returns:** void

## Events

### Available Events

#### `init`

Fired when toolbar is initialized.

```javascript
toolbar.on('init', () => {
    console.log('Toolbar initialized');
});
```

#### `render`

Fired when toolbar is rendered.

```javascript
toolbar.on('render', () => {
    console.log('Toolbar rendered');
});
```

#### `action:add`

Fired when action is added.

```javascript
toolbar.on('action:add', (data) => {
    console.log('Action added:', data.position, data.action);
});
```

#### `action:remove`

Fired when action is removed.

```javascript
toolbar.on('action:remove', (data) => {
    console.log('Action removed:', data.position, data.action);
});
```

#### `action:update`

Fired when action is updated.

```javascript
toolbar.on('action:update', (data) => {
    console.log('Action updated:', data.position, data.actionId);
});
```

#### `update`

Fired when configuration is updated.

```javascript
toolbar.on('update', (data) => {
    console.log('Toolbar updated:', data);
});
```

#### `destroy`

Fired when toolbar is destroyed.

```javascript
toolbar.on('destroy', () => {
    console.log('Toolbar destroyed');
});
```

## Theming

### Built-in Themes

FlexToolbar includes two built-in themes:

#### Light Theme

```javascript
{
    background: '#ffffff',
    color: '#1f2937',
    border: '#e5e7eb'
}
```

#### Dark Theme

```javascript
{
    background: '#1f2937',
    color: '#ffffff',
    border: '#374151'
}
```

### Custom Themes

Create custom themes by providing a theme object:

```javascript
const toolbar = new FlexToolbar('#toolbar', {
    theme: {
        background: '#7c3aed',  // Purple background
        color: '#ffffff',        // White text
        border: '#6d28d9'        // Darker purple border
    }
});
```

### Dynamic Theme Switching

```javascript
// Toggle between light and dark
let isDark = false;

toggleButton.addEventListener('click', () => {
    isDark = !isDark;
    toolbar.setTheme(isDark ? 'dark' : 'light');
});
```

## Best Practices

### 1. Use Semantic Action IDs

```javascript
// Good
{ id: 'user-profile', content: '...' }

// Avoid
{ id: 'action1', content: '...' }
```

### 2. Group Related Actions

```javascript
actions: {
    left: [/* Navigation and branding */],
    center: [/* Primary actions */],
    right: [/* User and settings */]
}
```

### 3. Responsive Height for Better Mobile UX

```javascript
height: {
    xs: '56px',  // Smaller on mobile
    md: '64px'   // Larger on desktop
}
```

### 4. Use Elevation Appropriately

```javascript
elevation: 0  // Flat, no distinction
elevation: 2  // Standard header (recommended)
elevation: 4  // Modal or overlay header
```

### 5. Consider Sticky Offset for Fixed Elements

```javascript
// If you have a notification bar above the toolbar
stickyOffset: 40  // Height of notification bar
```

### 6. Clean Up Event Listeners

```javascript
// When toolbar is removed
toolbar.destroy();
```

## Accessibility

### Landmark Roles

Use semantic HTML tags:

```javascript
tag: 'header'  // For page header
tag: 'nav'     // For navigation toolbar
tag: 'footer'  // For page footer
```

### Skip Links

Provide skip links for keyboard users:

```html
<a href="#main-content" class="skip-link">Skip to main content</a>
<header id="toolbar"></header>
```

### ARIA Labels

Add labels to icon-only buttons:

```javascript
actions: {
    right: [
        {
            content: '<button aria-label="Search"><i class="icon-search"></i></button>'
        }
    ]
}
```

### Keyboard Navigation

Ensure all actions are keyboard accessible:

```javascript
// Actions should use <button> or <a> elements
{ content: '<button>Menu</button>' }  // ✓ Good
{ content: '<div>Menu</div>' }        // ✗ Bad
```

### Focus Management

Maintain visible focus indicators:

```css
.flex-toolbar button:focus {
    outline: 2px solid var(--focus-color);
    outline-offset: 2px;
}
```

## Browser Support

FlexToolbar uses modern CSS features:

- Chrome/Edge: Latest 2 versions
- Firefox: Latest 2 versions
- Safari: Latest 2 versions
- iOS Safari: Latest 2 versions

Sticky positioning is supported in all modern browsers.

## Performance Considerations

1. **Action Count**: Keep action groups reasonable (< 10 actions per group)
2. **Responsive Updates**: Automatically debounced
3. **Sticky Performance**: Uses CSS `position: sticky` for optimal performance
4. **Shadow Rendering**: Elevation shadows use CSS box-shadow (GPU accelerated)

## Related Components

- **FlexCluster**: For grouping buttons and tags without toolbar structure
- **FlexContainer**: For constraining toolbar content width
- **FlexSection**: For full-width header sections

## See Also

- [FlexCluster Documentation](./flex-cluster.md)
- [Phase 3 Components Overview](../phase3-overview.md)
- [Theming Guide](../../guides/theming.md)
