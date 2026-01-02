
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.services.camera_service import camera_service
from app.services.ws_manager import ws_manager
from fastapi import WebSocket, WebSocketDisconnect
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cameras", tags=["cameras"])

class PhoneCamConfig(BaseModel):
    url: str

@router.get("/")
async def list_cameras():
    # Helper to check if active
    def is_active(cid):
        cam = camera_service.cameras.get(cid)
        return cam.is_running if cam else False
        
    # Helper to get URL for phone cam (id "1")
    phone_url = ""
    if "1" in camera_service.cameras:
        phone_url = camera_service.cameras["1"].source
        
    return [
        {"id": "0", "name": "PC Webcam", "active": is_active("0")},
        {"id": "1", "name": "Phone Camera", "active": is_active("1"), "url": phone_url}
    ]

@router.post("/phone/config")
async def config_phone_camera(config: PhoneCamConfig):
    # Re-initialize camera 1 with new URL
    camera_service.add_camera("1", config.url)
    return {"status": "configured", "url": config.url}

@router.post("/{camera_id}/toggle")
async def toggle_camera(camera_id: str, enable: bool):
    if enable:
        success = camera_service.start_camera(camera_id)
        return {"status": "started" if success else "failed", "camera_id": camera_id}
    else:
        camera_service.stop_camera(camera_id)
        return {"status": "stopped", "camera_id": camera_id}

@router.get("/{camera_id}/feed")
async def video_feed(camera_id: str):
    """
    Stream video feed with bounding boxes.
    """
    return StreamingResponse(
        camera_service.get_stream_generator(camera_id),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WS Error: {e}")
        ws_manager.disconnect(websocket)


