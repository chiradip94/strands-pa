import sys
import subprocess
import tempfile
import os
from pathlib import Path
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Python Executor")

SCRATCH_DIR = Path(__file__).resolve().parent.parent / "scratch"
SANDBOX = Path(__file__).resolve().parent / "_sandbox.py"

_BLOCKED_PATTERNS = [
    "os.system(",
    "os.popen(",
    "subprocess.",
    "shutil.rmtree(",
    "socket.connect(",
    "socket.create_connection(",
    "urllib.request.",
    "requests.",
    "httpx.",
    "ftplib.",
    "smtplib.",
    "exec(",
    "eval(",
    "compile(",
    "__import__(",
    "pickle.",
    "shelve.",
    "marshal.",
    "ctypes.",
]

_SECRET_ENV_PREFIXES = ("LLM_", "LANGFUSE_", "CAL_", "QDRANT_", "OPENAI_", "ANTHROPIC_")
_SECRET_ENV_PATTERNS = ("KEY", "SECRET", "TOKEN", "PASSWORD")


def _sanitized_env() -> dict:
    safe = {}
    for k, v in os.environ.items():
        ku = k.upper()
        if any(ku.startswith(p) for p in _SECRET_ENV_PREFIXES):
            continue
        if any(p in ku for p in _SECRET_ENV_PATTERNS):
            continue
        safe[k] = v
    return safe


def _is_safe(source: str) -> tuple[bool, str]:
    for pattern in _BLOCKED_PATTERNS:
        if pattern in source:
            return False, f"Blocked for security: '{pattern}' is not allowed"
    return True, ""


def _run(path: Path) -> str:
    result = subprocess.run(
        [sys.executable, str(SANDBOX), str(path)],
        capture_output=True,
        text=True,
        timeout=120,
        cwd=str(SCRATCH_DIR),
        env=_sanitized_env(),
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
        source = resolved.read_text()
        safe, reason = _is_safe(source)
        if not safe:
            return reason
        SCRATCH_DIR.mkdir(parents=True, exist_ok=True)
        try:
            return _run(resolved)
        except subprocess.TimeoutExpired:
            return "Error: Execution timed out (120s limit)"
        except Exception as e:
            return f"Error: {str(e)}"

    safe, reason = _is_safe(code)
    if not safe:
        return reason
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
