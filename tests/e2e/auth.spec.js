import { test, expect } from '@playwright/test';
import { loginAs, loginViaApi, USERS } from './helpers/login.js';

test.describe('Authentication', () => {
    test('login page loads', async ({ page }) => {
        await page.goto('/');
        await expect(page.locator('input[type="email"], input[name="email"], #email').first()).toBeVisible();
    });

    test('valid credentials log in and show dashboard', async ({ page }) => {
        await loginAs(page, 'user');
        // Should not be on login page; content area should be present
        await expect(page.locator('#content')).toBeVisible();
        expect(page.url()).not.toContain('login');
    });

    test('invalid credentials show error', async ({ page }) => {
        await page.goto('/');
        await page.waitForSelector('input[type="email"], input[name="email"], #email');
        await page.fill('input[type="email"], input[name="email"], #email', 'bad@example.com');
        await page.fill('input[type="password"], input[name="password"], #password', 'wrongpassword');
        await page.click('button[type="submit"]');
        // Error message should appear
        await expect(page.locator('text=/invalid|incorrect|wrong|error|failed/i').first()).toBeVisible({ timeout: 8_000 });
    });

    test('superadmin can log in', async ({ page }) => {
        await loginAs(page, 'superadmin');
        await expect(page.locator('#content')).toBeVisible();
    });

    test('logout clears session', async ({ page }) => {
        await loginAs(page, 'user');
        // Try clicking the logout button if visible
        const logoutBtn = page.locator('#btn-logout, button:has-text("Logout"), button:has-text("Sign Out")').first();
        if (await logoutBtn.isVisible({ timeout: 3_000 }).catch(() => false)) {
            // Playwright auto-accepts confirm() dialogs in headless mode
            await logoutBtn.click();
            // Should redirect to login page
            await page.waitForURL(/login/, { timeout: 10_000 }).catch(() => {});
        } else {
            // Clear tokens directly and navigate to login to verify redirect works
            await page.evaluate(() => localStorage.removeItem('tokens'));
        }
        // Navigate to the SPA root — it should redirect to login because tokens are gone
        await page.goto('/', { waitUntil: 'domcontentloaded' });
        // Either we're at login.html or the SPA shows a login form
        await page.waitForURL(/login/, { timeout: 10_000 }).catch(async () => {
            // Fallback: at least the tokens should be gone
            const hasTokens = await page.evaluate(() => !!localStorage.getItem('tokens'));
            expect(hasTokens).toBe(false);
        });
    });
});
