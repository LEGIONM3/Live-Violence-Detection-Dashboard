
import cv2
import os
import torch
import numpy as np
import time
from pytorchvideo.models.hub import slowfast_r50
import torch.nn as nn

from slowfast_handler import SlowFastViolenceDetector

import httpx

def main():
    # Initialize Detector
    detector = SlowFastViolenceDetector(weights_path='best_slowfast.pth')

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Webcam not available.")
        return
    
    # We maintain a buffer of raw frames
    # Need at least 64 frames (32 * 2 stride)
    buffer_maxlen = 70 
    buffer = []
    
    print("Starting Live SlowFast Inference (Optimized Handler)... Press 'q' to quit.")
    
    last_report_time = 0
    REPORT_COOLDOWN = 5.0 # seconds
    
    while True:
        ret, frame = cap.read()
        if not ret: break
        
        # Add to buffer
        buffer.append(frame)
        if len(buffer) > buffer_maxlen:
            buffer.pop(0) # Keep fresh
            
        # Run Inference
        # The detector handles all preprocessing, normalization, and path splitting internally
        prob, label = detector.predict(buffer)
        print(f"Prediction: {label} ({prob:.2f})")

        # Report to Backend if Violence Detected
        if label == "Violence":
            current_time = time.time()
            if current_time - last_report_time > REPORT_COOLDOWN:
                try:
                    httpx.post(
                        "http://127.0.0.1:8000/api/v1/history/",
                        json={
                            "camera_id": "Webcam 1",
                            "result": True,
                            "confidence": prob,
                            "details": f"Violence detected with {prob:.2f} confidence."
                        },
                        timeout=1.0
                    )
                    print(" [Reported] Violence event logged to history.")
                    last_report_time = current_time
                except Exception as e:
                    print(f" [Error] Failed to report to backend: {e}")
        
        # Visualization
        color = (0, 0, 255) if prob > 0.8 else (0, 255, 0)
        text = f"{label} ({prob:.2f})"
        
        cv2.putText(frame, text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
        cv2.imshow("SlowFast Violence Guard", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
