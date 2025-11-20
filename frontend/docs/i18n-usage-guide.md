# i18n Usage Guide - Buildify Platform

## Overview

The Buildify platform now supports **5 languages** with automatic translation using **i18next**:

- 🇬🇧 **English** (en) - Default
- 🇪🇸 **Español** (es) - Spanish
- 🇫🇷 **Français** (fr) - French
- 🇩🇪 **Deutsch** (de) - German
- 🇮🇩 **Bahasa Indonesia** (id) - Indonesian

## How It Works

### For Users

1. **Changing Language:**
   - Navigate to **Settings** page
   - Select your preferred language from the dropdown
   - Click "Save Preferences"
   - The entire interface will update to your selected language

2. **Automatic Language Detection:**
   - On first visit, the system detects your browser's language
   - Falls back to English if your browser language is not supported

3. **Language Persistence:**
   - Your language preference is saved to localStorage
   - The same language will be used on your next visit

### For Developers

#### File Structure

```
frontend/assets/i18n/
├── en/                      # English translations
│   ├── common.json         # Common terms (buttons, messages)
│   ├── menu.json           # Menu items
│   └── pages.json          # Page-specific content
├── es/                      # Spanish translations
│   ├── common.json
│   ├── menu.json
│   └── pages.json
├── fr/                      # French translations
│   ├── common.json
│   ├── menu.json
│   └── pages.json
├── de/                      # German translations
│   ├── common.json
│   ├── menu.json
│   └── pages.json
└── id/                      # Indonesian translations
    ├── common.json
    ├── menu.json
    └── pages.json
```

#### Adding Translations to HTML

Use the `data-i18n` attribute to mark translatable content:

```html
<!-- Simple text translation -->
<h1 data-i18n="pages.settings.title">Settings</h1>

<!-- Translation with options (for select elements) -->
<option value="light" data-i18n="pages.settings.themeLight">Light</option>

<!-- Translation in labels with icons -->
<label for="setting-language">
  <i class="ph-duotone ph-translate"></i>
  <span data-i18n="pages.settings.language">Language</span>
</label>
```

#### Using i18n in JavaScript

```javascript
// Translate a key
const translated = window.i18n.t('pages.settings.title');
// Returns: "Settings" (en), "Configuración" (es), "Pengaturan" (id), etc.

// Translate with interpolation
const greeting = window.i18n.t('user.greeting', { name: 'John' });
// Returns: "Hello John" (if translation is "Hello {{name}}")

// Change language programmatically
await window.i18n.changeLanguage('id');

// Get current language
const currentLang = window.i18n.getCurrentLanguage();

// Get all available languages
const languages = window.i18n.getAvailableLanguages();
// Returns: [{code: 'en', name: 'English', nativeName: 'English'}, ...]

// Translate specific element
window.i18n.translateElement('#my-heading', 'pages.dashboard.title');

// Translate all elements on page
window.i18n.translatePage();

// Listen for language changes
window.addEventListener('languageChanged', (e) => {
  console.log('Language changed to:', e.detail.language);
  // Update dynamic content here
});
```

## Adding New Translations

### Step 1: Add Translation Key

Add the translation key to all language files:

**`frontend/assets/i18n/en/pages.json`**
```json
{
  "myPage": {
    "title": "My New Page",
    "description": "This is a description"
  }
}
```

**`frontend/assets/i18n/id/pages.json`**
```json
{
  "myPage": {
    "title": "Halaman Baru Saya",
    "description": "Ini adalah deskripsi"
  }
}
```

### Step 2: Use in HTML

```html
<h1 data-i18n="pages.myPage.title">My New Page</h1>
<p data-i18n="pages.myPage.description">This is a description</p>
```

### Step 3: Test

1. Open the page
2. Go to Settings
3. Change language
4. Verify translation appears correctly

## Translation Namespaces

The system uses 3 namespaces for organization:

### 1. `common` - Common UI Elements
```javascript
window.i18n.t('common.save')        // "Save" / "Simpan" / "Guardar"
window.i18n.t('common.cancel')      // "Cancel" / "Batal" / "Cancelar"
window.i18n.t('common.delete')      // "Delete" / "Hapus" / "Eliminar"
```

### 2. `menu` - Menu Items
```javascript
window.i18n.t('menu.dashboard')     // "Dashboard" / "Dasbor" / "Panel"
window.i18n.t('menu.settings')      // "Settings" / "Pengaturan" / "Configuración"
```

### 3. `pages` - Page Content
```javascript
window.i18n.t('pages.settings.title')              // "Settings"
window.i18n.t('pages.accessControl.description')   // "Manage roles..."
```

## Adding a New Language

### Step 1: Create Language Directory

```bash
mkdir -p frontend/assets/i18n/pt
```

### Step 2: Create Translation Files

Copy from English and translate:

```bash
cp frontend/assets/i18n/en/common.json frontend/assets/i18n/pt/
cp frontend/assets/i18n/en/menu.json frontend/assets/i18n/pt/
cp frontend/assets/i18n/en/pages.json frontend/assets/i18n/pt/
```

### Step 3: Update i18n.js

In `frontend/assets/js/i18n.js`, add the language to supported languages:

```javascript
// Supported languages
supportedLngs: ['en', 'es', 'fr', 'de', 'id', 'pt'],
```

And add to `getAvailableLanguages()`:

