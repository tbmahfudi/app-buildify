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

/**
 * Load the main application template into #root
 */
async function loadMainTemplate() {
  try {
    const response = await fetch('/assets/templates/main.html');
    if (!response.ok) {
      throw new Error('Failed to load main template');
    }

    const html = await response.text();

    // Inject template directly into root
    const root = document.getElementById('root');
    if (root) {
      root.innerHTML = html;
    }

    // Hide the loader
    const loader = document.getElementById('app-loader');
    if (loader) {
      loader.style.display = 'none';
    }

    console.log('✓ Main application template loaded');
  } catch (error) {
    console.error('Failed to load main template:', error);

    // Hide the loader before showing error
    const loader = document.getElementById('app-loader');
    if (loader) {
      loader.style.display = 'none';
    }

    document.getElementById('root').innerHTML = `
      <div class="flex items-center justify-center h-screen bg-gray-50">
        <div class="text-center p-8">
          <i class="ph-duotone ph-warning-circle text-6xl text-red-500 mb-4"></i>
          <h1 class="text-2xl font-bold text-gray-900 mb-2">Failed to Load Application</h1>
          <p class="text-gray-600 mb-4">Please refresh the page to try again</p>
          <button onclick="location.reload()" class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
            Reload
          </button>
        </div>
      </div>
    `;
  }
}

