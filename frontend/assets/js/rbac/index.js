/**
 * RBAC Module Index
 * Central export point for all RBAC modules
 *
 * Usage:
 *   import { rbacAPI, modalManager, permissionGrid, permissionAssignmentHelper } from './rbac/index.js';
 */

// API Client
export { rbacAPI } from './rbac-api.js';

// UI Controllers
export { TableController } from './table-controller.js';
export { modalManager, ModalController } from './modal-controller.js';
export { permissionGrid, PermissionGrid } from './permission-grid.js';
export { permissionAssignmentHelper, PermissionAssignmentHelper } from './permission-assignment-helper.js';

// Utilities
export { keyboardShortcuts, KeyboardShortcuts, setupDefaultShortcuts } from './keyboard-shortcuts.js';
