/**
 * Shared login helper for Playwright E2E tests.
 *
 * Uses Node.js native fetch (Node 18+) to get a token, then injects it into
 * localStorage via addInitScript before the SPA starts so no redirect occurs.
 */

export const USERS = {
    user: {
        email: process.env.E2E_USER_EMAIL || 'ceo@techstart.com',
        password: process.env.E2E_USER_PASSWORD || 'password123',
    },
    superadmin: {
        email: process.env.E2E_SU_EMAIL || 'superadmin@system.com',
        password: process.env.E2E_SU_PASSWORD || 'SuperAdmin123!',
    },
};

const API_BASE = process.env.API_BASE || 'http://localhost:8000';

/**
 * Log in via the UI form (slower, but always works).
 *
 * After a successful UI login, login.html does `window.location.href = '/'`
 * which causes the SPA to load WITHOUT a hash fragment. The SPA then calls
 * loadRoute('dashboard') which renders content but does NOT update the hash.
 * Waiting for `window.location.hash !== ''` therefore never resolves.
 * Instead we wait for the #content element to be populated.
 */
export async function loginAs(page, role = 'user') {
    const { email, password } = USERS[role];
    await page.goto('/', { waitUntil: 'domcontentloaded' });
    await page.waitForSelector('#email, input[type="email"]', { timeout: 10_000 });
    await page.locator('#email, input[type="email"]').first().fill(email);
    await page.locator('#password, input[type="password"]').first().fill(password);
    await page.locator('#login-button, button[type="submit"]').first().click();
    // Wait for the SPA to load and render the content area after login redirect
    await page.waitForSelector('#content', { timeout: 25_000 });
    await page.waitForFunction(
        () => {
            const el = document.querySelector('#content');
            return el && el.textContent.trim().length > 20;
        },
        { timeout: 20_000 }
    );
}

/**
 * Fast login: fetch token via Node fetch, inject into localStorage via addInitScript,
 * then navigate straight to the app. Falls back to UI login on error.
 *
 * The app (auth-service.js) reads: localStorage.getItem('tokens') → JSON { access, refresh }
 *
 * @param {import('@playwright/test').Page} page
 * @param {unknown} _request - unused (kept for signature compat)
 * @param {'user'|'superadmin'} role
 */
export async function loginViaApi(page, _request, role = 'user') {
    const { email, password } = USERS[role];

    let accessToken = null;
    let refreshToken = null;

    try {
        const controller = new AbortController();
        const tid = setTimeout(() => controller.abort(), 5_000);
        const res = await fetch(`${API_BASE}/api/v1/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password }),
            signal: controller.signal,
        });
        clearTimeout(tid);
        if (res.ok) {
            const body = await res.json();
            accessToken = body.access_token ?? null;
            refreshToken = body.refresh_token ?? null;
        }
    } catch {
        // fetch failed or timed out — fall back to UI login
    }

    if (accessToken) {
        // addInitScript runs BEFORE any page JS, so localStorage is ready when the SPA boots
        await page.addInitScript(
            ({ at, rt }) => {
                try {
                    localStorage.setItem('tokens', JSON.stringify({ access: at, refresh: rt }));
                } catch {}
            },
            { at: accessToken, rt: refreshToken }
        );
        await page.goto('/#dashboard', { waitUntil: 'domcontentloaded' });
        await page.waitForSelector('#content', { timeout: 12_000 });
    } else {
        await loginAs(page, role);
    }
}
