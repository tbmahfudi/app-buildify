import { apiFetch, login, logout as apiLogout } from './api.js';
import { showToast, showLoading, hideLoading } from './ui-utils.js';
import { filterMenuByRole, applyRBACToElements } from './rbac.js';
import { moduleLoader, moduleRegistry } from './core/module-system/index.js';

// Module-level state (not polluting global namespace)
const appState = {
  user: null,
  currentRoute: 'dashboard'
};

// Export state getter for other modules
export function getAppState() {
  return appState;
}

export function getCurrentUser() {
  return appState.user;
}

export async function initApp() {
  // Check if logged in
  const tokensStr = localStorage.getItem('tokens');
  
  if (!tokensStr) {
    window.location.href = '/assets/templates/login.html';
    return;
  }

  showLoading();

  // Load user info
  try {
    const response = await apiFetch('/auth/me');

    if (!response.ok) throw new Error('Auth failed');

    appState.user = await response.json();

    // Update UI with user info
    updateUserInfo();
    
  } catch (error) {
    console.error('Failed to load user:', error);
    localStorage.removeItem('tokens');
    window.location.href = '/assets/templates/login.html';
    return;
  } finally {
    hideLoading();
  }

  // Setup main layout
  setupEventListeners();

  // Load enabled modules
  try {
    console.log('Loading enabled modules...');
    await moduleLoader.loadAllModules();

    // Register loaded modules
    for (const module of moduleLoader.getAllModules()) {
      moduleRegistry.register(module);
    }

    console.log(`✓ ${moduleRegistry.getModuleCount()} modules loaded and registered`);
  } catch (error) {
    console.error('Failed to load modules:', error);
    // Continue even if modules fail to load
  }

  // Load menu (now includes module menu items)
  await loadMenu();

  // Load initial route
  const hash = window.location.hash.slice(1) || 'dashboard';
  await loadRoute(hash);
  
  // Handle hash changes
  window.addEventListener('hashchange', () => {
    const route = window.location.hash.slice(1) || 'dashboard';
    loadRoute(route);
  });
}

function updateUserInfo() {
  const userEmailEl = document.getElementById('user-email');
  const userEmailDropdown = document.getElementById('user-email-dropdown');

  if (userEmailEl && appState.user) {
    userEmailEl.textContent = appState.user.email;
  }

  if (userEmailDropdown && appState.user) {
    userEmailDropdown.textContent = appState.user.email;
  }
}

function setupEventListeners() {
  // Logout button
  const logoutBtn = document.getElementById('btn-logout');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', (e) => {
      e.preventDefault();
      handleLogout();
    });
  }
}

async function handleLogout() {
  if (!window.confirm('Are you sure you want to logout?')) {
    return;
  }
  
  apiLogout();
  window.location.href = '/assets/templates/login.html';
}

async function loadMenu() {
  try {
    const response = await fetch('/config/menu.json');
    const menu = await response.json();

    // Get menu items from loaded modules
    const moduleMenuItems = await moduleRegistry.getAccessibleMenuItems();

    // Convert module menu items to core menu format
    const moduleMenuFormatted = moduleMenuItems.map(item => ({
      title: item.menu?.label || item.name,
      route: item.path.replace('#/', ''),
      icon: item.menu?.icon || 'bi-circle',
      permission: item.permission
    }));

    // Merge core menu with module menu items
    const allMenuItems = [...menu.items, ...moduleMenuFormatted];

    // Filter menu items based on user roles and permissions
    const filteredItems = filterMenuByRole(allMenuItems);

    const navContainer = document.getElementById('sidebar-nav');
    if (!navContainer) return;

    navContainer.innerHTML = '';

    filteredItems.forEach(item => {
      // If item has submenu, create an expandable menu
      if (item.submenu && item.submenu.length > 0) {
        const menuGroup = createSubmenuItem(item);
        navContainer.appendChild(menuGroup);
      } else {
        const link = createMenuItem(item);
        navContainer.appendChild(link);
      }
    });

    // Set initial active state
    updateActiveMenuItem();

  } catch (error) {
    console.error('Failed to load menu:', error);
    showToast('Failed to load menu', 'error');
  }
}

function createMenuItem(item) {
  const link = document.createElement('a');
  link.className = 'flex items-center gap-3 px-4 py-3 rounded-lg text-gray-700 hover:bg-gray-100 hover:text-blue-600 transition-colors group';
  link.href = `#${item.route}`;

  // Use icon from menu item or fallback to getMenuIcon
  const icon = item.icon || getMenuIcon(item.route);
  link.innerHTML = `
    <i class="bi ${icon} text-lg"></i>
    <span class="font-medium">${item.title}</span>
  `;

  link.onclick = (e) => {
    // Update active state
    document.querySelectorAll('#sidebar-nav a').forEach(l => {
      l.classList.remove('bg-blue-50', 'text-blue-600');
      l.classList.add('text-gray-700');
    });
    link.classList.add('bg-blue-50', 'text-blue-600');
    link.classList.remove('text-gray-700');
  };

  return link;
}

