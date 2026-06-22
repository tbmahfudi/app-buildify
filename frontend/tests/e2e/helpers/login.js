/**
 * E2E login helper
 */
const BASE_URL = 'http://localhost:8000';

export async function loginAs(page, { email, password }) {
    const response = await page.request.post(BASE_URL + '/api/v1/auth/login', {
        data: { email, password }
    });
    if (!response.ok()) {
        throw new Error('Login failed: ' + response.status());
    }
    const data = await response.json();
    const token = data.access_token || data.token;
    if (!token) throw new Error('No access token in response');

    await page.goto('/');
    await page.evaluate((t) => { localStorage.setItem('access_token', t); }, token);
    await page.reload();
}

export async function loginAsTenant(page) {
    await loginAs(page, { email: 'ceo@techstart.com', password: 'password123' });
}

export async function loginAsSuperadmin(page) {
    await loginAs(page, { email: 'superadmin@system.com', password: 'SuperAdmin123!' });
}
