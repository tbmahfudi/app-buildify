/**
 * FlexNotification Component
 *
 * Full-featured notification/toast system with stacking, positioning,
 * progress bars, actions, and persistent notifications.
 *
 * Distinct from ui-utils showToast (which is a quick one-liner).
 * Use FlexNotification when you need actions, persistence, or custom positioning.
 *
 * @version 1.0.0
 *
 * Usage (singleton):
 *   import FlexNotification from './components/flex-notification.js';
 *   const notify = FlexNotification.getInstance();
 *   notify.show({ title: 'Saved', message: 'Changes saved.', type: 'success' });
 *   notify.success('Done!');
 *   notify.error('Something went wrong', { persistent: true });
 */

export default class FlexNotification {
    static _instance = null;

    static DEFAULTS = {
        position: 'top-right',   // top-right | top-left | top-center | bottom-right | bottom-left | bottom-center
        maxVisible: 5,
        defaultDuration: 5000,   // ms; 0 = persistent
        gap: 8,                  // px between toasts
        zIndex: 9999,
    };

    static TYPES = {
        success: {
            icon: 'ph-check-circle',
            bg: 'bg-white',
            border: 'border-green-400',
            iconColor: 'text-green-500',
            titleColor: 'text-gray-900',
        },
        error: {
            icon: 'ph-warning-circle',
            bg: 'bg-white',
            border: 'border-red-400',
            iconColor: 'text-red-500',
            titleColor: 'text-gray-900',
        },
        warning: {
            icon: 'ph-warning',
            bg: 'bg-white',
            border: 'border-amber-400',
            iconColor: 'text-amber-500',
            titleColor: 'text-gray-900',
        },
        info: {
            icon: 'ph-info',
            bg: 'bg-white',
            border: 'border-blue-400',
            iconColor: 'text-blue-500',
            titleColor: 'text-gray-900',
        },
        loading: {
            icon: 'ph-spinner-gap',
            bg: 'bg-white',
            border: 'border-gray-300',
            iconColor: 'text-gray-500',
            titleColor: 'text-gray-900',
        },
    };

    // ── Singleton ──────────────────────────────────────────────────────────

    static getInstance(options = {}) {
        if (!FlexNotification._instance) {
            FlexNotification._instance = new FlexNotification(options);
        }
        return FlexNotification._instance;
    }

    static resetInstance() {
        if (FlexNotification._instance) {
            FlexNotification._instance._container?.remove();
            FlexNotification._instance = null;
        }
    }

    // ── Constructor ────────────────────────────────────────────────────────

    constructor(options = {}) {
        this.options = { ...FlexNotification.DEFAULTS, ...options };
        this._notifications = new Map();  // id -> { el, timer, opts }
        this._counter = 0;
        this._container = this._createContainer();
        document.body.appendChild(this._container);
    }

    // ── Container ──────────────────────────────────────────────────────────

    _createContainer() {
        const el = document.createElement('div');
        el.className = `flex-notification-container fixed flex flex-col pointer-events-none`;
        el.style.zIndex = this.options.zIndex;
        this._applyPosition(el);
        return el;
    }

    _applyPosition(el) {
        const pos = this.options.position;
        const isBottom = pos.startsWith('bottom');
        const isCenter = pos.endsWith('center');
        const isLeft   = pos.endsWith('left');

        el.style.top    = isBottom ? 'auto' : '1rem';
        el.style.bottom = isBottom ? '1rem' : 'auto';
        el.style.left   = isCenter ? '50%'  : isLeft ? '1rem' : 'auto';
        el.style.right  = isCenter ? 'auto' : isLeft ? 'auto' : '1rem';
        el.style.transform     = isCenter ? 'translateX(-50%)' : 'none';
        el.style.alignItems    = isCenter ? 'center' : isLeft ? 'flex-start' : 'flex-end';
        el.style.flexDirection = isBottom ? 'column-reverse' : 'column';
        el.style.gap           = `${this.options.gap}px`;
        el.style.width         = isCenter ? 'max-content' : 'auto';
        el.style.maxWidth      = '420px';
    }

