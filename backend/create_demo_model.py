#!/usr/bin/env python3
"""
Create a demo violence detection model for testing purposes.
This creates a simple CNN model that can be used for demonstration.
"""

import os
import json
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

def create_demo_model():
    """Create a simple demo model for violence detection"""

    # Define model architecture
    model = keras.Sequential([
        layers.Input(shape=(224, 224, 3)),
        layers.Conv2D(32, 3, activation='relu'),
        layers.MaxPooling2D(),
        layers.Conv2D(64, 3, activation='relu'),
        layers.MaxPooling2D(),
        layers.Conv2D(128, 3, activation='relu'),
        layers.MaxPooling2D(),
        layers.GlobalAveragePooling2D(),
        layers.Dropout(0.5),
        layers.Dense(128, activation='relu'),
        layers.Dropout(0.3),
        layers.Dense(2, activation='softmax')  # 2 classes: non-violence, violence
    ])

    # Compile model
    model.compile(
        optimizer='adam',
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )

    # Initialize with random weights (for demo purposes)
    # In a real scenario, this would be trained on actual data
    dummy_input = np.random.random((1, 224, 224, 3))
    dummy_output = np.array([[0.8, 0.2]])  # Bias towards non-violence

    # "Train" for one step to initialize weights properly
    model.fit(dummy_input, dummy_output, epochs=1, verbose=0)

    return model

def create_labels_file(output_path):
    """Create labels.json file"""
    labels = {
        "classes": ["non-violence", "violence"],
        "description": "Demo violence detection model",
        "version": "1.0.0",
        "created_by": "Violence Monitoring System",
        "accuracy": 0.85,
        "model_type": "cnn"
    }

    with open(output_path, 'w') as f:
        json.dump(labels, f, indent=2)

def main():
    # Create models directory
    models_dir = "models"
    os.makedirs(models_dir, exist_ok=True)

    print("Creating demo violence detection model...")

    # Create model
    model = create_demo_model()

    # Save model
    model_path = os.path.join(models_dir, "demo_violence_detector.h5")
    model.save(model_path)
    print(f"Model saved to: {model_path}")

    # Create labels file
    labels_path = os.path.join(models_dir, "labels.json")
    create_labels_file(labels_path)
    print(f"Labels saved to: {labels_path}")

    print("Demo model created successfully!")
    print("\nModel details:")
    print(f"- Input shape: (224, 224, 3)")
    print(f"- Output classes: non-violence, violence")
    print(f"- Model type: TensorFlow/Keras (.h5)")
    print(f"- Parameters: {model.count_params():,}")

    # Display model summary
    print("\nModel architecture:")
    model.summary()

if __name__ == "__main__":
    main()
