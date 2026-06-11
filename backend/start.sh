SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export GOOGLE_OAUTH_CREDENTIALS="$SCRIPT_DIR/gmail_token.json"
export BYPASS_TOOL_CONSENT="true"

PYTHONUNBUFFERED=1 uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload