#!/bin/bash
# MicroClimate HK - Quick Start Script (Linux/Mac)

echo "======================================"
echo "   MicroClimate HK - Quick Start"
echo "======================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Check if Docker is installed
echo -e "${YELLOW}Checking prerequisites...${NC}"
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓ Docker is installed${NC}"
else
    echo -e "${RED}✗ Docker is not installed. Please install Docker.${NC}"
    echo -e "${YELLOW}  Visit: https://docs.docker.com/get-docker/${NC}"
    exit 1
fi

# Check if docker-compose is available
if command -v docker-compose &> /dev/null; then
    echo -e "${GREEN}✓ Docker Compose is installed${NC}"
else
    echo -e "${RED}✗ Docker Compose is not installed${NC}"
    exit 1
fi

echo ""

# Check if .env exists
if [ -f ".env" ]; then
    echo -e "${GREEN}✓ .env file found${NC}"
else
    echo -e "${YELLOW}! .env file not found, creating from template...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✓ Created .env file${NC}"
    echo -e "${YELLOW}  Please edit .env with your configuration before proceeding${NC}"
    echo ""
    read -p "Press Enter to continue after editing .env"
fi

echo ""
echo -e "${YELLOW}Starting MicroClimate HK services...${NC}"
echo ""

# Start Docker Compose
docker-compose up -d

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}======================================${NC}"
    echo -e "${GREEN}   Services started successfully!${NC}"
    echo -e "${GREEN}======================================${NC}"
    echo ""
    echo -e "${CYAN}Access the application at:${NC}"
    echo "  Frontend:    http://localhost:5173"
    echo "  API:         http://localhost:8000"
    echo "  API Docs:    http://localhost:8000/docs"
    echo "  WebSocket:   ws://localhost:8001/ws"
    echo ""
    echo -e "${CYAN}View logs:${NC}"
    echo "  docker-compose logs -f [service-name]"
    echo ""
    echo -e "${CYAN}Stop services:${NC}"
    echo "  docker-compose down"
    echo ""
    echo -e "${CYAN}For more information, see:${NC}"
    echo "  docs/SETUP.md"
    echo ""
else
    echo ""
    echo -e "${RED}✗ Failed to start services${NC}"
    echo -e "${YELLOW}  Check the error messages above${NC}"
    echo ""
fi
