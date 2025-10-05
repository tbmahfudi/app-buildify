from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class DataSearchRequest(BaseModel):
    """Request for searching/listing data"""
    entity: str
    filters: Optional[List[Dict[str, Any]]] = []
    sort: Optional[List[List[str]]] = []  # [["field", "asc/desc"]]
    page: int = 1
    page_size: int = 25
    search: Optional[str] = None  # Global search
    scope: Optional[Dict[str, Any]] = None  # Org scope filters

class DataSearchResponse(BaseModel):
    """Response for data search"""
    rows: List[Dict[str, Any]]
    total: int
    filtered: int
    page: int
    page_size: int

class DataCreateRequest(BaseModel):
    """Request to create a record"""
    entity: str
    data: Dict[str, Any]
    scope: Optional[Dict[str, Any]] = None

class DataUpdateRequest(BaseModel):
    """Request to update a record"""
    entity: str
    id: str
    data: Dict[str, Any]
    version: Optional[int] = None  # For optimistic locking

class DataResponse(BaseModel):
    """Single record response"""
    id: str
    data: Dict[str, Any]
    version: Optional[int] = None

class BulkOperationRequest(BaseModel):
    """Bulk operation request"""
    entity: str
    operation: str  # create, update, delete
    records: List[Dict[str, Any]]

class BulkOperationResponse(BaseModel):
    """Bulk operation response"""
    success: int
    failed: int
    errors: List[Dict[str, Any]] = []