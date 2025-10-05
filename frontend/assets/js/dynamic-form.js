/**
 * Dynamic Form Builder - Renders forms from metadata
 */
export class DynamicForm {
  constructor(container, metadata, record = null) {
    this.container = container;
    this.metadata = metadata;
    this.record = record;
    this.fields = new Map();
  }

  /**
   * Render the form
   */
  render() {
    this.container.innerHTML = '';
    
    const form = document.createElement('form');
    form.className = 'dynamic-form';
    form.id = 'dynamic-form';

    this.metadata.form.fields.forEach(field => {
      const formGroup = this.createFormGroup(field);
      form.appendChild(formGroup);
    });

    this.container.appendChild(form);
    return form;
  }

  /**
   * Create form group for a field
   */
  createFormGroup(fieldConfig) {
    const div = document.createElement('div');
    div.className = 'mb-3';

    // Label
    const label = document.createElement('label');
    label.className = 'form-label';
    label.textContent = fieldConfig.title;
    if (fieldConfig.required) {
      label.innerHTML += ' <span class="text-danger">*</span>';
    }
    div.appendChild(label);

    // Input
    const input = this.createInput(fieldConfig);
    div.appendChild(input);

    // Store reference
    this.fields.set(fieldConfig.field, input);

    // Help text
    if (fieldConfig.help) {
      const help = document.createElement('small');
      help.className = 'form-text text-muted';
      help.textContent = fieldConfig.help;
      div.appendChild(help);
    }

    // Validation message
    const invalid = document.createElement('div');
    invalid.className = 'invalid-feedback';
    div.appendChild(invalid);

    return div;
  }

  /**
   * Create input element based on field type
   */
  createInput(fieldConfig) {
    const value = this.record?.data?.[fieldConfig.field] || fieldConfig.default || '';

    switch (fieldConfig.type) {
      case 'text':
      case 'email':
      case 'url':
        return this.createTextInput(fieldConfig, value);
      
      case 'number':
        return this.createNumberInput(fieldConfig, value);
      
      case 'textarea':
        return this.createTextarea(fieldConfig, value);
      
      case 'select':
        return this.createSelect(fieldConfig, value);
      
      case 'boolean':
        return this.createCheckbox(fieldConfig, value);
      
      case 'date':
        return this.createDateInput(fieldConfig, value);
      
      default:
        return this.createTextInput(fieldConfig, value);
    }
  }

  /**
   * Create text input
   */
  createTextInput(fieldConfig, value) {
    const input = document.createElement('input');
    input.type = fieldConfig.type === 'email' ? 'email' : 
                 fieldConfig.type === 'url' ? 'url' : 'text';
    input.className = 'form-control';
    input.name = fieldConfig.field;
    input.value = value;
    input.required = fieldConfig.required || false;
    input.readOnly = fieldConfig.readonly || false;

    if (fieldConfig.validators?.maxLength) {
      input.maxLength = fieldConfig.validators.maxLength;
    }

    return input;
  }

  /**
   * Create number input
   */
  createNumberInput(fieldConfig, value) {
    const input = document.createElement('input');
    input.type = 'number';
    input.className = 'form-control';
    input.name = fieldConfig.field;
    input.value = value;
    input.required = fieldConfig.required || false;
    input.readOnly = fieldConfig.readonly || false;

    if (fieldConfig.validators?.min !== undefined) {
      input.min = fieldConfig.validators.min;
    }
    if (fieldConfig.validators?.max !== undefined) {
      input.max = fieldConfig.validators.max;
    }
    if (fieldConfig.validators?.step) {
      input.step = fieldConfig.validators.step;
    }

    return input;
  }

  /**
   * Create textarea
   */
  createTextarea(fieldConfig, value) {
    const textarea = document.createElement('textarea');
    textarea.className = 'form-control';
    textarea.name = fieldConfig.field;
    textarea.value = value;
    textarea.required = fieldConfig.required || false;
    textarea.readOnly = fieldConfig.readonly || false;
    textarea.rows = fieldConfig.rows || 3;

    return textarea;
  }

  /**
   * Create select dropdown
   */
  createSelect(fieldConfig, value) {
    const select = document.createElement('select');
    select.className = 'form-select';
    select.name = fieldConfig.field;
    select.required = fieldConfig.required || false;
    select.disabled = fieldConfig.readonly || false;

    // Empty option
    if (!fieldConfig.required) {
      const option = document.createElement('option');
      option.value = '';
      option.textContent = '-- Select --';
      select.appendChild(option);
    }

    // Options
    if (fieldConfig.options) {
      fieldConfig.options.forEach(opt => {
        const option = document.createElement('option');
        option.value = opt.value;
        option.textContent = opt.label;
        option.selected = opt.value === value;
        select.appendChild(option);
      });
    }

    return select;
  }

  /**
   * Create checkbox
   */
  createCheckbox(fieldConfig, value) {
    const div = document.createElement('div');
    div.className = 'form-check';

    const input = document.createElement('input');
    input.type = 'checkbox';
    input.className = 'form-check-input';
    input.name = fieldConfig.field;
    input.checked = value === true || value === 'true';
    input.disabled = fieldConfig.readonly || false;

    const label = document.createElement('label');
    label.className = 'form-check-label';
    label.textContent = fieldConfig.title;

    div.appendChild(input);
    div.appendChild(label);

    return div;
  }

  /**
   * Create date input
   */
  createDateInput(fieldConfig, value) {
    const input = document.createElement('input');
    input.type = 'date';
    input.className = 'form-control';
    input.name = fieldConfig.field;
    input.value = value ? value.split('T')[0] : '';
    input.required = fieldConfig.required || false;
    input.readOnly = fieldConfig.readonly || false;

    return input;
  }

  /**
   * Get form values
   */
  getValues() {
    const values = {};
    
    this.fields.forEach((input, field) => {
      if (input.type === 'checkbox') {
        values[field] = input.checked;
      } else if (input.type === 'number') {
        values[field] = input.value ? parseFloat(input.value) : null;
      } else {
        values[field] = input.value;
      }
    });

    return values;
  }

  /**
   * Validate form
   */
  validate() {
    const form = document.getElementById('dynamic-form');
    if (!form.checkValidity()) {
      form.classList.add('was-validated');
      return false;
    }
    return true;
  }

  /**
   * Set error message for a field
   */
  setFieldError(field, message) {
    const input = this.fields.get(field);
    if (input) {
      input.classList.add('is-invalid');
      const feedback = input.parentElement.querySelector('.invalid-feedback');
      if (feedback) {
        feedback.textContent = message;
      }
    }
  }

  /**
   * Clear all errors
   */
  clearErrors() {
    this.fields.forEach(input => {
      input.classList.remove('is-invalid');
    });
  }
}