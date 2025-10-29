# FlexSection Component Guide

## Overview

**FlexSection** is a powerful component for creating full-width semantic page sections with backgrounds, consistent spacing, and slotted content areas. It provides preset variants for common section types and flexible configuration options for custom layouts.

## Why FlexSection?

- **Semantic Structure**: Section, header, body, footer slots for proper HTML semantics
- **Preset Variants**: Pre-configured styles for hero, content, feature, CTA, and footer sections
- **Rich Backgrounds**: Solid colors, gradients, images with overlays, and SVG patterns
- **Responsive Spacing**: Automatic padding that adapts to screen size
- **Width Control**: Integrates with FlexContainer for content width management
- **Advanced Features**: Parallax, sticky headers, scroll snap, viewport animations
- **Zero Dependencies**: Works standalone or with other Flex components

## Basic Usage

### Simple Content Section

```javascript
import FlexSection from './layout/flex-section.js';

const section = new FlexSection('#about', {
  variant: 'content',
  padding: 'xl',
  background: {
    type: 'solid',
    color: 'white'
  },
  slots: {
    header: {
      content: '<h2>About Us</h2>',
      align: 'center'
    },
    body: {
      content: document.querySelector('#about-content')
    }
  }
});
```

### Hero Section with Gradient

```javascript
const hero = new FlexSection('#hero', {
  variant: 'hero',
  padding: '2xl',
  background: {
    type: 'gradient',
    gradient: {
      from: 'indigo-600',
      to: 'purple-600',
      direction: 'to-br'
    }
  },
  slots: {
    body: {
      content: `
        <div class="text-center text-white">
          <h1 class="text-5xl font-bold mb-4">Welcome</h1>
          <p class="text-xl mb-8">Build amazing things</p>
          <button class="px-8 py-3 bg-white text-indigo-600 rounded-lg">
            Get Started
          </button>
        </div>
      `,
      align: 'center'
    }
  }
});
```

## Configuration Options

### Variants

FlexSection provides five built-in variants:

| Variant | Padding | Use Case |
|---------|---------|----------|
| **hero** | 2xl, center-aligned, min-height 500px | Hero sections, landing pages |
| **content** | xl, left-aligned | Standard content sections |
| **feature** | xl, background support | Feature showcases, highlights |
| **cta** | lg, center-aligned | Call-to-action banners |
| **footer** | lg, left-aligned | Footer sections |
| **custom** | - | Full control over all options |

```javascript
{
  variant: 'hero'  // hero | content | feature | cta | footer | custom
}
```

### Width Control

```javascript
{
  width: 'contained'  // fluid | contained | breakout
}
```

- **fluid**: Full viewport width, no constraints
- **contained**: Uses FlexContainer with standard preset (1280px)
- **breakout**: Uses FlexContainer with wide preset (1536px)

### Spacing System

```javascript
{
  // Preset spacing (applies to top and bottom)
  padding: 'xl',  // sm | md | lg | xl | 2xl

  // Or individual control
  paddingTop: { xs: 8, lg: 12 },
  paddingBottom: { xs: 8, lg: 12 }
}
```

**Spacing Scale**:
- **sm**: 2rem → 2.5rem (mobile → desktop)
- **md**: 2.5rem → 3rem
- **lg**: 3rem → 4rem
- **xl**: 4rem → 5rem
- **2xl**: 5rem → 7rem

### Background Types

#### 1. Solid Color

```javascript
{
  background: {
    type: 'solid',
    color: 'gray-50'  // Tailwind color class
  }
}
```

#### 2. Linear/Radial Gradient

```javascript
{
  background: {
    type: 'gradient',
    gradient: {
      from: 'indigo-500',
      via: 'purple-500',  // Optional
      to: 'pink-500',
      direction: 'to-br'  // Tailwind gradient directions
    }
  }
}
```

**Gradient Directions**: `to-t`, `to-tr`, `to-r`, `to-br`, `to-b`, `to-bl`, `to-l`, `to-tl`

#### 3. Image Background

```javascript
{
  background: {
    type: 'image',
    image: {
      url: '/images/hero.jpg',
      overlay: 'black',      // Overlay color
      overlayOpacity: 0.5,   // 0-1
      position: 'center',    // CSS background-position
      size: 'cover',         // CSS background-size
      parallax: true         // Enable parallax effect
    }
  }
}
```

#### 4. SVG Pattern

```javascript
{
  background: {
    type: 'pattern',
    pattern: 'dots'  // dots | grid | stripes
  }
}
```

