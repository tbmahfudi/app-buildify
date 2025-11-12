/**
 * Resource Loader with Enhanced Error Handling
 * Handles loading of templates, scripts, and other resources with retries and fallbacks
 */

class ResourceLoader {
  constructor() {
    this.loadedScripts = new Set();
    this.scriptCache = new Map();
    this.templateCache = new Map();
    this.maxRetries = 3;
    this.retryDelay = 1000; // 1 second
  }

  /**
   * Load a template with retry logic and error handling
   */
  async loadTemplate(templateName, options = {}) {
    const { retry = true, cache = true } = options;

    // Check cache first
    if (cache && this.templateCache.has(templateName)) {
      return this.templateCache.get(templateName);
    }

    const url = `/assets/templates/${templateName}.html`;
    let lastError;

    for (let attempt = 1; attempt <= (retry ? this.maxRetries : 1); attempt++) {
      try {
        const response = await fetch(url, {
          method: 'GET',
          headers: {
            'Cache-Control': 'no-cache',
          },
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const html = await response.text();

        // Validate that we got actual HTML content
        if (!html || html.trim().length === 0) {
          throw new Error('Empty template received');
        }

        // Check if we received index.html instead of the actual template
        // This can happen if nginx falls back to index.html for missing files
        const htmlLower = html.toLowerCase();
        if (htmlLower.includes('<!doctype html>') ||
            (htmlLower.includes('<html') && htmlLower.includes('<head>')) ||
            htmlLower.includes('nocode platform') ||
            htmlLower.includes('content-security-policy')) {
          throw new Error('HTTP 404: Template not found (index.html was served instead)');
        }

        // Parse HTML to extract body content and avoid CSP issues
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');

        // Check for parser errors
        const parserError = doc.querySelector('parsererror');
        if (parserError) {
          throw new Error('Failed to parse HTML: ' + parserError.textContent);
        }

        const bodyContent = doc.body?.innerHTML || html;

        // Cache the template
        if (cache) {
          this.templateCache.set(templateName, bodyContent);
        }

        console.log(`✓ Template loaded: ${templateName}`);
        return bodyContent;

      } catch (error) {
        lastError = error;
        console.warn(`Attempt ${attempt}/${this.maxRetries} failed to load template "${templateName}":`, error.message);

        // Don't retry on 404 errors
        if (error.message.includes('404')) {
          break;
        }

        // Wait before retrying
        if (attempt < this.maxRetries && retry) {
          await this.sleep(this.retryDelay * attempt);
        }
      }
    }

    // All attempts failed
    throw new ResourceLoadError('template', templateName, lastError);
  }

  /**
   * Load a JavaScript file dynamically with error handling
   */
  async loadScript(scriptPath, options = {}) {
    const { retry = true, timeout = 10000, cache = true } = options;

    // Normalize script path
    const normalizedPath = scriptPath.startsWith('/') ? scriptPath : `/assets/js/${scriptPath}`;

    // Check if already loaded
    if (cache && this.loadedScripts.has(normalizedPath)) {
      console.log(`Script already loaded: ${normalizedPath}`);
      return { success: true, cached: true };
    }

    let lastError;

    for (let attempt = 1; attempt <= (retry ? this.maxRetries : 1); attempt++) {
      try {
        await this.loadScriptWithTimeout(normalizedPath, timeout);

        // Mark as loaded
        this.loadedScripts.add(normalizedPath);
        console.log(`✓ Script loaded: ${normalizedPath}`);

        return { success: true, cached: false };

      } catch (error) {
        lastError = error;
        console.warn(`Attempt ${attempt}/${this.maxRetries} failed to load script "${scriptPath}":`, error.message);

        // Don't retry on 404 errors
        if (error.message.includes('404') || error.message.includes('not found')) {
          break;
        }

        // Wait before retrying
        if (attempt < this.maxRetries && retry) {
          await this.sleep(this.retryDelay * attempt);
        }
      }
    }

    // All attempts failed
    throw new ResourceLoadError('script', scriptPath, lastError);
  }

  /**
   * Load script with timeout
   */
  loadScriptWithTimeout(src, timeout) {
    return new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = src;
      script.type = 'text/javascript';
      script.async = true;

      const timeoutId = setTimeout(() => {
        script.remove();
        reject(new Error(`Script load timeout after ${timeout}ms`));
      }, timeout);

      script.onload = () => {
        clearTimeout(timeoutId);
        resolve();
      };

      script.onerror = (event) => {
        clearTimeout(timeoutId);
        script.remove();

        // Try to determine error type
        let errorMessage = 'Failed to load script';
        if (event && event.message) {
          errorMessage = event.message;
        } else if (!navigator.onLine) {
          errorMessage = 'Network connection lost';
        }

        reject(new Error(errorMessage));
      };

      document.head.appendChild(script);
    });
  }

