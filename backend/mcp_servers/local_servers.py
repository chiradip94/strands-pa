import sys
import os
from strands.tools.mcp import MCPClient
from mcp import stdio_client, StdioServerParameters
from dotenv import load_dotenv

load_dotenv()

# Get the absolute path to the python_executor script
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON_EXECUTOR_PATH = os.path.join(CURRENT_DIR, "python_executor.py")

python_server = MCPClient(
    lambda: stdio_client(
        StdioServerParameters(
            command=sys.executable, 
            args=[PYTHON_EXECUTOR_PATH]
        )
    )
)

BROWSER_SERVER_PATH = os.path.abspath(os.path.join(CURRENT_DIR, "..", "tools", "browser_server.py"))

_pw_url = os.getenv("PLAYWRIGHT_MCP_URL")

if _pw_url:
    from mcp.client.streamable_http import streamable_http_client
    playwright_client = MCPClient(
        lambda: streamable_http_client(url=_pw_url)
    )
else:
    _pw_env = {**os.environ}
    playwright_client = MCPClient(
        lambda env=_pw_env: stdio_client(
            StdioServerParameters(command=sys.executable, args=[BROWSER_SERVER_PATH], env=env)
        )
    )
    del _pw_env
del _pw_url