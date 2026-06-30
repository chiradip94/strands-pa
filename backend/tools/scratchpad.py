import re
from pathlib import Path

from strands import tool, ToolContext

SCRATCH_DIR = Path(__file__).resolve().parent.parent / "scratch" / "scratchpad"


def _ensure_scratch() -> Path:
    SCRATCH_DIR.mkdir(parents=True, exist_ok=True)
    return SCRATCH_DIR


def _file_path(filename: str) -> Path:
    return _ensure_scratch() / (filename or "plan.md")


@tool(context=True)
def scratchpad(action: str, content: str = "", filename: str = "", tool_context: ToolContext = None) -> str:
    """Working memory for planning and tracking progress across tool calls.

    All scratchpad data is persisted to files in scratch/scratchpad/.

    ACTIONS:
      write    - Write `content` to file (overwrites)
      append   - Append `content` to file
      read     - Return file content
      clear    - Empty the file
      checkoff - Mark a task complete by striking it through. `content` is text
                 to match in the first unchecked `- [ ]` task line.

    Args:
        action: write | append | read | clear | checkoff
        content: Text content (for write/append/checkoff)
        filename: Target filename (default "plan.md")

    Returns:
        Current scratchpad content or status message
    """
    fpath = _file_path(filename)

    if action == "write":
        fpath.write_text(content)
    elif action == "append":
        existing = fpath.read_text() if fpath.exists() else ""
        fpath.write_text((existing + "\n" + content) if existing else content)
    elif action == "read":
        return fpath.read_text() if fpath.exists() else "(scratchpad is empty)"
    elif action == "clear":
        fpath.write_text("")
    elif action == "checkoff":
        existing = fpath.read_text() if fpath.exists() else ""
        if not existing:
            return "(scratchpad is empty)"
        lines = existing.split("\n")
        found = False
        for i, line in enumerate(lines):
            if "~~" in line or "[x]" in line:
                continue
            # match either "- [ ] task" or "- task" (plain bullet)
            m = re.match(r"^(\s*-\s*)(?:\[\s*\]\s*)?(.*)", line)
            if m and content in line:
                indent = m.group(1)
                task_text = m.group(2)
                lines[i] = f"{indent}[x] ~~{task_text}~~"
                found = True
                break
        if not found:
            return f"No unchecked task matching '{content}' found"
        fpath.write_text("\n".join(lines))
        return f"Checked off: {task_text.strip()}"
    else:
        return f"Unknown action '{action}'. Use: write, append, read, clear, checkoff"

    return content if content else "(scratchpad is empty)"
