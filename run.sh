#!/usr/bin/env bash
# ==============================================================================
# OKF vs RAG Architectural Comparison POC
# Single-file runner: Configures environment, starts Docker, provisions data,
# and executes the side-by-side comparison in Console and Web UI.
# ==============================================================================

set -e

# Add common macOS / Linux paths for Docker and Python
export PATH="/usr/local/bin:/opt/homebrew/bin:/Applications/Docker.app/Contents/Resources/bin:$PATH"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "================================================================================"
echo "  🚀 Starting Open Knowledge Format (OKF) vs Vector RAG Comparison POC"
echo "================================================================================"

# 1. Check Python
if ! command -v python3 &>/dev/null; then
    echo "❌ Error: python3 is required but not found in PATH."
    exit 1
fi

# 2. Virtual Environment Setup
VENV_DIR="$SCRIPT_DIR/.venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Creating Python virtual environment in .venv..."
    python3 -m venv "$VENV_DIR"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# 3. Install / Verify Dependencies
echo "📥 Checking & installing dependencies from requirements.txt..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

# 4. Environment Variables Setup
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    if [ -f "$SCRIPT_DIR/../.env" ]; then
        echo "🔑 Copying existing credentials from parent directory .env..."
        cp "$SCRIPT_DIR/../.env" "$SCRIPT_DIR/.env"
    elif [ -f "$SCRIPT_DIR/../../.env" ]; then
        echo "🔑 Copying existing credentials from root workspace .env..."
        cp "$SCRIPT_DIR/../../.env" "$SCRIPT_DIR/.env"
    elif [ -f "$SCRIPT_DIR/.env.example" ]; then
        echo "ℹ️  Creating .env from .env.example..."
        cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
    fi
fi

# Ensure storage directory exists
mkdir -p "$SCRIPT_DIR/storage/qdrant_data"

# 5. Bring up Docker Container for Vector DB
echo "🐳 Checking Docker status for vector database..."
DOCKER_AVAILABLE=false

if command -v docker &>/dev/null; then
    # Check if docker daemon is running
    if ! docker info &>/dev/null; then
        if [[ "$OSTYPE" == "darwin"* ]] && [ -d "/Applications/Docker.app" ]; then
            echo "⏳ Launching Docker Desktop on macOS..."
            open -a Docker
            # Wait for docker daemon to initialize
            for i in {1..20}; do
                if docker info &>/dev/null; then
                    echo "✓ Docker daemon is active."
                    break
                fi
                sleep 2
            done
        fi
    fi

    if docker info &>/dev/null; then
        echo "🚀 Bringing up Qdrant Vector Database container via Docker Compose..."
        docker compose up -d
        DOCKER_AVAILABLE=true

        # Wait for Qdrant health check on port 6333
        echo "⏳ Waiting for Qdrant service readiness..."
        for i in {1..15}; do
            if curl -s http://localhost:6333/healthz &>/dev/null || curl -s http://localhost:6333/readyz &>/dev/null; then
                echo "✓ Qdrant Vector Database is ready on port 6333 (Dashboard: http://localhost:6333/dashboard)"
                break
            fi
            sleep 1
        done
    else
        echo "⚠️  Docker daemon could not be reached. The POC will run with the built-in embedded Qdrant vector engine."
    fi
else
    echo "⚠️  Docker command not found in PATH. Running with built-in embedded vector engine."
fi

# 6. Execute Application
echo "✨ Starting OKF vs RAG comparison engine..."
python -m src.main "$@"
