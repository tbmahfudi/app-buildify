/**
 * UIComponents - Reusable Tailwind component library
 * Pure Tailwind CSS with dark mode support
 * No localStorage - artifact-friendly
 */

export class UIComponents {
  
  /**
   * Create a button component
   * @param {object} options - Button configuration
   * @returns {HTMLElement}
   */
  static createButton(options = {}) {
    const {
      text = 'Button',
      variant = 'primary', // primary, secondary, success, danger, warning, ghost, outline
      size = 'md', // sm, md, lg, xl
      icon = null, // HTML string or element
      iconPosition = 'left', // left, right
      disabled = false,
      loading = false,
      fullWidth = false,
      className = '',
      onClick = null
    } = options;

    const button = document.createElement('button');
    button.type = 'button';

    // Size classes
    const sizeClasses = {
      sm: 'px-3 py-1.5 text-sm',
      md: 'px-4 py-2 text-base',
      lg: 'px-6 py-3 text-lg',
      xl: 'px-8 py-4 text-xl'
    };

    // Variant classes
    const variantClasses = {
      primary: 'bg-blue-600 hover:bg-blue-700 text-white border-transparent shadow-sm hover:shadow-md dark:bg-blue-500 dark:hover:bg-blue-600',
      secondary: 'bg-gray-600 hover:bg-gray-700 text-white border-transparent shadow-sm hover:shadow-md dark:bg-gray-500 dark:hover:bg-gray-600',
      success: 'bg-green-600 hover:bg-green-700 text-white border-transparent shadow-sm hover:shadow-md dark:bg-green-500 dark:hover:bg-green-600',
      danger: 'bg-red-600 hover:bg-red-700 text-white border-transparent shadow-sm hover:shadow-md dark:bg-red-500 dark:hover:bg-red-600',
      warning: 'bg-amber-600 hover:bg-amber-700 text-white border-transparent shadow-sm hover:shadow-md dark:bg-amber-500 dark:hover:bg-amber-600',
      ghost: 'bg-transparent hover:bg-gray-100 text-gray-700 border-transparent dark:hover:bg-slate-700 dark:text-gray-200',
      outline: 'bg-transparent hover:bg-gray-50 text-gray-700 border-gray-300 dark:border-slate-600 dark:text-gray-200 dark:hover:bg-slate-800'
    };

    // Base classes
    button.className = `
      inline-flex items-center justify-center gap-2
      font-medium rounded-lg border
      transition-all duration-200
      focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
      disabled:opacity-50 disabled:cursor-not-allowed
      ${sizeClasses[size]}
      ${variantClasses[variant]}
      ${fullWidth ? 'w-full' : ''}
      ${className}
    `.trim().replace(/\s+/g, ' ');

    // Loading spinner
    const spinner = `
      <svg class="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
    `;

    // Build button content
    let content = '';
    
    if (loading) {
      content = spinner;
    } else {
      if (icon && iconPosition === 'left') {
        content += typeof icon === 'string' ? icon : icon.outerHTML;
      }
      content += `<span>${text}</span>`;
      if (icon && iconPosition === 'right') {
        content += typeof icon === 'string' ? icon : icon.outerHTML;
      }
    }

    button.innerHTML = content;
    button.disabled = disabled || loading;

    if (onClick) {
      button.addEventListener('click', onClick);
    }

    return button;
  }

