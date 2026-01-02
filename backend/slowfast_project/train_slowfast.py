
import os
import cv2
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from tqdm import tqdm
import random
import numpy as np

# PyTorchVideo Models
from pytorchvideo.models.hub import slowfast_r50

# Configuration
BATCH_SIZE = 4 # SlowFast is heavy
EPOCHS = 20 # Fine-tuning doesn't need much
LEARNING_RATE = 0.0001
NUM_FRAMES = 32 # SlowFast Frame Count
SAMPLING_RATE = 2 
IMG_SIZE = 256
DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'

class VideoDataset(Dataset):
    def __init__(self, root_dir, clip_len=NUM_FRAMES, sampling_rate=SAMPLING_RATE, transform=None):
        self.root_dir = root_dir
        self.clip_len = clip_len
        self.sampling_rate = sampling_rate
        self.samples = [] 
        self.labels = []
        
        # Mapping: {Folder: Label}
        # Support both RWF-2000 names
        classes = {'Violence': 1, 'Fight': 1, 'NonViolence': 0, 'NonFight': 0}
        
        for folder, label in classes.items():
            folder_path = os.path.join(root_dir, folder)
            if os.path.exists(folder_path):
                files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.lower().endswith('.avi') or f.lower().endswith('.mp4')]
                for f in files:
                    self.samples.append(f)
                    self.labels.append(label)
                    
        print(f"Loaded {len(self.samples)} videos from {root_dir}")

    def __len__(self):
        return len(self.samples)

    def load_video(self, path):
        cap = cv2.VideoCapture(path)
        frames = []
        while True:
            ret, frame = cap.read()
            if not ret: break
            frame = cv2.resize(frame, (IMG_SIZE, IMG_SIZE))
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frames.append(frame)
        cap.release()
        return np.array(frames)

    def __getitem__(self, idx):
        path = self.samples[idx]
        label = self.labels[idx]
        
        try:
            # 1. Load Video
            video_data = self.load_video(path) # (T, H, W, C)
            
            if len(video_data) == 0:
                # Handle corrupted video
                return torch.zeros((3, self.clip_len, IMG_SIZE, IMG_SIZE)), torch.tensor(label).float()

            # 2. Temporal Sampling
            # Strategy: Uniform sampling or random clip? 
            # RWF-2000 clips are 5 sec (150 frames). We need 32 frames with stride 2 = 64 frames coverage.
            # Let's take a centered crop temporarily.
            total_frames = len(video_data)
            required_frames = self.clip_len * self.sampling_rate
            
            start = 0
            if total_frames > required_frames:
                # Random start for training, center for val? Let's simply do center for robustness now
                start = (total_frames - required_frames) // 2
            
            # Extract indices
            indices = [start + i * self.sampling_rate for i in range(self.clip_len)]
            
            # Handle out of bounds (padding/looping)
            indices = [min(i, total_frames - 1) for i in indices]
            
            clip = video_data[indices] # (32, 256, 256, 3)
            
            # 3. Preprocessing for SlowFast
            # Needs: (3, T, H, W)
            # Normalize 0-1 (Float) -> Then mean/std ideally.
            clip = torch.from_numpy(clip).permute(3, 0, 1, 2).float() / 255.0
            
            # Basic Mean/Std normalization (ImageNet)
            mean = torch.tensor([0.45, 0.45, 0.45]).view(3, 1, 1, 1)
            std = torch.tensor([0.225, 0.225, 0.225]).view(3, 1, 1, 1)
            clip = (clip - mean) / std

            # 4. Prepare SlowFast Inputs
            # Returns list: [slow_path, fast_path]
            # Fast uses all frames (alpha=8 usually in original paper, but here we just pass the clip)
            # Actually PyTorchVideo model expects specific subsampling.
            # To simplify: We pass the full (3, 32, 256, 256) tensor and let the model splitter handle if we use the hub model helper.
            # Wait, raw slowfast_r50 expects a list of [slow, fast].
            
            # Manual Split
            # Fast Path: All 32 frames. Shape (3, 32, 256, 256)
            # Slow Path: Subsample 1/4 (alpha=4). Shape (3, 8, 256, 256)
            
            fast_path = clip
            slow_path = torch.index_select(clip, 1, torch.linspace(0, clip.shape[1]-1, 8).long())
            
            return [slow_path, fast_path], torch.tensor([label], dtype=torch.float32)
            
        except Exception as e:
            print(f"Error loading {path}: {e}")
            # Return dummy
            return [torch.zeros(3, 8, IMG_SIZE, IMG_SIZE), torch.zeros(3, 32, IMG_SIZE, IMG_SIZE)], torch.tensor([label], dtype=torch.float32)

