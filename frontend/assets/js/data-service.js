import { apiFetch } from './api.js';

/**
 * Generic Data Service - CRUD operations for any entity
 */
class DataService {
  /**
   * List/search records
   */
  async list(entity, options = {}) {
    const {
      page = 1,
      pageSize = 25,
      filters = [],
      sort = [],
      search = null,
      scope = null
    } = options;

    // Build query params for GET request
    const params = new URLSearchParams();
    params.append('page', page);
    params.append('page_size', pageSize);

    if (search) {
      params.append('search', search);
    }

    if (sort && sort.length > 0) {
      // Convert [[field, dir], ...] to "field:dir,field2:dir2" format
      const sortStr = sort.map(s => `${s[0]}:${s[1]}`).join(',');
      params.append('sort', sortStr);
    }

    if (filters && filters.length > 0) {
      params.append('filters', JSON.stringify({ conditions: filters }));
    }

    const response = await apiFetch(`/dynamic-data/${entity}/records?${params.toString()}`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to fetch records');
    }

    const data = await response.json();

    // Normalize response to expected format
    return {
      rows: data.items || data.rows || [],
      total: data.total || 0,
      page: data.page || page,
      pageSize: data.page_size || pageSize,
      pages: data.pages || Math.ceil((data.total || 0) / pageSize)
    };
  }

  /**
   * Get single record
   */
  async get(entity, id) {
    const response = await apiFetch(`/dynamic-data/${entity}/records/${id}`);
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to fetch record');
    }
    return await response.json();
  }

  /**
   * Create record
   */
  async create(entity, data, scope = null) {
    const response = await apiFetch(`/dynamic-data/${entity}/records`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ data })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Create failed');
    }

    return await response.json();
  }

  /**
   * Update record
   */
  async update(entity, id, data, version = null) {
    const response = await apiFetch(`/dynamic-data/${entity}/records/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ data })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Update failed');
    }

    return await response.json();
  }

  /**
   * Delete record
   */
  async delete(entity, id) {
    const response = await apiFetch(`/dynamic-data/${entity}/records/${id}`, {
      method: 'DELETE'
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Delete failed');
    }

    return true;
  }

  /**
   * Bulk operations
   */
  async bulk(entity, operation, records) {
    const response = await apiFetch(`/dynamic-data/${entity}/bulk`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ operation, records })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Bulk operation failed');
    }

    return await response.json();
  }
}

// Export singleton instance
export const dataService = new DataService();