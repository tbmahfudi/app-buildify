/**
 * FlexProgress Component
 *
 * Progress bar and circular progress indicator with animations,
 * labels, striped/indeterminate modes, and stacked/segmented bars.
 *
 * @version 1.0.0
 */

import BaseComponent from '../core/base-component.js';

export default class FlexProgress extends BaseComponent {
    static DEFAULTS = {
        // Value
        value: 0,           // 0–max
        max: 100,
        min: 0,

        // Appearance
        variant: 'bar',     // bar | circular | segmented
        size: 'md',         // xs | sm | md | lg | xl
        color: 'blue',      // blue | green | red | amber | purple | gray | auto
        trackColor: null,   // override track (background) color class
        rounded: true,      // rounded ends on bar
        striped: false,     // diagonal stripe pattern
        animated: false,    // animate stripes (implies striped)

        // State
        indeterminate: false,  // show indeterminate animation (ignores value)

        // Labels
        showLabel: false,       // show percentage text inside/beside bar
        label: null,            // custom label string (overrides percentage)
        labelPosition: 'right', // right | inside | top | bottom (bar only)

        // Segmented variant
        segments: null,    // [{ value, color, label }] for segmented bars

        // Circular variant
        thickness: 8,      // stroke width in px
        showValue: true,   // show numeric value inside circle

        // Callbacks
        onChange: null,
    };

    static SIZES = {
        xs: { bar: 'h-1',   circle: 32,  font: 'text-xs',  stroke: 4  },
        sm: { bar: 'h-2',   circle: 48,  font: 'text-sm',  stroke: 5  },
        md: { bar: 'h-3',   circle: 64,  font: 'text-sm',  stroke: 6  },
        lg: { bar: 'h-4',   circle: 80,  font: 'text-base', stroke: 7 },
        xl: { bar: 'h-6',   circle: 104, font: 'text-lg',  stroke: 8  },
    };

    static COLORS = {
        blue:   { fill: 'bg-blue-500',   stroke: '#3b82f6' },
        green:  { fill: 'bg-green-500',  stroke: '#22c55e' },
        red:    { fill: 'bg-red-500',    stroke: '#ef4444' },
        amber:  { fill: 'bg-amber-500',  stroke: '#f59e0b' },
        purple: { fill: 'bg-purple-500', stroke: '#a855f7' },
        gray:   { fill: 'bg-gray-400',   stroke: '#9ca3af' },
    };

    constructor(element, options = {}) {
        super(element, options);
        this.state = {
            ...this.state,
            value: Math.min(Math.max(this.options.value, this.options.min), this.options.max),
        };
        this.init();
    }

    init() {
        this.render();
        this.state.initialized = true;
    }

    // ── Rendering ──────────────────────────────────────────────────────────

    render() {
        const { variant } = this.options;
        if (variant === 'circular') {
            this.container.innerHTML = this._renderCircular();
        } else if (variant === 'segmented') {
            this.container.innerHTML = this._renderSegmented();
        } else {
            this.container.innerHTML = this._renderBar();
        }
    }

    // ── Bar ────────────────────────────────────────────────────────────────

