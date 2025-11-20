# Multi-Language Implementation Guide

## Library Comparison Summary

### Selected: i18next

**Why i18next?**
- Perfect balance of features and bundle size (~11KB core)
- Framework-agnostic (works great with vanilla JS)
- Plugin ecosystem for future growth
- Industry standard with excellent documentation
- Active community and maintenance

### Alternatives Considered

1. **Polyglot.js** (3KB)
   - Pro: Lighter weight
   - Con: Fewer features, no async loading
   - Use when: Very simple translation needs

2. **FormatJS** (8KB)
   - Pro: Standards-based, powerful formatting
   - Con: More complex API
   - Use when: Heavy date/time/number formatting

3. **Custom Vanilla JS** (1-2KB)
   - Pro: Maximum control, tiny size
   - Con: Need to build everything yourself
   - Use when: Extremely simple requirements

## Implementation Steps with i18next

### 1. Install i18next

```bash
npm install i18next i18next-http-backend i18next-browser-languagedetector
```

**Or use CDN** (for vanilla JS projects):
```html
<script src="https://cdn.jsdelivr.net/npm/i18next@23/i18next.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/i18next-http-backend@2/i18nextHttpBackend.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/i18next-browser-languagedetector@7/i18nextBrowserLanguageDetector.min.js"></script>
```

### 2. Create Translation Files

**Structure:**
```
frontend/assets/i18n/
├── en/
│   ├── common.json
│   ├── menu.json
│   └── pages.json
├── es/
│   ├── common.json
│   ├── menu.json
│   └── pages.json
├── fr/
│   └── ...
└── de/
    └── ...
```

**Example: `frontend/assets/i18n/en/menu.json`**
```json
{
  "dashboard": "Dashboard",
  "systemManagement": "System Management",
  "administration": "Administration",
  "tenants": "Tenants",
  "users": "Users",
  "groups": "Groups",
  "accessControl": "Access Control",
  "authPolicies": "Auth Policies",
  "menuManagement": "Menu Management",
  "systemSettings": "System Settings",
  "general": "General",
  "integration": "Integration",
  "security": "Security",
  "notifications": "Notifications",
  "helpSupport": "Help & Support"
}
```

**Example: `frontend/assets/i18n/en/pages.json`**
```json
{
  "accessControl": {
    "title": "Access Control",
    "description": "Manage roles, permissions, groups, and user access",
    "tabs": {
      "dashboard": "Dashboard",
      "organization": "Organization",
      "roles": "Roles",
      "permissions": "Permissions",
      "groups": "Groups",
      "userAccess": "User Access"
    }
  },
  "settings": {
    "title": "Settings",
    "description": "Manage your preferences and account settings",
    "userPreferences": "User Preferences",
    "theme": "Theme",
    "density": "Density",
    "language": "Language",
    "timezone": "Timezone"
  }
}
```

### 3. Initialize i18next

**Create: `frontend/assets/js/i18n.js`**
```javascript
// Initialize i18next
const initI18n = async () => {
  // Check if using CDN or npm
  const i18next = window.i18next || (await import('i18next')).default;
  const HttpBackend = window.i18nextHttpBackend || (await import('i18next-http-backend')).default;
  const LanguageDetector = window.i18nextBrowserLanguageDetector || (await import('i18next-browser-languagedetector')).default;

  await i18next
    .use(HttpBackend) // Load translations via HTTP
    .use(LanguageDetector) // Detect user language
    .init({
      fallbackLng: 'en',
      debug: true, // Set to false in production

      // Namespace configuration
      ns: ['common', 'menu', 'pages'],
      defaultNS: 'common',

      // Backend configuration
      backend: {
        loadPath: '/assets/i18n/{{lng}}/{{ns}}.json',
        crossDomain: false
      },

      // Language detection
      detection: {
        order: ['localStorage', 'navigator'],
        caches: ['localStorage']
      },

      // Interpolation
      interpolation: {
        escapeValue: false // Not needed for vanilla JS
      }
    });

  return i18next;
};

// Helper function to translate text
const t = (key, options = {}) => {
  return window.i18next.t(key, options);
};

// Helper function to translate and update DOM
const updateElement = (selector, key, options = {}) => {
  const element = document.querySelector(selector);
  if (element) {
    element.textContent = t(key, options);
  }
};

// Helper function to translate all elements with data-i18n attribute
const translatePage = () => {
  const elements = document.querySelectorAll('[data-i18n]');
  elements.forEach(element => {
    const key = element.getAttribute('data-i18n');
    const options = element.getAttribute('data-i18n-options');
    element.textContent = t(key, options ? JSON.parse(options) : {});
  });
};

// Change language function
const changeLanguage = async (lng) => {
  await window.i18next.changeLanguage(lng);
  translatePage();

  // Dispatch event for other components to react
  window.dispatchEvent(new CustomEvent('languageChanged', { detail: { language: lng } }));
};

// Export functions
window.i18n = {
  init: initI18n,
  t,
  updateElement,
  translatePage,
  changeLanguage
};

export { initI18n, t, updateElement, translatePage, changeLanguage };
```

