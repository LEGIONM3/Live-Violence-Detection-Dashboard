from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float
from datetime import datetime
from app.core.database import Base

class DetectionHistory(Base):
    __tablename__ = "detection_history"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    camera_id = Column(String)
    result = Column(Boolean)  # True = Violence, False = Safe
    confidence = Column(Float)
    filename = Column(String, nullable=True) # Optional, if we save the clip
    details = Column(String, nullable=True)
    evidence_path = Column(String, nullable=True) # Path to video clip in Evidence folder
    analysis_result = Column(String, nullable=True) # Gemini analysis text

class LiveSessionLog(Base):
    __tablename__ = "live_session_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    camera_id = Column(String)
    result = Column(Boolean)
    confidence = Column(Float)
    
    # This table is cleared on restart
