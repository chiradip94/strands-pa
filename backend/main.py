from asyncio import base_events
from typing import Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from contextlib import asynccontextmanager
from utils.langfuse import get_langfuse_client
from services.chat import chat_with_agent
from mcp_servers.remote_servers import rival_search_mcp_client, remote_time_client
from mcp_servers.local_servers import python_server
import asyncio

# Initialize Langfuse
_ = get_langfuse_client()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await asyncio.gather(
        rival_search_mcp_client.load_tools(),
        python_server.load_tools(),
        remote_time_client.load_tools()
    )
    yield
    # Cleanup
    rival_search_mcp_client.stop(None, None, None)
    python_server.stop(None, None, None)
    remote_time_client.stop(None, None, None)



app = FastAPI(lifespan=lifespan)


def _process_event(event):
    msg = None
    event_type = event.get("type") if isinstance(event, dict) else None

    # 1. Agent taking control
    if event_type == "multiagent_node_start":
        msg = {"type": "node_start", "node_id": event.get("node_id", "")}

    # 2. Streaming content from an agent
    elif event_type == "multiagent_node_stream":
        inner = event.get("event", {})
        if isinstance(inner, dict):
            # Text streaming
            if "data" in inner and isinstance(inner["data"], str):
                msg = {"type": "text", "text": inner["data"]}
            # Reasoning/thinking
            elif "reasoningText" in inner and isinstance(inner["reasoningText"], str):
                msg = {"type": "reasoning", "text": inner["reasoningText"]}
            # Lifecycle events
            elif inner.get("init_event_loop") or inner.get("start_event_loop") or inner.get("start"):
                msg = {"type": "thinking"}
            # Stop signal
            elif inner.get("stop"):
                msg = {"type": "stop"}

    # 3. Handoff between agents
    elif event_type == "multiagent_handoff":
        from_ids = event.get("from_node_ids", [])
        to_ids = event.get("to_node_ids", [])
        msg = {
            "type": "handoff",
            "from": ", ".join(from_ids) if isinstance(from_ids, list) else str(from_ids),
            "to": ", ".join(to_ids) if isinstance(to_ids, list) else str(to_ids),
        }

    # 4. Final result
    elif event_type == "multiagent_result":
        result = event.get("result")
        metadata = {
            "status": result.status,
            "execution_time": result.execution_time,
            "execution_count": result.execution_count,
            "input_token": result.accumulated_usage.inputTokens,
            "output_token": result.accumulated_usage.outputTokens
        }
        final_response = result.node_history[-1].message
        msg = {"type": "done", "metadata": metadata, "text": final_response}
    
    return msg


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            query = await websocket.receive_text()

            try:
                async for event in chat_with_agent(query):
                    msg = _process_event(event)

                    if msg:
                        await websocket.send_json(msg)

            except Exception as stream_err:
                # Catch errors during a single query's streaming without killing the connection
                print(f"Streaming error: {stream_err}")
                await websocket.send_json({"error": str(stream_err)})

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)