  /**
   * Create an input component
   * @param {object} options - Input configuration
   * @returns {HTMLElement}
   */
  static createInput(options = {}) {
    const {
      type = 'text',
      placeholder = '',
      value = '',
      label = '',
      helperText = '',
      error = '',
      icon = null,
      iconPosition = 'left',
      disabled = false,
      required = false,
      fullWidth = false,
      size = 'md', // sm, md, lg
      className = '',
      onChange = null,
      onFocus = null,
      onBlur = null
    } = options;

    const wrapper = document.createElement('div');
    wrapper.className = `${fullWidth ? 'w-full' : ''} ${className}`;

    // Size classes
    const sizeClasses = {
      sm: 'px-3 py-1.5 text-sm',
      md: 'px-4 py-2 text-base',
      lg: 'px-5 py-3 text-lg'
    };

    // Label
    if (label) {
      const labelEl = document.createElement('label');
      labelEl.className = 'block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1';
      labelEl.textContent = label + (required ? ' *' : '');
      wrapper.appendChild(labelEl);
    }

    // Input container
    const inputContainer = document.createElement('div');
    inputContainer.className = 'relative';

    // Icon
    if (icon) {
      const iconEl = document.createElement('div');
      iconEl.className = `absolute top-1/2 transform -translate-y-1/2 ${iconPosition === 'left' ? 'left-3' : 'right-3'} text-gray-400`;
      iconEl.innerHTML = icon;
      inputContainer.appendChild(iconEl);
    }

    // Input
    const input = document.createElement('input');
    input.type = type;
    input.placeholder = placeholder;
    input.value = value;
    input.disabled = disabled;
    input.required = required;

    input.className = `
      block w-full rounded-lg border
      ${error ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : 'border-gray-300 focus:border-blue-500 focus:ring-blue-500 dark:border-slate-600'}
      bg-white dark:bg-slate-800
      text-gray-900 dark:text-gray-100
      placeholder-gray-400 dark:placeholder-gray-500
      focus:outline-none focus:ring-2 focus:ring-offset-2
      disabled:bg-gray-100 disabled:cursor-not-allowed dark:disabled:bg-slate-700
      transition-colors duration-200
      ${sizeClasses[size]}
      ${icon && iconPosition === 'left' ? 'pl-10' : ''}
      ${icon && iconPosition === 'right' ? 'pr-10' : ''}
    `.trim().replace(/\s+/g, ' ');

    if (onChange) input.addEventListener('input', (e) => onChange(e.target.value, e));
    if (onFocus) input.addEventListener('focus', onFocus);
    if (onBlur) input.addEventListener('blur', onBlur);

    inputContainer.appendChild(input);
    wrapper.appendChild(inputContainer);

    // Error message
    if (error) {
      const errorEl = document.createElement('p');
      errorEl.className = 'mt-1 text-sm text-red-600 dark:text-red-400';
      errorEl.textContent = error;
      wrapper.appendChild(errorEl);
    }

    // Helper text
    if (helperText && !error) {
      const helperEl = document.createElement('p');
      helperEl.className = 'mt-1 text-sm text-gray-500 dark:text-gray-400';
      helperEl.textContent = helperText;
      wrapper.appendChild(helperEl);
    }

    // Expose input element
    wrapper.input = input;

    return wrapper;
  }

  /**
   * Create a textarea component
   * @param {object} options - Textarea configuration
   * @returns {HTMLElement}
   */
  static createTextarea(options = {}) {
    const {
      placeholder = '',
      value = '',
      label = '',
      helperText = '',
      error = '',
      disabled = false,
      required = false,
      rows = 4,
      fullWidth = false,
      className = '',
      onChange = null
    } = options;

    const wrapper = document.createElement('div');
    wrapper.className = `${fullWidth ? 'w-full' : ''} ${className}`;

    // Label
    if (label) {
      const labelEl = document.createElement('label');
      labelEl.className = 'block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1';
      labelEl.textContent = label + (required ? ' *' : '');
      wrapper.appendChild(labelEl);
    }

    // Textarea
    const textarea = document.createElement('textarea');
    textarea.placeholder = placeholder;
    textarea.value = value;
    textarea.disabled = disabled;
    textarea.required = required;
    textarea.rows = rows;

    textarea.className = `
      block w-full rounded-lg border
      ${error ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : 'border-gray-300 focus:border-blue-500 focus:ring-blue-500 dark:border-slate-600'}
      bg-white dark:bg-slate-800
      text-gray-900 dark:text-gray-100
      placeholder-gray-400 dark:placeholder-gray-500
      focus:outline-none focus:ring-2 focus:ring-offset-2
      disabled:bg-gray-100 disabled:cursor-not-allowed dark:disabled:bg-slate-700
      transition-colors duration-200
      px-4 py-2 text-base
    `.trim().replace(/\s+/g, ' ');

    if (onChange) textarea.addEventListener('input', (e) => onChange(e.target.value, e));

    wrapper.appendChild(textarea);

    // Error or helper text
    if (error) {
      const errorEl = document.createElement('p');
      errorEl.className = 'mt-1 text-sm text-red-600 dark:text-red-400';
      errorEl.textContent = error;
      wrapper.appendChild(errorEl);
    } else if (helperText) {
      const helperEl = document.createElement('p');
      helperEl.className = 'mt-1 text-sm text-gray-500 dark:text-gray-400';
      helperEl.textContent = helperText;
      wrapper.appendChild(helperEl);
    }

    wrapper.textarea = textarea;
    return wrapper;
  }