  /**
   * Load multiple scripts in sequence
   */
  async loadScripts(scriptPaths, options = {}) {
    const results = [];

    for (const scriptPath of scriptPaths) {
      try {
        const result = await this.loadScript(scriptPath, options);
        results.push({ path: scriptPath, success: true, ...result });
      } catch (error) {
        results.push({ path: scriptPath, success: false, error: error.message });

        // Stop on first error unless continueOnError is true
        if (!options.continueOnError) {
          throw error;
        }
      }
    }

    return results;
  }

  /**
   * Preload templates for faster navigation
   */
  async preloadTemplates(templateNames) {
    const results = await Promise.allSettled(
      templateNames.map(name => this.loadTemplate(name, { retry: false }))
    );

    const successful = results.filter(r => r.status === 'fulfilled').length;
    console.log(`Preloaded ${successful}/${templateNames.length} templates`);

    return results;
  }

  /**
   * Clear caches
   */
  clearCache() {
    this.templateCache.clear();
    this.scriptCache.clear();
    console.log('Resource caches cleared');
  }

  /**
   * Check if a resource is available
   */
  async checkResource(url) {
    try {
      const response = await fetch(url, { method: 'HEAD' });
      return response.ok;
    } catch {
      return false;
    }
  }

  /**
   * Sleep utility
   */
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Get load statistics
   */
  getStats() {
    return {
      loadedScripts: this.loadedScripts.size,
      cachedTemplates: this.templateCache.size,
      scripts: Array.from(this.loadedScripts),
      templates: Array.from(this.templateCache.keys())
    };
  }
}

/**
 * Custom error class for resource loading failures
 */
class ResourceLoadError extends Error {
  constructor(resourceType, resourceName, originalError) {
    const message = `Failed to load ${resourceType}: ${resourceName}`;
    super(message);

    this.name = 'ResourceLoadError';
    this.resourceType = resourceType;
    this.resourceName = resourceName;
    this.originalError = originalError;
    this.timestamp = new Date().toISOString();

    // Preserve stack trace
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, ResourceLoadError);
    }
  }

  toJSON() {
    return {
      name: this.name,
      message: this.message,
      resourceType: this.resourceType,
      resourceName: this.resourceName,
      originalError: this.originalError?.message,
      timestamp: this.timestamp
    };
  }
}

/**
 * Error display utilities
 */
