from strands.multiagent import Swarm
from agents.all_agents import get_agents
from mcp_servers.remote_servers import rival_search_mcp_client, remote_time_client
from mcp_servers.local_servers import python_server
from container import Container
import asyncio

async def chat_with_agent(query: str):
    # Initialize container for DI
    container = Container()
    container.wire(modules=["agents.all_agents"])

    # Use ALREADY loaded tools (cached in the clients from lifespan/start)
    search_mcp_tools = await rival_search_mcp_client.load_tools()
    python_tools = await python_server.load_tools()
    time_tools = await remote_time_client.load_tools()
    
    # Get initialized native agents
    agents = get_agents(search_mcp_tools, python_tools, time_tools)
    
    # Find the initial agent to use as entry point
    initial_agent = next(a for a in agents if a.name == "Initial Agent")

    # Create the Swarm
    swarm = Swarm(
        agents,
        entry_point=initial_agent,
        max_handoffs=10,
        max_iterations=20,
        repetitive_handoff_detection_window=3,
        repetitive_handoff_min_unique_agents=2,
    )

    # Run the swarm
    async for event in swarm.stream_async(query):
        yield event