### 4. Update HTML Templates

**Before:**
```html
<h1 class="text-3xl font-bold text-gray-900">
  Access Control
</h1>
```

**After:**
```html
<h1 class="text-3xl font-bold text-gray-900" data-i18n="pages.accessControl.title">
  Access Control
</h1>
```

### 5. Integrate with Existing Settings

**Update `frontend/assets/js/settings.js`:**

```javascript
// In applyLanguage function
function applyLanguage(language) {
  // Set HTML lang attribute
  document.documentElement.lang = language;

  // Change i18next language
  if (window.i18n) {
    window.i18n.changeLanguage(language);
  }

  // Store for persistence
  localStorage.setItem('preferredLanguage', language);

  console.log(`Settings: Language set to ${language}`);
}
```

### 6. Initialize on App Load

**Update `frontend/assets/js/app.js` or create init script:**

```javascript
// At the top of your app initialization
document.addEventListener('DOMContentLoaded', async () => {
  // Initialize i18next
  await window.i18n.init();

  // Translate initial page
  window.i18n.translatePage();

  // Listen for language changes
  window.addEventListener('languageChanged', (e) => {
    console.log('Language changed to:', e.detail.language);
  });

  // ... rest of your initialization
});
```

## Usage Examples

### Basic Translation
```javascript
// In JavaScript
const title = t('menu.dashboard'); // "Dashboard"
const description = t('pages.settings.description'); // "Manage your preferences..."
```

### With Interpolation
```javascript
// Translation: "Hello {{name}}, you have {{count}} messages"
const greeting = t('user.greeting', { name: 'John', count: 5 });
// Result: "Hello John, you have 5 messages"
```

### With Pluralization
```json
{
  "item": "{{count}} item",
  "item_plural": "{{count}} items"
}
```

```javascript
t('item', { count: 1 }); // "1 item"
t('item', { count: 5 }); // "5 items"
```

### Dynamic Content
```javascript
// Translate menu items dynamically
function renderMenu(menuItems) {
  return menuItems.map(item => {
    return {
      ...item,
      title: t(`menu.${item.key}`)
    };
  });
}
```

## Migration Strategy

### Phase 1: Core Pages (Week 1)
- [ ] Settings page
- [ ] Access Control page
- [ ] Dashboard page

### Phase 2: Menus & Navigation (Week 2)
- [ ] Main menu
- [ ] Breadcrumbs
- [ ] Footer

### Phase 3: Forms & Messages (Week 3)
- [ ] Form labels and placeholders
- [ ] Validation messages
- [ ] Success/error notifications

### Phase 4: All Remaining Pages (Week 4)
- [ ] All other templates
- [ ] Modals and dialogs
- [ ] Help text and tooltips

## Performance Considerations

1. **Lazy Loading**: Load only needed namespaces
   ```javascript
   i18next.loadNamespaces('admin').then(() => {
     // Admin namespace loaded
   });
   ```

2. **Caching**: Translations are cached in memory by default

3. **Bundle Size Optimization**:
   - Core only: 11KB
   - With backend + detector: ~16KB
   - Use tree-shaking if using bundler

## Testing

```javascript
// Example test
describe('i18n', () => {
  it('should translate menu items', () => {
    expect(t('menu.dashboard')).toBe('Dashboard');
  });

  it('should handle missing keys gracefully', () => {
    expect(t('missing.key')).toBe('missing.key');
  });
});
```

## Alternative: If You Choose Polyglot.js

**Pros**:
- Smaller (3KB vs 11KB)
- Simpler API
- Less overhead

**Setup:**
```html
<script src="https://cdn.jsdelivr.net/npm/node-polyglot@2/build/polyglot.min.js"></script>
```

```javascript
const polyglot = new Polyglot({
  locale: 'en',
  phrases: {
    "menu.dashboard": "Dashboard",
    "user.greeting": "Hello %{name}"
  }
});

// Usage
polyglot.t('menu.dashboard');
polyglot.t('user.greeting', { name: 'John' });
```

**When to choose Polyglot**:
- You only need basic text translation
- No need for async loading
- Want absolute minimal bundle size
- Simple interpolation is enough

## Resources

- **i18next Docs**: https://www.i18next.com/
- **i18next Playground**: https://jsfiddle.net/i18next/
- **Polyglot Docs**: https://airbnb.io/polyglot.js/
- **Translation Best Practices**: https://phrase.com/blog/posts/i18n-best-practices/

## Conclusion

**Recommended**: Start with **i18next** for:
- Better scalability
- Rich features when you need them
- Strong community support
- Only 5KB more than Polyglot

**Alternative**: Use **Polyglot.js** if:
- You need absolute minimal size
- Requirements are very simple
- Team prefers simpler API
