import { test, expect } from '@playwright/test';
import { execSync } from 'child_process';

// UI coverage for the profile-page Two-Factor Authentication card (ADR-011 S5),
// driving the real SPA against the live stack. The happy path needs the OTP code,
// which only Redis has, so it reads it out of the dev Redis container (as the
// backend e2e does). Skips cleanly if Redis/docker isn't reachable from the host.

const BASE = 'http://localhost:8080';
const API = 'http://localhost:8000/api/v1';
const CREDS = { email: 'ceo@techstart.com', password: 'password123' };
const PREFIX = 'ui-mfa-';

function redis(args) {
  return execSync(`docker exec app_buildify_redis redis-cli ${args}`).toString().trim();
}

async function apiToken(request) {
  const r = await request.post(`${API}/auth/login`, { data: CREDS });
  return (await r.json()).access_token;
}

// Remove any factors a prior run left behind so the suite is idempotent.
async function cleanupFactors(request) {
  const token = await apiToken(request);
  const headers = { Authorization: `Bearer ${token}` };
  const list = await (await request.get(`${API}/mfa/factors`, { headers })).json();
  for (const f of list) {
    if (String(f.target).startsWith(PREFIX)) {
      await request.delete(`${API}/mfa/factors/${f.id}`, { headers });
    }
  }
}

test.beforeEach(async ({ request }) => {
  try {
    await cleanupFactors(request);
    redis(`--scan --pattern 'otp:daily:*' | xargs -r docker exec app_buildify_redis redis-cli del`);
  } catch (_) {
    test.skip(true, 'docker/redis not reachable from test host');
  }
});

test('profile MFA card: enroll email -> verify -> active -> remove', async ({ page }) => {
  const target = `${PREFIX}${Date.now()}@example.com`;

  // Log in through the real UI form.
  await page.goto(`${BASE}/`);
  await page.locator('#email').waitFor({ state: 'visible', timeout: 20000 });
  await page.fill('#email', CREDS.email);
  await page.fill('#password', CREDS.password);
  await page.click('#login-button');
  await page.waitForFunction(() => !!localStorage.getItem('tokens'), { timeout: 20000 });

  // Go to the profile route and find the MFA card. Wait for the list to finish
  // loading (not the template's "Loading…") — that also means initMfaPanel has run
  // and the enroll button's click handler is attached.
  await page.goto(`${BASE}/#profile`);
  await page.locator('#mfa-list').waitFor({ state: 'visible', timeout: 20000 });
  await expect(page.locator('#mfa-list')).not.toContainText('Loading', { timeout: 20000 });

  // Enroll an email factor → verify step reveals, a Pending row appears.
  await page.selectOption('#mfa-type', 'email_otp');
  await page.fill('#mfa-target', target);
  await page.click('#mfa-send-btn');
  await page.locator('#mfa-verify').waitFor({ state: 'visible', timeout: 10000 });
  await expect(page.locator('#mfa-list')).toContainText(target);
  await expect(page.locator('#mfa-list')).toContainText('Pending');

  // Read the real code from Redis and verify → factor flips to Active.
  let code = null;
  for (let i = 0; i < 10 && !code; i++) {
    const key = redis(`--scan --pattern 'otp:code:mfa:email:*:${target}' | head -1`);
    code = key ? redis(`get '${key}'`) : null;
    if (!code) await page.waitForTimeout(500);
  }
  expect(code).toMatch(/^\d{6}$/);
  await page.fill('#mfa-code', code);
  await page.click('#mfa-verify-btn');
  await expect(page.locator('#mfa-list')).toContainText('Active', { timeout: 10000 });
  await expect(page.locator('#mfa-verify')).toBeHidden();

  // Remove it → the row disappears.
  await page.click('[data-mfa-remove]');
  await expect(page.locator('#mfa-list')).not.toContainText(target, { timeout: 10000 });
});
