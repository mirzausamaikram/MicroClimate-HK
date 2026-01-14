package ingestor

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"

	"microclimate-hk/ingest/internal/database"
	"microclimate-hk/ingest/internal/models"

	"go.uber.org/zap"
)

type Ingestor struct {
	db     *database.Postgres
	redis  *database.Redis
	logger *zap.Logger
	queue  chan *models.SensorReading
}

func New(db *database.Postgres, redis *database.Redis, logger *zap.Logger) *Ingestor {
	return &Ingestor{
		db:     db,
		redis:  redis,
		logger: logger,
		queue:  make(chan *models.SensorReading, 10000),
	}
}

func (i *Ingestor) Start(ctx context.Context) {
	i.logger.Info("Starting sensor data ingestor")

	// Start multiple workers for parallel processing
	for w := 0; w < 10; w++ {
		go i.worker(ctx, w)
	}

	// Start batch processor
	go i.batchProcessor(ctx)
}

func (i *Ingestor) worker(ctx context.Context, id int) {
	i.logger.Info("Starting worker", zap.Int("id", id))

	for {
		select {
		case <-ctx.Done():
			i.logger.Info("Worker stopping", zap.Int("id", id))
			return
		case reading := <-i.queue:
			if err := i.processReading(ctx, reading); err != nil {
				i.logger.Error("Failed to process reading",
					zap.Int("worker", id),
					zap.Error(err),
				)
			}
		}
	}
}

func (i *Ingestor) batchProcessor(ctx context.Context) {
	ticker := time.NewTicker(5 * time.Second)
	defer ticker.Stop()

	batch := make([]*models.SensorReading, 0, 1000)

	for {
		select {
		case <-ctx.Done():
			// Process remaining batch
			if len(batch) > 0 {
				i.saveBatch(ctx, batch)
			}
			return
		case <-ticker.C:
			if len(batch) > 0 {
				i.saveBatch(ctx, batch)
				batch = make([]*models.SensorReading, 0, 1000)
			}
		}
	}
}

func (i *Ingestor) ProcessHTTPRequest(r *http.Request) error {
	body, err := io.ReadAll(r.Body)
	if err != nil {
		return fmt.Errorf("failed to read body: %w", err)
	}
	defer r.Body.Close()

	var reading models.SensorReading
	if err := json.Unmarshal(body, &reading); err != nil {
		return fmt.Errorf("failed to unmarshal reading: %w", err)
	}

	// Add to queue
	select {
	case i.queue <- &reading:
		return nil
	default:
		return fmt.Errorf("queue full")
	}
}

func (i *Ingestor) processReading(ctx context.Context, reading *models.SensorReading) error {
	// Validate reading
	if err := reading.Validate(); err != nil {
		return fmt.Errorf("invalid reading: %w", err)
	}

	// Apply sensor calibration if available
	calibrated := i.calibrateReading(reading)

	// Filter noise/outliers
	if !i.isValidReading(calibrated) {
		i.logger.Warn("Filtered out invalid reading", zap.String("sensor_id", reading.SensorID))
		return nil
	}

	// Publish to Redis for real-time updates
	if err := i.publishReading(ctx, calibrated); err != nil {
		i.logger.Error("Failed to publish reading", zap.Error(err))
	}

	// Save to database (batched)
	return i.saveReading(ctx, calibrated)
}

func (i *Ingestor) calibrateReading(reading *models.SensorReading) *models.SensorReading {
	// In production, load calibration data from database
	// For now, return as-is
	return reading
}

func (i *Ingestor) isValidReading(reading *models.SensorReading) bool {
	// Basic validation
	if reading.Temperature < -50 || reading.Temperature > 60 {
		return false
	}
	if reading.Humidity < 0 || reading.Humidity > 100 {
		return false
	}
	return true
}

func (i *Ingestor) publishReading(ctx context.Context, reading *models.SensorReading) error {
	data, err := json.Marshal(reading)
	if err != nil {
		return err
	}

	return i.redis.Client().Publish(ctx, "sensor:readings", data).Err()
}

func (i *Ingestor) saveReading(ctx context.Context, reading *models.SensorReading) error {
	query := `
		INSERT INTO weather_readings (
			timestamp, location, temperature, humidity, rainfall, 
			wind_speed, wind_direction, pressure, source, confidence, sensor_id
		) VALUES (
			$1, ST_SetSRID(ST_MakePoint($2, $3, $4), 4326), $5, $6, $7, $8, $9, $10, $11, $12, $13
		)
	`

	_, err := i.db.DB().ExecContext(ctx, query,
		reading.Timestamp,
		reading.Longitude,
		reading.Latitude,
		reading.Elevation,
		reading.Temperature,
		reading.Humidity,
		reading.Rainfall,
		reading.WindSpeed,
		reading.WindDirection,
		reading.Pressure,
		"crowdsourced",
		reading.Accuracy,
		reading.SensorID,
	)

	return err
}

func (i *Ingestor) saveBatch(ctx context.Context, batch []*models.SensorReading) error {
	i.logger.Info("Saving batch", zap.Int("count", len(batch)))

	// Use PostgreSQL COPY for bulk insert
	// For now, use individual inserts
	for _, reading := range batch {
		if err := i.saveReading(ctx, reading); err != nil {
			i.logger.Error("Failed to save reading", zap.Error(err))
		}
	}

	return nil
}
