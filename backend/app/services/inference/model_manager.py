
import os
import logging
from typing import List, Dict, Any, Optional
import numpy as np
import cv2
import pickle
import asyncio
import torch
import torch.nn as nn
from torchvision import transforms
from torchvision.models.video import r3d_18

logger = logging.getLogger(__name__)

# ==================================================================================
# 1. MODEL ARCHITECTURES (RESTORED FOR COMPATIBILITY)
# ==================================================================================

class ViolenceConv3D(nn.Module):
    def __init__(self, num_classes=2):
        super(ViolenceConv3D, self).__init__()
        self.conv1 = nn.Conv3d(3, 32, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm3d(32)
        self.pool1 = nn.MaxPool3d(kernel_size=(1, 2, 2), stride=(1, 2, 2))
        self.conv2 = nn.Conv3d(32, 64, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm3d(64)
        self.pool2 = nn.MaxPool3d(kernel_size=(2, 2, 2), stride=(2, 2, 2))
        self.conv3 = nn.Conv3d(64, 128, kernel_size=3, padding=1)
        self.bn3 = nn.BatchNorm3d(128)
        self.pool3 = nn.MaxPool3d(kernel_size=(2, 2, 2), stride=(2, 2, 2))
        self.conv4 = nn.Conv3d(128, 256, kernel_size=3, padding=1)
        self.bn4 = nn.BatchNorm3d(256)
        self.pool4 = nn.MaxPool3d(kernel_size=(2, 2, 2), stride=(2, 2, 2))
        
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(0.5)
        self.fc1 = nn.Linear(25088, 512)
        self.fc2 = nn.Linear(512, num_classes)

    def forward(self, x):
        x = self.relu(self.bn1(self.conv1(x)))
        x = self.pool1(x)
        x = self.relu(self.bn2(self.conv2(x)))
        x = self.pool2(x)
        x = self.relu(self.bn3(self.conv3(x)))
        x = self.pool3(x)
        x = self.relu(self.bn4(self.conv4(x)))
        x = self.pool4(x)
        x = x.reshape(x.size(0), -1)  
        x = self.dropout(self.relu(self.fc1(x)))
        x = self.fc2(x)
        return x

class ViolenceGRU(nn.Module):
    def __init__(self, num_classes=2):
        super(ViolenceGRU, self).__init__()
        self.conv1 = nn.Conv2d(3, 32, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm2d(32)
        self.pool1 = nn.MaxPool2d(2, 2)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm2d(64)
        self.pool2 = nn.MaxPool2d(2, 2)
        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, padding=1)
        self.bn3 = nn.BatchNorm2d(128)
        self.pool3 = nn.MaxPool2d(2, 2)
        self.conv4 = nn.Conv2d(128, 256, kernel_size=3, padding=1)
        self.bn4 = nn.BatchNorm2d(256)
        self.pool4 = nn.MaxPool2d(2, 2)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(0.5)
        self.gru = nn.GRU(12544, 256, num_layers=2, batch_first=True, dropout=0.5)
        self.fc = nn.Linear(256, num_classes)

    def forward(self, x):
        b, c, t, h, w = x.size()
        c_in = x.reshape(b * t, c, h, w)  
        x = self.relu(self.bn1(self.conv1(c_in)))
        x = self.pool1(x)
        x = self.relu(self.bn2(self.conv2(x)))
        x = self.pool2(x)
        x = self.relu(self.bn3(self.conv3(x)))
        x = self.pool3(x)
        x = self.relu(self.bn4(self.conv4(x)))
        x = self.pool4(x)
        x = x.reshape(x.size(0), -1)  
        x = x.reshape(b, t, -1)  
        out, _ = self.gru(x)
        out = out[:, -1, :]
        return self.fc(out)

class TwoStreamNetwork(nn.Module):
    def __init__(self, num_classes=2):
        super(TwoStreamNetwork, self).__init__()
        self.rgb_stream = r3d_18(weights=None)
        self.flow_stream = r3d_18(weights=None)
        self.rgb_stream.fc = nn.Linear(512, 512)
        self.flow_stream.fc = nn.Linear(512, 512)
        self.fusion_fc = nn.Sequential(
            nn.Linear(1024, 512),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(512, num_classes)
        )
    def forward(self, x_rgb, x_flow):
        f_rgb = self.rgb_stream(x_rgb)
        f_flow = self.flow_stream(x_flow)
        combined = torch.cat((f_rgb, f_flow), dim=1)
        return self.fusion_fc(combined)

class SlowFastNetwork(nn.Module):
    def __init__(self, num_classes=2):
        super(SlowFastNetwork, self).__init__()
        # Fast Path
        self.fast_conv1 = nn.Conv3d(3, 8, kernel_size=(5, 7, 7), stride=(1, 2, 2), padding=(2, 3, 3))
        self.fast_bn1 = nn.BatchNorm3d(8)
        self.fast_conv2 = nn.Conv3d(8, 16, kernel_size=3, padding=1)
        self.fast_bn2 = nn.BatchNorm3d(16)
        self.fast_conv3 = nn.Conv3d(16, 32, kernel_size=3, padding=1)
        self.fast_bn3 = nn.BatchNorm3d(32)
        
        # Slow Path
        self.slow_conv1 = nn.Conv3d(3, 64, kernel_size=(1, 7, 7), stride=(1, 2, 2), padding=(0, 3, 3))
        self.slow_bn1 = nn.BatchNorm3d(64)
        self.slow_conv2 = nn.Conv3d(80, 128, kernel_size=(1, 3, 3), padding=(0, 1, 1)) 
        self.slow_bn2 = nn.BatchNorm3d(128)
        self.slow_conv3 = nn.Conv3d(192, 256, kernel_size=(1, 3, 3), padding=(0, 1, 1))
        self.slow_bn3 = nn.BatchNorm3d(256)
        
        # Laterals
        self.lateral1 = nn.Conv3d(8, 16, kernel_size=(5, 1, 1), padding=(2, 0, 0)) 
        self.lateral2 = nn.Conv3d(16, 64, kernel_size=(5, 1, 1), padding=(2, 0, 0))
        
        self.relu = nn.ReLU(inplace=True)
        self.avg_pool = nn.AdaptiveAvgPool3d((1, 1, 1))
        self.dropout = nn.Dropout(0.5)
        self.fc = nn.Linear(288, num_classes)

    def forward(self, x):
        fast_input = x
        slow_input = x[:, :, ::4, :, :] 
        
        # --- Stage 1 ---
        x_fast = self.relu(self.fast_bn1(self.fast_conv1(fast_input)))
        x_slow = self.relu(self.slow_bn1(self.slow_conv1(slow_input)))
        lat1 = self.lateral1(x_fast)
        if lat1.shape[2] != x_slow.shape[2]:
            lat1 = nn.functional.interpolate(lat1, size=(x_slow.shape[2], x_slow.shape[3], x_slow.shape[4]), mode='nearest')
        x_slow = torch.cat([x_slow, lat1], dim=1)
        
        # --- Stage 2 ---
        x_fast = self.relu(self.fast_bn2(self.fast_conv2(x_fast)))
        x_slow = self.relu(self.slow_bn2(self.slow_conv2(x_slow))) 
        lat2 = self.lateral2(x_fast)
        if lat2.shape[2] != x_slow.shape[2]:
             lat2 = nn.functional.interpolate(lat2, size=(x_slow.shape[2], x_slow.shape[3], x_slow.shape[4]), mode='nearest')
        x_slow = torch.cat([x_slow, lat2], dim=1)
        
        # --- Stage 3 ---
        x_fast = self.relu(self.fast_bn3(self.fast_conv3(x_fast)))
        x_slow = self.relu(self.slow_bn3(self.slow_conv3(x_slow)))
        
        # --- Head ---
        x_fast = self.avg_pool(x_fast)
        x_slow = self.avg_pool(x_slow)
        x_fast = x_fast.view(x_fast.size(0), -1)
        x_slow = x_slow.view(x_slow.size(0), -1)
        feat = torch.cat([x_fast, x_slow], dim=1)
        feat = self.dropout(feat)
        return self.fc(feat)

# Safe Pickle Shim
class CustomUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        if module == "__main__":
            if name == 'ViolenceGRU': return ViolenceGRU
            if name == 'SlowFastNetwork': return SlowFastNetwork
            if name == 'ViolenceConv3D': return ViolenceConv3D
            if name == 'TwoStreamNetwork': return TwoStreamNetwork
        return super().find_class(module, name)

class SafePickle:
    Unpickler = CustomUnpickler
    @staticmethod
    def load(file, **kwargs):
        return CustomUnpickler(file, **kwargs).load()

# ==================================================================================
# 2. MODEL MANAGER
# ==================================================================================

class ModelManager:
    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # ACTIVE MODEL (For Authenticator / Testing other architectures)
        self.active_model = None
        self.active_model_name = None
        self.loaded_models = {}

        # Paths
        current_dir = os.path.abspath(__file__)
        self.backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
        self.models_dir = os.path.join(self.backend_dir, "models")
        # Livecam dir reference removed as we don't load from it here anymore

    # --- PUBLIC API FOR FRONTEND (MODELS TAB) ---

    def scan_models_directory(self) -> List[Dict[str, str]]:
        if not os.path.exists(self.models_dir):
            os.makedirs(self.models_dir)
        models = []
        for filename in os.listdir(self.models_dir):
            if filename.endswith(('.pth', '.pt', '.h5')):
                models.append({
                    "name": filename,
                    "path": os.path.join(self.models_dir, filename),
                    "type": "deep_learning"
                })
        return models

    def list_loaded_models(self) -> List[str]:
        return list(self.loaded_models.keys())

    async def load_model(self, name: str, path: str):
        """Load a model for the Authenticator / Testing."""
        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._load_model_sync, name, path)
        except RuntimeError:
            self._load_model_sync(name, path)

    async def set_active_model(self, model_name: str):
        models = self.scan_models_directory()
        target = next((m for m in models if m['name'] == model_name), None)
        if not target: raise ValueError(f"Model {model_name} not found")
        await self.load_model(target['name'], target['path'])

    def _load_model_sync(self, name: str, path: str):
        """Sync worker to load arbitrary models."""
        logger.info(f"Loading Active Model: {name}")
        try:
            # Inject classes into __main__ for pickle compatibility
            import sys
            sys.modules['__main__'].ViolenceConv3D = ViolenceConv3D
            sys.modules['__main__'].ViolenceGRU = ViolenceGRU
            sys.modules['__main__'].SlowFastNetwork = SlowFastNetwork
            sys.modules['__main__'].TwoStreamNetwork = TwoStreamNetwork
            
            # Load
            content = torch.load(path, map_location=self.device, pickle_module=SafePickle)
            
            # Instantiate based on content or name
            model = None
            if "Conv3D" in name: model = ViolenceConv3D()
            elif "GRU" in name: model = ViolenceGRU()
            elif "SlowFast" in name: model = SlowFastNetwork()
            elif "Two" in name: model = TwoStreamNetwork()
            else: 
                # Fallback, try to infer or use generic
                if isinstance(content, nn.Module):
                    model = content
                else:
                    model = ViolenceConv3D() # Default

            # State Dict Load
            if isinstance(content, dict) and model:
                 # Check for state_dict key or raw dict
                sd = content['state_dict'] if 'state_dict' in content else content
                try: 
                    model.load_state_dict(sd, strict=False)
                except: pass

            if model:
                model.to(self.device)
                model.eval()
                self.active_model = model
                self.active_model_name = name
                self.loaded_models[name] = "Ready"
                logger.info(f"Active Model set to {name}")

        except Exception as e:
            logger.error(f"Failed to load {name}: {e}")

    # --- INFERENCE ---

    async def process_video(self, video_path: str):
        """
        Used by AUTHENTICATOR (Uses self.active_model - Any)
        """
        if not self.active_model:
            return {"error": "No Active Model. Please load one in Models tab."}

        # Extract 32 frames for analysis
        frames = []
        cap = cv2.VideoCapture(video_path)
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total > 0:
            step = max(1, total // 32)
            for i in range(0, total, step):
                cap.set(cv2.CAP_PROP_POS_FRAMES, i)
                ret, frame = cap.read()
                if ret: frames.append(frame)
                if len(frames) >= 32: break
        cap.release()

        if len(frames) < 16: return {"error": "Video too short"}

        # Run Sync Inference
        res = self._run_inference(self.active_model, frames)
        
        return {
             "violence_detected": res.get("violence_detected", False),
             "confidence": f"{res.get('confidence', 0.0):.2%}",
             "model_used": self.active_model_name,
             "segments": [] 
        }

    def _run_inference(self, model, frames):
        try:
            # Preprocess to 112x112, Normalize
            processed = []
            for f in frames:
                f_rgb = cv2.cvtColor(f, cv2.COLOR_BGR2RGB)
                f_resized = cv2.resize(f_rgb, (112, 112))
                tensor = torch.from_numpy(f_resized).permute(2, 0, 1).float() / 255.0
                mean = torch.tensor([0.43216, 0.394666, 0.37645]).view(3, 1, 1)
                std = torch.tensor([0.22803, 0.22145, 0.216989]).view(3, 1, 1)
                tensor = (tensor - mean) / std
                processed.append(tensor)
            
            input_tensor = torch.stack(processed, dim=1) # [C, T, H, W]
            input_tensor = input_tensor.unsqueeze(0).to(self.device) # [1, C, T, H, W]
            
            with torch.no_grad():
                output = model(input_tensor)
                probs = torch.softmax(output, dim=1)
                conf = probs[0][1].item()
                
            return {
                "violence_detected": conf > 0.5,
                "confidence": conf
            }
        except Exception as e:
            logger.error(f"Inference Error: {e}")
            return {"error": str(e)}

model_manager = ModelManager()
