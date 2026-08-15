#!/usr/bin/env bash
set -uo pipefail

echo "=== GSU Weather Dashboard: Environment Setup ==="

# Detect which Docker Compose command is available
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
elif command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    echo "Neither 'docker compose' nor 'docker-compose' found - install Docker before continuing."
    return 1
fi

# 1. Create venv if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# 2. Activate venv
source venv/bin/activate

# 3. Install dependencies
echo "Installing requirements..."
pip install -r requirements.txt

# 4. Set up .env if missing
if [ ! -f ".env" ]; then
    echo "No .env found - copying .env.example. Fill in real values before continuing!"
    cp .env.example .env
    echo "Edit .env now, then re-run this script or run.sh"
    return 1
fi

# 5. Bring up the DB container
echo "Starting MariaDB container..."
$DOCKER_COMPOSE up -d

# 6. Wait for it to be healthy
echo "Waiting for database to be healthy..."
until [ "$(docker inspect -f '{{.State.Health.Status}}' gsu-weather-db 2>/dev/null)" == "healthy" ]; do
    sleep 1
done

echo "=== Setup complete. Environment ready. ==="
