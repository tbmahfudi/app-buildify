"""
Dashboard API router.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.dashboard import (
    DashboardCreate,
    DashboardUpdate,
    DashboardResponse,
    DashboardSummary,
    DashboardPageCreate,
    DashboardPageUpdate,
    DashboardPageResponse,
    DashboardWidgetCreate,
    DashboardWidgetUpdate,
    DashboardWidgetResponse,
    WidgetDataRequest,
    WidgetDataResponse,
    DashboardShareCreate,
    DashboardShareResponse,
    DashboardSnapshotCreate,
    DashboardSnapshotResponse,
    BulkWidgetUpdateRequest,
    DashboardCloneRequest
)
from app.services.dashboard_service import DashboardService


router = APIRouter(prefix="/dashboards", tags=["dashboards"])


# ==================== Dashboard Endpoints ====================

@router.post("", response_model=DashboardResponse, status_code=status.HTTP_201_CREATED)
def create_dashboard(
    dashboard_data: DashboardCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new dashboard."""
    try:
        dashboard = DashboardService.create_dashboard(
            db=db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
            dashboard_data=dashboard_data
        )
        return dashboard
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=List[DashboardSummary])
def list_dashboards(
    category: Optional[str] = None,
    favorites_only: bool = False,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all accessible dashboards."""
    dashboards = DashboardService.list_dashboards(
        db=db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        category=category,
        favorites_only=favorites_only,
        skip=skip,
        limit=limit
    )

    # Convert to summary format
    summaries = []
    for dashboard in dashboards:
        summaries.append(DashboardSummary(
            id=dashboard.id,
            name=dashboard.name,
            description=dashboard.description,
            category=dashboard.category,
            tags=dashboard.tags,
            is_public=dashboard.is_public,
            is_favorite=dashboard.is_favorite,
            created_by=dashboard.created_by,
            created_at=dashboard.created_at,
            updated_at=dashboard.updated_at,
            page_count=len(dashboard.pages)
        ))

    return summaries


@router.get("/{dashboard_id}", response_model=DashboardResponse)
def get_dashboard(
    dashboard_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific dashboard with all pages and widgets."""
    dashboard = DashboardService.get_dashboard(
        db=db,
        tenant_id=current_user.tenant_id,
        dashboard_id=dashboard_id,
        user_id=current_user.id
    )

    if not dashboard:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found")

    return dashboard


@router.put("/{dashboard_id}", response_model=DashboardResponse)
def update_dashboard(
    dashboard_id: int,
    dashboard_data: DashboardUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a dashboard."""
    dashboard = DashboardService.update_dashboard(
        db=db,
        tenant_id=current_user.tenant_id,
        dashboard_id=dashboard_id,
        dashboard_data=dashboard_data
    )

    if not dashboard:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found")

    return dashboard


@router.delete("/{dashboard_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dashboard(
    dashboard_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a dashboard (soft delete)."""
    success = DashboardService.delete_dashboard(
        db=db,
        tenant_id=current_user.tenant_id,
        dashboard_id=dashboard_id
    )

    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found")

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{dashboard_id}/clone", response_model=DashboardResponse)
def clone_dashboard(
    dashboard_id: int,
    clone_request: DashboardCloneRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Clone an existing dashboard."""
    dashboard = DashboardService.clone_dashboard(
        db=db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        dashboard_id=dashboard_id,
        new_name=clone_request.name
    )

    if not dashboard:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found")

    return dashboard


# ==================== Dashboard Page Endpoints ====================

@router.post("/pages", response_model=DashboardPageResponse, status_code=status.HTTP_201_CREATED)
def create_page(
    page_data: DashboardPageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new dashboard page."""
    try:
        page = DashboardService.create_page(
            db=db,
            tenant_id=current_user.tenant_id,
            page_data=page_data
        )
        return page
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/pages/{page_id}", response_model=DashboardPageResponse)
def update_page(
    page_id: int,
    page_data: DashboardPageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a dashboard page."""
    page = DashboardService.update_page(
        db=db,
        tenant_id=current_user.tenant_id,
        page_id=page_id,
        page_data=page_data
    )

    if not page:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Page not found")

    return page


@router.delete("/pages/{page_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_page(
    page_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a dashboard page."""
    success = DashboardService.delete_page(
        db=db,
        tenant_id=current_user.tenant_id,
        page_id=page_id
    )

    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Page not found")

    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ==================== Dashboard Widget Endpoints ====================

@router.post("/widgets", response_model=DashboardWidgetResponse, status_code=status.HTTP_201_CREATED)
def create_widget(
    widget_data: DashboardWidgetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new dashboard widget."""
    try:
        widget = DashboardService.create_widget(
            db=db,
            tenant_id=current_user.tenant_id,
            widget_data=widget_data
        )
        return widget
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/widgets/{widget_id}", response_model=DashboardWidgetResponse)
def update_widget(
    widget_id: int,
    widget_data: DashboardWidgetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a dashboard widget."""
    widget = DashboardService.update_widget(
        db=db,
        tenant_id=current_user.tenant_id,
        widget_id=widget_id,
        widget_data=widget_data
    )

    if not widget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Widget not found")

    return widget


@router.delete("/widgets/{widget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_widget(
    widget_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a dashboard widget."""
    success = DashboardService.delete_widget(
        db=db,
        tenant_id=current_user.tenant_id,
        widget_id=widget_id
    )

    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Widget not found")

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/widgets/bulk-update")
def bulk_update_widgets(
    bulk_request: BulkWidgetUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Bulk update widget positions and order (for drag-drop)."""
    try:
        success = DashboardService.bulk_update_widgets(
            db=db,
            tenant_id=current_user.tenant_id,
            updates=bulk_request.updates
        )
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ==================== Widget Data Endpoints ====================

@router.post("/widgets/data", response_model=WidgetDataResponse)
def get_widget_data(
    data_request: WidgetDataRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get data for a specific widget. Reuses ReportService for report-based widgets."""
    try:
        result = DashboardService.get_widget_data(
            db=db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
            widget_id=data_request.widget_id,
            parameters=data_request.parameters,
            use_cache=data_request.use_cache
        )

        return WidgetDataResponse(
            widget_id=data_request.widget_id,
            data=result['data'],
            metadata={'widget_type': result.get('widget_type')},
            cached=result.get('cached', False),
            execution_time_ms=result.get('execution_time_ms')
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ==================== Dashboard Sharing Endpoints ====================

@router.post("/shares", response_model=DashboardShareResponse, status_code=status.HTTP_201_CREATED)
def create_share(
    share_data: DashboardShareCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Share a dashboard with a user or role."""
    try:
        share = DashboardService.create_share(
            db=db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
            share_data=share_data
        )
        return share
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ==================== Dashboard Snapshot Endpoints ====================

@router.post("/snapshots", response_model=DashboardSnapshotResponse, status_code=status.HTTP_201_CREATED)
def create_snapshot(
    snapshot_data: DashboardSnapshotCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a snapshot of a dashboard at a specific point in time."""
    try:
        snapshot = DashboardService.create_snapshot(
            db=db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
            snapshot_data=snapshot_data
        )
        return snapshot
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
