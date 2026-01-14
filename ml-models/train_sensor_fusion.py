"""
Sensor Fusion Model Training

Combines multiple noisy crowdsourced sensor readings into accurate measurements.
Uses ensemble methods and statistical filtering to remove outliers.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score
import joblib
from pathlib import Path


DATA_DIR = Path("data/processed")
MODEL_DIR = Path("models")


def load_sensor_data():
    """Load crowdsourced sensor readings"""
    print("Loading sensor data...")
    
    # Sample data structure
    # In production, load real crowdsourced data
    n_samples = 50000
    
    data = pd.DataFrame({
        'sensor_1_temp': np.random.randn(n_samples) * 2 + 25,
        'sensor_2_temp': np.random.randn(n_samples) * 2 + 25,
        'sensor_3_temp': np.random.randn(n_samples) * 2 + 25,
        'sensor_1_accuracy': np.random.uniform(0.5, 1.0, n_samples),
        'sensor_2_accuracy': np.random.uniform(0.5, 1.0, n_samples),
        'sensor_3_accuracy': np.random.uniform(0.5, 1.0, n_samples),
        'time_of_day': np.random.randint(0, 24, n_samples),
        'sensor_distance': np.random.uniform(0, 1000, n_samples),  # meters
        'device_type_1': np.random.randint(0, 3, n_samples),
        'device_type_2': np.random.randint(0, 3, n_samples),
        'device_type_3': np.random.randint(0, 3, n_samples),
        'true_temp': np.random.randn(n_samples) * 1 + 25  # Ground truth
    })
    
    return data


def create_features(df):
    """Engineer features for sensor fusion"""
    
    # Statistical features
    df['temp_mean'] = df[['sensor_1_temp', 'sensor_2_temp', 'sensor_3_temp']].mean(axis=1)
    df['temp_std'] = df[['sensor_1_temp', 'sensor_2_temp', 'sensor_3_temp']].std(axis=1)
    df['temp_median'] = df[['sensor_1_temp', 'sensor_2_temp', 'sensor_3_temp']].median(axis=1)
    
    # Weighted by accuracy
    df['weighted_temp'] = (
        df['sensor_1_temp'] * df['sensor_1_accuracy'] +
        df['sensor_2_temp'] * df['sensor_2_accuracy'] +
        df['sensor_3_temp'] * df['sensor_3_accuracy']
    ) / (df['sensor_1_accuracy'] + df['sensor_2_accuracy'] + df['sensor_3_accuracy'])
    
    # Accuracy features
    df['avg_accuracy'] = df[['sensor_1_accuracy', 'sensor_2_accuracy', 'sensor_3_accuracy']].mean(axis=1)
    df['min_accuracy'] = df[['sensor_1_accuracy', 'sensor_2_accuracy', 'sensor_3_accuracy']].min(axis=1)
    
    return df


def train_sensor_fusion_model():
    """Train ensemble model for sensor fusion"""
    
    # Load data
    df = load_sensor_data()
    df = create_features(df)
    
    # Features
    feature_cols = [
        'sensor_1_temp', 'sensor_2_temp', 'sensor_3_temp',
        'sensor_1_accuracy', 'sensor_2_accuracy', 'sensor_3_accuracy',
        'temp_mean', 'temp_std', 'temp_median', 'weighted_temp',
        'avg_accuracy', 'min_accuracy',
        'time_of_day', 'sensor_distance',
        'device_type_1', 'device_type_2', 'device_type_3'
    ]
    
    X = df[feature_cols]
    y = df['true_temp']
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train Random Forest
    print("Training Random Forest...")
    rf_model = RandomForestRegressor(
        n_estimators=100,
        max_depth=20,
        min_samples_split=10,
        n_jobs=-1,
        random_state=42
    )
    
    rf_model.fit(X_train_scaled, y_train)
    
    # Evaluate
    train_score = rf_model.score(X_train_scaled, y_train)
    test_score = rf_model.score(X_test_scaled, y_test)
    
    print(f"Train R² Score: {train_score:.4f}")
    print(f"Test R² Score: {test_score:.4f}")
    
    # Cross-validation
    cv_scores = cross_val_score(rf_model, X_train_scaled, y_train, cv=5, scoring='r2')
    print(f"Cross-validation R² Score: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")
    
    # Feature importance
    importance = pd.DataFrame({
        'feature': feature_cols,
        'importance': rf_model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print("\nTop 10 Important Features:")
    print(importance.head(10))
    
    # Save model and scaler
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    
    joblib.dump(rf_model, MODEL_DIR / 'sensor_fusion_v1.pkl')
    joblib.dump(scaler, MODEL_DIR / 'sensor_fusion_scaler.pkl')
    
    print(f"\nModel saved to {MODEL_DIR / 'sensor_fusion_v1.pkl'}")
    
    return rf_model, scaler


if __name__ == '__main__':
    model, scaler = train_sensor_fusion_model()
    
    print("\nSensor fusion model training complete!")
