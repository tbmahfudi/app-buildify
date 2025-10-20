import { apiFetch, logout as apiLogout, tokens } from './api.js';

const LOGIN_PAGE = '/assets/templates/login.html';

// Global state
window.appState = {
  user: null,
  currentRoute: 'dashboard',
  menu: []
};

export async function initApp() {
  // Check if logged in
  if (!tokens.access) {
    redirectToLogin();
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
    apiLogout();
    localStorage.removeItem('user');
    redirectToLogin();
    return;
  }

  // Setup main layout
  try {
    await setupMainLayout();
  } catch (error) {
    console.error('Failed to setup layout:', error);
    return;
  }

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
    logoutBtn.addEventListener('click', (event) => {
      event.preventDefault();
      apiLogout();
      localStorage.removeItem('user');
      redirectToLogin();
    });
  }
}

function redirectToLogin() {
  window.location.replace(LOGIN_PAGE);
}

async function setupMainLayout() {
  const appRoot = document.getElementById('app');
  if (!appRoot) {
    throw new Error('App root element not found');
  }

  if (!document.getElementById('content')) {
    const response = await fetch('/assets/templates/main.html');
    if (!response.ok) {
      throw new Error('Main layout template not found');
    }

    const html = await response.text();
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, 'text/html');
    const templateApp = doc.getElementById('app');

    if (!templateApp) {
      throw new Error('Main layout template missing app container');
    }

    appRoot.innerHTML = templateApp.innerHTML;
  }

  initializeUserMenu();
  initializeSidebarToggle();
  updateUserProfileChip();
}

async function loadMenu() {
  try {
    const response = await fetch('/config/menu.json');
    const menu = await response.json();

    window.appState.menu = menu.items || [];

    const navContainer = document.getElementById('sidebar-nav');
    if (!navContainer) return;

    navContainer.innerHTML = '';

    window.appState.menu.forEach((item) => {
      const link = document.createElement('a');
      link.className = 'nav-link';
      link.href = `#${item.route}`;
      link.dataset.route = item.route;
      link.dataset.tooltip = item.title;
      link.setAttribute('aria-label', item.title);

      const content = document.createElement('div');
      content.className = 'nav-link-content';

      const iconWrapper = document.createElement('span');
      iconWrapper.className = 'nav-icon';
      iconWrapper.innerHTML = `<i class="bi ${item.icon || 'bi-circle'}"></i>`;

      const label = document.createElement('span');
      label.className = 'nav-label';
      label.textContent = item.title;

      content.appendChild(iconWrapper);
      content.appendChild(label);
      link.appendChild(content);

      if (item.submenu?.length) {
        const indicator = document.createElement('span');
        indicator.className = 'nav-label text-xs text-slate-300/80';
        indicator.textContent = `${item.submenu.length} shortcuts`;
        link.appendChild(indicator);
      }

      link.addEventListener('click', () => setActiveNavLink(item.route));
      navContainer.appendChild(link);
    });

    setActiveNavLink(window.appState.currentRoute);
  } catch (error) {
    console.error('Failed to load menu:', error);
  }
}

async function loadRoute(route) {
  window.appState.currentRoute = route;

  const content = document.getElementById('content');
  if (!content) {
    console.error('Content container not found for route:', route);
    return;
  }
  content.innerHTML = `
    <div class="flex h-full items-center justify-center">
      <div class="text-center">
        <div class="inline-flex h-12 w-12 items-center justify-center rounded-full border-4 border-sky-500/80 border-t-transparent animate-spin"></div>
        <p class="mt-3 text-sm font-medium text-slate-200">Loading workspace…</p>
      </div>
    </div>
  `;

  try {
    const response = await fetch(`/assets/templates/${route}.html`);
    if (!response.ok) throw new Error('Template not found');

    const html = await response.text();
    content.innerHTML = html;

    setActiveNavLink(route);

    // Dispatch event for route-specific JS
    document.dispatchEvent(new CustomEvent('route:loaded', {
      detail: { route }
    }));
  } catch (error) {
    content.innerHTML = `
      <div class="rounded-2xl border border-amber-500/30 bg-amber-500/10 p-6 text-left text-amber-100">
        <p class="text-sm font-semibold uppercase tracking-wide text-amber-300">Page not found</p>
        <p class="mt-2 text-base">The view for <span class="font-semibold">${route}</span> has not been created yet.</p>
      </div>
    `;
  }
}

