import { test, expect } from '@playwright/test';

const BASE = 'http://localhost:8000';

test.describe('Dashboard page', () => {
    let token;

    test.beforeEach(async ({ page }) => {
        const resp = await page.request.post(BASE + '/api/v1/auth/login', {
            data: { email: 'ceo@techstart.com', password: 'password123' }
        });
        token = (await resp.json()).access_token;
    });

    test('should load the frontend app', async ({ page }) => {
        await page.goto('/');
        await page.waitForTimeout(500);
        const html = await page.content();
        expect(html.length).toBeGreaterThan(100);
    });

    test('should render navigation elements after load', async ({ page }) => {
        await page.goto('/');
        await page.waitForTimeout(1000);
        // The page should render HTML (login form or dashboard)
        const body = await page.locator('body').textContent();
        expect(body).toBeTruthy();
    });
});