class ErrorDisplay {
  /**
   * Show template load error in content area
   */
  static showTemplateError(templateName, error, container) {
    const errorDetails = error instanceof ResourceLoadError ? error : new ResourceLoadError('template', templateName, error);

    const isNetworkError = !navigator.onLine || error.message.includes('network') || error.message.includes('fetch');
    const is404Error = error.message.includes('404') || error.message.includes('not found');

    container.innerHTML = `
      <div class="max-w-2xl mx-auto mt-20">
        <div class="bg-red-50 border-l-4 border-red-500 p-6 rounded-lg shadow-lg">
          <div class="flex items-start gap-4">
            <i class="ph-duotone ph-${is404Error ? 'file-x' : isNetworkError ? 'wifi-slash' : 'warning-circle'} text-red-500 text-4xl flex-shrink-0"></i>
            <div class="flex-1">
              <h3 class="text-xl font-bold text-red-800 mb-2">
                ${is404Error ? 'Page Not Found' : isNetworkError ? 'Connection Error' : 'Failed to Load Page'}
              </h3>

              <p class="text-red-700 mb-4">
                ${is404Error
                  ? `The template "${templateName}" does not exist or has been removed.`
                  : isNetworkError
                  ? 'Unable to connect to the server. Please check your internet connection.'
                  : `An error occurred while loading "${templateName}".`
                }
              </p>

              ${!is404Error && !isNetworkError ? `
                <details class="mb-4">
                  <summary class="cursor-pointer text-red-600 hover:text-red-700 font-medium">
                    Technical Details
                  </summary>
                  <div class="mt-2 p-3 bg-red-100 rounded border border-red-200 text-sm font-mono text-red-900 overflow-x-auto">
                    ${this.escapeHtml(error.message)}
                  </div>
                </details>
              ` : ''}

              <div class="flex gap-3">
                <button
                  onclick="window.location.hash = 'dashboard'"
                  class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition flex items-center gap-2 shadow">
                  <i class="ph ph-house"></i>
                  Go to Dashboard
                </button>

                ${isNetworkError ? `
                  <button
                    onclick="window.location.reload()"
                    class="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition flex items-center gap-2 shadow">
                    <i class="ph ph-arrow-clockwise"></i>
                    Retry
                  </button>
                ` : ''}

                <button
                  onclick="history.back()"
                  class="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition flex items-center gap-2">
                  <i class="ph ph-arrow-left"></i>
                  Go Back
                </button>
              </div>
            </div>
          </div>
        </div>

        ${!is404Error ? `
          <div class="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <p class="text-sm text-blue-800">
              <i class="ph ph-info"></i>
              <strong>Tip:</strong> If this problem persists, try clearing your browser cache or contact support.
            </p>
          </div>
        ` : ''}
      </div>
    `;
  }

  /**
   * Show script load error notification
   */
  static showScriptError(scriptName, error) {
    const isNetworkError = !navigator.onLine || error.message.includes('network') || error.message.includes('fetch');

    // Use existing notification system if available
    if (window.showNotification) {
      window.showNotification(
        `Failed to load script: ${scriptName}. ${isNetworkError ? 'Please check your connection.' : 'Some features may not work properly.'}`,
        'error',
        10000 // 10 seconds
      );
    } else {
      console.error(`Script load error: ${scriptName}`, error);
    }
  }

  /**
   * Show inline error message
   */
  static showInlineError(message, container, options = {}) {
    const { type = 'error', dismissible = true } = options;

    const colorMap = {
      error: { bg: 'bg-red-50', border: 'border-red-500', text: 'text-red-800', icon: 'ph-warning-circle' },
      warning: { bg: 'bg-yellow-50', border: 'border-yellow-500', text: 'text-yellow-800', icon: 'ph-warning' },
      info: { bg: 'bg-blue-50', border: 'border-blue-500', text: 'text-blue-800', icon: 'ph-info' }
    };

    const colors = colorMap[type] || colorMap.error;

    const errorDiv = document.createElement('div');
    errorDiv.className = `${colors.bg} border-l-4 ${colors.border} p-4 rounded-lg mb-4`;
    errorDiv.innerHTML = `
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <i class="ph-duotone ${colors.icon} ${colors.text} text-2xl"></i>
          <p class="${colors.text}">${this.escapeHtml(message)}</p>
        </div>
        ${dismissible ? `
          <button onclick="this.parentElement.parentElement.remove()" class="${colors.text} hover:opacity-70">
            <i class="ph ph-x text-xl"></i>
          </button>
        ` : ''}
      </div>
    `;

    container.insertBefore(errorDiv, container.firstChild);
  }

  /**
   * Escape HTML to prevent XSS
   */
  static escapeHtml(unsafe) {
    return unsafe
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
}

// Create singleton instance
const resourceLoader = new ResourceLoader();

// Make available globally for browser usage
if (typeof window !== 'undefined') {
  window.ResourceLoader = ResourceLoader;
  window.ResourceLoadError = ResourceLoadError;
  window.ErrorDisplay = ErrorDisplay;
  window.resourceLoader = resourceLoader;
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { ResourceLoader, resourceLoader, ResourceLoadError, ErrorDisplay };
}
