import { login } from './api.js';

const form = document.getElementById('login-form');
const errorDiv = document.getElementById('login-error');
const errorMessage = document.getElementById('error-message');

if (form) {
  form.addEventListener('submit', async (event) => {
    event.preventDefault();

    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const tenantValue = document.getElementById('tenant').value.trim();
    const tenant = tenantValue === '' ? null : tenantValue;

    errorDiv.classList.add('hidden');
    errorMessage.textContent = '';

    try {
      await login(email, password, tenant);
      window.location.href = '/index.html';
    } catch (error) {
      errorMessage.textContent = error.message;
      errorDiv.classList.remove('hidden');
    }
  });
}
