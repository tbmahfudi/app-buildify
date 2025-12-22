"""
Builder Pages API Router

Handles CRUD operations for builder pages, versioning, and publishing.
"""

import uuid
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from pydantic import BaseModel, Field

from app.core.dependencies import get_db, get_current_user
from app.models.builder_page import BuilderPage, BuilderPageVersion
from app.models.user import User


router = APIRouter()


# Pydantic models for request/response
class PageCreate(BaseModel):
    """Schema for creating a new page."""
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    module_name: Optional[str] = None
    route_path: str = Field(..., min_length=1)
    grapejs_data: dict
    html_output: Optional[str] = None
    css_output: Optional[str] = None
    js_output: Optional[str] = None
    menu_label: Optional[str] = None
    menu_icon: Optional[str] = None
    menu_parent: Optional[str] = None
    menu_order: Optional[int] = None
    show_in_menu: bool = True
    permission_code: Optional[str] = None
    permission_scope: str = "company"


class PageUpdate(BaseModel):
    """Schema for updating a page."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    slug: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    module_name: Optional[str] = None
    route_path: Optional[str] = None
    grapejs_data: Optional[dict] = None
    html_output: Optional[str] = None
    css_output: Optional[str] = None
    js_output: Optional[str] = None
    menu_label: Optional[str] = None
    menu_icon: Optional[str] = None
    menu_parent: Optional[str] = None
    menu_order: Optional[int] = None
    show_in_menu: Optional[bool] = None
    permission_code: Optional[str] = None
    permission_scope: Optional[str] = None


class PagePublish(BaseModel):
    """Schema for publishing a page."""
    commit_message: Optional[str] = None


@router.get("/", response_model=List[dict])
async def list_pages(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    module_name: Optional[str] = Query(None),
    published_only: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    List all builder pages with optional filtering.

    - **module_name**: Filter by module
    - **published_only**: Show only published pages
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    """
    tenant_id = str(current_user.tenant_id)

    # Build query
    query = db.query(BuilderPage).filter(BuilderPage.tenant_id == tenant_id)

    if module_name:
        query = query.filter(BuilderPage.module_name == module_name)

    if published_only:
        query = query.filter(BuilderPage.published == True)

    query = query.order_by(desc(BuilderPage.created_at)).offset(skip).limit(limit)

    pages = query.all()

    return [page.to_dict() for page in pages]


