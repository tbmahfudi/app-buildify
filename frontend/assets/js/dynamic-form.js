/**
 * Dynamic Form Builder - Renders forms from metadata with RBAC support
 * Now uses Flex* components for consistent UI
 */
import { canViewField, canEditField } from './rbac.js';
import FlexInput from './components/flex-input.js';
import FlexTextarea from './components/flex-textarea.js';
import FlexSelect from './components/flex-select.js';
import FlexCheckbox from './components/flex-checkbox.js';

export class DynamicForm {
  constructor(container, metadata, record = null) {
    this.container = container;
    this.metadata = metadata;
    this.record = record;
    this.fields = new Map(); // Maps field name to component instance
    this.fieldComponents = new Map(); // Maps field name to Flex component instance
  }

  /**
   * Render the form
   */
  render() {
    this.container.innerHTML = '';

    const form = document.createElement('form');
    form.className = 'dynamic-form space-y-4';
    form.id = 'dynamic-form';

    this.metadata.form.fields.forEach(field => {
      const formGroup = this.createFormGroup(field);
      form.appendChild(formGroup);
    });

    this.container.appendChild(form);
    return form;
  }

  /**
   * Create form group for a field with RBAC support
   */
  createFormGroup(fieldConfig) {
    // Check if user can view this field
    if (!canViewField(fieldConfig)) {
      // If user cannot view the field, return empty div
      const hiddenDiv = document.createElement('div');
      hiddenDiv.style.display = 'none';
      return hiddenDiv;
    }

    const fieldContainer = document.createElement('div');

    // Check if user can edit this field
    const canEdit = canEditField(fieldConfig);

    // If field is marked as readonly OR user cannot edit, make it readonly
    const readonly = fieldConfig.readonly || !canEdit;

    // Build label text
    let labelText = fieldConfig.title;

    // Add lock icon if readonly due to RBAC (show in helper text instead)
    let helperText = fieldConfig.help || '';
    if (!canEdit && !fieldConfig.readonly) {
      helperText = '🔒 You do not have permission to edit this field' + (helperText ? '. ' + helperText : '');
    }

    // Create input based on type
    const inputComponent = this.createInput(fieldConfig, readonly, labelText, helperText);
    if (inputComponent) {
      fieldContainer.appendChild(inputComponent);
    }

    return fieldContainer;
  }

  /**
   * Create input element based on field type
   */
  createInput(fieldConfig, readonly, labelText, helperText) {
    const value = this.record?.data?.[fieldConfig.field] || fieldConfig.default || '';

    switch (fieldConfig.type) {
      case 'text':
      case 'email':
      case 'url':
        return this.createTextInput(fieldConfig, value, readonly, labelText, helperText);

      case 'number':
        return this.createNumberInput(fieldConfig, value, readonly, labelText, helperText);

      case 'textarea':
        return this.createTextarea(fieldConfig, value, readonly, labelText, helperText);

      case 'select':
        return this.createSelect(fieldConfig, value, readonly, labelText, helperText);

      case 'boolean':
        return this.createCheckbox(fieldConfig, value, readonly, labelText, helperText);

      case 'date':
        return this.createDateInput(fieldConfig, value, readonly, labelText, helperText);

      default:
        return this.createTextInput(fieldConfig, value, readonly, labelText, helperText);
    }
  }

  /**
   * Create text input using FlexInput
   */
  createTextInput(fieldConfig, value, readonly, labelText, helperText) {
    const container = document.createElement('div');

    const component = new FlexInput(container, {
      type: fieldConfig.type === 'email' ? 'email' :
            fieldConfig.type === 'url' ? 'url' : 'text',
      label: labelText,
      value: value || '',
      placeholder: fieldConfig.placeholder || '',
      required: fieldConfig.required || false,
      readonly: readonly,
      helperText: helperText,
      maxLength: fieldConfig.validators?.maxLength,
      showCharCount: fieldConfig.validators?.maxLength ? true : false,
      variant: 'outlined',
      size: 'md'
    });

    // Store references
    this.fields.set(fieldConfig.field, component.inputElement);
    this.fieldComponents.set(fieldConfig.field, component);

    // Add name attribute for form submission
    component.inputElement.name = fieldConfig.field;

    return container;
  }

  /**
   * Create number input using FlexInput
   */
  createNumberInput(fieldConfig, value, readonly, labelText, helperText) {
    const container = document.createElement('div');

    const component = new FlexInput(container, {
      type: 'number',
      label: labelText,
      value: value || '',
      placeholder: fieldConfig.placeholder || '',
      required: fieldConfig.required || false,
      readonly: readonly,
      helperText: helperText,
      min: fieldConfig.validators?.min,
      max: fieldConfig.validators?.max,
      step: fieldConfig.validators?.step,
      variant: 'outlined',
      size: 'md'
    });

    // Store references
    this.fields.set(fieldConfig.field, component.inputElement);
    this.fieldComponents.set(fieldConfig.field, component);

    component.inputElement.name = fieldConfig.field;

    return container;
  }

