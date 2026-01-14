from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_alerts():
    """Get active weather alerts"""
    return {"alerts": []}
