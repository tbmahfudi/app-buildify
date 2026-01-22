/**
 * Menu Management Page
 * Provides UI for managing menu items via backend API
 */

import { apiFetch } from './api.js';
import { showToast } from './ui-utils.js';

class MenuManagement {
  constructor() {
    this.menuItems = [];
    this.currentEditId = null;
    this.selectedDeleteId = null;
  }

  /**
   * Initialize the menu management page
   */
  async init() {
    console.log('Initializing Menu Management');

    this.setupEventListeners();
    await this.loadMenuItems();
  }

  /**
   * Setup event listeners
   */
  setupEventListeners() {
    // Create button
    document.getElementById('btn-create-menu')?.addEventListener('click', () => {
      this.openCreateModal();
    });

    // Refresh button
    document.getElementById('btn-refresh-menu')?.addEventListener('click', () => {
      this.loadMenuItems();
    });

    // Expand/Collapse all
    document.getElementById('btn-expand-all')?.addEventListener('click', () => {
      this.expandAll();
    });

    document.getElementById('btn-collapse-all')?.addEventListener('click', () => {
      this.collapseAll();
    });

    // Modal close buttons
    document.getElementById('btn-close-modal')?.addEventListener('click', () => {
      this.closeModal();
    });

    document.getElementById('btn-cancel')?.addEventListener('click', () => {
      this.closeModal();
    });

    // Form submit
    document.getElementById('menu-form')?.addEventListener('submit', (e) => {
      e.preventDefault();
      this.saveMenuItem();
    });

    // Icon preview
    document.getElementById('input-icon')?.addEventListener('input', (e) => {
      this.updateIconPreview();
    });

    // Color pickers - sync color picker with text input
    document.getElementById('input-icon-color-primary')?.addEventListener('input', (e) => {
      document.getElementById('input-icon-color-primary-text').value = e.target.value;
      this.updateIconPreview();
    });

    document.getElementById('input-icon-color-primary-text')?.addEventListener('input', (e) => {
      const value = e.target.value;
      if (/^#[0-9A-Fa-f]{6}$/.test(value)) {
        document.getElementById('input-icon-color-primary').value = value;
        this.updateIconPreview();
      }
    });

    document.getElementById('input-icon-color-secondary')?.addEventListener('input', (e) => {
      document.getElementById('input-icon-color-secondary-text').value = e.target.value;
      this.updateIconPreview();
    });

    document.getElementById('input-icon-color-secondary-text')?.addEventListener('input', (e) => {
      const value = e.target.value;
      if (/^#[0-9A-Fa-f]{6}$/.test(value)) {
        document.getElementById('input-icon-color-secondary').value = value;
        this.updateIconPreview();
      }
    });

    // Delete modal
    document.getElementById('btn-cancel-delete')?.addEventListener('click', () => {
      this.closeDeleteModal();
    });

    document.getElementById('btn-confirm-delete')?.addEventListener('click', () => {
      this.confirmDelete();
    });

    // Close modals on backdrop click
    document.getElementById('menu-modal')?.addEventListener('click', (e) => {
      if (e.target.id === 'menu-modal') {
        this.closeModal();
      }
    });

    document.getElementById('delete-modal')?.addEventListener('click', (e) => {
      if (e.target.id === 'delete-modal') {
        this.closeDeleteModal();
      }
    });
  }

  /**
   * Load menu items from backend
   */
  async loadMenuItems() {
    const loadingEl = document.getElementById('menu-loading');
    const errorEl = document.getElementById('menu-error');
    const treeEl = document.getElementById('menu-tree');
    const emptyEl = document.getElementById('menu-empty');

    try {
      // Show loading
      loadingEl?.classList.remove('hidden');
      errorEl?.classList.add('hidden');
      treeEl.innerHTML = '';
      emptyEl?.classList.add('hidden');

      // Fetch menu items
      const response = await apiFetch('/menu/admin');

      if (!response.ok) {
        throw new Error(`Failed to fetch: ${response.status}`);
      }

      const data = await response.json();
      this.menuItems = data.items || [];

      // Hide loading
      loadingEl?.classList.add('hidden');

      // Render menu tree
      if (this.menuItems.length === 0) {
        emptyEl?.classList.remove('hidden');
      } else {
        this.renderMenuTree();
      }

    } catch (error) {
      console.error('Error loading menu items:', error);
      loadingEl?.classList.add('hidden');
      errorEl?.classList.remove('hidden');
      showToast('Failed to load menu items', 'error');
    }
  }