    // ── Show ───────────────────────────────────────────────────────────────

    /**
     * Show a notification.
     * @param {Object} opts
     * @param {string} opts.message      - Main message text (required)
     * @param {string} [opts.title]      - Bold title line
     * @param {string} [opts.type]       - success|error|warning|info|loading
     * @param {number} [opts.duration]   - ms before auto-dismiss; 0 = persistent
     * @param {boolean} [opts.persistent] - Alias for duration=0
     * @param {boolean} [opts.showProgress] - Show countdown progress bar
     * @param {Array}  [opts.actions]    - [{ label, onClick, variant }]
     * @param {string} [opts.id]         - Custom ID for update/dismiss by id
     * @returns {string} notification id
     */
    show(opts = {}) {
        const id   = opts.id || `notif_${++this._counter}`;
        const type = opts.type || 'info';
        const duration = opts.persistent ? 0 : (opts.duration ?? this.options.defaultDuration);
        const style = FlexNotification.TYPES[type] || FlexNotification.TYPES.info;
        const isLoading = type === 'loading';

        // Enforce maxVisible — dismiss oldest
        if (this._notifications.size >= this.options.maxVisible) {
            const oldestId = this._notifications.keys().next().value;
            this.dismiss(oldestId);
        }

        // If id already exists, update it
        if (this._notifications.has(id)) {
            this.update(id, opts);
            return id;
        }

        const el = document.createElement('div');
        el.className = `flex-notif pointer-events-auto w-full max-w-sm rounded-xl shadow-lg border-l-4
                        ${style.bg} ${style.border} overflow-hidden
                        transform transition-all duration-300`;
        el.dataset.notifId = id;
        el.style.opacity = '0';
        el.style.transform = 'translateX(100%)';

        const actions = opts.actions || [];
        const actionsHtml = actions.length ? `
            <div class="flex gap-2 mt-2 pt-2 border-t border-gray-100">
                ${actions.map((a, i) => `
                    <button class="flex-notif-action text-xs font-medium px-3 py-1.5 rounded-lg transition
                                   ${a.variant === 'danger'  ? 'bg-red-100 text-red-700 hover:bg-red-200' :
                                     a.variant === 'primary' ? 'bg-blue-600 text-white hover:bg-blue-700' :
                                                                'bg-gray-100 text-gray-700 hover:bg-gray-200'}"
                            data-action-index="${i}">
                        ${a.label}
                    </button>`).join('')}
            </div>` : '';

        el.innerHTML = `
            <div class="p-4">
                <div class="flex items-start gap-3">
                    <i class="ph ${style.icon} text-xl flex-shrink-0 mt-0.5 ${style.iconColor}
                               ${isLoading ? 'animate-spin' : ''}"></i>
                    <div class="flex-1 min-w-0">
                        ${opts.title ? `<p class="text-sm font-semibold ${style.titleColor} leading-snug">${opts.title}</p>` : ''}
                        <p class="text-sm text-gray-600 ${opts.title ? 'mt-0.5' : ''}">${opts.message}</p>
                        ${actionsHtml}
                    </div>
                    <button class="flex-notif-close flex-shrink-0 text-gray-400 hover:text-gray-600 ml-1 -mt-0.5" aria-label="Dismiss">
                        <i class="ph ph-x text-sm"></i>
                    </button>
                </div>
            </div>
            ${duration > 0 && opts.showProgress !== false ? `
                <div class="flex-notif-progress h-0.5 bg-gray-100">
                    <div class="flex-notif-bar h-full bg-current ${style.iconColor} transition-none"
                         style="width:100%"></div>
                </div>` : ''}`;

        // Wire close button
        el.querySelector('.flex-notif-close').addEventListener('click', () => this.dismiss(id));

        // Wire action buttons
        actions.forEach((action, i) => {
            el.querySelector(`[data-action-index="${i}"]`)?.addEventListener('click', (e) => {
                e.stopPropagation();
                if (action.onClick) action.onClick(id, this);
                if (action.dismiss !== false) this.dismiss(id);
            });
        });

        this._container.appendChild(el);

        // Animate in
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                el.style.opacity   = '1';
                el.style.transform = 'translateX(0)';
            });
        });

        // Auto-dismiss timer
        let timer = null;
        if (duration > 0) {
            // Progress bar animation
            const bar = el.querySelector('.flex-notif-bar');
            if (bar) {
                requestAnimationFrame(() => {
                    bar.style.transition = `width ${duration}ms linear`;
                    bar.style.width = '0%';
                });
            }
            timer = setTimeout(() => this.dismiss(id), duration);
        }

        this._notifications.set(id, { el, timer, opts: { ...opts, type, duration } });
        this._dispatch('show', { id, opts });
        return id;
    }

    // ── Shorthand methods ──────────────────────────────────────────────────

    success(message, opts = {}) { return this.show({ ...opts, message, type: 'success' }); }
    error(message, opts = {})   { return this.show({ ...opts, message, type: 'error'   }); }
    warning(message, opts = {}) { return this.show({ ...opts, message, type: 'warning' }); }
    info(message, opts = {})    { return this.show({ ...opts, message, type: 'info'    }); }
    loading(message, opts = {}) { return this.show({ ...opts, message, type: 'loading', persistent: true, ...opts }); }

    // ── Update ─────────────────────────────────────────────────────────────

    /**
     * Update an existing notification in-place (e.g. resolve a loading state).
     */
    update(id, opts = {}) {
        const entry = this._notifications.get(id);
        if (!entry) return this.show({ ...opts, id });

        // Clear old timer
        if (entry.timer) clearTimeout(entry.timer);

        // Re-render by dismiss + show (simplest correct approach)
        entry.el.remove();
        this._notifications.delete(id);
        return this.show({ ...opts, id });
    }

    // ── Dismiss ────────────────────────────────────────────────────────────

    dismiss(id) {
        const entry = this._notifications.get(id);
        if (!entry) return;
        if (entry.timer) clearTimeout(entry.timer);

        // Remove from map immediately so callers see the state change at once
        this._notifications.delete(id);
        this._dispatch('dismiss', { id });

        // Animate the DOM element out (deferred)
        const el = entry.el;
        el.style.opacity   = '0';
        el.style.transform = 'translateX(100%)';
        el.style.maxHeight = el.offsetHeight + 'px';
        setTimeout(() => {
            el.style.maxHeight = '0';
            el.style.margin    = '0';
            el.style.padding   = '0';
            setTimeout(() => el.remove(), 150);
        }, 300);
    }

    dismissAll() {
        for (const id of [...this._notifications.keys()]) {
            this.dismiss(id);
        }
    }

    // ── Promise helper ─────────────────────────────────────────────────────

    /**
     * Show a loading notification while a promise runs, then resolve to success/error.
     * @param {Promise} promise
     * @param {Object} messages - { loading, success, error }
     * @returns {Promise} the original promise result
     */
    async promise(promise, messages = {}) {
        const id = this.loading(messages.loading || 'Loading…');
        try {
            const result = await promise;
            this.update(id, {
                type: 'success',
                message: typeof messages.success === 'function'
                    ? messages.success(result)
                    : (messages.success || 'Done!'),
                duration: this.options.defaultDuration,
                persistent: false,
            });
            return result;
        } catch (err) {
            this.update(id, {
                type: 'error',
                message: typeof messages.error === 'function'
                    ? messages.error(err)
                    : (messages.error || err?.message || 'Something went wrong'),
                duration: this.options.defaultDuration,
                persistent: false,
            });
            throw err;
        }
    }

    // ── Utilities ──────────────────────────────────────────────────────────

    getCount()          { return this._notifications.size; }
    has(id)             { return this._notifications.has(id); }
    setPosition(pos)    { this.options.position = pos; this._applyPosition(this._container); }

    _dispatch(event, detail) {
        document.dispatchEvent(new CustomEvent(`flexnotif:${event}`, { detail, bubbles: true }));
    }

    destroy() {
        this.dismissAll();
        setTimeout(() => {
            this._container?.remove();
            if (FlexNotification._instance === this) FlexNotification._instance = null;
        }, 500);
    }
}
