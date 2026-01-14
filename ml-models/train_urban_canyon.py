"""
Training script for Urban Canyon Model

This model learns how Hong Kong's unique urban topology affects weather patterns.
It uses 3D convolutional neural networks to understand how buildings create
wind shadows, heat islands, and rainfall patterns.
"""

import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import pandas as pd
from pathlib import Path

# Configuration
DATA_DIR = Path("data/processed")
MODEL_DIR = Path("models")
BATCH_SIZE = 32
EPOCHS = 50
LEARNING_RATE = 0.001


def load_training_data():
    """Load preprocessed training data"""
    print("Loading training data...")
    
    # In production, load real data
    # For now, create sample data structure
    
    # Features: (lat, lng, elevation, temp, humid, wind, + 3D building grid)
    # Target: Adjusted weather conditions
    
    X_train = np.random.randn(10000, 32, 32, 16, 6)  # Simplified 3D grid
    y_train = np.random.randn(10000, 4)  # temp, humid, wind, rain
    
    X_val = np.random.randn(2000, 32, 32, 16, 6)
    y_val = np.random.randn(2000, 4)
    
    return (X_train, y_train), (X_val, y_val)


def create_urban_canyon_model(input_shape=(32, 32, 16, 6)):
    """
    Create 3D CNN model for urban canyon effect prediction
    
    Architecture:
    - 3D convolutions to capture spatial building patterns
    - Attention mechanism for important features
    - Dense layers for final weather prediction
    """
    
    inputs = layers.Input(shape=input_shape)
    
    # 3D Convolutional layers
    x = layers.Conv3D(32, (3, 3, 3), activation='relu', padding='same')(inputs)
    x = layers.BatchNormalization()(x)
    x = layers.MaxPooling3D((2, 2, 2))(x)
    
    x = layers.Conv3D(64, (3, 3, 3), activation='relu', padding='same')(x)
    x = layers.BatchNormalization()(x)
    x = layers.MaxPooling3D((2, 2, 2))(x)
    
    x = layers.Conv3D(128, (3, 3, 3), activation='relu', padding='same')(x)
    x = layers.BatchNormalization()(x)
    x = layers.GlobalAveragePooling3D()(x)
    
    # Dense layers
    x = layers.Dense(256, activation='relu')(x)
    x = layers.Dropout(0.3)(x)
    x = layers.Dense(128, activation='relu')(x)
    x = layers.Dropout(0.2)(x)
    
    # Output: [temperature_adj, humidity_adj, wind_speed_adj, rainfall_adj]
    outputs = layers.Dense(4, activation='linear')(x)
    
    model = keras.Model(inputs=inputs, outputs=outputs, name='urban_canyon_model')
    
    return model


def train_model():
    """Train the urban canyon model"""
    
    print("Creating model...")
    model = create_urban_canyon_model()
    
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=LEARNING_RATE),
        loss='mse',
        metrics=['mae', 'mse']
    )
    
    model.summary()
    
    # Load data
    (X_train, y_train), (X_val, y_val) = load_training_data()
    
    # Callbacks
    callbacks = [
        keras.callbacks.ModelCheckpoint(
            MODEL_DIR / 'urban_canyon_best.h5',
            save_best_only=True,
            monitor='val_loss'
        ),
        keras.callbacks.EarlyStopping(
            patience=10,
            restore_best_weights=True
        ),
        keras.callbacks.ReduceLROnPlateau(
            factor=0.5,
            patience=5,
            min_lr=1e-6
        ),
        keras.callbacks.TensorBoard(
            log_dir='logs/urban_canyon'
        )
    ]
    
    # Train
    print("Training model...")
    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        batch_size=BATCH_SIZE,
        epochs=EPOCHS,
        callbacks=callbacks,
        verbose=1
    )
    
    # Save final model
    model.save(MODEL_DIR / 'urban_canyon_v1.h5')
    print(f"Model saved to {MODEL_DIR / 'urban_canyon_v1.h5'}")
    
    # Convert to TensorFlow Lite for mobile
    print("Converting to TensorFlow Lite...")
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    tflite_model = converter.convert()
    
    with open(MODEL_DIR / 'urban_canyon_v1.tflite', 'wb') as f:
        f.write(tflite_model)
    
    print("TFLite model saved for offline use")
    
    return model, history


if __name__ == '__main__':
    # Create directories
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    
    # Train
    model, history = train_model()
    
    print("\nTraining complete!")
    print(f"Final validation MAE: {history.history['val_mae'][-1]:.4f}")
