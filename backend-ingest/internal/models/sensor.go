package models

import (
	"errors"
	"time"
)

type SensorReading struct {
	SensorID      string    `json:"sensor_id"`
	UserID        string    `json:"user_id,omitempty"`
	Timestamp     time.Time `json:"timestamp"`
	Latitude      float64   `json:"latitude"`
	Longitude     float64   `json:"longitude"`
	Elevation     float64   `json:"elevation"`
	Temperature   float64   `json:"temperature"`
	Humidity      float64   `json:"humidity"`
	Rainfall      float64   `json:"rainfall"`
	WindSpeed     float64   `json:"wind_speed"`
	WindDirection float64   `json:"wind_direction"`
	Pressure      float64   `json:"pressure"`
	DeviceType    string    `json:"device_type"`
	Accuracy      float64   `json:"accuracy"`
}

func (s *SensorReading) Validate() error {
	if s.SensorID == "" {
		return errors.New("sensor_id is required")
	}
	if s.Latitude < -90 || s.Latitude > 90 {
		return errors.New("invalid latitude")
	}
	if s.Longitude < -180 || s.Longitude > 180 {
		return errors.New("invalid longitude")
	}
	if s.Timestamp.IsZero() {
		s.Timestamp = time.Now()
	}
	if s.Accuracy == 0 {
		s.Accuracy = 0.5
	}
	return nil
}

type WeatherUpdate struct {
	Type      string      `json:"type"`
	Timestamp time.Time   `json:"timestamp"`
	Data      interface{} `json:"data"`
}
