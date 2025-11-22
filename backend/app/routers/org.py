import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.audit import compute_diff, create_audit_log
from app.core.crud_helpers import (
    check_duplicate_code,
    create_entity_with_uuid,
    get_entity_by_id,
    validate_parent_exists,
)
from app.core.dependencies import get_current_user, get_db, has_role
from app.core.exceptions_helpers import (
    duplicate_exception,
    not_found_exception,
    permission_denied_exception,
    relationship_violation_exception,
)
from app.core.response_builders import build_list_response
from app.models.branch import Branch
from app.models.company import Company
from app.models.department import Department
from app.models.rbac import Group, Role, UserGroup, UserRole
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.auth import UserResponse
from app.schemas.org import (
    BranchCreate,
    BranchListResponse,
    BranchResponse,
    BranchUpdate,
    CompanyCreate,
    CompanyListResponse,
    CompanyResponse,
    CompanyUpdate,
    DepartmentCreate,
    DepartmentListResponse,
    DepartmentResponse,
    DepartmentUpdate,
    TenantCreate,
    TenantListResponse,
    TenantResponse,
    TenantUpdate,
)

router = APIRouter(prefix="/org", tags=["org"])
logger = logging.getLogger(__name__)

# ============= COMPANIES =============

@router.get("/companies", response_model=CompanyListResponse)
def list_companies(
    tenant_id: str = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all companies with pagination.

    Retrieves a paginated list of all companies in the system.
    Requires authentication but no specific role.

    Args:
        tenant_id: Optional tenant UUID to filter by
        skip: Number of records to skip (default: 0)
        limit: Maximum number of records to return (default: 100, max: 1000)
        db: Database session (injected)
        current_user: Authenticated user (injected)

    Returns:
        CompanyListResponse: Object containing:
            - items: List of Company objects
            - total: Total count of companies in database

    Example Response:
        {
            "items": [
                {"id": "uuid...", "code": "ACME", "name": "Acme Corp"},
                {"id": "uuid...", "code": "INITECH", "name": "Initech Inc"}
            ],
            "total": 2
        }
    """
    query = db.query(Company)
    if tenant_id:
        query = query.filter(Company.tenant_id == tenant_id)
    return build_list_response(query, skip, limit)

@router.get("/companies/{company_id}", response_model=CompanyResponse)
def get_company(
    company_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific company by ID.

    Retrieves detailed information for a single company.
    Requires authentication but no specific role.

    Args:
        company_id: UUID of the company to retrieve
        db: Database session (injected)
        current_user: Authenticated user (injected)

    Returns:
        CompanyResponse: Company object with all fields

    Raises:
        HTTPException 404: Company not found
        HTTPException 401: Not authenticated

    Example Response:
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "code": "ACME",
            "name": "Acme Corporation",
            "created_at": "2023-11-12T10:30:00Z"
        }
    """
    return get_entity_by_id(db, Company, company_id, "Company")

@router.post("/companies", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
def create_company(
    company: CompanyCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_role("admin"))
):
    """
    Create a new company (admin only).

    Creates a new company record in the system. Automatically generates
    a UUID for the company and creates an audit log entry.

    Permissions Required:
        - Role: admin

    Args:
        company: Company creation data
            - code: Unique company code (required)
            - name: Company name (required)
        request: HTTP request object (injected, for audit logging)
        db: Database session (injected)
        current_user: Authenticated admin user (injected)

    Returns:
        CompanyResponse: Newly created company object

    Raises:
        HTTPException 400: Company code already exists
        HTTPException 403: User does not have admin role
        HTTPException 401: Not authenticated
        HTTPException 422: Validation error (invalid data)

    Example Request:
        POST /api/org/companies
        {
            "code": "ACME",
            "name": "Acme Corporation"
        }

    Example Response (201 Created):
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "code": "ACME",
            "name": "Acme Corporation",
            "created_at": "2023-11-12T10:30:00Z"
        }
    """
    # Check for duplicate code
    check_duplicate_code(db, Company, company.code)

    # Create company
    db_company = create_entity_with_uuid(db, Company, company.dict())

    # Update tenant's current_companies count
    if db_company.tenant_id:
        tenant = db.query(Tenant).filter(Tenant.id == db_company.tenant_id).first()
        if tenant:
            tenant.current_companies = db.query(Company).filter(
                Company.tenant_id == tenant.id,
                Company.deleted_at.is_(None)
            ).count()
            db.commit()
            db.refresh(tenant)

    # Audit company creation
    create_audit_log(
        db=db,
        action="create",
        user=current_user,
        entity_type="company",
        entity_id=str(db_company.id),
        changes={"name": company.name, "code": company.code},
        request=request,
        status="success"
    )

    return db_company

@router.put("/companies/{company_id}", response_model=CompanyResponse)
def update_company(
    company_id: str,
    company: CompanyUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_role("admin"))
):
    """Update a company (admin only)"""
    db_company = get_entity_by_id(db, Company, company_id, "Company")

    # Capture before state
    before = {"code": db_company.code, "name": db_company.name}

    # Check for duplicate code if changing
    if company.code and company.code != db_company.code:
        check_duplicate_code(db, Company, company.code)

    if company.code is not None:
        db_company.code = company.code
    if company.name is not None:
        db_company.name = company.name

    # Capture after state
    after = {"code": db_company.code, "name": db_company.name}

    db.commit()
    db.refresh(db_company)

    # Audit company update
    create_audit_log(
        db=db,
        action="update",
        user=current_user,
        entity_type="company",
        entity_id=company_id,
        changes=compute_diff(before, after),
        request=request,
        status="success"
    )

    return db_company

