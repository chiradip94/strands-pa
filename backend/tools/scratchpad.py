from strands import tool, ToolContext


@tool(context=True)
def scratchpad(action: str, content: str = "", tool_context: ToolContext = None) -> str:
    """Persistent working memory for tracking progress across tool calls. Use this to store checklists, plans, and intermediate notes while working through a task.

    Args:
        action: "write" to set content, "append" to add a new line, "read" to retrieve, "clear" to reset
        content: Text content for write/append actions (ignored for read/clear)

    Returns:
        Current scratchpad content after the action
    """
    state = tool_context.invocation_state
    scratch = state.get("scratchpad", "")
    if action == "write":
        scratch = content
    elif action == "append":
        scratch = (scratch + "\n" + content) if scratch else content
    elif action == "clear":
        scratch = ""
    state["scratchpad"] = scratch
    return scratch if scratch else "(scratchpad is empty)"
