"""
Liveness Detection CNN Training Script (PyTorch)

This script trains a CNN model to distinguish between real faces and spoofed faces
(printed photos, screen displays, etc.)

Dataset Structure:
    liveness_dataset/
        real/
            img1.jpg
            img2.jpg
            ...
        fake/
            img1.jpg
            img2.jpg
            ...

Usage:
    1. Collect real face images and save to liveness_dataset/real/
    2. Collect fake/spoof images (photos of photos, screens) and save to liveness_dataset/fake/
    3. Run this script: python train_liveness.py
    
If no dataset exists, a simple model will be created that can be fine-tuned later.
"""

import os
import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset

IMG_SIZE = 64
BATCH_SIZE = 32
EPOCHS = 20


class LivenessModel(nn.Module):
    """CNN model for liveness detection."""
    def __init__(self):
        super(LivenessModel, self).__init__()
        
        self.features = nn.Sequential(
            # First conv block
            nn.Conv2d(3, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),
            
            # Second conv block
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),
            
            # Third conv block
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),
        )
        
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(128 * 8 * 8, 256),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(256, 1),
            nn.Sigmoid()
        )
    
    def forward(self, x):
        x = self.features(x)
        x = self.classifier(x)
        return x

def load_images_from_folder(folder, label):
    """Load images from a folder and assign label."""
    images = []
    labels = []
    
    if not os.path.exists(folder):
        return np.array([]), np.array([])
    
    for filename in os.listdir(folder):
        img_path = os.path.join(folder, filename)
        img = cv2.imread(img_path)
        if img is not None:
            img = cv2.resize(img, (IMG_SIZE, IMG_SIZE))
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img = img / 255.0  # Normalize
            img = np.transpose(img, (2, 0, 1))  # HWC to CHW for PyTorch
            images.append(img)
            labels.append(label)
    
    return np.array(images, dtype=np.float32), np.array(labels, dtype=np.float32)


def train_with_dataset():
    """Train the model using the liveness dataset."""
    print("Loading dataset...")
    
    # Load real faces (label = 1)
    real_images, real_labels = load_images_from_folder("liveness_dataset/real", 1)
    # Load fake faces (label = 0)
    fake_images, fake_labels = load_images_from_folder("liveness_dataset/fake", 0)
    
    if len(real_images) == 0 or len(fake_images) == 0:
        return False
    
    # Combine datasets
    X = np.concatenate([real_images, fake_images])
    y = np.concatenate([real_labels, fake_labels])
    
    # Shuffle
    indices = np.random.permutation(len(X))
    X, y = X[indices], y[indices]
    
    # Split train/test
    split = int(0.8 * len(X))
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]
    
    print(f"Training samples: {len(X_train)}, Test samples: {len(X_test)}")
    
    # Convert to PyTorch tensors
    X_train = torch.from_numpy(X_train)
    y_train = torch.from_numpy(y_train).unsqueeze(1)
    X_test = torch.from_numpy(X_test)
    y_test = torch.from_numpy(y_test).unsqueeze(1)
    
    # Create data loaders
    train_dataset = TensorDataset(X_train, y_train)
    test_dataset = TensorDataset(X_test, y_test)
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE)
    
    # Create model
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = LivenessModel().to(device)
    criterion = nn.BCELoss()
    optimizer = optim.Adam(model.parameters())
    
    print(f"Training on: {device}")
    print(model)
    
    # Training loop
    for epoch in range(EPOCHS):
        model.train()
        running_loss = 0.0
        for inputs, labels in train_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            
            running_loss += loss.item()
        
        # Validation
        model.eval()
        correct = 0
        total = 0
        with torch.no_grad():
            for inputs, labels in test_loader:
                inputs, labels = inputs.to(device), labels.to(device)
                outputs = model(inputs)
                predicted = (outputs > 0.5).float()
                total += labels.size(0)
                correct += (predicted == labels).sum().item()
        
        acc = 100 * correct / total
        print(f"Epoch {epoch+1}/{EPOCHS}, Loss: {running_loss/len(train_loader):.4f}, Val Acc: {acc:.2f}%")
    
    # Final evaluation
    print(f"\n✅ Final Test Accuracy: {acc:.2f}%")
    
    # Save model
    os.makedirs("models", exist_ok=True)
    torch.save(model.state_dict(), "models/liveness_model.pth")
    print("✅ Model saved to models/liveness_model.pth")
    
    return True


def create_placeholder_model():
    """Create a placeholder model when no dataset is available."""
    print("⚠️  No liveness dataset found!")
    print("Creating placeholder model (will always predict 'live')...")
    print("\nTo train a proper model:")
    print("1. Create folder: liveness_dataset/real/ - with real face images")
    print("2. Create folder: liveness_dataset/fake/ - with spoofed face images")
    print("3. Run this script again\n")
    
    model = LivenessModel()
    
    # Initialize with bias towards predicting live
    # This is just so the model can run - it won't be accurate
    with torch.no_grad():
        model.classifier[-2].bias.fill_(2.0)  # Bias the final layer towards positive
    
    os.makedirs("models", exist_ok=True)
    torch.save(model.state_dict(), "models/liveness_model.pth")
    print("✅ Placeholder model saved to models/liveness_model.pth")
    print("⚠️  This model is NOT trained - it will always predict 'live'")

if __name__ == "__main__":
    print("=" * 50)
    print("LIVENESS DETECTION MODEL TRAINING (PyTorch)")
    print("=" * 50)
    
    # Check if dataset exists
    dataset_exists = (
        os.path.exists("liveness_dataset/real") and 
        os.path.exists("liveness_dataset/fake") and
        len(os.listdir("liveness_dataset/real")) > 0 and
        len(os.listdir("liveness_dataset/fake")) > 0
    )
    
    if dataset_exists:
        success = train_with_dataset()
        if not success:
            create_placeholder_model()
    else:
        create_placeholder_model()
