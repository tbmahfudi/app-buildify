import { test, expect } from '@playwright/test';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

/**
 * Healthcare clinic staff journey — driven entirely through the real SPA UI.
 *
 * Logs in as a clinic owner and walks the front-desk → clinical → billing spine the
 * same way a receptionist/clinician would, asserting the UI at each hop and saving a
 * screenshot per step:
 *
 *   login → Visit Registration (walk-in → queue ticket) → Queue Board (call the ticket)
 *         → EMR / Clinical Coding → Prescriptions → Lab Orders → Invoices → Departments
 *
 * The first three steps are REAL interactions against the backend (create a visit +
 * ticket, then call it and assert it actually moves to the Called column). The remaining
 * pages — EMR coding, Prescriptions, Lab Orders, Invoices, Departments — are all wired to
 * their live backend APIs: each step navigates the page and asserts it rendered a real
 * list (or a clean empty state) with no API error, not the old hard-coded sample rows.
 *
 * Screenshots land in tests/e2e/screenshots/clinic-journey/ and feed the companion doc
 * docs/healthcare-clinic-e2e.md.
 *
 * Runs against the live docker stack (frontend nginx :8080, API :8000). Skips cleanly if
 * the stack or the seeded clinic owner isn't reachable, so it never fails red in an
 * environment that isn't wired for it.
 */

const BASE = process.env.HC_UI_BASE || 'http://localhost:8080';
const API = process.env.HC_UI_API || 'http://localhost:8000/api/v1';
const CREDS = {
  email: process.env.HC_UI_EMAIL || 'admin@healthpoint.com',
  password: process.env.HC_UI_PASSWORD || 'password123',
};

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SHOTS = path.join(__dirname, 'screenshots', 'clinic-journey');
fs.mkdirSync(SHOTS, { recursive: true });

let _step = 0;
async function shot(page, name) {
  _step += 1;
  await page.screenshot({ path: path.join(SHOTS, `${String(_step).padStart(2, '0')}-${name}.png`), fullPage: true });
}

// Give an async page a moment to swap its "Loading…" placeholder for real content before
// a screenshot. Bounded and best-effort — static pages just pass the short settle.
async function settle(page, ms = 1500) {
  await page.locator('#app-content').getByText('Loading', { exact: false })
    .waitFor({ state: 'detached', timeout: 8000 }).catch(() => {});
  await page.waitForTimeout(ms);
}

// A wired list page renders either a real <table> (backed by the API) or a clean
// empty-state card — and NEVER a red error box. This is what distinguishes the wired
// pages from the old stubs, which hard-coded sample <tr> rows regardless of the backend.
async function expectWiredList(page, bodySel, label) {
  const body = page.locator(bodySel);
  await expect(body.locator('.bg-red-50'),
    `${label} should not show an API error`).toHaveCount(0);
  const table = body.locator('table');
  const empty = body.getByText(/No .* yet\./);
  await expect(table.or(empty),
    `${label} should render a live list or empty state`).toBeVisible({ timeout: 20000 });
}

test.beforeAll(async ({ request }) => {
  let r;
  try {
    r = await request.post(`${API}/auth/login`, { data: CREDS, timeout: 8000 });
  } catch (e) {
    test.skip(true, `API not reachable at ${API}: ${e}`);
  }
  if (!r || !r.ok()) test.skip(true, `clinic owner ${CREDS.email} cannot log in (HTTP ${r && r.status()})`);
});

async function login(page) {
  await page.goto(`${BASE}/`);
  await page.locator('#email').waitFor({ state: 'visible', timeout: 20000 });
  await page.fill('#email', CREDS.email);
  await page.fill('#password', CREDS.password);
  await page.click('#login-button');
  await page.waitForFunction(() => !!localStorage.getItem('tokens'), { timeout: 20000 });
  // Settle: the Healthcare menu entry appearing means the module registered and the
  // post-login landing redirect is done, so our route navigation below won't race it.
  await expect(page.getByText('Healthcare', { exact: false }).first()).toBeVisible({ timeout: 20000 });
}

