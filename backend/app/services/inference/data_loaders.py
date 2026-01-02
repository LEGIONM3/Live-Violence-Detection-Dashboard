
import cv2
import numpy as np
import torch
from typing import List, Tuple, Optional

# Standard ImageNet normalization means/stds
MEAN = [0.485, 0.456, 0.406]
STD = [0.229, 0.224, 0.225]

def prepare_generic_3d_input(frames: List[np.ndarray], target_frames: int = 16, img_size: int = 112) -> torch.Tensor:
    """
    Prepares input for Generic 3D CNNs (Conv3D, Swin, GRU-CNN backbone).
    Key steps:
    1. Sampling (Uniform)
    2. Resize
    3. RGB Conversion
    4. Normalization (0-1) - TODO: Add Mean/Std norm if required by training
    5. Permutation to (C, T, H, W)
    6. Batch Dimension
    """
    frames_list = list(frames)
    if not frames_list:
        raise ValueError("No frames provided")

    # 1. Uniform Sampling
    if len(frames_list) < target_frames:
        # Loop padding
        while len(frames_list) < target_frames:
            frames_list.append(frames_list[-1])
    elif len(frames_list) > target_frames:
        indices = np.linspace(0, len(frames_list)-1, target_frames, dtype=int)
        frames_list = [frames_list[i] for i in indices]

    processed = []
    for f in frames_list:
        f = cv2.resize(f, (img_size, img_size))
        f = cv2.cvtColor(f, cv2.COLOR_BGR2RGB)
        f = f.astype(np.float32) / 255.0
        # Optional: Normalize with ImageNet stats if training did so. 
        # For now, sticking to raw 0-1 as per previous code to avoid breaking changes unless necessary.
        processed.append(f)

    # Stack: (T, H, W, C)
    batch = np.stack(processed)
    # Permute: (C, T, H, W)
    batch = np.transpose(batch, (3, 0, 1, 2))
    # Batch unsqueeze: (1, C, T, H, W)
    tensor = torch.FloatTensor(batch).unsqueeze(0)
    
    if torch.cuda.is_available():
        tensor = tensor.cuda()
        
    return tensor

def prepare_slowfast_input(frames: List[np.ndarray], target_frames: int = 32, img_size: int = 112) -> torch.Tensor:
    """
    SlowFast usually requires a higher frame count to have a meaningful 'Fast' pathway.
    Target frames = 32 usually.
    Input tensor: (1, C, T, H, W)
    The model architecture splits this into fast/slow internally.
    """
    # SlowFast often uses 32 frames for the fast path, 8 for slow (alpha=4).
    # We prepare one tensor (C, T, H, W) and let the Generic 3D logic handle the initial stack.
    return prepare_generic_3d_input(frames, target_frames=target_frames, img_size=img_size)

def prepare_twostream_input(frames: List[np.ndarray], target_frames: int = 16, img_size: int = 112) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    Returns (rgb_tensor, flow_tensor).
    """
    frames_list = list(frames)
    if not frames_list:
        raise ValueError("No frames")

    # Sampling
    if len(frames_list) < target_frames:
        while len(frames_list) < target_frames:
            frames_list.append(frames_list[-1])
    elif len(frames_list) > target_frames:
        indices = np.linspace(0, len(frames_list)-1, target_frames, dtype=int)
        frames_list = [frames_list[i] for i in indices]

    processed_rgb = []
    for f in frames_list:
        f = cv2.resize(f, (img_size, img_size))
        # Keep BGR or RGB? r3d_18 pretrained on Kinetics usually expects RGB.
        # But previous code used raw resize? CV2 default is BGR.
        # Let's standardize to BGR->RGB.
        f = cv2.cvtColor(f, cv2.COLOR_BGR2RGB)
        processed_rgb.append(f)

    # Normalize RGB
    rgb_batch = np.array(processed_rgb, dtype=np.float32) / 255.0
    # (T, H, W, C) -> (C, T, H, W)
    rgb_batch = np.transpose(rgb_batch, (3, 0, 1, 2))
    rgb_tensor = torch.FloatTensor(rgb_batch).unsqueeze(0)

    # Flow Calculation
    # Need grayscale
    gray_frames = [cv2.cvtColor(f, cv2.COLOR_RGB2GRAY) for f in processed_rgb]
    
    flows = []
    prev_gray = gray_frames[0]
    
    # Pre-calc empty flow for first frame
    empty_flow = np.zeros((img_size, img_size, 3), dtype=np.float32)

    for i in range(len(gray_frames)):
        if i == 0:
            flows.append(empty_flow)
            continue
            
        curr_gray = gray_frames[i]
        # Farneback
        flow = cv2.calcOpticalFlowFarneback(
            prev_gray, curr_gray, None, 0.5, 3, 15, 3, 5, 1.2, 0
        )
        prev_gray = curr_gray
        
        # Visualize flow -> 3 channels (x, y, mag)
        mag, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
        # flow[..., 0] is x, flow[..., 1] is y.
        # This matches previous logic:
        flow_img = np.stack([flow[..., 0], flow[..., 1], mag], axis=-1)
        
        # Simple normalization from previous code
        flow_img = (flow_img + 20) / 40.0 
        flows.append(flow_img)

    flow_batch = np.array(flows, dtype=np.float32)
    # (T, H, W, C) -> (C, T, H, W)
    flow_batch = np.transpose(flow_batch, (3, 0, 1, 2))
    flow_tensor = torch.FloatTensor(flow_batch).unsqueeze(0)

    if torch.cuda.is_available():
        rgb_tensor = rgb_tensor.cuda()
        flow_tensor = flow_tensor.cuda()

    return rgb_tensor, flow_tensor

def prepare_yolo_input(frames: List[np.ndarray], sample_rate: int = 15) -> List[np.ndarray]:
    """
    Just subsamples frames for YOLO.
    """
    return frames[::sample_rate]