**Note**: Patterns require corresponding CSS definitions.

### Slot System

Sections have three slots: header, body, and footer.

```javascript
{
  slots: {
    header: {
      content: element | html,  // Required
      align: 'center',          // left | center | right
      maxWidth: '4xl'           // Tailwind max-width
    },
    body: {
      content: element | html,
      maxWidth: '6xl',
      layout: 'stack'           // stack | grid | custom
    },
    footer: {
      content: element | html,
      align: 'center'
    }
  }
}
```

**Content Types**:
- HTML string: `'<h2>Title</h2>'`
- DOM element: `document.querySelector('#content')`
- Component with `getElement()`: `new FlexGrid(...)`

### Dividers

```javascript
{
  divider: {
    top: true,
    bottom: true,
    variant: 'line',      // line | dashed | dotted
    color: 'gray-200',    // CSS variable name
    thickness: '1px'
  }
}
```

### Advanced Features

#### Sticky Header

```javascript
{
  sticky: true  // Section sticks to top when scrolling
}
```

#### Scroll Snap

```javascript
{
  scrollSnap: true  // Section snaps to viewport when scrolling
}
```

#### Parallax Scrolling

```javascript
{
  parallax: {
    enabled: true,
    speed: 0.5  // 0-1, slower = more parallax
  }
}
```

#### Viewport Animations

```javascript
{
  animated: {
    enabled: true,
    trigger: 'viewport',  // viewport | scroll
    effect: 'fade-in'     // fade-in | slide-up | scale
  }
}
```

## Public API

### Methods

#### `setVariant(variant)`
Change the section variant.

```javascript
section.setVariant('hero');  // hero | content | feature | cta | footer
```

#### `updateBackground(background)`
Update the background configuration.

```javascript
section.updateBackground({
  type: 'gradient',
  gradient: {
    from: 'blue-600',
    to: 'indigo-600'
  }
});
```

#### `updateSlot(slotName, config)`
Update slot content.

```javascript
section.updateSlot('header', {
  content: '<h2>New Title</h2>',
  align: 'center'
});
```

#### `updatePadding(padding)`
Update section spacing.

```javascript
// Preset
section.updatePadding('2xl');

// Custom
section.updatePadding({ xs: 16, lg: 24 });
```

#### `enableParallax(enabled)`
Toggle parallax effect.

```javascript
section.enableParallax(true);
```

#### `scrollToSection(smooth)`
Scroll to this section.

```javascript
section.scrollToSection(true);  // smooth scroll
```

#### `getElement()`
Get the section DOM element.

```javascript
const element = section.getElement();
```

#### `getSlot(slotName)`
Get a specific slot element.

```javascript
const header = section.getSlot('header');
```

#### `destroy()`
Clean up and remove section functionality.

```javascript
section.destroy();
```

### Events

```javascript
// Initialization
section.on('init', () => {
  console.log('Section initialized');
});

// Rendering complete
section.on('render', () => {
  console.log('Section rendered');
});

// Updates
section.on('update', (detail) => {
  console.log('Section updated:', detail);
  // detail: { variant, background, slot, padding, etc. }
});

// Destruction
section.on('destroy', () => {
  console.log('Section destroyed');
});
```

## Common Patterns

### Landing Page Hero

```javascript
const hero = new FlexSection('#hero', {
  variant: 'hero',
  padding: '2xl',
  background: {
    type: 'image',
    image: {
      url: '/images/hero-bg.jpg',
      overlay: 'black',
      overlayOpacity: 0.6,
      parallax: true
    }
  },
  slots: {
    body: {
      content: `
        <div class="text-center text-white max-w-4xl mx-auto">
          <h1 class="text-6xl font-bold mb-6">Transform Your Business</h1>
          <p class="text-2xl text-gray-200 mb-8">
            Powerful tools for modern teams
          </p>
          <div class="flex gap-4 justify-center">
            <button class="px-8 py-4 bg-white text-blue-600 font-bold rounded-lg">
              Start Free Trial
            </button>
            <button class="px-8 py-4 border-2 border-white text-white rounded-lg">
              Watch Demo
            </button>
          </div>
        </div>
      `
    }
  }
});
```

### Features Section with Grid

