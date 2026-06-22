/**
 * FlexDatepicker Component
 *
 * Date/datetime picker with calendar UI, keyboard navigation, and range support.
 *
 * @version 1.0.0
 */

import BaseComponent from '../core/base-component.js';

export default class FlexDatepicker extends BaseComponent {
    static DEFAULTS = {
        label: null,
        placeholder: 'Select date…',
        value: null,           // ISO date string or null
        minDate: null,
        maxDate: null,
        format: 'YYYY-MM-DD',  // display format
        mode: 'date',          // date | datetime | month | year
        firstDayOfWeek: 1,     // 0=Sun, 1=Mon
        clearable: true,
        disabled: false,
        readonly: false,
        required: false,
        size: 'md',
        variant: 'outlined',
        helperText: null,
        errorMessage: null,
        inline: false,         // render calendar inline (no popup)
        onChange: null,
        onOpen: null,
        onClose: null,
    };

    static SIZES = {
        sm: 'px-3 py-1.5 text-sm',
        md: 'px-4 py-2 text-base',
        lg: 'px-4 py-3 text-lg',
    };

    static MONTH_NAMES = [
        'January','February','March','April','May','June',
        'July','August','September','October','November','December',
    ];

    static DAY_NAMES_SHORT = ['Su','Mo','Tu','We','Th','Fr','Sa'];

    constructor(element, options = {}) {
        super(element, options);
        const v = this.options.value;
        this.state = {
            ...this.state,
            value: v ? new Date(v) : null,
            open: this.options.inline,
            viewYear: null,
            viewMonth: null,
        };
        const ref = this.state.value || new Date();
        this.state.viewYear  = ref.getFullYear();
        this.state.viewMonth = ref.getMonth();
        this.init();
    }

    init() {
        this.render();
        this._bindEvents();
        this.state.initialized = true;
    }

    // ── Rendering ──────────────────────────────────────────────────────────

    render() {
        const { label, disabled, required, helperText, errorMessage, inline, size, variant } = this.options;
        const inputSize = FlexDatepicker.SIZES[size] || FlexDatepicker.SIZES.md;
        const displayVal = this._formatDate(this.state.value);

        const variantClass = variant === 'filled'
            ? 'bg-gray-100 border-transparent focus-within:bg-white'
            : variant === 'underlined'
                ? 'border-0 border-b-2 rounded-none bg-transparent'
                : 'bg-white border-gray-300';

        this.container.innerHTML = `
            <div class="flex-datepicker relative w-full" data-flex-datepicker>
                ${label ? `<label class="block text-sm font-medium text-gray-700 mb-1">
                    ${label}${required ? ' <span class="text-red-500">*</span>' : ''}
                </label>` : ''}

                <div class="flex-dp-trigger flex items-center border rounded-lg transition-colors
                            ${variantClass} ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                            focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-blue-500">
                    <i class="ph ph-calendar-blank ml-3 text-gray-400 flex-shrink-0"></i>
                    <input type="text"
                        class="flex-dp-input flex-1 bg-transparent outline-none ${inputSize} text-gray-900 placeholder-gray-400"
                        placeholder="${this.options.placeholder}"
                        value="${displayVal}"
                        readonly
                        ${disabled ? 'disabled' : ''}
                        aria-haspopup="true"
                        aria-expanded="${this.state.open}">
                    ${this.options.clearable && displayVal ? `
                        <button class="flex-dp-clear mr-2 text-gray-400 hover:text-gray-600 p-1" aria-label="Clear">
                            <i class="ph ph-x text-sm"></i>
                        </button>` : '<span class="mr-3"></span>'}
                </div>

                ${helperText && !errorMessage ? `<p class="mt-1 text-xs text-gray-500">${helperText}</p>` : ''}
                ${errorMessage ? `<p class="mt-1 text-xs text-red-500">${errorMessage}</p>` : ''}

                ${!inline ? `<div class="flex-dp-popup absolute z-50 mt-1 bg-white rounded-xl shadow-xl border border-gray-200 w-72
                                          ${this.state.open ? '' : 'hidden'}">
                    ${this._renderCalendar()}
                </div>` : `<div class="flex-dp-popup mt-2 bg-white rounded-xl border border-gray-200 w-72">
                    ${this._renderCalendar()}
                </div>`}
            </div>`;

        this.elements.trigger = this.container.querySelector('.flex-dp-trigger');
        this.elements.input   = this.container.querySelector('.flex-dp-input');
        this.elements.popup   = this.container.querySelector('.flex-dp-popup');
        this.elements.clear   = this.container.querySelector('.flex-dp-clear');
    }

