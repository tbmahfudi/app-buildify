/**
 * Module System
 *
 * Exports all module system components for easy importing.
 */

import { BaseModule } from './base-module.js';
import { moduleLoader } from './module-loader.js';
import { moduleRegistry } from './module-registry.js';

// Named exports
export { BaseModule, moduleLoader, moduleRegistry };

// Default export
export default {
  BaseModule,
  moduleLoader,
  moduleRegistry
};
