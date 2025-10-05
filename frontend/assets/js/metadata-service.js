import { apiFetch } from './api.js';

/**
 * Metadata Service - Fetch and cache entity metadata
 */
class MetadataService {
  constructor() {
    this.cache = new Map();
  }

  /**
   * Get metadata for an entity
   */
  async getMetadata(entityName) {
    // Check cache first
    if (this.cache.has(entityName)) {
      return this.cache.get(entityName);
    }

    try {
      const response = await apiFetch(`/metadata/entities/${entityName}`);
      const metadata = await response.json();
      
      // Cache the metadata
      this.cache.set(entityName, metadata);
      return metadata;
    } catch (error) {
      console.error(`Failed to load metadata for ${entityName}:`, error);
      throw error;
    }
  }

  /**
   * List all available entities
   */
  async listEntities() {
    try {
      const response = await apiFetch('/metadata/entities');
      return await response.json();
    } catch (error) {
      console.error('Failed to list entities:', error);
      throw error;
    }
  }

  /**
   * Clear cache (when metadata is updated)
   */
  clearCache(entityName = null) {
    if (entityName) {
      this.cache.delete(entityName);
    } else {
      this.cache.clear();
    }
  }

  /**
   * Check if user has permission for action
   */
  hasPermission(metadata, action, userRoles) {
    if (!metadata.permissions) return true;
    
    for (const role of userRoles) {
      const rolePerms = metadata.permissions[role];
      if (rolePerms && rolePerms.includes(action)) {
        return true;
      }
    }
    return false;
  }
}

// Export singleton instance
export const metadataService = new MetadataService();