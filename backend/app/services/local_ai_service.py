
import logging
import json
import base64
import cv2
import asyncio
import httpx
import os
from app.core.config import settings

logger = logging.getLogger(__name__)

class LocalAIService:
    def __init__(self):
        self.base_url = settings.LOCAL_MODEL_API_URL
        self.model = settings.LOCAL_MODEL_NAME

    def _extract_frames(self, video_path, num_frames=8):
        """Extract 'num_frames' evenly spaced from the video."""
        frames_b64 = []
        try:
            cap = cv2.VideoCapture(video_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if total_frames <= 0: return []
            
            step = max(1, total_frames // num_frames)
            
            for i in range(0, total_frames, step):
                if len(frames_b64) >= num_frames: break
                cap.set(cv2.CAP_PROP_POS_FRAMES, i)
                ret, frame = cap.read()
                if ret:
                    # Encode to jpg
                    _, buffer = cv2.imencode('.jpg', frame)
                    b64 = base64.b64encode(buffer).decode('utf-8')
                    frames_b64.append(b64)
            cap.release()
        except Exception as e:
            logger.error(f"Frame extraction failed: {e}")
            
        return frames_b64

    async def analyze_frame_batch(self, base64_frames: list[str], camera_id: str) -> str:
        """
        Analyze a sequence of frames (Batch) to understand temporal context.
        """
        # Construct content for sequence
        # Construct content for sequence
        # Moondream Prompt Engineering for Violence Detection
        # 1. We ask for specific visual cues of aggression.
        # 2. We explicitly list examples of violence to 'wake up' the model's recognition.
        prompt = """
        Analyze this video sequence for SECURITY THREATS. 
        Focus on:
        - Physical Aggression (punching, kicking, pushing, grappling)
        - Weapons (guns, knives, bats)
        - Distress (people falling, fleeing, scared)
        
        Return a valid JSON object.
        JSON Schema:
        {
          "is_violent": boolean, 
          "confidence_score": number (0-1),
          "actions": ["list", "of", "actions"],
          "visual_summary": "Concise description of the event"
        }
        """

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a specialized Surveillance AI. Your ONLY purpose is to detect violence, fighting, and weapons. You must be accurate and not ignore threats. Return ONLY valid JSON."
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        # Flatten the list of images into the User message correctly
                        *[{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img}"}} for img in base64_frames]
                    ]
                }
            ],
            "max_tokens": 512, 
            "temperature": 0.1 # Keep low for JSON stability
        }
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return data['choices'][0]['message']['content']
                else:
                    logger.error(f"AI Server Error {resp.status_code}: {resp.text}")
                    return f"Error {resp.status_code}: {resp.text}"
        except Exception as e:
            logger.error(f"Batch analysis failed: {e}")
            return "Batch Analysis Timeout/Error"

    async def analyze_video(self, video_path: str, camera_id: str) -> str:
        # Legacy method for full video
        # ... (keep existing implementation or deprecate)
        return await super().analyze_video(video_path, camera_id)

local_ai_service = LocalAIService()
