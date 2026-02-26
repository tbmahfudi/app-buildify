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
    this.locale = this.getCurrentLocale(); // Current language locale
  }

  // ==================== Multi-language Support (Phase 5 Week 3-4) ====================

  /**
   * Get current locale from localStorage or default to 'en'
   * @returns {string} - Current locale code (e.g., 'en', 'es', 'fr')
   */
  getCurrentLocale() {
    return localStorage.getItem('app_locale') || 'en';
  }

  /**
   * Set current locale and reload form
   * @param {string} locale - Locale code to set
   */
  setLocale(locale) {
    localStorage.setItem('app_locale', locale);
    this.locale = locale;
    // Reload form with new locale
    this.render();
  }

  /**
   * Get localized text for a field property
   * @param {Object} fieldConfig - Field configuration
   * @param {string} property - Property name ('label', 'help_text', 'placeholder', 'description')
   * @returns {string} - Localized text or fallback to default
   */
  getLocalizedText(fieldConfig, property) {
    const i18nProperty = `${property}_i18n`;

    // Check if i18n version exists and has translation for current locale
    if (fieldConfig[i18nProperty] && fieldConfig[i18nProperty][this.locale]) {
      return fieldConfig[i18nProperty][this.locale];
    }

    // Fallback to default property
    // Handle different property name mappings
    const propertyMap = {
      'label': 'title',
      'help_text': 'help',
      'placeholder': 'placeholder',
      'description': 'description'
    };

    const fallbackProperty = propertyMap[property] || property;
    return fieldConfig[fallbackProperty] || fieldConfig[property] || '';
  }

  /**
   * Render the form
   */
  render() {
    this.container.innerHTML = '';

    const form = document.createElement('form');
    form.className = 'dynamic-form space-y-4';
    form.id = 'dynamic-form';

    // Check if field groups are defined
    if (this.metadata.form.groups && this.metadata.form.groups.length > 0) {
      // Render with field groups
      this.renderFieldGroups(form);
    } else {
      // Render fields without groups (legacy mode)
      this.metadata.form.fields.forEach(field => {
        const formGroup = this.createFormGroup(field);
        form.appendChild(formGroup);
      });
    }

    this.container.appendChild(form);

    // Initialize calculated fields and validation after all fields are rendered
    this.setupCalculatedFieldListeners();
    this.initializeCalculatedFields();
    this.setupValidationListeners();

    // Initialize conditional visibility
    this.setupVisibilityListeners();
    this.updateAllFieldVisibility();

    // Initialize field dependencies (cascading dropdowns)
    this.setupFieldDependencyListeners();

    return form;
  }

  /**
   * Render form with field groups (Phase 5 Week 3-4)
   * @param {HTMLFormElement} form - Form element to render groups into
   */
  renderFieldGroups(form) {
    const groups = this.metadata.form.groups || [];

    // Sort groups by display_order
    const sortedGroups = [...groups].sort((a, b) => (a.display_order || 0) - (b.display_order || 0));

    // Create a map of field_name to fieldConfig for quick lookup
    const fieldMap = new Map();
    this.metadata.form.fields.forEach(field => {
      fieldMap.set(field.field || field.name, field);
    });

    // Render each group
    sortedGroups.forEach(group => {
      if (!group.is_active) return; // Skip inactive groups

      const groupSection = this.createFieldGroupSection(group, fieldMap);
      form.appendChild(groupSection);
    });

    // Render ungrouped fields (fields not assigned to any group)
    const groupedFieldNames = new Set();
    sortedGroups.forEach(group => {
      if (group.fields) {
        group.fields.forEach(fieldName => groupedFieldNames.add(fieldName));
      }
    });

    const ungroupedFields = this.metadata.form.fields.filter(field => {
      const fieldName = field.field || field.name;
      return !groupedFieldNames.has(fieldName);
    });

    if (ungroupedFields.length > 0) {
      const ungroupedSection = document.createElement('div');
      ungroupedSection.className = 'ungrouped-fields space-y-4';
      ungroupedFields.forEach(field => {
        const formGroup = this.createFormGroup(field);
        ungroupedSection.appendChild(formGroup);
      });
      form.appendChild(ungroupedSection);
    }
  }

  /**
   * Create a field group section with collapsible functionality
   * @param {Object} group - Group configuration
   * @param {Map} fieldMap - Map of field names to field configs
   * @returns {HTMLElement} - Field group section element
   */
  createFieldGroupSection(group, fieldMap) {
    const section = document.createElement('div');
    section.className = 'field-group mb-6';
    section.dataset.groupId = group.id || group.name;

    // Header
    const header = document.createElement('div');
    header.className = 'field-group-header flex items-center justify-between p-3 bg-gray-50 rounded-t-lg border border-gray-200 cursor-pointer hover:bg-gray-100 transition-colors';
    header.innerHTML = `
      <div class="flex items-center gap-2">
        ${group.icon ? `<i class="ph ph-${group.icon} text-lg text-gray-600"></i>` : ''}
        <h3 class="font-semibold text-gray-900">${group.label}</h3>
        ${group.description ? `<span class="text-sm text-gray-500 ml-2">${group.description}</span>` : ''}
      </div>
      ${group.is_collapsible ? '<i class="ph ph-caret-down transition-transform text-gray-600"></i>' : ''}
    `;

    // Content container
    const content = document.createElement('div');
    content.className = 'field-group-content p-4 border border-t-0 border-gray-200 rounded-b-lg space-y-4 bg-white';

    // Set initial collapsed state
    if (group.is_collapsible && group.is_collapsed_default) {
      content.style.display = 'none';
      const caret = header.querySelector('.ph-caret-down');
      if (caret) caret.classList.add('rotate-180');
    }

    // Add fields to group
    const fieldNames = group.fields || [];
    fieldNames.forEach(fieldName => {
      const fieldConfig = fieldMap.get(fieldName);
      if (fieldConfig) {
        const formGroup = this.createFormGroup(fieldConfig);
        content.appendChild(formGroup);
      }
    });

    // Toggle collapse functionality
    if (group.is_collapsible) {
      header.addEventListener('click', () => {
        const isHidden = content.style.display === 'none';
        content.style.display = isHidden ? 'block' : 'none';

        const caret = header.querySelector('.ph-caret-down');
        if (caret) {
          if (isHidden) {
            caret.classList.remove('rotate-180');
          } else {
            caret.classList.add('rotate-180');
          }
        }
      });
    }

    section.appendChild(header);
    section.appendChild(content);

    return section;
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

    // Build label text (with i18n support)
    let labelText = this.getLocalizedText(fieldConfig, 'label');

    // Add indicator for calculated fields
    if (isCalculated) {
      labelText += ' 🧮'; // Calculator emoji to indicate calculated field
    }

    // Build helper text (with i18n support)
    let helperText = this.getLocalizedText(fieldConfig, 'help_text');
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

    // Get localized placeholder
    const placeholder = this.getLocalizedText(fieldConfig, 'placeholder');

    // Check for input_type override first (Phase 5 Priority 2: Advanced Input Types)
    if (fieldConfig.input_type) {
      switch (fieldConfig.input_type) {
        case 'color':
          return this.createColorPicker(fieldConfig, value, readonly, labelText, helperText);
        case 'rating':
          return this.createRating(fieldConfig, value, readonly, labelText, helperText);
        case 'currency':
          return this.createCurrencyInput(fieldConfig, value, readonly, labelText, helperText);
        case 'percentage':
          return this.createPercentageInput(fieldConfig, value, readonly, labelText, helperText);
        case 'slider':
          return this.createSlider(fieldConfig, value, readonly, labelText, helperText);
        case 'tags':
          return this.createTagInput(fieldConfig, value, readonly, labelText, helperText);
        case 'autocomplete':
          return this.createAutocomplete(fieldConfig, value, readonly, labelText, helperText);
        case 'rich-text':
          return this.createRichTextEditor(fieldConfig, value, readonly, labelText, helperText);
        case 'code-editor':
          return this.createCodeEditor(fieldConfig, value, readonly, labelText, helperText);
      }
    }

    // Fall back to field_type mapping
    switch (fieldConfig.type) {
      case 'text':
      case 'email':
      case 'url':
        return this.createTextInput(fieldConfig, value, readonly, labelText, helperText, placeholder);

      case 'number':
        return this.createNumberInput(fieldConfig, value, readonly, labelText, helperText, placeholder);

      case 'textarea':
        return this.createTextarea(fieldConfig, value, readonly, labelText, helperText, placeholder);

      case 'select':
        return this.createSelect(fieldConfig, value, readonly, labelText, helperText);

      case 'boolean':
      case 'checkbox':
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
  createTextInput(fieldConfig, value, readonly, labelText, helperText, placeholder = '') {
    const container = document.createElement('div');

    const component = new FlexInput(container, {
      type: fieldConfig.type === 'email' ? 'email' :
            fieldConfig.type === 'url' ? 'url' : 'text',
      label: labelText,
      value: value || '',
      placeholder: placeholder || fieldConfig.placeholder || '',
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
  createNumberInput(fieldConfig, value, readonly, labelText, helperText, placeholder = '') {
    const container = document.createElement('div');

    const component = new FlexInput(container, {
      type: 'number',
      label: labelText,
      value: value || '',
      placeholder: placeholder || fieldConfig.placeholder || '',
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
  createTextarea(fieldConfig, value, readonly, labelText, helperText, placeholder = '') {
    const container = document.createElement('div');

    const component = new FlexTextarea(container, {
      label: labelText,
      value: value || '',
      placeholder: placeholder || fieldConfig.placeholder || '',
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

    // Hidden input keeps the selected value in the DOM so getValues() / getFormData()
    // can read element.value without knowing about FlexSelect internals.
    const hiddenInput = document.createElement('input');
    hiddenInput.type = 'hidden';
    hiddenInput.name = fieldConfig.field;
    hiddenInput.value = value || '';
    container.appendChild(hiddenInput);

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
      size: 'md',
      onChange: (val) => { hiddenInput.value = val ?? ''; }
    });

    // Store the hidden input so getValues() gets a real element with .value
    this.fields.set(fieldConfig.field, hiddenInput);
    this.fieldComponents.set(fieldConfig.field, component);

    // Auto-fetch options for reference/lookup fields that have a reference_entity_id
    if (fieldConfig.reference_entity_id && !fieldConfig.depends_on_field) {
      this.loadReferenceFieldOptions(fieldConfig, component, value);
    }

    return container;
  }

  /**
   * Load options for a reference/lookup field from its referenced entity
   * @param {Object} fieldConfig - Field configuration with reference_entity_id
   * @param {Object} component - FlexSelect component instance
   * @param {*} currentValue - Current field value to restore after loading
   */
  async loadReferenceFieldOptions(fieldConfig, component, currentValue) {
    try {
      // Show loading state
      if (component.selectElement) {
        component.selectElement.disabled = true;
      }

      const params = new URLSearchParams({ limit: '100' });

      // Prefer entity name for the API call (dynamic-data API uses entity name, not UUID)
      const entityIdentifier = fieldConfig.reference_entity_name || fieldConfig.reference_entity_id;

      // Fetch records from the referenced entity
      const response = await fetch(
        `/api/v1/dynamic-data/${entityIdentifier}/records?${params}`
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      const records = data.items || data.data || data.records || [];

      // Format as options using display_field from field config
      const displayField = fieldConfig.display_field || 'name';
      const displayTemplate = fieldConfig.lookup_display_template;
      const options = records.map(record => {
        let label;
        if (displayTemplate) {
          // Apply display template, e.g., "{name} ({email})"
          label = displayTemplate.replace(/\{(\w+)\}/g, (match, key) => record[key] || '');
        } else {
          label = record[displayField] || record.name || record.id;
        }
        return {
          value: record.id,
          label: label
        };
      });

      // Update select options
      if (component.selectElement) {
        // Clear existing options except placeholder
        component.selectElement.innerHTML = '';

        // Add placeholder
        const placeholderOpt = document.createElement('option');
        placeholderOpt.value = '';
        placeholderOpt.textContent = fieldConfig.required ? 'Select an option' : '-- Select --';
        component.selectElement.appendChild(placeholderOpt);

        // Add fetched options
        options.forEach(opt => {
          const option = document.createElement('option');
          option.value = opt.value;
          option.textContent = opt.label;
          component.selectElement.appendChild(option);
        });

        // Restore current value if it exists in the options
        if (currentValue && options.some(opt => opt.value === currentValue)) {
          component.selectElement.value = currentValue;
        }

        // Re-enable
        component.selectElement.disabled = false;

        // Make searchable if many options
        if (component.updateOptions) {
          component.updateOptions(options);
        }
      }
    } catch (error) {
      console.error(`Error loading reference options for ${fieldConfig.field}:`, error);
      if (component.selectElement) {
        component.selectElement.disabled = false;
      }
    }
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
   * Create color picker input
   */
  createColorPicker(fieldConfig, value, readonly, labelText, helperText) {
    const container = document.createElement('div');
    container.className = 'space-y-2';

    // Label
    if (labelText) {
      const label = document.createElement('label');
      label.className = 'block text-sm font-medium text-gray-700';
      label.textContent = labelText;
      if (fieldConfig.required) {
        const asterisk = document.createElement('span');
        asterisk.className = 'text-red-500 ml-1';
        asterisk.textContent = '*';
        label.appendChild(asterisk);
      }
      container.appendChild(label);
    }

    // Color input wrapper
    const inputWrapper = document.createElement('div');
    inputWrapper.className = 'flex items-center gap-3';

    // Color picker input
    const colorInput = document.createElement('input');
    colorInput.type = 'color';
    colorInput.value = value || '#000000';
    colorInput.disabled = readonly;
    colorInput.name = fieldConfig.field;
    colorInput.className = 'h-10 w-20 cursor-pointer border border-gray-300 rounded';

    // Hex value display/input
    const hexInput = document.createElement('input');
    hexInput.type = 'text';
    hexInput.value = value || '#000000';
    hexInput.disabled = readonly;
    hexInput.placeholder = '#000000';
    hexInput.className = 'px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 font-mono text-sm';
    hexInput.maxLength = 7;

    // Sync color picker and hex input
    colorInput.addEventListener('input', () => {
      hexInput.value = colorInput.value;
    });

    hexInput.addEventListener('input', () => {
      if (/^#[0-9A-F]{6}$/i.test(hexInput.value)) {
        colorInput.value = hexInput.value;
      }
    });

    inputWrapper.appendChild(colorInput);
    inputWrapper.appendChild(hexInput);
    container.appendChild(inputWrapper);

    // Helper text
    if (helperText) {
      const helper = document.createElement('p');
      helper.className = 'text-sm text-gray-500';
      helper.textContent = helperText;
      container.appendChild(helper);
    }

    this.fields.set(fieldConfig.field, colorInput);

    return container;
  }

  /**
   * Create star rating input
   */
  createRating(fieldConfig, value, readonly, labelText, helperText) {
    const container = document.createElement('div');
    container.className = 'space-y-2';

    // Label
    if (labelText) {
      const label = document.createElement('label');
      label.className = 'block text-sm font-medium text-gray-700';
      label.textContent = labelText;
      if (fieldConfig.required) {
        const asterisk = document.createElement('span');
        asterisk.className = 'text-red-500 ml-1';
        asterisk.textContent = '*';
        label.appendChild(asterisk);
      }
      container.appendChild(label);
    }

    const maxStars = fieldConfig.max_value || 5;
    const currentRating = parseInt(value) || 0;

    // Rating wrapper
    const ratingWrapper = document.createElement('div');
    ratingWrapper.className = 'flex items-center gap-1';

    // Hidden input to store value
    const hiddenInput = document.createElement('input');
    hiddenInput.type = 'hidden';
    hiddenInput.value = currentRating;
    hiddenInput.name = fieldConfig.field;

    // Create stars
    for (let i = 1; i <= maxStars; i++) {
      const star = document.createElement('span');
      star.className = 'cursor-pointer text-3xl transition-colors';
      star.textContent = i <= currentRating ? '⭐' : '☆';
      star.dataset.rating = i;

      if (!readonly) {
        star.addEventListener('click', () => {
          hiddenInput.value = i;
          // Update all stars
          ratingWrapper.querySelectorAll('span').forEach((s, idx) => {
            s.textContent = (idx + 1) <= i ? '⭐' : '☆';
          });
        });

        star.addEventListener('mouseenter', () => {
          ratingWrapper.querySelectorAll('span').forEach((s, idx) => {
            s.textContent = (idx + 1) <= i ? '⭐' : '☆';
          });
        });
      }

      ratingWrapper.appendChild(star);
    }

    // Reset on mouse leave if not readonly
    if (!readonly) {
      ratingWrapper.addEventListener('mouseleave', () => {
        const currentValue = parseInt(hiddenInput.value) || 0;
        ratingWrapper.querySelectorAll('span').forEach((s, idx) => {
          s.textContent = (idx + 1) <= currentValue ? '⭐' : '☆';
        });
      });
    }

    container.appendChild(ratingWrapper);

    // Helper text
    if (helperText) {
      const helper = document.createElement('p');
      helper.className = 'text-sm text-gray-500';
      helper.textContent = helperText;
      container.appendChild(helper);
    }

    this.fields.set(fieldConfig.field, hiddenInput);
    container.appendChild(hiddenInput);

    return container;
  }

  /**
   * Create currency input with formatting
   */
  createCurrencyInput(fieldConfig, value, readonly, labelText, helperText) {
    const container = document.createElement('div');

    const component = new FlexInput(container, {
      type: 'number',
      label: labelText,
      value: value || '',
      placeholder: fieldConfig.placeholder || '0.00',
      required: fieldConfig.required || false,
      readonly: readonly,
      helperText: helperText,
      step: '0.01',
      min: fieldConfig.min_value || 0,
      variant: 'outlined',
      size: 'md'
    });

    this.fields.set(fieldConfig.field, component.inputElement);
    this.fieldComponents.set(fieldConfig.field, component);
    component.inputElement.name = fieldConfig.field;

    // Add currency prefix (e.g., $, €, £)
    const currencyPrefix = fieldConfig.prefix || fieldConfig.meta_data?.currency_symbol || '$';
    this.addPrefixSuffix(component.inputElement, { prefix: currencyPrefix });

    // Format on blur (add thousand separators)
    component.inputElement.addEventListener('blur', (e) => {
      if (e.target.value) {
        const num = parseFloat(e.target.value);
        e.target.value = num.toFixed(2);
      }
    });

    return container;
  }

  /**
   * Create percentage input with slider
   */
  createPercentageInput(fieldConfig, value, readonly, labelText, helperText) {
    const container = document.createElement('div');
    container.className = 'space-y-2';

    // Label
    if (labelText) {
      const label = document.createElement('label');
      label.className = 'block text-sm font-medium text-gray-700';
      label.textContent = labelText;
      if (fieldConfig.required) {
        const asterisk = document.createElement('span');
        asterisk.className = 'text-red-500 ml-1';
        asterisk.textContent = '*';
        label.appendChild(asterisk);
      }
      container.appendChild(label);
    }

    // Input wrapper with slider
    const inputWrapper = document.createElement('div');
    inputWrapper.className = 'flex items-center gap-3';

    // Range slider
    const slider = document.createElement('input');
    slider.type = 'range';
    slider.min = fieldConfig.min_value || 0;
    slider.max = fieldConfig.max_value || 100;
    slider.step = fieldConfig.step || 1;
    slider.value = value || 0;
    slider.disabled = readonly;
    slider.className = 'flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer';

    // Number input with % suffix
    const numberInput = document.createElement('input');
    numberInput.type = 'number';
    numberInput.min = slider.min;
    numberInput.max = slider.max;
    numberInput.step = slider.step;
    numberInput.value = value || 0;
    numberInput.disabled = readonly;
    numberInput.name = fieldConfig.field;
    numberInput.className = 'w-20 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-right';

    const percentLabel = document.createElement('span');
    percentLabel.className = 'text-gray-600 font-medium';
    percentLabel.textContent = '%';

    // Sync slider and input
    slider.addEventListener('input', () => {
      numberInput.value = slider.value;
    });

    numberInput.addEventListener('input', () => {
      slider.value = numberInput.value;
    });

    inputWrapper.appendChild(slider);
    inputWrapper.appendChild(numberInput);
    inputWrapper.appendChild(percentLabel);
    container.appendChild(inputWrapper);

    // Helper text
    if (helperText) {
      const helper = document.createElement('p');
      helper.className = 'text-sm text-gray-500';
      helper.textContent = helperText;
      container.appendChild(helper);
    }

    this.fields.set(fieldConfig.field, numberInput);

    return container;
  }

  /**
   * Create range slider input
   */
  createSlider(fieldConfig, value, readonly, labelText, helperText) {
    const container = document.createElement('div');
    container.className = 'space-y-2';

    // Label
    if (labelText) {
      const label = document.createElement('label');
      label.className = 'block text-sm font-medium text-gray-700';
      label.textContent = labelText;
      if (fieldConfig.required) {
        const asterisk = document.createElement('span');
        asterisk.className = 'text-red-500 ml-1';
        asterisk.textContent = '*';
        label.appendChild(asterisk);
      }
      container.appendChild(label);
    }

    // Slider wrapper
    const sliderWrapper = document.createElement('div');
    sliderWrapper.className = 'flex items-center gap-3';

    // Range slider
    const slider = document.createElement('input');
    slider.type = 'range';
    slider.min = fieldConfig.min_value || fieldConfig.validators?.min || 0;
    slider.max = fieldConfig.max_value || fieldConfig.validators?.max || 100;
    slider.step = fieldConfig.step || fieldConfig.validators?.step || 1;
    slider.value = value || slider.min;
    slider.disabled = readonly;
    slider.name = fieldConfig.field;
    slider.className = 'flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer';

    // Value display
    const valueDisplay = document.createElement('span');
    valueDisplay.className = 'text-sm font-semibold text-gray-700 min-w-[3rem] text-right';
    valueDisplay.textContent = slider.value;

    // Update display on slider change
    slider.addEventListener('input', () => {
      valueDisplay.textContent = slider.value;
    });

    sliderWrapper.appendChild(slider);
    sliderWrapper.appendChild(valueDisplay);
    container.appendChild(sliderWrapper);

    // Min/Max labels
    const labelsWrapper = document.createElement('div');
    labelsWrapper.className = 'flex justify-between text-xs text-gray-500';
    labelsWrapper.innerHTML = `
      <span>${slider.min}</span>
      <span>${slider.max}</span>
    `;
    container.appendChild(labelsWrapper);

    // Helper text
    if (helperText) {
      const helper = document.createElement('p');
      helper.className = 'text-sm text-gray-500 mt-1';
      helper.textContent = helperText;
      container.appendChild(helper);
    }

    this.fields.set(fieldConfig.field, slider);

    return container;
  }

  /**
   * Create tag input component
   */
  createTagInput(fieldConfig, value, readonly, labelText, helperText) {
    const container = document.createElement('div');
    container.className = 'space-y-2';

    // Label
    if (labelText) {
      const label = document.createElement('label');
      label.className = 'block text-sm font-medium text-gray-700';
      label.textContent = labelText;
      if (fieldConfig.required) {
        const asterisk = document.createElement('span');
        asterisk.className = 'text-red-500 ml-1';
        asterisk.textContent = '*';
        label.appendChild(asterisk);
      }
      container.appendChild(label);
    }

    // Tags wrapper
    const tagsWrapper = document.createElement('div');
    tagsWrapper.className = 'flex flex-wrap gap-2 p-3 border border-gray-300 rounded-lg min-h-[42px] focus-within:ring-2 focus-within:ring-blue-500';

    // Hidden input to store tag values
    const hiddenInput = document.createElement('input');
    hiddenInput.type = 'hidden';
    hiddenInput.name = fieldConfig.field;

    // Parse existing tags
    let tags = [];
    try {
      tags = value ? (Array.isArray(value) ? value : JSON.parse(value)) : [];
    } catch {
      tags = value ? value.split(',').map(t => t.trim()) : [];
    }

    // Render existing tags
    const renderTags = () => {
      tagsWrapper.innerHTML = '';

      tags.forEach((tag, index) => {
        const tagEl = document.createElement('span');
        tagEl.className = 'inline-flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-800 rounded text-sm';
        tagEl.innerHTML = `
          ${tag}
          ${!readonly ? '<button type="button" class="hover:text-blue-600" data-index="' + index + '">×</button>' : ''}
        `;

        if (!readonly) {
          const removeBtn = tagEl.querySelector('button');
          removeBtn.addEventListener('click', () => {
            tags.splice(index, 1);
            hiddenInput.value = JSON.stringify(tags);
            renderTags();
          });
        }

        tagsWrapper.appendChild(tagEl);
      });

      // Add input field for new tags
      if (!readonly) {
        const tagInput = document.createElement('input');
        tagInput.type = 'text';
        tagInput.placeholder = tags.length === 0 ? (fieldConfig.placeholder || 'Add tag...') : '';
        tagInput.className = 'flex-1 min-w-[120px] outline-none bg-transparent';

        tagInput.addEventListener('keydown', (e) => {
          if (e.key === 'Enter' || e.key === ',') {
            e.preventDefault();
            const newTag = tagInput.value.trim();
            if (newTag && !tags.includes(newTag)) {
              tags.push(newTag);
              hiddenInput.value = JSON.stringify(tags);
              tagInput.value = '';
              renderTags();
            }
          } else if (e.key === 'Backspace' && tagInput.value === '' && tags.length > 0) {
            tags.pop();
            hiddenInput.value = JSON.stringify(tags);
            renderTags();
          }
        });

        tagsWrapper.appendChild(tagInput);
      }
    };

    hiddenInput.value = JSON.stringify(tags);
    renderTags();

    container.appendChild(tagsWrapper);
    container.appendChild(hiddenInput);

    // Helper text
    if (helperText) {
      const helper = document.createElement('p');
      helper.className = 'text-sm text-gray-500';
      helper.textContent = helperText;
      container.appendChild(helper);
    }

    this.fields.set(fieldConfig.field, hiddenInput);

    return container;
  }

  /**
   * Create autocomplete input
   */
  createAutocomplete(fieldConfig, value, readonly, labelText, helperText) {
    const container = document.createElement('div');
    container.className = 'space-y-2 relative';

    // Label
    if (labelText) {
      const label = document.createElement('label');
      label.className = 'block text-sm font-medium text-gray-700';
      label.textContent = labelText;
      if (fieldConfig.required) {
        const asterisk = document.createElement('span');
        asterisk.className = 'text-red-500 ml-1';
        asterisk.textContent = '*';
        label.appendChild(asterisk);
      }
      container.appendChild(label);
    }

    // Input
    const input = document.createElement('input');
    input.type = 'text';
    input.value = value || '';
    input.disabled = readonly;
    input.name = fieldConfig.field;
    input.placeholder = fieldConfig.placeholder || 'Start typing...';
    input.className = 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500';
    input.autocomplete = 'off';

    // Dropdown for suggestions
    const dropdown = document.createElement('div');
    dropdown.className = 'absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto hidden';

    let debounceTimeout;
    input.addEventListener('input', () => {
      clearTimeout(debounceTimeout);

      if (input.value.length < 2) {
        dropdown.classList.add('hidden');
        return;
      }

      debounceTimeout = setTimeout(async () => {
        const suggestions = await this.fetchAutocompleteSuggestions(fieldConfig, input.value);

        if (suggestions.length > 0) {
          dropdown.innerHTML = '';
          suggestions.forEach(suggestion => {
            const item = document.createElement('div');
            item.className = 'px-3 py-2 hover:bg-gray-100 cursor-pointer';
            item.textContent = suggestion;
            item.addEventListener('click', () => {
              input.value = suggestion;
              dropdown.classList.add('hidden');
            });
            dropdown.appendChild(item);
          });
          dropdown.classList.remove('hidden');
        } else {
          dropdown.classList.add('hidden');
        }
      }, 300);
    });

    // Close dropdown on outside click
    document.addEventListener('click', (e) => {
      if (!container.contains(e.target)) {
        dropdown.classList.add('hidden');
      }
    });

    container.appendChild(input);
    container.appendChild(dropdown);

    // Helper text
    if (helperText) {
      const helper = document.createElement('p');
      helper.className = 'text-sm text-gray-500';
      helper.textContent = helperText;
      container.appendChild(helper);
    }

    this.fields.set(fieldConfig.field, input);

    return container;
  }

  /**
   * Fetch autocomplete suggestions
   */
  async fetchAutocompleteSuggestions(fieldConfig, query) {
    // Check if suggestions are configured in metadata
    const source = fieldConfig.meta_data?.autocomplete_source;

    if (source === 'api' && fieldConfig.meta_data?.api_url) {
      try {
        const response = await fetch(`${fieldConfig.meta_data.api_url}?q=${encodeURIComponent(query)}`);
        const data = await response.json();
        return data.results || data;
      } catch (error) {
        console.error('Autocomplete API error:', error);
        return [];
      }
    }

    // Static list from allowed_values
    if (fieldConfig.allowed_values && Array.isArray(fieldConfig.allowed_values)) {
      return fieldConfig.allowed_values.filter(val =>
        val.toLowerCase().includes(query.toLowerCase())
      );
    }

    return [];
  }

  /**
   * Create rich text editor
   */
  createRichTextEditor(fieldConfig, value, readonly, labelText, helperText) {
    const container = document.createElement('div');
    container.className = 'space-y-2';

    // Label
    if (labelText) {
      const label = document.createElement('label');
      label.className = 'block text-sm font-medium text-gray-700';
      label.textContent = labelText;
      if (fieldConfig.required) {
        const asterisk = document.createElement('span');
        asterisk.className = 'text-red-500 ml-1';
        asterisk.textContent = '*';
        label.appendChild(asterisk);
      }
      container.appendChild(label);
    }

    // Toolbar (if not readonly)
    if (!readonly) {
      const toolbar = document.createElement('div');
      toolbar.className = 'flex gap-1 p-2 bg-gray-50 border border-gray-300 rounded-t-lg';
      toolbar.innerHTML = `
        <button type="button" data-command="bold" class="px-2 py-1 hover:bg-gray-200 rounded" title="Bold"><strong>B</strong></button>
        <button type="button" data-command="italic" class="px-2 py-1 hover:bg-gray-200 rounded" title="Italic"><em>I</em></button>
        <button type="button" data-command="underline" class="px-2 py-1 hover:bg-gray-200 rounded" title="Underline"><u>U</u></button>
        <div class="w-px bg-gray-300 mx-1"></div>
        <button type="button" data-command="insertUnorderedList" class="px-2 py-1 hover:bg-gray-200 rounded" title="Bullet List">•</button>
        <button type="button" data-command="insertOrderedList" class="px-2 py-1 hover:bg-gray-200 rounded" title="Numbered List">1.</button>
      `;

      toolbar.querySelectorAll('button').forEach(btn => {
        btn.addEventListener('click', (e) => {
          e.preventDefault();
          document.execCommand(btn.dataset.command, false, null);
        });
      });

      container.appendChild(toolbar);
    }

    // Editable div
    const editor = document.createElement('div');
    editor.contentEditable = !readonly;
    editor.innerHTML = value || '';
    editor.className = `w-full min-h-[150px] p-3 border ${readonly ? 'border-t' : ''} border-gray-300 ${readonly ? 'rounded-lg' : 'rounded-b-lg'} focus:ring-2 focus:ring-blue-500 focus:outline-none overflow-y-auto`;

    // Hidden input to store HTML
    const hiddenInput = document.createElement('input');
    hiddenInput.type = 'hidden';
    hiddenInput.name = fieldConfig.field;
    hiddenInput.value = value || '';

    editor.addEventListener('input', () => {
      hiddenInput.value = editor.innerHTML;
    });

    container.appendChild(editor);
    container.appendChild(hiddenInput);

    // Helper text
    if (helperText) {
      const helper = document.createElement('p');
      helper.className = 'text-sm text-gray-500';
      helper.textContent = helperText;
      container.appendChild(helper);
    }

    this.fields.set(fieldConfig.field, hiddenInput);

    return container;
  }

  /**
   * Create code editor
   */
  createCodeEditor(fieldConfig, value, readonly, labelText, helperText) {
    const container = document.createElement('div');
    container.className = 'space-y-2';

    // Label
    if (labelText) {
      const label = document.createElement('label');
      label.className = 'block text-sm font-medium text-gray-700';
      label.textContent = labelText;
      if (fieldConfig.required) {
        const asterisk = document.createElement('span');
        asterisk.className = 'text-red-500 ml-1';
        asterisk.textContent = '*';
        label.appendChild(asterisk);
      }
      container.appendChild(label);
    }

    // Language indicator (if specified)
    const language = fieldConfig.meta_data?.language || 'text';
    if (language !== 'text') {
      const langLabel = document.createElement('div');
      langLabel.className = 'text-xs font-mono text-gray-500 bg-gray-100 px-2 py-1 rounded-t inline-block';
      langLabel.textContent = language;
      container.appendChild(langLabel);
    }

    // Textarea with monospace font
    const textarea = document.createElement('textarea');
    textarea.value = value || '';
    textarea.disabled = readonly;
    textarea.name = fieldConfig.field;
    textarea.placeholder = fieldConfig.placeholder || `// Enter ${language} code...`;
    textarea.className = 'w-full min-h-[200px] p-3 border border-gray-300 rounded-lg font-mono text-sm focus:ring-2 focus:ring-blue-500 bg-gray-50';
    textarea.spellcheck = false;

    // Enable tab key
    textarea.addEventListener('keydown', (e) => {
      if (e.key === 'Tab') {
        e.preventDefault();
        const start = textarea.selectionStart;
        const end = textarea.selectionEnd;
        textarea.value = textarea.value.substring(0, start) + '  ' + textarea.value.substring(end);
        textarea.selectionStart = textarea.selectionEnd = start + 2;
      }
    });

    container.appendChild(textarea);

    // Helper text
    if (helperText) {
      const helper = document.createElement('p');
      helper.className = 'text-sm text-gray-500';
      helper.textContent = helperText;
      container.appendChild(helper);
    }

    this.fields.set(fieldConfig.field, textarea);

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

  // ==================== Conditional Visibility (Phase 5 Week 3-4) ====================

  /**
   * Evaluate visibility rules for a field
   * @param {Object} fieldConfig - Field configuration with visibility_rules
   * @returns {boolean} - True if field should be visible
   */
  evaluateVisibilityRules(fieldConfig) {
    // If no visibility rules, field is always visible
    if (!fieldConfig.visibility_rules) {
      return true;
    }

    const rules = fieldConfig.visibility_rules;
    const operator = rules.operator || 'AND';
    const conditions = rules.conditions || [];

    // Evaluate each condition
    const results = conditions.map(condition => {
      const fieldValue = this.getFieldValue(condition.field);
      return this.evaluateVisibilityCondition(fieldValue, condition.operator, condition.value);
    });

    // Apply logical operator
    return operator === 'AND'
      ? results.every(r => r)
      : results.some(r => r);
  }

  /**
   * Evaluate a single visibility condition
   * @param {*} fieldValue - Current field value
   * @param {string} operator - Comparison operator
   * @param {*} compareValue - Value to compare against
   * @returns {boolean} - True if condition is met
   */
  evaluateVisibilityCondition(fieldValue, operator, compareValue) {
    // Convert to string for comparison if needed
    const strValue = String(fieldValue || '').toLowerCase();
    const strCompare = String(compareValue || '').toLowerCase();

    switch (operator) {
      case 'equals':
        return fieldValue === compareValue || strValue === strCompare;

      case 'not_equals':
        return fieldValue !== compareValue && strValue !== strCompare;

      case 'contains':
        return strValue.includes(strCompare);

      case 'not_contains':
        return !strValue.includes(strCompare);

      case 'in':
        // compareValue should be an array
        if (Array.isArray(compareValue)) {
          return compareValue.includes(fieldValue) ||
                 compareValue.map(v => String(v).toLowerCase()).includes(strValue);
        }
        return false;

      case 'not_in':
        if (Array.isArray(compareValue)) {
          return !compareValue.includes(fieldValue) &&
                 !compareValue.map(v => String(v).toLowerCase()).includes(strValue);
        }
        return true;

      case 'greater_than':
        return parseFloat(fieldValue) > parseFloat(compareValue);

      case 'less_than':
        return parseFloat(fieldValue) < parseFloat(compareValue);

      case 'greater_or_equal':
        return parseFloat(fieldValue) >= parseFloat(compareValue);

      case 'less_or_equal':
        return parseFloat(fieldValue) <= parseFloat(compareValue);

      case 'is_empty':
        return !fieldValue || strValue === '';

      case 'is_not_empty':
        return fieldValue && strValue !== '';

      default:
        console.warn(`Unknown visibility operator: ${operator}`);
        return true;
    }
  }

  /**
   * Get current value of a field
   * @param {string} fieldName - Field name
   * @returns {*} - Current field value
   */
  getFieldValue(fieldName) {
    const element = this.fields.get(fieldName);
    if (!element) return null;

    if (element.type === 'checkbox') {
      return element.checked;
    } else if (element.type === 'number') {
      return element.value ? parseFloat(element.value) : null;
    } else {
      return element.value;
    }
  }

  /**
   * Update visibility for all fields based on their rules
   */
  updateAllFieldVisibility() {
    this.metadata.form.fields.forEach(fieldConfig => {
      this.updateFieldVisibility(fieldConfig);
    });
  }

  /**
   * Update visibility for a specific field
   * @param {Object} fieldConfig - Field configuration
   */
  updateFieldVisibility(fieldConfig) {
    const shouldShow = this.evaluateVisibilityRules(fieldConfig);
    const element = this.fields.get(fieldConfig.field);

    if (element) {
      // Find the form group container (parent element)
      let container = element.closest('.form-group, .mb-4, [class*="space-y"]');

      // Fallback: traverse up to find a suitable container
      if (!container) {
        container = element.parentElement;
        while (container && !container.classList.contains('form-group') &&
               !container.classList.contains('mb-4')) {
          container = container.parentElement;
          // Stop at form level
          if (container && container.tagName === 'FORM') {
            container = element.parentElement;
            break;
          }
        }
      }

      if (container) {
        container.style.display = shouldShow ? '' : 'none';

        // Mark field as hidden for validation purposes
        element.dataset.hidden = shouldShow ? 'false' : 'true';

        // Optionally disable hidden fields to prevent submission
        if (!shouldShow) {
          element.setAttribute('data-was-required', element.required);
          element.required = false;
        } else if (element.dataset.wasRequired === 'true') {
          element.required = true;
        }
      }
    }
  }

  /**
   * Set up listeners for fields that affect visibility
   */
  setupVisibilityListeners() {
    // Find all fields that have visibility rules
    const fieldsWithRules = this.metadata.form.fields.filter(f => f.visibility_rules);

    if (fieldsWithRules.length === 0) {
      return; // No visibility rules to process
    }

    // Extract all fields that are referenced in visibility conditions
    const watchedFields = new Set();
    fieldsWithRules.forEach(fieldConfig => {
      if (fieldConfig.visibility_rules && fieldConfig.visibility_rules.conditions) {
        fieldConfig.visibility_rules.conditions.forEach(condition => {
          watchedFields.add(condition.field);
        });
      }
    });

    // Add change listeners to watched fields
    watchedFields.forEach(fieldName => {
      const element = this.fields.get(fieldName);
      if (element) {
        const updateVisibility = () => {
          // Update visibility for all fields that depend on this field
          fieldsWithRules.forEach(fieldConfig => {
            if (fieldConfig.visibility_rules &&
                fieldConfig.visibility_rules.conditions.some(c => c.field === fieldName)) {
              this.updateFieldVisibility(fieldConfig);
            }
          });
        };

        element.addEventListener('change', updateVisibility);
        element.addEventListener('input', updateVisibility);
      }
    });
  }

  // ==================== Field Dependencies (Cascading Dropdowns) ====================

  /**
   * Set up listeners for fields that have dependencies (Phase 5 Week 3-4)
   * When parent field changes, reload options for dependent fields
   */
  setupFieldDependencyListeners() {
    // Find all fields that depend on other fields
    const dependentFields = this.metadata.form.fields.filter(f => f.depends_on_field);

    if (dependentFields.length === 0) {
      return; // No dependencies to process
    }

    // Group dependent fields by their parent field
    const dependencyMap = new Map();
    dependentFields.forEach(fieldConfig => {
      const parentField = fieldConfig.depends_on_field;
      if (!dependencyMap.has(parentField)) {
        dependencyMap.set(parentField, []);
      }
      dependencyMap.get(parentField).push(fieldConfig);
    });

    // Add change listeners to parent fields
    dependencyMap.forEach((dependents, parentFieldName) => {
      const parentElement = this.fields.get(parentFieldName);
      if (parentElement) {
        parentElement.addEventListener('change', async () => {
          const parentValue = this.getFieldValue(parentFieldName);

          // Update all dependent fields
          for (const dependentConfig of dependents) {
            await this.updateDependentField(dependentConfig, parentValue);
          }
        });

        // Initialize dependent fields on first load
        const initialValue = this.getFieldValue(parentFieldName);
        if (initialValue) {
          dependents.forEach(async (dependentConfig) => {
            await this.updateDependentField(dependentConfig, initialValue);
          });
        }
      }
    });
  }

  /**
   * Update a dependent field when its parent value changes
   * @param {Object} fieldConfig - Dependent field configuration
   * @param {*} parentValue - Value of parent field
   */
  async updateDependentField(fieldConfig, parentValue) {
    const element = this.fields.get(fieldConfig.field);
    if (!element) return;

    // Clear current value and options
    const currentValue = element.value;
    element.value = '';

    // Disable field while loading
    element.disabled = true;

    try {
      // Load new options based on parent value
      const options = await this.fetchDependentOptions(fieldConfig, parentValue);

      // Update select options
      if (element.tagName === 'SELECT') {
        element.innerHTML = '<option value="">Select...</option>';
        options.forEach(opt => {
          const option = document.createElement('option');
          option.value = opt.value;
          option.textContent = opt.label;
          element.appendChild(option);
        });

        // Try to restore previous value if it still exists in new options
        if (currentValue && options.some(opt => opt.value === currentValue)) {
          element.value = currentValue;
        }
      }
    } catch (error) {
      console.error(`Error updating dependent field ${fieldConfig.field}:`, error);

      // Show error in UI
      const component = this.fieldComponents.get(fieldConfig.field);
      if (component && component.setError) {
        component.setError('Failed to load options');
      }
    } finally {
      // Re-enable field
      element.disabled = false;
    }
  }

  /**
   * Fetch options for a dependent field based on parent value
   * @param {Object} fieldConfig - Dependent field configuration
   * @param {*} parentValue - Value of parent field
   * @returns {Promise<Array>} - Array of {value, label} options
   */
  async fetchDependentOptions(fieldConfig, parentValue) {
    // If reference field, fetch from entity records
    if (fieldConfig.reference_entity_id) {
      return await this.fetchReferenceOptions(fieldConfig, parentValue);
    }

    // If select field with dynamic options API
    if (fieldConfig.meta_data?.options_api) {
      return await this.fetchDynamicOptions(fieldConfig, parentValue);
    }

    // If static allowed_values with filter expression
    if (fieldConfig.allowed_values && fieldConfig.filter_expression) {
      return this.filterStaticOptions(fieldConfig, parentValue);
    }

    return [];
  }

  /**
   * Fetch reference field options filtered by parent value
   * @param {Object} fieldConfig - Field configuration
   * @param {*} parentValue - Parent field value
   * @returns {Promise<Array>} - Array of options
   */
  async fetchReferenceOptions(fieldConfig, parentValue) {
    try {
      // Build filter expression
      let filter = {};
      if (fieldConfig.filter_expression) {
        // Replace {parent_field} with actual value
        const filterKey = fieldConfig.depends_on_field;
        filter[filterKey] = parentValue;
      }

      const params = new URLSearchParams({
        limit: 100,
        ...filter
      });

      // Prefer entity name for the API call (dynamic-data API uses entity name, not UUID)
      const entityIdentifier = fieldConfig.reference_entity_name || fieldConfig.reference_entity_id;

      const response = await fetch(
        `/api/v1/dynamic-data/${entityIdentifier}/records?${params}`
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      const records = data.data || data.records || data || [];

      // Format as options
      const displayField = fieldConfig.display_field || fieldConfig.reference_field || 'name';
      return records.map(record => ({
        value: record.id,
        label: record[displayField] || record.name || record.id
      }));
    } catch (error) {
      console.error('Error fetching reference options:', error);
      return [];
    }
  }

  /**
   * Fetch dynamic options from API
   * @param {Object} fieldConfig - Field configuration
   * @param {*} parentValue - Parent field value
   * @returns {Promise<Array>} - Array of options
   */
  async fetchDynamicOptions(fieldConfig, parentValue) {
    try {
      const apiUrl = fieldConfig.meta_data.options_api;
      const params = new URLSearchParams();

      if (fieldConfig.depends_on_field) {
        params.append(fieldConfig.depends_on_field, parentValue);
      }

      const response = await fetch(`${apiUrl}?${params}`);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      return data.options || data || [];
    } catch (error) {
      console.error('Error fetching dynamic options:', error);
      return [];
    }
  }

  /**
   * Filter static options based on parent value
   * @param {Object} fieldConfig - Field configuration
   * @param {*} parentValue - Parent field value
   * @returns {Array} - Filtered options
   */
  filterStaticOptions(fieldConfig, parentValue) {
    const options = fieldConfig.allowed_values || [];

    // If options is array of strings, convert to {value, label}
    let formattedOptions = Array.isArray(options)
      ? options.map(opt => typeof opt === 'string' ? { value: opt, label: opt } : opt)
      : Object.entries(options).map(([value, label]) => ({ value, label }));

    // Apply filter expression if provided
    if (fieldConfig.filter_expression) {
      // Simple filter: check if option has matching property
      // Example: filter_expression = "country_code = '{country}'"
      formattedOptions = formattedOptions.filter(opt => {
        // Check if option metadata matches parent value
        return opt[fieldConfig.depends_on_field] === parentValue;
      });
    }

    return formattedOptions;
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
