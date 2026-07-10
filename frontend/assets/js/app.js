import { apiFetch, login, logout as apiLogout } from './api.js';
import { showToast, showLoading, hideLoading } from './ui-utils.js';
import { filterMenuByRole, applyRBACToElements } from './rbac.js';
import { moduleLoader, moduleRegistry } from './core/module-system/index.js';
import { dynamicRouteRegistry } from './dynamic-route-registry.js';
// No-code entity page wrapper (ADR Step 3): registers <nocode-entity-page> and
// exposes NocodeEntityPage so no-code pages mount via the Step-1 contract.
import { NocodeEntityPage } from './nocode-entity-page.js';
import { upgradeAllSelects } from './utils/upgrade-select.js';

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

    // Portal-only users (patients) belong in the healthcare portal, not the
    // staff SPA. If a patient hits the root app URL directly, exchange their
    // platform JWT for a patient session and redirect to the portal. They must
    // never land on the staff application.
    if ((appState.user.roles || []).includes('patient') && !appState.user.is_superuser) {
      try {
        const brRes = await apiFetch('/patients/auth/from-platform', { method: 'POST' });
        if (brRes.ok) {
          const data = await brRes.json();
          if (data.access_token) localStorage.setItem('hc_patient_token', data.access_token);
        }
      } catch (_e) { /* portal will handle its own auth if the bridge fails */ }
      window.location.href = '/portal/healthcare/';
      return;
    }

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

  // Register all published nocode entities for auto-generated UI
  try {
    console.log('Loading published nocode entities...');
    await dynamicRouteRegistry.registerAllPublishedEntities();
    console.log('✓ Published nocode entities registered');
  } catch (error) {
    console.error('Failed to register nocode entities:', error);
    // Continue even if entity registration fails
  }

  // Load initial route.
  // Single-module landing: on a fresh landing (no explicit hash), if the user's
  // accessible module menu items resolve to exactly ONE module and they are not
  // a platform admin, send them straight to that module's dashboard instead of
  // the platform #dashboard.
  const explicitHash = window.location.hash.slice(1);
  let hash = explicitHash || 'dashboard';
  if (!explicitHash) {
    try {
      const landing = await resolveSingleModuleLanding();
      if (landing) hash = landing;
    } catch (e) {
      console.warn('Single-module landing check failed, using dashboard:', e);
    }
  }
  await loadRoute(hash);

  // Handle hash changes
  window.addEventListener('hashchange', () => {
    const route = window.location.hash.slice(1) || 'dashboard';
    loadRoute(route);
  });

  // Expose globally so non-module scripts (e.g. security-admin.js) can call it too.
  window.upgradeAllSelects = upgradeAllSelects;

  // Auto-upgrade native <select> elements to FlexSelect after every route load.
  // A short delay lets page-specific scripts run first (so dynamically inserted
  // options are present before the upgrade reads them).
  document.addEventListener('route:loaded', () => {
    setTimeout(() => {
      const content = document.getElementById('content') || document.body;
      upgradeAllSelects(content);
    }, 50);
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

/**
 * Single-module landing resolver.
 *
 * Returns a module dashboard route (e.g. 'healthcare/dashboard') when the user's
 * accessible MODULE routes all belong to exactly ONE module and the user is not
 * a platform admin. Otherwise returns null (→ keep platform #dashboard).
 *
 * We use moduleRegistry.getAccessibleRoutes() (the module's registered routes,
 * each with a `path` like '#/healthcare/dashboard') rather than the manifest
 * navigation menu items — a module's nav often declares only a route-less parent
 * ("Healthcare"), which carries no landing target. Routes are grouped by the
 * first path segment (the module slug).
 */
async function resolveSingleModuleLanding() {
  // Platform admins (superusers) always land on the platform dashboard.
  if (appState.user && appState.user.is_superuser) {
    return null;
  }

  let routes = [];
  try {
    routes = await moduleRegistry.getAccessibleRoutes();
  } catch (e) {
    return null;
  }
  if (!Array.isArray(routes) || routes.length === 0) {
    return null;
  }

  // Group accessible module routes by module slug (first path segment).
  const bySlug = new Map();
  for (const route of routes) {
    const rawPath = (route.path || route.route || '').replace(/^#?\/?/, '');
    if (!rawPath) continue;
    const slug = rawPath.split('/')[0];
    if (!slug) continue;
    if (!bySlug.has(slug)) bySlug.set(slug, []);
    bySlug.get(slug).push(rawPath);
  }

  // Exactly one module → land there. 0 or 2+ → platform dashboard.
  if (bySlug.size !== 1) {
    return null;
  }

  const [slug, paths] = [...bySlug.entries()][0];

  // Prefer an explicit "<slug>/dashboard" route; else the module's first route.
  const landing = paths.find((p) => p === `${slug}/dashboard`) || paths[0];

  console.log(`[Landing] Single accessible module "${slug}" → #${landing}`);
  return landing;
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

    // Org context (tenant / company / branch); "System" for the superadmin.
    updateOrgContext();

    // Store user in localStorage for quick access across the app
    localStorage.setItem('user', JSON.stringify(appState.user));
  }
}

/**
 * Render the logged-in user's organization context (tenant › company › branch)
 * in the header badge and the profile dropdown. The platform superadmin has no
 * tenant and is shown as "System".
 */
function updateOrgContext() {
  const u = appState.user || {};
  const headerWrap  = document.getElementById('org-context-header');
  const headerLabel = document.getElementById('org-context-header-label');
  const dropdown    = document.getElementById('org-context-dropdown');

  if (u.is_system) {
    if (headerLabel) headerLabel.textContent = 'System';
    if (headerWrap)  headerWrap.title = 'System (platform superadmin)';
    if (dropdown) {
      dropdown.innerHTML =
        '<div class="flex items-center gap-1.5 text-gray-700">' +
        '<i class="ph-duotone ph-globe-hemisphere-west" aria-hidden="true"></i>' +
        '<span class="font-medium">System</span></div>';
    }
    return;
  }

  // Ordered, non-empty levels for the compact header label.
  const levels = [
    ['Tenant', u.tenant_name],
    ['Company', u.company_name],
    ['Branch', u.branch_name],
    ['Department', u.department_name],
  ].filter(([, v]) => v);

  const compact = levels.map(([, v]) => v).join(' › ') || '—';
  if (headerLabel) headerLabel.textContent = compact;
  if (headerWrap)  headerWrap.title = levels.map(([k, v]) => `${k}: ${v}`).join('\n');

  if (dropdown) {
    dropdown.innerHTML = levels.length
      ? levels.map(([k, v]) =>
          `<div class="flex justify-between gap-3"><span class="text-gray-400">${k}</span>` +
          `<span class="text-gray-700 font-medium truncate text-right">${escapeOrgHtml(v)}</span></div>`
        ).join('')
      : '<div class="text-gray-400">No organization assigned</div>';
  }
}

function escapeOrgHtml(s) {
  return String(s).replace(/[&<>"']/g, c =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
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


  // My Sessions drawer
  const mySessionsBtn = document.getElementById('btn-my-sessions');
  if (mySessionsBtn) {
    mySessionsBtn.addEventListener('click', async (e) => {
      e.preventDefault();
      const { openSessionsDrawer } = await import('./sessions-drawer.js');
      openSessionsDrawer();
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
    const convertedMenu = convertBackendMenuFormat(menuData);


    return convertedMenu;

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
    icon: item.menu?.icon || 'ph-circle',
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
        icon_color_primary: item.icon_color_primary,
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

  // Check for custom colors (for duo-tone icons)
  let iconStyle = '';
  let iconColorClass = '';

  if (item.icon_color_primary) {
    const primaryColor = item.icon_color_primary;

    if (icon.includes('ph-duotone')) {
      iconStyle = `style="color: ${primaryColor}; --ph-duotone-primary: ${primaryColor};"`;
    } else {
      iconStyle = `style="color: ${primaryColor};"`;
    }
  } else {
    // Fallback to Tailwind color classes
    iconColorClass = getIconColor(item.title, item.route, item);
  }

  if (isCollapsed) {
    link.innerHTML = `
      <div class="w-full flex justify-center">
        <i class="${icon} text-2xl ${iconColorClass}" ${iconStyle}></i>
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
      <i class="${icon} text-xl flex-shrink-0 ${iconColorClass}" ${iconStyle}></i>
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
    parent.className = 'sidebar-menu-item flex items-center justify-center px-4 py-3 rounded-lg text-gray-700 hover:bg-gray-100 cursor-pointer transition-colors relative';

    const icon = item.icon || getMenuIcon(item.route);

    // Check for custom colors
    let iconStyle = '';
    let iconColorClass = '';

    if (item.icon_color_primary) {
      const primaryColor = item.icon_color_primary;

      if (icon.includes('ph-duotone')) {
        iconStyle = `style="color: ${primaryColor}; --ph-duotone-primary: ${primaryColor};"`;
      } else {
        iconStyle = `style="color: ${primaryColor};"`;
      }
    } else {
      iconColorClass = getIconColor(item.title, item.route, item);
    }

    parent.innerHTML = `
      <i class="${icon} text-2xl ${iconColorClass}" ${iconStyle}></i>
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

    // Check for custom colors
    let iconStyle = '';
    let iconColorClass = '';

    if (item.icon_color_primary) {
      const primaryColor = item.icon_color_primary;

      if (icon.includes('ph-duotone')) {
        iconStyle = `style="color: ${primaryColor}; --ph-duotone-primary: ${primaryColor};"`;
      } else {
        iconStyle = `style="color: ${primaryColor};"`;
      }
    } else {
      iconColorClass = getIconColor(item.title, item.route, item);
    }

    const i18nKey = getMenuI18nKey(item.title);
    const i18nAttr = i18nKey ? `data-i18n="${i18nKey}"` : '';

    parent.innerHTML = `
      <div class="flex items-center gap-3">
        <i class="${icon} text-xl flex-shrink-0 ${iconColorClass}" ${iconStyle}></i>
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

        // Check for custom colors
        let subiconStyle = '';
        let subiconColorClass = '';

        if (subitem.icon_color_primary) {
          const primaryColor = subitem.icon_color_primary;

          if (subicon.includes('ph-duotone')) {
            subiconStyle = `style="color: ${primaryColor}; --ph-duotone-primary: ${primaryColor};"`;
          } else {
            subiconStyle = `style="color: ${primaryColor};"`;
          }
        } else {
          subiconColorClass = getIconColor(subitem.title, subitem.route, subitem);
        }

        const subI18nKey = getMenuI18nKey(subitem.title);
        const subI18nAttr = subI18nKey ? `data-i18n="${subI18nKey}"` : '';

        sublink.innerHTML = `
          <i class="${subicon} text-lg flex-shrink-0 ${subiconColorClass}" ${subiconStyle}></i>
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

/**
 * Bind robust hover behavior for a sidebar flyout (collapsed-mode popup).
 *
 * Shows `flyout` while either `trigger` or `flyout` is hovered, and hides it
 * after a short grace period once both are left. Two things make multi-level
 * nesting robust:
 *   1. a single cancelable timer (cleared on every re-enter) avoids the
 *      stacked-setTimeout race that hid the flyout mid-transition; and
 *   2. a flyout is NOT closed while it has an active child flyout open
 *      (`flyout.hasActiveChild`) — so moving from a parent flyout into its
 *      child (positioned outside the parent) never collapses the parent.
 */
function bindFlyoutHover(trigger, flyout, parentPopup, siblings, position) {
  let closeTimer = null;

  const open = () => {
    if (closeTimer) { clearTimeout(closeTimer); closeTimer = null; }
    (siblings || []).forEach(p => {
      if (p !== flyout) { p.classList.add('hidden'); p.isActive = false; }
    });
    if (typeof position === 'function') position();
    flyout.classList.remove('hidden');
    flyout.isActive = true;
    // Cancel any pending close on the parent and mark it as having an active
    // child, so the parent stays open while we're in this flyout.
    if (parentPopup) {
      parentPopup.hasActiveChild = true;
      if (typeof parentPopup._cancelClose === 'function') parentPopup._cancelClose();
    }
  };

  const scheduleClose = () => {
    if (closeTimer) clearTimeout(closeTimer);
    closeTimer = setTimeout(() => {
      closeTimer = null;
      if (trigger.matches(':hover') || flyout.matches(':hover') || flyout.hasActiveChild) {
        return;  // still in use (incl. a child flyout open) — keep it open
      }
      flyout.classList.add('hidden');
      flyout.isActive = false;
      if (parentPopup) {
        parentPopup.hasActiveChild = (siblings || []).some(p => p.isActive);
      }
    }, 240);
  };

  // Let a child's open() cancel this flyout's pending close.
  flyout._cancelClose = () => { if (closeTimer) { clearTimeout(closeTimer); closeTimer = null; } };

  trigger.addEventListener('mouseenter', open);
  trigger.addEventListener('mouseleave', scheduleClose);
  flyout.addEventListener('mouseenter', open);
  flyout.addEventListener('mouseleave', scheduleClose);
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
  const submenuItems = item.submenu || item.children || [];
  const allItemsFinal = submenuItems.every(subitem =>
    (!subitem.submenu || subitem.submenu.length === 0) &&
    (!subitem.children || subitem.children.length === 0)
  );

  // Add submenu items
  const popupContent = document.createElement('div');

  if (allItemsFinal) {
    // Grid layout for final items - big icons with text below
    // Vertical-priority layout: items flow vertically first, then horizontally
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

      // Check for custom colors
      let subiconStyle = '';
      let subiconColorClass = '';

      if (subitem.icon_color_primary) {
        const primaryColor = subitem.icon_color_primary;

        if (subicon.includes('ph-duotone')) {
          subiconStyle = `style="color: ${primaryColor}; --ph-duotone-primary: ${primaryColor};"`;
        } else {
          subiconStyle = `style="color: ${primaryColor};"`;
        }
      } else {
        subiconColorClass = getIconColor(subitem.title, subitem.route, subitem);
      }

      const gridI18nKey = getMenuI18nKey(subitem.title);
      const gridI18nAttr = gridI18nKey ? `data-i18n="${gridI18nKey}"` : '';

      gridItem.innerHTML = `
        <i class="${subicon} text-4xl ${subiconColorClass}" ${subiconStyle}></i>
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

    // Use submenuItems already defined above
    submenuItems.forEach(subitem => {
      const subitemChildren = subitem.submenu || subitem.children || [];
      if (subitemChildren.length > 0) {
        // Nested submenu - create item that shows another popup on hover
        const nestedContainer = document.createElement('div');
        nestedContainer.className = 'relative';

        const nestedTrigger = document.createElement('div');
        nestedTrigger.className = 'flex items-center justify-between px-4 py-2 text-gray-700 hover:bg-blue-50 hover:text-blue-600 cursor-pointer transition-colors';

        const subicon = subitem.icon || 'ph-duotone ph-folder';

        // Check for custom colors
        let subiconStyle = '';
        let subiconColorClass = '';

        if (subitem.icon_color_primary) {
          const primaryColor = subitem.icon_color_primary;

          if (subicon.includes('ph-duotone')) {
            subiconStyle = `style="color: ${primaryColor}; --ph-duotone-primary: ${primaryColor};"`;
          } else {
            subiconStyle = `style="color: ${primaryColor};"`;
          }
        } else {
          subiconColorClass = getIconColor(subitem.title, subitem.route, subitem);
        }

        const nestedI18nKey = getMenuI18nKey(subitem.title);
        const nestedI18nAttr = nestedI18nKey ? `data-i18n="${nestedI18nKey}"` : '';

        nestedTrigger.innerHTML = `
          <div class="flex items-center gap-3">
            <i class="${subicon} text-lg ${subiconColorClass}" ${subiconStyle}></i>
            <span class="text-sm font-medium" ${nestedI18nAttr}>${subitem.title}</span>
          </div>
          <i class="ph ph-caret-right text-xs"></i>
        `;

        // Create nested popup menu
        const nestedPopup = createNestedPopup(subitem, popup, 2); // Pass level 2
        childPopups.push(nestedPopup);
        document.body.appendChild(nestedPopup);

        // Show nested popup on hover, with a generous overlap and a shared
        // cancelable close-timer so crossing from the trigger into the flyout
        // (or moving between its items) never hides it mid-transition.
        bindFlyoutHover(nestedTrigger, nestedPopup, popup, childPopups, () => {
          const rect = nestedTrigger.getBoundingClientRect();
          nestedPopup.style.left = `${rect.right - 6}px`;
          nestedPopup.style.top = `${rect.top}px`;
        });

        nestedContainer.appendChild(nestedTrigger);
        popupContent.appendChild(nestedContainer);
      } else {
        // Regular link
        const sublink = document.createElement('a');
        sublink.className = 'flex items-center gap-3 px-4 py-2 text-gray-600 hover:bg-blue-50 hover:text-blue-600 transition-colors text-sm';
        sublink.href = `#${subitem.route}`;

        const subicon = subitem.icon || 'ph-duotone ph-square';

        // Check for custom colors
        let subiconStyle = '';
        let subiconColorClass = '';

        if (subitem.icon_color_primary) {
          const primaryColor = subitem.icon_color_primary;

          if (subicon.includes('ph-duotone')) {
            subiconStyle = `style="color: ${primaryColor}; --ph-duotone-primary: ${primaryColor};"`;
          } else {
            subiconStyle = `style="color: ${primaryColor};"`;
          }
        } else {
          subiconColorClass = getIconColor(subitem.title, subitem.route, subitem);
        }

        const sublinkI18nKey = getMenuI18nKey(subitem.title);
        const sublinkI18nAttr = sublinkI18nKey ? `data-i18n="${sublinkI18nKey}"` : '';

        sublink.innerHTML = `
          <i class="${subicon} text-lg ${subiconColorClass}" ${subiconStyle}></i>
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
      // Check if any child or descendant is hovered or active (including hasActiveChild)
      const isAnyDescendantActive = () => {
        if (!popup.childPopups) return false;

        for (const child of popup.childPopups) {
          if (child.matches(':hover') || child.isActive || child.hasActiveChild) return true;
          // Check child's children (for 3-level menus)
          if (child.childPopups) {
            for (const grandchild of child.childPopups) {
              if (grandchild.matches(':hover') || grandchild.isActive || grandchild.hasActiveChild) return true;
              // Check grandchild's children (for 4-level menus if they exist)
              if (grandchild.childPopups && grandchild.childPopups.some(ggc => ggc.matches(':hover') || ggc.isActive)) {
                return true;
              }
            }
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
function createNestedPopup(item, parentPopup, level = 2) {
  const nestedPopup = document.createElement('div');

  // Check if all items are final - use grid layout
  // Support both submenu and children properties
  const submenuItems = item.submenu || item.children || [];
  const allItemsFinal = submenuItems.every(subitem =>
    (!subitem.submenu || subitem.submenu.length === 0) &&
    (!subitem.children || subitem.children.length === 0)
  );

  if (allItemsFinal) {
    // Grid layout for final items - vertical priority
    nestedPopup.className = 'fixed hidden bg-white border border-gray-200 rounded-xl shadow-xl overflow-hidden';
    // Increment z-index based on level to ensure proper stacking
    nestedPopup.style.zIndex = (99999 + level * 1000).toString();

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

      // Check for custom colors
      let nestedIconStyle = '';
      let nestedIconColorClass = '';

      if (nestedItem.icon_color_primary) {
        const primaryColor = nestedItem.icon_color_primary;

        if (nestedIcon.includes('ph-duotone')) {
          nestedIconStyle = `style="color: ${primaryColor}; --ph-duotone-primary: ${primaryColor};"`;
        } else {
          nestedIconStyle = `style="color: ${primaryColor};"`;
        }
      } else {
        nestedIconColorClass = getIconColor(nestedItem.title, nestedItem.route, nestedItem);
      }

      const nestedI18nKey = getMenuI18nKey(nestedItem.title);
      const nestedI18nAttr = nestedI18nKey ? `data-i18n="${nestedI18nKey}"` : '';
      gridItem.innerHTML = `
        <i class="${nestedIcon} text-4xl ${nestedIconColorClass}" ${nestedIconStyle}></i>
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
    // List layout for items with nested submenus
    nestedPopup.className = 'fixed hidden bg-white border border-gray-200 rounded-xl shadow-xl min-w-[200px] overflow-hidden';
    // Increment z-index based on level to ensure proper stacking
    nestedPopup.style.zIndex = (99999 + level * 1000).toString();

    const nestedContent = document.createElement('div');
    nestedContent.className = 'py-1';

    // Support both submenu and children properties
    const nestedItems = item.submenu || item.children || [];
    const childPopups = [];

    nestedItems.forEach(nestedItem => {
      const nestedItemChildren = nestedItem.submenu || nestedItem.children || [];

      if (nestedItemChildren.length > 0) {
        // This item has children - create a trigger that shows another nested popup
        const nestedContainer = document.createElement('div');
        nestedContainer.className = 'relative';

        const nestedTrigger = document.createElement('div');
        nestedTrigger.className = 'flex items-center justify-between px-4 py-2 text-gray-700 hover:bg-blue-50 hover:text-blue-600 cursor-pointer transition-colors';

        const nestedIcon = nestedItem.icon || 'ph-duotone ph-folder';

        // Check for custom colors
        let nestedIconStyle = '';
        let nestedIconColorClass = '';

        if (nestedItem.icon_color_primary) {
          const primaryColor = nestedItem.icon_color_primary;

          if (nestedIcon.includes('ph-duotone')) {
            nestedIconStyle = `style="color: ${primaryColor}; --ph-duotone-primary: ${primaryColor};"`;
          } else {
            nestedIconStyle = `style="color: ${primaryColor};"`;
          }
        } else {
          nestedIconColorClass = getIconColor(nestedItem.title, nestedItem.route, nestedItem);
        }

        const nestedI18nKey = getMenuI18nKey(nestedItem.title);
        const nestedI18nAttr = nestedI18nKey ? `data-i18n="${nestedI18nKey}"` : '';

        nestedTrigger.innerHTML = `
          <div class="flex items-center gap-3">
            <i class="${nestedIcon} text-base ${nestedIconColorClass}" ${nestedIconStyle}></i>
            <span class="text-sm font-medium" ${nestedI18nAttr}>${nestedItem.title}</span>
          </div>
          <i class="ph ph-caret-right text-xs"></i>
        `;

        // Recursively create another nested popup for this item's children
        const deeperNestedPopup = createNestedPopup(nestedItem, nestedPopup, level + 1); // Increment level
        childPopups.push(deeperNestedPopup);
        document.body.appendChild(deeperNestedPopup);

        // Shared cancelable hover handling (see bindFlyoutHover) — keeps the
        // deeper flyout open while moving into it or across its items.
        bindFlyoutHover(nestedTrigger, deeperNestedPopup, nestedPopup, childPopups, () => {
          const rect = nestedTrigger.getBoundingClientRect();
          deeperNestedPopup.style.left = `${rect.right - 6}px`;
          deeperNestedPopup.style.top = `${rect.top}px`;
        });

        nestedContainer.appendChild(nestedTrigger);
        nestedContent.appendChild(nestedContainer);
      } else {
        // Regular link - no children
        const nestedLink = document.createElement('a');
        nestedLink.className = 'flex items-center gap-3 px-4 py-2 text-gray-600 hover:bg-blue-50 hover:text-blue-600 transition-colors text-sm';
        nestedLink.href = `#${nestedItem.route}`;

        const nestedIcon = nestedItem.icon || 'ph-duotone ph-circle';

        // Check for custom colors
        let nestedIconStyle = '';
        let nestedIconColorClass = '';

        if (nestedItem.icon_color_primary) {
          const primaryColor = nestedItem.icon_color_primary;

          if (nestedIcon.includes('ph-duotone')) {
            nestedIconStyle = `style="color: ${primaryColor}; --ph-duotone-primary: ${primaryColor};"`;
          } else {
            nestedIconStyle = `style="color: ${primaryColor};"`;
          }
        } else {
          nestedIconColorClass = getIconColor(nestedItem.title, nestedItem.route, nestedItem);
        }

        const nestedI18nKey = getMenuI18nKey(nestedItem.title);
        const nestedI18nAttr = nestedI18nKey ? `data-i18n="${nestedI18nKey}"` : '';
        nestedLink.innerHTML = `
          <i class="${nestedIcon} text-base ${nestedIconColorClass}" ${nestedIconStyle}></i>
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
      }
    });

    // Store child popups for tracking
    nestedPopup.childPopups = childPopups;
    nestedPopup.hasActiveChild = false;

    nestedPopup.appendChild(nestedContent);
  }

  // Enhanced mouseleave to keep both popup and parent visible when content is hovered
  nestedPopup.addEventListener('mouseleave', () => {
    setTimeout(() => {
      // Check if any child popup is active or hovered before hiding
      const isAnyChildActive = () => {
        if (!nestedPopup.childPopups) return false;

        for (const child of nestedPopup.childPopups) {
          if (child.matches(':hover') || child.isActive) return true;
          // Check grandchildren (for 4-level menus if they exist)
          if (child.childPopups && child.childPopups.some(grandchild => grandchild.matches(':hover') || grandchild.isActive)) {
            return true;
          }
        }
        return false;
      };

      // Update hasActiveChild flag
      nestedPopup.hasActiveChild = isAnyChildActive();

      // Only hide if neither the popup nor any child is hovered/active
      if (!nestedPopup.matches(':hover') && !nestedPopup.hasActiveChild) {
        nestedPopup.classList.add('hidden');
        nestedPopup.isActive = false;
        // Update parent's hasActiveChild flag
        if (parentPopup.childPopups) {
          parentPopup.hasActiveChild = parentPopup.childPopups.some(p => p.isActive || p.hasActiveChild);
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


// ── T-24.030: Dev-tool routes removed from production nav ────────────────────
// These five routes are no longer in any menu or nav config arrays.
// Direct URL navigation shows an informational banner.
const _DEV_ROUTES = new Set([
  'flex-layout-sandbox',
  'builder-showcase',
  'components-showcase',
  'datatable',
  'debug-financial-module',
]);

function _showDevBanner(container, route) {
  container.innerHTML = `
    <div class="max-w-lg mx-auto mt-24 text-center px-6">
      <i class="ph ph-wrench text-4xl text-blue-400 mb-4 block"></i>
      <h2 class="text-xl font-semibold text-gray-800 mb-2">Developer Tool</h2>
      <p class="text-sm text-gray-500">
        <code class="font-mono text-blue-700 bg-blue-50 px-1 py-0.5 rounded">#${route}</code>
        is a developer-only page and has been removed from the production navigation.
      </p>
      <a href="#dashboard"
         class="inline-flex items-center gap-2 mt-6 px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition">
        <i class="ph ph-house"></i> Go to Dashboard
      </a>
    </div>`;
}
// ─────────────────────────────────────────────────────────────────────────────

async function loadRoute(route) {
  // Normalize route - remove leading slashes
  route = route.replace(/^\/+/, '');

  // Redirect duplicate route → canonical
  if (route === 'reports-designer') {
    window.location.hash = 'report-designer';
    return;
  }

  // Tear down a previously-mounted module page (optional lifecycle).
  if (appState.currentModulePage) {
    try {
      const prev = appState.currentModulePage;
      // Light-DOM page class: optional async destroy().
      if (typeof prev.destroy === 'function') {
        await prev.destroy();
      }
      // Custom element: remove from DOM -> disconnectedCallback() fires.
      if (prev instanceof HTMLElement && prev.parentNode) {
        prev.remove();
      }
    } catch (teardownError) {
      console.warn('Module page teardown failed:', teardownError);
    } finally {
      appState.currentModulePage = null;
    }
  }

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
    // Check if this is a dynamic entity route (nocode auto-generated UI).
    // ADR Step 3: route it through the SAME unified page contract as a module
    // page. We parse the legacy `dynamic/{entity}/...` URL into a
    // NocodeEntityPage and mount it into #app-content, tracking it as
    // appState.currentModulePage so it tears down identically on route change.
    const nocodeParsed = dynamicRouteRegistry.parseRoute(route);
    if (nocodeParsed) {
      content.innerHTML = '<div id="app-content"></div>';
      const appContent = document.getElementById('app-content');
      const page = new NocodeEntityPage({
        entity: nocodeParsed.entity,
        action: nocodeParsed.action,
        id: nocodeParsed.id,
      });
      await page.render(appContent);
      appState.currentModulePage = page;
      document.dispatchEvent(new CustomEvent('route:loaded', {
        detail: { route, isDynamic: true }
      }));
      return;
    }

    // Handle builder routes (core feature, not a module)
    if (route === 'builder' || route.startsWith('builder?')) {
      console.log('Loading builder page');
      const bodyContent = await window.resourceLoader.loadTemplate('builder');
      content.innerHTML = bodyContent;

      // Load the JavaScript file
      try {
        await window.resourceLoader.loadScript('builder.js');
      } catch (error) {
        console.warn('Builder script loading failed:', error);
      }

      document.dispatchEvent(new CustomEvent('route:loaded', {
        detail: { route: 'builder', isModule: false }
      }));
      return;
    }

    if (route === 'builder-pages') {
      console.log('Loading builder pages list');
      const bodyContent = await window.resourceLoader.loadTemplate('builder-pages');
      content.innerHTML = bodyContent;

      // Load the JavaScript file
      try {
        await window.resourceLoader.loadScript('builder-pages-list.js');
      } catch (error) {
        console.warn('Builder pages list script loading failed:', error);
      }

      document.dispatchEvent(new CustomEvent('route:loaded', {
        detail: { route: 'builder-pages', isModule: false }
      }));
      return;
    }

    // ── T-24.030: Dev-tool banner guard ─────────────────────────────────────────
    if (_DEV_ROUTES.has(route)) {
      _showDevBanner(content, route);
      document.dispatchEvent(new CustomEvent('route:loaded', {
        detail: { route, isModule: false }
      }));
      return;
    }

    // Handle module management route (nocode module creator)
    if (route === 'modules') {
      console.log('Loading modules page');
      const bodyContent = await window.resourceLoader.loadTemplate('nocode-modules');
      content.innerHTML = bodyContent;

      // Load the JavaScript file
      try {
        await window.resourceLoader.loadScript('nocode-modules.js');
      } catch (error) {
        console.warn('Modules script loading failed:', error);
      }

      document.dispatchEvent(new CustomEvent('route:loaded', {
        detail: { route: 'modules', isModule: false }
      }));
      return;
    }

    // Admin module installation page (superuser only)
    if (route === 'admin/modules') {
      content.innerHTML = '';
      try {
        const { render } = await import('./admin-modules.js');
        await render(content);
      } catch (error) {
        console.warn('admin-modules loading failed:', error);
        content.innerHTML = '<div class="p-6 text-red-500">Failed to load module installation page.</div>';
      }
      document.dispatchEvent(new CustomEvent('route:loaded', {
        detail: { route: 'admin/modules', isModule: false }
      }));
      return;
    }

    // ── Settings split: User Settings vs Admin Settings ──────────────────────
    // Legacy 'settings' route → redirect to the new User Settings page.
    if (route === 'settings') {
      window.location.hash = 'settings/user';
      return;
    }

    // User Settings (personal preferences) — visible to all authenticated users.
    if (route === 'settings/user') {
      const bodyContent = await window.resourceLoader.loadTemplate('settings-user');
      content.innerHTML = bodyContent;
      try {
        await window.resourceLoader.loadScript('settings.js');
      } catch (error) {
        console.warn('settings.js loading failed:', error);
      }
      document.dispatchEvent(new CustomEvent('route:loaded', {
        detail: { route: 'settings/user', isModule: false }
      }));
      return;
    }

    // Admin Settings (tenant / company configuration) — admin-gated.
    if (route === 'settings/admin') {
      const bodyContent = await window.resourceLoader.loadTemplate('settings-admin');
      content.innerHTML = bodyContent;
      try {
        await window.resourceLoader.loadScript('settings-admin.js');
      } catch (error) {
        console.warn('settings-admin.js loading failed:', error);
      }
      document.dispatchEvent(new CustomEvent('route:loaded', {
        detail: { route: 'settings/admin', isModule: false }
      }));
      return;
    }

    // T-23.019: tenant module activation page
    if (route === 'settings/modules') {
      content.innerHTML = '';
      try {
        const { render } = await import('./modules-page.js');
        await render(content);
      } catch (error) {
        console.warn('modules-page loading failed:', error);
        content.innerHTML = '<div class="p-6 text-red-500">Failed to load modules page.</div>';
      }
      document.dispatchEvent(new CustomEvent('route:loaded', {
        detail: { route: 'settings/modules', isModule: false }
      }));
      return;
    }

    // Handle module store route (code-module installer)
    if (route === 'module-store') {
      document.dispatchEvent(new CustomEvent('route:loaded', {
        detail: { route: 'module-store', isModule: false }
      }));
      return;
    }

    if (route === 'nocode-data-model') {
      console.log('Loading no-code data model page');
      const bodyContent = await window.resourceLoader.loadTemplate('nocode-data-model');
      content.innerHTML = bodyContent;

      // Load the JavaScript file
      try {
        await window.resourceLoader.loadScript('nocode-data-model.js');
      } catch (error) {
        console.warn('No-code data model script loading failed:', error);
      }

      document.dispatchEvent(new CustomEvent('route:loaded', {
        detail: { route: 'nocode-data-model', isModule: false }
      }));
      return;
    }

    if (route === 'nocode-workflows') {
      console.log('Loading no-code workflows page');
      const bodyContent = await window.resourceLoader.loadTemplate('nocode-workflows');
      content.innerHTML = bodyContent;

      // Load the JavaScript file
      try {
        await window.resourceLoader.loadScript('nocode-workflows.js');
      } catch (error) {
        console.warn('No-code workflows script loading failed:', error);
      }

      document.dispatchEvent(new CustomEvent('route:loaded', {
        detail: { route: 'nocode-workflows', isModule: false }
      }));
      return;
    }

    if (route === 'nocode-automations') {
      console.log('Loading no-code automations page');
      const bodyContent = await window.resourceLoader.loadTemplate('nocode-automations');
      content.innerHTML = bodyContent;

      // Load the JavaScript file
      try {
        await window.resourceLoader.loadScript('nocode-automations.js');
      } catch (error) {
        console.warn('No-code automations script loading failed:', error);
      }

      document.dispatchEvent(new CustomEvent('route:loaded', {
        detail: { route: 'nocode-automations', isModule: false }
      }));
      return;
    }

    if (route === 'nocode-lookups') {
      console.log('Loading no-code lookups page');
      const bodyContent = await window.resourceLoader.loadTemplate('nocode-lookups');
      content.innerHTML = bodyContent;

      // Load the JavaScript file
      try {
        await window.resourceLoader.loadScript('nocode-lookups.js');
      } catch (error) {
        console.warn('No-code lookups script loading failed:', error);
      }

      document.dispatchEvent(new CustomEvent('route:loaded', {
        detail: { route: 'nocode-lookups', isModule: false }
      }));
      return;
    }

    // ── Password Reset -- request view (Story 24.1.1 / T-24.005 T-24.006) ──────
    // #reset-password → request-reset form (email entry)
    if (route === 'reset-password') {
      console.log('Loading password-reset request view');
      content.innerHTML = '';
      try {
        const { renderRequestReset } = await import('./login-page.js');
        await renderRequestReset(content);
      } catch (error) {
        console.warn('login-page renderRequestReset failed:', error);
        content.innerHTML = '<div class="p-6 text-red-500">Failed to load password reset page.</div>';
      }
      document.dispatchEvent(new CustomEvent('route:loaded', {
        detail: { route: 'reset-password', isModule: false }
      }));
      return;
    }

    // ── Password Reset -- confirm view (Story 24.1.1 / T-24.005 T-24.007) ─────
    // #reset-password-confirm?token=xxx → set-new-password form
    if (route === 'reset-password-confirm' || route.startsWith('reset-password-confirm?')) {
      console.log('Loading password-reset confirm view');
      content.innerHTML = '';
      try {
        const { render } = await import('./password-reset-page.js');
        await render(content);
      } catch (error) {
        console.warn('password-reset-page loading failed:', error);
        content.innerHTML = '<div class="p-6 text-red-500">Failed to load password reset page.</div>';
      }
      document.dispatchEvent(new CustomEvent('route:loaded', {
        detail: { route: 'reset-password-confirm', isModule: false }
      }));
      return;
    }

    // ── Reports list ──────────────────────────────────────────────────────────
    if (route === 'reports' || route === 'reports-list') {
      console.log('Loading reports list page');
      const bodyContent = await window.resourceLoader.loadTemplate('reports-list');
      content.innerHTML = bodyContent;

      try {
        await window.resourceLoader.loadScript('reports-list-page.js');
      } catch (error) {
        console.warn('Reports list script loading failed:', error);
      }

      document.dispatchEvent(new CustomEvent('route:loaded', {
        detail: { route: 'reports', isModule: false }
      }));
      return;
    }

    // ── Report designer (create or edit) ─────────────────────────────────────
    if (route === 'reports/designer' || route.startsWith('reports/designer/') ||
        route === 'report-designer' || route.startsWith('report-designer?')) {
      console.log('Loading report designer page');
      const bodyContent = await window.resourceLoader.loadTemplate('report-designer');
      content.innerHTML = bodyContent;

      // Re-execute inline module scripts (scripts injected via innerHTML don't run automatically)
      content.querySelectorAll('script').forEach(oldScript => {
        const newScript = document.createElement('script');
        newScript.type = oldScript.type || 'text/javascript';
        newScript.textContent = oldScript.textContent;
        oldScript.replaceWith(newScript);
      });

      document.dispatchEvent(new CustomEvent('route:loaded', {
        detail: { route, isModule: false }
      }));
      return;
    }

    // ── Report viewer (run / view report) ────────────────────────────────────
    if (route.startsWith('report-viewer/') || route.startsWith('reports/viewer/')) {
      const reportId = route.split('/').pop();
      window.location.hash = `#/reports/designer/${reportId}`;
      return;
    }

    // Handle dashboard designer route
    if (route === 'dashboard-designer' || route.startsWith('dashboard-designer?')) {
      console.log('Loading dashboard designer page');

      // The dashboard-designer component is self-contained, just load it
      content.innerHTML = '<div id="dashboard-designer-container"></div>';

      // Load the JavaScript file
      try {
        await window.resourceLoader.loadScript('dashboard-designer.js');
      } catch (error) {
        console.warn('Dashboard designer script loading failed:', error);
      }

      document.dispatchEvent(new CustomEvent('route:loaded', {
        detail: { route: 'dashboard-designer', isModule: false }
      }));
      return;
    }

    // Handle dashboards list route
    if (route === 'dashboards-list') {
      console.log('Loading dashboards list page');
      const bodyContent = await window.resourceLoader.loadTemplate('dashboards-list');
      content.innerHTML = bodyContent;

      // Load the JavaScript file
      try {
        await window.resourceLoader.loadScript('dashboards-list-page.js');
      } catch (error) {
        console.warn('Dashboards list script loading failed:', error);
      }

      document.dispatchEvent(new CustomEvent('route:loaded', {
        detail: { route: 'dashboards-list', isModule: false }
      }));
      return;
    }

    // Check if this is a module route
    const moduleRoute = moduleRegistry.findRoute(`#/${route}`);

    if (moduleRoute && moduleRoute.handler) {
      // This is a module route - load and mount the module page.
      console.log(`Loading module route: ${route}`);

      // The shell always provides a clean light-DOM mount point.
      content.innerHTML = '<div id="app-content"></div>';
      const appContent = document.getElementById('app-content');

      try {
        // The handler returns a mount descriptor (ADR page-element contract):
        //   { kind: 'element', tag }  -> custom element, mounted by tag
        //   { kind: 'class', PageClass } -> light-DOM page class
        // For backward-compatibility we also accept a bare class/function
        // (older module.js handlers that return the PageClass directly).
        const result = await moduleRoute.handler();

        if (!result) {
          throw new Error('Module page failed to load');
        }

        // Normalize legacy return (bare class) into a descriptor.
        const descriptor = (typeof result === 'function')
          ? { kind: 'class', PageClass: result }
          : result;

        if (descriptor.kind === 'nocode') {
          // No-code-backed module route (ADR Step 3): mount the no-code CRUD
          // page for the declared entity via the SAME page contract. A single
          // module can thus mix auto-generated CRUD and hand-coded pages.
          const page = new NocodeEntityPage({
            entity: descriptor.entity,
            action: descriptor.action,
          });
          await page.render(appContent);
          appState.currentModulePage = page;
        } else if (descriptor.kind === 'element') {
          // Custom-element page: create the tag and append into #app-content.
          // The element's connectedCallback() does the rendering.
          const el = document.createElement(descriptor.tag);
          appContent.appendChild(el);
          // Track for teardown on next route change (optional lifecycle).
          appState.currentModulePage = el;
        } else if (descriptor.kind === 'class' && descriptor.PageClass) {
          const page = new descriptor.PageClass();
          if (typeof page.render !== 'function') {
            throw new Error('Module page class does not have a render() method');
          }
          await page.render();
          appState.currentModulePage = page;
        } else {
          throw new Error('Module route returned an unrecognized page descriptor');
        }

        // Dispatch event for route-specific JS
        document.dispatchEvent(new CustomEvent('route:loaded', {
          detail: { route, isModule: true }
        }));
      } catch (pageError) {
        // Clean error state (NOT a raw 404) when a module page fails to load.
        console.error(`Module page error for route "${route}":`, pageError);
        appContent.innerHTML = `
          <div class="max-w-xl mx-auto mt-12 p-6 bg-white border border-red-200 rounded-lg text-center">
            <i class="ph-duotone ph-warning-circle text-4xl text-red-500"></i>
            <h2 class="mt-3 text-lg font-semibold text-gray-900">This page could not be loaded</h2>
            <p class="mt-2 text-sm text-gray-600">
              The module page for <code class="px-1 bg-gray-100 rounded">${route}</code>
              failed to load. Please try again or contact your administrator.
            </p>
          </div>`;
        document.dispatchEvent(new CustomEvent('route:loaded', {
          detail: { route, isModule: true, error: true }
        }));
      }

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