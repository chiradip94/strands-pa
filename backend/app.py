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

    # 1. Agent taking control
    if event_type == "multiagent_node_start":
        msgs.append({"type": "node_start", "node_id": event.get("node_id", "")})

    # 2. Streaming content from an agent
    elif event_type == "multiagent_node_stream":
        inner = event.get("event", {})
        if isinstance(inner, dict):
            if "data" in inner and isinstance(inner["data"], str):
                msgs.append({"type": "text", "text": inner["data"]})
            elif "reasoningText" in inner and isinstance(inner["reasoningText"], str):
                msgs.append({"type": "reasoning", "text": inner["reasoningText"]})

    # 3. Handoff between agents
    elif event_type == "multiagent_handoff":
        from_ids = event.get("from_node_ids", [])
        to_ids = event.get("to_node_ids", [])
        msgs.append({
            "type": "handoff",
            "from": ", ".join(from_ids) if isinstance(from_ids, list) else str(from_ids),
            "to": ", ".join(to_ids) if isinstance(to_ids, list) else str(to_ids),
        })

    # 4. Final result
    elif event_type == "multiagent_result":
        result = event.get("result")
        metadata = {
            "status": result.status.value,
            "execution_time": result.execution_time,
            "execution_count": result.execution_count,
            "input_token": result.accumulated_usage["inputTokens"],
            "output_token": result.accumulated_usage["outputTokens"]
        }
        last_node = result.node_history[-1]
        node_result = result.results[last_node.node_id]
        final_response = str(node_result.result)
        msgs.append({"type": "done", "metadata": metadata, "text": final_response})

    # 5. Conversation summarization
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
            try:
                with langfuse.start_as_current_observation(as_type="span", name="chat"):
                    with propagate_attributes(session_id=session_id):
                        async for event in chat.chat_with_agent(query, session_id):
                            for msg in _process_event(event):
                                await websocket.send_json(msg)
            except Exception as stream_err:
                print(f"Streaming error: {stream_err}")
                await websocket.send_json({"error": str(stream_err)})

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")


@app.get("/history")
@inject
async def get_history(session_id: str = "default", conversation_history=Provide[Container.conversation_history]):
    messages = conversation_history.get_conversation(session_id)
    return [
        {
            "role": msg.get("role"),
            "content": msg.get("content"),
            "agent_name": msg.get("agent_name"),
            "metadata": msg.get("metadata"),
        }
        for msg in messages
    ]

container.wire(modules=[__name__])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)