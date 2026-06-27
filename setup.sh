#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"

echo "=== strands-pa setup ==="

# --- Check prerequisites ---
PYTHON_OK=false
for cmd in python3.11 python3.12 python3; do
    if command -v "$cmd" &>/dev/null; then
        ver=$("$cmd" --version 2>&1 | grep -oP '\d+\.\d+')
        major="${ver%.*}"
        minor="${ver#*.}"
        if [ "$major" -ge 3 ] && [ "$minor" -ge 11 ]; then
            PYTHON_OK=true
            PYTHON="$cmd"
            echo "[OK] Python $("$PYTHON" --version 2>&1)"
            break
        fi
    fi
done
if [ "$PYTHON_OK" != true ]; then
    echo "[ERROR] Python 3.11+ is required. Install it first."
    echo "  Recommended: https://github.com/astral-sh/uv (includes Python)"
    exit 1
fi

if ! command -v uv &>/dev/null; then
    echo "[INFO] uv not found."
    echo "  Install via brew: brew install uv"
    echo "  Or via script: curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo "  See: https://docs.astral.sh/uv/"
    exit 1
fi
echo "[OK] uv $(uv --version 2>&1 | head -1)"

# --- .env ---
if [ ! -f "$BACKEND_DIR/.env" ]; then
    if [ -f "$BACKEND_DIR/.env.example" ]; then
        cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
        echo "[INFO] Created backend/.env from .env.example — edit it with your API keys."
    else
        echo "[WARN] No .env.example found. Create backend/.env manually."
    fi
else
    echo "[OK] backend/.env exists"
fi

# --- Python dependencies ---
echo "[INFO] Installing Python dependencies..."
cd "$BACKEND_DIR"
uv sync
echo "[OK] Dependencies installed"

# --- Playwright Firefox ---
echo "[INFO] Installing Playwright Firefox browser..."
uv run playwright install firefox
echo "[OK] Playwright Firefox installed"

# --- System deps (optional) ---
echo "[INFO] Playwright may need system libraries for headed mode."
echo "  Run this if Firefox doesn't launch:"
echo "    sudo uv run playwright install-deps firefox"
echo ""

# --- Done ---
echo ""
echo "=== Setup complete ==="
echo ""
echo "Next steps:"
echo "  1. Edit backend/.env with your API keys (LLM provider, Qdrant, Cal.com, MongoDB)"
echo "  2. Start the backend: cd backend && uv run uvicorn app:app --host 0.0.0.0 --port 8000 --reload"
echo "  3. Start the frontend: cd frontend && python3 -m http.server 8080"
echo "  4. Open http://localhost:8080 in your browser"
echo ""
