export GOOGLE_OAUTH_CREDENTIALS="/home/chiro/projects/pa/backend/gmail_token.json"
export BYPASS_TOOL_CONSENT="true"

PYTHONUNBUFFERED=1 uv run uvicorn main:app --host 0.0.0.0 --port 8000