    _renderCalendar() {
        const { viewYear, viewMonth } = this.state;
        const today   = new Date();
        const selDate = this.state.value;

        const firstDay = new Date(viewYear, viewMonth, 1).getDay();
        const offset   = (firstDay - this.options.firstDayOfWeek + 7) % 7;
        const daysInMonth = new Date(viewYear, viewMonth + 1, 0).getDate();

        // Day headers rotated by firstDayOfWeek
        const dayNames = FlexDatepicker.DAY_NAMES_SHORT;
        const rotated  = [...dayNames.slice(this.options.firstDayOfWeek), ...dayNames.slice(0, this.options.firstDayOfWeek)];

        let cells = '';
        for (let i = 0; i < offset; i++) cells += '<div></div>';
        for (let d = 1; d <= daysInMonth; d++) {
            const date    = new Date(viewYear, viewMonth, d);
            const isToday = this._sameDay(date, today);
            const isSel   = selDate && this._sameDay(date, selDate);
            const isMin   = this.options.minDate && date < new Date(this.options.minDate);
            const isMax   = this.options.maxDate && date > new Date(this.options.maxDate);
            const disabled = isMin || isMax;
            cells += `<button
                class="flex-dp-day w-9 h-9 rounded-full text-sm transition flex items-center justify-center
                       ${isSel ? 'bg-blue-600 text-white font-semibold' : isToday ? 'border border-blue-400 text-blue-600' : 'text-gray-700 hover:bg-blue-50'}
                       ${disabled ? 'opacity-30 cursor-not-allowed' : ''}"
                data-date="${viewYear}-${String(viewMonth+1).padStart(2,'0')}-${String(d).padStart(2,'0')}"
                ${disabled ? 'disabled' : ''}>${d}</button>`;
        }

        return `
            <div class="flex-dp-calendar p-3">
                <div class="flex items-center justify-between mb-3">
                    <button class="flex-dp-prev p-1.5 rounded-lg hover:bg-gray-100 text-gray-600">
                        <i class="ph ph-caret-left"></i>
                    </button>
                    <button class="flex-dp-header text-sm font-semibold text-gray-800 hover:text-blue-600 px-2 py-1 rounded">
                        ${FlexDatepicker.MONTH_NAMES[viewMonth]} ${viewYear}
                    </button>
                    <button class="flex-dp-next p-1.5 rounded-lg hover:bg-gray-100 text-gray-600">
                        <i class="ph ph-caret-right"></i>
                    </button>
                </div>
                <div class="grid grid-cols-7 gap-0.5 mb-1">
                    ${rotated.map(d => `<div class="w-9 h-7 flex items-center justify-center text-xs text-gray-400 font-medium">${d}</div>`).join('')}
                </div>
                <div class="grid grid-cols-7 gap-0.5">
                    ${cells}
                </div>
                <div class="mt-2 pt-2 border-t flex justify-between">
                    <button class="flex-dp-today text-xs text-blue-600 hover:underline px-2 py-1">Today</button>
                    ${this.options.clearable ? '<button class="flex-dp-clear-cal text-xs text-gray-400 hover:text-gray-600 px-2 py-1">Clear</button>' : ''}
                </div>
            </div>`;
    }

    _refreshPopup() {
        const popup = this.container.querySelector('.flex-dp-popup');
        if (popup) popup.innerHTML = this._renderCalendar();
        this._bindCalendarEvents();
    }

    // ── Events ─────────────────────────────────────────────────────────────

