import os
from pathlib import Path

from strands import tool

SCRATCH_DIR = Path(__file__).resolve().parent.parent / "scratch"


def _ensure_scratch() -> Path:
    SCRATCH_DIR.mkdir(parents=True, exist_ok=True)
    return SCRATCH_DIR


def _safe_path(filename: str) -> Path:
    path = (_ensure_scratch() / filename).resolve()
    if not str(path).startswith(str(SCRATCH_DIR.resolve())):
        raise ValueError("Access denied: path traversal blocked")
    return path


@tool
def write_file(filename: str, content: str) -> str:
    """Save text content to a file for later retrieval. Use this to persist results, reports, or generated content. Path traversal (../) is blocked.

    Args:
        filename: Name of the file (e.g. "report.txt" or "data/output.json"). Subdirectories are created automatically.
        content: Text content to write

    Returns:
        Confirmation with byte count
    """
    path = _safe_path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return f"Written {len(content)} bytes"


@tool
def read_file(filename: str) -> str:
    """Read text content from a previously saved file. Use this to retrieve saved results, reports, or data files. Path traversal (../) is blocked.

    Args:
        filename: Name of the file (e.g. "report.txt" or "data/output.json").

    Returns:
        File content as text
    """
    path = _safe_path(filename)
    if not path.exists():
        return f"Error: '{filename}' not found"
    return path.read_text()


@tool
def delete_file(filename: str) -> str:
    """Delete a file or empty directory. Use this for cleanup after completing a task. Path traversal (../) is blocked.

    Args:
        filename: Name of the file or directory to delete (e.g. "report.txt" or "temp/")

    Returns:
        Confirmation of deletion
    """
    path = _safe_path(filename)
    if not path.exists():
        return f"Error: '{filename}' not found"
    if path.is_dir():
        path.rmdir()
        return "Deleted"
    path.unlink()
    return "Deleted"


@tool
def list_files(path: str = "") -> str:
    """List saved files and directories. Use this to see what files exist. Subdirectory contents are not shown recursively — use a path like "subdir/" to peek inside.

    Args:
        path: Optional subdirectory path (e.g. "data/" or "notes/"). Empty string lists the root.

    Returns:
        Directory listing with file sizes
    """
    base = _safe_path(path) if path else _ensure_scratch()
    if not base.exists():
        return f"Error: '{path}' not found" if path else "(empty)"
    if base.is_file():
        return f"{base.name} ({base.stat().st_size} bytes)"
    entries = []
    for entry in sorted(base.iterdir()):
        if entry.is_dir():
            entries.append(f"{entry.name}/")
        else:
            entries.append(f"{entry.name} ({entry.stat().st_size} bytes)")
    return "\n".join(entries) if entries else "(empty)"
