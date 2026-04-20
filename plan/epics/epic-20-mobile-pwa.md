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
- `frontend/manifest.json` (Web App Manifest): `name`, `short_name`, `start_url`, `display: "standalone"`, `background_color`, `theme_color`, icons at 192×192 and 512×512
- `<link rel="manifest" href="/manifest.json">` in `main.html`; `<meta name="theme-color">` set dynamically to tenant's `primary_color`
- `frontend/sw.js` — service worker registered on app load via `navigator.serviceWorker.register('/sw.js')`
- Service worker uses Cache-First strategy for static assets (JS, CSS, fonts, images); Network-First for API calls
- App shell (HTML/CSS/core JS) pre-cached on service worker install so the app loads instantly even offline
- "Add to Home Screen" install prompt: captured `beforeinstallprompt` event; shown as a subtle banner after 3rd visit with "Install App" CTA and dismiss option
- iOS Safari: `<meta name="apple-mobile-web-app-capable" content="yes">`, apple touch icons, splash screens

---

### Story 20.1.2 — Offline Access and Background Sync `[PLANNED]`

#### Backend
*As an API, I want to support idempotent record creation so that offline-queued POST requests can be safely replayed without creating duplicates.*
- All `POST /api/v1/dynamic-data/{entity}/records` accept an optional `idempotency_key` header; duplicate submissions with the same key return the original response (201 → 200)
- `idempotency_keys` table stores `{key, response_body, created_at}` with a 24h TTL; auto-cleaned by a scheduler job

#### Frontend
*As a field worker with intermittent connectivity, I want to create and edit records while offline and have my changes automatically sync when connectivity is restored, so that I don't lose work due to network outages.*
- Service worker intercepts failed API `POST`/`PUT`/`PATCH` calls and adds them to an IndexedDB sync queue
- Background Sync API (`SyncManager.register('offline-sync')`) triggers queue replay when connectivity returns
- Offline indicator: a persistent banner "You are offline — changes will sync when reconnected" shown when `navigator.onLine === false`
- Sync status: after reconnection, a toast "Syncing X pending changes…" followed by "All changes synced" or per-item error summary
- Read operations: last-fetched list/record data served from cache when offline; stale indicator "Data last updated [time]" shown in list headers
- Conflict resolution: if a record was updated server-side while the client was offline, the sync response returns 409; user is shown a diff modal "Remote has newer data — keep mine / use theirs / merge"

---

## Feature 20.2 — Mobile-Responsive UI `[PLANNED]`

### Story 20.2.1 — Responsive Layout Adaptation `[PLANNED]`

#### Backend
*No backend story — responsive layout is a frontend concern.*
- API responses for list endpoints support `fields` query param so mobile clients can request a minimal field set: `GET /records?fields=id,name,status` reduces payload size

#### Frontend
*As a user on a phone, I want every page to reflow into a single-column layout with touch-friendly tap targets, so that I can use all platform features comfortably on a small screen.*
- All page templates updated with responsive breakpoints using Tailwind classes: single-column on mobile (`sm:`), two-column on tablet (`md:`), full layout on desktop (`lg:`)
- Navigation: sidebar collapses to a slide-out drawer on mobile; hamburger button in the top nav opens/closes it; drawer closes on outside tap or back button press
- Top nav on mobile: breadcrumb hidden; only page title + hamburger + user avatar shown
- `FlexDataGrid` on mobile: columns collapse to a card view (one card per row showing key fields); horizontally scrollable table mode available via a toggle
- `FlexModal` on mobile: `size="full"` auto-applied on viewports < 640px; bottom sheet animation instead of center fade
- All tap targets minimum 44×44 px (WCAG 2.5.5); no hover-only interactions; all tooltips also accessible via long-press
- Forms: inputs stack vertically; `FlexSelect` dropdown opens as a full-screen bottom sheet on mobile

---

### Story 20.2.2 — Touch Gestures and Mobile Navigation `[PLANNED]`

#### Backend
*No backend story.*

