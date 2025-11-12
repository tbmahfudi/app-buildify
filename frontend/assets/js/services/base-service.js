/**
 * Base Service Class
 *
 * Provides common functionality for all API services:
 * - Singleton pattern implementation
 * - Authenticated fetch wrapper with error handling
 * - Common HTTP methods (GET, POST, PUT, DELETE)
 * - Query parameter building
 *
 * Consolidates ~150+ lines of duplicate code across service classes.
 *
 * Usage:
 *   class ReportService extends BaseService {
 *       constructor() {
 *           super('/reports');
 *       }
 *   }
 */

import { apiFetch } from '../api.js';

export class BaseService {
    /**
     * Create a new service instance.
     *
     * @param {string} baseUrl - Base URL for this service's endpoints
     * @param {Object} options - Service configuration options
     */
    constructor(baseUrl, options = {}) {
        // Implement singleton pattern
        const className = this.constructor.name;
        if (BaseService.instances && BaseService.instances[className]) {
            return BaseService.instances[className];
        }

        this.baseUrl = baseUrl;
        this.options = {
            timeout: options.timeout || 30000,
            retries: options.retries || 0,
            ...options
        };

        // Store singleton instance
        if (!BaseService.instances) {
            BaseService.instances = {};
        }
        BaseService.instances[className] = this;
    }

    /**
     * Perform an authenticated fetch with automatic error handling.
     *
     * Consolidates the duplicate pattern:
     *   const response = await apiFetch(endpoint, options);
     *   if (!response.ok) {
     *       const error = await response.json().catch(() => ({ detail: 'Request failed' }));
     *       throw new Error(error.detail || `HTTP ${response.status}`);
     *   }
     *   return response.json();
     *
     * @param {string} endpoint - API endpoint (relative to baseUrl or absolute)
     * @param {Object} options - Fetch options
     * @returns {Promise<any>} Response data
     * @throws {Error} Request failed
     */
    async _fetchWithAuth(endpoint, options = {}) {
        const response = await apiFetch(endpoint, options);

        if (!response.ok) {
            const error = await response.json().catch(() => ({
                detail: 'Request failed'
            }));
            throw new Error(error.detail || error.message || `HTTP ${response.status}`);
        }

        // Handle 204 No Content
        if (response.status === 204) {
            return null;
        }

        return response.json();
    }

    /**
     * Build URL with query parameters.
     *
     * Consolidates the pattern:
     *   const params = new URLSearchParams();
     *   if (filters.category) params.append('category', filters.category);
     *   const url = `${baseUrl}?${params.toString()}`;
     *
     * @param {string} path - Base path
     * @param {Object} params - Query parameters
     * @returns {string} Complete URL with query string
     */
    _buildUrl(path, params = {}) {
        const url = path.startsWith('http') ? path : `${this.baseUrl}${path}`;

        if (Object.keys(params).length === 0) {
            return url;
        }

        const searchParams = new URLSearchParams();

        for (const [key, value] of Object.entries(params)) {
            if (value !== null && value !== undefined && value !== '') {
                // Handle arrays
                if (Array.isArray(value)) {
                    value.forEach(v => searchParams.append(key, v));
                } else {
                    searchParams.append(key, value);
                }
            }
        }

        const queryString = searchParams.toString();
        return queryString ? `${url}?${queryString}` : url;
    }

    /**
     * Perform a GET request.
     *
     * @param {string} path - Endpoint path
     * @param {Object} params - Query parameters
     * @returns {Promise<any>} Response data
     */
    async get(path = '', params = {}) {
        const url = this._buildUrl(path, params);
        return this._fetchWithAuth(url, {
            method: 'GET'
        });
    }