function createSubmenuItem(item) {
  const container = document.createElement('div');
  container.className = 'submenu-container';

  // Create parent item
  const parent = document.createElement('div');
  parent.className = 'flex items-center justify-between px-4 py-3 rounded-lg text-gray-700 hover:bg-gray-100 cursor-pointer transition-colors';

  const icon = item.icon || getMenuIcon(item.route);
  parent.innerHTML = `
    <div class="flex items-center gap-3">
      <i class="bi ${icon} text-lg"></i>
      <span class="font-medium">${item.title}</span>
    </div>
    <i class="bi bi-chevron-down text-sm transition-transform submenu-arrow"></i>
  `;

  // Create submenu
  const submenu = document.createElement('div');
  submenu.className = 'submenu hidden ml-4 mt-1 space-y-1';

  item.submenu.forEach(subitem => {
    const sublink = document.createElement('a');
    sublink.className = 'flex items-center gap-3 px-4 py-2 rounded-lg text-gray-600 hover:bg-gray-50 hover:text-blue-600 transition-colors text-sm';
    sublink.href = `#${subitem.route}`;

    const subicon = subitem.icon || 'bi-circle';
    sublink.innerHTML = `
      <i class="bi ${subicon}"></i>
      <span>${subitem.title}</span>
    `;

    sublink.onclick = (e) => {
      // Update active state for submenu items
      document.querySelectorAll('#sidebar-nav a').forEach(l => {
        l.classList.remove('bg-blue-50', 'text-blue-600');
        l.classList.add('text-gray-600');
      });
      sublink.classList.add('bg-blue-50', 'text-blue-600');
      sublink.classList.remove('text-gray-600');
    };

    submenu.appendChild(sublink);
  });

  // Toggle submenu on parent click
  parent.onclick = () => {
    submenu.classList.toggle('hidden');
    const arrow = parent.querySelector('.submenu-arrow');
    if (submenu.classList.contains('hidden')) {
      arrow.style.transform = 'rotate(0deg)';
    } else {
      arrow.style.transform = 'rotate(180deg)';
    }
  };

  container.appendChild(parent);
  container.appendChild(submenu);

  return container;
}

function getMenuIcon(route) {
  const icons = {
    'dashboard': 'bi-speedometer2',
    'companies': 'bi-building',
    'branches': 'bi-diagram-3',
    'departments': 'bi-people',
    'users': 'bi-people-fill',
    'audit': 'bi-clock-history',
    'settings': 'bi-gear'
  };
  return icons[route] || 'bi-circle';
}

function updateActiveMenuItem() {
  const currentRoute = window.location.hash.slice(1) || 'dashboard';
  
  document.querySelectorAll('#sidebar-nav a').forEach(link => {
    const linkRoute = link.getAttribute('href').slice(1);
    
    if (linkRoute === currentRoute) {
      link.classList.add('bg-blue-50', 'text-blue-600');
      link.classList.remove('text-gray-700');
    } else {
      link.classList.remove('bg-blue-50', 'text-blue-600');
      link.classList.add('text-gray-700');
    }
  });
}

async function loadRoute(route) {
  appState.currentRoute = route;
  updateActiveMenuItem();

  const content = document.getElementById('content');

  // Show loading state
  content.innerHTML = `
    <div class="flex items-center justify-center h-full">
      <div class="text-center">
        <div class="inline-block">
          <div class="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
        </div>
        <p class="mt-4 text-gray-600 font-medium">Loading ${route}...</p>
      </div>
    </div>
  `;

  try {
    // Check if this is a module route
    const moduleRoute = moduleRegistry.findRoute(`#/${route}`);

    if (moduleRoute && moduleRoute.handler) {
      // This is a module route - load the module page
      console.log(`Loading module route: ${route}`);

      // Create app-content div if it doesn't exist
      content.innerHTML = '<div id="app-content"></div>';

      // Call the module route handler
      const PageClass = await moduleRoute.handler();

      if (PageClass) {
        const page = new PageClass();
        if (typeof page.render === 'function') {
          await page.render();
        } else {
          throw new Error('Module page does not have a render method');
        }
      } else {
        throw new Error('Module page not found');
      }

      // Dispatch event for route-specific JS
      document.dispatchEvent(new CustomEvent('route:loaded', {
        detail: { route, isModule: true }
      }));

      return;
    }

    // Not a module route - try loading core template
    const response = await fetch(`/assets/templates/${route}.html`);

    if (!response.ok) {
      throw new Error('Template not found');
    }

    const html = await response.text();
    content.innerHTML = html;

    // Dispatch event for route-specific JS
    document.dispatchEvent(new CustomEvent('route:loaded', {
      detail: { route, isModule: false }
    }));

  } catch (error) {
    console.error(`Error loading route ${route}:`, error);
    content.innerHTML = `
      <div class="max-w-md mx-auto mt-20">
        <div class="bg-yellow-50 border-l-4 border-yellow-500 p-6 rounded-lg shadow-sm">
          <div class="flex items-start gap-3">
            <i class="bi bi-exclamation-triangle-fill text-yellow-500 text-2xl"></i>
            <div>
              <h3 class="text-lg font-semibold text-yellow-800 mb-2">Page Not Found</h3>
              <p class="text-yellow-700 mb-4">The page "${route}" could not be loaded.</p>
              <button
                onclick="window.location.hash = 'dashboard'"
                class="px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition">
                <i class="bi bi-house"></i> Go to Dashboard
              </button>
            </div>
          </div>
        </div>
      </div>
    `;
  }
}