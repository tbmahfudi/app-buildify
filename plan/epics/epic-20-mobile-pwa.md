# Epic 20 — Mobile & Progressive Web App (PWA)

> Offline-capable, installable PWA with mobile-responsive UI optimized for touch and small screens.

---

## Feature 20.1 — Progressive Web App Foundation `[PLANNED]`

### Story 20.1.1 — PWA Manifest and Service Worker `[PLANNED]`

#### Backend
*No backend story — PWA manifest and service worker are purely frontend concerns.*
- `GET /api/v1/admin/version` provides `{version, commit_sha}` used by the service worker cache-busting strategy
- Static files served with correct `Cache-Control` headers: immutable assets (hashed filenames) get `max-age=31536000`; HTML files get `no-cache`

#### Frontend
*As a user on a mobile device, I want to install the app to my home screen and have it launch full-screen without a browser bar, so that the platform feels like a native app.*
- No dedicated route — PWA manifest and service worker are global; no isolated page

- `frontend/manifest.json`: `name` | `short_name` | `start_url` | `display: "standalone"` | `background_color` | `theme_color` (set dynamically to tenant `primary_color`) | icons (192×192, 512×512)
- `main.html`: `<link rel="manifest">` + `<meta name="apple-mobile-web-app-capable" content="yes">` + apple touch icons + splash screen meta
- `frontend/sw.js`: registered via `navigator.serviceWorker.register('/sw.js')` on app load
  - Cache-First for static assets (JS, CSS, fonts, images) — pre-cached on install
  - Network-First for API calls
  - App shell (HTML/CSS/core JS) pre-cached so the app loads instantly offline

- `InstallBanner` (shown after 3rd visit, dismissable): FlexAlert(type=info, dismissible) "Install App" FlexButton(ghost) + × dismiss

- Interactions:
  - click "Install App": captured `beforeinstallprompt.prompt()` called → system install dialog appears
  - dismiss banner: banner hidden; `localStorage` flag set to prevent re-showing
  - app launched from home screen: runs in `standalone` mode (no browser chrome)

---

### Story 20.1.2 — Offline Access and Background Sync `[PLANNED]`

#### Backend
*As an API, I want to support idempotent record creation so that offline-queued POST requests can be safely replayed without creating duplicates.*
- All `POST /api/v1/dynamic-data/{entity}/records` accept an optional `idempotency_key` header; duplicate submissions with the same key return the original response (201 → 200)
- `idempotency_keys` table stores `{key, response_body, created_at}` with a 24h TTL; auto-cleaned by a scheduler job

#### Frontend
*As a field worker with intermittent connectivity, I want to create and edit records while offline and have my changes automatically sync when connectivity is restored, so that I don't lose work due to network outages.*
- No dedicated route — offline behavior is handled globally by the service worker and `api.js`

- Offline queue: service worker intercepts failed `POST`/`PUT`/`PATCH` calls → queued in IndexedDB sync queue
- Background Sync: `SyncManager.register('offline-sync')` replays queue when connectivity returns

- `OfflineBanner` (global, persistent): FlexAlert(type=warning, dismissible=false) "You are offline — changes will sync when reconnected" — shown when `navigator.onLine === false`

- Read cache: last-fetched list/record data served from cache when offline; stale FlexBadge(color=neutral) "Data last updated [time]" shown in list page headers

- `ConflictModal` FlexModal(size=md) triggered on 409 sync response:
  - body: field-by-field diff — local value vs remote value per changed field
  - footer: "Keep Mine" FlexButton(ghost) | "Use Theirs" FlexButton(ghost) | "Merge" FlexButton(primary)

- Interactions:
  - connectivity restored: toast "Syncing X pending changes…" → queue replays with idempotency keys → toast "All changes synced" (or per-item error list on failure)
  - 409 sync conflict: ConflictModal opens for that record; user resolves; sync continues

---

## Feature 20.2 — Mobile-Responsive UI `[PLANNED]`

### Story 20.2.1 — Responsive Layout Adaptation `[PLANNED]`

#### Backend
*No backend story — responsive layout is a frontend concern.*
- API responses for list endpoints support `fields` query param so mobile clients can request a minimal field set: `GET /records?fields=id,name,status` reduces payload size

#### Frontend
*As a user on a phone, I want every page to reflow into a single-column layout with touch-friendly tap targets, so that I can use all platform features comfortably on a small screen.*
- No dedicated route — responsive behavior applies globally to all page templates

- Responsive:
  - `sm:` (< 640px): single-column layout; sidebar hidden (slide-out drawer via hamburger)
  - `md:` (640–1024px): two-column layout; sidebar visible collapsed
  - `lg:` (≥ 1024px): full desktop layout

- Mobile nav: top nav shows page title + hamburger + user avatar only (breadcrumb hidden); hamburger opens sidebar drawer; tap outside or back button closes drawer

- Component mobile adaptations:
  - `FlexDataGrid`: card-view per row on mobile (key fields only); toggle to horizontal-scroll table mode
  - `FlexModal`: `size="full"` auto-applied on viewports < 640px; bottom-sheet animation replaces center-fade
  - `FlexSelect`: dropdown opens as full-screen bottom sheet on mobile
  - Forms: all inputs stack vertically on mobile

- Accessibility: all tap targets minimum 44×44 px (WCAG 2.5.5); no hover-only interactions; tooltips accessible via long-press