export async function initApp() {
  // Check if logged in
  const tokensStr = localStorage.getItem('tokens');

  if (!tokensStr) {
    window.location.href = '/assets/templates/login.html';
    return;
  }

  // Load main application template
  await loadMainTemplate();

  showLoading();

  // Load user info
  try {
    const response = await apiFetch('/auth/me');

    if (!response.ok) throw new Error('Auth failed');

    appState.user = await response.json();

    // Log user info for debugging
    console.log('[User] Current user:', {
      email: appState.user.email,
      name: appState.user.name,
      is_superuser: appState.user.is_superuser,
      tenant_id: appState.user.tenant_id,
      roles: appState.user.roles || [],
      permissions_count: appState.user.permissions?.length || 0,
      permissions: appState.user.permissions || []
    });

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

  // Load and apply saved sidebar state
  loadSidebarState();

  // Position toggle button based on user preference
  positionSidebarToggle();

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

  // Setup i18n translation hooks
  if (window.i18n && window.i18n.isInitialized) {
    // Translate page content after route loads
    document.addEventListener('route:loaded', () => {
      setTimeout(() => {
        window.i18n.translatePage();
      }, 50);
    });

    // Re-translate everything when language changes
    window.addEventListener('languageChanged', async () => {
      // Reload menu with new language
      await loadMenu();
      // Current page is already translated by i18n.changeLanguage()
    });
  }
}

function updateUserInfo() {
  const userNameEl = document.getElementById('user-name');
  const userRoleEl = document.getElementById('user-role');
  const userEmailDropdown = document.getElementById('user-email-dropdown');

  if (appState.user) {
    // Display name with fallback to full_name, then email
    const displayName = appState.user.display_name || appState.user.full_name || appState.user.email.split('@')[0];

    if (userNameEl) {
      userNameEl.textContent = displayName;
    }

    // Display user role
    if (userRoleEl) {
      let roleText = 'User';

      if (appState.user.is_superuser) {
        roleText = 'Super Administrator';
      } else if (appState.user.roles && appState.user.roles.length > 0) {
        // Get the first role and capitalize it
        roleText = appState.user.roles[0].charAt(0).toUpperCase() + appState.user.roles[0].slice(1);
      }

      userRoleEl.textContent = roleText;
    }

    if (userEmailDropdown) {
      userEmailDropdown.textContent = appState.user.email;
    }

    // Store user in localStorage for quick access across the app
    localStorage.setItem('user', JSON.stringify(appState.user));
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

  // Sidebar toggle button (navbar)
  const sidebarToggle = document.getElementById('sidebar-toggle');

  if (sidebarToggle) {
    sidebarToggle.addEventListener('click', toggleSidebar);
  }

  // Setup dropdown menus
  setupDropdownMenus();
}

/**
 * Setup dropdown menu interactions for navbar
 */
function setupDropdownMenus() {
  // Only target dropdown containers in the navbar to avoid interfering with sidebar
  const navbar = document.querySelector('nav');
  if (!navbar) return;

  const dropdowns = navbar.querySelectorAll('.group');

  dropdowns.forEach(dropdown => {
    const button = dropdown.querySelector('button');
    const menu = dropdown.querySelector('[role="menu"]');

    if (button && menu) {
      // Add click event as fallback
      button.addEventListener('click', function(e) {
        e.stopPropagation();

        // Close other navbar dropdowns
        navbar.querySelectorAll('[role="menu"]').forEach(m => {
          if (m !== menu) {
            m.classList.add('opacity-0', 'invisible');
            m.classList.remove('opacity-100', 'visible');
          }
        });

        // Toggle current dropdown
        menu.classList.toggle('opacity-0');
        menu.classList.toggle('invisible');
        menu.classList.toggle('opacity-100');
        menu.classList.toggle('visible');
      });

      // Ensure hover works too
      dropdown.addEventListener('mouseenter', function() {
        menu.classList.remove('opacity-0', 'invisible');
        menu.classList.add('opacity-100', 'visible');
      });

      dropdown.addEventListener('mouseleave', function() {
        menu.classList.add('opacity-0', 'invisible');
        menu.classList.remove('opacity-100', 'visible');
      });
    }
  });

  // Close dropdowns when clicking outside
  document.addEventListener('click', function() {
    navbar.querySelectorAll('[role="menu"]').forEach(menu => {
      menu.classList.add('opacity-0', 'invisible');
      menu.classList.remove('opacity-100', 'visible');
    });
  });
}

/**
 * Toggle sidebar collapsed/expanded state
 */
function toggleSidebar() {
  const sidebar = document.getElementById('sidebar');
  if (!sidebar) return;

  const isCollapsed = sidebar.getAttribute('data-collapsed') === 'true';

  if (isCollapsed) {
    // Expand sidebar
    sidebar.setAttribute('data-collapsed', 'false');
    sidebar.classList.remove('sidebar-collapsed');
    sidebar.classList.add('w-64');
  } else {
    // Collapse sidebar
    sidebar.setAttribute('data-collapsed', 'true');
    sidebar.classList.add('sidebar-collapsed');
    sidebar.classList.remove('w-64');
  }

  // Save state to localStorage
  saveSidebarState(!isCollapsed);

  // Reload menu to update tooltips and popup menus
  loadMenu();
}

/**
 * Position the sidebar toggle button based on user preference
 */
export function positionSidebarToggle() {
  const toggleButton = document.getElementById('sidebar-toggle');
  if (!toggleButton) return;

  // Get user preference (default: after-title)
  const position = localStorage.getItem('sidebarTogglePosition') || 'after-title';

  // All possible position containers
  const positions = {
    'sidebar-header': document.getElementById('toggle-position-sidebar-header'),
    'before-logo': document.getElementById('toggle-position-before-logo'),
    'between': document.getElementById('toggle-position-between'),
    'after-title': document.getElementById('toggle-position-after-title')
  };

  // Hide all position containers
  Object.values(positions).forEach(container => {
    if (container) {
      container.classList.add('hidden');
      container.innerHTML = '';
    }
  });

  // Move button to selected position
  const targetContainer = positions[position];
  if (targetContainer) {
    targetContainer.classList.remove('hidden');
    targetContainer.appendChild(toggleButton);
  }
}

/**
 * Load sidebar state from localStorage
 */
function loadSidebarState() {
  const sidebar = document.getElementById('sidebar');
  if (!sidebar) return;

  // Check for saved state, fallback to default setting
  const savedState = localStorage.getItem('sidebarCollapsed');
  const defaultState = localStorage.getItem('sidebarDefaultState') || 'expanded';

  let shouldCollapse = false;

  if (savedState !== null) {
    // Use saved state if available
    shouldCollapse = savedState === 'true';
  } else if (defaultState === 'collapsed') {
    // Use default setting from preferences
    shouldCollapse = true;
  }

  if (shouldCollapse) {
    sidebar.setAttribute('data-collapsed', 'true');
    sidebar.classList.add('sidebar-collapsed');
    sidebar.classList.remove('w-64');
  } else {
    sidebar.setAttribute('data-collapsed', 'false');
    sidebar.classList.remove('sidebar-collapsed');
    sidebar.classList.add('w-64');
  }
}

/**
 * Save sidebar state to localStorage
 */
function saveSidebarState(isCollapsed) {
  localStorage.setItem('sidebarCollapsed', isCollapsed.toString());
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
    // Feature flag: Use backend-driven menu system
    const useDynamicMenu = window.APP_CONFIG?.useDynamicMenu !== false; // Default to true

    let menuItems;

    if (useDynamicMenu) {
      // NEW: Backend-driven RBAC menu system
      menuItems = await loadMenuFromBackend();
    } else {
      // LEGACY: Static JSON menu with client-side filtering
      menuItems = await loadMenuFromStatic();
    }

    const navContainer = document.getElementById('sidebar-nav');
    if (!navContainer) return;

    navContainer.innerHTML = '';

    menuItems.forEach(item => {
      // If item has submenu/children, create an expandable menu
      if ((item.submenu && item.submenu.length > 0) || (item.children && item.children.length > 0)) {
        const menuGroup = createSubmenuItem(item);
        navContainer.appendChild(menuGroup);
      } else {
        const link = createMenuItem(item);
        navContainer.appendChild(link);
      }
    });

    // Set initial active state
    updateActiveMenuItem();

    // Translate menu items after rendering
    if (window.i18n && window.i18n.isInitialized) {
      setTimeout(() => {
        window.i18n.translatePage();
      }, 50);
    }

  } catch (error) {
    console.error('Failed to load menu:', error);
    showToast('Failed to load menu', 'error');
  }
}

/**
 * Load menu from backend API (NEW - RBAC filtered on server)
 */
async function loadMenuFromBackend() {
  try {
    const response = await apiFetch('/menu?include_modules=true');

    if (!response.ok) {
      throw new Error(`Failed to fetch menu: ${response.status}`);
    }

    const menuData = await response.json();

    // Backend returns pre-filtered menu based on user's RBAC
    // Convert 'children' to 'submenu' for compatibility with existing rendering
    return convertBackendMenuFormat(menuData);

  } catch (error) {
    console.error('Error loading menu from backend:', error);

    // Fallback to static menu if backend fails
    console.warn('Falling back to static menu');
    return await loadMenuFromStatic();
  }
}

/**
 * Load menu from static JSON (LEGACY - with client-side filtering)
 */
async function loadMenuFromStatic() {
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
  return filterMenuByRole(allMenuItems);
}

/**
 * Convert backend menu format to frontend format
 * Backend uses 'children', frontend expects 'submenu'
 * Preserves permission and role information for potential client-side checks
 * Filters out parent menus with no children
 */
function convertBackendMenuFormat(menuItems) {
  return menuItems
    .map(item => {
      const converted = {
        title: item.title,
        route: item.route,
        icon: item.icon,
        order: item.order,
        target: item.target || '_self'
      };

      // Preserve RBAC information (already filtered by backend, but useful for client-side checks)
      if (item.permission) {
        converted.permission = item.permission;
      }
      if (item.required_roles) {
        converted.roles = item.required_roles;  // Map to 'roles' for consistency with static menu format
      }

      // Preserve extra_data if present (includes icon_color)
      if (item.extra_data) {
        converted.extra_data = item.extra_data;
        // Apply icon_color if present
        if (item.extra_data.icon_color) {
          converted.iconColor = item.extra_data.icon_color;
        }
      }

      // Convert children to submenu
      if (item.children && item.children.length > 0) {
        converted.submenu = convertBackendMenuFormat(item.children);
      }

      return converted;
    })
    .filter(item => {
      // Filter out parent-only menus (no route) with no children
      // If menu has a route, keep it (it's a clickable item)
      // If menu has no route but has children, keep it (it's a valid parent)
      // If menu has no route and no children, filter it out
      if (!item.route && (!item.submenu || item.submenu.length === 0)) {
        return false;
      }
      return true;
    });
}

// Helper function to convert menu title to i18n key
function getMenuI18nKey(title) {
  const keyMap = {
    'Dashboard': 'menu.dashboard',
    'System Management': 'menu.systemManagement',
    'Administration': 'menu.administration',
    'Tenants': 'menu.tenants',
    'Users': 'menu.users',
    'Groups': 'menu.groups',
    'Access Control': 'menu.accessControl',
    'Roles & Permissions': 'menu.rolesPermissions',
    'Auth Policies': 'menu.authPolicies',
    'Menu Management': 'menu.menuManagement',
    'System Settings': 'menu.systemSettings',
    'General': 'menu.general',
    'Integration': 'menu.integration',
    'Security': 'menu.security',
    'Notifications': 'menu.notifications',
    'Module Management': 'menu.moduleManagement',
    'Installed Modules': 'menu.installedModules',
    'Marketplace': 'menu.marketplace',
    'Updates': 'menu.updates',
    'Builder': 'menu.builder',
    'Monitoring & Audit': 'menu.monitoringAudit',
    'Audit Trail': 'menu.auditTrail',
    'System Logs': 'menu.systemLogs',
    'API Activity': 'menu.apiActivity',
    'Usage Analytics': 'menu.usageAnalytics',
    'Help & Support': 'menu.helpSupport',
    'User Guide': 'menu.userGuide',
    'API Docs': 'menu.apiDocs',
    'Contact Support': 'menu.contactSupport',
    'Changelog': 'menu.changelog',
    'Developer Tools': 'menu.developerTools',
    'Sample Reports & Dashboards': 'menu.sampleReportsDashboards',
    'Components': 'menu.components',
    'Schema Designer': 'menu.schemaDesigner',
    'API Playground': 'menu.apiPlayground',
    'Code Generator': 'menu.codeGenerator'
  };

  return keyMap[title] || null;
}

// Helper function to get icon color based on menu category
function getIconColor(title, route, item = null) {
  // Check if item has custom iconColor property first
  if (item && item.iconColor) {
    return item.iconColor;
  }

  const colorMap = {
    // Main menu items - vibrant colors
    'Dashboard': 'text-purple-600',
    'Administration': 'text-blue-600',
    'System Management': 'text-orange-600',
    'Developer Tools': 'text-green-600',
    'Help & Support': 'text-pink-600',

    // Administration submenu
    'Tenants': 'text-blue-600',
    'Tenants & Organizations': 'text-blue-600',
    'Tenant Management': 'text-blue-600',
    'Companies': 'text-blue-500',
    'Branches': 'text-cyan-600',
    'Departments': 'text-sky-600',
    'Users': 'text-indigo-600',
    'Groups': 'text-violet-600',
    'Access Control': 'text-purple-600',
    'Users & Access Control': 'text-purple-600',
    'Auth Policies': 'text-fuchsia-600',

    // System Settings submenu
    'System Settings': 'text-orange-500',
    'Menu Management': 'text-emerald-600',
    'General': 'text-amber-600',
    'Integration': 'text-cyan-600',
    'Security': 'text-red-600',
    'Notifications': 'text-indigo-600',

    // Module Management submenu
    'Module Management': 'text-orange-500',
    'Installed Modules': 'text-violet-600',
    'Marketplace': 'text-emerald-600',
    'Updates': 'text-sky-600',
    'Builder': 'text-teal-600',

    // Monitoring & Audit submenu
    'Monitoring & Audit': 'text-orange-500',
    'Audit Trail': 'text-amber-600',
    'System Logs': 'text-slate-600',
    'API Activity': 'text-fuchsia-600',
    'Usage Analytics': 'text-lime-600',

    // Developer Tools submenu
    'Components': 'text-green-500',
    'Schema Designer': 'text-emerald-600',
    'API Playground': 'text-teal-600',
    'Code Generator': 'text-lime-600',

    // Help & Support submenu
    'User Guide': 'text-pink-500',
    'API Docs': 'text-rose-600',
    'Contact Support': 'text-pink-600',
    'Changelog': 'text-fuchsia-600',
  };

  return colorMap[title] || 'text-gray-600';
}

function createMenuItem(item) {
  const sidebar = document.getElementById('sidebar');
  const isCollapsed = sidebar?.getAttribute('data-collapsed') === 'true';

  const link = document.createElement('a');
  link.className = 'sidebar-menu-item flex items-center gap-3 px-4 py-3 rounded-lg text-gray-700 hover:bg-gray-100 hover:text-blue-600 transition-colors group relative';
  link.href = `#${item.route}`;
  link.setAttribute('data-tooltip', item.title);

  // Use icon from menu item or fallback to getMenuIcon
  const icon = item.icon || getMenuIcon(item.route);
  const iconColor = getIconColor(item.title, item.route, item);

  if (isCollapsed) {
    link.innerHTML = `
      <div class="w-full flex justify-center">
        <i class="${icon} text-2xl ${iconColor}"></i>
      </div>
    `;

    // Add tooltip with fixed positioning to avoid clipping
    const tooltip = document.createElement('div');
    tooltip.className = 'fixed hidden px-3 py-2 bg-gray-900 text-white text-sm rounded-lg whitespace-nowrap shadow-lg pointer-events-none';
    tooltip.style.zIndex = '99999';
    tooltip.textContent = item.title;
    document.body.appendChild(tooltip);

    link.addEventListener('mouseenter', (e) => {
      const rect = link.getBoundingClientRect();
      tooltip.style.left = `${rect.right + 8}px`;
      tooltip.style.top = `${rect.top + rect.height / 2}px`;
      tooltip.style.transform = 'translateY(-50%)';
      tooltip.classList.remove('hidden');
    });

    link.addEventListener('mouseleave', () => {
      tooltip.classList.add('hidden');
    });
  } else {
    const i18nKey = getMenuI18nKey(item.title);
    const i18nAttr = i18nKey ? `data-i18n="${i18nKey}"` : '';

    link.innerHTML = `
      <i class="${icon} text-xl flex-shrink-0 ${iconColor}"></i>
      <span class="sidebar-menu-label font-medium" ${i18nAttr}>${item.title}</span>
    `;
  }

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

function createSubmenuItem(item, level = 1) {
  const sidebar = document.getElementById('sidebar');
  const isCollapsed = sidebar?.getAttribute('data-collapsed') === 'true';

  const container = document.createElement('div');
  container.className = 'submenu-container relative group';

  if (isCollapsed) {
    // Collapsed state - show icon with popup menu
    const parent = document.createElement('div');
    parent.className = 'flex items-center justify-center px-4 py-3 rounded-lg text-gray-700 hover:bg-gray-100 cursor-pointer transition-colors relative';

    const icon = item.icon || getMenuIcon(item.route);
    const iconColor = getIconColor(item.title, item.route, item);
    parent.innerHTML = `
      <i class="${icon} text-2xl ${iconColor}"></i>
    `;

    // Create popup menu with fixed positioning to avoid clipping
    const popup = createCollapsedSubmenuPopup(item);
    document.body.appendChild(popup);

    // Position popup on hover - overlap by 2px to eliminate gap
    parent.addEventListener('mouseenter', () => {
      const rect = parent.getBoundingClientRect();
      popup.style.left = `${rect.right - 2}px`;
      popup.style.top = `${rect.top}px`;
      popup.classList.remove('hidden');
    });

    parent.addEventListener('mouseleave', (e) => {
      // Check if moving to popup or if popup is already being hovered
      setTimeout(() => {
        if (!popup.matches(':hover') && !popup.hasActiveChild) {
          popup.classList.add('hidden');
        }
      }, 100);
    });

    popup.addEventListener('mouseleave', () => {
      setTimeout(() => {
        if (!parent.matches(':hover') && !popup.hasActiveChild) {
          popup.classList.add('hidden');
        }
      }, 100);
    });

    container.appendChild(parent);
  } else {
    // Expanded state - show full menu with arrow
    const parent = document.createElement('div');
    parent.className = 'flex items-center justify-between px-4 py-3 rounded-lg text-gray-700 hover:bg-gray-100 cursor-pointer transition-colors';

    const icon = item.icon || getMenuIcon(item.route);
    const iconColor = getIconColor(item.title, item.route, item);
    const i18nKey = getMenuI18nKey(item.title);
    const i18nAttr = i18nKey ? `data-i18n="${i18nKey}"` : '';

    parent.innerHTML = `
      <div class="flex items-center gap-3">
        <i class="${icon} text-xl flex-shrink-0 ${iconColor}"></i>
        <span class="font-medium sidebar-menu-label" ${i18nAttr}>${item.title}</span>
      </div>
      <i class="ph ph-caret-down text-sm transition-transform submenu-arrow"></i>
    `;

    // Create submenu
    const submenu = document.createElement('div');
    submenu.className = 'submenu hidden ml-4 mt-1 space-y-1';

    // Support both submenu and children properties
    const submenuItems = item.submenu || item.children || [];
    submenuItems.forEach(subitem => {
      const subitemChildren = subitem.submenu || subitem.children || [];
      if (subitemChildren.length > 0) {
        // Nested submenu - recursively create
        const nestedSubmenuItem = createSubmenuItem(subitem, level + 1);
        submenu.appendChild(nestedSubmenuItem);
      } else {
        // Regular link
        const sublink = document.createElement('a');
        sublink.className = 'flex items-center gap-3 px-4 py-2 rounded-lg text-gray-600 hover:bg-gray-50 hover:text-blue-600 transition-colors text-sm';
        sublink.href = `#${subitem.route}`;

        const subicon = subitem.icon || 'ph-duotone ph-square';
        const subiconColor = getIconColor(subitem.title, subitem.route, subitem);
        const subI18nKey = getMenuI18nKey(subitem.title);
        const subI18nAttr = subI18nKey ? `data-i18n="${subI18nKey}"` : '';

        sublink.innerHTML = `
          <i class="${subicon} text-lg flex-shrink-0 ${subiconColor}"></i>
          <span ${subI18nAttr}>${subitem.title}</span>
        `;

        sublink.onclick = (e) => {
          document.querySelectorAll('#sidebar-nav a').forEach(l => {
            l.classList.remove('bg-blue-50', 'text-blue-600');
            l.classList.add('text-gray-600');
          });
          sublink.classList.add('bg-blue-50', 'text-blue-600');
          sublink.classList.remove('text-gray-600');
        };

        submenu.appendChild(sublink);
      }
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
  }

  return container;
}

// Helper function to create collapsed popup menu (supports nested submenus)
function createCollapsedSubmenuPopup(item) {
  const popup = document.createElement('div');
  popup.className = 'fixed hidden bg-white border border-gray-200 rounded-xl shadow-xl min-w-[220px] max-w-[280px] overflow-hidden';
  popup.style.zIndex = '99999';
  popup.dataset.popupLevel = '1';

  // Add title header
  const popupHeader = document.createElement('div');
  popupHeader.className = 'px-4 py-2 bg-gray-100 border-b border-gray-200';
  const headerI18nKey = getMenuI18nKey(item.title);
  const headerI18nAttr = headerI18nKey ? `data-i18n="${headerI18nKey}"` : '';
  popupHeader.innerHTML = `<span class="font-semibold text-gray-900 text-sm" ${headerI18nAttr}>${item.title}</span>`;
  popup.appendChild(popupHeader);

  // Check if all items are final (no submenu) - use grid layout
  const allItemsFinal = item.submenu.every(subitem => !subitem.submenu || subitem.submenu.length === 0);

  // Add submenu items
  const popupContent = document.createElement('div');

  if (allItemsFinal) {
    // Grid layout for final items - big icons with text below
    // Vertical-priority layout: items flow vertically first, then horizontally
    const submenuItems = item.submenu || item.children || [];
    const itemCount = submenuItems.length;

    // Calculate grid layout based on item count (vertical priority)
    // 1-2 items: 1 column (all vertical)
    // 3-4 items: 2 rows, 2 columns
    // 5-6 items: 3 rows, 2 columns
    // 7-9 items: 3 rows, 3 columns
    // etc.
    let gridRows, gridCols;
    if (itemCount <= 2) {
      gridRows = itemCount;
      gridCols = 1;
    } else if (itemCount <= 4) {
      gridRows = 2;
      gridCols = 2;
    } else if (itemCount <= 6) {
      gridRows = 3;
      gridCols = 2;
    } else {
      gridRows = 3;
      gridCols = Math.ceil(itemCount / 3);
    }

    // Adjust popup width based on number of columns
    if (gridCols === 1) {
      popup.style.minWidth = '180px';
      popup.style.maxWidth = '200px';
    } else if (gridCols === 2) {
      popup.style.minWidth = '280px';
      popup.style.maxWidth = '320px';
    } else {
      popup.style.minWidth = '380px';
      popup.style.maxWidth = '420px';
    }

    popupContent.className = 'p-4 grid gap-3';
    popupContent.style.gridTemplateRows = `repeat(${gridRows}, minmax(0, 1fr))`;
    popupContent.style.gridTemplateColumns = `repeat(${gridCols}, minmax(0, 1fr))`;
    popupContent.style.gridAutoFlow = 'column'; // Fill columns first (vertical priority)

    submenuItems.forEach(subitem => {
      const gridItem = document.createElement('a');
      gridItem.className = 'flex flex-col items-center gap-2 p-3 rounded-lg text-gray-600 hover:bg-blue-50 hover:text-blue-600 transition-colors cursor-pointer';
      gridItem.href = `#${subitem.route}`;

      const subicon = subitem.icon || 'ph-duotone ph-square';
      const subiconColor = getIconColor(subitem.title, subitem.route, subitem);
      const gridI18nKey = getMenuI18nKey(subitem.title);
      const gridI18nAttr = gridI18nKey ? `data-i18n="${gridI18nKey}"` : '';

      gridItem.innerHTML = `
        <i class="${subicon} text-4xl ${subiconColor}"></i>
        <span class="text-xs text-center font-medium leading-tight" ${gridI18nAttr}>${subitem.title}</span>
      `;

      gridItem.onclick = (e) => {
        e.preventDefault();
        popup.classList.add('hidden');
        // Navigate to route
        window.location.hash = subitem.route;
      };

      popupContent.appendChild(gridItem);
    });
  } else {
    // List layout for items with submenus
    popupContent.className = 'py-1';
    const childPopups = [];

    // Support both submenu and children properties
    const submenuItems = item.submenu || item.children || [];
    submenuItems.forEach(subitem => {
      const subitemChildren = subitem.submenu || subitem.children || [];
      if (subitemChildren.length > 0) {
        // Nested submenu - create item that shows another popup on hover
        const nestedContainer = document.createElement('div');
        nestedContainer.className = 'relative';

        const nestedTrigger = document.createElement('div');
        nestedTrigger.className = 'flex items-center justify-between px-4 py-2 text-gray-700 hover:bg-blue-50 hover:text-blue-600 cursor-pointer transition-colors';

        const subicon = subitem.icon || 'ph-duotone ph-folder';
        const subiconColor = getIconColor(subitem.title, subitem.route, subitem);
        const nestedI18nKey = getMenuI18nKey(subitem.title);
        const nestedI18nAttr = nestedI18nKey ? `data-i18n="${nestedI18nKey}"` : '';

        nestedTrigger.innerHTML = `
          <div class="flex items-center gap-3">
            <i class="${subicon} text-lg ${subiconColor}"></i>
            <span class="text-sm font-medium" ${nestedI18nAttr}>${subitem.title}</span>
          </div>
          <i class="ph ph-caret-right text-xs"></i>
        `;

        // Create nested popup menu
        const nestedPopup = createNestedPopup(subitem, popup);
        childPopups.push(nestedPopup);
        document.body.appendChild(nestedPopup);

        // Show nested popup on hover - overlap by 2px to eliminate gap
        nestedTrigger.addEventListener('mouseenter', () => {
          // Hide other child popups
          childPopups.forEach(p => {
            if (p !== nestedPopup) {
              p.classList.add('hidden');
              p.isActive = false;
            }
          });

          const rect = nestedTrigger.getBoundingClientRect();
          nestedPopup.style.left = `${rect.right - 2}px`;
          nestedPopup.style.top = `${rect.top}px`;
          nestedPopup.classList.remove('hidden');
          nestedPopup.isActive = true;
          popup.hasActiveChild = true;
        });

        nestedTrigger.addEventListener('mouseleave', () => {
          setTimeout(() => {
            if (!nestedPopup.matches(':hover')) {
              nestedPopup.classList.add('hidden');
              nestedPopup.isActive = false;
              popup.hasActiveChild = childPopups.some(p => p.isActive);
            }
          }, 100);
        });

        // Keep parent visible when nested popup is hovered
        nestedPopup.addEventListener('mouseenter', () => {
          popup.hasActiveChild = true;
          nestedPopup.isActive = true;
        });

        nestedPopup.addEventListener('mouseleave', () => {
          setTimeout(() => {
            if (!nestedPopup.matches(':hover') && !nestedTrigger.matches(':hover')) {
              nestedPopup.classList.add('hidden');
              nestedPopup.isActive = false;
              popup.hasActiveChild = childPopups.some(p => p.isActive);
            }
          }, 100);
        });

        nestedContainer.appendChild(nestedTrigger);
        popupContent.appendChild(nestedContainer);
      } else {
        // Regular link
        const sublink = document.createElement('a');
        sublink.className = 'flex items-center gap-3 px-4 py-2 text-gray-600 hover:bg-blue-50 hover:text-blue-600 transition-colors text-sm';
        sublink.href = `#${subitem.route}`;

        const subicon = subitem.icon || 'ph-duotone ph-square';
        const subiconColor = getIconColor(subitem.title, subitem.route, subitem);
        const sublinkI18nKey = getMenuI18nKey(subitem.title);
        const sublinkI18nAttr = sublinkI18nKey ? `data-i18n="${sublinkI18nKey}"` : '';

        sublink.innerHTML = `
          <i class="${subicon} text-lg ${subiconColor}"></i>
          <span ${sublinkI18nAttr}>${subitem.title}</span>
        `;

        sublink.onclick = (e) => {
          e.preventDefault();
          popup.classList.add('hidden');
          // Navigate to route
          window.location.hash = subitem.route;
        };

        popupContent.appendChild(sublink);
      }
    });

    // Store child popups reference and initialize state
    popup.childPopups = childPopups;
    popup.hasActiveChild = false;
  }

  popup.appendChild(popupContent);

  // Keep popup visible when mouse re-enters from child
  popup.addEventListener('mouseenter', () => {
    popup.classList.remove('hidden');
  });

  // Enhanced mouseleave to check child popups and their descendants
  popup.addEventListener('mouseleave', () => {
    setTimeout(() => {
      // Check if any child or descendant is hovered or active
      const isAnyDescendantActive = () => {
        if (!popup.childPopups) return false;

        for (const child of popup.childPopups) {
          if (child.matches(':hover') || child.isActive) return true;
          // Check child's children (for 3-level menus)
          if (child.childPopups && child.childPopups.some(grandchild => grandchild.matches(':hover') || grandchild.isActive)) {
            return true;
          }
        }
        return false;
      };

      // Update hasActiveChild flag
      popup.hasActiveChild = isAnyDescendantActive();

      // Only hide if neither the popup nor any descendant is hovered/active
      if (!popup.matches(':hover') && !popup.hasActiveChild) {
        popup.classList.add('hidden');
        if (popup.childPopups) {
          popup.childPopups.forEach(child => {
            child.classList.add('hidden');
            child.isActive = false;
            // Also hide child's children
            if (child.childPopups) {
              child.childPopups.forEach(grandchild => {
                grandchild.classList.add('hidden');
                grandchild.isActive = false;
              });
            }
          });
        }
      }
    }, 100);
  });

  return popup;
}

// Helper function to create nested popup (for second level)
function createNestedPopup(item, parentPopup) {
  const nestedPopup = document.createElement('div');

  // Check if all items are final - use grid layout
  const allItemsFinal = item.submenu.every(subitem => !subitem.submenu || subitem.submenu.length === 0);

  if (allItemsFinal) {
    // Grid layout for final items - vertical priority
    nestedPopup.className = 'fixed hidden bg-white border border-gray-200 rounded-xl shadow-xl overflow-hidden';
    nestedPopup.style.zIndex = '100000';

    const nestedContent = document.createElement('div');

    // Support both submenu and children properties
    const nestedItems = item.submenu || item.children || [];
    const itemCount = nestedItems.length;

    // Calculate grid layout based on item count (vertical priority)
    let gridRows, gridCols;
    if (itemCount <= 2) {
      gridRows = itemCount;
      gridCols = 1;
    } else if (itemCount <= 4) {
      gridRows = 2;
      gridCols = 2;
    } else if (itemCount <= 6) {
      gridRows = 3;
      gridCols = 2;
    } else {
      gridRows = 3;
      gridCols = Math.ceil(itemCount / 3);
    }

    // Adjust nested popup width based on number of columns
    if (gridCols === 1) {
      nestedPopup.style.minWidth = '180px';
      nestedPopup.style.maxWidth = '200px';
    } else if (gridCols === 2) {
      nestedPopup.style.minWidth = '280px';
      nestedPopup.style.maxWidth = '320px';
    } else {
      nestedPopup.style.minWidth = '380px';
      nestedPopup.style.maxWidth = '420px';
    }

    nestedContent.className = 'p-4 grid gap-3';
    nestedContent.style.gridTemplateRows = `repeat(${gridRows}, minmax(0, 1fr))`;
    nestedContent.style.gridTemplateColumns = `repeat(${gridCols}, minmax(0, 1fr))`;
    nestedContent.style.gridAutoFlow = 'column'; // Fill columns first (vertical priority)

    nestedItems.forEach(nestedItem => {
      const gridItem = document.createElement('a');
      gridItem.className = 'flex flex-col items-center gap-2 p-3 rounded-lg text-gray-600 hover:bg-blue-50 hover:text-blue-600 transition-colors cursor-pointer';
      const nestedIcon = nestedItem.icon || 'ph-duotone ph-circle';
      const nestedIconColor = getIconColor(nestedItem.title, nestedItem.route, nestedItem);
      const nestedI18nKey = getMenuI18nKey(nestedItem.title);
      const nestedI18nAttr = nestedI18nKey ? `data-i18n="${nestedI18nKey}"` : '';
      gridItem.innerHTML = `
        <i class="${nestedIcon} text-4xl ${nestedIconColor}"></i>
        <span class="text-xs text-center font-medium leading-tight" ${nestedI18nAttr}>${nestedItem.title}</span>
      `;
      gridItem.href = `#${nestedItem.route}`;

      gridItem.onclick = (e) => {
        e.preventDefault();
        parentPopup.classList.add('hidden');
        nestedPopup.classList.add('hidden');
        // Also hide parent's parent if it exists
        if (parentPopup.parentPopup) {
          parentPopup.parentPopup.classList.add('hidden');
        }
        // Navigate to route
        window.location.hash = nestedItem.route;
      };

      nestedContent.appendChild(gridItem);
    });

    nestedPopup.appendChild(nestedContent);
  } else {
    // List layout
    nestedPopup.className = 'fixed hidden bg-white border border-gray-200 rounded-xl shadow-xl min-w-[200px] overflow-hidden';
    nestedPopup.style.zIndex = '100000';

    const nestedContent = document.createElement('div');
    nestedContent.className = 'py-1';

    // Support both submenu and children properties
    const nestedItems = item.submenu || item.children || [];
    nestedItems.forEach(nestedItem => {
      const nestedLink = document.createElement('a');
      nestedLink.className = 'flex items-center gap-3 px-4 py-2 text-gray-600 hover:bg-blue-50 hover:text-blue-600 transition-colors text-sm';
      nestedLink.href = `#${nestedItem.route}`;

      const nestedIcon = nestedItem.icon || 'ph-duotone ph-circle';
      const nestedIconColor = getIconColor(nestedItem.title, nestedItem.route, nestedItem);
      const nestedI18nKey = getMenuI18nKey(nestedItem.title);
      const nestedI18nAttr = nestedI18nKey ? `data-i18n="${nestedI18nKey}"` : '';
      nestedLink.innerHTML = `
        <i class="${nestedIcon} text-base ${nestedIconColor}"></i>
        <span ${nestedI18nAttr}>${nestedItem.title}</span>
      `;

      nestedLink.onclick = (e) => {
        e.preventDefault();
        parentPopup.classList.add('hidden');
        nestedPopup.classList.add('hidden');
        // Also hide parent's parent if it exists
        if (parentPopup.parentPopup) {
          parentPopup.parentPopup.classList.add('hidden');
        }
        // Navigate to route
        window.location.hash = nestedItem.route;
      };

      nestedContent.appendChild(nestedLink);
    });

    nestedPopup.appendChild(nestedContent);
  }

  // Enhanced mouseleave to keep both popup and parent visible when content is hovered
  nestedPopup.addEventListener('mouseleave', () => {
    setTimeout(() => {
      if (!nestedPopup.matches(':hover')) {
        nestedPopup.classList.add('hidden');
        nestedPopup.isActive = false;
        // Update parent's hasActiveChild flag
        if (parentPopup.childPopups) {
          parentPopup.hasActiveChild = parentPopup.childPopups.some(p => p.isActive);
        }
      }
    }, 150);
  });

  // Keep parent visible when nested popup content is hovered
  nestedPopup.addEventListener('mouseenter', () => {
    nestedPopup.isActive = true;
    parentPopup.hasActiveChild = true;
  });

  // Store reference to parent for chain hiding and visibility tracking
  nestedPopup.parentPopup = parentPopup;
  nestedPopup.isActive = false;

  return nestedPopup;
}

function getMenuIcon(route) {
  const icons = {
    'dashboard': 'ph-duotone ph-gauge',
    'tenants': 'ph-duotone ph-globe',
    'companies': 'ph-duotone ph-buildings',
    'branches': 'ph-duotone ph-tree-structure',
    'departments': 'ph-duotone ph-users-three',
    'users': 'ph-duotone ph-users',
    'audit': 'ph-duotone ph-clock-counter-clockwise',
    'settings': 'ph-duotone ph-gear',
    'rbac': 'ph-duotone ph-shield-check',
    'modules': 'ph-duotone ph-package',
    'components-showcase': 'ph-duotone ph-squares-four'
  };
  return icons[route] || 'ph-duotone ph-circle';
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
  // Normalize route - remove leading slashes
  route = route.replace(/^\/+/, '');

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

    // Not a module route - try loading core template with enhanced error handling
    // Use resource loader if available
    if (window.resourceLoader) {
      try {
        const bodyContent = await window.resourceLoader.loadTemplate(route);
        content.innerHTML = bodyContent;

        // Try to load route-specific JavaScript if it exists (optional)
        try {
          await window.resourceLoader.loadScript(`${route}.js`, { retry: false });
        } catch (scriptError) {
          // Script not found - this is optional and expected for many routes
          // Only log if it's not a 404 error
          if (!scriptError.message.includes('404')) {
            console.warn(`Optional route script ${route}.js failed to load:`, scriptError.message);
          }
        }

        // Dispatch event for route-specific JS
        document.dispatchEvent(new CustomEvent('route:loaded', {
          detail: { route, isModule: false }
        }));

      } catch (error) {
        // Use enhanced error display
        if (window.ErrorDisplay) {
          window.ErrorDisplay.showTemplateError(route, error, content);
        } else {
          throw error; // Fallback to old error handling
        }
      }
    } else {
      // Fallback to original fetch method if resource loader not available
      const response = await fetch(`/assets/templates/${route}.html`);

      if (!response.ok) {
        throw new Error('Template not found');
      }

      const html = await response.text();

      // Parse HTML to extract only body content and avoid CSP meta tag issues
      const parser = new DOMParser();
      const doc = parser.parseFromString(html, 'text/html');
      const bodyContent = doc.body?.innerHTML || html;

      content.innerHTML = bodyContent;

      // Dispatch event for route-specific JS
      document.dispatchEvent(new CustomEvent('route:loaded', {
        detail: { route, isModule: false }
      }));
    }

  } catch (error) {
    console.error(`Error loading route ${route}:`, error);

    // Enhanced error display with network detection
    const isNetworkError = !navigator.onLine || error.message.includes('network') || error.message.includes('fetch');
    const is404 = error.message.includes('404') || error.message.includes('not found');

    content.innerHTML = `
      <div class="max-w-2xl mx-auto mt-20">
        <div class="bg-red-50 border-l-4 border-red-500 p-6 rounded-lg shadow-lg">
          <div class="flex items-start gap-4">
            <i class="ph-duotone ph-${is404 ? 'file-x' : isNetworkError ? 'wifi-slash' : 'warning-circle'} text-red-500 text-4xl flex-shrink-0"></i>
            <div class="flex-1">
              <h3 class="text-xl font-bold text-red-800 mb-2">
                ${is404 ? 'Page Not Found' : isNetworkError ? 'Connection Error' : 'Failed to Load Page'}
              </h3>
              <p class="text-red-700 mb-4">
                ${is404
                  ? `The page "${route}" does not exist or has been removed.`
                  : isNetworkError
                  ? 'Unable to connect to the server. Please check your internet connection.'
                  : `An error occurred while loading "${route}".`
                }
              </p>

              ${!is404 && !isNetworkError ? `
                <details class="mb-4">
                  <summary class="cursor-pointer text-red-600 hover:text-red-700 font-medium">
                    Technical Details
                  </summary>
                  <div class="mt-2 p-3 bg-red-100 rounded border border-red-200 text-sm font-mono text-red-900 overflow-x-auto">
                    ${error.message}
                  </div>
                </details>
              ` : ''}

              <div class="flex gap-3 flex-wrap">
                <button
                  onclick="window.location.hash = 'dashboard'"
                  class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition flex items-center gap-2 shadow">
                  <i class="ph ph-house"></i>
                  Go to Dashboard
                </button>

                ${isNetworkError || !is404 ? `
                  <button
                    onclick="window.location.reload()"
                    class="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition flex items-center gap-2">
                    <i class="ph ph-arrow-clockwise"></i>
                    Retry
                  </button>
                ` : ''}

                <button
                  onclick="history.back()"
                  class="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition flex items-center gap-2">
                  <i class="ph ph-arrow-left"></i>
                  Go Back
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;
  }
}