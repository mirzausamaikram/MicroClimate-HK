from fastapi import APIRouter

router = APIRouter()

@router.get("/models")
async def list_ml_models():
    """List available ML models"""
    return {
        "models": [
            {
                "id": "urban_canyon_v1",
                "type": "neural_network",
                "accuracy": 0.85
            },
            {
                "id": "sensor_fusion_v1",
                "type": "ensemble",
                "accuracy": 0.92
            }
        ]
    }
