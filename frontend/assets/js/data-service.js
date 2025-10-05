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

    const response = await apiFetch(`/data/${entity}/list`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        entity,
        page,
        page_size: pageSize,
        filters,
        sort,
        search,
        scope
      })
    });

    return await response.json();
  }

  /**
   * Get single record
   */
  async get(entity, id) {
    const response = await apiFetch(`/data/${entity}/${id}`);
    return await response.json();
  }

  /**
   * Create record
   */
  async create(entity, data, scope = null) {
    const response = await apiFetch(`/data/${entity}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ entity, data, scope })
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
    const response = await apiFetch(`/data/${entity}/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ entity, id, data, version })
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
    const response = await apiFetch(`/data/${entity}/${id}`, {
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
    const response = await apiFetch(`/data/${entity}/bulk`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ entity, operation, records })
    });

    return await response.json();
  }
}

// Export singleton instance
export const dataService = new DataService();