def build_model():
    print("Downloading/Loading SlowFast R50...")
    # Using PyTorchVideo Hub for correct architecture
    model = slowfast_r50(pretrained=True)
    
    # Freeze all parameters
    for param in model.parameters():
        param.requires_grad = False
        
    print("Freezing Backbone... Fine-tuning Head only.")
    
    # Replace Head
    # SlowFast head is usually model.blocks[-1] (ResNetBasicHead)
    # Input size depends on R50 fusion. usually 2048+256 = 2304
    
    # Let's inspect or just overwrite the projection
    # The 'proj' layer inside the head is what we need to change.
    
    # Standard SlowFast R50 has head: ResNetBasicHead(dropout, proj, output_pool, ...)
    # dimensions: 2304 -> 400 (Kinetics-400)
    
    model.blocks[-1].proj = nn.Linear(2304, 1) # Binary Classification
    
    # Unfreeze Head
    for param in model.blocks[-1].parameters():
        param.requires_grad = True
        
    return model

def train():
    # Point to the dataset in the sibling folder
    dataset_root = "../skeleton_violence_detection/RWF-2000" 
    
    if not os.path.exists(dataset_root):
        print(f"Dataset not found at {os.path.abspath(dataset_root)}")
        return

    train_set = VideoDataset(os.path.join(dataset_root)) # Just pass root, it searches subfolders
    # Actually my dataset logic searches specific predefined subfolders in root.
    # The RWF usually has 'train' and 'val' folders.
    # User said: /dataset/Violence etc.
    # Let's support naive structure:
    # If root has 'train', use that for training.
    
    train_root = dataset_root
    val_root = dataset_root
    
    if os.path.exists(os.path.join(dataset_root, 'train')):
        train_root = os.path.join(dataset_root, 'train')
        val_root = os.path.join(dataset_root, 'val')
        print("Detected train/val split in RWF-2000.")
        
    train_ds = VideoDataset(train_root)
    val_ds = VideoDataset(val_root)
    
    # Limit validation size for speed if same as train (e.g. flat structure)
    if train_root == val_root:
        # Split logic
        total = len(train_ds)
        train_len = int(0.8 * total)
        train_ds, val_ds = torch.utils.data.random_split(train_ds, [train_len, total-train_len])
        
    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True, num_workers=4, pin_memory=True)
    val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE, shuffle=False, num_workers=4, pin_memory=True)

    model = build_model().to(DEVICE)
    
    # Loss & Opt
    criterion = nn.BCEWithLogitsLoss()
    optimizer = torch.optim.Adam(model.blocks[-1].parameters(), lr=LEARNING_RATE) # Optimize Head Only
    
    print("Starting Training...")
    
    best_acc = 0.0
    
    for epoch in range(EPOCHS):
        model.train()
        epoch_loss = 0
        
        loop = tqdm(train_loader, desc=f"Epoch {epoch+1}/{EPOCHS}")
        for batch_idx, (inputs, labels) in enumerate(loop):
            # inputs is list [slow, fast]
            slow = inputs[0].to(DEVICE)
            fast = inputs[1].to(DEVICE)
            labels = labels.to(DEVICE)
            
            optimizer.zero_grad()
            logits = model([slow, fast]) # Returns (B, 1)
            
            loss = criterion(logits, labels)
            loss.backward()
            optimizer.step()
            
            epoch_loss += loss.item()
            loop.set_postfix(loss=loss.item())
            
        # Validation
        model.eval()
        correct = 0
        total = 0
        
        with torch.no_grad():
            for inputs, labels in val_loader:
                slow = inputs[0].to(DEVICE)
                fast = inputs[1].to(DEVICE)
                labels = labels.to(DEVICE)
                
                logits = model([slow, fast])
                preds = (torch.sigmoid(logits) > 0.5).float()
                
                correct += (preds == labels).sum().item()
                total += labels.size(0)
                
        acc = correct / total * 100
        print(f"Validation Accuracy: {acc:.2f}%")
        
        if acc > best_acc:
            best_acc = acc
            torch.save(model.state_dict(), "best_slowfast.pth")
            print("Saved Best Model.")

if __name__ == "__main__":
    train()