    _renderBar() {
        const { size, color, trackColor, rounded, striped, animated,
                indeterminate, showLabel, label, labelPosition } = this.options;
        const sizeConf  = FlexProgress.SIZES[size] || FlexProgress.SIZES.md;
        const colorConf = this._resolveColor(color);
        const pct       = this._pct();

        const roundedClass  = rounded ? 'rounded-full' : 'rounded-none';
        const trackBg       = trackColor || 'bg-gray-200';
        const fillClass     = colorConf.fill;
        const stripeClass   = striped || animated ? 'flex-progress-striped' : '';
        const animClass     = animated ? 'flex-progress-animated' : '';

        const labelText = label ?? `${Math.round(pct)}%`;
        const topLabel  = showLabel && labelPosition === 'top'    ? `<div class="flex justify-between mb-1"><span class="text-xs text-gray-500">${labelText}</span></div>` : '';
        const botLabel  = showLabel && labelPosition === 'bottom' ? `<div class="mt-1 text-xs text-gray-500 text-right">${labelText}</div>` : '';

        const barContent = `
            <div class="flex-progress-track relative w-full ${sizeConf.bar} ${trackBg} ${roundedClass} overflow-hidden">
                ${indeterminate
                    ? `<div class="flex-progress-indeterminate absolute inset-0 ${fillClass} ${roundedClass}"></div>`
                    : `<div class="flex-progress-fill ${fillClass} ${roundedClass} ${stripeClass} ${animClass} h-full transition-all duration-500 ease-out"
                            style="width:${pct}%"
                            role="progressbar"
                            aria-valuenow="${this.state.value}"
                            aria-valuemin="${this.options.min}"
                            aria-valuemax="${this.options.max}">
                            ${showLabel && labelPosition === 'inside' && pct > 10
                                ? `<span class="absolute inset-0 flex items-center justify-center text-white text-xs font-medium">${labelText}</span>`
                                : ''}
                       </div>`}
            </div>`;

        const rightLabel = showLabel && labelPosition === 'right'
            ? `<span class="ml-2 text-sm font-medium text-gray-700 whitespace-nowrap flex-shrink-0">${labelText}</span>` : '';

        return `
            <div class="flex-progress w-full" data-flex-progress>
                ${topLabel}
                <div class="flex items-center w-full">
                    ${barContent}
                    ${rightLabel}
                </div>
                ${botLabel}
            </div>`;
    }

    // ── Circular ───────────────────────────────────────────────────────────

    _renderCircular() {
        const { size, color, indeterminate, showValue, label, thickness } = this.options;
        const sizeConf  = FlexProgress.SIZES[size] || FlexProgress.SIZES.md;
        const colorConf = this._resolveColor(color);
        const dim       = sizeConf.circle;
        const stroke    = thickness || sizeConf.stroke;
        const r         = (dim - stroke) / 2;
        const circ      = 2 * Math.PI * r;
        const pct       = this._pct();
        const offset    = circ - (pct / 100) * circ;

        const cx = dim / 2;
        const cy = dim / 2;

        const valueText = label ?? (showValue ? `${Math.round(pct)}%` : '');

        return `
            <div class="flex-progress flex-progress--circular inline-flex flex-col items-center" data-flex-progress>
                <svg width="${dim}" height="${dim}" viewBox="0 0 ${dim} ${dim}" class="transform -rotate-90
                     ${indeterminate ? 'flex-progress-spin' : ''}">
                    <!-- Track -->
                    <circle
                        cx="${cx}" cy="${cy}" r="${r}"
                        fill="none"
                        stroke="#e5e7eb"
                        stroke-width="${stroke}"/>
                    <!-- Fill -->
                    <circle
                        class="flex-progress-circle-fill transition-all duration-500 ease-out"
                        cx="${cx}" cy="${cy}" r="${r}"
                        fill="none"
                        stroke="${colorConf.stroke}"
                        stroke-width="${stroke}"
                        stroke-linecap="round"
                        stroke-dasharray="${circ}"
                        stroke-dashoffset="${indeterminate ? circ * 0.25 : offset}"/>
                </svg>
                ${valueText ? `
                    <div class="flex-progress-value absolute inset-0 flex items-center justify-center">
                        <span class="${sizeConf.font} font-semibold text-gray-700">${valueText}</span>
                    </div>` : ''}
            </div>`;
    }

    // ── Segmented ──────────────────────────────────────────────────────────

