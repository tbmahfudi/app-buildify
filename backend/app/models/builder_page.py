"""Builder page models."""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, ForeignKey, UniqueConstraint, Index, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from .base import Base


class BuilderPage(Base):
    """Model for builder pages."""

    __tablename__ = 'builder_pages'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), nullable=False, index=True)

    # Page information
    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, index=True)
    description = Column(Text)

    # Module association
    module_id = Column(String(36), nullable=True, index=True)
    module_name = Column(String(100), nullable=True)

    # Route configuration
    route_path = Column(String(500), nullable=False)

    # GrapeJS data and outputs
    grapejs_data = Column(JSONB, nullable=False)
    html_output = Column(Text)
    css_output = Column(Text)
    js_output = Column(Text)

    # Menu configuration
    menu_id = Column(String(36), nullable=True)
    menu_label = Column(String(255))
    menu_icon = Column(String(100))
    menu_parent = Column(String(100))
    menu_order = Column(Integer)
    show_in_menu = Column(Boolean, default=True, nullable=False)

    # Permission configuration
    permission_id = Column(String(36), nullable=True)
    permission_code = Column(String(255))
    permission_scope = Column(String(50), default='company')

    # Publishing
    published = Column(Boolean, default=False, nullable=False, index=True)
    published_at = Column(DateTime)
    published_by = Column(String(36))

    # Metadata
    created_by = Column(String(36), nullable=False)
    updated_by = Column(String(36))
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    versions = relationship('BuilderPageVersion', back_populates='page', cascade='all, delete-orphan')

    # Constraints
    __table_args__ = (
        UniqueConstraint('tenant_id', 'slug', name='uq_builder_page_slug'),
        UniqueConstraint('tenant_id', 'route_path', name='uq_builder_page_route'),
        Index('idx_builder_pages_tenant_module', 'tenant_id', 'module_name'),
        Index('idx_builder_pages_published', 'tenant_id', 'published'),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'module_id': self.module_id,
            'module_name': self.module_name,
            'route_path': self.route_path,
            'grapejs_data': self.grapejs_data,
            'html_output': self.html_output,
            'css_output': self.css_output,
            'js_output': self.js_output,
            'menu_label': self.menu_label,
            'menu_icon': self.menu_icon,
            'menu_parent': self.menu_parent,
            'menu_order': self.menu_order,
            'show_in_menu': self.show_in_menu,
            'permission_code': self.permission_code,
            'permission_scope': self.permission_scope,
            'published': self.published,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'created_by': self.created_by,
            'updated_by': self.updated_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class BuilderPageVersion(Base):
    """Model for builder page versions."""

    __tablename__ = 'builder_page_versions'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    page_id = Column(String(36), ForeignKey('builder_pages.id', ondelete='CASCADE'), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)

    # Version data
    grapejs_data = Column(JSONB, nullable=False)
    html_output = Column(Text)
    css_output = Column(Text)
    js_output = Column(Text)
    commit_message = Column(String(500))

    # Metadata
    created_by = Column(String(36), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    page = relationship('BuilderPage', back_populates='versions')

    # Constraints
    __table_args__ = (
        UniqueConstraint('page_id', 'version_number', name='uq_page_version'),
        Index('idx_builder_versions_page', 'page_id', 'created_at'),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            'id': self.id,
            'page_id': self.page_id,
            'version_number': self.version_number,
            'grapejs_data': self.grapejs_data,
            'html_output': self.html_output,
            'css_output': self.css_output,
            'js_output': self.js_output,
            'commit_message': self.commit_message,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