```javascript
import { FlexGrid } from './layout/flex-grid.js';

const features = new FlexSection('#features', {
  variant: 'content',
  padding: 'xl',
  width: 'contained',
  background: {
    type: 'solid',
    color: 'gray-50'
  },
  slots: {
    header: {
      content: '<h2 class="text-4xl font-bold">Why Choose Us</h2>',
      align: 'center'
    },
    body: {
      content: new FlexGrid('#features-grid', {
        columns: { xs: 1, md: 2, lg: 3 },
        gap: 8,
        items: [
          { content: featureCard1 },
          { content: featureCard2 },
          { content: featureCard3 }
        ]
      }).getElement()
    }
  }
});
```

### Call-to-Action Banner

```javascript
const cta = new FlexSection('#cta', {
  variant: 'cta',
  padding: 'lg',
  background: {
    type: 'gradient',
    gradient: {
      from: 'green-400',
      to: 'blue-500',
      direction: 'to-r'
    }
  },
  divider: {
    top: true,
    color: 'green-300',
    thickness: '2px'
  },
  slots: {
    body: {
      content: `
        <div class="flex flex-col md:flex-row items-center justify-between gap-6 text-white max-w-5xl mx-auto">
          <div>
            <h3 class="text-3xl font-bold mb-2">Ready to get started?</h3>
            <p class="text-lg text-green-100">Join 10,000+ happy customers</p>
          </div>
          <button class="px-10 py-4 bg-white text-green-600 font-bold rounded-lg hover:bg-green-50 transition-colors shadow-lg">
            Sign Up Free
          </button>
        </div>
      `
    }
  }
});
```

### Testimonials Section

```javascript
const testimonials = new FlexSection('#testimonials', {
  variant: 'content',
  padding: { xs: 'lg', lg: 'xl' },
  width: 'contained',
  background: {
    type: 'solid',
    color: 'white'
  },
  divider: {
    top: true,
    bottom: true,
    color: 'gray-200'
  },
  slots: {
    header: {
      content: `
        <div class="text-center">
          <h2 class="text-4xl font-bold text-gray-900 mb-3">What Our Customers Say</h2>
          <p class="text-xl text-gray-600">Trusted by teams worldwide</p>
        </div>
      `,
      align: 'center'
    },
    body: {
      content: new FlexGrid('#testimonials-grid', {
        columns: { xs: 1, lg: 3 },
        gap: 6,
        items: testimonialCards
      }).getElement()
    }
  }
});
```

### Footer Section

```javascript
const footer = new FlexSection('#footer', {
  variant: 'footer',
  padding: 'lg',
  width: 'contained',
  background: {
    type: 'solid',
    color: 'gray-900'
  },
  slots: {
    body: {
      content: `
        <div class="grid grid-cols-1 md:grid-cols-4 gap-8 text-gray-300">
          <div>
            <h4 class="text-white font-bold mb-4">Company</h4>
            <ul class="space-y-2">
              <li><a href="#" class="hover:text-white">About</a></li>
              <li><a href="#" class="hover:text-white">Careers</a></li>
              <li><a href="#" class="hover:text-white">Contact</a></li>
            </ul>
          </div>
          <div>
            <h4 class="text-white font-bold mb-4">Product</h4>
            <ul class="space-y-2">
              <li><a href="#" class="hover:text-white">Features</a></li>
              <li><a href="#" class="hover:text-white">Pricing</a></li>
              <li><a href="#" class="hover:text-white">Security</a></li>
            </ul>
          </div>
          <div>
            <h4 class="text-white font-bold mb-4">Resources</h4>
            <ul class="space-y-2">
              <li><a href="#" class="hover:text-white">Docs</a></li>
              <li><a href="#" class="hover:text-white">Blog</a></li>
              <li><a href="#" class="hover:text-white">Support</a></li>
            </ul>
          </div>
          <div>
            <h4 class="text-white font-bold mb-4">Legal</h4>
            <ul class="space-y-2">
              <li><a href="#" class="hover:text-white">Privacy</a></li>
              <li><a href="#" class="hover:text-white">Terms</a></li>
            </ul>
          </div>
        </div>
      `
    },
    footer: {
      content: `
        <div class="border-t border-gray-800 mt-8 pt-8 text-center text-gray-500">
          <p>&copy; 2024 Your Company. All rights reserved.</p>
        </div>
      `
    }
  }
});
```

## Complete Landing Page Example

