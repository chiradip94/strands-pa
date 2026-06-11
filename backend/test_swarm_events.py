import asyncio
import os
import json
from strands.multiagent import Swarm
from strands import Agent
from strands.models.openai import OpenAIModel

async def test_swarm_streaming():
    model = OpenAIModel(
        model_id=os.getenv("LLM_MODEL"),
        client_args={
            "api_key": os.getenv("LLM_API_KEY"),
            "base_url": os.getenv("LLM_BASE_URL"),
        }
    )
    
    a1 = Agent(model=model, name="A1", description="Simple agent")
    swarm = Swarm([a1], entry_point=a1)
    
    print("Testing Swarm stream_async...")
    async for event in swarm.stream_async("Say hello"):
        # This mimics the sanitization in main.py
        if hasattr(event, "model_dump"):
            d = event.model_dump()
            print(f"Event Type: {type(event).__name__}")
            print(f"Fields: {list(d.keys())}")
            if "delta" in d:
                print(f"Delta: {repr(d['delta'])}")
            if "content" in d:
                print(f"Content: {repr(d['content'])}")
        else:
            print(f"Non-Pydantic Event: {type(event)} -> {event}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    asyncio.run(test_swarm_streaming())
