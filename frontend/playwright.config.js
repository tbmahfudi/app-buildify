import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
    testDir: './tests/e2e',
    fullyParallel: false,
    forbidOnly: !!process.env.CI,
    retries: 0,
    workers: 1,
    reporter: [['html', { open: 'never' }], ['list']],
    timeout: 30000,
    use: {
        baseURL: 'http://localhost:8080',
        headless: true,
        viewport: { width: 1280, height: 720 },
        screenshot: 'only-on-failure',
        video: 'off',
    },
    projects: [
        {
            name: 'chromium',
            use: { ...devices['Desktop Chrome'] }
        }
    ]
});
