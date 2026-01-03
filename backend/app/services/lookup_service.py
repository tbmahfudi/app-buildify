"""
Lookup Configuration Service

Business logic for the Lookup Configuration feature.
Handles dynamic data retrieval and caching.
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta
import hashlib
import json

from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException, status

from app.models.lookup import (
    LookupConfiguration,
    LookupCache,
    CascadingLookupRule,
)
from app.schemas.lookup import (
    LookupConfigurationCreate,
    LookupConfigurationUpdate,
    CascadingLookupRuleCreate,
    CascadingLookupRuleUpdate,
)


class LookupService:
    """Service for managing lookup configurations"""

    def __init__(self, db: Session, current_user):
        self.db = db
        self.current_user = current_user
        self.tenant_id = current_user.tenant_id

    # ==================== Lookup Configuration Methods ====================

    async def create_configuration(self, config_data: LookupConfigurationCreate):
        """Create a new lookup configuration"""
        # Check if configuration name already exists
        existing = self.db.query(LookupConfiguration).filter(
            LookupConfiguration.tenant_id == self.tenant_id,
            LookupConfiguration.name == config_data.name,
            LookupConfiguration.is_deleted == False
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Lookup configuration with name '{config_data.name}' already exists"
            )

        config = LookupConfiguration(
            **config_data.model_dump(),
            tenant_id=self.tenant_id,
            created_by=self.current_user.id,
            updated_by=self.current_user.id
        )

        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)

        return config

    async def list_configurations(
        self,
        source_type: Optional[str] = None,
        entity_id: Optional[UUID] = None
    ):
        """List all lookup configurations"""
        query = self.db.query(LookupConfiguration).filter(
            LookupConfiguration.tenant_id == self.tenant_id,
            LookupConfiguration.is_deleted == False
        )

        if source_type:
            query = query.filter(LookupConfiguration.source_type == source_type)
        if entity_id:
            query = query.filter(LookupConfiguration.source_entity_id == entity_id)

        return query.all()

    async def get_configuration(self, config_id: UUID):
        """Get lookup configuration by ID"""
        config = self.db.query(LookupConfiguration).filter(
            LookupConfiguration.id == config_id,
            LookupConfiguration.tenant_id == self.tenant_id,
            LookupConfiguration.is_deleted == False
        ).first()

        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lookup configuration not found"
            )

        return config

    async def update_configuration(self, config_id: UUID, config_data: LookupConfigurationUpdate):
        """Update lookup configuration"""
        config = await self.get_configuration(config_id)

        update_data = config_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(config, key, value)

        config.updated_by = self.current_user.id

        # Clear cache when configuration changes
        await self._clear_cache(config_id)

        self.db.commit()
        self.db.refresh(config)

        return config

    async def delete_configuration(self, config_id: UUID):
        """Delete lookup configuration"""
        config = await self.get_configuration(config_id)

        config.is_deleted = True
        config.updated_by = self.current_user.id

        # Clear cache
        await self._clear_cache(config_id)

        self.db.commit()

        return {"message": "Lookup configuration deleted successfully"}

    # ==================== Lookup Data Methods ====================

    async def get_lookup_data(
        self,
        config_id: UUID,
        search: Optional[str] = None,
        filters: Optional[dict] = None,
        parent_value: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ):
        """Get lookup data based on configuration"""
        config = await self.get_configuration(config_id)

        # Check cache first
        if config.enable_caching:
            cache_key = self._generate_cache_key(config_id, search, filters, parent_value)
            cached_data = await self._get_from_cache(config_id, cache_key)

            if cached_data:
                return self._paginate_data(cached_data, page, page_size)

        # Fetch data based on source type
        if config.source_type == "static_list":
            data = await self._get_static_list_data(config, search, filters)
        elif config.source_type == "entity":
            data = await self._get_entity_data(config, search, filters, parent_value)
        elif config.source_type == "custom_query":
            data = await self._get_custom_query_data(config, search, filters, parent_value)
        elif config.source_type == "api":
            data = await self._get_api_data(config, search, filters, parent_value)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported source type: {config.source_type}"
            )

        # Cache the data
        if config.enable_caching:
            await self._save_to_cache(config, cache_key, data)

        return self._paginate_data(data, page, page_size)

    # ==================== Cascading Lookup Rule Methods ====================

    async def create_cascading_rule(self, rule_data: CascadingLookupRuleCreate):
        """Create a cascading lookup rule"""
        rule = CascadingLookupRule(
            **rule_data.model_dump(),
            tenant_id=self.tenant_id,
            created_by=self.current_user.id
        )

        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)

        return rule

    async def list_cascading_rules(
        self,
        parent_lookup_id: Optional[UUID] = None,
        child_lookup_id: Optional[UUID] = None
    ):
        """List cascading lookup rules"""
        query = self.db.query(CascadingLookupRule).filter(
            CascadingLookupRule.tenant_id == self.tenant_id,
            CascadingLookupRule.is_active == True
        )

        if parent_lookup_id:
            query = query.filter(CascadingLookupRule.parent_lookup_id == parent_lookup_id)
        if child_lookup_id:
            query = query.filter(CascadingLookupRule.child_lookup_id == child_lookup_id)

        return query.all()

    # ==================== Helper Methods ====================

    def _generate_cache_key(
        self,
        config_id: UUID,
        search: Optional[str],
        filters: Optional[dict],
        parent_value: Optional[str]
    ) -> str:
        """Generate a cache key for lookup data"""
        key_data = {
            "config_id": str(config_id),
            "search": search,
            "filters": filters,
            "parent_value": parent_value
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()

    async def _get_from_cache(self, lookup_id: UUID, cache_key: str):
        """Get data from cache"""
        cache_entry = self.db.query(LookupCache).filter(
            LookupCache.lookup_id == lookup_id,
            LookupCache.cache_key == cache_key,
            LookupCache.expires_at > datetime.utcnow()
        ).first()

        if cache_entry:
            # Update hit count
            cache_entry.hit_count += 1
            cache_entry.last_accessed_at = datetime.utcnow()
            self.db.commit()

            return cache_entry.cached_data

        return None

    async def _save_to_cache(self, config: LookupConfiguration, cache_key: str, data: list):
        """Save data to cache"""
        expires_at = datetime.utcnow() + timedelta(seconds=config.cache_ttl_seconds)

        cache_entry = LookupCache(
            lookup_id=config.id,
            tenant_id=self.tenant_id,
            cache_key=cache_key,
            cached_data=data,
            record_count=len(data),
            expires_at=expires_at
        )

        self.db.add(cache_entry)
        self.db.commit()

    async def _clear_cache(self, lookup_id: UUID):
        """Clear all cache entries for a lookup"""
        self.db.query(LookupCache).filter(
            LookupCache.lookup_id == lookup_id
        ).delete()
        self.db.commit()

    async def _get_static_list_data(
        self,
        config: LookupConfiguration,
        search: Optional[str],
        filters: Optional[dict]
    ):
        """Get data from static list"""
        data = config.static_options or []

        if search and config.enable_search:
            search_lower = search.lower()
            data = [
                item for item in data
                if search_lower in str(item.get("label", "")).lower()
            ]

        return data

    async def _get_entity_data(
        self,
        config: LookupConfiguration,
        search: Optional[str],
        filters: Optional[dict],
        parent_value: Optional[str]
    ):
        """Get data from entity source (simplified)"""
        # Simplified implementation
        # In production, query the actual entity table
        return [
            {"value": "1", "label": "Option 1"},
            {"value": "2", "label": "Option 2"},
        ]

    async def _get_custom_query_data(
        self,
        config: LookupConfiguration,
        search: Optional[str],
        filters: Optional[dict],
        parent_value: Optional[str]
    ):
        """Get data from custom query (simplified)"""
        # Simplified implementation
        # In production, execute the custom SQL query
        return []

    async def _get_api_data(
        self,
        config: LookupConfiguration,
        search: Optional[str],
        filters: Optional[dict],
        parent_value: Optional[str]
    ):
        """Get data from API source (simplified)"""
        # Simplified implementation
        # In production, call the external API
        return []

    def _paginate_data(self, data: list, page: int, page_size: int):
        """Paginate lookup data"""
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size

        items = data[start_idx:end_idx]

        return {
            "items": items,
            "total_count": len(data),
            "page": page,
            "page_size": page_size,
            "has_more": end_idx < len(data)
        }
