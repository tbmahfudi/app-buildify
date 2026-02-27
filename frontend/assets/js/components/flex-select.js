/**
 * FlexSelect Component
 *
 * Dropdown select field with search, multi-select, and custom rendering
 *
 * @author Claude Code
 * @version 1.0.0
 */

import BaseComponent from '../core/base-component.js';

export default class FlexSelect extends BaseComponent {
    /**
     * Default configuration
     */
    static DEFAULTS = {
        label: null,
        labelPosition: 'top',       // top | floating
        placeholder: 'Select an option',
        value: null,                // Single value or array for multi
        multiple: false,
        searchable: true,
        clearable: true,
        disabled: false,
        required: false,
        size: 'md',                 // sm | md | lg
        variant: 'outlined',        // outlined | filled
        options: [],                // Array of { value, label, disabled, group }
        maxHeight: '300px',
        helperText: null,
        errorMessage: null,
        noOptionsText: 'No options found',
        noSearchResultsText: 'No results found',
        loadingText: 'Loading...',
        loading: false,
        prefixIcon: null,
        classes: [],
        inputClasses: [],
        onChange: null,
        onSearch: null,
        onOpen: null,
        onClose: null
    };

    /**
     * Size mappings
     */
    static SIZES = {
        sm: { input: 'px-3 py-1.5 text-sm', option: 'px-3 py-1.5 text-sm' },
        md: { input: 'px-4 py-2 text-base', option: 'px-4 py-2 text-base' },
        lg: { input: 'px-4 py-3 text-lg', option: 'px-4 py-3 text-lg' }
    };

    constructor(element, options = {}) {
        super(element, options);

        this.state = {
            value: this.options.multiple
                ? (Array.isArray(this.options.value) ? this.options.value : [])
                : this.options.value,
            isOpen: false,
            searchQuery: '',
            focusedIndex: -1,
            touched: false
        };

        this.selectElement = null;
        this.dropdownElement = null;
        this.searchInput = null;

        this.init();
    }

    /**
     * Initialize component
     */
    init() {
        this.render();
        this.attachEventListeners();
        this.emit('init');
    }

    /**
     * Render component
     */
    render() {
        const wrapper = this.createWrapper();
        const label = this.createLabel();
        const selectBox = this.createSelectBox();
        const dropdown = this.createDropdown();
        const message = this.createMessage();

        if (label) wrapper.appendChild(label);
        wrapper.appendChild(selectBox);
        wrapper.appendChild(dropdown);
        if (message) wrapper.appendChild(message);

        this.element.innerHTML = '';
        this.element.appendChild(wrapper);

        this.dropdownElement = dropdown;

        // Re-align the panel whenever the DOM is rebuilt while open, e.g. after
        // setOptions() / setValue() are called while the dropdown is visible.
        if (this.state.isOpen) {
            this._alignDropdown();
        }

        this.emit('render');
    }

    /**
     * Create wrapper
     */
    createWrapper() {
        const wrapper = document.createElement('div');
        // No `relative` here intentionally: the dropdown uses `absolute` positioning
        // and needs its containing block to be the modal dialog wrapper (which sits
        // *above* the modal body's `overflow-y: auto`).  If we put `relative` on this
        // wrapper the containing block falls inside the overflow container and the
        // dropdown gets clipped.
        wrapper.className = `flex-select-wrapper space-y-1.5 ${this.options.classes.join(' ')}`;
        return wrapper;
    }

    /**
     * Create label
     */
    createLabel() {
        if (!this.options.label) return null;

        const label = document.createElement('label');
        label.className = 'flex-select-label font-medium text-gray-700 text-sm';
        label.textContent = this.options.label;

        if (this.options.required) {
            const asterisk = document.createElement('span');
            asterisk.className = 'text-red-500 ml-1';
            asterisk.textContent = '*';
            label.appendChild(asterisk);
        }

        return label;
    }