```javascript
// Hero Section
const hero = new FlexSection('#hero', {
  variant: 'hero',
  padding: '2xl',
  background: {
    type: 'gradient',
    gradient: { from: 'indigo-600', to: 'purple-600', direction: 'to-br' }
  },
  slots: {
    body: { content: heroContent }
  }
});

// Features Section
const features = new FlexSection('#features', {
  variant: 'content',
  padding: 'xl',
  width: 'contained',
  background: { type: 'solid', color: 'white' },
  slots: {
    header: { content: '<h2>Features</h2>', align: 'center' },
    body: { content: featuresGrid }
  }
});

// Testimonials Section
const testimonials = new FlexSection('#testimonials', {
  variant: 'content',
  padding: 'xl',
  width: 'contained',
  background: { type: 'solid', color: 'gray-50' },
  slots: {
    header: { content: '<h2>Testimonials</h2>', align: 'center' },
    body: { content: testimonialsGrid }
  }
});

// CTA Section
const cta = new FlexSection('#cta', {
  variant: 'cta',
  padding: 'lg',
  background: {
    type: 'gradient',
    gradient: { from: 'green-400', to: 'blue-500' }
  },
  slots: {
    body: { content: ctaContent }
  }
});

// Footer Section
const footer = new FlexSection('#footer', {
  variant: 'footer',
  padding: 'lg',
  width: 'contained',
  background: { type: 'solid', color: 'gray-900' },
  slots: {
    body: { content: footerContent }
  }
});
```

## Integration with Other Components

### With FlexContainer

FlexSection uses FlexContainer internally when `width` is set to `contained` or `breakout`:

```javascript
const section = new FlexSection('#section', {
  variant: 'content',
  width: 'contained',  // Creates FlexContainer internally
  // Container will have preset: 'standard', align: 'center', gutter: true
});
```

### With FlexGrid

Common pattern: section with grid layout in body slot:

```javascript
import { FlexGrid } from './layout/flex-grid.js';

const section = new FlexSection('#section', {
  slots: {
    body: {
      content: new FlexGrid('#grid', {
        columns: { xs: 1, md: 3 },
        items: gridItems
      }).getElement()
    }
  }
});
```

### With FlexStack

Vertical stacking within a section:

```javascript
import { FlexStack } from './layout/flex-stack.js';

const section = new FlexSection('#section', {
  slots: {
    body: {
      content: new FlexStack('#stack', {
        direction: 'vertical',
        gap: 6,
        items: stackItems
      }).getElement()
    }
  }
});
```

### With FlexCard

Section containing multiple cards:

```javascript
import { FlexCard } from './components/flex-card.js';

const cards = [
  new FlexCard({ title: 'Card 1', content: 'Content' }),
  new FlexCard({ title: 'Card 2', content: 'Content' }),
  new FlexCard({ title: 'Card 3', content: 'Content' })
];

const section = new FlexSection('#section', {
  slots: {
    body: {
      content: new FlexGrid('#cards-grid', {
        columns: { xs: 1, md: 3 },
        items: cards.map(card => ({ content: card.getElement() }))
      }).getElement()
    }
  }
});
```

## Advanced Techniques

### Dynamic Background Switching

```javascript
const section = new FlexSection('#hero', {
  variant: 'hero',
  background: {
    type: 'gradient',
    gradient: { from: 'blue-600', to: 'indigo-600' }
  }
});

// Switch to image background
document.querySelector('#bg-toggle').addEventListener('click', () => {
  section.updateBackground({
    type: 'image',
    image: {
      url: '/images/hero.jpg',
      overlay: 'black',
      overlayOpacity: 0.5
    }
  });
});
```

### Parallax Image Background

```javascript
const section = new FlexSection('#hero', {
  variant: 'hero',
  padding: '2xl',
  background: {
    type: 'image',
    image: {
      url: '/images/mountain.jpg',
      overlay: 'black',
      overlayOpacity: 0.4,
      position: 'center',
      size: 'cover',
      parallax: true
    }
  },
  parallax: {
    enabled: true,
    speed: 0.3  // Slower = more dramatic effect
  }
});
```

### Scroll-Triggered Section

```javascript
const section = new FlexSection('#features', {
  variant: 'content',
  animated: {
    enabled: true,
    trigger: 'viewport',
    effect: 'fade-in'
  }
});

// Section fades in when scrolled into view
```

### Sticky Section Header

```javascript
const section = new FlexSection('#sticky-nav', {
  variant: 'content',
  padding: 'md',
  sticky: true,  // Sticks to top when scrolling
  background: {
    type: 'solid',
    color: 'white'
  },
  slots: {
    body: {
      content: `
        <nav class="flex gap-6 justify-center">
          <a href="#home">Home</a>
          <a href="#about">About</a>
          <a href="#contact">Contact</a>
        </nav>
      `
    }
  }
});
```