@router.get("/{page_id}", response_model=dict)
async def get_page(
    page_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific page by ID.
    """
    tenant_id = str(current_user.tenant_id)

    page = db.query(BuilderPage).filter(
        and_(
            BuilderPage.id == page_id,
            BuilderPage.tenant_id == tenant_id
        )
    ).first()

    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    return page.to_dict()


@router.post("/", response_model=dict, status_code=201)
async def create_page(
    page_data: PageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new builder page.
    """
    tenant_id = str(current_user.tenant_id)
    user_id = str(current_user.id)

    # Check for duplicate slug
    existing = db.query(BuilderPage).filter(
        and_(
            BuilderPage.tenant_id == tenant_id,
            BuilderPage.slug == page_data.slug
        )
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Page with this slug already exists")

    # Check for duplicate route path
    route_exists = db.query(BuilderPage).filter(
        and_(
            BuilderPage.tenant_id == tenant_id,
            BuilderPage.route_path == page_data.route_path
        )
    ).first()
    if route_exists:
        raise HTTPException(status_code=409, detail="Page with this route already exists")

    # Create page
    page = BuilderPage(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        created_by=user_id,
        **page_data.dict()
    )

    db.add(page)
    db.commit()
    db.refresh(page)

    return page.to_dict()


@router.put("/{page_id}", response_model=dict)
async def update_page(
    page_id: str,
    page_data: PageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing page.
    """
    tenant_id = str(current_user.tenant_id)
    user_id = str(current_user.id)

    # Get existing page
    page = db.query(BuilderPage).filter(
        and_(
            BuilderPage.id == page_id,
            BuilderPage.tenant_id == tenant_id
        )
    ).first()

    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    # Check for slug conflicts if slug is being changed
    if page_data.slug and page_data.slug != page.slug:
        slug_exists = db.query(BuilderPage).filter(
            and_(
                BuilderPage.tenant_id == tenant_id,
                BuilderPage.slug == page_data.slug,
                BuilderPage.id != page_id
            )
        ).first()
        if slug_exists:
            raise HTTPException(status_code=409, detail="Page with this slug already exists")

    # Update fields
    update_data = page_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(page, field, value)

    page.updated_by = user_id

    db.commit()
    db.refresh(page)

    return page.to_dict()


@router.delete("/{page_id}", status_code=204)
async def delete_page(
    page_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a page and all its versions.
    """
    tenant_id = str(current_user.tenant_id)

    page = db.query(BuilderPage).filter(
        and_(
            BuilderPage.id == page_id,
            BuilderPage.tenant_id == tenant_id
        )
    ).first()

    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    db.delete(page)
    db.commit()

    return None


@router.post("/{page_id}/publish", response_model=dict)
async def publish_page(
    page_id: str,
    publish_data: PagePublish,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Publish a page (creates a version snapshot).
    """
    tenant_id = str(current_user.tenant_id)
    user_id = str(current_user.id)

    # Get page
    page = db.query(BuilderPage).filter(
        and_(
            BuilderPage.id == page_id,
            BuilderPage.tenant_id == tenant_id
        )
    ).first()

    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    # Get latest version number
    latest_version = db.query(BuilderPageVersion).filter(
        BuilderPageVersion.page_id == page_id
    ).order_by(desc(BuilderPageVersion.version_number)).first()

    next_version_number = 1
    if latest_version:
        next_version_number = latest_version.version_number + 1

    # Create version snapshot
    version = BuilderPageVersion(
        id=str(uuid.uuid4()),
        page_id=page_id,
        version_number=next_version_number,
        grapejs_data=page.grapejs_data,
        html_output=page.html_output,
        css_output=page.css_output,
        js_output=page.js_output,
        commit_message=publish_data.commit_message,
        created_by=user_id
    )

    db.add(version)

    # Update page publish status
    page.published = True
    page.published_at = datetime.utcnow()
    page.published_by = user_id

    db.commit()
    db.refresh(page)

    return page.to_dict()


@router.post("/{page_id}/unpublish", response_model=dict)
async def unpublish_page(
    page_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Unpublish a page (keeps versions).
    """
    tenant_id = str(current_user.tenant_id)

    page = db.query(BuilderPage).filter(
        and_(
            BuilderPage.id == page_id,
            BuilderPage.tenant_id == tenant_id
        )
    ).first()

    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    page.published = False

    db.commit()
    db.refresh(page)

    return page.to_dict()


@router.get("/{page_id}/versions", response_model=List[dict])
async def list_page_versions(
    page_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """
    List all versions of a page.
    """
    tenant_id = str(current_user.tenant_id)

    # Verify page exists and belongs to tenant
    page = db.query(BuilderPage).filter(
        and_(
            BuilderPage.id == page_id,
            BuilderPage.tenant_id == tenant_id
        )
    ).first()

    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    # Get versions
    versions = db.query(BuilderPageVersion).filter(
        BuilderPageVersion.page_id == page_id
    ).order_by(desc(BuilderPageVersion.version_number)).offset(skip).limit(limit).all()

    return [version.to_dict() for version in versions]


@router.get("/{page_id}/versions/{version_number}", response_model=dict)
async def get_page_version(
    page_id: str,
    version_number: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific version of a page.
    """
    tenant_id = str(current_user.tenant_id)

    # Verify page exists
    page = db.query(BuilderPage).filter(
        and_(
            BuilderPage.id == page_id,
            BuilderPage.tenant_id == tenant_id
        )
    ).first()

    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    # Get version
    version = db.query(BuilderPageVersion).filter(
        and_(
            BuilderPageVersion.page_id == page_id,
            BuilderPageVersion.version_number == version_number
        )
    ).first()

    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    return version.to_dict()


@router.post("/{page_id}/restore/{version_number}", response_model=dict)
async def restore_page_version(
    page_id: str,
    version_number: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Restore a page to a previous version.
    """
    tenant_id = str(current_user.tenant_id)
    user_id = str(current_user.id)

    # Get page
    page = db.query(BuilderPage).filter(
        and_(
            BuilderPage.id == page_id,
            BuilderPage.tenant_id == tenant_id
        )
    ).first()

    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    # Get version to restore
    version = db.query(BuilderPageVersion).filter(
        and_(
            BuilderPageVersion.page_id == page_id,
            BuilderPageVersion.version_number == version_number
        )
    ).first()

    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    # Restore version data to page
    page.grapejs_data = version.grapejs_data
    page.html_output = version.html_output
    page.css_output = version.css_output
    page.js_output = version.js_output
    page.updated_by = user_id

    db.commit()
    db.refresh(page)

    return page.to_dict()