    _renderSegmented() {
        const { size, segments, trackColor, rounded } = this.options;
        const sizeConf     = FlexProgress.SIZES[size] || FlexProgress.SIZES.md;
        const roundedClass = rounded ? 'rounded-full' : 'rounded-none';
        const trackBg      = trackColor || 'bg-gray-200';

        const segs = segments || [];
        const total = segs.reduce((s, seg) => s + (seg.value || 0), 0) || this.options.max;

        const segHtml = segs.map((seg, i) => {
            const w    = ((seg.value || 0) / total) * 100;
            const conf = this._resolveColor(seg.color || 'blue');
            const isFirst = i === 0;
            const isLast  = i === segs.length - 1;
            return `<div class="${conf.fill} h-full transition-all duration-500 ease-out
                         ${rounded && isFirst ? 'rounded-l-full' : ''}
                         ${rounded && isLast  ? 'rounded-r-full' : ''}"
                        style="width:${w}%"
                        title="${seg.label ? `${seg.label}: ${seg.value}` : seg.value}">
                   </div>`;
        }).join('');

        const legendHtml = segs.some(s => s.label) ? `
            <div class="flex flex-wrap gap-3 mt-2">
                ${segs.map(seg => {
                    const conf = this._resolveColor(seg.color || 'blue');
                    return `<div class="flex items-center gap-1.5 text-xs text-gray-600">
                        <span class="w-2.5 h-2.5 rounded-full ${conf.fill} flex-shrink-0"></span>
                        ${seg.label}${seg.value != null ? ` (${seg.value})` : ''}
                    </div>`;
                }).join('')}
            </div>` : '';

        return `
            <div class="flex-progress flex-progress--segmented w-full" data-flex-progress>
                <div class="flex w-full ${sizeConf.bar} ${trackBg} ${roundedClass} overflow-hidden gap-px">
                    ${segHtml}
                </div>
                ${legendHtml}
            </div>`;
    }

    // ── Percentage helper ──────────────────────────────────────────────────

    _pct() {
        const { min, max } = this.options;
        const range = max - min;
        if (range === 0) return 0;
        return Math.min(100, Math.max(0, ((this.state.value - min) / range) * 100));
    }

    _resolveColor(color) {
        if (color === 'auto') {
            const pct = this._pct();
            color = pct < 33 ? 'red' : pct < 67 ? 'amber' : 'green';
        }
        return FlexProgress.COLORS[color] || FlexProgress.COLORS.blue;
    }

    // ── Public API ─────────────────────────────────────────────────────────

    /**
     * Set progress value (0–max). Re-renders fill only for performance.
     */
    setValue(value) {
        const clamped = Math.min(Math.max(value, this.options.min), this.options.max);
        const prev = this.state.value;
        this.state.value = clamped;

        // Fast-path: update fill width without full re-render
        const fill = this.container.querySelector('.flex-progress-fill');
        if (fill) {
            const pct = this._pct();
            fill.style.width = `${pct}%`;
            fill.setAttribute('aria-valuenow', clamped);
            const label = this.container.querySelector('.flex-progress-fill span');
            if (label) label.textContent = this.options.label ?? `${Math.round(pct)}%`;
        }

        const circleFill = this.container.querySelector('.flex-progress-circle-fill');
        if (circleFill) {
            const sizeConf = FlexProgress.SIZES[this.options.size] || FlexProgress.SIZES.md;
            const dim = sizeConf.circle;
            const stroke = this.options.thickness || sizeConf.stroke;
            const r = (dim - stroke) / 2;
            const circ = 2 * Math.PI * r;
            circleFill.style.strokeDashoffset = String(circ - (this._pct() / 100) * circ);
            const valEl = this.container.querySelector('.flex-progress-value span');
            if (valEl) valEl.textContent = this.options.label ?? `${Math.round(this._pct())}%`;
        }

        const rightLabel = this.container.querySelector('.ml-2.text-sm');
        if (rightLabel) rightLabel.textContent = this.options.label ?? `${Math.round(this._pct())}%`;

        this.emit('change', { value: clamped, prev, pct: this._pct() });
        if (this.options.onChange) this.options.onChange(clamped, this._pct());
    }

    /** Increment value by step (default 1). */
    increment(step = 1) { this.setValue(this.state.value + step); }

    /** Decrement value by step (default 1). */
    decrement(step = 1) { this.setValue(this.state.value - step); }

    /** Reset to min. */
    reset() { this.setValue(this.options.min); }

    /** Complete to max. */
    complete() { this.setValue(this.options.max); }

    getValue() { return this.state.value; }
    getPercent() { return this._pct(); }

    /** Switch to indeterminate mode (e.g. while waiting on unknown duration). */
    setIndeterminate(val) {
        this.options.indeterminate = val;
        this.render();
    }

    /** Update color and re-render. */
    setColor(color) {
        this.options.color = color;
        this.render();
    }
}
