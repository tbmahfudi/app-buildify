/**
 * Flex Components - Central Export
 *
 * Import all Flex* components from a single location
 *
 * Usage:
 *   import { FlexButton, FlexInput, FlexModal } from './components/index.js';
 *
 * Or import individually:
 *   import FlexButton from './components/flex-button.js';
 */

// Form Components
export { default as FlexInput } from './flex-input.js';
export { default as FlexTextarea } from './flex-textarea.js';
export { default as FlexSelect } from './flex-select.js';
export { default as FlexCheckbox } from './flex-checkbox.js';
export { default as FlexRadio } from './flex-radio.js';

// UI Components
export { default as FlexButton } from './flex-button.js';
export { default as FlexCard } from './flex-card.js';
export { default as FlexModal } from './flex-modal.js';
export { default as FlexTabs } from './flex-tabs.js';
export { default as FlexAccordion } from './flex-accordion.js';
export { default as FlexBreadcrumb } from './flex-breadcrumb.js';

// Feedback Components
export { default as FlexAlert } from './flex-alert.js';
export { default as FlexBadge } from './flex-badge.js';
export { default as FlexTooltip } from './flex-tooltip.js';
export { default as FlexSpinner } from './flex-spinner.js';

// Navigation Components
export { default as FlexDropdown } from './flex-dropdown.js';

// Base Component
export { default as BaseComponent } from '../core/base-component.js';