  /**
   * Render menu tree structure
   */
  renderMenuTree() {
    const treeEl = document.getElementById('menu-tree');
    if (!treeEl) return;

    // Build tree structure
    const tree = this.buildTree(this.menuItems);

    // Render tree
    treeEl.innerHTML = tree.map(item => this.renderMenuItem(item, 0)).join('');

    // Attach event listeners to action buttons
    this.attachMenuItemListeners();
  }

  /**
   * Build hierarchical tree structure
   */
  buildTree(items, parentId = null) {
    return items
      .filter(item => item.parent_id === parentId)
      .sort((a, b) => (a.order || 0) - (b.order || 0))
      .map(item => ({
        ...item,
        children: this.buildTree(items, item.id)
      }));
  }

  /**
   * Render a single menu item
   */
  renderMenuItem(item, level) {
    const hasChildren = item.children && item.children.length > 0;
    const indent = level * 24;
    const isExpanded = true; // Default expanded

    const statusBadge = item.is_active
      ? '<span class="px-2 py-0.5 text-xs bg-green-100 text-green-700 rounded">Active</span>'
      : '<span class="px-2 py-0.5 text-xs bg-gray-100 text-gray-600 rounded">Inactive</span>';

    const permissionBadge = item.permission
      ? `<span class="px-2 py-0.5 text-xs bg-blue-100 text-blue-700 rounded font-mono">${item.permission}</span>`
      : '';

    // Apply icon colors for duo-tone icons
    const iconClass = item.icon || 'ph-duotone ph-circle';
    const primaryColor = item.icon_color_primary || '#3b82f6';
    const secondaryColor = item.icon_color_secondary || '#93c5fd';
    const iconStyle = iconClass.includes('ph-duotone')
      ? `color: ${primaryColor}; --ph-duotone-primary: ${primaryColor}; --ph-duotone-secondary: ${secondaryColor};`
      : `color: ${primaryColor};`;

    const html = `
      <div class="menu-item" data-id="${item.id}" data-level="${level}">
        <div class="flex items-center gap-2 p-2 hover:bg-gray-50 rounded-lg group">
          <div style="width: ${indent}px"></div>

          ${hasChildren ? `
            <button class="toggle-btn w-5 h-5 flex items-center justify-center text-gray-400 hover:text-gray-600 transition" data-id="${item.id}">
              <i class="ph ph-caret-down transition-transform ${isExpanded ? '' : '-rotate-90'}"></i>
            </button>
          ` : '<div class="w-5"></div>'}

          <div class="flex-1 flex items-center gap-3">
            <i class="${iconClass} text-xl" style="${iconStyle}"></i>
            <div class="flex-1">
              <div class="flex items-center gap-2">
                <span class="font-medium text-gray-900">${item.title}</span>
                ${statusBadge}
                ${permissionBadge}
              </div>
              <div class="text-xs text-gray-500 mt-0.5">
                Code: <span class="font-mono">${item.code}</span>
                ${item.route ? ` • Route: <span class="font-mono">${item.route}</span>` : ''}
                ${item.is_system ? ' • <span class="text-amber-600">System Menu</span>' : ''}
              </div>
            </div>
          </div>

          <div class="opacity-0 group-hover:opacity-100 transition flex items-center gap-1">
            <button class="btn-edit p-2 hover:bg-blue-50 text-blue-600 rounded transition" data-id="${item.id}" title="Edit">
              <i class="ph ph-pencil-simple"></i>
            </button>
            ${!item.is_system ? `
              <button class="btn-delete p-2 hover:bg-red-50 text-red-600 rounded transition" data-id="${item.id}" title="Delete">
                <i class="ph ph-trash"></i>
              </button>
            ` : ''}
          </div>
        </div>

        ${hasChildren ? `
          <div class="children-container ${isExpanded ? '' : 'hidden'}" data-parent="${item.id}">
            ${item.children.map(child => this.renderMenuItem(child, level + 1)).join('')}
          </div>
        ` : ''}
      </div>
    `;

    return html;
  }

