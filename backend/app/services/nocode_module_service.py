"""
No-Code Module Service

Business logic for the Module System Foundation (Phase 4 Priority 1).
Handles module creation, versioning, and dependency management.
"""

from typing import List, Optional, Tuple, Dict
from uuid import UUID
import re
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from fastapi import HTTPException, status
from packaging import version as pkg_version

from app.models.nocode_module import Module, ModuleDependency, ModuleVersion

# Alias for backward compat within this service
NocodeModule = Module
from app.models.base import generate_uuid


class NocodeModuleService:
    """Service for managing no-code modules"""

    def __init__(self, db: Session, current_user):
        self.db = db
        self.current_user = current_user
        self.tenant_id = current_user.tenant_id

    # ==================== Module CRUD ====================

    async def create_module(
        self,
        name: str,
        display_name: str,
        description: str,
        table_prefix: str,
        category: Optional[str] = None,
        icon: Optional[str] = None,
        color: Optional[str] = None,
        is_platform_level: bool = False
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        Create a new module

        Args:
            name: Module internal name (e.g., "hr_management")
            display_name: User-facing name (e.g., "HR Management")
            description: Module description
            table_prefix: Database table prefix (max 10 chars, lowercase alphanumeric, no underscore)
            category: Module category (hr, finance, sales, etc.)
            icon: Phosphor icon name
            color: Hex color code
            is_platform_level: True for platform templates (NULL tenant_id)

        Returns:
            Tuple of (success, message, module_data)
        """

        # Validate table prefix (max 10 chars, lowercase alphanumeric, no underscore within)
        if not re.match(r'^[a-z0-9]{1,10}$', table_prefix):
            return False, "Table prefix must be 1-10 lowercase alphanumeric characters (no underscore)", None

        # Determine tenant_id
        target_tenant_id = None if is_platform_level else self.tenant_id

        # Only superusers can create platform-level modules
        if is_platform_level and not self.current_user.is_superuser:
            return False, "Only superusers can create platform-level modules", None

        # Check if prefix already exists
        existing_prefix = self.db.query(NocodeModule).filter(
            NocodeModule.table_prefix == table_prefix
        ).first()
        if existing_prefix:
            return False, f"Table prefix '{table_prefix}' already in use by module '{existing_prefix.name}'", None

        # Check if name already exists (scope: tenant or platform)
        if is_platform_level:
            existing_filter = NocodeModule.tenant_id == None
        else:
            existing_filter = or_(
                NocodeModule.tenant_id == self.tenant_id,
                NocodeModule.tenant_id == None
            )

        existing_name = self.db.query(NocodeModule).filter(
            existing_filter,
            NocodeModule.name == name
        ).first()
        if existing_name:
            scope = "platform-level" if existing_name.tenant_id is None else "tenant"
            return False, f"Module name '{name}' already exists at {scope} level", None

        # Create module
        module = NocodeModule(
            id=generate_uuid(),
            name=name,
            display_name=display_name,
            description=description,
            module_type='nocode',
            table_prefix=table_prefix,
            category=category,
            icon=icon or 'cube',
            color=color or '#3b82f6',
            version='1.0.0',
            major_version=1,
            minor_version=0,
            patch_version=0,
            status='draft',
            tenant_id=target_tenant_id,
            created_by=self.current_user.id,
            updated_by=self.current_user.id
        )

        self.db.add(module)
        self.db.commit()
        self.db.refresh(module)

        return True, "Module created successfully", {
            "id": str(module.id),
            "name": module.name,
            "display_name": module.display_name,
            "version": module.version,
            "table_prefix": module.table_prefix,
            "status": module.status
        }

    async def get_module(self, module_id: str) -> Optional[Dict]:
        """Get module by ID"""
        module = self.db.query(NocodeModule).filter(
            NocodeModule.id == module_id
        ).first()

        if not module:
            return None

        # Check access (tenant isolation)
        if module.tenant_id and module.tenant_id != self.tenant_id:
            if not self.current_user.is_superuser:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to access this module"
                )

        return self._module_to_dict(module)

    async def list_modules(
        self,
        status: Optional[str] = None,
        category: Optional[str] = None,
        include_platform: bool = True
    ) -> List[Dict]:
        """List modules accessible to current user"""

        query = self.db.query(NocodeModule)

        # Tenant isolation (include platform templates if requested)
        if include_platform:
            query = query.filter(
                or_(
                    NocodeModule.tenant_id == self.tenant_id,
                    NocodeModule.tenant_id == None
                )
            )
        else:
            query = query.filter(NocodeModule.tenant_id == self.tenant_id)

        # Filters
        if status:
            query = query.filter(NocodeModule.status == status)
        if category:
            query = query.filter(NocodeModule.category == category)

        modules = query.order_by(NocodeModule.created_at.desc()).all()

        return [self._module_to_dict(m) for m in modules]

    async def update_module(
        self,
        module_id: str,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[str] = None,
        icon: Optional[str] = None,
        color: Optional[str] = None,
        config: Optional[Dict] = None
    ) -> Tuple[bool, str]:
        """Update module metadata (name and table_prefix cannot be changed)"""

        module = self.db.query(NocodeModule).filter(
            NocodeModule.id == module_id
        ).first()

        if not module:
            return False, "Module not found"

        # Check permissions
        if module.tenant_id and module.tenant_id != self.tenant_id:
            if not self.current_user.is_superuser:
                return False, "You don't have permission to update this module"

        # Update fields
        if display_name:
            module.display_name = display_name
        if description is not None:
            module.description = description
        if category:
            module.category = category
        if icon:
            module.icon = icon
        if color:
            module.color = color
        if config is not None:
            module.configuration = config

        module.updated_by = self.current_user.id
        module.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(module)

        return True, "Module updated successfully"

    async def publish_module(self, module_id: str) -> Tuple[bool, str]:
        """Publish module (draft → active)"""

        module = self.db.query(NocodeModule).filter(
            NocodeModule.id == module_id
        ).first()

        if not module:
            return False, "Module not found"

        if module.status != 'draft':
            return False, f"Module status is '{module.status}', can only publish from 'draft'"

        # Check dependencies are satisfied
        is_valid, issues = await self.check_dependency_compatibility(module_id)
        if not is_valid:
            return False, f"Dependency issues: {', '.join(issues)}"

        module.status = 'active'
        module.published_at = datetime.utcnow()
        module.published_by = self.current_user.id
        module.updated_by = self.current_user.id
        module.updated_at = datetime.utcnow()

        self.db.commit()

        return True, "Module published successfully"

    async def delete_module(self, module_id: str) -> Tuple[bool, str]:
        """Delete module (only if no dependencies)"""

        module = self.db.query(NocodeModule).filter(
            NocodeModule.id == module_id
        ).first()

        if not module:
            return False, "Module not found"

        # Check if module is core (cannot delete)
        if module.is_core:
            return False, "Cannot delete core module"

        # Check if other modules depend on this
        dependents = self.db.query(ModuleDependency).filter(
            ModuleDependency.depends_on_module_id == module_id
        ).count()

        if dependents > 0:
            return False, f"Cannot delete module: {dependents} other module(s) depend on it"

        # Delete module (CASCADE will handle dependencies and versions)
        self.db.delete(module)
        self.db.commit()

        return True, "Module deleted successfully"

    # ==================== Dependency Management ====================

    async def add_dependency(
        self,
        module_id: str,
        depends_on_module_id: str,
        dependency_type: str = 'required',
        min_version: Optional[str] = None,
        max_version: Optional[str] = None,
        reason: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Add a dependency between modules"""

        # Get modules
        module = self.db.query(NocodeModule).filter(
            NocodeModule.id == module_id
        ).first()
        depends_on = self.db.query(NocodeModule).filter(
            NocodeModule.id == depends_on_module_id
        ).first()

        if not module or not depends_on:
            return False, "Module not found"

        # Check for circular dependencies
        if await self._has_circular_dependency(module_id, depends_on_module_id):
            return False, f"Circular dependency detected: {module.name} → {depends_on.name} → {module.name}"

        # Validate version constraints
        if min_version and not self._is_valid_version(min_version):
            return False, f"Invalid min_version: {min_version}"
        if max_version and not self._is_valid_version(max_version):
            return False, f"Invalid max_version: {max_version}"

        # Build version constraint string
        version_constraint = None
        if min_version and max_version:
            version_constraint = f">={min_version}, <{max_version}"
        elif min_version:
            version_constraint = f">={min_version}"
        elif max_version:
            version_constraint = f"<{max_version}"

        # Check if dependency already exists
        existing = self.db.query(ModuleDependency).filter(
            ModuleDependency.module_id == module_id,
            ModuleDependency.depends_on_module_id == depends_on_module_id
        ).first()

        if existing:
            return False, f"Dependency already exists: {module.name} → {depends_on.name}"

        # Create dependency
        dependency = ModuleDependency(
            id=generate_uuid(),
            module_id=module_id,
            depends_on_module_id=depends_on_module_id,
            dependency_type=dependency_type,
            min_version=min_version,
            max_version=max_version,
            version_constraint=version_constraint,
            reason=reason,
            created_by=self.current_user.id
        )

        self.db.add(dependency)
        self.db.commit()

        return True, f"Dependency added: {module.name} → {depends_on.name}"

    async def remove_dependency(
        self,
        module_id: str,
        dependency_id: str
    ) -> Tuple[bool, str]:
        """Remove a dependency"""

        dependency = self.db.query(ModuleDependency).filter(
            ModuleDependency.id == dependency_id,
            ModuleDependency.module_id == module_id
        ).first()

        if not dependency:
            return False, "Dependency not found"

        self.db.delete(dependency)
        self.db.commit()

        return True, "Dependency removed successfully"

    async def list_dependencies(self, module_id: str) -> List[Dict]:
        """List all dependencies for a module"""

        dependencies = self.db.query(ModuleDependency).filter(
            ModuleDependency.module_id == module_id
        ).all()

        return [
            {
                "id": str(dep.id),
                "depends_on_module": {
                    "id": str(dep.depends_on_module.id),
                    "name": dep.depends_on_module.name,
                    "display_name": dep.depends_on_module.display_name,
                    "version": dep.depends_on_module.version
                },
                "dependency_type": dep.dependency_type,
                "min_version": dep.min_version,
                "max_version": dep.max_version,
                "version_constraint": dep.version_constraint,
                "reason": dep.reason
            }
            for dep in dependencies
        ]

    async def list_dependents(self, module_id: str) -> List[Dict]:
        """List modules that depend on this module"""

        dependents = self.db.query(ModuleDependency).filter(
            ModuleDependency.depends_on_module_id == module_id
        ).all()

        return [
            {
                "id": str(dep.id),
                "module": {
                    "id": str(dep.module.id),
                    "name": dep.module.name,
                    "display_name": dep.module.display_name,
                    "version": dep.module.version
                },
                "dependency_type": dep.dependency_type,
                "version_constraint": dep.version_constraint
            }
            for dep in dependents
        ]

    async def check_dependency_compatibility(
        self,
        module_id: str
    ) -> Tuple[bool, List[str]]:
        """Check if all dependencies are satisfied"""

        issues = []

        # Get module and its dependencies
        module = self.db.query(NocodeModule).filter(
            NocodeModule.id == module_id
        ).first()

        if not module:
            return False, ["Module not found"]

        dependencies = self.db.query(ModuleDependency).filter(
            ModuleDependency.module_id == module_id
        ).all()

        for dep in dependencies:
            depends_on = dep.depends_on_module

            # Check if dependency is active
            if depends_on.status != 'active':
                issues.append(
                    f"Dependency '{depends_on.name}' is not active (status: {depends_on.status})"
                )
                continue

            # Check version compatibility
            if dep.min_version:
                if not self._version_satisfies(depends_on.version, f">={dep.min_version}"):
                    issues.append(
                        f"Dependency '{depends_on.name}' version {depends_on.version} "
                        f"does not satisfy minimum version {dep.min_version}"
                    )

            if dep.max_version:
                if not self._version_satisfies(depends_on.version, f"<{dep.max_version}"):
                    issues.append(
                        f"Dependency '{depends_on.name}' version {depends_on.version} "
                        f"exceeds maximum version {dep.max_version}"
                    )

        return len(issues) == 0, issues

    # ==================== Version Management ====================

    async def increment_version(
        self,
        module_id: str,
        change_type: str,  # major, minor, patch
        change_summary: str,
        changelog: Optional[str] = None,
        breaking_changes: Optional[str] = None
    ) -> Tuple[bool, str, Optional[str]]:
        """Increment module version and create snapshot"""

        module = self.db.query(NocodeModule).filter(
            NocodeModule.id == module_id
        ).first()

        if not module:
            return False, "Module not found", None

        # Calculate new version
        if change_type == 'major':
            new_major = module.major_version + 1
            new_minor = 0
            new_patch = 0
        elif change_type == 'minor':
            new_major = module.major_version
            new_minor = module.minor_version + 1
            new_patch = 0
        else:  # patch
            new_major = module.major_version
            new_minor = module.minor_version
            new_patch = module.patch_version + 1

        new_version = f"{new_major}.{new_minor}.{new_patch}"

        # Create version snapshot
        snapshot = await self._create_module_snapshot(module)

        # Get next version number
        max_version_num = self.db.query(func.max(ModuleVersion.version_number)).filter(
            ModuleVersion.module_id == module_id
        ).scalar() or 0

        version_record = ModuleVersion(
            id=generate_uuid(),
            module_id=module_id,
            version=new_version,
            version_number=max_version_num + 1,
            major_version=new_major,
            minor_version=new_minor,
            patch_version=new_patch,
            change_type=change_type,
            change_summary=change_summary,
            changelog=changelog,
            breaking_changes=breaking_changes,
            snapshot=snapshot,
            is_current=True,
            created_by=self.current_user.id
        )

        # Mark previous versions as not current
        self.db.query(ModuleVersion).filter(
            ModuleVersion.module_id == module_id,
            ModuleVersion.is_current == True
        ).update({"is_current": False})

        # Update module version
        module.version = new_version
        module.major_version = new_major
        module.minor_version = new_minor
        module.patch_version = new_patch
        module.updated_by = self.current_user.id
        module.updated_at = datetime.utcnow()

        self.db.add(version_record)
        self.db.commit()

        return True, f"Version updated to {new_version}", new_version

    async def list_versions(self, module_id: str) -> List[Dict]:
        """List all versions of a module"""

        versions = self.db.query(ModuleVersion).filter(
            ModuleVersion.module_id == module_id
        ).order_by(ModuleVersion.version_number.desc()).all()

        return [
            {
                "id": str(v.id),
                "version": v.version,
                "version_number": v.version_number,
                "change_type": v.change_type,
                "change_summary": v.change_summary,
                "changelog": v.changelog,
                "breaking_changes": v.breaking_changes,
                "is_current": v.is_current,
                "created_at": v.created_at.isoformat() if v.created_at else None,
                "created_by": str(v.created_by) if v.created_by else None
            }
            for v in versions
        ]

    # ==================== Helper Methods ====================

    def _module_to_dict(self, module: NocodeModule) -> Dict:
        """Convert module model to dictionary"""
        return {
            "id": str(module.id),
            "name": module.name,
            "display_name": module.display_name,
            "description": module.description,
            "version": module.version,
            "table_prefix": module.table_prefix,
            "category": module.category,
            "tags": module.tags,
            "icon": module.icon,
            "color": module.color,
            "status": module.status,
            "is_core": module.is_core,
            "is_template": module.is_template,
            "tenant_id": str(module.tenant_id) if module.tenant_id else None,
            "permissions": module.permissions,
            "config": module.configuration,
            "created_at": module.created_at.isoformat() if module.created_at else None,
            "updated_at": module.updated_at.isoformat() if module.updated_at else None,
            "published_at": module.published_at.isoformat() if module.published_at else None
        }

    def _is_valid_version(self, version_str: str) -> bool:
        """Validate semantic version format"""
        return bool(re.match(r'^\d+\.\d+\.\d+$', version_str))

    def _version_satisfies(self, version_str: str, constraint: str) -> bool:
        """Check if version satisfies constraint"""
        try:
            v = pkg_version.parse(version_str)

            if constraint.startswith('>='):
                min_v = pkg_version.parse(constraint[2:])
                return v >= min_v
            elif constraint.startswith('<'):
                max_v = pkg_version.parse(constraint[1:])
                return v < max_v
            elif constraint.startswith('=='):
                exact_v = pkg_version.parse(constraint[2:])
                return v == exact_v

            return False
        except:
            return False

    async def _has_circular_dependency(self, module_id: str, depends_on_id: str) -> bool:
        """Check for circular dependencies using DFS"""
        visited = set()

        def dfs(current_id: str) -> bool:
            if current_id == module_id:
                return True
            if current_id in visited:
                return False

            visited.add(current_id)

            # Get dependencies of current module
            deps = self.db.query(ModuleDependency).filter(
                ModuleDependency.module_id == current_id
            ).all()

            for dep in deps:
                if dfs(str(dep.depends_on_module_id)):
                    return True

            return False

        return dfs(depends_on_id)

    async def _create_module_snapshot(self, module: NocodeModule) -> Dict:
        """Create complete snapshot of module state"""
        from app.models.data_model import EntityDefinition
        from app.models.workflow import WorkflowDefinition
        from app.models.automation import AutomationRule
        from app.models.lookup import LookupConfiguration
        from app.models.report import ReportDefinition
        from app.models.dashboard import Dashboard

        # Fetch all components belonging to this module
        entities = self.db.query(EntityDefinition).filter(
            EntityDefinition.module_id == module.id
        ).all()

        workflows = self.db.query(WorkflowDefinition).filter(
            WorkflowDefinition.module_id == module.id
        ).all()

        automations = self.db.query(AutomationRule).filter(
            AutomationRule.module_id == module.id
        ).all()

        lookups = self.db.query(LookupConfiguration).filter(
            LookupConfiguration.module_id == module.id
        ).all()

        reports = self.db.query(ReportDefinition).filter(
            ReportDefinition.module_id == module.id
        ).all()

        dashboards = self.db.query(Dashboard).filter(
            Dashboard.module_id == module.id
        ).all()

        return {
            "module": {
                "name": module.name,
                "display_name": module.display_name,
                "version": module.version,
                "table_prefix": module.table_prefix,
                "category": module.category,
                "description": module.description
            },
            "entities": [{"id": str(e.id), "name": e.name} for e in entities],
            "workflows": [{"id": str(w.id), "name": w.name} for w in workflows],
            "automations": [{"id": str(a.id), "name": a.name} for a in automations],
            "lookups": [{"id": str(l.id), "name": l.name} for l in lookups],
            "reports": [{"id": str(r.id), "name": r.name} for r in reports],
            "dashboards": [{"id": str(d.id), "name": d.name} for d in dashboards],
            "component_counts": {
                "entities": len(entities),
                "workflows": len(workflows),
                "automations": len(automations),
                "lookups": len(lookups),
                "reports": len(reports),
                "dashboards": len(dashboards)
            }
        }


    # ==================== Validation Helpers ====================

    async def validate_prefix(self, table_prefix: str) -> Tuple[bool, str]:
        """Validate table prefix availability"""

        if not re.match(r'^[a-z0-9]{1,10}$', table_prefix):
            return False, "Table prefix must be 1-10 lowercase alphanumeric characters (no underscore)"

        existing = self.db.query(NocodeModule).filter(
            NocodeModule.table_prefix == table_prefix
        ).first()

        if existing:
            return False, f"Table prefix '{table_prefix}' already in use by module '{existing.name}'"

        return True, "Table prefix is available"

    async def validate_name(self, name: str, is_platform_level: bool = False) -> Tuple[bool, str]:
        """Validate module name availability"""

        if is_platform_level:
            existing_filter = NocodeModule.tenant_id == None
        else:
            existing_filter = or_(
                NocodeModule.tenant_id == self.tenant_id,
                NocodeModule.tenant_id == None
            )

        existing = self.db.query(NocodeModule).filter(
            existing_filter,
            NocodeModule.name == name
        ).first()

        if existing:
            scope = "platform-level" if existing.tenant_id is None else "tenant"
            return False, f"Module name '{name}' already exists at {scope} level"

        return True, "Module name is available"
