"""
Report API router.
"""
import io
import logging
import os
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db, has_permission
from app.core.exceptions_helpers import not_found_exception
from app.core.response_builders import build_list_response
from app.models.user import User
from app.schemas.report import (
    ExportFormat,
    LookupDataRequest,
    LookupDataResponse,
    ReportDefinitionCreate,
    ReportDefinitionResponse,
    ReportDefinitionUpdate,
    ReportExecutionRequest,
    ReportExecutionResponse,
    ReportScheduleCreate,
    ReportScheduleResponse,
    ReportScheduleUpdate,
    ReportTemplateResponse,
)
from app.services.report_export import ReportExporter
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["reports"])
logger = logging.getLogger(__name__)


# Report Definition Endpoints

@router.post("/definitions", response_model=ReportDefinitionResponse, status_code=status.HTTP_201_CREATED)
def create_report_definition(
    report_data: ReportDefinitionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("reports:create:tenant"))
):
    """
    Create a new report definition.

    Requires permission: reports:create:tenant
    """
    try:
        report = ReportService.create_report_definition(
            db=db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
            report_data=report_data
        )
        return report
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/definitions", response_model=List[ReportDefinitionResponse])
def list_report_definitions(
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("reports:read:tenant"))
):
    """
    List all accessible report definitions.

    Requires permission: reports:read:tenant
    """
    reports = ReportService.list_report_definitions(
        db=db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        category=category,
        skip=skip,
        limit=limit
    )
    return reports


@router.get("/definitions/{report_id}", response_model=ReportDefinitionResponse)
def get_report_definition(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("reports:read:tenant"))
):
    """
    Get a specific report definition.

    Requires permission: reports:read:tenant
    """
    report = ReportService.get_report_definition(
        db=db,
        tenant_id=current_user.tenant_id,
        report_id=report_id,
        user_id=current_user.id
    )

    if not report:
        raise not_found_exception("Report", str(report_id))

    return report


@router.put("/definitions/{report_id}", response_model=ReportDefinitionResponse)
def update_report_definition(
    report_id: int,
    report_data: ReportDefinitionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("reports:update:own"))
):
    """
    Update a report definition.

    Requires permission: reports:update:own
    """
    report = ReportService.update_report_definition(
        db=db,
        tenant_id=current_user.tenant_id,
        report_id=report_id,
        report_data=report_data
    )

    if not report:
        raise not_found_exception("Report", str(report_id))

    return report


@router.delete("/definitions/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_report_definition(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("reports:delete:own"))
):
    """
    Delete a report definition (soft delete).

    Requires permission: reports:delete:own
    """
    success = ReportService.delete_report_definition(
        db=db,
        tenant_id=current_user.tenant_id,
        report_id=report_id
    )

    if not success:
        raise not_found_exception("Report", str(report_id))

    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Report Execution Endpoints

@router.post("/execute", response_model=ReportExecutionResponse)
def execute_report(
    request: ReportExecutionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("reports:execute:tenant"))
):
    """
    Execute a report and return results or export file.

    Requires permission: reports:execute:tenant
    """
    try:
        execution = ReportService.execute_report(
            db=db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
            request=request
        )
        return execution
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/execute/export")
def execute_and_export_report(
    request: ReportExecutionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("reports:export:tenant"))
):
    """
    Execute a report and return the exported file.

    Requires permission: reports:export:tenant
    """
    try:
        # Get report definition
        report_def = ReportService.get_report_definition(
            db=db,
            tenant_id=current_user.tenant_id,
            report_id=request.report_definition_id,
            user_id=current_user.id
        )

        if not report_def:
            raise not_found_exception("Report", str(request.report_definition_id))

        # Build and execute query
        query_result = ReportService._build_and_execute_query(
            db=db,
            tenant_id=current_user.tenant_id,
            report_def=report_def,
            parameters=request.parameters
        )

        # Export to requested format
        export_format = request.export_format or ExportFormat.PDF
        file_content, file_extension = ReportExporter.export_report(
            data=query_result['data'],
            columns=query_result['columns'],
            export_format=export_format.value,
            report_name=report_def.name,
            parameters=request.parameters,
            formatting_rules=report_def.formatting_rules
        )

        # Determine content type
        content_types = {
            'csv': 'text/csv',
            'json': 'application/json',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'pdf': 'application/pdf',
            'html': 'text/html'
        }
        content_type = content_types.get(file_extension, 'application/octet-stream')

        # Generate filename
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"{report_def.name.replace(' ', '_')}_{timestamp}.{file_extension}"

        # Return file as streaming response
        return StreamingResponse(
            io.BytesIO(file_content),
            media_type=content_type,
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"'
            }
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ImportError as e:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/executions/history")
def get_execution_history(
    report_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("reports:history:read:tenant"))
):
    """
    Get report execution history.

    Requires permission: reports:history:read:tenant
    """
    from app.models.report import ReportExecution

    query = db.query(ReportExecution).filter(
        ReportExecution.tenant_id == current_user.tenant_id
    )

    if report_id:
        query = query.filter(ReportExecution.report_definition_id == report_id)

    query = query.order_by(ReportExecution.executed_at.desc())
    executions = query.offset(skip).limit(limit).all()

    return executions


