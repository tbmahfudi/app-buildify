// @ts-check
import { test, expect } from '@playwright/test';

/**
 * Drives the real MFA login challenge in a browser (ADR-HC-009 D3/D4).
 *
 * This is the test that catches what the API tests cannot: that the SPA actually
 * hands off to the code step instead of storing `undefined` tokens. `res.ok` is
 * true for a 202, so a login page that does not special-case it fails *silently*
 * rather than erroring.
 *
 * Enrolls MFA on a throwaway user and deletes it afterwards, so no shared seeded
 * account is ever left needing a code.
 */

const API = 'http://localhost:8000/api/v1';
const SU = { email: 'superadmin@system.com', password: 'SuperAdmin123!' };
const PASSWORD = 'BrowserMfa123!';

async function suToken(request) {
  const r = await request.post(`${API}/auth/login`, { data: SU });
  return (await r.json()).access_token;
}

/** The emailed code, read out of MailHog. */
async function codeFor(request, target) {
  const r = await request.get(`http://localhost:8025/api/v2/search?kind=to&query=${encodeURIComponent(target)}`);
  const items = (await r.json()).items || [];
  if (!items.length) throw new Error(`no email for ${target}`);
  const body = items[0].Content.Body;
  const m = body.match(/\b(\d{6})\b/);
  if (!m) throw new Error(`no 6-digit code in email to ${target}`);
  return m[1];
}