    _bindEvents() {
        const trigger = this.container.querySelector('.flex-dp-trigger');
        if (trigger && !this.options.inline) {
            trigger.addEventListener('click', (e) => {
                if (this.options.disabled) return;
                if (e.target.closest('.flex-dp-clear')) return;
                this._toggle();
            });
        }

        const clearBtn = this.container.querySelector('.flex-dp-clear');
        if (clearBtn) clearBtn.addEventListener('click', (e) => { e.stopPropagation(); this._clear(); });

        // Close on outside click
        if (!this.options.inline) {
            this._outsideHandler = (e) => {
                if (!this.container.contains(e.target)) this._close();
            };
            document.addEventListener('click', this._outsideHandler);
        }

        this._bindCalendarEvents();
    }

    _bindCalendarEvents() {
        const popup = this.container.querySelector('.flex-dp-popup');
        if (!popup) return;

        popup.querySelector('.flex-dp-prev')?.addEventListener('click', () => this._prevMonth());
        popup.querySelector('.flex-dp-next')?.addEventListener('click', () => this._nextMonth());
        popup.querySelector('.flex-dp-today')?.addEventListener('click', () => this._selectDate(new Date()));
        popup.querySelector('.flex-dp-clear-cal')?.addEventListener('click', () => this._clear());

        popup.querySelectorAll('.flex-dp-day').forEach(btn => {
            btn.addEventListener('click', () => {
                const [y, m, d] = btn.dataset.date.split('-').map(Number);
                this._selectDate(new Date(y, m - 1, d));
            });
        });
    }

    // ── State helpers ──────────────────────────────────────────────────────

    _toggle() { this.state.open ? this._close() : this._open(); }

    _open() {
        this.state.open = true;
        const popup = this.container.querySelector('.flex-dp-popup');
        if (popup) popup.classList.remove('hidden');
        this.emit('open', { value: this.state.value });
        
    }

    _close() {
        this.state.open = false;
        const popup = this.container.querySelector('.flex-dp-popup');
        if (popup) popup.classList.add('hidden');
        this.emit('close', { value: this.state.value });
        
    }

    _selectDate(date) {
        this.state.value = date;
        this.state.viewYear  = date.getFullYear();
        this.state.viewMonth = date.getMonth();
        const input = this.container.querySelector('.flex-dp-input');
        if (input) input.value = this._formatDate(date);
        this._refreshPopup();
        if (!this.options.inline) this._close();
        this.emit('change', { value: date, formatted: this._formatDate(date) });
        
    }

    _clear() {
        this.state.value = null;
        const input = this.container.querySelector('.flex-dp-input');
        if (input) input.value = '';
        this._refreshPopup();
        this.emit('change', { value: null, formatted: null });
        
    }

    _prevMonth() {
        if (this.state.viewMonth === 0) { this.state.viewMonth = 11; this.state.viewYear--; }
        else this.state.viewMonth--;
        this._refreshPopup();
    }

    _nextMonth() {
        if (this.state.viewMonth === 11) { this.state.viewMonth = 0; this.state.viewYear++; }
        else this.state.viewMonth++;
        this._refreshPopup();
    }

    // ── Public API ─────────────────────────────────────────────────────────

    getValue() { return this.state.value; }

    setValue(date) {
        const d = date ? new Date(date) : null;
        this.state.value = d;
        if (d) { this.state.viewYear = d.getFullYear(); this.state.viewMonth = d.getMonth(); }
        const input = this.container.querySelector('.flex-dp-input');
        if (input) input.value = this._formatDate(d);
        this._refreshPopup();
    }

    setError(msg) { this.options.errorMessage = msg; this.render(); this._bindEvents(); }
    clearError()  { this.options.errorMessage = null; this.render(); this._bindEvents(); }

    // ── Utilities ──────────────────────────────────────────────────────────

    _formatDate(date) {
        if (!date) return '';
        const y = date.getFullYear();
        const m = String(date.getMonth() + 1).padStart(2, '0');
        const d = String(date.getDate()).padStart(2, '0');
        return this.options.format
            .replace('YYYY', y).replace('MM', m).replace('DD', d);
    }

    _sameDay(a, b) {
        return a.getFullYear() === b.getFullYear() &&
               a.getMonth()    === b.getMonth()    &&
               a.getDate()     === b.getDate();
    }

    destroy() {
        if (this._outsideHandler) document.removeEventListener('click', this._outsideHandler);
        super.destroy();
    }
}
