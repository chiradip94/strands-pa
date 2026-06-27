import json
import re
import contextvars

ws_send = contextvars.ContextVar("ws_send")
ws_recv = contextvars.ContextVar("ws_recv")


def _format_prompt(prompt: str) -> str:
    m = re.match(r'^Tool "(\w+)" requires human approval\. Input: ({.*})$', prompt)
    if not m:
        return prompt
    tool_name = m.group(1)
    try:
        params = json.loads(m.group(2))
    except json.JSONDecodeError:
        return prompt

    labels = {
        "cancel_booking": "Cancel Booking",
        "delete_event_type": "Delete Event Type",
        "delete_schedule": "Delete Schedule",
    }
    label = labels.get(tool_name, tool_name.replace("_", " ").title())

    lines = [f"Approve: {label}"]
    for k, v in params.items():
        key = k.replace("_", " ").title()
        lines.append(f"  {key}: {v}")
    lines.append("  (yes/no)")
    return "\n".join(lines)


async def ask_human(prompt: str) -> str:
    send = ws_send.get()
    recv = ws_recv.get()
    await send({"type": "confirmation_required", "prompt": _format_prompt(prompt)})
    raw = await recv()
    if isinstance(raw, str) and raw.startswith("{"):
        try:
            return json.loads(raw).get("response", "no")
        except json.JSONDecodeError:
            pass
    return raw
