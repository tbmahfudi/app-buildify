import { test, expect } from '@playwright/test';
import { loginViaApi } from './helpers/login.js';

test.describe('Dashboard', () => {
    test.beforeEach(async ({ page, request }) => {
        await loginViaApi(page, request, 'user');
    });

    test('dashboard route renders content area', async ({ page }) => {
        await page.goto('/#dashboard');
        await expect(page.locator('#content')).toBeVisible();
    });

    test('dashboard page does not show error state', async ({ page }) => {
        await page.goto('/#dashboard');
        await page.waitForTimeout(1000);
        // Should not contain a generic error message
        const content = await page.locator('#content').textContent();
        expect(content).not.toMatch(/500|internal server error/i);
    });

    test('navigation sidebar is present after login', async ({ page }) => {
        await page.goto('/#dashboard');
        // Sidebar or nav element should be visible
        const nav = page.locator('nav, #sidebar, [data-sidebar], .sidebar').first();
        await expect(nav).toBeVisible({ timeout: 8_000 });
    });

    test('can navigate from dashboard to another route', async ({ page }) => {
        await page.goto('/#dashboard');
        await page.goto('/#reports');
        // Content should change (not show same dashboard widgets)
        await page.waitForSelector('#content', { timeout: 8_000 });
        expect(page.url()).toContain('#reports');
    });
});