```javascript
getAvailableLanguages() {
  return [
    { code: 'en', name: 'English', nativeName: 'English' },
    { code: 'es', name: 'Spanish', nativeName: 'Español' },
    { code: 'fr', name: 'French', nativeName: 'Français' },
    { code: 'de', name: 'German', nativeName: 'Deutsch' },
    { code: 'id', name: 'Indonesian', nativeName: 'Bahasa Indonesia' },
    { code: 'pt', name: 'Portuguese', nativeName: 'Português' }
  ];
}
```

### Step 4: Update Settings Page

In `frontend/assets/templates/settings.html`:

```html
<select id="setting-language">
  <option value="en">English</option>
  <option value="es">Español (Spanish)</option>
  <option value="fr">Français (French)</option>
  <option value="de">Deutsch (German)</option>
  <option value="id">Bahasa Indonesia (Indonesian)</option>
  <option value="pt">Português (Portuguese)</option>
</select>
```

## Advanced Features

### Pluralization

i18next supports pluralization out of the box:

**Translation:**
```json
{
  "item": "{{count}} item",
  "item_plural": "{{count}} items"
}
```

**Usage:**
```javascript
window.i18n.t('item', { count: 1 });  // "1 item"
window.i18n.t('item', { count: 5 });  // "5 items"
```

### Nesting

You can nest translation keys:

**Translation:**
```json
{
  "user": {
    "profile": {
      "name": "Name",
      "email": "Email"
    }
  }
}
```

**Usage:**
```javascript
window.i18n.t('user.profile.name');   // "Name"
window.i18n.t('user.profile.email');  // "Email"
```

### Fallback

If a translation key is missing:
1. Returns the key itself (e.g., "pages.missing.key")
2. Logs a warning to console
3. Falls back to English if available

## Best Practices

### 1. Always Provide English Translation
English is the fallback language. Always translate to English first.

### 2. Use Descriptive Keys
```javascript
// Good
'pages.settings.userPreferences'

// Bad
'sp.up'
```

### 3. Group Related Translations
```json
{
  "accessControl": {
    "title": "Access Control",
    "tabs": {
      "roles": "Roles",
      "permissions": "Permissions"
    }
  }
}
```

### 4. Keep Translations Consistent
Use the same translation for the same concept across all pages.

### 5. Test All Languages
After adding new content, test in all supported languages.

## Troubleshooting

### Translations Not Appearing

**Check:**
1. ✅ Is the translation key correct?
2. ✅ Is the JSON file valid (no syntax errors)?
3. ✅ Did you clear browser cache?
4. ✅ Is the file served correctly (check Network tab)?

**Debug:**
```javascript
// Check if i18n is initialized
console.log(window.i18n.isInitialized);

// Check current language
console.log(window.i18n.getCurrentLanguage());

// Test translation directly
console.log(window.i18n.t('pages.settings.title'));
```

### Wrong Language Displayed

**Check:**
1. ✅ localStorage: `localStorage.getItem('preferredLanguage')`
2. ✅ Browser language detection: Check browser settings

**Fix:**
```javascript
// Force specific language
await window.i18n.changeLanguage('id');

// Clear stored preference
localStorage.removeItem('preferredLanguage');
```

### JSON Syntax Error

Use a JSON validator:
```bash
# Validate JSON file
python -m json.tool frontend/assets/i18n/id/pages.json
```

Or use online tools: https://jsonlint.com/

## Performance

### Bundle Size
- **i18next core**: 11KB
- **HTTP backend**: 3KB
- **Language detector**: 2KB
- **Total**: ~16KB (gzipped)

### Loading Strategy
- Translations are loaded **on-demand** via HTTP
- **Cached** in memory after first load
- **localStorage** caches language preference

### Optimization Tips

1. **Lazy load namespaces:**
```javascript
// Load only when needed
i18next.loadNamespaces('admin').then(() => {
  // Admin namespace available
});
```

2. **Reduce translation file size:**
- Remove unused keys
- Use shorter key names for large files

## Examples

### Complete Page Example

**HTML:**
```html
<div class="page">
  <h1 data-i18n="pages.dashboard.title">Dashboard</h1>
  <p data-i18n="pages.dashboard.welcome">Welcome to your dashboard</p>

  <button data-i18n="common.save">Save</button>
  <button data-i18n="common.cancel">Cancel</button>
</div>
```

**JavaScript:**
```javascript
// After page loads or language changes
document.addEventListener('DOMContentLoaded', () => {
  window.i18n.translatePage();
});

// Listen for language changes
window.addEventListener('languageChanged', () => {
  // Update any dynamic content
  updateDashboardStats();
});
```

### Dynamic Content Example

```javascript
// Translate dynamically generated content
function renderUserList(users) {
  const html = users.map(user => `
    <div class="user-card">
      <h3>${user.name}</h3>
      <p>${window.i18n.t('pages.users.role')}: ${user.role}</p>
      <button>${window.i18n.t('common.edit')}</button>
    </div>
  `).join('');

  document.getElementById('user-list').innerHTML = html;
}
```

## Resources

- **i18next Documentation**: https://www.i18next.com/
- **Translation Best Practices**: https://phrase.com/blog/posts/i18n-best-practices/
- **Language Codes**: https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes

## Support

For issues or questions:
1. Check console for error messages
2. Verify JSON syntax
3. Test in different browsers
4. Check network tab for failed requests

## Changelog

### v1.0.0 (2025-01-20)
- ✅ Initial implementation with i18next
- ✅ Support for EN, ES, FR, DE, ID
- ✅ Settings page integration
- ✅ Access Control page translations
- ✅ Automatic language detection
- ✅ localStorage persistence