  /**
   * Create a select/dropdown component
   * @param {object} options - Select configuration
   * @returns {HTMLElement}
   */
  static createSelect(options = {}) {
    const {
      options: selectOptions = [],
      value = '',
      label = '',
      helperText = '',
      error = '',
      disabled = false,
      required = false,
      fullWidth = false,
      placeholder = 'Select an option',
      className = '',
      onChange = null
    } = options;

    const wrapper = document.createElement('div');
    wrapper.className = `${fullWidth ? 'w-full' : ''} ${className}`;

    // Label
    if (label) {
      const labelEl = document.createElement('label');
      labelEl.className = 'block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1';
      labelEl.textContent = label + (required ? ' *' : '');
      wrapper.appendChild(labelEl);
    }

    // Select
    const select = document.createElement('select');
    select.disabled = disabled;
    select.required = required;

    select.className = `
      block w-full rounded-lg border
      ${error ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : 'border-gray-300 focus:border-blue-500 focus:ring-blue-500 dark:border-slate-600'}
      bg-white dark:bg-slate-800
      text-gray-900 dark:text-gray-100
      focus:outline-none focus:ring-2 focus:ring-offset-2
      disabled:bg-gray-100 disabled:cursor-not-allowed dark:disabled:bg-slate-700
      transition-colors duration-200
      px-4 py-2 text-base
    `.trim().replace(/\s+/g, ' ');

    // Placeholder option
    if (placeholder) {
      const placeholderOption = document.createElement('option');
      placeholderOption.value = '';
      placeholderOption.textContent = placeholder;
      placeholderOption.disabled = true;
      placeholderOption.selected = value === '';
      select.appendChild(placeholderOption);
    }

    // Options
    selectOptions.forEach(opt => {
      const option = document.createElement('option');
      option.value = opt.value;
      option.textContent = opt.label || opt.value;
      option.selected = opt.value === value;
      select.appendChild(option);
    });

    if (onChange) select.addEventListener('change', (e) => onChange(e.target.value, e));

    wrapper.appendChild(select);

    // Error or helper text
    if (error) {
      const errorEl = document.createElement('p');
      errorEl.className = 'mt-1 text-sm text-red-600 dark:text-red-400';
      errorEl.textContent = error;
      wrapper.appendChild(errorEl);
    } else if (helperText) {
      const helperEl = document.createElement('p');
      helperEl.className = 'mt-1 text-sm text-gray-500 dark:text-gray-400';
      helperEl.textContent = helperText;
      wrapper.appendChild(helperEl);
    }

    wrapper.select = select;
    return wrapper;
  }

  /**
   * Create a card component
   * @param {object} options - Card configuration
   * @returns {HTMLElement}
   */
  static createCard(options = {}) {
    const {
      title = '',
      subtitle = '',
      content = '',
      footer = '',
      variant = 'default', // default, bordered, elevated
      padding = 'md', // sm, md, lg, none
      className = '',
      header = null, // Custom header element
      actions = [] // Array of button configs
    } = options;

    const card = document.createElement('div');

    // Variant classes
    const variantClasses = {
      default: 'bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700',
      bordered: 'bg-white dark:bg-slate-800 border-2 border-gray-300 dark:border-slate-600',
      elevated: 'bg-white dark:bg-slate-800 shadow-lg border border-gray-200 dark:border-slate-700'
    };

    // Padding classes
    const paddingClasses = {
      none: '',
      sm: 'p-3',
      md: 'p-6',
      lg: 'p-8'
    };

    card.className = `
      rounded-lg overflow-hidden
      ${variantClasses[variant]}
      ${className}
    `.trim().replace(/\s+/g, ' ');

    // Header
    if (header || title || subtitle) {
      const headerEl = document.createElement('div');
      headerEl.className = `border-b border-gray-200 dark:border-slate-700 ${paddingClasses[padding]}`;
      
      if (header) {
        headerEl.appendChild(typeof header === 'string' ? this._parseHTML(header) : header);
      } else {
        if (title) {
          const titleEl = document.createElement('h3');
          titleEl.className = 'text-lg font-semibold text-gray-900 dark:text-gray-100';
          titleEl.textContent = title;
          headerEl.appendChild(titleEl);
        }
        if (subtitle) {
          const subtitleEl = document.createElement('p');
          subtitleEl.className = 'mt-1 text-sm text-gray-500 dark:text-gray-400';
          subtitleEl.textContent = subtitle;
          headerEl.appendChild(subtitleEl);
        }
      }
      
      card.appendChild(headerEl);
    }

    // Content
    if (content) {
      const contentEl = document.createElement('div');
      contentEl.className = `text-gray-700 dark:text-gray-300 ${paddingClasses[padding]}`;
      contentEl.innerHTML = content;
      card.appendChild(contentEl);
    }

    // Footer
    if (footer || actions.length > 0) {
      const footerEl = document.createElement('div');
      footerEl.className = `border-t border-gray-200 dark:border-slate-700 ${paddingClasses[padding]}`;
      
      if (actions.length > 0) {
        const actionsContainer = document.createElement('div');
        actionsContainer.className = 'flex items-center gap-2 justify-end';
        
        actions.forEach(actionConfig => {
          const button = this.createButton(actionConfig);
          actionsContainer.appendChild(button);
        });
        
        footerEl.appendChild(actionsContainer);
      } else {
        footerEl.innerHTML = footer;
      }
      
      card.appendChild(footerEl);
    }

    return card;
  }

