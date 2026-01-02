from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.future import select
from sqlalchemy import delete
from app.core.database import get_db, AsyncSession
from app.models.history_log import DetectionHistory

router = APIRouter(prefix="/history", tags=["history"])

@router.get("/")
async def get_history(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DetectionHistory).order_by(DetectionHistory.timestamp.desc()))
    history = result.scalars().all()
    return history

@router.delete("/clear")
async def clear_history(db: AsyncSession = Depends(get_db)):
    # Task 4: Clear history button logic
    await db.execute(delete(DetectionHistory))
    await db.commit()
    return {"status": "history cleared"}

from pydantic import BaseModel

class HistoryCreate(BaseModel):
    camera_id: str
    result: bool
    confidence: float
    details: str = None

@router.post("/")
async def add_history(item: HistoryCreate, db: AsyncSession = Depends(get_db)):
    new_entry = DetectionHistory(
        camera_id=item.camera_id,
        result=item.result,
        confidence=item.confidence,
        details=item.details
    )
    db.add(new_entry)
    await db.commit()
    await db.refresh(new_entry)
    return new_entry
