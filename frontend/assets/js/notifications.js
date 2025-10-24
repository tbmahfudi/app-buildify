/**
 * Advanced Notification System
 * Supports: Toast, Alert, Confirm, Prompt, Progress notifications
 * Features: Queue management, positioning, stacking, animations
 */

class NotificationSystem {
  constructor() {
    this.notifications = new Map();
    this.queue = [];
    this.maxVisible = 5;
    this.defaultDuration = 5000;
    this.positions = {
      'top-right': 'top-4 right-4',
      'top-left': 'top-4 left-4',
      'top-center': 'top-4 left-1/2 -translate-x-1/2',
      'bottom-right': 'bottom-4 right-4',
      'bottom-left': 'bottom-4 left-4',
      'bottom-center': 'bottom-4 left-1/2 -translate-x-1/2'
    };
    this.defaultPosition = 'top-right';
    
    this.init();
  }

  /**
   * Initialize notification containers
   */
  init() {
    // Create containers for each position
    Object.keys(this.positions).forEach(position => {
      if (!document.getElementById(`notification-container-${position}`)) {
        const container = document.createElement('div');
        container.id = `notification-container-${position}`;
        container.className = `fixed ${this.positions[position]} z-50 pointer-events-none`;
        container.style.maxWidth = '420px';
        document.body.appendChild(container);
      }
    });

    // Create modal container for dialogs
    if (!document.getElementById('notification-modal-container')) {
      const modalContainer = document.createElement('div');
      modalContainer.id = 'notification-modal-container';
      modalContainer.className = 'fixed inset-0 z-[60]';
      modalContainer.style.display = 'none';
      document.body.appendChild(modalContainer);
    }
  }

  /**
   * Show toast notification
   * @param {string} message - Notification message
   * @param {object} options - Configuration options
   */
  toast(message, options = {}) {
    const config = {
      type: options.type || 'info',
      duration: options.duration !== undefined ? options.duration : this.defaultDuration,
      position: options.position || this.defaultPosition,
      title: options.title || null,
      closable: options.closable !== false,
      icon: options.icon || null,
      actions: options.actions || [],
      onClick: options.onClick || null,
      onClose: options.onClose || null,
      progress: options.progress || false
    };

    const id = this.generateId();
    const notification = this.createToast(id, message, config);
    
    this.show(id, notification, config);
    
    return id;
  }

  /**
   * Create toast element
   */
  createToast(id, message, config) {
    const toast = document.createElement('div');
    toast.id = `notification-${id}`;
    toast.className = `pointer-events-auto mb-3 transform transition-all duration-300 ease-out opacity-0 translate-x-full`;
    
    const colors = this.getColors(config.type);
    
    toast.innerHTML = `
      <div class="${colors.bg} ${colors.border} border-l-4 rounded-lg shadow-xl overflow-hidden">
        ${config.progress ? `<div class="h-1 bg-gradient-to-r ${colors.progressBg} transition-all duration-300" style="width: 100%"></div>` : ''}
        
        <div class="p-4">
          <div class="flex items-start gap-3">
            ${config.icon !== false ? `
              <div class="flex-shrink-0 mt-0.5">
                ${config.icon || this.getIcon(config.type, colors.text)}
              </div>
            ` : ''}
            
            <div class="flex-1 min-w-0">
              ${config.title ? `
                <h4 class="text-sm font-semibold ${colors.title} mb-1">
                  ${this.escapeHtml(config.title)}
                </h4>
              ` : ''}
              
              <p class="text-sm ${colors.text}">
                ${this.escapeHtml(message)}
              </p>
              
              ${config.actions.length > 0 ? `
                <div class="flex gap-2 mt-3">
                  ${config.actions.map((action, index) => `
                    <button 
                      class="text-xs font-medium px-3 py-1.5 rounded ${action.primary ? colors.buttonPrimary : colors.buttonSecondary} transition"
                      data-action-index="${index}">
                      ${this.escapeHtml(action.label)}
                    </button>
                  `).join('')}
                </div>
              ` : ''}
            </div>
            
            ${config.closable ? `
              <button class="flex-shrink-0 text-gray-400 hover:text-gray-600 transition" data-close>
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
              </button>
            ` : ''}
          </div>
        </div>
      </div>
    `;

    // Attach event listeners
    this.attachToastEvents(toast, id, config);
    
    return toast;
  }

