/**
 * Modal Controller
 * Unified modal management with keyboard support
 */

export class ModalController {
  constructor(modalId) {
    this.modalId = modalId;
    this.modal = document.getElementById(modalId);
    this.isOpen = false;
    this.onClose = null;

    if (!this.modal) {
      console.error(`Modal not found: ${modalId}`);
      return;
    }

    this.setupEventListeners();
  }

  setupEventListeners() {
    // Close button
    const closeBtn = this.modal.querySelector('[id$="-close"]');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => this.close());
    }

    // Click outside to close
    this.modal.addEventListener('click', (e) => {
      if (e.target === this.modal) {
        this.close();
      }
    });

    // Escape key to close
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.isOpen) {
        this.close();
      }
    });
  }

  open(options = {}) {
    this.isOpen = true;
    this.modal.classList.remove('hidden');
    document.body.style.overflow = 'hidden'; // Prevent background scroll

    // Set title if provided
    if (options.title) {
      const titleEl = this.modal.querySelector('[id$="-title"]');
      if (titleEl) titleEl.textContent = options.title;
    }

    // Set content if provided
    if (options.content) {
      const contentEl = this.modal.querySelector('[id$="-content"]');
      if (contentEl) {
        if (typeof options.content === 'string') {
          contentEl.innerHTML = options.content;
        } else if (options.content instanceof HTMLElement) {
          contentEl.innerHTML = '';
          contentEl.appendChild(options.content);
        }
      }
    }

    // Store close callback
    if (options.onClose) {
      this.onClose = options.onClose;
    }

    // Focus trap
    this.trapFocus();
  }

  close() {
    this.isOpen = false;
    this.modal.classList.add('hidden');
    document.body.style.overflow = ''; // Restore scroll

    // Call close callback
    if (this.onClose) {
      this.onClose();
      this.onClose = null;
    }
  }

  setContent(content) {
    const contentEl = this.modal.querySelector('[id$="-content"]');
    if (contentEl) {
      if (typeof content === 'string') {
        contentEl.innerHTML = content;
      } else if (content instanceof HTMLElement) {
        contentEl.innerHTML = '';
        contentEl.appendChild(content);
      }
    }
  }

  setTitle(title) {
    const titleEl = this.modal.querySelector('[id$="-title"]');
    if (titleEl) titleEl.textContent = title;
  }

  showLoading(message = 'Loading...') {
    this.setContent(`
      <div class="flex flex-col items-center justify-center py-12">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
        <p class="text-gray-600">${message}</p>
      </div>
    `);
  }

  showError(message = 'An error occurred') {
    this.setContent(`
      <div class="flex flex-col items-center justify-center py-12">
        <i class="ph ph-warning-circle text-6xl text-red-500 mb-4"></i>
        <p class="text-gray-900 font-semibold mb-2">Error</p>
        <p class="text-gray-600">${message}</p>
      </div>
    `);
  }

  trapFocus() {
    const focusableElements = this.modal.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );

    if (focusableElements.length === 0) return;

    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    this.modal.addEventListener('keydown', (e) => {
      if (e.key !== 'Tab') return;

      if (e.shiftKey) {
        if (document.activeElement === firstElement) {
          e.preventDefault();
          lastElement.focus();
        }
      } else {
        if (document.activeElement === lastElement) {
          e.preventDefault();
          firstElement.focus();
        }
      }
    });

    // Focus first element
    firstElement.focus();
  }
}

/**
 * Global modal management
 */
export class ModalManager {
  constructor() {
    this.modals = new Map();
    this.stack = [];
  }

  register(modalId) {
    if (!this.modals.has(modalId)) {
      this.modals.set(modalId, new ModalController(modalId));
    }
    return this.modals.get(modalId);
  }

  open(modalId, options = {}) {
    const modal = this.register(modalId);
    modal.open(options);
    this.stack.push(modalId);
  }

  close(modalId) {
    const modal = this.modals.get(modalId);
    if (modal) {
      modal.close();
      this.stack = this.stack.filter(id => id !== modalId);
    }
  }

  closeAll() {
    this.stack.forEach(modalId => {
      const modal = this.modals.get(modalId);
      if (modal) modal.close();
    });
    this.stack = [];
  }

  getCurrent() {
    if (this.stack.length === 0) return null;
    const currentId = this.stack[this.stack.length - 1];
    return this.modals.get(currentId);
  }
}

// Export singleton instance
export const modalManager = new ModalManager();
