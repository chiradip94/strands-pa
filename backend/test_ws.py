import asyncio
import websockets
import json

async def test_ws():
    uri = "ws://localhost:8000/ws"
    async with websockets.connect(uri) as websocket:
        print("Connected to WebSocket.")
        query = "Tell me about Strands Agents framework."
        print(f"Sending query: {query}")
        await websocket.send(query)
        
        try:
            while True:
                response = await websocket.recv()
                event = json.loads(response)
                
                # Show raw event for debugging
                # print(f"Raw event: {json.dumps(event, indent=2)}")
                
                if "data" in event:
                    print(event["data"], end="", flush=True)
                elif "reasoningText" in event:
                    print(f"Reasoning: {event['reasoningText']}", end="", flush=True)
                elif "result" in event:
                    print("\n\nFinal Result:", event["result"])
                    # Don't break immediately to see the rest of events
                elif "stop" in event:
                    print(f"\n[Stop Event: {event['stop'][0]}]")
                    break
                elif "error" in event:
                    print(f"\n[Error: {event['error']}]")
                    break
                else:
                    if "type" in event:
                        print(f"\n[Event Type: {event['type']}]")
                    else:
                        print(f"\n[Other Event: {list(event.keys())}]")
        except websockets.exceptions.ConnectionClosed:
            print("\nConnection closed.")

if __name__ == "__main__":
    asyncio.run(test_ws())
