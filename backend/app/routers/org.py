from fastapi import APIRouter
router = APIRouter(prefix="/api/org", tags=["org"])

@router.get("/companies")
def list_companies():
    return {"message": "stub"}
