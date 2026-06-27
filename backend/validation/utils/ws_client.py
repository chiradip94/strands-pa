import json
import asyncio
from dataclasses import dataclass, field


@dataclass
class WsResponse:
    text: str = ""
    reasoning: str = ""
    tool_uses: list[str] = field(default_factory=list)
    handoffs: list[tuple[str, str]] = field(default_factory=list)
    events: list[dict] = field(default_factory=list)
    error: str | None = None
    execution_time: float | None = None


class WsClient:
    def __init__(self, url: str = "ws://localhost:8000/ws"):
        self._url = url

    async def send(self, query: str, session_id: str = "validation") -> WsResponse:
        import websockets

        result = WsResponse()
        uri = f"{self._url}?session_id={session_id}"
        async with websockets.connect(uri) as ws:
            await ws.send(query)
            while True:
                raw = await ws.recv()
                if isinstance(raw, bytes):
                    raw = raw.decode()
                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    result.events.append({"raw": raw})
                    result.text += raw
                    continue

                result.events.append(msg)
                msg_type = msg.get("type")

                if msg_type == "text":
                    result.text += msg.get("text", "")
                elif msg_type == "reasoning":
                    result.reasoning += msg.get("text", "")
                elif msg_type == "tool_start":
                    name = msg.get("tool_name", "")
                    if name and name not in result.tool_uses:
                        result.tool_uses.append(name)
                elif msg_type == "handoff":
                    fr = msg.get("from", "")
                    to = msg.get("to", "")
                    result.handoffs.append((fr, to))
                elif msg_type == "done":
                    result.text = msg.get("text", result.text)
                    meta = msg.get("metadata", {})
                    result.execution_time = meta.get("execution_time")
                    break
                elif msg_type == "error":
                    result.error = msg.get("error") or msg.get("text", str(msg))
                    break

        return result
