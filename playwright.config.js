// @ts-check
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
    testDir: './tests/e2e',
    fullyParallel: false,   // sequential — one browser, shared auth state
    forbidOnly: !!process.env.CI,
    retries: process.env.CI ? 1 : 0,
    workers: 1,
    reporter: [['list'], ['html', { outputFolder: 'tests/e2e/report', open: 'never' }]],
    timeout: 60_000,   // 60s per test — covers UI login (~10s) + assertions
    use: {
        baseURL: process.env.BASE_URL || 'http://localhost:8080',
        headless: true,
        trace: 'retain-on-failure',
        screenshot: 'only-on-failure',
        actionTimeout: 15_000,
        navigationTimeout: 30_000,
    },
    projects: [
        { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    ],
    // No webServer block — stack is started manually via ./manage.sh up
});