# Lookup Data Endpoints

@router.post("/lookup", response_model=LookupDataResponse)
def get_lookup_data(
    request: LookupDataRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get lookup data for report parameters."""
    try:
        result = ReportService.get_lookup_data(
            db=db,
            tenant_id=current_user.tenant_id,
            request=request
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# Report Schedule Endpoints

@router.post("/schedules", response_model=ReportScheduleResponse, status_code=status.HTTP_201_CREATED)
def create_report_schedule(
    schedule_data: ReportScheduleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("reports:schedule:create:tenant"))
):
    """
    Create a new report schedule.

    Requires permission: reports:schedule:create:tenant
    """
    from app.models.report import ReportSchedule

    # Verify report exists
    report = ReportService.get_report_definition(
        db=db,
        tenant_id=current_user.tenant_id,
        report_id=schedule_data.report_definition_id,
        user_id=current_user.id
    )

    if not report:
        raise not_found_exception("Report", str(schedule_data.report_definition_id))

    # Create schedule
    db_schedule = ReportSchedule(
        tenant_id=current_user.tenant_id,
        created_by=current_user.id,
        **schedule_data.model_dump()
    )
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)

    return db_schedule


@router.get("/schedules", response_model=List[ReportScheduleResponse])
def list_report_schedules(
    report_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("reports:schedule:read:tenant"))
):
    """
    List all report schedules.

    Requires permission: reports:schedule:read:tenant
    """
    from app.models.report import ReportSchedule

    query = db.query(ReportSchedule).filter(
        ReportSchedule.tenant_id == current_user.tenant_id
    )

    if report_id:
        query = query.filter(ReportSchedule.report_definition_id == report_id)

    schedules = query.offset(skip).limit(limit).all()
    return schedules


@router.put("/schedules/{schedule_id}", response_model=ReportScheduleResponse)
def update_report_schedule(
    schedule_id: int,
    schedule_data: ReportScheduleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("reports:schedule:update:own"))
):
    """
    Update a report schedule.

    Requires permission: reports:schedule:update:own
    """
    from app.models.report import ReportSchedule

    db_schedule = db.query(ReportSchedule).filter(
        ReportSchedule.id == schedule_id,
        ReportSchedule.tenant_id == current_user.tenant_id
    ).first()

    if not db_schedule:
        raise not_found_exception("Schedule", str(schedule_id))

    update_data = schedule_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_schedule, field, value)

    db.commit()
    db.refresh(db_schedule)
    return db_schedule


@router.delete("/schedules/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_report_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("reports:schedule:delete:own"))
):
    """
    Delete a report schedule.

    Requires permission: reports:schedule:delete:own
    """
    from app.models.report import ReportSchedule

    db_schedule = db.query(ReportSchedule).filter(
        ReportSchedule.id == schedule_id,
        ReportSchedule.tenant_id == current_user.tenant_id
    ).first()

    if not db_schedule:
        raise not_found_exception("Schedule", str(schedule_id))

    db.delete(db_schedule)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Report Templates Endpoints

@router.get("/templates", response_model=List[ReportTemplateResponse])
def list_report_templates(
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("reports:templates:read:tenant"))
):
    """
    List available report templates.

    Requires permission: reports:templates:read:tenant
    """
    from app.models.report import ReportTemplate

    query = db.query(ReportTemplate)

    if category:
        query = query.filter(ReportTemplate.category == category)

    templates = query.offset(skip).limit(limit).all()
    return templates


@router.post("/templates/{template_id}/use", response_model=ReportDefinitionResponse)
def create_from_template(
    template_id: int,
    name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("reports:templates:create:tenant"))
):
    """
    Create a new report from a template.

    Requires permission: reports:templates:create:tenant
    """
    from app.models.report import ReportDefinition, ReportTemplate

    template = db.query(ReportTemplate).filter(ReportTemplate.id == template_id).first()

    if not template:
        raise not_found_exception("Template", str(template_id))

    # Create report from template config
    template_config = template.template_config
    db_report = ReportDefinition(
        tenant_id=current_user.tenant_id,
        created_by=current_user.id,
        name=name,
        **template_config
    )
    db.add(db_report)

    # Update template usage count
    template.usage_count += 1

    db.commit()
    db.refresh(db_report)

    return db_report