function setActiveNavLink(route) {
  const navContainer = document.getElementById('sidebar-nav');
  if (!navContainer) return;

  navContainer.querySelectorAll('.nav-link').forEach((link) => {
    link.classList.remove('active');
  });

  const parentItem = findParentMenuItem(route);
  if (!parentItem) {
    updateFloatingSubmenu();
    return;
  }

  const activeLink = navContainer.querySelector(`[data-route="${parentItem.route}"]`);
  if (activeLink) {
    activeLink.classList.add('active');
  }

  updateFloatingSubmenu(parentItem, route);
}

function findParentMenuItem(route) {
  return window.appState.menu.find((item) => {
    if (item.route === route) return true;
    return item.submenu?.some((sub) => sub.route === route);
  });
}

function updateFloatingSubmenu(menuItem = null, activeRoute = '') {
  const floatingSubmenu = document.getElementById('floating-submenu');
  if (!floatingSubmenu) return;

  floatingSubmenu.innerHTML = '';

  if (!menuItem?.submenu?.length) {
    floatingSubmenu.classList.add('hidden');
    return;
  }

  floatingSubmenu.classList.remove('hidden');

  menuItem.submenu.forEach((subItem) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'submenu-item';
    button.innerHTML = `<i class="bi ${subItem.icon || 'bi-circle'}"></i>`;
    button.dataset.tooltip = subItem.title;

    if (subItem.route === activeRoute) {
      button.classList.add('active');
    }

    button.addEventListener('click', () => {
      window.location.hash = `#${subItem.route}`;
      setActiveNavLink(subItem.route);
    });

    floatingSubmenu.appendChild(button);
  });
}

function initializeSidebarToggle() {
  if (window.__sidebarToggleInitialized) return;
  const toggleButton = document.getElementById('sidebar-toggle');
  if (!toggleButton) return;

  toggleButton.addEventListener('click', () => {
    document.body.classList.toggle('sidebar-collapsed');
  });
  window.__sidebarToggleInitialized = true;
}

function initializeUserMenu() {
  if (window.__userMenuInitialized) return;
  const userMenuButton = document.getElementById('user-menu-button');
  const userMenuDropdown = document.getElementById('user-menu-dropdown');

  if (!userMenuButton || !userMenuDropdown) return;

  const toggleMenu = () => {
    const isOpen = !userMenuDropdown.classList.contains('hidden');
    if (isOpen) {
      userMenuDropdown.classList.add('hidden');
      userMenuButton.setAttribute('aria-expanded', 'false');
    } else {
      userMenuDropdown.classList.remove('hidden');
      userMenuButton.setAttribute('aria-expanded', 'true');
    }
  };

  userMenuButton.addEventListener('click', (event) => {
    event.stopPropagation();
    toggleMenu();
  });

  const handleDocumentClick = (event) => {
    if (!userMenuDropdown.classList.contains('hidden') && !userMenuDropdown.contains(event.target)) {
      userMenuDropdown.classList.add('hidden');
      userMenuButton.setAttribute('aria-expanded', 'false');
    }
  };

  document.addEventListener('click', handleDocumentClick);

  const handleKeydown = (event) => {
    if (event.key === 'Escape') {
      userMenuDropdown.classList.add('hidden');
      userMenuButton.setAttribute('aria-expanded', 'false');
      userMenuButton.focus();
    }
  };

  document.addEventListener('keydown', handleKeydown);

  window.__userMenuInitialized = true;
}

function updateUserProfileChip() {
  const userEmail = document.getElementById('user-email');
  const avatar = document.querySelector('.user-avatar');

  const displayName = window.appState.user?.name || window.appState.user?.email || 'User';

  if (userEmail) {
    userEmail.textContent = displayName;
  }

  if (avatar && displayName) {
    avatar.textContent = displayName
      .split(' ')
      .map((part) => part.charAt(0))
      .join('')
      .slice(0, 2)
      .toUpperCase();
  }
}
