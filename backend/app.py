import asyncio
import json
import signal
import sys
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from dependency_injector.wiring import inject, Provide
from langfuse import propagate_attributes
from utils.langfuse import get_langfuse_client
from container import Container, container
from services.confirmation import ws_send, ws_recv


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
            cbs = chunk["contentBlockStart"]
            # OpenAI adapter nests toolUse under "start": {"start": {"toolUse": {...}}}
            # Anthropic/Bedrock nests toolUse directly: {"toolUse": {...}}
            tool_container = cbs.get("start", cbs)
            if "toolUse" in tool_container:
                msgs.append({"type": "tool_start", "tool_name": tool_container["toolUse"].get("name", "")})

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
    session_id = websocket.query_params.get("session_id", "default")
    stream_task = None

    async def _stream_chat(query, session_id):
        with langfuse.start_as_current_observation(as_type="span", name="chat") as span:
            with propagate_attributes(session_id=session_id):
                token_send = ws_send.set(websocket.send_json)
                token_recv = ws_recv.set(websocket.receive_text)
                try:
                    async for event in chat.chat_with_agent(query, session_id):
                        for msg in _process_event(event):
                            await websocket.send_json(msg)
                except asyncio.CancelledError:
                    await websocket.send_json({
                        "type": "done", "text": "(stopped)",
                        "metadata": {"status": "CANCELLED", "execution_time": 0}
                    })
                except Exception as stream_err:
                    span.update(level="ERROR", status_message=str(stream_err))
                    print(f"Streaming error: {stream_err}")
                    await websocket.send_json({"error": str(stream_err)})
                finally:
                    ws_send.reset(token_send)
                    ws_recv.reset(token_recv)
        langfuse.flush()

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                data = {"text": raw}

            msg_type = data.get("type", "")

            if msg_type == "stop":
                if stream_task and not stream_task.done():
                    stream_task.cancel()
                    stream_task = None
                continue

            query = data.get("text", "")
            if not query:
                continue

            if stream_task and not stream_task.done():
                stream_task.cancel()

            stream_task = asyncio.create_task(_stream_chat(query, session_id))

    except WebSocketDisconnect:
        if stream_task and not stream_task.done():
            stream_task.cancel()
        print("Client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")


@app.get("/sessions")
@inject
async def list_sessions(session_repo=Provide[Container.session_repo]):
    return session_repo.list_sessions()


@app.delete("/sessions/{session_id}")
@inject
async def delete_session(session_id: str, session_repo=Provide[Container.session_repo]):
    session_repo.delete_session(session_id)
    return {"ok": True}


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
