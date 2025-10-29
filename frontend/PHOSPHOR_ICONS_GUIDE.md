# Phosphor Icons Integration Guide

## Overview

This project now includes **Phosphor Icons** - a flexible icon family with **9,000+ icons** across **6 expressive weights**. Phosphor Icons provides much more flexibility and variety compared to Bootstrap Icons while maintaining a consistent, modern design language.

## Why Phosphor Icons?

- **9,000+ Icons**: 1,500+ unique icons × 6 weights = massive library
- **6 Weights**: Thin, Light, Regular, Bold, Fill, and Duotone
- **Consistent Design**: All icons follow the same design system
- **Tailwind-Friendly**: Works seamlessly with Tailwind CSS utilities
- **MIT License**: Free for commercial and personal use
- **Active Development**: Regular updates and community support

---

## Icon Weights

Phosphor Icons offers 6 different weights for each icon:

| Weight | Class | Use Case | Example |
|--------|-------|----------|---------|
| **Thin** | `ph-thin` | Elegant, minimal interfaces | `<i class="ph-thin ph-heart"></i>` |
| **Light** | `ph-light` | Subtle, airy designs | `<i class="ph-light ph-heart"></i>` |
| **Regular** | `ph` | Default, balanced weight | `<i class="ph ph-heart"></i>` |
| **Bold** | `ph-bold` | Emphasis, strong visual hierarchy | `<i class="ph-bold ph-heart"></i>` |
| **Fill** | `ph-fill` | Solid icons, active states | `<i class="ph-fill ph-heart"></i>` |
| **Duotone** | `ph-duotone` | Two-tone effect, premium look | `<i class="ph-duotone ph-heart"></i>` |

---

## Basic Usage

### Simple Icon
```html
<i class="ph ph-user"></i>
```

### Different Weights
```html
<!-- Thin weight -->
<i class="ph-thin ph-star"></i>

<!-- Light weight -->
<i class="ph-light ph-star"></i>

<!-- Regular weight (default) -->
<i class="ph ph-star"></i>

<!-- Bold weight -->
<i class="ph-bold ph-star"></i>

<!-- Fill weight (solid) -->
<i class="ph-fill ph-star"></i>

<!-- Duotone weight (two-tone) -->
<i class="ph-duotone ph-star"></i>
```

---

## Styling with Tailwind CSS

### Sizing
```html
<!-- Text size utilities -->
<i class="ph ph-star text-sm"></i>     <!-- 14px -->
<i class="ph ph-star text-base"></i>   <!-- 16px -->
<i class="ph ph-star text-lg"></i>     <!-- 18px -->
<i class="ph ph-star text-xl"></i>     <!-- 20px -->
<i class="ph ph-star text-2xl"></i>    <!-- 24px -->
<i class="ph ph-star text-3xl"></i>    <!-- 30px -->
<i class="ph ph-star text-4xl"></i>    <!-- 36px -->
<i class="ph ph-star text-5xl"></i>    <!-- 48px -->
```

### Coloring
```html
<!-- Tailwind color utilities -->
<i class="ph ph-heart text-red-500"></i>
<i class="ph ph-star text-yellow-500"></i>
<i class="ph ph-check-circle text-green-500"></i>
<i class="ph ph-info text-blue-500"></i>
<i class="ph ph-warning text-orange-500"></i>

<!-- Hover effects -->
<i class="ph ph-gear text-gray-600 hover:text-blue-600 transition-colors"></i>
```

### Spacing & Layout
```html
<!-- Flexbox -->
<div class="flex items-center gap-2">
    <i class="ph ph-user"></i>
    <span>Profile</span>
</div>

<!-- Margin utilities -->
<i class="ph ph-bell mr-2"></i>
<i class="ph ph-envelope ml-2"></i>
```

---

## Using in FlexCard Component

