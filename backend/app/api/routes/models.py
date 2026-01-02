from fastapi import APIRouter
from app.services.inference.model_manager import model_manager

router = APIRouter(prefix="/models", tags=["models"])

@router.get("/")
async def list_models():
    return model_manager.scan_models_directory()

@router.post("/active")
async def set_active_model(model_name: str):
    try:
        await model_manager.set_active_model(model_name)
        return {"status": "success", "active_model": model_name}
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to activate model: {str(e)}"}

@router.get("/active")
async def get_active_model():
    return {"active_model": model_manager.active_model}
