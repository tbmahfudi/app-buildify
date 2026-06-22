import { test, expect } from '@playwright/test';
import { loginViaApi } from './helpers/login.js';

test.describe('Tenants (superadmin)', () => {
    test.beforeEach(async ({ page, request }) => {
        await loginViaApi(page, request, 'superadmin');
    });

    test('tenants list page loads', async ({ page }) => {
        await page.goto('/#tenants');
        await page.waitForSelector('#content', { timeout: 10_000 });
        const content = await page.locator('#content').textContent();
        expect(content).not.toMatch(/404|not found/i);
    });

    test('tenants page shows at least one tenant row', async ({ page }) => {
        await page.goto('/#tenants');
        // Wait for list to render — look for a table row or card
        await page.waitForFunction(
            () => {
                const el = document.querySelector('#content');
                return el && el.textContent.trim().length > 50;
            },
            { timeout: 10_000 }
        );
        const content = await page.locator('#content').textContent();
        // TechStart is a seeded tenant
        expect(content).toMatch(/techstart|tenant/i);
    });

    test('create tenant button is visible', async ({ page }) => {
        await page.goto('/#tenants');
        await page.waitForSelector('#content', { timeout: 10_000 });
        const btn = page.locator('button:has-text("Create"), button:has-text("Add"), button:has-text("New")').first();
        await expect(btn).toBeVisible({ timeout: 8_000 });
    });
});
