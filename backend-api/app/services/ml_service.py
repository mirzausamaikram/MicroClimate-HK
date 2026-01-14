from typing import List, Dict, Any
import numpy as np
from scipy.spatial import cKDTree
from scipy.interpolate import Rbf
import logging

logger = logging.getLogger(__name__)


class MLService:
    """Machine Learning service for weather prediction"""
    
    def __init__(self):
        self.urban_canyon_model = None
        self.sensor_fusion_model = None
        self._load_models()
    
    def _load_models(self):
        """Load ML models"""
        # In production, load actual TensorFlow models
        # For now, use placeholder
        logger.info("ML models initialized (placeholder)")
    
    async def interpolate_weather(
        self,
        readings: List[Any],
        target_lat: float,
        target_lng: float,
        target_elev: float
    ) -> Dict[str, float]:
        """
        Interpolate weather data using spatial interpolation
        
        Uses Radial Basis Function (RBF) interpolation for smooth results
        """
        
        if not readings:
            return {}
        
        # Extract coordinates and values
        points = []
        temps = []
        humidities = []
        rainfalls = []
        wind_speeds = []
        
        for reading in readings:
            # Assuming reading has location with x, y, z attributes
            points.append([
                reading.location.x,  # longitude
                reading.location.y,  # latitude
                reading.location.z or 0  # elevation
            ])
            temps.append(reading.temperature)
            humidities.append(reading.humidity)
            rainfalls.append(reading.rainfall)
            wind_speeds.append(reading.wind_speed)
        
        points = np.array(points)
        target = np.array([[target_lng, target_lat, target_elev]])
        
        # Use inverse distance weighting for simplicity
        # In production, use more sophisticated ML models
        tree = cKDTree(points)
        distances, indices = tree.query(target, k=min(5, len(points)))
        
        # Inverse distance weights
        weights = 1 / (distances[0] + 1e-6)
        weights = weights / weights.sum()
        
        # Weighted average
        temperature = sum(temps[i] * w for i, w in zip(indices[0], weights))
        humidity = sum(humidities[i] * w for i, w in zip(indices[0], weights))
        rainfall = sum(rainfalls[i] * w for i, w in zip(indices[0], weights))
        wind_speed = sum(wind_speeds[i] * w for i, w in zip(indices[0], weights))
        
        return {
            "temperature": float(temperature),
            "humidity": float(humidity),
            "rainfall": float(rainfall),
            "wind_speed": float(wind_speed),
            "wind_direction": readings[indices[0][0]].wind_direction,
            "pressure": readings[indices[0][0]].pressure,
            "uv_index": readings[indices[0][0]].uv_index
        }
    
    async def predict_urban_canyon_effect(
        self,
        lat: float,
        lng: float,
        building_data: List[Any],
        base_weather: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Predict how urban canyon affects weather
        
        This would use the Urban Canyon Neural Network in production
        """
        
        # Placeholder: Simple adjustment based on building density
        if building_data:
            density_factor = min(1.0, len(building_data) / 10)
            
            # Urban heat island effect
            temp_adjustment = density_factor * 1.5
            
            # Reduced wind in canyons
            wind_factor = 1 - (density_factor * 0.3)
            
            return {
                "temperature": base_weather["temperature"] + temp_adjustment,
                "humidity": base_weather["humidity"],
                "wind_speed": base_weather["wind_speed"] * wind_factor
            }
        
        return base_weather
    
    async def fuse_sensor_readings(
        self,
        readings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Fuse multiple sensor readings to get accurate measurement
        
        Filters out noise and outliers from crowdsourced data
        """
        
        if not readings:
            return {}
        
        # Remove outliers using IQR method
        def remove_outliers(values: List[float]) -> List[float]:
            if len(values) < 4:
                return values
            
            q1, q3 = np.percentile(values, [25, 75])
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            
            return [v for v in values if lower <= v <= upper]
        
        # Extract values
        temps = [r.get("temperature") for r in readings if r.get("temperature")]
        humids = [r.get("humidity") for r in readings if r.get("humidity")]
        
        # Remove outliers
        temps = remove_outliers(temps)
        humids = remove_outliers(humids)
        
        if not temps or not humids:
            return {}
        
        # Calculate weighted average based on sensor accuracy
        accuracies = [r.get("accuracy", 0.5) for r in readings]
        weights = np.array(accuracies) / sum(accuracies)
        
        return {
            "temperature": float(np.average(temps[:len(weights)], weights=weights[:len(temps)])),
            "humidity": float(np.average(humids[:len(weights)], weights=weights[:len(humids)])),
            "confidence": float(np.mean(accuracies))
        }
