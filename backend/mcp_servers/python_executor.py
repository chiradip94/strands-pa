import sys
import subprocess
import tempfile
import os
from mcp.server.fastmcp import FastMCP

# Create the server
mcp = FastMCP("Python Executor")

@mcp.tool()
def run_python(code: str) -> str:
    """
    Execute python code and return the standard output and error.
    Use this for calculations, data processing, or testing logic.
    """
    with tempfile.NamedTemporaryFile(suffix=".py", mode='w', delete=False) as f:
        f.write(code)
        f_path = f.name
    
    try:
        # Run the script using the current python interpreter
        result = subprocess.run(
            [sys.executable, f_path], 
            capture_output=True, 
            text=True, 
            timeout=30
        )
        output = result.stdout
        if result.stderr:
            output += f"\nErrors:\n{result.stderr}"
        return output.strip() or "Success (no output)"
    except subprocess.TimeoutExpired:
        return "Error: Execution timed out (30s limit)"
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        if os.path.exists(f_path):
            os.remove(f_path)

if __name__ == "__main__":
    mcp.run()