  /**
   * Attach event listeners to toast
   */
  attachToastEvents(toast, id, config) {
    // Close button
    const closeBtn = toast.querySelector('[data-close]');
    if (closeBtn) {
      closeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        this.close(id);
      });
    }

    // Action buttons
    const actionButtons = toast.querySelectorAll('[data-action-index]');
    actionButtons.forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const index = parseInt(btn.dataset.actionIndex);
        const action = config.actions[index];
        
        if (action.onClick) {
          action.onClick();
        }
        
        if (action.closeOnClick !== false) {
          this.close(id);
        }
      });
    });

    // Click handler
    if (config.onClick) {
      toast.style.cursor = 'pointer';
      toast.addEventListener('click', () => {
        config.onClick();
      });
    }
  }

  /**
   * Show notification
   */
  show(id, notification, config) {
    const container = document.getElementById(`notification-container-${config.position}`);
    
    // Check if max visible reached
    const visibleCount = container.children.length;
    if (visibleCount >= this.maxVisible) {
      this.queue.push({ id, notification, config });
      return;
    }

    // Add to container
    container.appendChild(notification);
    
    // Store notification data
    this.notifications.set(id, {
      element: notification,
      config,
      timeout: null
    });

    // Trigger animation
    requestAnimationFrame(() => {
      notification.classList.remove('opacity-0', 'translate-x-full');
      notification.classList.add('opacity-100', 'translate-x-0');
    });

    // Auto close
    if (config.duration > 0) {
      this.startAutoClose(id, config.duration);
    }

    // Update progress bar if enabled
    if (config.progress && config.duration > 0) {
      this.animateProgress(id, config.duration);
    }
  }

  /**
   * Start auto-close timer
   */
  startAutoClose(id, duration) {
    const data = this.notifications.get(id);
    if (!data) return;

    data.timeout = setTimeout(() => {
      this.close(id);
    }, duration);
  }

  /**
   * Animate progress bar
   */
  animateProgress(id, duration) {
    const data = this.notifications.get(id);
    if (!data) return;

    const progressBar = data.element.querySelector('[class*="h-1"]');
    if (!progressBar) return;

    let start = null;
    
    const animate = (timestamp) => {
      if (!start) start = timestamp;
      const elapsed = timestamp - start;
      const progress = Math.max(0, 100 - (elapsed / duration) * 100);
      
      progressBar.style.width = `${progress}%`;
      
      if (elapsed < duration && this.notifications.has(id)) {
        requestAnimationFrame(animate);
      }
    };
    
    requestAnimationFrame(animate);
  }

  /**
   * Close notification
   */
  close(id) {
    const data = this.notifications.get(id);
    if (!data) return;

    // Clear timeout
    if (data.timeout) {
      clearTimeout(data.timeout);
    }

    // Animate out
    data.element.classList.add('opacity-0', 'translate-x-full');
    
    setTimeout(() => {
      // Remove element
      if (data.element.parentNode) {
        data.element.parentNode.removeChild(data.element);
      }
      
      // Remove from map
      this.notifications.delete(id);
      
      // Call onClose callback
      if (data.config.onClose) {
        data.config.onClose();
      }
      
      // Show next in queue
      this.showNextInQueue(data.config.position);
    }, 300);
  }

  /**
   * Show next notification in queue
   */
  showNextInQueue(position) {
    const nextIndex = this.queue.findIndex(item => item.config.position === position);
    
    if (nextIndex !== -1) {
      const next = this.queue.splice(nextIndex, 1)[0];
      this.show(next.id, next.notification, next.config);
    }
  }

  /**
   * Close all notifications
   */
  closeAll(position = null) {
    const ids = Array.from(this.notifications.keys());
    
    ids.forEach(id => {
      const data = this.notifications.get(id);
      if (!position || data.config.position === position) {
        this.close(id);
      }
    });

    // Clear queue
    if (position) {
      this.queue = this.queue.filter(item => item.config.position !== position);
    } else {
      this.queue = [];
    }
  }

  /**
   * Success notification
   */
  success(message, options = {}) {
    return this.toast(message, { ...options, type: 'success' });
  }

  /**
   * Error notification
   */
  error(message, options = {}) {
    return this.toast(message, { ...options, type: 'error', duration: options.duration || 7000 });
  }

  /**
   * Warning notification
   */
  warning(message, options = {}) {
    return this.toast(message, { ...options, type: 'warning' });
  }

  /**
   * Info notification
   */
  info(message, options = {}) {
    return this.toast(message, { ...options, type: 'info' });
  }

  /**
   * Loading notification
   */
  loading(message, options = {}) {
    return this.toast(message, {
      ...options,
      type: 'loading',
      duration: 0,
      closable: false,
      icon: `
        <svg class="animate-spin h-5 w-5 text-blue-600" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
      `
    });
  }

  /**
   * Update notification
   */
  update(id, message, options = {}) {
    const data = this.notifications.get(id);
    if (!data) return;

    const messageEl = data.element.querySelector('p');
    if (messageEl) {
      messageEl.textContent = message;
    }

    if (options.type) {
      const colors = this.getColors(options.type);
      const container = data.element.querySelector('[class*="border-l-4"]');
      
      // Update colors (simplified - in real implementation would need more logic)
      container.className = container.className
        .replace(/bg-\w+-50/g, colors.bg.match(/bg-\w+-50/)[0])
        .replace(/border-\w+-500/g, colors.border.match(/border-\w+-500/)[0]);
    }

    if (options.duration !== undefined) {
      if (data.timeout) clearTimeout(data.timeout);
      
      if (options.duration > 0) {
        this.startAutoClose(id, options.duration);
      }
    }
  }

  /**
   * Confirm dialog
   */
  async confirm(message, options = {}) {
    return new Promise((resolve) => {
      const config = {
        title: options.title || 'Confirm',
        confirmText: options.confirmText || 'Confirm',
        cancelText: options.cancelText || 'Cancel',
        type: options.type || 'warning',
        icon: options.icon || null
      };

      const id = this.generateId();
      const dialog = this.createDialog(id, message, config, resolve);
      
      this.showModal(dialog);
    });
  }

  /**
   * Alert dialog
   */
  async alert(message, options = {}) {
    return new Promise((resolve) => {
      const config = {
        title: options.title || 'Alert',
        confirmText: options.confirmText || 'OK',
        type: options.type || 'info',
        icon: options.icon || null
      };

      const id = this.generateId();
      const dialog = this.createDialog(id, message, config, resolve, true);
      
      this.showModal(dialog);
    });
  }

  /**
   * Prompt dialog
   */
  async prompt(message, options = {}) {
    return new Promise((resolve) => {
      const config = {
        title: options.title || 'Input Required',
        confirmText: options.confirmText || 'Submit',
        cancelText: options.cancelText || 'Cancel',
        placeholder: options.placeholder || '',
        defaultValue: options.defaultValue || '',
        inputType: options.inputType || 'text',
        required: options.required !== false
      };

      const id = this.generateId();
      const dialog = this.createPromptDialog(id, message, config, resolve);
      
      this.showModal(dialog);
    });
  }

  /**
   * Create dialog
   */
  createDialog(id, message, config, resolve, alertMode = false) {
    const colors = this.getColors(config.type);
    
    const dialog = document.createElement('div');
    dialog.id = `dialog-${id}`;
    dialog.innerHTML = `
      <div class="fixed inset-0 bg-black bg-opacity-50 transition-opacity" data-backdrop></div>
      <div class="fixed inset-0 flex items-center justify-center p-4">
        <div class="bg-white rounded-xl shadow-2xl max-w-md w-full transform transition-all scale-95 opacity-0" data-dialog>
          <div class="p-6">
            <div class="flex items-start gap-4">
              ${config.icon !== false ? `
                <div class="flex-shrink-0">
                  ${config.icon || this.getIcon(config.type, colors.text, 'w-6 h-6')}
                </div>
              ` : ''}
              
              <div class="flex-1">
                <h3 class="text-lg font-semibold text-gray-900 mb-2">
                  ${this.escapeHtml(config.title)}
                </h3>
                <p class="text-sm text-gray-600">
                  ${this.escapeHtml(message)}
                </p>
              </div>
            </div>
          </div>
          
          <div class="flex gap-3 px-6 pb-6 ${alertMode ? 'justify-end' : 'justify-between'}">
            ${!alertMode ? `
              <button 
                class="flex-1 px-4 py-2.5 border border-gray-300 rounded-lg hover:bg-gray-50 transition font-medium"
                data-cancel>
                ${this.escapeHtml(config.cancelText)}
              </button>
            ` : ''}
            <button 
              class="flex-1 px-4 py-2.5 ${colors.button} text-white rounded-lg hover:opacity-90 transition font-medium"
              data-confirm>
              ${this.escapeHtml(config.confirmText)}
            </button>
          </div>
        </div>
      </div>
    `;

    // Event listeners
    const backdrop = dialog.querySelector('[data-backdrop]');
    const cancelBtn = dialog.querySelector('[data-cancel]');
    const confirmBtn = dialog.querySelector('[data-confirm]');
    const dialogEl = dialog.querySelector('[data-dialog]');

    const close = (result) => {
      dialogEl.classList.add('scale-95', 'opacity-0');
      backdrop.classList.add('opacity-0');
      
      setTimeout(() => {
        this.hideModal();
        resolve(result);
      }, 200);
    };

    if (!alertMode) {
      backdrop.addEventListener('click', () => close(false));
      if (cancelBtn) {
        cancelBtn.addEventListener('click', () => close(false));
      }
    }
    
    confirmBtn.addEventListener('click', () => close(true));

    // Animate in
    setTimeout(() => {
      dialogEl.classList.remove('scale-95', 'opacity-0');
      dialogEl.classList.add('scale-100', 'opacity-100');
    }, 10);

    return dialog;
  }

  /**
   * Create prompt dialog
   */
  createPromptDialog(id, message, config, resolve) {
    const dialog = document.createElement('div');
    dialog.id = `dialog-${id}`;
    dialog.innerHTML = `
      <div class="fixed inset-0 bg-black bg-opacity-50 transition-opacity" data-backdrop></div>
      <div class="fixed inset-0 flex items-center justify-center p-4">
        <div class="bg-white rounded-xl shadow-2xl max-w-md w-full transform transition-all scale-95 opacity-0" data-dialog>
          <form data-form>
            <div class="p-6">
              <h3 class="text-lg font-semibold text-gray-900 mb-2">
                ${this.escapeHtml(config.title)}
              </h3>
              <p class="text-sm text-gray-600 mb-4">
                ${this.escapeHtml(message)}
              </p>
              
              <input 
                type="${config.inputType}"
                class="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="${this.escapeHtml(config.placeholder)}"
                value="${this.escapeHtml(config.defaultValue)}"
                ${config.required ? 'required' : ''}
                data-input
                autofocus>
            </div>
            
            <div class="flex gap-3 px-6 pb-6">
              <button 
                type="button"
                class="flex-1 px-4 py-2.5 border border-gray-300 rounded-lg hover:bg-gray-50 transition font-medium"
                data-cancel>
                ${this.escapeHtml(config.cancelText)}
              </button>
              <button 
                type="submit"
                class="flex-1 px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium">
                ${this.escapeHtml(config.confirmText)}
              </button>
            </div>
          </form>
        </div>
      </div>
    `;

    const backdrop = dialog.querySelector('[data-backdrop]');
    const cancelBtn = dialog.querySelector('[data-cancel]');
    const form = dialog.querySelector('[data-form]');
    const input = dialog.querySelector('[data-input]');
    const dialogEl = dialog.querySelector('[data-dialog]');

    const close = (result) => {
      dialogEl.classList.add('scale-95', 'opacity-0');
      backdrop.classList.add('opacity-0');
      
      setTimeout(() => {
        this.hideModal();
        resolve(result);
      }, 200);
    };

    backdrop.addEventListener('click', () => close(null));
    cancelBtn.addEventListener('click', () => close(null));
    
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      close(input.value);
    });

    // Animate in
    setTimeout(() => {
      dialogEl.classList.remove('scale-95', 'opacity-0');
      dialogEl.classList.add('scale-100', 'opacity-100');
    }, 10);

    return dialog;
  }

  /**
   * Show modal
   */
  showModal(dialog) {
    const container = document.getElementById('notification-modal-container');
    container.innerHTML = '';
    container.appendChild(dialog);
    container.style.display = 'block';
  }

  /**
   * Hide modal
   */
  hideModal() {
    const container = document.getElementById('notification-modal-container');
    container.style.display = 'none';
    container.innerHTML = '';
  }

  /**
   * Get colors for notification type
   */
  getColors(type) {
    const colors = {
      success: {
        bg: 'bg-green-50',
        border: 'border-green-500',
        text: 'text-green-800',
        title: 'text-green-900',
        buttonPrimary: 'bg-green-600 hover:bg-green-700 text-white',
        buttonSecondary: 'bg-green-100 hover:bg-green-200 text-green-700',
        progressBg: 'from-green-400 to-green-600',
        button: 'bg-green-600'
      },
      error: {
        bg: 'bg-red-50',
        border: 'border-red-500',
        text: 'text-red-800',
        title: 'text-red-900',
        buttonPrimary: 'bg-red-600 hover:bg-red-700 text-white',
        buttonSecondary: 'bg-red-100 hover:bg-red-200 text-red-700',
        progressBg: 'from-red-400 to-red-600',
        button: 'bg-red-600'
      },
      warning: {
        bg: 'bg-yellow-50',
        border: 'border-yellow-500',
        text: 'text-yellow-800',
        title: 'text-yellow-900',
        buttonPrimary: 'bg-yellow-600 hover:bg-yellow-700 text-white',
        buttonSecondary: 'bg-yellow-100 hover:bg-yellow-200 text-yellow-700',
        progressBg: 'from-yellow-400 to-yellow-600',
        button: 'bg-yellow-600'
      },
      info: {
        bg: 'bg-blue-50',
        border: 'border-blue-500',
        text: 'text-blue-800',
        title: 'text-blue-900',
        buttonPrimary: 'bg-blue-600 hover:bg-blue-700 text-white',
        buttonSecondary: 'bg-blue-100 hover:bg-blue-200 text-blue-700',
        progressBg: 'from-blue-400 to-blue-600',
        button: 'bg-blue-600'
      },
      loading: {
        bg: 'bg-gray-50',
        border: 'border-gray-400',
        text: 'text-gray-800',
        title: 'text-gray-900',
        buttonPrimary: 'bg-gray-600 hover:bg-gray-700 text-white',
        buttonSecondary: 'bg-gray-100 hover:bg-gray-200 text-gray-700',
        progressBg: 'from-gray-400 to-gray-600',
        button: 'bg-gray-600'
      }
    };

    return colors[type] || colors.info;
  }

  /**
   * Get icon for notification type
   */
  getIcon(type, colorClass, sizeClass = 'w-5 h-5') {
    const icons = {
      success: `<svg class="${sizeClass} ${colorClass}" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path></svg>`,
      error: `<svg class="${sizeClass} ${colorClass}" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path></svg>`,
      warning: `<svg class="${sizeClass} ${colorClass}" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path></svg>`,
      info: `<svg class="${sizeClass} ${colorClass}" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"></path></svg>`
    };

    return icons[type] || icons.info;
  }

  /**
   * Escape HTML
   */
  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  /**
   * Generate unique ID
   */
  generateId() {
    return `notification-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }
}

// Create singleton instance
const notifications = new NotificationSystem();

// Export for use
export default notifications;
export { notifications };