  /**
   * Create a badge component
   * @param {object} options - Badge configuration
   * @returns {HTMLElement}
   */
  static createBadge(options = {}) {
    const {
      text = '',
      variant = 'default', // default, primary, success, warning, danger, info
      size = 'md', // sm, md, lg
      rounded = true,
      className = ''
    } = options;

    const badge = document.createElement('span');

    // Size classes
    const sizeClasses = {
      sm: 'px-2 py-0.5 text-xs',
      md: 'px-2.5 py-1 text-sm',
      lg: 'px-3 py-1.5 text-base'
    };

    // Variant classes
    const variantClasses = {
      default: 'bg-gray-100 text-gray-800 dark:bg-slate-700 dark:text-gray-200',
      primary: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
      success: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
      warning: 'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200',
      danger: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
      info: 'bg-sky-100 text-sky-800 dark:bg-sky-900 dark:text-sky-200'
    };

    badge.className = `
      inline-flex items-center font-medium
      ${rounded ? 'rounded-full' : 'rounded'}
      ${sizeClasses[size]}
      ${variantClasses[variant]}
      ${className}
    `.trim().replace(/\s+/g, ' ');

    badge.textContent = text;

    return badge;
  }

  /**
   * Create an alert component
   * @param {object} options - Alert configuration
   * @returns {HTMLElement}
   */
  static createAlert(options = {}) {
    const {
      title = '',
      message = '',
      variant = 'info', // info, success, warning, danger
      dismissible = false,
      icon = true,
      className = '',
      onDismiss = null
    } = options;

    const alert = document.createElement('div');

    // Variant classes and icons
    const variants = {
      info: {
        classes: 'bg-blue-50 border-blue-200 text-blue-800 dark:bg-blue-900/20 dark:border-blue-800 dark:text-blue-200',
        icon: '<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/></svg>'
      },
      success: {
        classes: 'bg-green-50 border-green-200 text-green-800 dark:bg-green-900/20 dark:border-green-800 dark:text-green-200',
        icon: '<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/></svg>'
      },
      warning: {
        classes: 'bg-amber-50 border-amber-200 text-amber-800 dark:bg-amber-900/20 dark:border-amber-800 dark:text-amber-200',
        icon: '<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/></svg>'
      },
      danger: {
        classes: 'bg-red-50 border-red-200 text-red-800 dark:bg-red-900/20 dark:border-red-800 dark:text-red-200',
        icon: '<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/></svg>'
      }
    };

    const variantConfig = variants[variant];

    alert.className = `
      rounded-lg border p-4
      ${variantConfig.classes}
      ${className}
    `.trim().replace(/\s+/g, ' ');

    const contentWrapper = document.createElement('div');
    contentWrapper.className = 'flex items-start';

    // Icon
    if (icon) {
      const iconEl = document.createElement('div');
      iconEl.className = 'flex-shrink-0';
      iconEl.innerHTML = variantConfig.icon;
      contentWrapper.appendChild(iconEl);
    }

    // Text content
    const textWrapper = document.createElement('div');
    textWrapper.className = `${icon ? 'ml-3' : ''} flex-1`;

    if (title) {
      const titleEl = document.createElement('h3');
      titleEl.className = 'font-medium';
      titleEl.textContent = title;
      textWrapper.appendChild(titleEl);
    }

    if (message) {
      const messageEl = document.createElement('p');
      messageEl.className = `${title ? 'mt-1' : ''} text-sm`;
      messageEl.textContent = message;
      textWrapper.appendChild(messageEl);
    }

    contentWrapper.appendChild(textWrapper);

    // Dismiss button
    if (dismissible) {
      const dismissBtn = document.createElement('button');
      dismissBtn.className = 'ml-3 flex-shrink-0 inline-flex hover:opacity-75 transition-opacity';
      dismissBtn.innerHTML = '<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/></svg>';
      
      dismissBtn.addEventListener('click', () => {
        alert.style.opacity = '0';
        alert.style.transition = 'opacity 200ms';
        setTimeout(() => {
          alert.remove();
          if (onDismiss) onDismiss();
        }, 200);
      });

      contentWrapper.appendChild(dismissBtn);
    }

    alert.appendChild(contentWrapper);

    return alert;
  }

  /**
   * Helper to parse HTML strings
   * @private
   */
  static _parseHTML(html) {
    const temp = document.createElement('div');
    temp.innerHTML = html;
    return temp.firstChild;
  }
}

export default UIComponents;