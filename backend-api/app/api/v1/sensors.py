from fastapi import APIRouter

router = APIRouter()

@router.post("/readings")
async def submit_sensor_reading():
    """Submit sensor reading from crowdsourced device"""
    return {"status": "accepted"}
