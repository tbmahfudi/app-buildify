import logging
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.audit import compute_diff, create_audit_log
from app.core.dependencies import get_current_user, get_db, has_role
from app.models.branch import Branch
from app.models.company import Company
from app.models.department import Department
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
)

router = APIRouter(prefix="/org", tags=["org"])
logger = logging.getLogger(__name__)

# ============= COMPANIES =============

@router.get("/companies", response_model=CompanyListResponse)
def list_companies(
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
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return CompanyListResponse(items=items, total=total)

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
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company

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
    existing = db.query(Company).filter(Company.code == company.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Company code already exists")

    db_company = Company(
        id=str(uuid.uuid4()),
        code=company.code,
        name=company.name
    )
    db.add(db_company)
    db.commit()
    db.refresh(db_company)

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
    db_company = db.query(Company).filter(Company.id == company_id).first()
    if not db_company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Capture before state
    before = {"code": db_company.code, "name": db_company.name}

    # Check for duplicate code if changing
    if company.code and company.code != db_company.code:
        existing = db.query(Company).filter(Company.code == company.code).first()
        if existing:
            raise HTTPException(status_code=400, detail="Company code already exists")

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
    db_company = db.query(Company).filter(Company.id == company_id).first()
    if not db_company:
        raise HTTPException(status_code=404, detail="Company not found")

    company_name = db_company.name

    db.delete(db_company)
    db.commit()

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
    company_id: str = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List branches, optionally filtered by company"""
    query = db.query(Branch)
    if company_id:
        query = query.filter(Branch.company_id == company_id)
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return BranchListResponse(items=items, total=total)

@router.get("/branches/{branch_id}", response_model=BranchResponse)
def get_branch(
    branch_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific branch"""
    branch = db.query(Branch).filter(Branch.id == branch_id).first()
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")
    return branch

@router.post("/branches", response_model=BranchResponse, status_code=status.HTTP_201_CREATED)
def create_branch(
    branch: BranchCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_role("admin"))
):
    """Create a new branch (admin only)"""
    # Verify company exists
    company = db.query(Company).filter(Company.id == branch.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Check for duplicate code within company
    existing = db.query(Branch).filter(
        Branch.company_id == branch.company_id,
        Branch.code == branch.code
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Branch code already exists in this company")

    db_branch = Branch(
        id=str(uuid.uuid4()),
        company_id=branch.company_id,
        code=branch.code,
        name=branch.name
    )
    db.add(db_branch)
    db.commit()
    db.refresh(db_branch)

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
    db_branch = db.query(Branch).filter(Branch.id == branch_id).first()
    if not db_branch:
        raise HTTPException(status_code=404, detail="Branch not found")

    # Capture before state
    before = {"code": db_branch.code, "name": db_branch.name}

    # Check for duplicate code if changing
    if branch.code and branch.code != db_branch.code:
        existing = db.query(Branch).filter(
            Branch.company_id == db_branch.company_id,
            Branch.code == branch.code
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Branch code already exists in this company")

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
    db_branch = db.query(Branch).filter(Branch.id == branch_id).first()
    if not db_branch:
        raise HTTPException(status_code=404, detail="Branch not found")

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
    company_id: str = None,
    branch_id: str = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List departments, optionally filtered by company/branch"""
    query = db.query(Department)
    if company_id:
        query = query.filter(Department.company_id == company_id)
    if branch_id:
        query = query.filter(Department.branch_id == branch_id)
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return DepartmentListResponse(items=items, total=total)

@router.get("/departments/{department_id}", response_model=DepartmentResponse)
def get_department(
    department_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific department"""
    dept = db.query(Department).filter(Department.id == department_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    return dept

@router.post("/departments", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
def create_department(
    department: DepartmentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_role("admin"))
):
    """Create a new department (admin only)"""
    # Verify company exists
    company = db.query(Company).filter(Company.id == department.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Verify branch exists if provided
    if department.branch_id:
        branch = db.query(Branch).filter(Branch.id == department.branch_id).first()
        if not branch:
            raise HTTPException(status_code=404, detail="Branch not found")
        # Ensure branch belongs to the same company
        if branch.company_id != department.company_id:
            raise HTTPException(status_code=400, detail="Branch does not belong to this company")

    # Check for duplicate code within company
    existing = db.query(Department).filter(
        Department.company_id == department.company_id,
        Department.code == department.code
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Department code already exists in this company")

    db_dept = Department(
        id=str(uuid.uuid4()),
        company_id=department.company_id,
        branch_id=department.branch_id,
        code=department.code,
        name=department.name
    )
    db.add(db_dept)
    db.commit()
    db.refresh(db_dept)

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
    db_dept = db.query(Department).filter(Department.id == department_id).first()
    if not db_dept:
        raise HTTPException(status_code=404, detail="Department not found")

    # Capture before state
    before = {"code": db_dept.code, "name": db_dept.name, "branch_id": db_dept.branch_id}

    # Check for duplicate code if changing
    if department.code and department.code != db_dept.code:
        existing = db.query(Department).filter(
            Department.company_id == db_dept.company_id,
            Department.code == department.code
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Department code already exists in this company")

    # Verify branch if changing
    if department.branch_id is not None and department.branch_id != db_dept.branch_id:
        if department.branch_id:  # Not setting to None
            branch = db.query(Branch).filter(Branch.id == department.branch_id).first()
            if not branch:
                raise HTTPException(status_code=404, detail="Branch not found")
            if branch.company_id != db_dept.company_id:
                raise HTTPException(status_code=400, detail="Branch does not belong to this company")

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
    db_dept = db.query(Department).filter(Department.id == department_id).first()
    if not db_dept:
        raise HTTPException(status_code=404, detail="Department not found")

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

@router.get("/tenants")
def list_tenants(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all tenants - superuser only"""
    # Only superusers can list tenants
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Only superusers can list tenants")

    from app.models.tenant import Tenant

    query = db.query(Tenant)
    total = query.count()
    items = query.offset(skip).limit(limit).all()

    return {
        "items": [
            {
                "id": str(t.id),
                "name": t.name,
                "is_active": t.is_active,
                "created_at": t.created_at.isoformat() if t.created_at else None
            }
            for t in items
        ],
        "total": total
    }


# ============= USERS =============

@router.get("/users")
def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all users - superusers see all, regular users see their tenant"""
    query = db.query(User)

    # Filter by tenant for non-superusers
    if not current_user.is_superuser:
        if current_user.tenant_id:
            query = query.filter(User.tenant_id == current_user.tenant_id)
        else:
            # Non-superuser without tenant - return empty
            return {"items": [], "total": 0}

    total = query.count()
    items = query.offset(skip).limit(limit).all()

    return {
        "items": [
            {
                "id": str(u.id),
                "email": u.email,
                "full_name": u.full_name,
                "is_active": u.is_active,
                "is_superuser": u.is_superuser,
                "tenant_id": str(u.tenant_id) if u.tenant_id else None,
                "created_at": u.created_at.isoformat() if u.created_at else None
            }
            for u in items
        ],
        "total": total
    }