@router.delete("/companies/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_company(
    company_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_role("admin"))
):
    """Delete a company (admin only)"""
    db_company = get_entity_by_id(db, Company, company_id, "Company")

    company_name = db_company.name
    tenant_id = db_company.tenant_id

    db.delete(db_company)
    db.commit()

    # Update tenant's current_companies count
    if tenant_id:
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if tenant:
            tenant.current_companies = db.query(Company).filter(
                Company.tenant_id == tenant.id,
                Company.deleted_at.is_(None)
            ).count()
            db.commit()
            db.refresh(tenant)

    # Audit company deletion
    create_audit_log(
        db=db,
        action="delete",
        user=current_user,
        entity_type="company",
        entity_id=company_id,
        context_info={"name": company_name},
        request=request,
        status="success"
    )

    return None

# ============= BRANCHES =============

@router.get("/branches", response_model=BranchListResponse)
def list_branches(
    tenant_id: str = None,
    company_id: str = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List branches, optionally filtered by tenant and/or company"""
    query = db.query(Branch)
    if tenant_id:
        query = query.filter(Branch.tenant_id == tenant_id)
    if company_id:
        query = query.filter(Branch.company_id == company_id)
    return build_list_response(query, skip, limit)

@router.get("/branches/{branch_id}", response_model=BranchResponse)
def get_branch(
    branch_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific branch"""
    return get_entity_by_id(db, Branch, branch_id, "Branch")

@router.post("/branches", response_model=BranchResponse, status_code=status.HTTP_201_CREATED)
def create_branch(
    branch: BranchCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_role("admin"))
):
    """Create a new branch (admin only)"""
    # Verify company exists and get tenant_id from it
    company = validate_parent_exists(db, Company, branch.company_id, "Company")

    # Check for duplicate code within company
    check_duplicate_code(db, Branch, branch.code, "company_id", branch.company_id)

    # Create branch with tenant_id from parent company
    branch_data = branch.dict()
    branch_data['tenant_id'] = company.tenant_id
    db_branch = create_entity_with_uuid(db, Branch, branch_data)

    # Audit branch creation
    create_audit_log(
        db=db,
        action="create",
        user=current_user,
        entity_type="branch",
        entity_id=str(db_branch.id),
        changes={"name": branch.name, "code": branch.code, "company_id": branch.company_id},
        request=request,
        status="success"
    )

    return db_branch

