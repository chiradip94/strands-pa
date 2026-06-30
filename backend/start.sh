SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

PYTHONUNBUFFERED=1 uv run uvicorn app:app --host 0.0.0.0 --port 8000 --reload --reload-exclude 'scratch/*' --reload-exclude 'validation/*'