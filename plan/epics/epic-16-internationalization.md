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
- Route: `#/settings` → settings page; language selector within the user preferences section
- Layout addition (user settings section): FlexForm row — Language (FlexSelect with flag emoji + language name: English / Deutsch / Español / Français / Bahasa Indonesia)

- Interactions:
  - select language: `i18next.changeLanguage(code)` called → namespace files lazy-loaded from `frontend/assets/i18n/{code}/` → all `data-i18n` attributes re-render in the new language → PUT /settings/user {language: code} → toast "Language changed to [Language Name]" (rendered in the new language)
  - app load / login: language preference read from `UserSettings` before first render; correct namespace files loaded before any page renders

- States:
  - loading (language files): brief spinner on language selector while namespace files fetch
  - missing key (dev mode): falls back to `en` value; browser console warning logged

---

### Story 16.1.2 — Translation Namespace Coverage `[DONE]`

#### Backend
*No backend story — this is a frontend translation concern.*

#### Frontend
*As a translator adding a new language, I want all user-visible strings organized into predictable namespace files with clear key names, so that I can translate the entire application without reading any JavaScript code.*
- No dedicated route — namespace files are static assets; no UI page involved

- File structure: `frontend/assets/i18n/{code}/` per language with 3 files:
  - `common.json`: action labels (Save, Cancel, Delete, Confirm, Edit, Create, Loading, Error, Success, No Data, Search, Filters, Apply, Reset, Export, Import, Close, Back, Next)
  - `pages.json`: page-specific titles and field labels, grouped by page name as top-level keys
  - `menu.json`: navigation menu item labels keyed by menu item ID

- i18next config: `fallbackLng: "en"` | `ns: ["common", "pages", "menu"]` | `defaultNS: "common"`
- Usage in JS: `t('common:Save')` or `t('pages:users.title')`; in HTML: `data-i18n="common:Save"`
- No hardcoded English strings in component or page JS files — enforced by ESLint rule in CI

---

### Story 16.1.3 — Translation Completeness Check `[DONE]`

#### Backend
*No backend story.*

#### Frontend
*As a developer adding new UI strings, I want a script that compares all translation keys in the English files against all other language files, so that I can see which keys are missing before a release.*
- No dedicated route — developer/CI tooling; no UI page involved

- Script: `frontend/scripts/check-translations.js`
  - compares `en/` namespace files against all other language directories
  - output: per-language completeness percentage + missing key list
  - missing key format: full key path + English value for context (e.g. `pages:users.title → "User Management"`)
- Run: `npm run i18n:check`; also runs automatically in CI on PRs that touch `i18n/` files

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
- No dedicated route — module i18n is a developer convention; no UI page involved

- On module activation: namespace added to i18next: `i18next.loadNamespaces(['financial'])`
- Module locale files loaded lazily on first access to the module's routes
- Namespace keys scoped under the module name to prevent collisions with core namespaces
- Fallback chain on missing key: module `en` file → core `en` fallback

---

### Story 16.2.2 — Entity and Field Label i18n `[PLANNED]`

#### Backend
*As an API, I want entity and field labels to return the localized label from `label_i18n` JSONB based on the requesting user's language, so that the NoCode platform is fully multilingual.*
- `EntityDefinition.label_i18n` JSONB: `{"en": "Sales Order", "de": "Verkaufsauftrag", "es": "Orden de Venta"}`
- `FieldDefinition.label_i18n` JSONB: same structure per field
- `GET /dynamic-data/{entity}/metadata` resolves the label using `Accept-Language`, falling back to `label` if the language is not in `label_i18n`

#### Frontend
*As a tenant administrator designing an entity for a multilingual deployment, I want to enter labels for each configured language in the entity and field designer, so that the generated forms and reports show the correct language to each user.*
- Route: `#/nocode/data-model` → entity designer; translations section added within entity and field property panels

- Layout addition (Entity Settings panel — below Label field):
  - "Translations" FlexAccordion (collapsed by default)
  - body: one row per configured tenant language — flag emoji | language name | label FlexInput
  - optional: "Translate" FlexButton(ghost) per row (calls translation API if configured; auto-fills input with suggestion)

- Layout addition (Field Properties panel — below field Label):
  - same "Translations" FlexAccordion structure as entity settings panel

- Layout addition (designer preview panel header):
  - Language FlexSelect — switches preview rendering to the selected language

- Interactions:
  - expand "Translations" accordion: rows render for each tenant-configured language
  - type in a language label input: `label_i18n` JSONB updated on save (no auto-save)
  - click "Translate" (if configured): POST /translate {text, target_lang} → input auto-filled with suggestion
  - change language selector in preview panel: preview panel re-renders entity/field labels in selected language

- States:
  - no-translation-api: "Translate" button absent when translation API is not configured
  - unsaved: accordion header shows unsaved-indicator FlexBadge until entity/field is saved