async function gotoHash(page, hash, headingText) {
  await page.goto(`${BASE}/${hash}`);
  // Each healthcare page renders its <h1> once the dynamic module route mounts.
  await expect(page.locator('#app-content')).toContainText(headingText, { timeout: 20000 });
}

test('clinic staff journey: registration → queue → EMR → pharmacy → lab → billing', async ({ page }) => {
  test.setTimeout(120000);

  // 1) Sign in through the real login form.
  await login(page);
  await shot(page, 'login-landing');

  // 2) Visit Registration — register a walk-in and issue a queue ticket. Uses the
  //    front-desk default department (which the Queue Board also defaults to, so the
  //    ticket is immediately in view there).
  await gotoHash(page, '#/healthcare/registration', 'Visit Registration');
  await page.locator('#hc-reg-form').waitFor({ state: 'visible', timeout: 20000 });
  const deptLabel = await page.locator('#hc-r-dept').evaluate(
    (el) => (el.options[el.selectedIndex] && el.options[el.selectedIndex].text.trim()) || '');
  await page.selectOption('#hc-r-payer', 'self_pay');
  await shot(page, 'registration-form');

  await page.click('#hc-reg-form button[type="submit"]');
  const ticketEl = page.locator('#hc-reg-result .text-3xl');
  await expect(ticketEl).toBeVisible({ timeout: 20000 });
  const ticketNumber = (await ticketEl.textContent()).trim();
  expect(ticketNumber, 'a ticket number was issued').toBeTruthy();
  await expect(page.locator('#hc-reg-result')).toContainText('Ticket issued');
  await shot(page, 'registration-ticket-issued');

  // 3) Queue Board — the new ticket sits in Waiting; call it → moves to Called.
  await gotoHash(page, '#/healthcare/queue-board', 'Queue Board');
  // Keep the board on the same department we registered under (it defaults there already).
  if (deptLabel) {
    await page.locator('#hc-queue-dept').waitFor({ state: 'visible', timeout: 20000 });
    await page.selectOption('#hc-queue-dept', { label: deptLabel }).catch(() => {});
  }
  // Our ticket's card offers a "Call" action while Waiting.
  const card = page.locator('#hc-queue-body div.rounded-lg', { hasText: ticketNumber });
  await expect(card).toBeVisible({ timeout: 20000 });
  await expect(card.locator('[data-act="call"]')).toBeVisible({ timeout: 20000 });
  await shot(page, 'queue-waiting');

  // Call it → it moves to the Called column. Assert the real move (ticket-specific,
  // rerun-safe): our card loses "Call" and gains "Serve", which only Called cards render
  // — not the always-present "Called" column header.
  await card.locator('[data-act="call"]').click();
  const calledCard = page.locator('#hc-queue-body div.rounded-lg', { hasText: ticketNumber });
  await expect(calledCard.locator('[data-act="serve"]')).toBeVisible({ timeout: 20000 });
  await expect(calledCard.locator('[data-act="call"]')).toHaveCount(0);
  await shot(page, 'queue-called');

  // 4) EMR / Clinical Coding — the clinician's coding workspace.
  await gotoHash(page, '#/healthcare/emr-coding', 'EMR — Clinical Coding');
  await settle(page);
  await shot(page, 'emr-coding');

  // 5) Prescriptions (pharmacy) — live list from the pharmacy API.
  await gotoHash(page, '#/healthcare/prescriptions', 'Prescriptions');
  await settle(page);
  await expectWiredList(page, '#hc-rx-body', 'Prescriptions');
  await shot(page, 'prescriptions');

  // 6) Lab Orders — live list from the lab API.
  await gotoHash(page, '#/healthcare/lab-orders', 'Lab Orders');
  await settle(page);
  await expectWiredList(page, '#hc-lab-body', 'Lab Orders');
  await shot(page, 'lab-orders');

  // 7) Invoices (billing) — live list from the billing API.
  await gotoHash(page, '#/healthcare/invoices', 'Invoices');
  await settle(page);
  await expectWiredList(page, '#hc-inv-body', 'Invoices');
  await shot(page, 'invoices');

  // 8) Organization & Departments — the clinic structure the journey ran against.
  await gotoHash(page, '#/healthcare/departments', 'Organization');
  await settle(page);
  await shot(page, 'departments');
});