#### Frontend
*As a mobile user navigating between records, I want to swipe left/right to go back/forward and pull down to refresh lists, so that navigation feels native.*
- Pull-to-refresh on all list pages: `touchstart`/`touchmove` detection; when pull distance > 60px a spinner appears; on release triggers the list reload API call
- Swipe-back gesture: `touchstart`/`touchend` on the left edge (< 20px from screen edge) with rightward swipe > 100px triggers `history.back()`
- Swipe-to-reveal on list rows: left swipe reveals "Delete" (red) action; right swipe reveals "Edit" (blue) action — uses `HammerJS` or native pointer events
- Keyboard: `viewport-fit=cover` meta tag; `padding-bottom: env(safe-area-inset-bottom)` applied to page container for notch/home-indicator devices
- `FlexDrawer` (side nav) supports swipe-from-edge gesture to open; swipe-left to close
- Long-press on a list row opens a context menu (same actions as the row's kebab menu) — alternative to right-click for touch devices

---

### Story 20.2.3 — Mobile Performance Optimization `[PLANNED]`

#### Backend
*As an API, I want paginated list endpoints to support cursor-based pagination as an alternative to offset pagination, so that mobile clients can efficiently load the next page without recalculating offsets.*
- `GET /api/v1/dynamic-data/{entity}/records?cursor={cursor_token}&page_size=20` returns `{items, next_cursor, has_more}`
- Cursor is an opaque base64-encoded token encoding `{last_id, last_sort_value}`; server-side validated and not user-constructible
- Existing offset pagination (`?page=N`) continues to work for backwards compatibility

#### Frontend
*As a user on a mobile device with a slow connection, I want the app to load quickly and scroll smoothly even with large datasets, so that the platform is usable on cellular networks.*
- Code splitting: each page's JS loaded on demand (dynamic `import()`) — initial bundle limited to app shell + auth; pages loaded on first navigation
- Images: all avatars and file previews use `loading="lazy"` + `srcset` for responsive images; WebP format preferred
- `FlexDataGrid` on mobile switches to cursor-based infinite scroll (loads next 20 records on scroll-to-bottom) instead of pagination buttons
- Font loading: `font-display: swap` in CSS; fonts subset to used character ranges
- `IntersectionObserver` used for deferred rendering of off-screen widgets on dashboards
- Lighthouse mobile score target: Performance ≥ 85, Accessibility ≥ 95, Best Practices ≥ 90; measured in CI

---

## Feature 20.3 — Mobile-Specific Features `[PLANNED]`

### Story 20.3.1 — Camera and File Capture `[PLANNED]`

#### Backend
*No backend story — same presigned upload API from Epic 19 is used.*

#### Frontend
*As a field worker attaching a photo to a record, I want to tap "Take Photo" and have my phone's camera open directly, so that I can capture and attach evidence without leaving the app.*
- `FlexFileUpload` on mobile: "Take Photo" button uses `<input type="file" accept="image/*" capture="environment">` to open the rear camera
- "Record Video" and "Capture Document" (PDF scan) options added to the upload action sheet on mobile
- Image captured from camera auto-compressed client-side to < 2MB using Canvas API before presigned upload
- EXIF data (GPS coordinates, timestamp) stripped from images before upload for privacy (unless the entity field has `capture_location: true`)
- Offline capture: photos taken offline stored in IndexedDB as blobs; uploaded automatically when connectivity returns (using Background Sync)

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
- On first login (mobile), prompt "Enable notifications?" — uses `Notification.requestPermission()` before subscribing
- Service worker `push` event handler: displays a system notification via `self.registration.showNotification(title, {body, icon, badge, data})`
- Notification click: service worker `notificationclick` opens the app and navigates to the relevant record/workflow using the `data.url` in the notification payload
- Notification settings page (under `#/settings`): "Push Notifications" section with toggles per notification type (Workflow, Assignments, Mentions, System)
- VAPID public key stored in `appState.config` (fetched from `GET /api/v1/config`); `PushManager.subscribe({userVisibleOnly: true, applicationServerKey})` called with it
- Subscription automatically re-registered if the service worker updates or the subscription expires

---
