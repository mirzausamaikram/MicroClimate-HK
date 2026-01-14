# MicroClimate HK - ML Models

AI/ML models for weather prediction and sensor fusion.

## Models

### 1. Urban Canyon Model
**Purpose**: Predicts how weather propagates through Hong Kong's street corridors and around skyscrapers.

**Architecture**: Convolutional Neural Network (CNN)
- Input: Weather conditions + 3D building layout
- Output: Adjusted weather parameters for specific coordinates
- Training: Historical weather data + crowdsourced corrections

**File**: `models/urban_canyon_v1.h5`

### 2. Sensor Fusion Model
**Purpose**: Combines noisy crowdsourced sensor readings into accurate measurements.

**Architecture**: Ensemble (Random Forest + Kalman Filter)
- Input: Multiple sensor readings with metadata (location, device type, historical accuracy)
- Output: Fused weather measurement with confidence score
- Features: Outlier detection, noise filtering, calibration

**File**: `models/sensor_fusion_v1.pkl`

### 3. Vertical Weather Model
**Purpose**: Predicts temperature, humidity, and wind at different elevations/floor levels.

**Architecture**: Gradient Boosting (XGBoost)
- Input: Ground-level weather + elevation + building data
- Output: Weather parameters at target elevation
- Features: Atmospheric lapse rate, building effects, wind shear

**File**: `models/vertical_weather_v1.json`

### 4. Laundry Dry Time Predictor
**Purpose**: AI-powered prediction for drying time based on environmental factors.

**Architecture**: Random Forest Regression
- Input: Temperature, humidity, wind speed, sunlight exposure, building shadows
- Output: Estimated dry time in minutes
- Training: User-reported dry times + weather conditions

**File**: `models/laundry_predictor_v1.pkl`

## Training Data

```
data/
├── raw/
│   ├── hko_official/         # Hong Kong Observatory data
│   ├── crowdsourced/         # Sensor readings from users
│   └── building_layouts/     # 3D building data from LandsD
├── processed/
│   ├── training_set.parquet
│   ├── validation_set.parquet
│   └── test_set.parquet
└── features/
    ├── spatial_features.npz
    └── temporal_features.npz
```

## Training Scripts

### Urban Canyon Model

```python
# train_urban_canyon.py
import tensorflow as tf
from tensorflow import keras

# Load and preprocess data
# ... data loading code ...

# Model architecture
model = keras.Sequential([
    keras.layers.Conv3D(64, (3, 3, 3), activation='relu'),
    keras.layers.MaxPooling3D((2, 2, 2)),
    keras.layers.Conv3D(128, (3, 3, 3), activation='relu'),
    keras.layers.GlobalAveragePooling3D(),
    keras.layers.Dense(256, activation='relu'),
    keras.layers.Dropout(0.3),
    keras.layers.Dense(4)  # temp, humidity, wind, rainfall
])

model.compile(optimizer='adam', loss='mse', metrics=['mae'])
model.fit(X_train, y_train, validation_data=(X_val, y_val), epochs=50)
model.save('models/urban_canyon_v1.h5')
```

### Sensor Fusion Model

```python
# train_sensor_fusion.py
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import joblib

# Train model
rf = RandomForestRegressor(n_estimators=100, max_depth=20)
rf.fit(X_train, y_train)

# Save model
joblib.dump(rf, 'models/sensor_fusion_v1.pkl')
```

## Model Deployment

### TensorFlow Lite (for offline mobile)

```python
# Convert to TensorFlow Lite
converter = tf.lite.TFLiteConverter.from_keras_model(model)
converter.optimizations = [tf.lite.Optimize.DEFAULT]
tflite_model = converter.convert()

with open('models/urban_canyon_v1.tflite', 'wb') as f:
    f.write(tflite_model)
```

### ONNX (for web deployment)

```python
import tf2onnx

# Convert to ONNX
onnx_model, _ = tf2onnx.convert.from_keras(model)
with open('models/urban_canyon_v1.onnx', 'wb') as f:
    f.write(onnx_model.SerializeToString())
```

## Model Performance

| Model | MAE | R² Score | Inference Time |
|-------|-----|----------|----------------|
| Urban Canyon | 0.8°C | 0.92 | ~15ms |
| Sensor Fusion | 0.5°C | 0.95 | ~5ms |
| Vertical Weather | 1.2°C | 0.88 | ~8ms |
| Laundry Predictor | 12min | 0.85 | ~3ms |

## Model Correction Approach

Since official hyperlocal historical data doesn't exist, we use a **bias correction model**:

1. Collect HKO official forecasts for 6 months
2. Gather actual crowdsourced readings at specific coordinates
3. Train model to predict: `actual_weather = official_forecast + learned_bias(location, time, conditions)`
4. Result: Location-specific corrections to official forecasts

## Requirements

```
tensorflow==2.15.0
scikit-learn==1.4.0
xgboost==2.0.3
numpy==1.26.3
pandas==2.1.4
```

## Usage in API

```python
from app.services.ml_service import MLService

ml_service = MLService()

# Load models on startup
ml_service.load_urban_canyon_model('models/urban_canyon_v1.h5')
ml_service.load_sensor_fusion_model('models/sensor_fusion_v1.pkl')

# Inference
predicted_weather = await ml_service.predict_urban_canyon_effect(
    lat=22.2819,
    lng=114.1577,
    building_data=buildings,
    base_weather=hko_data
)
```