    /**
     * Create select box (trigger)
     */
    createSelectBox() {
        const box = document.createElement('div');
        const sizeClasses = FlexSelect.SIZES[this.options.size].input;

        box.className = `flex-select-box relative ${sizeClasses} w-full border rounded-lg cursor-pointer transition-colors focus:outline-none focus:ring-2`;

        if (this.options.variant === 'outlined') {
            box.className += ' border-gray-300 bg-white focus:border-indigo-500 focus:ring-indigo-200';
        } else {
            box.className += ' border-transparent bg-gray-100 focus:bg-white focus:border-indigo-500 focus:ring-indigo-200';
        }

        if (this.options.disabled) {
            box.className += ' opacity-50 cursor-not-allowed bg-gray-50';
        }

        // Display value
        const display = document.createElement('div');
        display.className = 'flex items-center justify-between gap-2';

        const valueText = document.createElement('span');
        valueText.className = 'flex-1 truncate';
        valueText.textContent = this.getDisplayText();

        const icons = document.createElement('div');
        icons.className = 'flex items-center gap-1';

        if (this.options.clearable && this.state.value !== null && this.state.value?.length > 0) {
            const clearBtn = document.createElement('button');
            clearBtn.type = 'button';
            clearBtn.className = 'text-gray-400 hover:text-gray-600';
            clearBtn.innerHTML = '<i class="ph ph-x text-sm"></i>';
            clearBtn.onclick = (e) => {
                e.stopPropagation();
                this.clear();
            };
            icons.appendChild(clearBtn);
        }

        const chevron = document.createElement('i');
        chevron.className = `ph ph-caret-down text-gray-400 transition-transform ${this.state.isOpen ? 'rotate-180' : ''}`;
        icons.appendChild(chevron);

        display.appendChild(valueText);
        display.appendChild(icons);
        box.appendChild(display);

        box.tabIndex = this.options.disabled ? -1 : 0;

        return box;
    }

    /**
     * Create dropdown
     */
    createDropdown() {
        const dropdown = document.createElement('div');
        // `absolute` positions relative to the nearest `position:relative` ancestor.
        // With no `relative` on the wrapper that ancestor is the modal dialog wrapper,
        // which is ABOVE the modal body's `overflow-y:auto` — so the panel is never
        // clipped.  z-index 1100 exceeds FlexModal's stack (base 1000, first modal 1001).
        // left / top / width are set dynamically by _alignDropdown() so the panel
        // always matches the trigger box regardless of its position in the page.
        //
        // `overflow: hidden` (both axes) is intentional: it clips child backgrounds
        // to the rounded-lg corners in ALL browsers.  Firefox does NOT clip to
        // border-radius when only overflow-y is non-visible; Chrome does.  Using
        // `overflow: hidden` on the outer shell and a separate inner scroller div
        // gives consistent corner clipping everywhere.
        dropdown.className = `flex-select-dropdown absolute overflow-hidden bg-white border border-gray-300 rounded-lg shadow-lg ${this.state.isOpen ? '' : 'hidden'}`;
        dropdown.style.zIndex = '1100';
        // The wrapper uses `space-y-1.5` which would add margin-top to every
        // non-first child, including this absolutely-positioned panel.  For
        // absolute elements `top` positions the *margin-box* edge, so that
        // margin stacks on top of the JS gap set by _alignDropdown().  Zero it.
        dropdown.style.marginTop = '0';

        if (this.options.searchable) {
            const searchBox = this.createSearchBox();
            dropdown.appendChild(searchBox);
        }

        // Scrolling lives in an inner container so the outer dropdown can use
        // `overflow: hidden` for proper border-radius clipping without losing
        // the ability to scroll long option lists.
        const scroller = document.createElement('div');
        scroller.className = 'flex-select-scroller';
        scroller.style.overflowY = 'auto';
        scroller.style.maxHeight = this.options.maxHeight;

        const optionsList = this.createOptionsList();
        scroller.appendChild(optionsList);
        dropdown.appendChild(scroller);

        return dropdown;
    }

    /**
     * Create search box
     */
    createSearchBox() {
        const searchBox = document.createElement('div');
        searchBox.className = 'p-2 border-b border-gray-200';

        this.searchInput = document.createElement('input');
        this.searchInput.type = 'text';
        this.searchInput.className = 'w-full px-3 py-2 text-sm border border-gray-300 rounded focus:outline-none focus:border-indigo-500';
        this.searchInput.placeholder = 'Search...';
        this.searchInput.value = this.state.searchQuery;

        searchBox.appendChild(this.searchInput);
        return searchBox;
    }

    /**
     * Create options list
     */
    createOptionsList() {
        const list = document.createElement('div');
        list.className = 'flex-select-options w-full';

        const filtered = this.getFilteredOptions();

        if (this.options.loading) {
            list.innerHTML = `<div class="px-4 py-3 text-sm text-gray-500">${this.options.loadingText}</div>`;
        } else if (filtered.length === 0) {
            const noResults = this.state.searchQuery ? this.options.noSearchResultsText : this.options.noOptionsText;
            list.innerHTML = `<div class="px-4 py-3 text-sm text-gray-500">${noResults}</div>`;
        } else {
            filtered.forEach((option, index) => {
                const optionEl = this.createOption(option, index);
                list.appendChild(optionEl);
            });
        }

        return list;
    }

