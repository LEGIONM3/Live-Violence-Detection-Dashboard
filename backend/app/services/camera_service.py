
import cv2
import logging
import asyncio
import time
import threading
from collections import deque
from typing import Dict, Optional

from app.services.inference.slowfast_handler import SlowFastViolenceDetector
from app.services.ws_manager import ws_manager
from app.core.database import AsyncSessionLocal
from app.models.history_log import DetectionHistory

logger = logging.getLogger(__name__)

class CameraStream:
    def __init__(self, c_id, source):
        self.id = c_id
        self.source = source
        self.cap = None
        self.is_running = False
        
        # Threading
        self.thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()
        self.loop = None
        
        # Detector (Using the Safe SlowFast Handler)
        # Note: Weights must exist at backend/livecam/best_slowfast.pth
        self.detector = SlowFastViolenceDetector(weights_path='best_slowfast.pth')
        
        # State
        self.latest_frame_bytes = None
        self.frame_buffer = deque(maxlen=70) # User requested buffer maxlen = 70
        self.frame_count = 0 
        
        # Visualization State (Persist last prediction)
        self.last_text = "Initializing..."
        self.last_color = (0, 255, 0)
        
        # Smoothing Queue (Last 5 predictions)
        self.pred_queue = deque(maxlen=5)

    def start(self):
        if self.is_running: return True
        
        # Open Camera
        src = self.source
        if isinstance(src, str) and src.isdigit(): src = int(src)
        self.cap = cv2.VideoCapture(src)
        if not self.cap.isOpened():
            logger.error(f"Failed to open camera {self.id}")
            return False

        # Get Event Loop
        try:
            self.loop = asyncio.get_running_loop()
        except RuntimeError:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

        self.is_running = True
        
        # Thread 1: Capture & Streaming (Fast)
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.capture_thread.start()
        
        # Thread 2: Inference (Heavy)
        self.inference_thread = threading.Thread(target=self._inference_loop, daemon=True)
        self.inference_thread.start()
        
        logger.info(f"Camera {self.id} started (Decoupled: Capture + Inference threads).")
        return True

    def stop(self):
        self.is_running = False
        # Join both threads
        if self.capture_thread:
            self.capture_thread.join(timeout=1.0)
            self.capture_thread = None
        if self.inference_thread:
            self.inference_thread.join(timeout=1.0)
            self.inference_thread = None
            
        if self.cap:
            self.cap.release()
            self.cap = None

    def _capture_loop(self):
        """
        High-Speed Loop: Reads frames, draws OSD, updates stream.
        Does NOT wait for inference.
        """
        while self.is_running and self.cap:
            ret, frame = self.cap.read()
            if not ret:
                time.sleep(0.01)
                continue
            
            # 1. Visualization (Draw stored result)
            # Use cached text/color from the inference thread
            cv2.putText(frame, self.last_text, (20, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, self.last_color, 2)

            # 2. Add to Buffer (Thread-Safe)
            with self.lock:
                self.frame_buffer.append(frame)
                self.frame_count += 1
                
                # 3. Update Monitor Stream immediately
                _, buf = cv2.imencode('.jpg', frame)
                self.latest_frame_bytes = (b'--frame\r\n' 
                                           b'Content-Type: image/jpeg\r\n\r\n' + buf.tobytes() + b'\r\n')
            
            # Run as fast as possible
            time.sleep(0.005)

    def _inference_loop(self):
        """
        Inference Loop: Polls buffer, predicts, updates shared OSD state.
        """
        while self.is_running:
            # 1. Get Clip safely
            clip = None
            with self.lock:
                 if len(self.frame_buffer) >= 32:
                     clip = list(self.frame_buffer)
            
            if clip:
                try:
                    start = time.time()
                    # Run Inference (Blocks THIS thread, not video)
                    prob, _ = self.detector.predict(clip) # Ignore detector label, make our own logic
                    self.pred_queue.append(prob)
                    
                    # SMOOTHING (Average last 5 predictions)
                    avg_prob = sum(self.pred_queue) / len(self.pred_queue)
                    
                    # Logic: Trigger if AVERAGE > 0.8
                    label = "Violence" if avg_prob > 0.8 else "Normal"
                    
                    lat = time.time() - start
                    
                    # Update Shared Visualization State
                    # Show Avg prob to user so they see the smoothed value
                    self.last_text = f"{label} ({avg_prob:.2f})"
                    self.last_color = (0, 0, 255) if label == "Violence" else (0, 255, 0)
                    
                    # Broadcast
                    if self.loop:
                         asyncio.run_coroutine_threadsafe(
                            self._broadcast_result(avg_prob, label, lat), 
                            self.loop
                        )
                except Exception as e:
                    logger.error(f"Inference error: {e}")
            else:
                # Buffer not ready
                pass
                
            # Yield slightly to avoid CPU pinning if model is extremely fast, 
            # or simply wait for next frames
            time.sleep(0.02)

    async def _broadcast_result(self, prob, label, latency):
        is_violent = (label == "Violence")
        
        # --- SIMPLE LOGIC: RED OR GREEN ---
        if is_violent:
            # 1. Update Monitor Status (RED)
            await ws_manager.broadcast({
                "type": "alert_confirmed",
                "camera_id": self.id,
                "text": f"SlowFast: VIOLENCE ({prob:.2f})", # Shows on UI Report
                "latency": f"{latency:.2f}s"
            })
            # 2. Log History
             # (Optional: Only log periodically to avoid spamming DB)
            await self._save_log(prob)
            
        else:
            # 1. Update Monitor Status (GREEN)
            await ws_manager.broadcast({
                "type": "inference_status", # UI maps this to Secure/Suspicious
                "status": "secure", 
                "camera_id": self.id,
                "message": f"Normal Activity ({prob:.2f})"
            })

    async def _save_log(self, conf):
        try:
             async with AsyncSessionLocal() as db:
                entry = DetectionHistory(
                    camera_id=f"Cam {self.id}",
                    result=True,
                    confidence=float(conf),
                    details="SlowFast Live Detection",
                    evidence_path="Live Stream",
                    analysis_result="Direct Inference"
                )
                db.add(entry)
                await db.commit()
        except: pass

class CameraService:
    def __init__(self):
        self.cameras: Dict[str, CameraStream] = {}
        # Auto-add default cam
        self.add_camera("0", 0) 

    def add_camera(self, c_id, source):
        # Stop existing if replacing
        if c_id in self.cameras:
            self.cameras[c_id].stop()
        self.cameras[c_id] = CameraStream(c_id, source)
        
    def start_camera(self, c_id):
        if c_id in self.cameras: return self.cameras[c_id].start()
        return False
        
    def stop_camera(self, c_id):
        if c_id in self.cameras: self.cameras[c_id].stop()

    async def get_stream_generator(self, c_id):
        cam = self.cameras.get(c_id)
        if not cam: return
        # Auto-start on stream request
        if not cam.is_running: cam.start()
        
        while cam.is_running:
            frame_data = None
            with cam.lock:
                frame_data = cam.latest_frame_bytes
            if frame_data: 
                yield frame_data
            else:
                # If no frame yet, wait a bit
                await asyncio.sleep(0.01)
                continue
            await asyncio.sleep(0.01) # Try to stream as fast as possible

camera_service = CameraService()
