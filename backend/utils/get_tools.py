def get_mcp_tools(mcp_client):
    if not mcp_client._tool_provider_started:
        mcp_client.start()
        mcp_client._tool_provider_started = True
    if mcp_client._loaded_tools is None:
        mcp_client._loaded_tools = []
        token = None
        while True:
            page = mcp_client.list_tools_sync(
                token, prefix=mcp_client._prefix, tool_filters=mcp_client._tool_filters
            )
            mcp_client._loaded_tools.extend(page)
            token = page.pagination_token
            if not token:
                break
    return mcp_client._loaded_tools
