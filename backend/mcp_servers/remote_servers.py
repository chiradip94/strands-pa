from mcp.client.streamable_http import streamablehttp_client
from strands.tools.mcp import MCPClient


rival_search_mcp_client = MCPClient(
    lambda: streamablehttp_client(
        url="https://RivalSearchMCP.fastmcp.app/mcp"
    )
)

remote_time_client = MCPClient(lambda: streamablehttp_client(
    url="https://date-time-tools.iabhishek.workers.dev/mcp"
))