    /**
     * Create single option
     */
    createOption(option, index) {
        const optionEl = document.createElement('div');
        const sizeClasses = FlexSelect.SIZES[this.options.size].option;

        optionEl.className = `flex-select-option w-full block ${sizeClasses} cursor-pointer hover:bg-indigo-50 ${option.disabled ? 'opacity-50 cursor-not-allowed' : ''}`;
        optionEl.dataset.value = option.value;
        optionEl.dataset.index = index;

        if (this.isSelected(option.value)) {
            optionEl.className += ' bg-indigo-100 font-medium';
        }

        if (index === this.state.focusedIndex) {
            optionEl.className += ' bg-gray-100';
        }

        if (this.options.multiple) {
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.className = 'mr-2';
            checkbox.checked = this.isSelected(option.value);
            checkbox.disabled = option.disabled;
            optionEl.appendChild(checkbox);
        }

        const label = document.createElement('span');
        label.textContent = option.label;
        optionEl.appendChild(label);

        return optionEl;
    }

    /**
     * Create message
     */
    createMessage() {
        if (this.options.helperText) {
            const msg = document.createElement('div');
            msg.className = 'text-sm text-gray-500';
            msg.textContent = this.options.helperText;
            return msg;
        }
        return null;
    }

    /**
     * Attach event listeners
     */
    attachEventListeners() {
        const box = this.element.querySelector('.flex-select-box');
        if (!box) return;

        // stopPropagation prevents the triggering click from bubbling to the
        // document outside-click handler, which would otherwise see the now-detached
        // old box element (replaced by render()) as "outside" and close immediately.
        box.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggle();
        });
        box.addEventListener('keydown', (e) => this.handleKeyDown(e));

        if (this.searchInput) {
            this.searchInput.addEventListener('input', (e) => {
                this.state.searchQuery = e.target.value;
                this.updateDropdown();
                if (this.options.onSearch) {
                    this.options.onSearch(this.state.searchQuery);
                }
            });
            this.searchInput.addEventListener('keydown', (e) => this.handleKeyDown(e));
        }

        // Close on outside click — stored reference so it is removed and re-added
        // on each render(), keeping exactly one active listener at a time.
        if (this._docClickHandler) {
            document.removeEventListener('click', this._docClickHandler);
        }
        this._docClickHandler = (e) => {
            if (!this.element.contains(e.target)) {
                this.close();
            }
        };
        document.addEventListener('click', this._docClickHandler);

        // Option clicks
        this.element.addEventListener('click', (e) => {
            const option = e.target.closest('.flex-select-option');
            if (option && !option.classList.contains('opacity-50')) {
                this.selectOption(option.dataset.value);
            }
        });
    }

    /**
     * Handle keyboard navigation
     */
    handleKeyDown(e) {
        if (this.options.disabled) return;

        switch(e.key) {
            case 'Enter':
            case ' ':
                if (!this.state.isOpen) {
                    e.preventDefault();
                    this.open();
                } else if (this.state.focusedIndex >= 0) {
                    e.preventDefault();
                    const filtered = this.getFilteredOptions();
                    this.selectOption(filtered[this.state.focusedIndex].value);
                }
                break;
            case 'Escape':
                e.preventDefault();
                this.close();
                break;
            case 'ArrowDown':
                e.preventDefault();
                if (!this.state.isOpen) {
                    this.open();
                } else {
                    const filtered = this.getFilteredOptions();
                    this.state.focusedIndex = Math.min(this.state.focusedIndex + 1, filtered.length - 1);
                    this.updateDropdown();
                }
                break;
            case 'ArrowUp':
                e.preventDefault();
                if (this.state.isOpen) {
                    this.state.focusedIndex = Math.max(this.state.focusedIndex - 1, 0);
                    this.updateDropdown();
                }
                break;
        }
    }

    /**
     * Get display text
     */
    getDisplayText() {
        if (this.options.multiple) {
            if (!this.state.value || this.state.value.length === 0) {
                return this.options.placeholder;
            }
            const selected = this.options.options.filter(opt =>
                this.state.value.includes(opt.value)
            );
            return selected.map(opt => opt.label).join(', ');
        } else {
            if (this.state.value === null || this.state.value === undefined) {
                return this.options.placeholder;
            }
            const selected = this.options.options.find(opt => opt.value === this.state.value);
            return selected ? selected.label : this.options.placeholder;
        }
    }

    /**
     * Get filtered options
     */
    getFilteredOptions() {
        if (!this.state.searchQuery) {
            return this.options.options;
        }
        const query = this.state.searchQuery.toLowerCase();
        return this.options.options.filter(opt =>
            opt.label.toLowerCase().includes(query)
        );
    }

    /**
     * Check if option is selected
     */
    isSelected(value) {
        if (this.options.multiple) {
            return this.state.value && this.state.value.includes(value);
        }
        return this.state.value === value;
    }

    /**
     * Select option
     */
    selectOption(value) {
        if (this.options.multiple) {
            const current = this.state.value || [];
            if (current.includes(value)) {
                this.state.value = current.filter(v => v !== value);
            } else {
                this.state.value = [...current, value];
            }
        } else {
            this.state.value = value;
            this.close();
        }

        this.state.touched = true;
        this.render();
        this.attachEventListeners();
        this.emit('change', { value: this.state.value });

        if (this.options.onChange) {
            this.options.onChange(this.state.value);
        }
    }

    /**
     * Align the dropdown panel to the trigger box.
     *
     * The dropdown is `position:absolute` whose containing block is the nearest
     * `position:relative` ancestor (typically the modal dialog wrapper).  We use
     * getBoundingClientRect() on both the trigger box and that containing block
     * (via offsetParent) to compute the correct left / top / width so the panel
     * sits directly below the trigger regardless of where it is in the page.
     */
    _alignDropdown() {
        const box = this.element.querySelector('.flex-select-box');
        const dropdown = this.element.querySelector('.flex-select-dropdown');
        if (!box || !dropdown) return;

        const boxRect = box.getBoundingClientRect();
        // offsetParent is the element's containing block (first non-static ancestor).
        const cb = dropdown.offsetParent || document.body;
        const cbRect = cb.getBoundingClientRect();

        dropdown.style.left  = `${boxRect.left  - cbRect.left + cb.scrollLeft}px`;
        dropdown.style.top   = `${boxRect.bottom - cbRect.top  + cb.scrollTop  + 4}px`;
        dropdown.style.width = `${boxRect.width}px`;
        dropdown.style.right = 'auto';
    }

    /**
     * Open dropdown
     */
    open() {
        if (this.options.disabled || this.state.isOpen) return;

        this.state.isOpen = true;
        this.state.focusedIndex = -1;
        this.render();
        this.attachEventListeners();
        this._alignDropdown();

        if (this.searchInput) {
            this.searchInput.focus();
        }

        this.emit('open');
        if (this.options.onOpen) {
            this.options.onOpen();
        }
    }

    /**
     * Close dropdown
     */
    close() {
        if (!this.state.isOpen) return;

        this.state.isOpen = false;
        this.state.searchQuery = '';
        this.render();
        this.attachEventListeners();

        this.emit('close');
        if (this.options.onClose) {
            this.options.onClose();
        }
    }

    /**
     * Toggle dropdown
     */
    toggle() {
        if (this.state.isOpen) {
            this.close();
        } else {
            this.open();
        }
    }

    /**
     * Update dropdown content
     */
    updateDropdown() {
        const dropdown = this.element.querySelector('.flex-select-dropdown');
        if (!dropdown) return;

        const newOptionsList = this.createOptionsList();
        const oldOptionsList = dropdown.querySelector('.flex-select-options');
        if (oldOptionsList) {
            // Replace within the actual parent (may be the inner scroller, not
            // the dropdown directly) so the nesting stays correct.
            oldOptionsList.parentNode.replaceChild(newOptionsList, oldOptionsList);
        }
    }

    /**
     * Clear selection
     */
    clear() {
        this.state.value = this.options.multiple ? [] : null;
        this.state.touched = true;
        this.render();
        this.attachEventListeners();
        this.emit('clear');
        this.emit('change', { value: this.state.value });

        if (this.options.onChange) {
            this.options.onChange(this.state.value);
        }
    }

    /**
     * Get value
     */
    getValue() {
        return this.state.value;
    }

    /**
     * Set value
     */
    setValue(value) {
        this.state.value = value;
        this.render();
        this.attachEventListeners();
        this.emit('change', { value });
    }

    /**
     * Set options
     */
    setOptions(options) {
        this.options.options = options;
        this.render();
        this.attachEventListeners();
    }

    /**
     * Set disabled
     */
    setDisabled(disabled) {
        this.options.disabled = disabled;
        this.render();
        this.attachEventListeners();
    }

    /**
     * Destroy component
     */
    destroy() {
        if (this._docClickHandler) {
            document.removeEventListener('click', this._docClickHandler);
        }
        super.destroy();
    }
}