  /**
   * Attach event listeners to menu item buttons
   */
  attachMenuItemListeners() {
    // Toggle buttons
    document.querySelectorAll('.toggle-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const id = e.currentTarget.dataset.id;
        this.toggleMenuItem(id);
      });
    });

    // Edit buttons
    document.querySelectorAll('.btn-edit').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const id = e.currentTarget.dataset.id;
        this.openEditModal(id);
      });
    });

    // Delete buttons
    document.querySelectorAll('.btn-delete').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const id = e.currentTarget.dataset.id;
        this.openDeleteModal(id);
      });
    });
  }

  /**
   * Toggle menu item expansion
   */
  toggleMenuItem(id) {
    const container = document.querySelector(`.children-container[data-parent="${id}"]`);
    const toggleBtn = document.querySelector(`.toggle-btn[data-id="${id}"] i`);

    if (container && toggleBtn) {
      container.classList.toggle('hidden');
      toggleBtn.classList.toggle('-rotate-90');
    }
  }

  /**
   * Expand all menu items
   */
  expandAll() {
    document.querySelectorAll('.children-container').forEach(el => {
      el.classList.remove('hidden');
    });
    document.querySelectorAll('.toggle-btn i').forEach(el => {
      el.classList.remove('-rotate-90');
    });
  }

  /**
   * Collapse all menu items
   */
  collapseAll() {
    document.querySelectorAll('.children-container').forEach(el => {
      el.classList.add('hidden');
    });
    document.querySelectorAll('.toggle-btn i').forEach(el => {
      el.classList.add('-rotate-90');
    });
  }

  /**
   * Open create modal
   */
  openCreateModal() {
    this.currentEditId = null;
    document.getElementById('modal-title').textContent = 'Create Menu Item';
    document.getElementById('menu-form').reset();

    // Set default colors
    const defaultPrimary = '#3b82f6';
    const defaultSecondary = '#93c5fd';
    document.getElementById('input-icon-color-primary').value = defaultPrimary;
    document.getElementById('input-icon-color-primary-text').value = defaultPrimary;
    document.getElementById('input-icon-color-secondary').value = defaultSecondary;
    document.getElementById('input-icon-color-secondary-text').value = defaultSecondary;

    this.updateIconPreview();
    this.populateParentOptions();
    document.getElementById('menu-modal')?.classList.remove('hidden');
  }

  /**
   * Open edit modal
   */
  openEditModal(id) {
    const item = this.menuItems.find(m => m.id === id);
    if (!item) return;

    this.currentEditId = id;
    document.getElementById('modal-title').textContent = 'Edit Menu Item';

    // Populate form
    document.getElementById('input-code').value = item.code || '';
    document.getElementById('input-title').value = item.title || '';
    document.getElementById('input-icon').value = item.icon || '';
    document.getElementById('input-route').value = item.route || '';
    document.getElementById('input-permission').value = item.permission || '';
    document.getElementById('input-roles').value = item.required_roles ? JSON.stringify(item.required_roles) : '';
    document.getElementById('input-description').value = item.description || '';
    document.getElementById('input-order').value = item.order || 0;
    document.getElementById('input-active').checked = item.is_active !== false;
    document.getElementById('input-visible').checked = item.is_visible !== false;

    // Populate icon colors
    const primaryColor = item.icon_color_primary || '#3b82f6';
    const secondaryColor = item.icon_color_secondary || '#93c5fd';
    document.getElementById('input-icon-color-primary').value = primaryColor;
    document.getElementById('input-icon-color-primary-text').value = primaryColor;
    document.getElementById('input-icon-color-secondary').value = secondaryColor;
    document.getElementById('input-icon-color-secondary-text').value = secondaryColor;

    this.updateIconPreview();
    this.populateParentOptions(item.parent_id);

    document.getElementById('menu-modal')?.classList.remove('hidden');
  }

  /**
   * Close modal
   */
  closeModal() {
    document.getElementById('menu-modal')?.classList.add('hidden');
    this.currentEditId = null;
  }

  /**
   * Update icon preview with colors
   */
  updateIconPreview() {
    const preview = document.querySelector('#icon-preview i');
    if (!preview) return;

    const iconClass = document.getElementById('input-icon')?.value || '';
    const primaryColor = document.getElementById('input-icon-color-primary')?.value || '#3b82f6';
    const secondaryColor = document.getElementById('input-icon-color-secondary')?.value || '#93c5fd';

    preview.className = iconClass || 'text-2xl text-gray-400';

    // Apply colors if it's a duo-tone icon
    if (iconClass.includes('ph-duotone')) {
      preview.style.color = primaryColor;
      preview.style.setProperty('--ph-duotone-primary', primaryColor);
      preview.style.setProperty('--ph-duotone-secondary', secondaryColor);
    } else {
      preview.style.color = primaryColor;
      preview.style.removeProperty('--ph-duotone-primary');
      preview.style.removeProperty('--ph-duotone-secondary');
    }
  }

  /**
   * Populate parent options
   */
  populateParentOptions(selectedId = null) {
    const select = document.getElementById('input-parent');
    if (!select) return;

    // Clear existing options except first
    select.innerHTML = '<option value="">None (Top Level)</option>';

    // Add menu items as options (excluding self if editing)
    const options = this.menuItems
      .filter(item => item.id !== this.currentEditId)
      .map(item => `<option value="${item.id}" ${item.id === selectedId ? 'selected' : ''}>${item.title}</option>`)
      .join('');

    select.innerHTML += options;
  }

  /**
   * Save menu item
   */
  async saveMenuItem() {
    const form = document.getElementById('menu-form');
    const formData = new FormData(form);

    try {
      // Build request data
      const data = {
        code: formData.get('code'),
        title: formData.get('title'),
        icon: formData.get('icon') || null,
        icon_color_primary: formData.get('icon_color_primary') || '#3b82f6',
        icon_color_secondary: formData.get('icon_color_secondary') || '#93c5fd',
        route: formData.get('route') || null,
        parent_id: formData.get('parent_id') || null,
        permission: formData.get('permission') || null,
        description: formData.get('description') || null,
        order: parseInt(formData.get('order')) || 0,
        is_active: formData.get('is_active') === 'on',
        is_visible: formData.get('is_visible') === 'on'
      };

      // Parse roles if provided
      const rolesInput = formData.get('required_roles');
      if (rolesInput) {
        try {
          data.required_roles = JSON.parse(rolesInput);
        } catch (e) {
          showToast('Invalid JSON format for roles', 'error');
          return;
        }
      }

      // Send request
      let response;
      if (this.currentEditId) {
        // Update existing
        response = await apiFetch(`/menu/${this.currentEditId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data)
        });
      } else {
        // Create new
        response = await apiFetch('/menu', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data)
        });
      }

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to save menu item');
      }

      showToast(
        this.currentEditId ? 'Menu item updated successfully' : 'Menu item created successfully',
        'success'
      );

      this.closeModal();
      await this.loadMenuItems();

    } catch (error) {
      console.error('Error saving menu item:', error);
      showToast(error.message || 'Failed to save menu item', 'error');
    }
  }

  /**
   * Open delete modal
   */
  openDeleteModal(id) {
    const item = this.menuItems.find(m => m.id === id);
    if (!item) return;

    this.selectedDeleteId = id;
    document.getElementById('delete-menu-name').textContent = `"${item.title}"`;
    document.getElementById('delete-modal')?.classList.remove('hidden');
  }

  /**
   * Close delete modal
   */
  closeDeleteModal() {
    document.getElementById('delete-modal')?.classList.add('hidden');
    this.selectedDeleteId = null;
  }

  /**
   * Confirm delete
   */
  async confirmDelete() {
    if (!this.selectedDeleteId) return;

    try {
      const response = await apiFetch(`/menu/${this.selectedDeleteId}`, {
        method: 'DELETE'
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to delete menu item');
      }

      showToast('Menu item deleted successfully', 'success');
      this.closeDeleteModal();
      await this.loadMenuItems();

    } catch (error) {
      console.error('Error deleting menu item:', error);
      showToast(error.message || 'Failed to delete menu item', 'error');
    }
  }
}

// Initialize when route is loaded
document.addEventListener('route:loaded', async (event) => {
  const { route } = event.detail;

  if (route === 'menu-management') {
    console.log('Menu Management route loaded');
    const menuMgmt = new MenuManagement();
    await menuMgmt.init();
  }
});

export default MenuManagement;