@router.put("/branches/{branch_id}", response_model=BranchResponse)
def update_branch(
    branch_id: str,
    branch: BranchUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_role("admin"))
):
    """Update a branch (admin only)"""
    db_branch = get_entity_by_id(db, Branch, branch_id, "Branch")

    # Capture before state
    before = {"code": db_branch.code, "name": db_branch.name}

    # Check for duplicate code if changing
    if branch.code and branch.code != db_branch.code:
        check_duplicate_code(db, Branch, branch.code, "company_id", db_branch.company_id)

    if branch.code is not None:
        db_branch.code = branch.code
    if branch.name is not None:
        db_branch.name = branch.name

    # Capture after state
    after = {"code": db_branch.code, "name": db_branch.name}

    db.commit()
    db.refresh(db_branch)

    # Audit branch update
    create_audit_log(
        db=db,
        action="update",
        user=current_user,
        entity_type="branch",
        entity_id=branch_id,
        changes=compute_diff(before, after),
        request=request,
        status="success"
    )

    return db_branch

@router.delete("/branches/{branch_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_branch(
    branch_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_role("admin"))
):
    """Delete a branch (admin only)"""
    db_branch = get_entity_by_id(db, Branch, branch_id, "Branch")

    branch_name = db_branch.name

    db.delete(db_branch)
    db.commit()

    # Audit branch deletion
    create_audit_log(
        db=db,
        action="delete",
        user=current_user,
        entity_type="branch",
        entity_id=branch_id,
        context_info={"name": branch_name},
        request=request,
        status="success"
    )

    return None

# ============= DEPARTMENTS =============

@router.get("/departments", response_model=DepartmentListResponse)
def list_departments(
    tenant_id: str = None,
    company_id: str = None,
    branch_id: str = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List departments, optionally filtered by tenant, company, and/or branch"""
    query = db.query(Department)
    if tenant_id:
        query = query.filter(Department.tenant_id == tenant_id)
    if company_id:
        query = query.filter(Department.company_id == company_id)
    if branch_id:
        query = query.filter(Department.branch_id == branch_id)
    return build_list_response(query, skip, limit)

@router.get("/departments/{department_id}", response_model=DepartmentResponse)
def get_department(
    department_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific department"""
    return get_entity_by_id(db, Department, department_id, "Department")

@router.post("/departments", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
def create_department(
    department: DepartmentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_role("admin"))
):
    """Create a new department (admin only)"""
    # Verify company exists and get tenant_id from it
    company = validate_parent_exists(db, Company, department.company_id, "Company")

    # Verify branch exists if provided
    if department.branch_id:
        branch = validate_parent_exists(db, Branch, department.branch_id, "Branch")
        # Ensure branch belongs to the same company (convert to strings for comparison)
        if str(branch.company_id) != str(department.company_id):
            raise relationship_violation_exception("Company", "Branch", "Branch does not belong to this company")

    # Check for duplicate code within company
    check_duplicate_code(db, Department, department.code, "company_id", department.company_id)

    # Create department with tenant_id from parent company
    dept_data = department.dict()
    dept_data['tenant_id'] = company.tenant_id
    db_dept = create_entity_with_uuid(db, Department, dept_data)

    # Audit department creation
    create_audit_log(
        db=db,
        action="create",
        user=current_user,
        entity_type="department",
        entity_id=str(db_dept.id),
        changes={"name": department.name, "code": department.code, "company_id": department.company_id, "branch_id": department.branch_id},
        request=request,
        status="success"
    )

    return db_dept

@router.put("/departments/{department_id}", response_model=DepartmentResponse)
def update_department(
    department_id: str,
    department: DepartmentUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_role("admin"))
):
    """Update a department (admin only)"""
    db_dept = get_entity_by_id(db, Department, department_id, "Department")

    # Capture before state
    before = {"code": db_dept.code, "name": db_dept.name, "branch_id": db_dept.branch_id}

    # Check for duplicate code if changing
    if department.code and department.code != db_dept.code:
        check_duplicate_code(db, Department, department.code, "company_id", db_dept.company_id)

    # Verify branch if changing
    if department.branch_id is not None and department.branch_id != db_dept.branch_id:
        if department.branch_id:  # Not setting to None
            branch = validate_parent_exists(db, Branch, department.branch_id, "Branch")
            if branch.company_id != db_dept.company_id:
                raise relationship_violation_exception("Company", "Branch", "Branch does not belong to this company")

    if department.branch_id is not None:
        db_dept.branch_id = department.branch_id
    if department.code is not None:
        db_dept.code = department.code
    if department.name is not None:
        db_dept.name = department.name

    # Capture after state
    after = {"code": db_dept.code, "name": db_dept.name, "branch_id": db_dept.branch_id}

    db.commit()
    db.refresh(db_dept)

    # Audit department update
    create_audit_log(
        db=db,
        action="update",
        user=current_user,
        entity_type="department",
        entity_id=department_id,
        changes=compute_diff(before, after),
        request=request,
        status="success"
    )

    return db_dept

