# Epic 16 — Internationalization (i18n)

> Full multi-language support using i18next with lazy-loaded namespace JSON files and runtime language switching.

---

## Feature 16.1 — Multi-Language Support `[DONE]`

### Story 16.1.1 — Language Loading and Runtime Switching `[DONE]`

#### Backend
*As an API, I want to return localized entity metadata labels based on the user's language preference, so that the NoCode platform feels native in each language.*
- `GET /dynamic-data/{entity}/metadata` reads `Accept-Language` header and returns localized `label` and `plural_label` from `label_i18n` JSONB if available

#### Frontend
*As a user on the settings page, I want to select my preferred language from a dropdown and have the entire application re-render in that language immediately — without a page reload, so that switching languages is instant and satisfying.*
- Language select on `#/settings` page: `FlexSelect` with flag emoji + language name options (English, Deutsch, Español, Français, Bahasa Indonesia)
- Selecting a language:
  1. Calls `i18next.changeLanguage(code)` — lazy-loads the namespace files for the selected language from `frontend/assets/i18n/{code}/`
  2. All `data-i18n` attributes re-render with the new translations
  3. Language preference saved to `UserSettings` via `PUT /settings/user`
  4. Toast: "Language changed to [Language Name]" in the new language
- Language also applied on login: loaded from `UserSettings` before the app renders
- Missing translation keys: fall back to `en` and log a warning in the browser console (dev mode)

---

### Story 16.1.2 — Translation Namespace Coverage `[DONE]`

#### Backend
*No backend story — this is a frontend translation concern.*

#### Frontend
*As a translator adding a new language, I want all user-visible strings organized into predictable namespace files with clear key names, so that I can translate the entire application without reading any JavaScript code.*
- 3 namespace files per language under `frontend/assets/i18n/{code}/`:
  - `common.json`: action labels (Save, Cancel, Delete, Confirm, Edit, Create, Loading, Error, Success, No Data, Search, Filters, Apply, Reset, Export, Import, Close, Back, Next)
  - `pages.json`: page-specific titles and field labels, grouped by page name as top-level keys
  - `menu.json`: navigation menu item labels keyed by menu item ID
- i18next configured with: `fallbackLng: "en"`, `ns: ["common", "pages", "menu"]`, `defaultNS: "common"`
- In JS: `t('common:Save')` or `t('pages:users.title')`; in HTML: `data-i18n="common:Save"`
- No hardcoded English strings in component or page JS files — enforced by an ESLint rule in CI

---

### Story 16.1.3 — Translation Completeness Check `[DONE]`

#### Backend
*No backend story.*

#### Frontend
*As a developer adding new UI strings, I want a script that compares all translation keys in the English files against all other language files, so that I can see which keys are missing before a release.*
- Script at `frontend/scripts/check-translations.js` compares `en/` namespace files against all other language directories
- Output: per-language completeness percentage + list of missing keys
- Run via `npm run i18n:check`; also runs in CI on PRs that touch `i18n/` files
- Missing key report shows the full key path and the English value for context: `pages:users.title → "User Management"`

---

## Feature 16.2 — Module and Dynamic Content i18n `[PLANNED]`

### Story 16.2.1 — Module i18n Namespace Registration `[PLANNED]`

#### Backend
*As an API, I want modules to declare their i18n namespace in the manifest so the platform loads their translation files on activation.*
- Module manifest: `"i18n": {"namespace": "financial", "locales_path": "frontend/i18n/"}`
- On module activation: the platform copies/symlinks the module's locale files into the frontend's i18n directory
- Missing locale files for the module default to `en` without throwing errors

#### Frontend
*As a module developer, I want to use `t('financial:accounts.title')` in my module's frontend code and have translations loaded automatically, so that my module is fully localizable with the same i18next setup as the platform.*
- Module registration adds the namespace to i18next's `ns` array: `i18next.loadNamespaces(['financial'])`
- Module locale files loaded lazily when the module's routes are first accessed
- Module namespace keys scoped under the module name to prevent collisions with core namespaces
- Missing module translations: i18next falls back to the module's `en` file, then to the core `en` fallback

---

### Story 16.2.2 — Entity and Field Label i18n `[PLANNED]`

#### Backend
*As an API, I want entity and field labels to return the localized label from `label_i18n` JSONB based on the requesting user's language, so that the NoCode platform is fully multilingual.*
- `EntityDefinition.label_i18n` JSONB: `{"en": "Sales Order", "de": "Verkaufsauftrag", "es": "Orden de Venta"}`
- `FieldDefinition.label_i18n` JSONB: same structure per field
- `GET /dynamic-data/{entity}/metadata` resolves the label using `Accept-Language`, falling back to `label` if the language is not in `label_i18n`

#### Frontend
*As a tenant administrator designing an entity for a multilingual deployment, I want to enter labels for each configured language in the entity and field designer, so that the generated forms and reports show the correct language to each user.*
- Entity designer "Entity Settings" panel: below the Label field, an "Translations" collapsible section
- Translations section shows a row per configured tenant language (e.g. German, Spanish): language flag + language name + label input
- Auto-filled with a suggestion: the English label translated via Google Translate button (optional, calls a translation API if configured)
- Same translations section on each field definition in the field properties panel
- Preview panel in the entity designer shows the labels in the currently selected preview language (language selector in the preview panel header)
