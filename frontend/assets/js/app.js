import { apiFetch } from './api.js';

// Global state
window.appState = {
  user: null,
  currentRoute: 'dashboard'
};

export async function initApp() {
  // Check if logged in
  const token = localStorage.getItem('access_token');
  if (!token) {
    showLogin();
    return;
  }

  // Load user info
  try {
    const response = await apiFetch('/auth/me');
    window.appState.user = await response.json();
    localStorage.setItem('user', JSON.stringify(window.appState.user));
  } catch (error) {
    console.error('Failed to load user:', error);
    showLogin();
    return;
  }

  // Show main app
  showApp();
  
  // Load menu
  await loadMenu();
  
  // Load initial route
  const hash = window.location.hash.slice(1) || 'dashboard';
  await loadRoute(hash);
  
  // Handle hash changes
  window.addEventListener('hashchange', () => {
    const route = window.location.hash.slice(1) || 'dashboard';
    loadRoute(route);
  });

  // Logout button
  document.getElementById('btn-logout').addEventListener('click', logout);
}

function showLogin() {
  document.body.innerHTML = `
    <div class="d-flex align-items-center justify-content-center vh-100 bg-light">
      <div class="card shadow" style="width: 400px;">
        <div class="card-body p-4">
          <h4 class="text-center mb-4">NoCode Platform</h4>
          <form id="login-form">
            <div class="mb-3">
              <label class="form-label">Email</label>
              <input type="email" class="form-control" id="email" required>
            </div>
            <div class="mb-3">
              <label class="form-label">Password</label>
              <input type="password" class="form-control" id="password" required>
            </div>
            <div id="login-error" class="alert alert-danger" style="display:none;"></div>
            <button type="submit" class="btn btn-primary w-100">Login</button>
          </form>
          <div class="mt-3 small text-muted text-center">
            <p class="mb-1">Test Credentials:</p>
            <p class="mb-0">admin@example.com / admin123</p>
          </div>
        </div>
      </div>
    </div>
  `;

  document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    
    try {
      const response = await fetch('http://localhost:8000/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });

      if (!response.ok) {
        throw new Error('Invalid credentials');
      }

      const data = await response.json();
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      
      window.location.reload();
    } catch (error) {
      const errorDiv = document.getElementById('login-error');
      errorDiv.textContent = error.message;
      errorDiv.style.display = 'block';
    }
  });
}

function showApp() {
  document.body.innerHTML = `
    <nav class="navbar navbar-expand navbar-dark bg-dark px-3">
      <span class="navbar-brand">NoCode Platform</span>
      <ul class="navbar-nav ms-auto">
        <li class="nav-item dropdown">
          <a class="nav-link dropdown-toggle" href="#" data-bs-toggle="dropdown">
            ${window.appState.user?.email || 'User'}
          </a>
          <ul class="dropdown-menu dropdown-menu-end">
            <li><a class="dropdown-item" href="#settings">Settings</a></li>
            <li><hr class="dropdown-divider"></li>
            <li><a class="dropdown-item" href="#" id="btn-logout">Logout</a></li>
          </ul>
        </li>
      </ul>
    </nav>
    <div class="d-flex">
      <aside id="sidebar" class="bg-white border-end p-2" style="width:260px; min-height: calc(100vh - 56px);"></aside>
      <main id="content" class="flex-fill p-3" style="min-height: calc(100vh - 56px);"></main>
    </div>
  `;
}

async function loadMenu() {
  try {
    const response = await fetch('/config/menu.json');
    const menu = await response.json();
    
    const sidebar = document.getElementById('sidebar');
    const nav = document.createElement('nav');
    nav.className = 'nav flex-column';
    
    menu.items.forEach(item => {
      const link = document.createElement('a');
      link.className = 'nav-link text-dark';
      link.href = `#${item.route}`;
      link.textContent = item.title;
      link.onclick = () => {
        document.querySelectorAll('#sidebar .nav-link').forEach(l => l.classList.remove('active'));
        link.classList.add('active');
      };
      nav.appendChild(link);
    });
    
    sidebar.appendChild(nav);
  } catch (error) {
    console.error('Failed to load menu:', error);
  }
}

async function loadRoute(route) {
  window.appState.currentRoute = route;
  
  const content = document.getElementById('content');
  content.innerHTML = '<div class="text-center"><div class="spinner-border"></div></div>';
  
  try {
    const response = await fetch(`/assets/templates/${route}.html`);
    if (!response.ok) throw new Error('Template not found');
    
    const html = await response.text();
    content.innerHTML = html;
    
    // Dispatch event for route-specific JS
    document.dispatchEvent(new CustomEvent('route:loaded', { 
      detail: { route } 
    }));
  } catch (error) {
    content.innerHTML = `
      <div class="alert alert-warning">
        <strong>Page not found:</strong> ${route}
      </div>
    `;
  }
}

function logout() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');
  window.location.reload();
}