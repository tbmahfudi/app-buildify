import { apiFetch, login, logout as apiLogout } from './api.js';

// Global state
window.appState = {
  user: null,
  currentRoute: 'dashboard'
};

export async function initApp() {
  // Check if logged in
  const token = localStorage.getItem('access_token');
  if (!token) {
    window.location.href = '/assets/pages/login.html';
    return;
  }

  // Load user info
  try {
    const response = await apiFetch('/auth/me');
    if (!response.ok) throw new Error('Auth failed');
    window.appState.user = await response.json();
    localStorage.setItem('user', JSON.stringify(window.appState.user));
  } catch (error) {
    console.error('Failed to load user:', error);
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    window.location.href = '/assets/pages/login.html';
    return;
  }

  // Setup main layout
  setupMainLayout();
  
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
  const logoutBtn = document.getElementById('btn-logout');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', (e) => {
      e.preventDefault();
      apiLogout();
      window.location.href = '/assets/pages/login.html';
    });
  }
}

function setupMainLayout() {
  // Set user email in navbar
  const userEmail = document.getElementById('user-email');
  if (userEmail) {
    userEmail.textContent = window.appState.user?.email || 'User';
  }
}

async function loadMenu() {
  try {
    const response = await fetch('/config/menu.json');
    const menu = await response.json();
    
    const navContainer = document.getElementById('sidebar-nav');
    if (!navContainer) return;
    
    navContainer.innerHTML = '';
    
    menu.items.forEach(item => {
      const link = document.createElement('a');
      link.className = 'nav-link block px-4 py-2 rounded-lg text-gray-800 hover:bg-gray-100 transition';
      link.href = `#${item.route}`;
      link.textContent = item.title;
      link.onclick = (e) => {
        document.querySelectorAll('#sidebar-nav .nav-link').forEach(l => {
          l.classList.remove('active', 'bg-blue-100', 'text-blue-600');
        });
        link.classList.add('active', 'bg-blue-100', 'text-blue-600');
      };
      navContainer.appendChild(link);
    });
  } catch (error) {
    console.error('Failed to load menu:', error);
  }
}

async function loadRoute(route) {
  window.appState.currentRoute = route;
  
  const content = document.getElementById('content');
  content.innerHTML = '<div class="flex items-center justify-center h-full"><div class="text-center"><div class="inline-block"><div class="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div></div><p class="mt-3 text-gray-600">Loading...</p></div></div>';
  
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
      <div class="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
        <strong class="text-yellow-800">Page not found:</strong>
        <p class="text-yellow-700">${route}</p>
      </div>
    `;
  }
}