---

### Story 20.2.2 — Touch Gestures and Mobile Navigation `[PLANNED]`

#### Backend
*No backend story.*

#### Frontend
*As a mobile user navigating between records, I want to swipe left/right to go back/forward and pull down to refresh lists, so that navigation feels native.*
- No dedicated route — touch gestures are global behaviors applied to all list pages and navigation

- Gesture specs:
  - Pull-to-refresh (list pages): `touchstart`/`touchmove` detection; spinner appears at pull distance > 60px; on release → list reload API call
  - Swipe-back: `touchstart`/`touchend` from left edge (< 20px) + rightward swipe > 100px → `history.back()`
  - Swipe-to-reveal (list rows): left swipe → "Delete" action (red); right swipe → "Edit" action (blue)
  - FlexDrawer (side nav): swipe-from-left-edge to open; swipe-left to close
  - Long-press on list row: context menu (same actions as row kebab menu)

- Device safe areas: `viewport-fit=cover` meta; `padding-bottom: env(safe-area-inset-bottom)` on page container (notch/home-indicator devices)

---

### Story 20.2.3 — Mobile Performance Optimization `[PLANNED]`

#### Backend
*As an API, I want paginated list endpoints to support cursor-based pagination as an alternative to offset pagination, so that mobile clients can efficiently load the next page without recalculating offsets.*
- `GET /api/v1/dynamic-data/{entity}/records?cursor={cursor_token}&page_size=20` returns `{items, next_cursor, has_more}`
- Cursor is an opaque base64-encoded token encoding `{last_id, last_sort_value}`; server-side validated and not user-constructible
- Existing offset pagination (`?page=N`) continues to work for backwards compatibility

#### Frontend
*As a user on a mobile device with a slow connection, I want the app to load quickly and scroll smoothly even with large datasets, so that the platform is usable on cellular networks.*
- No dedicated route — performance optimizations are applied globally to the build and runtime

- Optimizations:
  - Code splitting: each page JS loaded on demand (`dynamic import()`); initial bundle = app shell + auth only
  - Images: `loading="lazy"` + `srcset` on all avatars and file previews; WebP format preferred
  - Fonts: `font-display: swap`; subsetted to used character ranges
  - Dashboard widgets: `IntersectionObserver` defers rendering of off-screen widgets
  - `FlexDataGrid` on mobile: cursor-based infinite scroll (next 20 records on scroll-to-bottom) replaces pagination buttons

- Lighthouse mobile targets (measured in CI): Performance ≥ 85 | Accessibility ≥ 95 | Best Practices ≥ 90

---

## Feature 20.3 — Mobile-Specific Features `[PLANNED]`

### Story 20.3.1 — Camera and File Capture `[PLANNED]`

#### Backend
*No backend story — same presigned upload API from Epic 19 is used.*

#### Frontend
*As a field worker attaching a photo to a record, I want to tap "Take Photo" and have my phone's camera open directly, so that I can capture and attach evidence without leaving the app.*
- No dedicated route — camera capture is a `FlexFileUpload` mobile enhancement; used on any Attachments tab

- `FlexFileUpload` mobile action sheet (replaces drop zone on mobile):
  - "Take Photo" → `<input type="file" accept="image/*" capture="environment">` (rear camera)
  - "Record Video" and "Capture Document" (PDF scan) options

- Interactions:
  - capture photo: Canvas API auto-compresses to < 2MB before presigned upload; EXIF stripped (GPS, timestamp) unless field has `capture_location: true`
  - offline capture: photo stored as IndexedDB blob → uploaded via Background Sync when connectivity returns

---

### Story 20.3.2 — Push Notifications `[PLANNED]`

#### Backend
*As an API, I want to send push notifications to registered device endpoints via the Web Push protocol, so that users receive alerts even when the app is not open.*
- `POST /api/v1/notifications/push/subscribe` stores `{endpoint, keys: {p256dh, auth}, user_id}` in `push_subscriptions` table
- `DELETE /api/v1/notifications/push/unsubscribe` removes the subscription
- `NotificationService.send_push(user_id, title, body, data)` uses `pywebpush` library to send to all user's registered endpoints
- Platform notification events (workflow approval needed, record assigned, automation triggered) call `send_push` after creating the DB notification record

#### Frontend
*As a user, I want to receive push notifications for workflow approvals and record assignments even when the app is not open, so that I don't miss time-sensitive actions.*
- Route: `#/settings` → Push Notifications section (added to user settings page)
- Layout addition (settings page — Push Notifications section): FlexStack(gap=sm) — "Enable notifications?" FlexCheckbox toggle + per-type toggles (Workflow / Assignments / Mentions / System)

- Service worker behavior:
  - `push` event: `self.registration.showNotification(title, {body, icon, badge, data})`
  - `notificationclick` event: opens app and navigates to `data.url`
  - subscription auto re-registered if service worker updates or subscription expires

- Interactions:
  - first login (mobile): FlexModal(size=sm) "Enable notifications?" prompt → confirm: `Notification.requestPermission()` → on grant: `PushManager.subscribe({applicationServerKey: VAPID_public_key})` → POST /notifications/push/subscribe
  - toggle notification type (settings): PUT /settings/user {push_preferences} → auto-save
  - disable all push: DELETE /notifications/push/unsubscribe → subscription removed

---
