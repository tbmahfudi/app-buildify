/**
 * upgradeSelect — convert a native <select> element into a FlexSelect component.
 *
 * Usage (single element):
 *   import { upgradeSelect, upgradeAllSelects } from './utils/upgrade-select.js';
 *   const fs = upgradeSelect(document.getElementById('my-select'));
 *
 * Usage (whole page):
 *   upgradeAllSelects(document.getElementById('content'));
 *
 * The original <select> is replaced in the DOM by:
 *   1. A hidden <input> with the same id / name / value so that any existing
 *      code that reads `document.getElementById(id).value` continues to work.
 *   2. A <div> wrapper that FlexSelect renders into.
 *
 * Dynamic option changes:
 *   The returned FlexSelect instance is attached to the hidden input as
 *   `hiddenInput._flexSelect` so callers can reach setOptions() / setValue().
 *
 * onChange compatibility:
 *   After FlexSelect fires its onChange the utility:
 *     • updates the hidden input's value
 *     • dispatches a native `change` event on the hidden input (bubbles)
 *     • executes the original `onchange` attribute string if one existed
 */

import FlexSelect from '../components/flex-select.js';

/**
 * Set options on a FlexSelect-upgraded element (or a native <select> fallback).
 * Use this in place of `select.innerHTML = ...` when the options are loaded async.
 *
 * @param {string|Element} idOrEl   — element id string or the element itself
 * @param {Array<{value,label,disabled}>} opts
 * @param {string} [placeholder]    — placeholder text (shown as first item)
 */
export function setFlexOptions(idOrEl, opts, placeholder) {
    const el = typeof idOrEl === 'string' ? document.getElementById(idOrEl) : idOrEl;
    if (!el) return;
    if (el._flexSelect) {
        el._flexSelect.setOptions(opts);
        if (placeholder !== undefined) el._flexSelect.options.placeholder = placeholder;
    } else if (el.tagName === 'SELECT') {
        el.innerHTML =
            (placeholder !== undefined ? `<option value="">${placeholder}</option>` : '') +
            opts.map(o => `<option value="${o.value}"${o.disabled ? ' disabled' : ''}>${o.label}</option>`).join('');
    }
}

/**
 * Set the current value on a FlexSelect-upgraded element (or native <select>).
 *
 * @param {string|Element} idOrEl
 * @param {string} value
 */
export function setFlexValue(idOrEl, value) {
    const el = typeof idOrEl === 'string' ? document.getElementById(idOrEl) : idOrEl;
    if (!el) return;
    if (el._flexSelect) {
        el._flexSelect.setValue(value);
        // FlexSelect.setValue does not call onChange, so the hidden input's value
        // would stay stale. Keep it in sync so that el.value reads back correctly.
        el.value = value ?? '';
    } else if (el.tagName === 'SELECT') {
        el.value = value;
    }
}

/**
 * Upgrade a single <select> element.
 *
 * @param {HTMLSelectElement} selectEl   — the element to upgrade
 * @param {Object}            overrides  — any extra FlexSelect options
 * @returns {FlexSelect}                 — the FlexSelect instance
 */
export function upgradeSelect(selectEl, overrides = {}) {
    if (!(selectEl instanceof HTMLSelectElement)) return null;

    // ── Read the native select ───────────────────────────────────────────────
    const id       = selectEl.id   || '';
    const name     = selectEl.name || '';
    const required = selectEl.required;
    const disabled = selectEl.disabled;
    const multiple = selectEl.multiple;
    const onchangeAttr = selectEl.getAttribute('onchange') || '';

    // Gather options from <option> children
    let placeholderText = 'Select...';
    const opts = [];
    for (const opt of selectEl.options) {
        if (opt.value === '' && !opt.disabled) {
            placeholderText = opt.text;   // treat empty-value option as placeholder
        } else {
            opts.push({
                value:    opt.value,
                label:    opt.text,
                disabled: opt.disabled,
            });
        }
    }

    const currentValue = (selectEl.value && selectEl.value !== '') ? selectEl.value : null;

    // ── Build replacement DOM ────────────────────────────────────────────────
    const parent = selectEl.parentNode;

    // Hidden input — keeps the same id/name so getElementById/FormData still work
    const hidden = document.createElement('input');
    hidden.type  = 'hidden';
    if (id)   hidden.id   = id;
    if (name) hidden.name = name;
    hidden.value = currentValue ?? '';

    // Copy all data-* attributes so delegated listeners using dataset still work
    for (const { name: attrName, value: attrValue } of selectEl.attributes) {
        if (attrName.startsWith('data-')) hidden.setAttribute(attrName, attrValue);
    }

    // Container div that FlexSelect renders inside
    const container = document.createElement('div');
    container.className = 'flex-select-host';

    // Copy explicit width / block classes from the select so layout is preserved
    if (selectEl.classList.contains('w-full')) container.classList.add('w-full');

    parent.insertBefore(hidden,    selectEl);
    parent.insertBefore(container, selectEl);
    parent.removeChild(selectEl);

    // ── Initialise FlexSelect ────────────────────────────────────────────────
    const fs = new FlexSelect(container, {
        options:    opts,
        value:      currentValue,
        placeholder: placeholderText,
        required,
        disabled,
        multiple,
        searchable: opts.length > 6,
        clearable:  !required,
        size:       'md',
        ...overrides,
        onChange(val) {
            hidden.value = val ?? '';
            // Dispatch native events for compatibility:
            // 'change' for addEventListener('change') callers
            // 'input' for delegated addEventListener('input') callers (e.g. form containers)
            hidden.dispatchEvent(new Event('change', { bubbles: true }));
            hidden.dispatchEvent(new Event('input',  { bubbles: true }));
            // Execute inline onchange attribute if present
            if (onchangeAttr) {
                try {
                    // eslint-disable-next-line no-new-func
                    new Function('value', `(function(){ ${onchangeAttr.replace(/this\.value/g, 'value')} })()`)(val ?? '');
                } catch (_) { /* ignore */ }
            }
            if (overrides.onChange) overrides.onChange(val);
        },
    });

    // Expose the FlexSelect instance on the hidden input for programmatic access
    hidden._flexSelect = fs;

    return fs;
}

/**
 * Upgrade every <select> found inside a root element.
 *
 * @param {Element} root       — scope to search (defaults to document.body)
 * @param {Object}  overrides  — FlexSelect option overrides applied to every select
 * @returns {Map<string, FlexSelect>}  — map of original select id → FlexSelect instance
 */
export function upgradeAllSelects(root = document.body, overrides = {}) {
    const instances = new Map();
    const selects = Array.from(root.querySelectorAll('select'));
    for (const sel of selects) {
        const origId = sel.id;
        const fs = upgradeSelect(sel, overrides);
        if (fs && origId) instances.set(origId, fs);
    }
    return instances;
}
