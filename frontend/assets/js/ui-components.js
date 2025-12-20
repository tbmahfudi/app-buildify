/**
 * UIComponents - Reusable component library
 * Wrapper around Flex* components for backward compatibility
 * Pure Tailwind CSS with dark mode support
 */

import FlexButton from './components/flex-button.js';
import FlexInput from './components/flex-input.js';
import FlexTextarea from './components/flex-textarea.js';
import FlexSelect from './components/flex-select.js';
import FlexCard from './components/flex-card.js';
import FlexBadge from './components/flex-badge.js';
import FlexAlert from './components/flex-alert.js';

export class UIComponents {

  /**
   * Create a button component using FlexButton
   * @param {object} options - Button configuration
   * @returns {HTMLElement}
   */
  static createButton(options = {}) {
    const {
      text = 'Button',
      variant = 'primary',
      size = 'md',
      icon = null,
      iconPosition = 'left',
      disabled = false,
      loading = false,
      fullWidth = false,
      className = '',
      onClick = null
    } = options;

    // Create container for FlexButton
    const container = document.createElement('div');
    container.style.display = 'inline-block';

    // Map className to classes array
    const classes = className ? [className] : [];

    // Create FlexButton instance
    const flexButton = new FlexButton(container, {
      text,
      variant,
      size,
      icon,
      iconPosition,
      disabled,
      loading,
      fullWidth,
      classes,
      onClick
    });

    // Return the button element itself for backward compatibility
    return flexButton.getElement();
  }

  /**
   * Create an input component using FlexInput
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
      size = 'md',
      className = '',
      onChange = null,
      onFocus = null,
      onBlur = null
    } = options;

    // Create container
    const container = document.createElement('div');
    if (fullWidth) container.className = 'w-full';

    const classes = className ? [className] : [];

    // Map icon position to prefix/suffix
    const prefixIcon = icon && iconPosition === 'left' ? icon : null;
    const suffixIcon = icon && iconPosition === 'right' ? icon : null;

    // Create FlexInput instance
    const flexInput = new FlexInput(container, {
      type,
      placeholder,
      value,
      label,
      helperText,
      errorMessage: error,
      prefixIcon,
      suffixIcon,
      disabled,
      required,
      size,
      variant: 'outlined',
      classes,
      onChange,
      onFocus,
      onBlur
    });

    // Expose input element for backward compatibility
    container.input = flexInput.inputElement;

    return container;
  }

  /**
   * Create a textarea component using FlexTextarea
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

    const container = document.createElement('div');
    if (fullWidth) container.className = 'w-full';

    const classes = className ? [className] : [];

    // Create FlexTextarea instance
    const flexTextarea = new FlexTextarea(container, {
      placeholder,
      value,
      label,
      helperText,
      errorMessage: error,
      disabled,
      required,
      rows,
      variant: 'outlined',
      classes,
      onChange
    });

    // Expose textarea element for backward compatibility
    container.textarea = flexTextarea.textareaElement;

    return container;
  }

  /**
   * Create a select/dropdown component using FlexSelect
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

    const container = document.createElement('div');
    if (fullWidth) container.className = 'w-full';

    const classes = className ? [className] : [];

    // Create FlexSelect instance
    const flexSelect = new FlexSelect(container, {
      label,
      placeholder,
      value,
      options: selectOptions,
      helperText,
      errorMessage: error,
      disabled,
      required,
      variant: 'outlined',
      searchable: false, // Basic select, not searchable
      classes,
      onChange
    });

    // Expose select element for backward compatibility
    container.select = flexSelect.selectElement;

    return container;
  }

  /**
   * Create a card component using FlexCard
   * @param {object} options - Card configuration
   * @returns {HTMLElement}
   */
  static createCard(options = {}) {
    const {
      title = '',
      subtitle = '',
      content = '',
      footer = '',
      variant = 'default',
      padding = 'md',
      className = '',
      header = null,
      actions = []
    } = options;

    const container = document.createElement('div');

    const classes = className ? [className] : [];

    // Map variant
    const variantMap = {
      default: 'default',
      bordered: 'bordered',
      elevated: 'shadowed'
    };

    // Map actions to button configs
    const footerActions = actions.map(actionConfig => ({
      label: actionConfig.text || 'Action',
      icon: actionConfig.icon,
      onClick: actionConfig.onClick,
      variant: actionConfig.variant || 'primary'
    }));

    // Create FlexCard instance
    new FlexCard(container, {
      title,
      subtitle,
      content,
      footer: footer || null,
      footerActions: footerActions.length > 0 ? footerActions : [],
      variant: variantMap[variant] || 'default',
      size: padding === 'sm' ? 'sm' : padding === 'lg' ? 'lg' : 'md',
      classes
    });

    return container.firstElementChild;
  }

  /**
   * Create a badge component using FlexBadge
   * @param {object} options - Badge configuration
   * @returns {HTMLElement}
   */
  static createBadge(options = {}) {
    const {
      text = '',
      variant = 'default',
      size = 'md',
      rounded = true,
      className = ''
    } = options;

    const container = document.createElement('span');
    const classes = className ? [className] : [];

    // Map variant
    const variantMap = {
      default: 'secondary',
      primary: 'primary',
      success: 'success',
      warning: 'warning',
      danger: 'danger',
      info: 'info'
    };

    // Create FlexBadge instance
    new FlexBadge(container, {
      text,
      variant: variantMap[variant] || 'primary',
      size,
      rounded: rounded ? 'full' : 'md',
      classes
    });

    return container.firstElementChild;
  }

  /**
   * Create an alert component using FlexAlert
   * @param {object} options - Alert configuration
   * @returns {HTMLElement}
   */
  static createAlert(options = {}) {
    const {
      title = '',
      message = '',
      variant = 'info',
      dismissible = false,
      icon = true,
      className = '',
      onDismiss = null
    } = options;

    const container = document.createElement('div');
    const classes = className ? [className] : [];

    // Create FlexAlert instance
    new FlexAlert(container, {
      title,
      message,
      variant,
      dismissible,
      icon: icon ? null : '', // null = use default, '' = no icon
      classes,
      onDismiss
    });

    return container.firstElementChild;
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
