/**
 * RBAC (Role-Based Access Control) Module
 * Provides permission checking and role-based UI visibility
 */

import { getCurrentUser as getUser } from './app.js';

/**
 * Get current user from app state
 * @returns {Object|null} Current user object
 */
function getCurrentUser() {
  return getUser() || null;
}

/**
 * Check if user is a superuser
 * @returns {boolean} True if user is superuser
 */
export function isSuperuser() {
  const user = getCurrentUser();
  return user?.is_superuser === true;
}

/**
 * Check if user has a specific role
 * @param {string} role - Role name to check
 * @returns {boolean} True if user has the role
 */
export function hasRole(role) {
  const user = getCurrentUser();
  if (!user) return false;

  // Superusers have all roles
  if (user.is_superuser) return true;

  // Check if user has the role
  return Array.isArray(user.roles) && user.roles.includes(role);
}

/**
 * Check if user has any of the specified roles
 * @param {string[]} roles - Array of role names
 * @returns {boolean} True if user has any of the roles
 */
export function hasAnyRole(roles) {
  if (!Array.isArray(roles)) return false;
  return roles.some(role => hasRole(role));
}

/**
 * Check if user has all of the specified roles
 * @param {string[]} roles - Array of role names
 * @returns {boolean} True if user has all roles
 */
export function hasAllRoles(roles) {
  if (!Array.isArray(roles)) return false;
  return roles.every(role => hasRole(role));
}

/**
 * Check if user can perform an action based on permission
 * For metadata-driven permissions
 * @param {string} permission - Permission string (e.g., "users:create")
 * @returns {boolean} True if user has permission
 */
export function can(permission) {
  const user = getCurrentUser();
  if (!user) return false;

  // Superusers can do everything
  if (user.is_superuser) return true;

  // For now, check roles
  // In the future, this can be enhanced with fine-grained permissions
  const [resource, action] = permission.split(':');

  // Admin role has all permissions
  if (hasRole('admin')) return true;

  // Check resource-specific permissions
  switch (action) {
    case 'view':
    case 'list':
      // All authenticated users can view
      return true;
    case 'create':
    case 'update':
    case 'delete':
      // Only admins can modify
      return hasRole('admin');
    default:
      return false;
  }
}

/**
 * Alias for can() function - checks if user has a specific permission
 * @param {string} permission - Permission string (e.g., "users:create")
 * @returns {boolean} True if user has permission
 */
export function hasPermission(permission) {
  return can(permission);
}

/**
 * Check if user can view a field based on metadata RBAC
 * @param {Object} fieldMeta - Field metadata with rbac_view array
 * @returns {boolean} True if user can view the field
 */
export function canViewField(fieldMeta) {
  const user = getCurrentUser();
  if (!user) return false;

  // Superusers can view everything
  if (user.is_superuser) return true;

  // If no RBAC defined, allow viewing
  if (!fieldMeta?.rbac_view || !Array.isArray(fieldMeta.rbac_view)) {
    return true;
  }

  // Check if user has any of the required roles
  return hasAnyRole(fieldMeta.rbac_view);
}

/**
 * Check if user can edit a field based on metadata RBAC
 * @param {Object} fieldMeta - Field metadata with rbac_edit array
 * @returns {boolean} True if user can edit the field
 */
export function canEditField(fieldMeta) {
  const user = getCurrentUser();
  if (!user) return false;

  // Superusers can edit everything
  if (user.is_superuser) return true;

  // If no RBAC defined, check general permissions
  if (!fieldMeta?.rbac_edit || !Array.isArray(fieldMeta.rbac_edit)) {
    return hasRole('admin');
  }

  // Check if user has any of the required roles
  return hasAnyRole(fieldMeta.rbac_edit);
}

/**
 * Check if user belongs to specific tenant
 * @param {string} tenantId - Tenant ID to check
 * @returns {boolean} True if user belongs to tenant
 */
export function belongsToTenant(tenantId) {
  const user = getCurrentUser();
  if (!user) return false;

  // Superusers can access all tenants
  if (user.is_superuser) return true;

  return user.tenant_id === tenantId;
}

/**
 * Get user's roles
 * @returns {string[]} Array of role names
 */
export function getUserRoles() {
  const user = getCurrentUser();
  return user?.roles || [];
}

/**
 * Get user's tenant ID
 * @returns {string|null} Tenant ID or null
 */
export function getUserTenantId() {
  const user = getCurrentUser();
  return user?.tenant_id || null;
}

/**
 * Show/hide element based on role
 * @param {HTMLElement} element - DOM element
 * @param {string|string[]} roles - Role or array of roles
 */
export function showIfHasRole(element, roles) {
  if (!element) return;

  const roleArray = Array.isArray(roles) ? roles : [roles];
  const hasAccess = hasAnyRole(roleArray);

  if (hasAccess) {
    element.style.display = '';
    element.removeAttribute('hidden');
  } else {
    element.style.display = 'none';
    element.setAttribute('hidden', 'true');
  }
}

/**
 * Enable/disable element based on role
 * @param {HTMLElement} element - DOM element
 * @param {string|string[]} roles - Role or array of roles
 */
export function enableIfHasRole(element, roles) {
  if (!element) return;

  const roleArray = Array.isArray(roles) ? roles : [roles];
  const hasAccess = hasAnyRole(roleArray);

  if (hasAccess) {
    element.removeAttribute('disabled');
  } else {
    element.setAttribute('disabled', 'true');
  }
}

/**
 * Apply RBAC to multiple elements based on data attributes
 * Usage: <button data-rbac-role="admin">Admin Only</button>
 * @param {HTMLElement} container - Container element to search within
 */
export function applyRBACToElements(container = document) {
  // Handle role-based visibility
  const roleElements = container.querySelectorAll('[data-rbac-role]');
  roleElements.forEach(el => {
    const roles = el.getAttribute('data-rbac-role').split(',').map(r => r.trim());
    showIfHasRole(el, roles);
  });

  // Handle permission-based visibility
  const permElements = container.querySelectorAll('[data-rbac-permission]');
  permElements.forEach(el => {
    const permission = el.getAttribute('data-rbac-permission');
    const hasPermission = can(permission);

    if (hasPermission) {
      el.style.display = '';
      el.removeAttribute('hidden');
    } else {
      el.style.display = 'none';
      el.setAttribute('hidden', 'true');
    }
  });
}

/**
 * Filter menu items based on user roles and permissions
 * @param {Array} menuItems - Array of menu item objects
 * @returns {Array} Filtered menu items
 */
export function filterMenuByRole(menuItems) {
  const user = getCurrentUser();
  if (!user) return [];

  return menuItems.filter(item => {
    // Check permission if specified
    if (item.permission) {
      const hasAccess = can(item.permission);
      if (!hasAccess) return false;
    }

    // Check roles if specified
    if (item.roles && Array.isArray(item.roles) && item.roles.length > 0) {
      return hasAnyRole(item.roles);
    }

    // If no roles or permission specified, show to all authenticated users
    return true;
  }).map(item => {
    // Recursively filter submenu items
    if (item.submenu && Array.isArray(item.submenu)) {
      return {
        ...item,
        submenu: filterMenuByRole(item.submenu)
      };
    }
    return item;
  });
}

// Export all functions as default object
export default {
  isSuperuser,
  hasRole,
  hasAnyRole,
  hasAllRoles,
  can,
  hasPermission,
  canViewField,
  canEditField,
  belongsToTenant,
  getUserRoles,
  getUserTenantId,
  showIfHasRole,
  enableIfHasRole,
  applyRBACToElements,
  filterMenuByRole
};
