# Contributing to MicroClimate HK

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the project.

## 🌟 Ways to Contribute

### 1. Connect Your Weather Sensor
Have an Arduino or Raspberry Pi with temperature/humidity/pressure sensors? Connect it to MicroClimate HK!

**Requirements:**
- Temperature sensor (±0.5°C accuracy)
- Humidity sensor (±5% accuracy)
- GPS location or fixed coordinates
- Internet connectivity

**How to Submit Data:**
```bash
POST /api/v1/sensors/readings
Content-Type: application/json

{
  "sensor_id": "your-unique-sensor-id",
  "latitude": 22.3193,
  "longitude": 114.1694,
  "elevation": 50,
  "temperature": 28.5,
  "humidity": 75.0,
  "pressure": 1013.25,
  "timestamp": "2026-01-14T10:30:00Z"
}
```

### 2. Report Bugs
Found a bug? [Create an issue](https://github.com/mirzausamaikram/MicroClimate-HK/issues) with:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Screenshots (if applicable)
- Environment details (OS, Docker version, etc.)

### 3. Suggest Features
Have an idea? [Start a discussion](https://github.com/mirzausamaikram/MicroClimate-HK/discussions) with:
- Problem you're trying to solve
- Proposed solution
- Use cases and examples
- Potential implementation approach

### 4. Improve Documentation
- Fix typos or unclear explanations
- Add examples or tutorials
- Translate to Traditional Chinese/Cantonese
- Create video walkthroughs

### 5. Code Contributions
- Fix bugs
- Implement new features
- Optimize performance
- Add tests

## 🔧 Development Setup

### Prerequisites
- Docker Desktop
- Git
- Node.js 18+ (for frontend development)
- Python 3.11+ (for backend development)
- Go 1.21+ (for ingestion service development)

### Clone and Setup
```bash
git clone https://github.com/mirzausamaikram/MicroClimate-HK.git
cd MicroClimate-HK
cp .env.example .env
```

### Development Workflow

#### Frontend Development
```bash
cd frontend
npm install
npm run dev
# Frontend runs on http://localhost:5173 with hot reload
```

#### Backend API Development
```bash
cd backend-api
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

#### Ingestion Service Development
```bash
cd backend-ingest
go mod download
go run cmd/server/main.go
```

### Running Tests
```bash
# Frontend tests
cd frontend
npm test

# Backend tests
cd backend-api
pytest tests/

# Go tests
cd backend-ingest
go test ./...
```

## 📝 Code Style Guidelines

### Python (Backend)
- Follow PEP 8
- Use type hints
- Document functions with docstrings
- Maximum line length: 120 characters

```python
from typing import Optional

async def get_weather(
    lat: float,
    lon: float,
    elevation: Optional[float] = None
) -> WeatherReading:
    """
    Fetch weather data for a specific location.
    
    Args:
        lat: Latitude in decimal degrees
        lon: Longitude in decimal degrees
        elevation: Optional elevation in meters
    
    Returns:
        WeatherReading object with current conditions
    """
    ...
```

### TypeScript (Frontend)
- Use TypeScript strict mode
- Follow Svelte conventions
- Use meaningful variable names
- Document complex logic

```typescript
interface WeatherData {
  temperature: number;
  humidity: number;
  timestamp: Date;
}

export async function fetchWeather(location: Location): Promise<WeatherData> {
  // Implementation
}
```

### Go (Ingestion Service)
- Follow Go conventions
- Use meaningful package names
- Document exported functions
- Use context for cancellation

```go
// ProcessReading validates and stores a weather sensor reading
func (i *Ingestor) ProcessReading(ctx context.Context, reading SensorReading) error {
    // Implementation
}
```

## 🔀 Pull Request Process

1. **Fork the repository** and create a new branch
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following code style guidelines

3. **Test your changes**
   - Ensure all existing tests pass
   - Add new tests for new features
   - Test manually in Docker environment

4. **Commit with clear messages**
   ```bash
   git commit -m "feat: add vertical wind profile calculation"
   git commit -m "fix: correct elevation interpolation in urban canyons"
   git commit -m "docs: update API integration guide"
   ```

5. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request**
   - Use a clear title and description
   - Reference any related issues
   - Include screenshots for UI changes
   - Wait for code review

### PR Review Checklist
- [ ] Code follows style guidelines
- [ ] Tests pass and coverage is maintained
- [ ] Documentation is updated
- [ ] No breaking changes (or clearly documented)
- [ ] Commit messages are clear
- [ ] PR description explains what and why

## 🐛 Bug Report Template

```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. See error

**Expected behavior**
What you expected to happen.

**Screenshots**
If applicable, add screenshots.

**Environment:**
 - OS: [e.g. Windows 11, macOS 14]
 - Docker version: [e.g. 24.0.6]
 - Browser: [e.g. Chrome 120]

**Additional context**
Any other context about the problem.
```

## ✨ Feature Request Template

```markdown
**Problem Statement**
What problem does this feature solve?

**Proposed Solution**
How should this feature work?

**Alternatives Considered**
What other approaches did you consider?

**Additional Context**
Mockups, examples, use cases, etc.
```

## 🎯 Coding Priorities

1. **Accuracy** - Weather predictions must be reliable
2. **Performance** - Fast response times (<500ms)
3. **Reliability** - Handle edge cases gracefully
4. **Security** - Validate all inputs, prevent injection attacks
5. **Maintainability** - Write clear, documented code

## 📧 Questions?

- **General questions**: [GitHub Discussions](https://github.com/mirzausamaikram/MicroClimate-HK/discussions)
- **Security issues**: Email mirza.usama.ikram@gmail.com
- **Feature proposals**: [GitHub Issues](https://github.com/mirzausamaikram/MicroClimate-HK/issues)

## 🙏 Recognition

Contributors will be:
- Listed in the project README
- Credited in release notes
- Given credit in documentation they help create

Thank you for making MicroClimate HK better!
