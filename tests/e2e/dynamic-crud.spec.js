import { test, expect } from '@playwright/test';
import { loginViaApi } from './helpers/login.js';

test.describe('Dynamic CRUD', () => {
    test.beforeEach(async ({ page, request }) => {
        await loginViaApi(page, request, 'user');
    });

    test('dynamic list route loads without error', async ({ page }) => {
        // Try a common seeded entity name
        await page.goto('/#dynamic/contact/list');
        await page.waitForSelector('#content', { timeout: 10_000 });
        const content = await page.locator('#content').textContent();
        // Should show a list, empty state, or "no entity" — not a hard error
        expect(content).not.toMatch(/uncaught|typeerror|referenceerror/i);
    });

    test('dynamic route for unknown entity shows graceful message', async ({ page }) => {
        await page.goto('/#dynamic/nonexistent_entity_xyz/list');
        await page.waitForSelector('#content', { timeout: 10_000 });
        // Should not throw an unhandled JS error — page should still render
        await expect(page.locator('#content')).toBeVisible();
    });

    test('new record route loads a form', async ({ page }) => {
        await page.goto('/#dynamic/contact/new');
        await page.waitForSelector('#content', { timeout: 10_000 });
        await page.waitForFunction(
            () => {
                const el = document.querySelector('#content');
                return el && el.textContent.trim().length > 20;
            },
            { timeout: 8_000 }
        );
        const content = await page.locator('#content').textContent();
        expect(content).not.toMatch(/uncaught|typeerror/i);
    });
});
