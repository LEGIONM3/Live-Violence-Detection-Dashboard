import torch
import torch.nn as nn
import numpy as np
import cv2
import os
import logging
import sys

# Monkeypatch for pytorchvideo compatibility with newer torchvision
import torchvision.transforms.functional as F
sys.modules["torchvision.transforms.functional_tensor"] = F

from pytorchvideo.models.hub import slowfast_r50

logger = logging.getLogger(__name__)

class SlowFastViolenceDetector:
    def __init__(self, weights_path='best_slowfast.pth', device=None):
        """
        Initializes the SlowFast Model for Real-Time Analysis.
        Adapted from backend/slowfast_project/slowfast_handler.py
        """
        self.device = device if device else ('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"Initializing SlowFast Detector on {self.device}...")
        
        # 1. Define Architecture
        self.model = slowfast_r50(pretrained=False) # Architecture only
        
        # 2. Modify Head to match training (Binary Class)
        # SlowFast R50 output dim is 2304
        self.model.blocks[-1].proj = nn.Linear(2304, 1)
        
        # 3. Load Weights
        # Resolve absolute path if relative provided
        if not os.path.exists(weights_path):
             # Finding 'backend' root. 
             # File is: .../backend/app/services/inference/slowfast_handler.py
             current_file = os.path.abspath(__file__)
             inference_dir = os.path.dirname(current_file)
             services_dir = os.path.dirname(inference_dir)
             app_dir = os.path.dirname(services_dir)
             backend_dir = os.path.dirname(app_dir)
             
             # Search candidates
             candidates = [
                 r"E:\live-violence-monitoring\backend\slowfast_project\best_slowfast.pth", # HARDCODED FAILSAFE
                 os.path.join(backend_dir, "slowfast_project", "best_slowfast.pth"),
                 os.path.join(backend_dir, "livecam", "best_slowfast.pth"),
                 "best_slowfast.pth"
             ]
             
             for candidate in candidates:
                 if os.path.exists(candidate):
                     weights_path = candidate
                     print(f"DEBUG: Found weights at: {weights_path}") # VISIBLE IN TERMINAL
                     break

        if os.path.exists(weights_path):
            try:
                checkpoint = torch.load(weights_path, map_location=self.device)
                if isinstance(checkpoint, dict) and 'state_dict' in checkpoint:
                     self.model.load_state_dict(checkpoint['state_dict'], strict=False)
                else:
                     self.model.load_state_dict(checkpoint, strict=False)
                logger.info(f"SlowFast Handler loaded weights from {weights_path}")
                print(f"DEBUG: SUCCESS - Weights loaded from {weights_path}")
            except Exception as e:
                logger.error(f"Failed to load weights: {e}")
                print(f"DEBUG: FAILED to load weights: {e}")
        else:
            logger.error(f"WARNING: Weights not found at {weights_path}. Model is untrained.")
            print(f"DEBUG: CRITICAL - Weights NOT FOUND. Predictions will be random.")
            
        self.model.to(self.device)
        self.model.eval()
        
        # Configs
        self.img_size = 256
        self.clip_len = 32
        self.sampling_rate = 2
        
        # Normalization constants (Kinetics-400 mean/std)
        self.mean = torch.tensor([0.45, 0.45, 0.45], device=self.device).view(3, 1, 1, 1)
        self.std = torch.tensor([0.225, 0.225, 0.225], device=self.device).view(3, 1, 1, 1)

    def preprocess_buffer(self, buffer):
        """
        Takes a list of raw BGR OpenCV frames (buffer).
        Returns the Slow and Fast pathway inputs.
        """
        # Ensure we have enough frames
        # We need CLIP_LEN * SAMPLING_RATE frames max context
        required_len = self.clip_len * self.sampling_rate
        
        if len(buffer) < required_len:
            # Not enough data yet
            return None
            
        # Get the recent window (last 64 frames for 32 frame input stride 2)
        window = list(buffer)[-required_len:]
        
        # Subsample: Take every 2nd frame to get 32 frames
        subsampled = [window[i * self.sampling_rate] for i in range(self.clip_len)]
        
        processed_frames = []
        for frame in subsampled:
            # Resize and Convert
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (self.img_size, self.img_size))
            processed_frames.append(frame)
            
        # Stack -> (T, H, W, C)
        clip = np.array(processed_frames)
        
        # Convert to Tensor -> (3, T, H, W)
        clip = torch.from_numpy(clip).permute(3, 0, 1, 2).float().to(self.device) / 255.0
        
        # Normalize
        clip = (clip - self.mean) / self.std
        
        return clip

    def predict(self, frame_buffer):
        """
        Main Inference API.
        Input: list of cv2 frames.
        Output: probability (float), label (str)
        """
        try:
            clip = self.preprocess_buffer(frame_buffer)
            
            if clip is None:
                return 0.0, "Buffering..."
                
            # Prepare Pathways
            # Fast Path: All 32 frames
            fast_path = clip.unsqueeze(0) # (1, 3, 32, 256, 256)
            
            # Slow Path: 1/4 frames = 8 frames
            # Index select with stride 4 relative to clip (which is already stride 2)
            indices = torch.linspace(0, clip.shape[1]-1, 8).long().to(self.device)
            slow_path = torch.index_select(clip, 1, indices).unsqueeze(0)
            
            with torch.no_grad():
                logits = self.model([slow_path, fast_path])
                prob = torch.sigmoid(logits).item()
                
            label = "Violence" if prob > 0.8 else "Normal"
            return prob, label

        except Exception as e:
            logger.error(f"Prediction logic error: {e}")
            return 0.0, "Error"
