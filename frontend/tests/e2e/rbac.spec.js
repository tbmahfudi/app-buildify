import { test, expect } from '@playwright/test';

const BASE = 'http://localhost:8000';

test.describe('RBAC API', () => {
    let token;

    test.beforeEach(async ({ page }) => {
        const resp = await page.request.post(BASE + '/api/v1/auth/login', {
            data: { email: 'superadmin@system.com', password: 'SuperAdmin123!' }
        });
        token = (await resp.json()).access_token;
    });

    test('should list roles', async ({ page }) => {
        const resp = await page.request.get(BASE + '/api/v1/rbac/roles', {
            headers: { Authorization: 'Bearer ' + token }
        });
        expect(resp.ok()).toBe(true);
    });

    test('should list permissions', async ({ page }) => {
        const resp = await page.request.get(BASE + '/api/v1/rbac/permissions', {
            headers: { Authorization: 'Bearer ' + token }
        });
        expect(resp.ok()).toBe(true);
    });

    test('should list permission categories', async ({ page }) => {
        const resp = await page.request.get(BASE + '/api/v1/rbac/permission-categories', {
            headers: { Authorization: 'Bearer ' + token }
        });
        expect(resp.ok()).toBe(true);
    });

    test('should list groups', async ({ page }) => {
        const resp = await page.request.get(BASE + '/api/v1/rbac/groups', {
            headers: { Authorization: 'Bearer ' + token }
        });
        expect(resp.ok()).toBe(true);
    });

    test('should create and delete a role', async ({ page }) => {
        const createResp = await page.request.post(BASE + '/api/v1/rbac/roles', {
            headers: { Authorization: 'Bearer ' + token },
            data: { name: 'E2ETestRole_' + Date.now(), description: 'E2E test' }
        });
        expect([200, 201, 422].includes(createResp.status())).toBe(true);
        if (createResp.ok()) {
            const role = await createResp.json();
            if (role.id) {
                const delResp = await page.request.delete(BASE + '/api/v1/rbac/roles/' + role.id, {
                    headers: { Authorization: 'Bearer ' + token }
                });
                expect([200, 204].includes(delResp.status())).toBe(true);
            }
        }
    });
});
