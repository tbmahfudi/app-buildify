# Implementation Plan - Phase 4: Forms & Testing

## Overview

This document outlines the implementation plan for Phase 4, covering:
- **Option B**: Additional form and utility components
- **Option C**: Testing infrastructure and quality assurance

## Phase 4A: Form Components

### Priority 1: Essential Form Components

#### 1. FlexInput
**Purpose**: Universal input field component

**Features:**
- Input types: text, email, password, number, tel, url, search
- Label support (floating, inline, top)
- Validation states (error, success, warning)
- Helper text and error messages
- Prefix/suffix icons
- Disabled and readonly states
- Character counter
- Clear button
- Size variants (sm, md, lg)

**API:**
```javascript
const input = new FlexInput('#input', {
    type: 'email',
    label: 'Email Address',
    placeholder: 'Enter email',
    required: true,
    validator: (value) => /\S+@\S+\.\S+/.test(value),
    errorMessage: 'Invalid email format'
});
```

**Estimated Size**: ~350 lines

#### 2. FlexSelect
**Purpose**: Dropdown select component

**Features:**
- Single/multiple selection
- Search/filter options
- Custom option rendering
- Grouped options
- Disabled options
- Placeholder support
- Clear button
- Loading state
- Custom dropdown positioning

**API:**
```javascript
const select = new FlexSelect('#select', {
    options: [
        { value: '1', label: 'Option 1' },
        { value: '2', label: 'Option 2', disabled: true }
    ],
    placeholder: 'Select option',
    searchable: true,
    multiple: false
});
```

**Estimated Size**: ~450 lines

#### 3. FlexCheckbox
**Purpose**: Checkbox input component

**Features:**
- Checked/unchecked states
- Indeterminate state
- Label support
- Disabled state
- Custom colors
- Size variants
- Group support

**API:**
```javascript
const checkbox = new FlexCheckbox('#checkbox', {
    label: 'Accept terms',
    checked: false,
    onChange: (checked) => console.log(checked)
});
```

**Estimated Size**: ~250 lines

#### 4. FlexRadio
**Purpose**: Radio button group component

**Features:**
- Single selection from group
- Horizontal/vertical layout
- Disabled options
- Custom colors
- Size variants
- Description support

**API:**
```javascript
const radio = new FlexRadio('#radio', {
    name: 'payment',
    options: [
        { value: 'card', label: 'Credit Card' },
        { value: 'paypal', label: 'PayPal' }
    ],
    value: 'card'
});
```

**Estimated Size**: ~300 lines

### Priority 2: Data & Navigation Components

#### 5. FlexTable
**Purpose**: Data table with sorting and filtering

**Features:**
- Column configuration
- Sorting (single/multiple columns)
- Filtering (per column)
- Pagination
- Row selection
- Custom cell rendering
- Responsive (mobile cards)
- Loading state
- Empty state

**API:**
```javascript
const table = new FlexTable('#table', {
    columns: [
        { id: 'name', label: 'Name', sortable: true },
        { id: 'email', label: 'Email', sortable: true }
    ],
    data: [...],
    sortable: true,
    filterable: true,
    pagination: { pageSize: 10 }
});
```

**Estimated Size**: ~600 lines

#### 6. FlexAccordion
**Purpose**: Collapsible content sections

**Features:**
- Single/multiple open panels
- Animated transitions
- Custom headers
- Disabled panels
- Icons (expand/collapse)
- Nested accordions

**API:**
```javascript
const accordion = new FlexAccordion('#accordion', {
    items: [
        {
            id: 'section1',
            header: 'Section 1',
            content: '<p>Content 1</p>',
            open: true
        }
    ],
    allowMultiple: false
});
```

**Estimated Size**: ~400 lines

#### 7. FlexBreadcrumb
**Purpose**: Breadcrumb navigation

**Features:**
- Hierarchical navigation
- Custom separators
- Clickable/non-clickable items
- Icons support
- Responsive (collapse on mobile)
- Active item styling

**API:**
```javascript
const breadcrumb = new FlexBreadcrumb('#breadcrumb', {
    items: [
        { label: 'Home', href: '/' },
        { label: 'Products', href: '/products' },
        { label: 'Item', active: true }
    ],
    separator: '/'
});
```

**Estimated Size**: ~250 lines

## Phase 4B: Testing & Quality

### 1. Testing Infrastructure

#### Test Framework Setup
**Tool**: Vitest (fast, modern, Vite-compatible)

```bash
npm init -y
npm install -D vitest @vitest/ui jsdom @testing-library/dom
```

**Config**: `vitest.config.js`
```javascript
export default {
    test: {
        environment: 'jsdom',
        globals: true,
        coverage: {
            provider: 'v8',
            reporter: ['text', 'html'],
            exclude: ['node_modules/', 'tests/']
        }
    }
};
```

#### Directory Structure
```
tests/
├── unit/
│   ├── base-component.test.js
│   ├── flex-responsive.test.js
│   ├── components/
│   │   ├── flex-card.test.js
│   │   ├── flex-modal.test.js
│   │   └── flex-tabs.test.js
│   └── layout/
│       ├── flex-stack.test.js
│       ├── flex-grid.test.js
│       └── ...
├── integration/
│   ├── composition.test.js
│   └── responsive.test.js
└── helpers/
    └── test-utils.js
```

