import signal
import sys
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from dependency_injector.wiring import inject, Provide
from langfuse import propagate_attributes
from utils.langfuse import get_langfuse_client
from container import Container, container


def safe_exit(signum, frame):
    print("\nSaving your data safely... Please wait!")
    sys.exit(0)


signal.signal(signal.SIGINT, safe_exit)

# Initialize Langfuse
langfuse = get_langfuse_client()


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _process_event(event):
    msgs = []
    event_type = event.get("type") if isinstance(event, dict) else None

    # Text from the orchestrator (TextStreamEvent: {"data": "...", "delta": {"text": ...}})
    if "data" in event and isinstance(event.get("delta"), dict):
        msgs.append({"type": "text", "text": event["data"]})

    # Reasoning from the orchestrator (ReasoningTextStreamEvent)
    elif event.get("reasoning"):
        msgs.append({"type": "reasoning", "text": event.get("reasoningText", "")})

    # Raw model chunk — tool call start or text fallback
    elif "event" in event:
        chunk = event["event"]
        if "contentBlockStart" in chunk:
            start = chunk["contentBlockStart"]
            if "toolUse" in start:
                msgs.append({"type": "tool_start", "tool_name": start["toolUse"].get("name", "")})

    # Sub-agent streaming (AgentAsToolStreamEvent / ToolStreamEvent)
    elif event_type == "tool_stream":
        tool_stream_event = event.get("tool_stream_event", {})
        tool_name = tool_stream_event.get("tool_use", {}).get("name", "")
        data = tool_stream_event.get("data", {})
        if "data" in data:
            msgs.append({"type": "text", "tool_name": tool_name, "text": data["data"]})
        elif data.get("reasoning"):
            msgs.append({"type": "reasoning", "tool_name": tool_name, "text": data.get("reasoningText", "")})

    # Final result from Chat service (already WS-ready)
    elif event_type == "done":
        msgs.append(event)

    # Conversation summarization
    elif event_type == "summarized":
        msgs.append({"type": "summarized", "text": event.get("text", "")})

    return msgs


@app.websocket("/ws")
@inject
async def websocket_endpoint(websocket: WebSocket, chat=Provide[Container.chat]):

    await websocket.accept()
    try:
        while True:
            query = await websocket.receive_text()
            session_id = websocket.query_params.get("session_id", "default")
            with langfuse.start_as_current_observation(as_type="span", name="chat") as span:
                with propagate_attributes(session_id=session_id):
                    try:
                        async for event in chat.chat_with_agent(query, session_id):
                            for msg in _process_event(event):
                                await websocket.send_json(msg)
                    except Exception as stream_err:
                        span.update(level="ERROR", status_message=str(stream_err))
                        print(f"Streaming error: {stream_err}")
                        await websocket.send_json({"error": str(stream_err)})
            langfuse.flush()

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")


@app.get("/history")
@inject
async def get_history(session_id: str = "default", session_repo=Provide[Container.session_repo]):
    from services.chat import AGENT_ID
    sms = session_repo.list_messages(session_id, AGENT_ID)
    result = []
    for sm in sms:
        msg = sm.to_message()
        role = msg.get("role")
        if role == "system":
            continue
        text = " ".join(
            b.get("text", "") for b in msg.get("content", []) if isinstance(b, dict) and "text" in b
        )
        if not text:
            continue
        result.append({"role": role, "content": text})
    return result

container.wire(modules=[__name__])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
