"""
Template Category Model

Defines taxonomy for organizing no-code platform templates.
Categories help users find relevant templates based on industry or use-case.
"""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import GUID, Base, generate_uuid


class TemplateCategory(Base):
    """
    Template Category Model

    Hierarchical categorization for platform templates.
    Supports both industry-based and use-case-based organization.
    """
    __tablename__ = "template_categories"

    # Primary Key
    id = Column(GUID, primary_key=True, default=generate_uuid)

    # Category Info
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    icon = Column(String(50))  # Phosphor icon name
    color = Column(String(50))  # Color theme for UI

    # Hierarchy
    parent_id = Column(GUID, ForeignKey("template_categories.id"), nullable=True)
    level = Column(Integer, default=0)  # 0=root, 1=subcategory, etc.
    path = Column(String(500))  # Materialized path: /industry/healthcare/

    # Category Type
    category_type = Column(String(50), nullable=False)  # 'industry', 'use_case', 'function'

    # Display
    display_order = Column(Integer, default=0)
    is_featured = Column(Boolean, default=False)

    # Status
    is_active = Column(Boolean, default=True)
    is_system = Column(Boolean, default=True)  # System categories can't be deleted

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    children = relationship("TemplateCategory",
                          remote_side=[id],
                          backref="parent")

    # Table constraints
    __table_args__ = (
        Index("idx_template_categories_type", "category_type"),
        Index("idx_template_categories_parent", "parent_id"),
        Index("idx_template_categories_path", "path"),
    )

    def __repr__(self):
        return f"<TemplateCategory(code={self.code}, name={self.name})>"


class TemplateVersion(Base):
    """
    Template Version Model

    Tracks version history of platform templates.
    Stores snapshots of template configuration for rollback and audit.
    """
    __tablename__ = "template_versions"

    # Primary Key
    id = Column(GUID, primary_key=True, default=generate_uuid)

    # Template Reference
    template_type = Column(String(50), nullable=False)  # 'entity', 'workflow', 'automation', 'lookup'
    template_id = Column(GUID, nullable=False, index=True)

    # Version Info
    version_number = Column(Integer, nullable=False)
    version_name = Column(String(100))  # e.g., "v1.0", "Initial Release"

    # Change Info
    change_summary = Column(Text, nullable=False)
    change_type = Column(String(50))  # 'major', 'minor', 'patch', 'hotfix'
    changelog = Column(Text)  # Detailed changelog

    # Snapshot Data
    template_snapshot = Column(Text, nullable=False)  # JSON snapshot of template state

    # Metadata
    is_published = Column(Boolean, default=False)
    is_current = Column(Boolean, default=True)
    published_at = Column(DateTime)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(GUID, ForeignKey("users.id"), nullable=False)

    # Table constraints
    __table_args__ = (
        Index("idx_template_versions_template", "template_type", "template_id"),
        Index("idx_template_versions_version", "template_type", "template_id", "version_number"),
        Index("idx_template_versions_current", "is_current"),
    )

    def __repr__(self):
        return f"<TemplateVersion(type={self.template_type}, version={self.version_number})>"


class TemplatePackage(Base):
    """
    Template Package Model

    Packages multiple templates together for import/export.
    Useful for distributing template bundles (e.g., "CRM Starter Pack").
    """
    __tablename__ = "template_packages"

    # Primary Key
    id = Column(GUID, primary_key=True, default=generate_uuid)

    # Package Info
    code = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    version = Column(String(50), default="1.0.0")

    # Author Info
    author = Column(String(200))
    author_email = Column(String(255))
    license = Column(String(100))
    homepage_url = Column(String(500))

    # Category
    category_id = Column(GUID, ForeignKey("template_categories.id"))

    # Package Contents
    package_data = Column(Text, nullable=False)  # JSON with all templates
    dependencies = Column(Text)  # JSON list of required packages/templates

    # Installation Info
    install_count = Column(Integer, default=0)
    last_installed_at = Column(DateTime)

    # Status
    is_published = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)  # Verified by platform admins
    is_active = Column(Boolean, default=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(GUID, ForeignKey("users.id"))

    # Table constraints
    __table_args__ = (
        Index("idx_template_packages_category", "category_id"),
        Index("idx_template_packages_published", "is_published", "is_active"),
    )

    def __repr__(self):
        return f"<TemplatePackage(code={self.code}, version={self.version})>"