```javascript
import { FlexCard } from './components/flex-card.js';

const card = new FlexCard('#container', {
    title: 'User Profile',
    icon: 'ph ph-user-circle',  // Regular weight
    badge: { text: 'Active', variant: 'success' },
    actions: [
        {
            label: 'Edit',
            icon: 'ph ph-pencil',
            variant: 'ghost',
            onClick: () => console.log('Edit')
        },
        {
            label: 'Delete',
            icon: 'ph ph-trash',
            variant: 'ghost',
            onClick: () => console.log('Delete')
        }
    ]
});
```

---

## Using in FlexModal Component

```javascript
import { FlexModal } from './components/flex-modal.js';

const modal = new FlexModal({
    title: 'Confirm Action',
    icon: 'ph-duotone ph-warning',  // Duotone for emphasis
    size: 'sm',
    content: '<p>Are you sure?</p>',
    footerActions: [
        {
            label: 'Cancel',
            icon: 'ph ph-x',
            variant: 'ghost',
            onClick: (e, modal) => modal.hide()
        },
        {
            label: 'Confirm',
            icon: 'ph ph-check',
            variant: 'primary',
            onClick: (e, modal) => {
                // Action here
                modal.hide();
            }
        }
    ]
});
```

---

## Using in FlexTabs Component

```javascript
import { FlexTabs } from './components/flex-tabs.js';

const tabs = new FlexTabs('#container', {
    variant: 'underline',
    tabs: [
        {
            id: 'home',
            label: 'Home',
            icon: 'ph ph-house',
            content: '<p>Home content</p>'
        },
        {
            id: 'settings',
            label: 'Settings',
            icon: 'ph-bold ph-gear',  // Bold for emphasis
            content: '<p>Settings content</p>'
        },
        {
            id: 'notifications',
            label: 'Notifications',
            icon: 'ph-fill ph-bell',  // Fill for active state
            badge: { text: '5', variant: 'danger' },
            content: '<p>Notifications content</p>'
        }
    ]
});
```

---

## Migration from Bootstrap Icons

Both icon libraries can coexist in the project. Here's a quick reference for migrating commonly used icons:

| Bootstrap Icons | Phosphor Icons | Notes |
|----------------|----------------|-------|
| `bi-house` | `ph ph-house` | Same name |
| `bi-person` | `ph ph-user` | Different name |
| `bi-person-circle` | `ph ph-user-circle` | Similar name |
| `bi-people` | `ph ph-users` | Pluralized |
| `bi-gear` | `ph ph-gear` | Same name |
| `bi-search` | `ph ph-magnifying-glass` | Different name |
| `bi-envelope` | `ph ph-envelope` | Same name |
| `bi-bell` | `ph ph-bell` | Same name |
| `bi-star` | `ph ph-star` | Same name |
| `bi-star-fill` | `ph-fill ph-star` | Use fill weight |
| `bi-heart` | `ph ph-heart` | Same name |
| `bi-heart-fill` | `ph-fill ph-heart` | Use fill weight |
| `bi-trash` | `ph ph-trash` | Same name |
| `bi-pencil` | `ph ph-pencil` | Same name |
| `bi-plus` | `ph ph-plus` | Same name |
| `bi-x` | `ph ph-x` | Same name |
| `bi-check` | `ph ph-check` | Same name |
| `bi-check-lg` | `ph ph-check` | Same name |
| `bi-chevron-down` | `ph ph-caret-down` | Different name |
| `bi-arrow-clockwise` | `ph ph-arrows-clockwise` | Pluralized |
| `bi-info-circle` | `ph ph-info` | Simplified |
| `bi-exclamation-triangle` | `ph ph-warning` | Different name |
| `bi-clipboard-check` | `ph ph-clipboard-text` | Similar |
| `bi-box` | `ph ph-package` | Different name |
| `bi-bar-chart` | `ph ph-chart-bar` | Reordered |
| `bi-graph-up` | `ph ph-chart-line-up` | More specific |
| `bi-window` | `ph ph-app-window` | More specific |
| `bi-code-slash` | `ph ph-code` | Simplified |
| `bi-eye` | `ph ph-eye` | Same name |
| `bi-eye-slash` | `ph ph-eye-slash` | Same name |
| `bi-file-text` | `ph ph-file-text` | Same name |
| `bi-folder` | `ph ph-folder` | Same name |
| `bi-shield-lock` | `ph ph-shield-check` | Similar |
| `bi-activity` | `ph ph-activity` | Same name |
| `bi-sliders` | `ph ph-sliders` | Same name |
| `bi-building` | `ph ph-buildings` | Pluralized |