    /**
     * Perform a POST request.
     *
     * @param {string} path - Endpoint path
     * @param {Object} data - Request body data
     * @param {Object} params - Query parameters
     * @returns {Promise<any>} Response data
     */
    async post(path = '', data = {}, params = {}) {
        const url = this._buildUrl(path, params);
        return this._fetchWithAuth(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
    }

    /**
     * Perform a PUT request.
     *
     * @param {string} path - Endpoint path
     * @param {Object} data - Request body data
     * @param {Object} params - Query parameters
     * @returns {Promise<any>} Response data
     */
    async put(path = '', data = {}, params = {}) {
        const url = this._buildUrl(path, params);
        return this._fetchWithAuth(url, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
    }

    /**
     * Perform a PATCH request.
     *
     * @param {string} path - Endpoint path
     * @param {Object} data - Request body data
     * @param {Object} params - Query parameters
     * @returns {Promise<any>} Response data
     */
    async patch(path = '', data = {}, params = {}) {
        const url = this._buildUrl(path, params);
        return this._fetchWithAuth(url, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
    }

    /**
     * Perform a DELETE request.
     *
     * @param {string} path - Endpoint path
     * @param {Object} params - Query parameters
     * @returns {Promise<any>} Response data (usually null for 204)
     */
    async delete(path = '', params = {}) {
        const url = this._buildUrl(path, params);
        return this._fetchWithAuth(url, {
            method: 'DELETE'
        });
    }

    /**
     * List resources with pagination and filtering.
     *
     * Consolidates the common list pattern:
     *   const params = new URLSearchParams();
     *   if (filters.category) params.append('category', filters.category);
     *   if (filters.skip) params.append('skip', filters.skip);
     *   if (filters.limit) params.append('limit', filters.limit);
     *
     * @param {Object} filters - Filter parameters (category, skip, limit, etc.)
     * @returns {Promise<Object>} List response with items and total
     */
    async list(filters = {}) {
        return this.get('', filters);
    }

    /**
     * Get a single resource by ID.
     *
     * @param {string} id - Resource ID
     * @returns {Promise<Object>} Resource data
     */
    async getById(id) {
        return this.get(`/${id}`);
    }

    /**
     * Create a new resource.
     *
     * @param {Object} data - Resource data
     * @returns {Promise<Object>} Created resource
     */
    async create(data) {
        return this.post('', data);
    }

    /**
     * Update an existing resource.
     *
     * @param {string} id - Resource ID
     * @param {Object} data - Updated data
     * @returns {Promise<Object>} Updated resource
     */
    async update(id, data) {
        return this.put(`/${id}`, data);
    }

    /**
     * Delete a resource.
     *
     * @param {string} id - Resource ID
     * @returns {Promise<void>}
     */
    async remove(id) {
        return this.delete(`/${id}`);
    }

    /**
     * Handle errors consistently.
     *
     * @param {Error} error - Error object
     * @param {string} context - Error context for logging
     * @throws {Error} Rethrows the error after logging
     */
    handleError(error, context = 'API request') {
        console.error(`[${this.constructor.name}] ${context} failed:`, error);
        throw error;
    }

    /**
     * Clear the singleton instance (useful for testing).
     */
    static clearInstance(className) {
        if (BaseService.instances && BaseService.instances[className]) {
            delete BaseService.instances[className];
        }
    }

    /**
     * Clear all singleton instances (useful for testing).
     */
    static clearAllInstances() {
        BaseService.instances = {};
    }
}

/**
 * Singleton Service Mixin
 *
 * Alternative to extending BaseService for classes that need singleton
 * pattern but already extend another class.
 *
 * Usage:
 *   class MyService {
 *       constructor() {
 *           return SingletonMixin.getInstance(this, MyService);
 *       }
 *   }
 */
export class SingletonMixin {
    static instances = {};

    static getInstance(instance, ServiceClass) {
        const className = ServiceClass.name;

        if (SingletonMixin.instances[className]) {
            return SingletonMixin.instances[className];
        }

        SingletonMixin.instances[className] = instance;
        return instance;
    }

    static clearInstance(ServiceClass) {
        const className = ServiceClass.name;
        delete SingletonMixin.instances[className];
    }
}

// Export for use in other services
export default BaseService;
