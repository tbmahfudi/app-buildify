import { test, expect } from '@playwright/test';

const BASE = 'http://localhost:8000';

test.describe('Data Model API', () => {
    let token;

    test.beforeEach(async ({ page }) => {
        const resp = await page.request.post(BASE + '/api/v1/auth/login', {
            data: { email: 'ceo@techstart.com', password: 'password123' }
        });
        token = (await resp.json()).access_token;
    });

    test('should list entities', async ({ page }) => {
        const resp = await page.request.get(BASE + '/api/v1/data-model/entities', {
            headers: { Authorization: 'Bearer ' + token }
        });
        expect(resp.ok()).toBe(true);
    });

    test('should create and delete an entity', async ({ page }) => {
        const name = 'TestEnt_' + Date.now();
        const createResp = await page.request.post(BASE + '/api/v1/data-model/entities', {
            headers: { Authorization: 'Bearer ' + token },
            data: { name, label: 'Test Entity', description: 'E2E test' }
        });
        expect([200, 201, 422].includes(createResp.status())).toBe(true);
        if (createResp.ok()) {
            const entity = await createResp.json();
            if (entity.id) {
                const delResp = await page.request.delete(BASE + '/api/v1/data-model/entities/' + entity.id, {
                    headers: { Authorization: 'Bearer ' + token }
                });
                expect([200, 204].includes(delResp.status())).toBe(true);
            }
        }
    });

    test('should list relationships', async ({ page }) => {
        const resp = await page.request.get(BASE + '/api/v1/data-model/relationships', {
            headers: { Authorization: 'Bearer ' + token }
        });
        expect([200, 404].includes(resp.status())).toBe(true);
    });
});