---

## Design Patterns

### Visual Hierarchy with Weights

Use different weights to create visual hierarchy:

```html
<!-- Headers - Bold weight -->
<h2 class="flex items-center gap-2">
    <i class="ph-bold ph-user text-2xl"></i>
    <span>User Profile</span>
</h2>

<!-- Body content - Regular weight -->
<p class="flex items-center gap-2">
    <i class="ph ph-info text-blue-600"></i>
    <span>Regular information</span>
</p>

<!-- Subtle labels - Light weight -->
<span class="flex items-center gap-1 text-sm text-gray-500">
    <i class="ph-light ph-calendar"></i>
    <span>Created on Jan 1, 2024</span>
</span>
```

### Active/Inactive States

Use fill weight for active states:

```html
<!-- Inactive (outline) -->
<button class="flex items-center gap-2">
    <i class="ph ph-heart"></i>
    <span>Like</span>
</button>

<!-- Active (filled) -->
<button class="flex items-center gap-2 text-red-500">
    <i class="ph-fill ph-heart"></i>
    <span>Liked</span>
</button>
```

### Duotone for Premium Features

Use duotone weight for premium, special, or highlighted features:

```html
<div class="flex items-center gap-3 p-4 bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg">
    <i class="ph-duotone ph-crown text-4xl text-purple-600"></i>
    <div>
        <h3 class="font-semibold">Premium Feature</h3>
        <p class="text-sm text-gray-600">Upgrade to unlock</p>
    </div>
</div>
```

---

## Icon Browser & Search

To find icons:

1. **Official Website**: https://phosphoricons.com
   - Search by keyword
   - Preview all weights
   - Copy icon names

2. **In Your App**: Navigate to `/components-showcase` to see:
   - All 6 weights demonstrated
   - Popular icons
   - Duotone examples
   - Usage examples

---

## Performance Considerations

### Current Setup
- All 6 weights loaded via CDN
- Total size: ~300KB (50KB per weight)
- Cached by browser

### Production Optimization
For production, consider loading only needed weights:

```html
<!-- Load only Regular and Fill weights -->
<link rel="stylesheet" href="https://unpkg.com/@phosphor-icons/web@2.1.1/src/regular/style.css">
<link rel="stylesheet" href="https://unpkg.com/@phosphor-icons/web@2.1.1/src/fill/style.css">
```

Or use a build tool to include only used icons.

---

## Accessibility

Always include proper ARIA labels for icon-only buttons:

```html
<!-- Bad -->
<button>
    <i class="ph ph-x"></i>
</button>

<!-- Good -->
<button aria-label="Close">
    <i class="ph ph-x"></i>
</button>

<!-- Better -->
<button aria-label="Close">
    <i class="ph ph-x" aria-hidden="true"></i>
    <span class="sr-only">Close</span>
</button>
```

---

## Resources

- **Official Website**: https://phosphoricons.com
- **GitHub Repository**: https://github.com/phosphor-icons/web
- **NPM Package**: `@phosphor-icons/web`
- **Documentation**: https://github.com/phosphor-icons/web#readme
- **License**: MIT License

---

## Support

For questions or issues:
1. Browse the showcase page: `/components-showcase`
2. Check the official documentation: https://phosphoricons.com
3. Search the GitHub issues: https://github.com/phosphor-icons/web/issues

---

## Version

- **Phosphor Icons**: v2.1.1
- **Integration Date**: 2025-01-28
- **Project**: app-buildify NoCode Platform

---

**Enjoy using Phosphor Icons! 🎨**
