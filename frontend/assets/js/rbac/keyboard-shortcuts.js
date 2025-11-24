/**
 * Keyboard Shortcuts Handler
 * Global keyboard shortcuts for RBAC interface
 */

export class KeyboardShortcuts {
  constructor() {
    this.shortcuts = new Map();
    this.enabled = true;
    this.init();
  }

  init() {
    document.addEventListener('keydown', (e) => {
      if (!this.enabled) return;

      // Don't trigger if user is typing in an input
      if (['INPUT', 'TEXTAREA', 'SELECT'].includes(e.target.tagName)) {
        // Allow Escape to work in inputs
        if (e.key !== 'Escape') return;
      }

      const key = this.getKeyCombo(e);
      const handler = this.shortcuts.get(key);

      if (handler) {
        e.preventDefault();
        handler(e);
      }
    });
  }

  getKeyCombo(e) {
    const parts = [];
    if (e.ctrlKey || e.metaKey) parts.push('ctrl');
    if (e.shiftKey) parts.push('shift');
    if (e.altKey) parts.push('alt');
    parts.push(e.key.toLowerCase());
    return parts.join('+');
  }

  register(keyCombo, handler, description = '') {
    this.shortcuts.set(keyCombo.toLowerCase(), handler);
    if (description) {
      // Store description for help menu
      if (!this.descriptions) this.descriptions = new Map();
      this.descriptions.set(keyCombo.toLowerCase(), description);
    }
  }

  unregister(keyCombo) {
    this.shortcuts.delete(keyCombo.toLowerCase());
    if (this.descriptions) {
      this.descriptions.delete(keyCombo.toLowerCase());
    }
  }

  enable() {
    this.enabled = true;
  }

  disable() {
    this.enabled = false;
  }

  getHelp() {
    if (!this.descriptions) return [];
    return Array.from(this.descriptions.entries()).map(([key, desc]) => ({
      key: this.formatKeyCombo(key),
      description: desc
    }));
  }

  formatKeyCombo(keyCombo) {
    return keyCombo
      .split('+')
      .map(part => {
        if (part === 'ctrl') return '⌘/Ctrl';
        if (part === 'shift') return '⇧';
        if (part === 'alt') return '⌥';
        return part.toUpperCase();
      })
      .join(' + ');
  }

  showHelp() {
    const help = this.getHelp();
    if (help.length === 0) return;

    const helpHTML = `
      <div class="space-y-4">
        <h3 class="text-lg font-semibold text-gray-900">Keyboard Shortcuts</h3>
        <div class="space-y-2">
          ${help.map(({ key, description }) => `
            <div class="flex justify-between items-center py-2 border-b border-gray-100">
              <span class="text-gray-700">${description}</span>
              <kbd class="px-2 py-1 text-xs font-semibold text-gray-800 bg-gray-100 border border-gray-300 rounded">
                ${key}
              </kbd>
            </div>
          `).join('')}
        </div>
      </div>
    `;

    // Show in modal (assuming modal manager is available)
    if (window.rbacModals) {
      window.rbacModals.open('help-modal', {
        title: 'Keyboard Shortcuts',
        content: helpHTML
      });
    }
  }
}

// Default shortcuts configuration
export function setupDefaultShortcuts(shortcuts, handlers) {
  // Global search
  shortcuts.register('ctrl+k', () => {
    handlers.focusSearch();
  }, 'Focus search');

  shortcuts.register('ctrl+shift+k', () => {
    handlers.showCommandPalette();
  }, 'Show command palette');

  // Close modal/panel
  shortcuts.register('escape', () => {
    handlers.closeModal();
  }, 'Close modal or panel');

  // Navigation
  shortcuts.register('alt+1', () => {
    handlers.switchTab('dashboard');
  }, 'Go to Dashboard');

  shortcuts.register('alt+2', () => {
    handlers.switchTab('roles');
  }, 'Go to Roles');

  shortcuts.register('alt+3', () => {
    handlers.switchTab('users');
  }, 'Go to Users');

  shortcuts.register('alt+4', () => {
    handlers.switchTab('groups');
  }, 'Go to Groups');

  // Actions
  shortcuts.register('ctrl+n', () => {
    handlers.newItem();
  }, 'Create new item');

  shortcuts.register('ctrl+s', () => {
    handlers.save();
  }, 'Save changes');

  shortcuts.register('ctrl+r', () => {
    handlers.refresh();
  }, 'Refresh current view');

  // Selection
  shortcuts.register('ctrl+a', (e) => {
    handlers.selectAll();
  }, 'Select all');

  shortcuts.register('ctrl+d', () => {
    handlers.deselectAll();
  }, 'Deselect all');

  // Help
  shortcuts.register('shift+?', () => {
    shortcuts.showHelp();
  }, 'Show this help');
}

// Export singleton
export const keyboardShortcuts = new KeyboardShortcuts();
