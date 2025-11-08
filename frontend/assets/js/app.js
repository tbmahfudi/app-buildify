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

  // Load and apply saved sidebar state
  loadSidebarState();

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

  // Sidebar toggle button (navbar)
  const sidebarToggle = document.getElementById('sidebar-toggle');

  if (sidebarToggle) {
    sidebarToggle.addEventListener('click', toggleSidebar);
  }
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
 * Update the collapse button icon direction
 */
function updateCollapseButtonIcon(isCollapsed) {
  const collapseBtn = document.getElementById('sidebar-collapse-btn');
  if (!collapseBtn) return;

  const icon = collapseBtn.querySelector('i');
  const tooltip = collapseBtn.querySelector('.sidebar-collapse-tooltip');

  if (isCollapsed) {
    // Show right arrow (expand)
    icon.className = 'ph-duotone ph-caret-right text-xl transition-transform duration-300';
    if (tooltip) tooltip.textContent = 'Expand sidebar';
    collapseBtn.setAttribute('title', 'Expand sidebar');
  } else {
    // Show left arrow (collapse)
    icon.className = 'ph-duotone ph-caret-left text-xl transition-transform duration-300';
    if (tooltip) tooltip.textContent = 'Collapse sidebar';
    collapseBtn.setAttribute('title', 'Collapse sidebar');
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
    updateCollapseButtonIcon(true);
  } else {
    sidebar.setAttribute('data-collapsed', 'false');
    sidebar.classList.remove('sidebar-collapsed');
    sidebar.classList.add('w-64');
    updateCollapseButtonIcon(false);
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
  const sidebar = document.getElementById('sidebar');
  const isCollapsed = sidebar?.getAttribute('data-collapsed') === 'true';

  const link = document.createElement('a');
  link.className = 'sidebar-menu-item flex items-center gap-3 px-4 py-3 rounded-lg text-gray-700 hover:bg-gray-100 hover:text-blue-600 transition-colors group relative';
  link.href = `#${item.route}`;
  link.setAttribute('data-tooltip', item.title);

  // Use icon from menu item or fallback to getMenuIcon
  const icon = item.icon || getMenuIcon(item.route);

  if (isCollapsed) {
    link.innerHTML = `
      <div class="w-full flex justify-center">
        <i class="${icon} text-2xl"></i>
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
    link.innerHTML = `
      <i class="${icon} text-xl flex-shrink-0"></i>
      <span class="sidebar-menu-label font-medium">${item.title}</span>
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
    parent.innerHTML = `
      <i class="${icon} text-2xl"></i>
    `;

    // Create popup menu with fixed positioning to avoid clipping
    const popup = createCollapsedSubmenuPopup(item);
    document.body.appendChild(popup);

    // Position popup on hover
    parent.addEventListener('mouseenter', () => {
      const rect = parent.getBoundingClientRect();
      popup.style.left = `${rect.right + 8}px`;
      popup.style.top = `${rect.top}px`;
      popup.classList.remove('hidden');
    });

    parent.addEventListener('mouseleave', (e) => {
      const popupRect = popup.getBoundingClientRect();
      const isMovingToPopup = e.clientX >= popupRect.left && e.clientX <= popupRect.right &&
                               e.clientY >= popupRect.top && e.clientY <= popupRect.bottom;
      if (!isMovingToPopup) {
        setTimeout(() => {
          if (!popup.matches(':hover')) {
            popup.classList.add('hidden');
          }
        }, 100);
      }
    });

    popup.addEventListener('mouseleave', () => {
      popup.classList.add('hidden');
    });

    container.appendChild(parent);
  } else {
    // Expanded state - show full menu with arrow
    const parent = document.createElement('div');
    parent.className = 'flex items-center justify-between px-4 py-3 rounded-lg text-gray-700 hover:bg-gray-100 cursor-pointer transition-colors';

    const icon = item.icon || getMenuIcon(item.route);
    parent.innerHTML = `
      <div class="flex items-center gap-3">
        <i class="${icon} text-xl flex-shrink-0"></i>
        <span class="font-medium sidebar-menu-label">${item.title}</span>
      </div>
      <i class="ph ph-caret-down text-sm transition-transform submenu-arrow"></i>
    `;

    // Create submenu
    const submenu = document.createElement('div');
    submenu.className = 'submenu hidden ml-4 mt-1 space-y-1';

    item.submenu.forEach(subitem => {
      if (subitem.submenu && subitem.submenu.length > 0) {
        // Nested submenu - recursively create
        const nestedSubmenuItem = createSubmenuItem(subitem, level + 1);
        submenu.appendChild(nestedSubmenuItem);
      } else {
        // Regular link
        const sublink = document.createElement('a');
        sublink.className = 'flex items-center gap-3 px-4 py-2 rounded-lg text-gray-600 hover:bg-gray-50 hover:text-blue-600 transition-colors text-sm';
        sublink.href = `#${subitem.route}`;

        const subicon = subitem.icon || 'ph-duotone ph-square';
        sublink.innerHTML = `
          <i class="${subicon} text-lg flex-shrink-0"></i>
          <span>${subitem.title}</span>
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
  popupHeader.className = 'px-4 py-2 bg-gray-50 border-b border-gray-200';
  popupHeader.innerHTML = `<span class="font-semibold text-gray-700 text-sm">${item.title}</span>`;
  popup.appendChild(popupHeader);

  // Check if all items are final (no submenu) - use grid layout
  const allItemsFinal = item.submenu.every(subitem => !subitem.submenu || subitem.submenu.length === 0);

  // Add submenu items
  const popupContent = document.createElement('div');

  if (allItemsFinal) {
    // Grid layout for final items - big icons with text below
    popupContent.className = 'p-4 grid grid-cols-2 gap-3';

    item.submenu.forEach(subitem => {
      const gridItem = document.createElement('a');
      gridItem.className = 'flex flex-col items-center gap-2 p-3 rounded-lg text-gray-600 hover:bg-blue-50 hover:text-blue-600 transition-colors cursor-pointer';
      gridItem.href = `#${subitem.route}`;

      const subicon = subitem.icon || 'ph-duotone ph-square';
      gridItem.innerHTML = `
        <i class="${subicon} text-4xl"></i>
        <span class="text-xs text-center font-medium leading-tight">${subitem.title}</span>
      `;

      gridItem.onclick = () => {
        document.querySelectorAll('#sidebar-nav a').forEach(l => {
          l.classList.remove('bg-blue-50', 'text-blue-600');
          l.classList.add('text-gray-600');
        });
        gridItem.classList.add('bg-blue-50', 'text-blue-600');
        gridItem.classList.remove('text-gray-600');
        popup.classList.add('hidden');
      };

      popupContent.appendChild(gridItem);
    });
  } else {
    // List layout for items with submenus
    popupContent.className = 'py-1';
    const childPopups = [];

    item.submenu.forEach(subitem => {
      if (subitem.submenu && subitem.submenu.length > 0) {
        // Nested submenu - create item that shows another popup on hover
        const nestedContainer = document.createElement('div');
        nestedContainer.className = 'relative';

        const nestedTrigger = document.createElement('div');
        nestedTrigger.className = 'flex items-center justify-between px-4 py-2 text-gray-700 hover:bg-blue-50 hover:text-blue-600 cursor-pointer transition-colors';

        const subicon = subitem.icon || 'ph-duotone ph-folder';
        nestedTrigger.innerHTML = `
          <div class="flex items-center gap-3">
            <i class="${subicon} text-lg"></i>
            <span class="text-sm font-medium">${subitem.title}</span>
          </div>
          <i class="ph ph-caret-right text-xs"></i>
        `;

        // Create nested popup menu
        const nestedPopup = createNestedPopup(subitem, popup);
        childPopups.push(nestedPopup);
        document.body.appendChild(nestedPopup);

        // Show nested popup on hover
        nestedTrigger.addEventListener('mouseenter', () => {
          // Hide other child popups
          childPopups.forEach(p => {
            if (p !== nestedPopup) p.classList.add('hidden');
          });

          const rect = nestedTrigger.getBoundingClientRect();
          nestedPopup.style.left = `${rect.right + 8}px`;
          nestedPopup.style.top = `${rect.top}px`;
          nestedPopup.classList.remove('hidden');
        });

        nestedTrigger.addEventListener('mouseleave', (e) => {
          const nestedRect = nestedPopup.getBoundingClientRect();
          const isMovingToNested = e.clientX >= nestedRect.left && e.clientX <= nestedRect.right &&
                                    e.clientY >= nestedRect.top && e.clientY <= nestedRect.bottom;
          if (!isMovingToNested) {
            setTimeout(() => {
              if (!nestedPopup.matches(':hover')) {
                nestedPopup.classList.add('hidden');
              }
            }, 100);
          }
        });

        nestedPopup.addEventListener('mouseleave', () => {
          setTimeout(() => {
            if (!nestedPopup.matches(':hover') && !nestedTrigger.matches(':hover')) {
              nestedPopup.classList.add('hidden');
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
        sublink.innerHTML = `
          <i class="${subicon} text-lg"></i>
          <span>${subitem.title}</span>
        `;

        sublink.onclick = (e) => {
          document.querySelectorAll('#sidebar-nav a').forEach(l => {
            l.classList.remove('bg-blue-50', 'text-blue-600');
            l.classList.add('text-gray-600');
          });
          sublink.classList.add('bg-blue-50', 'text-blue-600');
          sublink.classList.remove('text-gray-600');
          popup.classList.add('hidden');
        };

        popupContent.appendChild(sublink);
      }
    });

    // Store child popups reference
    popup.childPopups = childPopups;
  }

  popup.appendChild(popupContent);

  // Enhanced mouseleave to check child popups
  popup.addEventListener('mouseleave', () => {
    setTimeout(() => {
      const anyChildHovered = popup.childPopups && popup.childPopups.some(child => child.matches(':hover'));
      if (!popup.matches(':hover') && !anyChildHovered) {
        popup.classList.add('hidden');
        if (popup.childPopups) {
          popup.childPopups.forEach(child => child.classList.add('hidden'));
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
    // Grid layout for final items
    nestedPopup.className = 'fixed hidden bg-white border border-gray-200 rounded-xl shadow-xl min-w-[280px] overflow-hidden';
    nestedPopup.style.zIndex = '100000';

    const nestedContent = document.createElement('div');
    nestedContent.className = 'p-4 grid grid-cols-2 gap-3';

    item.submenu.forEach(nestedItem => {
      const gridItem = document.createElement('a');
      gridItem.className = 'flex flex-col items-center gap-2 p-3 rounded-lg text-gray-600 hover:bg-blue-50 hover:text-blue-600 transition-colors cursor-pointer';
      gridItem.href = `#${nestedItem.route}`;

      const nestedIcon = nestedItem.icon || 'ph-duotone ph-circle';
      gridItem.innerHTML = `
        <i class="${nestedIcon} text-4xl"></i>
        <span class="text-xs text-center font-medium leading-tight">${nestedItem.title}</span>
      `;

      gridItem.onclick = () => {
        document.querySelectorAll('#sidebar-nav a').forEach(l => {
          l.classList.remove('bg-blue-50', 'text-blue-600');
          l.classList.add('text-gray-600');
        });
        gridItem.classList.add('bg-blue-50', 'text-blue-600');
        gridItem.classList.remove('text-gray-600');
        parentPopup.classList.add('hidden');
        nestedPopup.classList.add('hidden');
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

    item.submenu.forEach(nestedItem => {
      const nestedLink = document.createElement('a');
      nestedLink.className = 'flex items-center gap-3 px-4 py-2 text-gray-600 hover:bg-blue-50 hover:text-blue-600 transition-colors text-sm';
      nestedLink.href = `#${nestedItem.route}`;

      const nestedIcon = nestedItem.icon || 'ph-duotone ph-circle';
      nestedLink.innerHTML = `
        <i class="${nestedIcon} text-base"></i>
        <span>${nestedItem.title}</span>
      `;

      nestedLink.onclick = () => {
        document.querySelectorAll('#sidebar-nav a').forEach(l => {
          l.classList.remove('bg-blue-50', 'text-blue-600');
          l.classList.add('text-gray-600');
        });
        nestedLink.classList.add('bg-blue-50', 'text-blue-600');
        nestedLink.classList.remove('text-gray-600');
        parentPopup.classList.add('hidden');
        nestedPopup.classList.add('hidden');
      };

      nestedContent.appendChild(nestedLink);
    });

    nestedPopup.appendChild(nestedContent);
  }

  return nestedPopup;
}

function getMenuIcon(route) {
  const icons = {
    'dashboard': 'ph-duotone ph-gauge',
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
            <i class="ph-duotone ph-warning text-yellow-500 text-3xl"></i>
            <div>
              <h3 class="text-lg font-semibold text-yellow-800 mb-2">Page Not Found</h3>
              <p class="text-yellow-700 mb-4">The page "${route}" could not be loaded.</p>
              <button
                onclick="window.location.hash = 'dashboard'"
                class="px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition flex items-center gap-2">
                <i class="ph ph-house"></i> Go to Dashboard
              </button>
            </div>
          </div>
        </div>
      </div>
    `;
  }
}