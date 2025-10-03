import { initRouter, navigate } from './router.js';
import { login, logout, tokens } from './api.js';

async function loadMenu() {
  const resp = await fetch('assets/config/menu.json');
  const menu = await resp.json();
  const s = document.getElementById('sidebar');
  s.innerHTML = '';
  menu.items.forEach(i => {
    const a = document.createElement('a');
    a.href = `#${i.route}`;
    a.className = 'd-block py-2 px-2';
    a.textContent = i.title;
    s.appendChild(a);
  });
}

function requireAuth() {
  const hasToken = !!(tokens && tokens.access);
  if (!hasToken) {
    location.hash = '#login';
    return false;
  }
  return true;
}

function wireGlobalLogout() {
  const btn = document.getElementById('btn-logout');
  if (btn) {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      logout();
      location.hash = '#login';
    });
  }
}

function routeGuards() {
  document.addEventListener('route:loaded', (e) => {
    const route = e.detail.route;
    if (route !== 'login' && !requireAuth()) return;

    if (route === 'login') {
      const form = document.getElementById('login-form');
      if (form) {
        form.addEventListener('submit', async (ev) => {
          ev.preventDefault();
          const email = document.getElementById('email').value.trim();
          const password = document.getElementById('password').value;
          const tenant = document.getElementById('tenant').value.trim();
          const btn = document.getElementById('btn-login');
          const err = document.getElementById('login-error');
          btn.disabled = true; err.textContent = '';
          try {
            await login(email, password, tenant || null);
            await loadMenu();
            location.hash = '#dashboard';
          } catch (e) {
            err.textContent = e.message;
          } finally {
            btn.disabled = false;
          }
        });
      }
    }
  });
}

async function initApp() {
  wireGlobalLogout();
  await loadMenu();
  initRouter();
  if (!tokens || !tokens.access) {
    location.hash = '#login';
  } else {
    if (!location.hash) location.hash = '#dashboard';
  }
}

export { initApp };
