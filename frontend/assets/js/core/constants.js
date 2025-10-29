/**
 * Core Constants
 *
 * Shared constants used across all layout components
 *
 * @author Claude Code
 * @version 1.0.0
 */

// Tailwind CSS breakpoints (matches default Tailwind config)
export const BREAKPOINTS = {
    xs: 0,
    sm: 640,
    md: 768,
    lg: 1024,
    xl: 1280,
    '2xl': 1536
};

// Breakpoint order for comparisons
export const BREAKPOINT_ORDER = ['xs', 'sm', 'md', 'lg', 'xl', '2xl'];

// Tailwind gap/spacing scale (in rem units)
export const SPACING_SCALE = {
    0: '0',
    1: '0.25rem',
    2: '0.5rem',
    3: '0.75rem',
    4: '1rem',
    5: '1.25rem',
    6: '1.5rem',
    7: '1.75rem',
    8: '2rem',
    9: '2.25rem',
    10: '2.5rem',
    11: '2.75rem',
    12: '3rem'
};

// Component event types
export const EVENTS = {
    INIT: 'init',
    RENDER: 'render',
    UPDATE: 'update',
    DESTROY: 'destroy',
    ITEM_ADD: 'item:add',
    ITEM_REMOVE: 'item:remove',
    ITEM_UPDATE: 'item:update',
    REORDER: 'reorder',
    RESIZE: 'resize',
    BREAKPOINT_CHANGE: 'breakpoint:change',
    STATE_CHANGE: 'state:change'
};

// Animation durations (in ms)
export const ANIMATION_DURATION = {
    FAST: 150,
    NORMAL: 300,
    SLOW: 500
};

// Z-index layers
export const Z_INDEX = {
    BASE: 1,
    DROPDOWN: 10,
    STICKY: 20,
    MODAL: 50,
    TOAST: 100
};

export default {
    BREAKPOINTS,
    BREAKPOINT_ORDER,
    SPACING_SCALE,
    EVENTS,
    ANIMATION_DURATION,
    Z_INDEX
};
