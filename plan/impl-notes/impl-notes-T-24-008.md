# impl-notes-T-24-008

**Task**: Honesty banner, reports-designer redirect, debug-financial-module deletion, dev-route removal.

## What was done

### Notification honesty banner (Story 24.1.2)
- Updated `frontend/assets/js/settings-notifications.js`.
- Added `_prependHonestyBanner()` called on `route:loaded` for `settings-notifications`.
- Inserts a `role="alert"` warning div with `ph-envelope-simple-slash` icon before any page content.
- Text: "Email notifications are not yet active — configuration in progress."
- Guard: checks for `#notif-honesty-banner` to prevent double-insertion.

### reports-designer redirect (Story 24.1.3)
- Redirect `#reports-designer` → `#report-designer` already present in `app.js` line 1597 from earlier work.
- No `frontend/assets/templates/reports-designer.html` existed — already absent.
- `report-designer-page.js` comment referencing `reports-designer` is documentation only; no runtime impact.

### debug-financial-module.html deletion
- Verified `frontend/debug-financial-module.html` had no references from any JS file (grep returned nothing).
- File deleted.

### Dev-route removal (Story 24.7.1 / T-24.030)
- Removed the `flex-layout-sandbox` and `builder-showcase` individual route handlers from `loadRoute()`.
- Added `_DEV_ROUTES` Set containing all 5 dev routes: `flex-layout-sandbox`, `builder-showcase`,
  `components-showcase`, `datatable`, `debug-financial-module`.
- Added `_showDevBanner(container, route)` function rendering an informational message.
- `_DEV_ROUTES.has(route)` guard fires before any template loading, ensuring direct-URL
  navigation hits the banner instead of a broken page.
- `components-showcase` was in `getMenuIcon()` icon map — no removal needed (it just returns
  a fallback icon if the key is queried; the route itself is gated by the dev-banner guard).

## Files changed
- `frontend/assets/js/settings-notifications.js`
- `frontend/assets/js/app.js`
- `frontend/debug-financial-module.html` (deleted)