@router.delete("/departments/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_department(
    department_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_role("admin"))
):
    """Delete a department (admin only)"""
    db_dept = get_entity_by_id(db, Department, department_id, "Department")

    dept_name = db_dept.name

    db.delete(db_dept)
    db.commit()

    # Audit department deletion
    create_audit_log(
        db=db,
        action="delete",
        user=current_user,
        entity_type="department",
        entity_id=department_id,
        context_info={"name": dept_name},
        request=request,
        status="success"
    )

    return None


# ============= TENANTS =============

@router.get("/tenants", response_model=TenantListResponse)
def list_tenants(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all tenants - superuser only"""
    # Only superusers can list tenants
    if not current_user.is_superuser:
        raise permission_denied_exception("list", "tenants")

    from app.models.tenant import Tenant

    query = db.query(Tenant).filter(Tenant.deleted_at.is_(None))
    result = build_list_response(query, skip, limit)

    # Format items for response
    return {
        "items": [
            {
                "id": str(t.id),
                "name": t.name,
                "code": t.code,
                "description": t.description,
                "subscription_tier": t.subscription_tier,
                "subscription_status": t.subscription_status,
                "subscription_start": t.subscription_start,
                "subscription_end": t.subscription_end,
                "max_companies": t.max_companies,
                "max_users": t.max_users,
                "max_storage_gb": t.max_storage_gb,
                "current_companies": t.current_companies,
                "current_users": t.current_users,
                "current_storage_gb": t.current_storage_gb,
                "is_active": t.is_active,
                "is_trial": t.is_trial,
                "contact_name": t.contact_name,
                "contact_email": t.contact_email,
                "contact_phone": t.contact_phone,
                "logo_url": t.logo_url,
                "primary_color": t.primary_color,
                "created_at": t.created_at,
                "updated_at": t.updated_at
            }
            for t in result["items"]
        ],
        "total": result["total"]
    }


@router.get("/tenants/{tenant_id}", response_model=TenantResponse)
def get_tenant(
    tenant_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific tenant - superuser only"""
    if not current_user.is_superuser:
        raise permission_denied_exception("view", "tenant")

    from app.models.tenant import Tenant
    from uuid import UUID

    try:
        tenant_uuid = UUID(tenant_id)
    except ValueError:
        raise not_found_exception("Tenant")

    tenant = db.query(Tenant).filter(
        Tenant.id == tenant_uuid,
        Tenant.deleted_at.is_(None)
    ).first()

    if not tenant:
        raise not_found_exception("Tenant")

    return {
        "id": str(tenant.id),
        "name": tenant.name,
        "code": tenant.code,
        "description": tenant.description,
        "subscription_tier": tenant.subscription_tier,
        "subscription_status": tenant.subscription_status,
        "subscription_start": tenant.subscription_start,
        "subscription_end": tenant.subscription_end,
        "max_companies": tenant.max_companies,
        "max_users": tenant.max_users,
        "max_storage_gb": tenant.max_storage_gb,
        "current_companies": tenant.current_companies,
        "current_users": tenant.current_users,
        "current_storage_gb": tenant.current_storage_gb,
        "is_active": tenant.is_active,
        "is_trial": tenant.is_trial,
        "contact_name": tenant.contact_name,
        "contact_email": tenant.contact_email,
        "contact_phone": tenant.contact_phone,
        "logo_url": tenant.logo_url,
        "primary_color": tenant.primary_color,
        "created_at": tenant.created_at,
        "updated_at": tenant.updated_at
    }


@router.post("/tenants", response_model=TenantResponse, status_code=201)
def create_tenant(
    tenant: TenantCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new tenant - superuser only"""
    if not current_user.is_superuser:
        raise permission_denied_exception("create", "tenant")

    from app.models.tenant import Tenant

    # Check if code already exists
    existing = db.query(Tenant).filter(Tenant.code == tenant.code).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Tenant with code '{tenant.code}' already exists"
        )

    # Create new tenant
    new_tenant = Tenant(
        name=tenant.name,
        code=tenant.code,
        description=tenant.description,
        subscription_tier=tenant.subscription_tier or "free",
        subscription_status=tenant.subscription_status or "active",
        max_companies=tenant.max_companies or 10,
        max_users=tenant.max_users or 500,
        max_storage_gb=tenant.max_storage_gb or 10,
        is_active=tenant.is_active if tenant.is_active is not None else True,
        is_trial=tenant.is_trial or False,
        contact_name=tenant.contact_name,
        contact_email=tenant.contact_email,
        contact_phone=tenant.contact_phone,
        logo_url=tenant.logo_url,
        primary_color=tenant.primary_color
    )

    db.add(new_tenant)
    db.commit()
    db.refresh(new_tenant)

    return {
        "id": str(new_tenant.id),
        "name": new_tenant.name,
        "code": new_tenant.code,
        "description": new_tenant.description,
        "subscription_tier": new_tenant.subscription_tier,
        "subscription_status": new_tenant.subscription_status,
        "subscription_start": new_tenant.subscription_start,
        "subscription_end": new_tenant.subscription_end,
        "max_companies": new_tenant.max_companies,
        "max_users": new_tenant.max_users,
        "max_storage_gb": new_tenant.max_storage_gb,
        "current_companies": new_tenant.current_companies,
        "current_users": new_tenant.current_users,
        "current_storage_gb": new_tenant.current_storage_gb,
        "is_active": new_tenant.is_active,
        "is_trial": new_tenant.is_trial,
        "contact_name": new_tenant.contact_name,
        "contact_email": new_tenant.contact_email,
        "contact_phone": new_tenant.contact_phone,
        "logo_url": new_tenant.logo_url,
        "primary_color": new_tenant.primary_color,
        "created_at": new_tenant.created_at,
        "updated_at": new_tenant.updated_at
    }


@router.put("/tenants/{tenant_id}", response_model=TenantResponse)
def update_tenant(
    tenant_id: str,
    tenant_update: TenantUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a tenant - superuser only"""
    if not current_user.is_superuser:
        raise permission_denied_exception("update", "tenant")

    from app.models.tenant import Tenant
    from uuid import UUID

    try:
        tenant_uuid = UUID(tenant_id)
    except ValueError:
        raise not_found_exception("Tenant")

    tenant = db.query(Tenant).filter(
        Tenant.id == tenant_uuid,
        Tenant.deleted_at.is_(None)
    ).first()

    if not tenant:
        raise not_found_exception("Tenant")

    # Check if code is being changed and if it conflicts
    if tenant_update.code and tenant_update.code != tenant.code:
        existing = db.query(Tenant).filter(Tenant.code == tenant_update.code).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Tenant with code '{tenant_update.code}' already exists"
            )

    # Update fields
    update_data = tenant_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tenant, field, value)

    db.commit()
    db.refresh(tenant)

    return {
        "id": str(tenant.id),
        "name": tenant.name,
        "code": tenant.code,
        "description": tenant.description,
        "subscription_tier": tenant.subscription_tier,
        "subscription_status": tenant.subscription_status,
        "subscription_start": tenant.subscription_start,
        "subscription_end": tenant.subscription_end,
        "max_companies": tenant.max_companies,
        "max_users": tenant.max_users,
        "max_storage_gb": tenant.max_storage_gb,
        "current_companies": tenant.current_companies,
        "current_users": tenant.current_users,
        "current_storage_gb": tenant.current_storage_gb,
        "is_active": tenant.is_active,
        "is_trial": tenant.is_trial,
        "contact_name": tenant.contact_name,
        "contact_email": tenant.contact_email,
        "contact_phone": tenant.contact_phone,
        "logo_url": tenant.logo_url,
        "primary_color": tenant.primary_color,
        "created_at": tenant.created_at,
        "updated_at": tenant.updated_at
    }