  /**
   * Create textarea using FlexTextarea
   */
  createTextarea(fieldConfig, value, readonly, labelText, helperText) {
    const container = document.createElement('div');

    const component = new FlexTextarea(container, {
      label: labelText,
      value: value || '',
      placeholder: fieldConfig.placeholder || '',
      required: fieldConfig.required || false,
      readonly: readonly,
      helperText: helperText,
      rows: fieldConfig.rows || 3,
      autoResize: true,
      maxLength: fieldConfig.validators?.maxLength,
      showCharCount: fieldConfig.validators?.maxLength ? true : false,
      variant: 'outlined',
      size: 'md'
    });

    // Store references
    this.fields.set(fieldConfig.field, component.textareaElement);
    this.fieldComponents.set(fieldConfig.field, component);

    component.textareaElement.name = fieldConfig.field;

    return container;
  }

  /**
   * Create select dropdown using FlexSelect
   */
  createSelect(fieldConfig, value, readonly, labelText, helperText) {
    const container = document.createElement('div');

    // Map options to FlexSelect format
    const options = (fieldConfig.options || []).map(opt => ({
      value: opt.value,
      label: opt.label
    }));

    const component = new FlexSelect(container, {
      label: labelText,
      value: value || '',
      options: options,
      placeholder: fieldConfig.required ? 'Select an option' : '-- Select --',
      required: fieldConfig.required || false,
      disabled: readonly,
      helperText: helperText,
      searchable: options.length > 10, // Make searchable if many options
      variant: 'outlined',
      size: 'md'
    });

    // Store references
    this.fields.set(fieldConfig.field, component.selectElement);
    this.fieldComponents.set(fieldConfig.field, component);

    component.selectElement.name = fieldConfig.field;

    return container;
  }

  /**
   * Create checkbox using FlexCheckbox
   */
  createCheckbox(fieldConfig, value, readonly, labelText, helperText) {
    const container = document.createElement('div');

    const component = new FlexCheckbox(container, {
      label: labelText,
      checked: value === true || value === 'true',
      disabled: readonly,
      helperText: helperText,
      size: 'md'
    });

    // Store references
    this.fields.set(fieldConfig.field, component.checkboxElement);
    this.fieldComponents.set(fieldConfig.field, component);

    component.checkboxElement.name = fieldConfig.field;

    return container;
  }

  /**
   * Create date input using FlexInput
   */
  createDateInput(fieldConfig, value, readonly, labelText, helperText) {
    const container = document.createElement('div');

    const component = new FlexInput(container, {
      type: 'date',
      label: labelText,
      value: value ? value.split('T')[0] : '',
      required: fieldConfig.required || false,
      readonly: readonly,
      helperText: helperText,
      variant: 'outlined',
      size: 'md'
    });

    // Store references
    this.fields.set(fieldConfig.field, component.inputElement);
    this.fieldComponents.set(fieldConfig.field, component);

    component.inputElement.name = fieldConfig.field;

    return container;
  }

  /**
   * Get form values
   */
  getValues() {
    const values = {};

    this.fields.forEach((element, field) => {
      if (element.type === 'checkbox') {
        values[field] = element.checked;
      } else if (element.type === 'number') {
        values[field] = element.value ? parseFloat(element.value) : null;
      } else {
        values[field] = element.value;
      }
    });

    return values;
  }

  /**
   * Validate form
   */
  validate() {
    let isValid = true;

    this.fieldComponents.forEach((component, field) => {
      // Use the component's validate method if available
      if (component.validate) {
        if (!component.validate()) {
          isValid = false;
        }
      } else {
        // Fallback to HTML5 validation
        const element = this.fields.get(field);
        if (element && !element.checkValidity()) {
          isValid = false;
        }
      }
    });

    return isValid;
  }

  /**
   * Set error message for a field
   */
  setFieldError(field, message) {
    const component = this.fieldComponents.get(field);
    if (component && component.setError) {
      component.setError(message);
    } else {
      // Fallback: try to set error on the element directly
      const element = this.fields.get(field);
      if (element) {
        // Create error message element if needed
        let errorEl = element.parentElement.querySelector('.text-red-600');
        if (!errorEl) {
          errorEl = document.createElement('p');
          errorEl.className = 'mt-1 text-sm text-red-600';
          element.parentElement.appendChild(errorEl);
        }
        errorEl.textContent = message;
        element.classList.add('border-red-500');
      }
    }
  }

  /**
   * Clear all errors
   */
  clearErrors() {
    this.fieldComponents.forEach((component) => {
      if (component.clearError) {
        component.clearError();
      }
    });

    // Also clear any manual error elements
    this.fields.forEach((element) => {
      element.classList.remove('border-red-500');
      const errorEl = element.parentElement.querySelector('.text-red-600');
      if (errorEl) {
        errorEl.remove();
      }
    });
  }

  /**
   * Destroy all field components
   */
  destroy() {
    this.fieldComponents.forEach((component) => {
      if (component.destroy) {
        component.destroy();
      }
    });
    this.fields.clear();
    this.fieldComponents.clear();
  }
}
