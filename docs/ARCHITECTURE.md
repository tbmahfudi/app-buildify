# Flex Component Library - Architecture

This document provides a comprehensive overview of the Flex Component Library architecture, design patterns, and implementation details.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Core Concepts](#core-concepts)
- [Component Hierarchy](#component-hierarchy)
- [Design Patterns](#design-patterns)
- [Module System](#module-system)
- [Event System](#event-system)
- [Responsive System](#responsive-system)
- [State Management](#state-management)
- [Rendering Pipeline](#rendering-pipeline)
- [Extension Points](#extension-points)

## Architecture Overview

The Flex Component Library follows a **component-based architecture** with clear separation of concerns, event-driven communication, and a modular design that supports tree-shaking and lazy loading.

### Key Principles

1. **Component Encapsulation**: Each component is self-contained with its own state and lifecycle
2. **Event-Driven Communication**: Components communicate via events, not direct references
3. **Composition Over Inheritance**: Components can be composed to create complex UIs
4. **Responsive by Default**: Mobile-first responsive behavior built into core
5. **Extensibility**: Easy to extend and customize via inheritance or composition
6. **Zero Dependencies**: Pure vanilla JavaScript, works anywhere

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Application Layer                       │
│  (Your code using Flex components)                          │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────┼─────────────────────────────────┐
│                  Component Layer                             │
├──────────────────┬────────┴─────────┬───────────────────────┤
│   UI Components  │ Layout Components│ Advanced Components   │
│   - FlexCard     │ - FlexStack      │ - FlexCluster         │
│   - FlexModal    │ - FlexGrid       │ - FlexToolbar         │
│   - FlexTabs     │ - FlexContainer  │ - FlexMasonry         │
│                  │ - FlexSection    │ - FlexSplitPane       │
│                  │ - FlexSidebar    │                       │
└──────────────────┴──────────────────┴───────────────────────┘
                            │
┌───────────────────────────┼─────────────────────────────────┐
│                      Core Layer                              │
├──────────────────────────┬──────────────────────────────────┤
│   BaseComponent          │   FlexResponsive (Singleton)     │
│   - Lifecycle            │   - Breakpoint Detection         │
│   - Event Emitter        │   - Responsive Utilities         │
│   - State Management     │   - Window Resize Handling       │
└──────────────────────────┴──────────────────────────────────┘
                            │
┌───────────────────────────┼─────────────────────────────────┐
│                   Utilities Layer                            │
│   - ui-utils.js (Toast, helpers)                            │
│   - DOM manipulation utilities                               │
└─────────────────────────────────────────────────────────────┘
```

## Core Concepts

### 1. Component Lifecycle

Every component follows a consistent lifecycle:

```javascript
class Component extends BaseComponent {
    constructor(element, options) {
        super(element, options);
        // 1. INITIALIZATION
        // - Merge options with defaults
        // - Store references
        // - Set initial state

        this.init();
        // 2. SETUP
        // - Create DOM structure
        // - Attach event listeners
        // - Initialize child components

        this.render();
        // 3. RENDER
        // - Generate/update DOM
        // - Apply styles
        // - Emit 'render' event
    }

    update(options) {
        // 4. UPDATE
        // - Merge new options
        // - Re-render if needed
        // - Emit 'update' event
    }

    destroy() {
        // 5. CLEANUP
        // - Remove event listeners
        // - Clean up child components
        // - Remove from DOM
        // - Emit 'destroy' event
        super.destroy();
    }
}
```

### 2. BaseComponent

All components extend `BaseComponent`, which provides:

**Lifecycle Management:**
```javascript
constructor(element, options) {
    this.element = element;
    this.options = this.mergeOptions(options);
    this.state = {};
    this.listeners = new Map();
}
```

**Event Emitter:**
```javascript
emit(event, data) {
    if (this.listeners.has(event)) {
        this.listeners.get(event).forEach(cb => cb(data));
    }
}

on(event, callback) {
    if (!this.listeners.has(event)) {
        this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
}
```

**Option Merging:**
```javascript
mergeOptions(options) {
    return {
        ...this.constructor.DEFAULTS,
        ...options
    };
}
```

**Element Management:**
```javascript
getElement() {
    return this.element;
}

setElement(element) {
    this.element = element;
}
```

### 3. Component Types

#### Layout Components
Focus on organizing and structuring content:
- **FlexStack**: Linear layouts (vertical/horizontal)
- **FlexGrid**: Multi-column grid layouts
- **FlexContainer**: Max-width containers
- **FlexSection**: Full-width page sections
- **FlexSidebar**: Collapsible sidebar layouts

#### Advanced Layout Components
Complex layout patterns:
- **FlexCluster**: Horizontal grouping with wrapping
- **FlexToolbar**: Header/footer toolbars
- **FlexMasonry**: Pinterest-style masonry grids
- **FlexSplitPane**: Resizable split layouts

#### UI Components
User interface elements:
- **FlexCard**: Content cards
- **FlexModal**: Modal dialogs
- **FlexTabs**: Tab navigation

## Component Hierarchy

### Inheritance Chain

```
Object
  └─ BaseComponent
       ├─ FlexStack
       ├─ FlexGrid
       ├─ FlexCard
       ├─ FlexModal
       ├─ FlexTabs
       ├─ FlexContainer
       ├─ FlexSection
       ├─ FlexSidebar
       ├─ FlexCluster
       ├─ FlexToolbar
       ├─ FlexMasonry
       └─ FlexSplitPane
```

### Composition Patterns

Components can be composed to create complex UIs:

```javascript
// FlexGrid contains FlexCard instances
const grid = new FlexGrid('#grid', {
    columns: { xs: 1, md: 3 },
    items: []
});

// Create cards and add to grid
for (let i = 0; i < 6; i++) {
    const card = new FlexCard(document.createElement('div'), {
        title: `Card ${i}`,
        content: `<p>Content ${i}</p>`
    });

    grid.addItem({
        id: `card-${i}`,
        content: card.getElement()
    });
}
```

```javascript
// FlexSection contains FlexStack
const section = new FlexSection('#section', {
    variant: 'content',
    slots: {
        body: {
            content: (() => {
                const stack = new FlexStack(document.createElement('div'), {
                    direction: 'vertical',
                    gap: 4,
                    items: [...]
                });
                return stack.getElement();
            })()
        }
    }
});
```

## Design Patterns

### 1. Singleton Pattern (FlexResponsive)

```javascript
class FlexResponsive {
    constructor() {
        if (FlexResponsive.instance) {
            return FlexResponsive.instance;
        }
        FlexResponsive.instance = this;

        this.breakpoints = {
            xs: 0, sm: 640, md: 768, lg: 1024, xl: 1280
        };

        this.init();
    }

    static getInstance() {
        if (!FlexResponsive.instance) {
            FlexResponsive.instance = new FlexResponsive();
        }
        return FlexResponsive.instance;
    }
}

export default FlexResponsive.getInstance();
```

**Benefits:**
- Single source of truth for breakpoints
- Centralized window resize handling
- Shared event listeners across all components

### 2. Factory Pattern (Component Creation)

```javascript
class ComponentFactory {
    static create(type, element, options) {
        switch(type) {
            case 'card':
                return new FlexCard(element, options);
            case 'modal':
                return new FlexModal(options);
            case 'grid':
                return new FlexGrid(element, options);
            default:
                throw new Error(`Unknown component type: ${type}`);
        }
    }
}
```

### 3. Observer Pattern (Event System)

```javascript
// Component emits events
class FlexModal extends BaseComponent {
    show() {
        this.element.classList.add('active');
        this.emit('show');
    }

    hide() {
        this.element.classList.remove('active');
        this.emit('hide');
    }
}

// Application observes events
const modal = new FlexModal({ ... });

modal.on('show', () => {
    console.log('Modal shown');
});

modal.on('hide', () => {
    console.log('Modal hidden');
});
```

### 4. Builder Pattern (Fluent API)

```javascript
// Fluent configuration
const sidebar = new FlexSidebar('#app', {
    position: 'left',
    width: '280px'
})
    .setCollapsible(true)
    .setBackdrop(true)
    .toggle();
```

### 5. Strategy Pattern (Responsive Behavior)

```javascript
class ResponsiveStrategy {
    apply(value, breakpoint) {
        if (typeof value === 'object') {
            // Responsive object: { xs: 1, md: 2, lg: 3 }
            const breakpoints = ['xl', 'lg', 'md', 'sm', 'xs'];
            for (const bp of breakpoints) {
                if (FlexResponsive.isAbove(bp) && value[bp] !== undefined) {
                    return value[bp];
                }
            }
            return value.xs || value[Object.keys(value)[0]];
        }
        // Static value
        return value;
    }
}
```

## Module System

### ES6 Modules

All components use ES6 module syntax:

```javascript
// Exporting
export default class FlexCard extends BaseComponent { }

// Named exports
export { FlexCard, FlexModal, FlexTabs };

// Importing
import FlexCard from './components/flex-card.js';
import { FlexModal } from './components/flex-modal.js';
```

### Module Structure

```
frontend/assets/js/
├── core/
│   ├── base-component.js       # Base class for all components
│   └── flex-responsive.js      # Responsive singleton
├── components/
│   ├── flex-card.js            # Card component
│   ├── flex-modal.js           # Modal component
│   └── flex-tabs.js            # Tabs component
├── layout/
│   ├── flex-stack.js           # Stack layout
│   ├── flex-grid.js            # Grid layout
│   ├── flex-container.js       # Container layout
│   ├── flex-section.js         # Section layout
│   ├── flex-sidebar.js         # Sidebar layout
│   ├── flex-cluster.js         # Cluster layout
│   ├── flex-toolbar.js         # Toolbar layout
│   ├── flex-masonry.js         # Masonry layout
│   └── flex-split-pane.js      # Split pane layout
└── ui-utils.js                 # Utility functions
```

### Dependency Graph

```
FlexCard ──────┐
FlexModal ─────┼──> BaseComponent ──> (no dependencies)
FlexTabs ──────┘

FlexStack ─────┐
FlexGrid ──────┼──> BaseComponent + FlexResponsive
FlexContainer ─┤
FlexSection ───┤
FlexSidebar ───┤
FlexCluster ───┤
FlexToolbar ───┤
FlexMasonry ───┤
FlexSplitPane ─┘

FlexResponsive ──> (no dependencies)
```

## Event System

### Event Flow

```
User Action
    │
    ├──> DOM Event (click, input, etc.)
    │        │
    │        └──> Component Method
    │                  │
    │                  └──> this.emit(event, data)
    │                            │
    │                            └──> Event Listeners
    │                                      │
    │                                      └──> Callbacks
    │
    └──> Application Code
```

### Standard Events

Every component emits these lifecycle events:

- `init` - Component initialized
- `render` - Component rendered
- `update` - Configuration updated
- `destroy` - Component destroyed

### Component-Specific Events

**FlexModal:**
- `show` - Modal shown
- `hide` - Modal hidden
- `backdrop-click` - Backdrop clicked

**FlexTabs:**
- `tab-change` - Active tab changed
- `tab-add` - Tab added
- `tab-remove` - Tab removed

**FlexSidebar:**
- `open` - Sidebar opened
- `close` - Sidebar closed
- `resize` - Sidebar resized

**FlexSplitPane:**
- `resize:start` - Resize started
- `resize` - Resizing
- `resize:end` - Resize ended

### Event Example

```javascript
const modal = new FlexModal({
    title: 'Example',
    content: '<p>Content</p>'
});

// Listen to events
modal.on('show', () => {
    console.log('Modal is now visible');
    // Track analytics
    trackEvent('modal_shown', { title: 'Example' });
});

modal.on('hide', () => {
    console.log('Modal is now hidden');
    // Clean up resources
    cleanupResources();
});

modal.on('backdrop-click', () => {
    console.log('User clicked outside modal');
});

// Show the modal
modal.show();
```

## Responsive System

### Breakpoint System

```javascript
const breakpoints = {
    xs: 0,      // Mobile (< 640px)
    sm: 640,    // Large mobile/small tablet
    md: 768,    // Tablet
    lg: 1024,   // Desktop
    xl: 1280    // Large desktop
};
```

### Responsive Values

Components accept responsive values as objects:

```javascript
// Single value (all breakpoints)
{ gap: 4 }

// Responsive values
{ gap: { xs: 2, md: 4, lg: 6 } }

// Responsive columns
{ columns: { xs: 1, sm: 2, md: 3, lg: 4 } }

// Responsive height
{ height: { xs: '56px', md: '64px' } }
```

### Resolution Algorithm

```javascript
function resolveResponsiveValue(value, currentBreakpoint) {
    if (typeof value !== 'object') {
        return value;  // Static value
    }

    // Find the appropriate value for current breakpoint
    const breakpoints = ['xl', 'lg', 'md', 'sm', 'xs'];
    const currentIndex = breakpoints.indexOf(currentBreakpoint);

    // Search from current breakpoint down to xs
    for (let i = currentIndex; i < breakpoints.length; i++) {
        const bp = breakpoints[i];
        if (value[bp] !== undefined) {
            return value[bp];
        }
    }

    // Fallback to first available value
    return value[breakpoints[0]] || value.xs;
}
```

### Breakpoint Detection

```javascript
import FlexResponsive from './core/flex-responsive.js';

// Get current breakpoint
const current = FlexResponsive.getCurrentBreakpoint(); // 'md'

// Check if above/below breakpoint
if (FlexResponsive.isAbove('md')) {
    // Desktop layout
}

if (FlexResponsive.isBelow('md')) {
    // Mobile layout
}

// Listen for breakpoint changes
FlexResponsive.on('breakpoint', (breakpoint) => {
    console.log('Breakpoint changed to:', breakpoint);
});
```

## State Management

### Component State

Each component manages its own local state:

```javascript
class FlexTabs extends BaseComponent {
    constructor(element, options) {
        super(element, options);

        this.state = {
            activeTab: options.defaultTab || (options.tabs[0]?.id),
            tabs: options.tabs || []
        };
    }

    setActiveTab(tabId) {
        const oldTab = this.state.activeTab;
        this.state.activeTab = tabId;

        this.render();
        this.emit('tab-change', { from: oldTab, to: tabId });
    }
}
```

### State Persistence

Components can persist state to localStorage:

```javascript
class FlexSplitPane extends BaseComponent {
    saveState() {
        if (this.options.persist) {
            const sizes = this.getSizes();
            localStorage.setItem(
                this.options.persistKey,
                JSON.stringify(sizes)
            );
        }
    }

    loadState() {
        if (this.options.persist) {
            const saved = localStorage.getItem(this.options.persistKey);
            if (saved) {
                return JSON.parse(saved);
            }
        }
        return null;
    }
}
```

### State Update Pattern

```javascript
// 1. Update state
this.state.value = newValue;

// 2. Re-render if needed
this.render();

// 3. Emit event
this.emit('update', { value: newValue });
```

## Rendering Pipeline

### Render Flow

```
1. Constructor
    │
    ├─> mergeOptions()
    ├─> init()
    └─> render()
        │
        ├─> createElement() or selectElement()
        ├─> applyClasses()
        ├─> applyStyles()
        ├─> renderContent()
        ├─> attachEventListeners()
        └─> emit('render')

2. Update (user action or API call)
    │
    ├─> update(newOptions)
    ├─> mergeOptions(newOptions)
    ├─> render()
    └─> emit('update')

3. Destroy
    │
    ├─> removeEventListeners()
    ├─> destroyChildComponents()
    ├─> removeFromDOM()
    └─> emit('destroy')
```

### Virtual DOM (Not Used)

**Why not virtual DOM?**
- Direct DOM manipulation is fast for our use case
- Components are relatively small and isolated
- Browser performance is excellent for modern DOM APIs
- Simpler architecture without abstraction overhead

### DOM Update Strategy

**Incremental updates:**
```javascript
// Instead of recreating entire component
updateItem(itemId, changes) {
    const item = this.items.find(i => i.id === itemId);
    Object.assign(item, changes);

    // Update only the affected DOM element
    const element = this.getItemElement(itemId);
    element.innerHTML = item.content;
}
```

**Batch updates:**
```javascript
// Batch multiple changes
addItems(items) {
    // Disable rendering
    const wasRendering = this.rendering;
    this.rendering = false;

    // Add all items
    items.forEach(item => this.items.push(item));

    // Re-enable and render once
    this.rendering = wasRendering;
    this.render();
}
```

## Extension Points

### 1. Extending Components

```javascript
// Custom component extending FlexCard
class CustomCard extends FlexCard {
    constructor(element, options) {
        super(element, {
            ...options,
            variant: 'custom'
        });
    }

    render() {
        super.render();

        // Add custom functionality
        this.addCustomFeature();
    }

    addCustomFeature() {
        // Custom implementation
        const badge = document.createElement('div');
        badge.className = 'custom-badge';
        badge.textContent = 'CUSTOM';
        this.element.appendChild(badge);
    }
}
```

### 2. Custom Themes

```javascript
// Define custom theme for FlexToolbar
const customTheme = {
    background: '#6366f1',  // Indigo
    color: '#ffffff',
    border: '#4f46e5'
};

const toolbar = new FlexToolbar('#toolbar', {
    theme: customTheme
});
```

### 3. Plugin System (Future)

```javascript
// Planned plugin architecture
class FlexCard extends BaseComponent {
    use(plugin) {
        plugin.install(this);
        return this;
    }
}

// Plugin example
const analyticsPlugin = {
    install(component) {
        component.on('render', () => {
            trackEvent('component_rendered', {
                type: component.constructor.name
            });
        });
    }
};

card.use(analyticsPlugin);
```

### 4. Custom Validators

```javascript
// Custom validation for options
class FlexGrid extends BaseComponent {
    static validateOptions(options) {
        if (options.columns < 1) {
            throw new Error('Columns must be at least 1');
        }
        return true;
    }

    constructor(element, options) {
        super(element, options);
        this.constructor.validateOptions(options);
    }
}
```

## Performance Optimization

### 1. Debouncing

```javascript
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Used in FlexResponsive
window.addEventListener('resize', debounce(() => {
    this.updateBreakpoint();
}, 150));
```

### 2. Lazy Loading

```javascript
// FlexMasonry lazy loading
if (this.options.lazyLoad) {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                observer.unobserve(img);
            }
        });
    });

    this.element.querySelectorAll('img[data-src]').forEach(img => {
        observer.observe(img);
    });
}
```

### 3. Event Delegation

```javascript
// Instead of individual listeners
this.element.addEventListener('click', (e) => {
    if (e.target.matches('.tab-button')) {
        this.handleTabClick(e.target);
    }
});
```

### 4. Memory Management

```javascript
destroy() {
    // Remove event listeners
    this.listeners.clear();

    // Destroy child components
    this.children.forEach(child => child.destroy());
    this.children = [];

    // Clear references
    this.element = null;
    this.options = null;
    this.state = null;

    super.destroy();
}
```

## Best Practices

### 1. Component Design
- Keep components focused on single responsibility
- Use composition over inheritance when possible
- Make components configurable through options
- Emit events for important state changes

### 2. Performance
- Batch DOM updates when possible
- Use event delegation for dynamic content
- Clean up resources in `destroy()`
- Debounce expensive operations

### 3. Accessibility
- Include ARIA attributes
- Ensure keyboard navigation
- Provide focus management
- Support screen readers

### 4. Testing
- Test component initialization
- Test lifecycle methods
- Test event emissions
- Test responsive behavior
- Test error cases

---

**Next Steps:**
- [Component Documentation](./components/)
- [Migration Guide](./MIGRATION.md)
- [Contributing Guide](./CONTRIBUTING.md)
