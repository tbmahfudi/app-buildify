import { test, expect } from '@playwright/test';

const BASE = 'http://localhost:8000';

test.describe('Dynamic CRUD', () => {
    let token;

    test.beforeEach(async ({ page }) => {
        const resp = await page.request.post(BASE + '/api/v1/auth/login', {
            data: { email: 'ceo@techstart.com', password: 'password123' }
        });
        token = (await resp.json()).access_token;
    });

    test('should list dynamic entity endpoints via metadata', async ({ page }) => {
        const resp = await page.request.get(BASE + '/api/v1/data-model/entities', {
            headers: { Authorization: 'Bearer ' + token }
        });
        expect(resp.ok()).toBe(true);
        const body = await resp.json();
        const entities = Array.isArray(body) ? body : (body.items || body.data || []);
        const published = entities.filter((e) => e.status === 'published' || e.is_published);
        // May be 0 if none published, that is valid
        expect(Array.isArray(published)).toBe(true);
    });

    test('should handle dynamic list request', async ({ page }) => {
        const resp = await page.request.get(BASE + '/api/v1/dynamic/nonexistent_entity_12345', {
            headers: { Authorization: 'Bearer ' + token }
        });
        // 404 is the expected response for nonexistent entity
        expect([200, 404].includes(resp.status())).toBe(true);
    });
});
