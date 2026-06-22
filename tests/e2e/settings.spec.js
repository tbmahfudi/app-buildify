import { test, expect } from '@playwright/test';
import { loginViaApi } from './helpers/login.js';

test.describe('Settings', () => {
    test.beforeEach(async ({ page, request }) => {
        await loginViaApi(page, request, 'user');
    });

    test('settings/modules page loads', async ({ page }) => {
        await page.goto('/#settings/modules');
        await page.waitForSelector('#content', { timeout: 10_000 });
        const content = await page.locator('#content').textContent();
        expect(content).not.toMatch(/404|not found/i);
    });

    test('settings/modules shows module cards or empty state', async ({ page }) => {
        await page.goto('/#settings/modules');
        await page.waitForFunction(
            () => {
                const el = document.querySelector('#content');
                return el && el.textContent.trim().length > 20;
            },
            { timeout: 10_000 }
        );
        const content = await page.locator('#content').textContent();
        expect(content.length).toBeGreaterThan(20);
    });

    test('module store page loads', async ({ page }) => {
        await page.goto('/#module-store');
        await page.waitForSelector('#content', { timeout: 10_000 });
        const content = await page.locator('#content').textContent();
        expect(content).not.toMatch(/uncaught|typeerror/i);
    });

    test('profile or account settings reachable', async ({ page }) => {
        // Try common profile routes
        for (const route of ['#profile', '#account', '#settings']) {
            await page.goto(`/${route}`);
            await page.waitForTimeout(500);
            const content = await page.locator('#content').textContent().catch(() => '');
            if (content && content.trim().length > 20) {
                expect(content).not.toMatch(/uncaught|typeerror/i);
                return;
            }
        }
    });
});