@router.delete("/tenants/{tenant_id}", status_code=204)
def delete_tenant(
    tenant_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a tenant (soft delete) - superuser only"""
    if not current_user.is_superuser:
        raise permission_denied_exception("delete", "tenant")

    from app.models.tenant import Tenant
    from uuid import UUID
    from datetime import datetime

    try:
        tenant_uuid = UUID(tenant_id)
    except ValueError:
        raise not_found_exception("Tenant")

    tenant = db.query(Tenant).filter(
        Tenant.id == tenant_uuid,
        Tenant.deleted_at.is_(None)
    ).first()

    if not tenant:
        raise not_found_exception("Tenant")

    # Soft delete
    tenant.deleted_at = datetime.utcnow()
    db.commit()

    return None


# ============= USERS =============

@router.get("/users")
def list_users(
    skip: int = 0,
    limit: int = 100,
    include_roles: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all users - superusers see all, regular users see their tenant"""
    from sqlalchemy.orm import joinedload

    query = db.query(User)

    # Eager load roles and groups if requested
    if include_roles:
        query = query.options(
            joinedload(User.user_roles).joinedload(UserRole.role),
            joinedload(User.user_groups).joinedload(UserGroup.group)
        )

    # Filter by tenant for non-superusers
    if not current_user.is_superuser:
        if current_user.tenant_id:
            query = query.filter(User.tenant_id == current_user.tenant_id)
        else:
            # Non-superuser without tenant - return empty
            return {"items": [], "total": 0}

    result = build_list_response(query, skip, limit)

    # Format items for response
    items = []
    for u in result["items"]:
        user_data = {
            "id": str(u.id),
            "email": u.email,
            "full_name": u.full_name,
            "is_active": u.is_active,
            "is_superuser": u.is_superuser,
            "tenant_id": str(u.tenant_id) if u.tenant_id else None,
            "created_at": u.created_at.isoformat() if u.created_at else None
        }

        # Add roles and groups if requested
        if include_roles:
            # Get direct roles
            direct_roles = [
                {
                    "id": str(ur.role.id),
                    "name": ur.role.name,
                    "code": ur.role.code
                }
                for ur in u.user_roles if ur.role and ur.role.is_active
            ]

            # Get groups
            groups = [
                {
                    "id": str(ug.group.id),
                    "name": ug.group.name
                }
                for ug in u.user_groups if ug.group and ug.group.is_active
            ]

            user_data["roles"] = direct_roles
            user_data["groups"] = groups

        items.append(user_data)

    return {
        "items": items,
        "total": result["total"]
    }