### 2. Unit Tests

#### Test Coverage Goals
- **BaseComponent**: 90%+
- **Layout Components**: 85%+
- **UI Components**: 85%+
- **Utilities**: 90%+

#### Example Test Structure
```javascript
import { describe, it, expect, beforeEach } from 'vitest';
import { FlexCard } from '../frontend/assets/js/components/flex-card.js';

describe('FlexCard', () => {
    let container;

    beforeEach(() => {
        container = document.createElement('div');
        document.body.appendChild(container);
    });

    it('should render with title', () => {
        const card = new FlexCard(container, {
            title: 'Test Card'
        });

        expect(container.querySelector('.card-title').textContent).toBe('Test Card');
    });

    it('should emit render event', () => {
        const card = new FlexCard(container, { title: 'Test' });
        let emitted = false;

        card.on('render', () => {
            emitted = true;
        });

        card.render();
        expect(emitted).toBe(true);
    });
});
```

### 3. E2E Tests (Future)

**Tool**: Playwright

**Test Scenarios:**
- Component showcase interactions
- Modal opening/closing
- Tab switching
- Responsive behavior
- Form validation
- Table sorting/filtering

### 4. Performance Profiling

#### Metrics to Track
- **Component initialization time**: < 50ms
- **Render time**: < 16ms (60fps)
- **Memory usage**: < 5MB per component
- **Bundle size**: Keep components < 25KB minified

#### Profiling Tools
- Chrome DevTools Performance
- Lighthouse
- Bundle analyzer

#### Test Cases
```javascript
// Performance test example
describe('FlexGrid Performance', () => {
    it('should render 100 items in < 100ms', () => {
        const start = performance.now();

        const grid = new FlexGrid('#grid', {
            columns: { xs: 1, md: 4 },
            items: Array.from({ length: 100 }, (_, i) => ({
                id: `item-${i}`,
                content: `<div>Item ${i}</div>`
            }))
        });

        const end = performance.now();
        expect(end - start).toBeLessThan(100);
    });
});
```

### 5. Accessibility Audit

#### Tools
- axe-core (automated testing)
- NVDA/JAWS (screen reader testing)
- Keyboard navigation testing
- Color contrast checker

#### Checklist
- [ ] All interactive elements keyboard accessible
- [ ] Proper ARIA attributes
- [ ] Focus management
- [ ] Screen reader announcements
- [ ] Color contrast (WCAG AA: 4.5:1)
- [ ] Alternative text for images
- [ ] Semantic HTML
- [ ] Skip links where needed

#### Automated Tests
```javascript
import { axe } from 'vitest-axe';

describe('FlexModal Accessibility', () => {
    it('should have no accessibility violations', async () => {
        const modal = new FlexModal({
            title: 'Test Modal',
            content: '<p>Content</p>'
        });

        modal.show();
        const results = await axe(modal.getElement());
        expect(results.violations).toHaveLength(0);
    });
});
```

## Implementation Priority

### Week 1: Essential Form Components
- [x] Plan and design
- [ ] Day 1-2: FlexInput (350 lines)
- [ ] Day 3: FlexCheckbox (250 lines)
- [ ] Day 4: FlexRadio (300 lines)
- [ ] Day 5: FlexSelect (450 lines)
- [ ] Documentation for form components

### Week 2: Navigation & Data Components
- [ ] Day 1-2: FlexAccordion (400 lines)
- [ ] Day 3: FlexBreadcrumb (250 lines)
- [ ] Day 4-5: FlexTable (600 lines)
- [ ] Documentation for these components

### Week 3: Testing Infrastructure
- [ ] Day 1: Set up Vitest and testing environment
- [ ] Day 2: Write BaseComponent tests
- [ ] Day 3: Write FlexStack, FlexGrid tests
- [ ] Day 4: Write FlexCard, FlexModal tests
- [ ] Day 5: Write form component tests

### Week 4: Quality & Documentation
- [ ] Day 1: Performance profiling
- [ ] Day 2: Accessibility audit
- [ ] Day 3: Fix issues found in audits
- [ ] Day 4: Update documentation
- [ ] Day 5: Final testing and review

## Success Metrics

### Code Quality
- [ ] Test coverage > 80%
- [ ] No accessibility violations
- [ ] All components < 25KB minified
- [ ] Performance targets met

### Documentation
- [ ] All new components documented
- [ ] Testing guide created
- [ ] Performance guide created
- [ ] Accessibility guide created

### User Experience
- [ ] Keyboard navigation works
- [ ] Screen reader compatible
- [ ] Responsive on all devices
- [ ] Fast and performant

## Next Steps

1. Start with FlexInput (most essential form component)
2. Follow with FlexCheckbox and FlexRadio (simpler forms)
3. Build FlexSelect (more complex)
4. Create FlexAccordion (useful layout)
5. Build FlexBreadcrumb (simple navigation)
6. Tackle FlexTable (most complex)
7. Set up testing infrastructure
8. Write comprehensive tests
9. Run audits and optimize

Let's begin! 🚀
