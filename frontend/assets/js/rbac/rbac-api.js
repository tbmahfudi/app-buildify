/**
 * RBAC API Client
 * Centralized API calls for RBAC operations
 */

import { apiFetch } from '../api.js';

export const rbacAPI = {
  // ============================================================================
  // ROLES
  // ============================================================================

  async getRoles(params = {}) {
    const query = new URLSearchParams(params);
    const response = await apiFetch(`/rbac/roles?${query}`);
    return response.json();
  },

  async getRole(roleId) {
    const response = await apiFetch(`/rbac/roles/${roleId}`);
    return response.json();
  },

  // ============================================================================
  // PERMISSIONS
  // ============================================================================

  async getPermissions(params = {}) {
    const query = new URLSearchParams(params);
    const response = await apiFetch(`/rbac/permissions?${query}`);
    return response.json();
  },

  async getPermission(permissionId) {
    const response = await apiFetch(`/rbac/permissions/${permissionId}`);
    return response.json();
  },

  async getGroupedPermissions(params = {}) {
    const query = new URLSearchParams(params);
    const response = await apiFetch(`/rbac/permissions/grouped?${query}`);
    return response.json();
  },

  async getPermissionCategories() {
    const response = await apiFetch('/rbac/permission-categories');
    return response.json();
  },

  async createPermission(permissionData) {
    const response = await apiFetch('/rbac/permissions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(permissionData)
    });
    return response.json();
  },

  async updatePermission(permissionId, permissionData) {
    const response = await apiFetch(`/rbac/permissions/${permissionId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(permissionData)
    });
    return response.json();
  },

  async deletePermission(permissionId) {
    const response = await apiFetch(`/rbac/permissions/${permissionId}`, {
      method: 'DELETE'
    });
    return response.json();
  },

  // ============================================================================
  // ROLE PERMISSIONS
  // ============================================================================

  async assignPermissionsToRole(roleId, permissionIds) {
    const response = await apiFetch(`/rbac/roles/${roleId}/permissions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(permissionIds)
    });
    return response.json();
  },

  async removePermissionFromRole(roleId, permissionId) {
    const response = await apiFetch(`/rbac/roles/${roleId}/permissions/${permissionId}`, {
      method: 'DELETE'
    });
    return response.json();
  },

  async bulkUpdateRolePermissions(roleId, grantIds, revokeIds) {
    const response = await apiFetch(`/rbac/roles/${roleId}/permissions/bulk`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        grant_ids: grantIds,
        revoke_ids: revokeIds
      })
    });
    return response.json();
  },

  // ============================================================================
  // GROUPS
  // ============================================================================

  async getGroups(params = {}) {
    const query = new URLSearchParams(params);
    const response = await apiFetch(`/rbac/groups?${query}`);
    return response.json();
  },

  async getGroup(groupId) {
    const response = await apiFetch(`/rbac/groups/${groupId}`);
    return response.json();
  },

  async addMembersToGroup(groupId, userIds) {
    const response = await apiFetch(`/rbac/groups/${groupId}/members`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(userIds)
    });
    return response.json();
  },

  async removeMemberFromGroup(groupId, userId) {
    const response = await apiFetch(`/rbac/groups/${groupId}/members/${userId}`, {
      method: 'DELETE'
    });
    return response.json();
  },

  async assignRolesToGroup(groupId, roleIds) {
    const response = await apiFetch(`/rbac/groups/${groupId}/roles`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(roleIds)
    });
    return response.json();
  },

  async removeRoleFromGroup(groupId, roleId) {
    const response = await apiFetch(`/rbac/groups/${groupId}/roles/${roleId}`, {
      method: 'DELETE'
    });
    return response.json();
  },

  // ============================================================================
  // USERS
  // ============================================================================

  async getUsers(params = {}) {
    const query = new URLSearchParams(params);
    const response = await apiFetch(`/org/users?${query}`);
    return response.json();
  },

  async getUser(userId) {
    const response = await apiFetch(`/org/users/${userId}`);
    return response.json();
  },

  async createUser(userData) {
    const response = await apiFetch('/org/users', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(userData)
    });
    return response.json();
  },

  async updateUser(userId, userData) {
    const response = await apiFetch(`/org/users/${userId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(userData)
    });
    return response.json();
  },

  async deleteUser(userId) {
    const response = await apiFetch(`/org/users/${userId}`, {
      method: 'DELETE'
    });
    return response.json();
  },

  // ============================================================================
  // USER RBAC
  // ============================================================================

  async getUserRoles(userId) {
    const response = await apiFetch(`/rbac/users/${userId}/roles`);
    return response.json();
  },

  async getUserPermissions(userId) {
    const response = await apiFetch(`/rbac/users/${userId}/permissions`);
    return response.json();
  },

  async assignRolesToUser(userId, roleIds) {
    const response = await apiFetch(`/rbac/users/${userId}/roles`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(roleIds)
    });
    return response.json();
  },

  async removeRoleFromUser(userId, roleId) {
    const response = await apiFetch(`/rbac/users/${userId}/roles/${roleId}`, {
      method: 'DELETE'
    });
    return response.json();
  },

  // ============================================================================
  // ORGANIZATION
  // ============================================================================

  async getOrganizationStructure(tenantId = null) {
    const params = tenantId ? `?tenant_id=${tenantId}` : '';
    const response = await apiFetch(`/rbac/organization-structure${params}`);
    return response.json();
  },

  async getCompanies(params = {}) {
    const query = new URLSearchParams(params);
    const response = await apiFetch(`/org/companies?${query}`);
    return response.json();
  },

  // ============================================================================
  // DASHBOARD
  // ============================================================================

  async getDashboardStats(companyId = null) {
    // Fetch multiple endpoints for dashboard stats
    const params = companyId ? { company_id: companyId, limit: 1 } : { limit: 1 };

    const [roles, permissions, groups, users] = await Promise.all([
      this.getRoles(params),
      this.getPermissions(params),
      this.getGroups(params),
      this.getUsers(params)
    ]);

    return {
      totalRoles: roles.total || 0,
      totalPermissions: permissions.total || 0,
      totalGroups: groups.total || 0,
      totalUsers: users.total || 0
    };
  }
};
