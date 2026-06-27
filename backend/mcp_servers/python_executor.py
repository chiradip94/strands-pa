import sys
import subprocess
import tempfile
import os
from pathlib import Path
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Python Executor")

SCRATCH_DIR = Path(__file__).resolve().parent.parent / "scratch"

def _run(path: Path) -> str:
    result = subprocess.run(
        [sys.executable, str(path)],
        capture_output=True,
        text=True,
        timeout=120,
        cwd=str(SCRATCH_DIR),
    )
    output = result.stdout
    if result.stderr:
        output += f"\nErrors:\n{result.stderr}"
    return output.strip() or "Success (no output)"


@mcp.tool()
def run_python(code: str = "", path: str = "") -> str:
    """Execute python code and return the standard output and error.
    Use this for calculations, data processing, or testing logic.

    Provide either `code` (inline script) or `path` (existing file to run).
    Relative file paths in your code resolve automatically.
    All packages from the project (strands, httpx, etc.) are importable.

    Args:
        code: Python source code to execute (ignored if path is given)
        path: Name of an existing .py file to run. Use this to execute
              multi-file projects or scripts saved earlier.

    Returns:
        stdout and stderr from execution
    """
    if not code and not path:
        return "Error: provide either `code` or `path`"

    if path:
        resolved = (SCRATCH_DIR / path).resolve()
        if not str(resolved).startswith(str(SCRATCH_DIR.resolve())):
            return "Error: path traversal blocked"
        if not resolved.exists():
            return f"Error: '{path}' not found"
        SCRATCH_DIR.mkdir(parents=True, exist_ok=True)
        try:
            return _run(resolved)
        except subprocess.TimeoutExpired:
            return "Error: Execution timed out (120s limit)"
        except Exception as e:
            return f"Error: {str(e)}"

    with tempfile.NamedTemporaryFile(suffix=".py", mode='w', delete=False) as f:
        f.write(code)
        f_path = f.name

    try:
        SCRATCH_DIR.mkdir(parents=True, exist_ok=True)
        try:
            return _run(Path(f_path))
        except subprocess.TimeoutExpired:
            return "Error: Execution timed out (120s limit)"
        except Exception as e:
            return f"Error: {str(e)}"
    finally:
        os.unlink(f_path)

if __name__ == "__main__":
    mcp.run()
