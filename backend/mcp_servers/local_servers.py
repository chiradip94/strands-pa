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