### Full-Page Sections with Scroll Snap

```javascript
// Enable scroll snapping on parent
document.documentElement.style.scrollSnapType = 'y mandatory';

// Each section snaps to viewport
['#hero', '#features', '#testimonials', '#cta'].forEach(id => {
  new FlexSection(id, {
    scrollSnap: true,
    // ... other options
  });
});
```

## Accessibility

### Semantic HTML

```javascript
const section = new FlexSection('#about', {
  tag: 'section',  // Default, use <section> element
  slots: {
    header: {
      content: '<h2>About Us</h2>'  // Proper heading hierarchy
    },
    body: {
      content: '<p>We are...</p>'
    }
  }
});
```

### ARIA Labels

```javascript
// Add ARIA labels after initialization
const section = new FlexSection('#hero');
section.getElement().setAttribute('aria-label', 'Hero section');
```

### Focus Management

```javascript
// Make section focusable for skip links
const section = new FlexSection('#main-content');
section.getElement().setAttribute('tabindex', '-1');
section.getElement().setAttribute('id', 'main-content');

// Skip link in header:
// <a href="#main-content">Skip to main content</a>
```

### Reduced Motion

```javascript
// Respect user's motion preferences
const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

const section = new FlexSection('#hero', {
  parallax: {
    enabled: !prefersReducedMotion  // Disable parallax if user prefers reduced motion
  },
  animated: {
    enabled: !prefersReducedMotion  // Disable animations
  }
});
```

## Performance Considerations

- **Lazy Loading Images**: Use loading="lazy" for background images
- **Parallax Throttling**: Parallax scroll handler is throttled to 16ms (~60fps)
- **Intersection Observer**: Viewport animations use efficient Intersection Observer API
- **Minimize Reflows**: Styles applied in batches to reduce layout thrashing
- **Debounced Breakpoints**: Breakpoint changes are debounced by FlexResponsive

## Troubleshooting

### Background gradient not showing

**Problem**: Gradient classes not applying.

**Solution**: Ensure Tailwind CSS is configured for gradients:
```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
      }
    }
  }
}
```

### Section not full-width

**Problem**: Section doesn't extend to viewport edges.

**Solution**: Ensure no parent containers have max-width constraints:
```css
/* Remove constraints */
#parent {
  max-width: none !important;
  width: 100%;
}
```

### Parallax not working

**Problem**: Parallax effect not visible.

**Solution**: Check parallax configuration and ensure image background is set:
```javascript
{
  background: {
    type: 'image',  // Required for parallax
    image: {
      parallax: true  // Enable on image config
    }
  },
  parallax: {
    enabled: true  // Also enable on section
  }
}
```

### Slot content not rendering

**Problem**: Slot remains empty.

**Solution**: Ensure content is valid:
```javascript
// Wrong: undefined content
{ slots: { body: { content: undefined } } }

// Right: valid content
{ slots: { body: { content: '<div>Content</div>' } } }
// or
{ slots: { body: { content: element } } }
```

## Browser Support

FlexSection works in all modern browsers:

- ✅ Chrome/Edge 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ iOS Safari 14+
- ✅ Android Chrome 90+

**Intersection Observer** (for animations): Chrome 51+, Firefox 55+, Safari 12.1+

## Best Practices

1. **Use Semantic Variants**: Start with variant that matches your use case
2. **Consistent Spacing**: Use preset padding scales for consistency
3. **Accessible Headings**: Use proper heading hierarchy in slots
4. **Optimize Images**: Compress background images for performance
5. **Test Responsiveness**: Verify spacing and content at all breakpoints
6. **Limit Parallax**: Only use parallax on 1-2 hero sections, not throughout
7. **Meaningful Sections**: Each section should have a clear purpose
8. **Color Contrast**: Ensure text is readable on background colors/images

## Related Components

- **FlexContainer**: Used internally for width control
- **FlexGrid**: Commonly used in body slots
- **FlexStack**: Alternative layout for body slots
- **FlexCard**: Often contained within sections
- **FlexSidebar**: Main content area contains multiple sections

## Further Reading

- [FlexContainer Guide](./FLEX_CONTAINER_GUIDE.md)
- [FlexSidebar Guide](./FLEX_SIDEBAR_GUIDE.md)
- [FlexGrid Documentation](./docs/FLEX_GRID.md)
- [BaseComponent Documentation](./docs/BASE_COMPONENT.md)
