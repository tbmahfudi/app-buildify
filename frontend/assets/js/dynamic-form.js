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
    this.calculatedFields = new Map(); // Maps calculated field name to formula
    this.fieldDependencies = new Map(); // Maps field name to dependent calculated fields
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

    // Initialize calculated fields and validation after all fields are rendered
    this.setupCalculatedFieldListeners();
    this.initializeCalculatedFields();
    this.setupValidationListeners();

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

    // Check if field is calculated
    const isCalculated = fieldConfig.is_calculated || fieldConfig.isCalculated || false;

    // If field is calculated, readonly, or user cannot edit, make it readonly
    const readonly = isCalculated || fieldConfig.readonly || !canEdit;

    // Build label text
    let labelText = fieldConfig.title;

    // Add indicator for calculated fields
    if (isCalculated) {
      labelText += ' 🧮'; // Calculator emoji to indicate calculated field
    }

    // Add lock icon if readonly due to RBAC (show in helper text instead)
    let helperText = fieldConfig.help || '';
    if (isCalculated && fieldConfig.calculation_formula) {
      helperText = `📐 Calculated: ${fieldConfig.calculation_formula}` + (helperText ? '\n' + helperText : '');
    } else if (!canEdit && !fieldConfig.readonly) {
      helperText = '🔒 You do not have permission to edit this field' + (helperText ? '. ' + helperText : '');
    }

    // Register calculated field
    if (isCalculated && fieldConfig.calculation_formula) {
      this.registerCalculatedField(fieldConfig.field, fieldConfig.calculation_formula);
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

    // Add prefix/suffix if configured
    this.addPrefixSuffix(component.inputElement, fieldConfig);

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

    // Add prefix/suffix if configured
    this.addPrefixSuffix(component.inputElement, fieldConfig);

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

    this.metadata.form.fields.forEach((fieldConfig) => {
      const fieldName = fieldConfig.field;
      const component = this.fieldComponents.get(fieldName);

      // Use the component's validate method if available
      if (component && component.validate) {
        if (!component.validate()) {
          isValid = false;
        }
      } else {
        // Fallback to HTML5 validation
        const element = this.fields.get(fieldName);
        if (element && !element.checkValidity()) {
          isValid = false;
        }
      }

      // Custom validation rules
      if (fieldConfig.validation_rules && fieldConfig.validation_rules.length > 0) {
        const fieldValid = this.validateFieldRules(fieldConfig);
        if (!fieldValid) {
          isValid = false;
        }
      }
    });

    return isValid;
  }

  /**
   * Validate field against custom validation rules
   */
  validateFieldRules(fieldConfig) {
    const element = this.fields.get(fieldConfig.field);
    if (!element) return true;

    const value = element.type === 'checkbox' ? element.checked :
                 element.type === 'number' ? parseFloat(element.value) :
                 element.value;

    const rules = fieldConfig.validation_rules || [];

    for (const rule of rules) {
      const result = this.evaluateValidationRule(rule, value, fieldConfig.field);

      if (!result.valid) {
        this.setFieldError(fieldConfig.field, result.message || rule.message || 'Validation failed');
        return false;
      }
    }

    // Clear error if all rules pass
    const component = this.fieldComponents.get(fieldConfig.field);
    if (component && component.clearError) {
      component.clearError();
    }

    return true;
  }

  /**
   * Evaluate a single validation rule
   */
  evaluateValidationRule(rule, value, fieldName) {
    try {
      switch (rule.type) {
        case 'regex':
          if (!rule.pattern) {
            return { valid: true };
          }
          const regex = new RegExp(rule.pattern);
          const valid = regex.test(String(value));
          return {
            valid,
            message: rule.message || `Value does not match required pattern`
          };

        case 'min_length':
          const minLength = parseInt(rule.value);
          const lengthValid = String(value).length >= minLength;
          return {
            valid: lengthValid,
            message: rule.message || `Minimum length is ${minLength} characters`
          };

        case 'max_length':
          const maxLength = parseInt(rule.value);
          const maxLengthValid = String(value).length <= maxLength;
          return {
            valid: maxLengthValid,
            message: rule.message || `Maximum length is ${maxLength} characters`
          };

        case 'min_value':
          const minValue = parseFloat(rule.value);
          const minValid = parseFloat(value) >= minValue;
          return {
            valid: minValid,
            message: rule.message || `Minimum value is ${minValue}`
          };

        case 'max_value':
          const maxValue = parseFloat(rule.value);
          const maxValid = parseFloat(value) <= maxValue;
          return {
            valid: maxValid,
            message: rule.message || `Maximum value is ${maxValue}`
          };

        case 'email':
          const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
          const emailValid = emailRegex.test(String(value));
          return {
            valid: emailValid,
            message: rule.message || 'Please enter a valid email address'
          };

        case 'url':
          try {
            new URL(value);
            return { valid: true };
          } catch {
            return {
              valid: false,
              message: rule.message || 'Please enter a valid URL'
            };
          }

        case 'phone':
          // Simple phone validation (allows various formats)
          const phoneRegex = /^[\d\s\-\+\(\)]+$/;
          const phoneValid = phoneRegex.test(String(value)) && String(value).replace(/\D/g, '').length >= 10;
          return {
            valid: phoneValid,
            message: rule.message || 'Please enter a valid phone number'
          };

        case 'custom':
          // Evaluate custom JavaScript expression
          if (!rule.expression) {
            return { valid: true };
          }
          const customResult = this.evaluateCustomValidation(rule.expression, value, fieldName);
          return {
            valid: customResult,
            message: rule.message || 'Validation failed'
          };

        default:
          console.warn(`Unknown validation rule type: ${rule.type}`);
          return { valid: true };
      }
    } catch (error) {
      console.error('Validation rule error:', error, rule);
      return { valid: true }; // Don't fail on validation errors
    }
  }

  /**
   * Evaluate custom validation expression
   */
  evaluateCustomValidation(expression, value, fieldName) {
    try {
      // Create context with current field value and all other field values
      const context = { value };

      this.fields.forEach((element, name) => {
        if (name !== fieldName) {
          context[name] = element.type === 'checkbox' ? element.checked :
                         element.type === 'number' ? parseFloat(element.value) :
                         element.value;
        }
      });

      // Replace field references in expression
      let evalExpression = expression;
      Object.keys(context).forEach(key => {
        const regex = new RegExp(`\\b${key}\\b`, 'g');
        const val = context[key];
        evalExpression = evalExpression.replace(regex, typeof val === 'string' ? `"${val}"` : val);
      });

      // Safely evaluate
      return new Function(`return ${evalExpression}`)();
    } catch (error) {
      console.error('Custom validation error:', error, expression);
      return true; // Don't fail on errors
    }
  }

  /**
   * Set up real-time validation on field blur/change
   */
  setupValidationListeners() {
    this.metadata.form.fields.forEach((fieldConfig) => {
      if (!fieldConfig.validation_rules || fieldConfig.validation_rules.length === 0) {
        return;
      }

      const element = this.fields.get(fieldConfig.field);
      if (!element) return;

      // Validate on blur
      element.addEventListener('blur', () => {
        this.validateFieldRules(fieldConfig);
      });

      // Also validate on change for immediate feedback
      element.addEventListener('change', () => {
        this.validateFieldRules(fieldConfig);
      });
    });
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
   * Add prefix/suffix to input element
   */
  addPrefixSuffix(inputElement, fieldConfig) {
    const prefix = fieldConfig.prefix;
    const suffix = fieldConfig.suffix;

    if (!prefix && !suffix) return;

    // Find the input wrapper (parent of input element)
    const inputWrapper = inputElement.parentElement;
    if (!inputWrapper) return;

    // Add styles to make it a flexbox if needed
    if (!inputWrapper.classList.contains('flex')) {
      inputWrapper.classList.add('flex', 'items-center', 'border', 'border-gray-300', 'rounded-lg');
      inputWrapper.classList.add('focus-within:ring-2', 'focus-within:ring-blue-500', 'focus-within:border-blue-500');

      // Remove border from input since wrapper now has it
      inputElement.classList.remove('border', 'border-gray-300', 'rounded-lg');
      inputElement.classList.add('border-0', 'focus:ring-0');
    }

    // Add prefix
    if (prefix) {
      const prefixEl = document.createElement('span');
      prefixEl.className = 'px-3 text-gray-600 font-medium bg-gray-50 border-r border-gray-300';
      prefixEl.textContent = prefix;
      inputWrapper.insertBefore(prefixEl, inputElement);
    }

    // Add suffix
    if (suffix) {
      const suffixEl = document.createElement('span');
      suffixEl.className = 'px-3 text-gray-600 font-medium bg-gray-50 border-l border-gray-300';
      suffixEl.textContent = suffix;
      inputWrapper.appendChild(suffixEl);
    }

    // Make input flex-1 to fill space
    inputElement.classList.add('flex-1');
  }

  /**
   * Register calculated field and track dependencies
   */
  registerCalculatedField(fieldName, formula) {
    this.calculatedFields.set(fieldName, formula);

    // Extract field references from formula (simple regex for field names)
    const fieldReferences = this.extractFieldReferences(formula);

    // Track dependencies: when fieldX changes, recalculate this field
    fieldReferences.forEach(refField => {
      if (!this.fieldDependencies.has(refField)) {
        this.fieldDependencies.set(refField, []);
      }
      this.fieldDependencies.get(refField).push(fieldName);
    });
  }

  /**
   * Extract field references from formula
   * Supports: fieldName, field_name patterns
   */
  extractFieldReferences(formula) {
    const references = new Set();

    // Match field names (letters, numbers, underscores)
    const pattern = /\b([a-zA-Z_][a-zA-Z0-9_]*)\b/g;
    let match;

    while ((match = pattern.exec(formula)) !== null) {
      const fieldName = match[1];
      // Exclude keywords and functions
      const keywords = ['IF', 'SUM', 'AVG', 'MIN', 'MAX', 'COUNT', 'ROUND', 'ABS', 'true', 'false', 'null'];
      if (!keywords.includes(fieldName) && this.fields.has(fieldName)) {
        references.add(fieldName);
      }
    }

    return Array.from(references);
  }

  /**
   * Evaluate formula with current field values
   */
  evaluateFormula(formula) {
    try {
      // Get all field values
      const context = {};
      this.fields.forEach((element, fieldName) => {
        let value;
        if (element.type === 'checkbox') {
          value = element.checked;
        } else if (element.type === 'number') {
          value = element.value ? parseFloat(element.value) : 0;
        } else {
          value = element.value || '';
        }
        context[fieldName] = value;
      });

      // Replace field references with values
      let expression = formula;
      Object.keys(context).forEach(fieldName => {
        const value = context[fieldName];
        // Use a regex to replace whole word matches only
        const regex = new RegExp(`\\b${fieldName}\\b`, 'g');
        expression = expression.replace(regex, typeof value === 'string' ? `"${value}"` : value);
      });

      // Support basic functions
      expression = this.replaceFunctions(expression, context);

      // Safely evaluate the expression
      const result = this.safeEval(expression);
      return result;
    } catch (error) {
      console.error('Formula evaluation error:', error, 'Formula:', formula);
      return null;
    }
  }

  /**
   * Replace function calls with JavaScript equivalents
   */
  replaceFunctions(expression, context) {
    // IF(condition, true_value, false_value)
    expression = expression.replace(/IF\s*\(\s*(.+?)\s*,\s*(.+?)\s*,\s*(.+?)\s*\)/gi,
      '(($1) ? ($2) : ($3))');

    // SUM(...fields) - get all values and sum
    expression = expression.replace(/SUM\s*\(\s*([^)]+)\s*\)/gi, (match, args) => {
      const fields = args.split(',').map(f => f.trim());
      const values = fields.map(f => context[f] || 0);
      return values.reduce((a, b) => a + b, 0);
    });

    // AVG(...fields)
    expression = expression.replace(/AVG\s*\(\s*([^)]+)\s*\)/gi, (match, args) => {
      const fields = args.split(',').map(f => f.trim());
      const values = fields.map(f => context[f] || 0);
      return values.length > 0 ? values.reduce((a, b) => a + b, 0) / values.length : 0;
    });

    // MIN(...fields)
    expression = expression.replace(/MIN\s*\(\s*([^)]+)\s*\)/gi, (match, args) => {
      const fields = args.split(',').map(f => f.trim());
      const values = fields.map(f => context[f] || 0);
      return Math.min(...values);
    });

    // MAX(...fields)
    expression = expression.replace(/MAX\s*\(\s*([^)]+)\s*\)/gi, (match, args) => {
      const fields = args.split(',').map(f => f.trim());
      const values = fields.map(f => context[f] || 0);
      return Math.max(...values);
    });

    // ROUND(value, decimals)
    expression = expression.replace(/ROUND\s*\(\s*(.+?)\s*,\s*(\d+)\s*\)/gi,
      'Math.round(($1) * Math.pow(10, $2)) / Math.pow(10, $2)');

    // ABS(value)
    expression = expression.replace(/ABS\s*\(\s*(.+?)\s*\)/gi, 'Math.abs($1)');

    return expression;
  }

  /**
   * Safely evaluate expression (restricted eval)
   */
  safeEval(expression) {
    // Only allow math operations, numbers, and basic operators
    const safeExpression = expression.replace(/[^0-9+\-*/(). <>=!&|"]/g, '');

    // Use Function constructor instead of eval for better safety
    try {
      return new Function(`return ${expression}`)();
    } catch (error) {
      console.error('Safe eval error:', error);
      return null;
    }
  }

  /**
   * Update calculated fields when dependencies change
   */
  updateCalculatedFields(changedFieldName) {
    const dependentFields = this.fieldDependencies.get(changedFieldName) || [];

    dependentFields.forEach(calcFieldName => {
      const formula = this.calculatedFields.get(calcFieldName);
      if (formula) {
        const result = this.evaluateFormula(formula);

        // Update the calculated field's value
        const element = this.fields.get(calcFieldName);
        if (element && result !== null) {
          element.value = result;

          // Trigger change event for cascading calculations
          element.dispatchEvent(new Event('change', { bubbles: true }));
        }
      }
    });
  }

  /**
   * Set up field change listeners for calculated fields
   */
  setupCalculatedFieldListeners() {
    this.fields.forEach((element, fieldName) => {
      // Skip calculated fields themselves
      if (this.calculatedFields.has(fieldName)) {
        return;
      }

      // Listen for changes
      element.addEventListener('input', () => {
        this.updateCalculatedFields(fieldName);
      });

      element.addEventListener('change', () => {
        this.updateCalculatedFields(fieldName);
      });
    });
  }

  /**
   * Initialize all calculated fields with their initial values
   */
  initializeCalculatedFields() {
    this.calculatedFields.forEach((formula, fieldName) => {
      const result = this.evaluateFormula(formula);
      const element = this.fields.get(fieldName);
      if (element && result !== null) {
        element.value = result;
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
    this.calculatedFields.clear();
    this.fieldDependencies.clear();
  }
}
