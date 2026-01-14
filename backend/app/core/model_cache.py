"""
Model Cache - Caches runtime-generated SQLAlchemy models

This module provides a thread-safe cache for dynamically generated SQLAlchemy models.
Models are cached per entity per tenant to avoid regenerating them on every request.
"""

from typing import Type, Optional, Dict
from threading import RLock
import hashlib
import json
from datetime import datetime, timedelta


class ModelCache:
    """
    Thread-safe cache for runtime-generated SQLAlchemy models

    Cache Key Format: {tenant_id}:{entity_name}:{version_hash}
    - tenant_id: UUID of the tenant (or 'platform' for platform-level entities)
    - entity_name: Name of the entity
    - version_hash: MD5 hash of entity definition (to detect changes)
    """

    def __init__(self, ttl_minutes: int = 60):
        """
        Initialize model cache

        Args:
            ttl_minutes: Time-to-live in minutes (default: 60)
                        After TTL, cached models will be regenerated
        """
        self._cache: Dict[str, dict] = {}
        self._lock = RLock()
        self._ttl = timedelta(minutes=ttl_minutes)

    def get(
        self,
        tenant_id: str,
        entity_name: str,
        entity_def_hash: str
    ) -> Optional[Type]:
        """
        Get cached model if exists and not expired

        Args:
            tenant_id: Tenant ID (or 'platform')
            entity_name: Entity name
            entity_def_hash: Hash of entity definition

        Returns:
            Cached SQLAlchemy model class or None
        """
        cache_key = self._build_key(tenant_id, entity_name, entity_def_hash)

        with self._lock:
            if cache_key not in self._cache:
                return None

            entry = self._cache[cache_key]

            # Check if expired
            if self._is_expired(entry):
                del self._cache[cache_key]
                return None

            return entry['model']

    def set(
        self,
        tenant_id: str,
        entity_name: str,
        entity_def_hash: str,
        model: Type
    ):
        """
        Cache a model

        Args:
            tenant_id: Tenant ID (or 'platform')
            entity_name: Entity name
            entity_def_hash: Hash of entity definition
            model: SQLAlchemy model class to cache
        """
        cache_key = self._build_key(tenant_id, entity_name, entity_def_hash)

        with self._lock:
            self._cache[cache_key] = {
                'model': model,
                'created_at': datetime.utcnow(),
                'tenant_id': tenant_id,
                'entity_name': entity_name,
                'hash': entity_def_hash
            }

    def invalidate(self, tenant_id: Optional[str] = None, entity_name: Optional[str] = None):
        """
        Invalidate cached models

        Args:
            tenant_id: If provided, invalidate only this tenant's models
            entity_name: If provided, invalidate only this entity's models
        """
        with self._lock:
            if tenant_id is None and entity_name is None:
                # Clear entire cache
                self._cache.clear()
                return

            # Selective invalidation
            keys_to_delete = []
            for key, entry in self._cache.items():
                should_delete = True

                if tenant_id and entry['tenant_id'] != tenant_id:
                    should_delete = False

                if entity_name and entry['entity_name'] != entity_name:
                    should_delete = False

                if should_delete:
                    keys_to_delete.append(key)

            for key in keys_to_delete:
                del self._cache[key]

    def cleanup_expired(self):
        """Remove all expired entries from cache"""
        with self._lock:
            keys_to_delete = []
            for key, entry in self._cache.items():
                if self._is_expired(entry):
                    keys_to_delete.append(key)

            for key in keys_to_delete:
                del self._cache[key]

    def get_stats(self) -> dict:
        """Get cache statistics"""
        with self._lock:
            total = len(self._cache)
            expired = sum(1 for entry in self._cache.values() if self._is_expired(entry))

            # Group by tenant
            tenants = {}
            for entry in self._cache.values():
                tenant_id = entry['tenant_id']
                if tenant_id not in tenants:
                    tenants[tenant_id] = 0
                tenants[tenant_id] += 1

            return {
                'total_entries': total,
                'active_entries': total - expired,
                'expired_entries': expired,
                'tenants': tenants,
                'ttl_minutes': self._ttl.total_seconds() / 60
            }

    def _build_key(self, tenant_id: str, entity_name: str, entity_def_hash: str) -> str:
        """Build cache key"""
        return f"{tenant_id}:{entity_name}:{entity_def_hash}"

    def _is_expired(self, entry: dict) -> bool:
        """Check if cache entry is expired"""
        age = datetime.utcnow() - entry['created_at']
        return age > self._ttl

    @staticmethod
    def hash_entity_definition(entity_def: dict) -> str:
        """
        Create a hash of entity definition

        This hash changes when entity structure changes, triggering cache invalidation

        Args:
            entity_def: EntityDefinition as dict

        Returns:
            MD5 hash string
        """
        # Extract only fields that affect model structure
        relevant_fields = {
            'name': entity_def.get('name'),
            'table_name': entity_def.get('table_name'),
            'schema_name': entity_def.get('schema_name'),
            'fields': [
                {
                    'name': f.get('name'),
                    'field_type': f.get('field_type'),
                    'db_column_name': f.get('db_column_name'),
                    'is_required': f.get('is_required'),
                    'is_primary_key': f.get('is_primary_key'),
                    'is_unique': f.get('is_unique'),
                    'max_length': f.get('max_length'),
                    'precision': f.get('precision'),
                    'scale': f.get('scale'),
                }
                for f in entity_def.get('fields', [])
            ],
            'relationships': [
                {
                    'name': r.get('name'),
                    'type': r.get('relationship_type'),
                    'target_entity': r.get('target_entity'),
                }
                for r in entity_def.get('relationships', [])
            ]
        }

        # Sort to ensure consistent hashing
        json_str = json.dumps(relevant_fields, sort_keys=True)

        # Create MD5 hash
        return hashlib.md5(json_str.encode()).hexdigest()


# Global model cache instance
_model_cache = ModelCache(ttl_minutes=60)


def get_model_cache() -> ModelCache:
    """Get the global model cache instance"""
    return _model_cache