test.describe('MFA login challenge', () => {
  let user;

  test.beforeEach(async ({ request }) => {
    const token = await suToken(request);
    const auth = { Authorization: `Bearer ${token}` };

    // Each test gets a fresh user and a fresh delivery target, so the per-target
    // and per-account OTP caps (R6) never bind. The per-IP cap is the shared one;
    // this suite stays well under it.
    const tenantsRes = await request.get(`${API}/org/tenants`, { headers: auth });
    const tenantsBody = await tenantsRes.json();
    const tenants = tenantsBody.items || tenantsBody;
    const tenantId = tenants[0].id;

    const suffix = Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
    const email = `pw-mfa-${suffix}@example.com`;
    const target = `pw-mfa-target-${suffix}@example.com`;

    const created = await request.post(`${API}/org/users`, {
      headers: auth,
      data: { email, full_name: 'Playwright MFA', password: PASSWORD, tenant_id: tenantId },
    });
    expect(created.ok(), `create user: ${created.status()} ${await created.text()}`).toBeTruthy();

    // Enroll + activate an email factor as that user.
    const loginRes = await request.post(`${API}/auth/login`, { data: { email, password: PASSWORD } });
    const userToken = (await loginRes.json()).access_token;
    const userAuth = { Authorization: `Bearer ${userToken}` };

    const enrolled = await request.post(`${API}/mfa/factors`, {
      headers: userAuth,
      data: { factor_type: 'email_otp', target },
    });
    expect(enrolled.ok(), `enroll: ${enrolled.status()} ${await enrolled.text()}`).toBeTruthy();
    const factorId = (await enrolled.json()).factor_id;

    const verified = await request.post(`${API}/mfa/factors/${factorId}/verify`, {
      headers: userAuth,
      data: { code: await codeFor(request, target) },
    });
    expect(verified.ok(), `activate: ${verified.status()} ${await verified.text()}`).toBeTruthy();

    user = { email, target, userAuth };
  });

  test.afterEach(async ({ request }) => {
    // The platform has no delete-user endpoint, so the throwaway account row stays
    // behind. Strip its factors instead — that is what matters, since an account
    // left holding an active factor can no longer log in with a password alone.
    // Removing a factor also revokes that user's trusted devices (D4).
    if (!user?.userAuth) return;
    const listed = await request.get(`${API}/mfa/factors`, { headers: user.userAuth });
    if (!listed.ok()) return;
    for (const f of await listed.json()) {
      await request.delete(`${API}/mfa/factors/${f.id}`, { headers: user.userAuth });
    }
  });

  test('password alone shows the code step, not the app', async ({ page, request }) => {
    await page.goto('/assets/templates/login.html');

    await page.fill('#email', user.email);
    await page.fill('#password', PASSWORD);
    await page.click('#login-button');

    // The challenge card replaces the login card.
    await expect(page.locator('#mfa-view')).toBeVisible();
    await expect(page.locator('#login-form')).toBeHidden();

    // ...and it tells the user where the code went, masked.
    const sentTo = await page.locator('#mfa-sent-to').textContent();
    expect(sentTo).toContain('@example.com');
    expect(sentTo).not.toBe(user.target);

    // Critically: no tokens were stored. A 202 is `res.ok`, so a naive login page
    // would have saved `undefined` here and "succeeded".
    const stored = await page.evaluate(() => localStorage.getItem('tokens'));
    expect(stored === null || !JSON.parse(stored).access).toBeTruthy();
  });

  test('a wrong code shows an error and keeps the user on the code step', async ({ page }) => {
    await page.goto('/assets/templates/login.html');
    await page.fill('#email', user.email);
    await page.fill('#password', PASSWORD);
    await page.click('#login-button');
    await expect(page.locator('#mfa-view')).toBeVisible();

    await page.fill('#mfa-code', '000000');
    await page.click('#mfa-verify-btn');

    await expect(page.locator('#mfa-error')).toBeVisible();
    await expect(page.locator('#mfa-view')).toBeVisible();
  });

  test('the right code signs the user in', async ({ page, request }) => {
    await page.goto('/assets/templates/login.html');
    await page.fill('#email', user.email);
    await page.fill('#password', PASSWORD);
    await page.click('#login-button');
    await expect(page.locator('#mfa-view')).toBeVisible();

    await page.fill('#mfa-code', await codeFor(request, user.target));
    await page.click('#mfa-verify-btn');

    // Lands in the SPA, with real tokens.
    await page.waitForURL((url) => !url.pathname.includes('login.html'), { timeout: 15000 });
    const stored = await page.evaluate(() => localStorage.getItem('tokens'));
    expect(JSON.parse(stored).access).toBeTruthy();
  });

  test('remember this device skips the challenge next time', async ({ page, request, context }) => {
    await page.goto('/assets/templates/login.html');
    await page.fill('#email', user.email);
    await page.fill('#password', PASSWORD);
    await page.click('#login-button');
    await expect(page.locator('#mfa-view')).toBeVisible();

    await page.check('#mfa-remember');
    await page.fill('#mfa-code', await codeFor(request, user.target));
    await page.click('#mfa-verify-btn');
    await page.waitForURL((url) => !url.pathname.includes('login.html'), { timeout: 15000 });

    // The device cookie is set and script cannot read it (HttpOnly).
    const cookies = await context.cookies();
    expect(cookies.find((c) => c.name === 'tdid')?.httpOnly).toBe(true);
    const visibleToScript = await page.evaluate(() => document.cookie);
    expect(visibleToScript).not.toContain('tdid');

    // Log in again in the same browser: straight through, no code step.
    // Navigate first, *then* clear the tokens — clearing them while the SPA is
    // still loaded makes app.js bounce to the login page itself and abort this
    // navigation out from under us.
    await page.goto('/assets/templates/login.html', { waitUntil: 'domcontentloaded' });
    await page.evaluate(() => localStorage.clear());
    await page.fill('#email', user.email);
    await page.fill('#password', PASSWORD);
    await page.click('#login-button');

    await page.waitForURL((url) => !url.pathname.includes('login.html'), { timeout: 15000 });
    await expect(page.locator('#mfa-view')).toHaveCount(0);
  });

  test('back to sign in abandons the challenge', async ({ page }) => {
    await page.goto('/assets/templates/login.html');
    await page.fill('#email', user.email);
    await page.fill('#password', PASSWORD);
    await page.click('#login-button');
    await expect(page.locator('#mfa-view')).toBeVisible();

    await page.click('#mfa-cancel');
    await expect(page.locator('#login-form')).toBeVisible();
    await expect(page.locator('#mfa-view')).toBeHidden();
  });
});
