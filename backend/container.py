from dependency_injector import containers, providers
from strands import Agent
from vector_store.qdrant import QdrantVectorStore
from config import config
from session_manager.mongo_session_manager import ConversationHistoryManager
from utils.llm import get_llm_model
from agents.all_agents import get_sub_agents
from utils.get_tools import get_mcp_tools
from mcp_servers.local_servers import python_server
from tools.cal_com import make_cal_tools
from mcp_servers.remote_servers import rival_search_mcp_client, remote_time_client
from tools.vector_search import make_memory_tools
from agents.memory_graph import create_memory_graph, make_memory_graph_tool


ORCHESTRATOR_PROMPT = """You are a coordinator AI. Handle simple questions directly. For anything requiring specialized knowledge or capabilities, use one of the available tool agents.

AVAILABLE TOOL AGENTS:
- search_agent: Web research, news, social media, content analysis, scientific research. Use for finding current information or doing deep research.
- python_agent: Calculations, data processing, code execution, math problems. Use when the user needs computation or code.
- cal_agent: Calendar scheduling, bookings, event types, availability. Use for anything involving meetings, events, or scheduling.
- memory_agent: Storing or retrieving personal user facts (name, age, relationships, preferences, location, goals). Use when the user shares personal information or asks about stored information.

DIRECT TOOLS (call these yourself without a sub-agent):
- currentDateTimeAndTimezone — get the live current date/time
- convertTimezones — convert between IANA timezones
- mutateDate — add/subtract days, hours, months, years

RULES:
- Only use a tool agent when needed. For simple answers, respond directly.
- When you invoke a tool agent, do not generate any text before or while it runs.
- When a tool agent returns a result, present it clearly to the user. Do not call another tool to verify — trust the response.
- Never reference dates or times from your training data — they are always stale. Use the DIRECT TIME TOOLS for current temporal data. When the user says "today", "now", "tomorrow", or any relative date/time, call currentDateTimeAndTimezone first.
- Default timezone: Asia/Kolkata (+5:30). Account for timezone differences in conversions."""


def _create_orchestrator(llm_model):
    search_tools = get_mcp_tools(rival_search_mcp_client)
    python_tools = get_mcp_tools(python_server)
    time_tools = get_mcp_tools(remote_time_client)
    try:
        cal_tools = make_cal_tools()
    except ValueError:
        cal_tools = []
    memory_tools = make_memory_tools(container.vector_store())
    memory_graph = create_memory_graph(llm_model, container.vector_store())
    memory_storage_tool = make_memory_graph_tool(memory_graph)

    search_agent, python_agent, cal_agent, memory_agent = get_sub_agents(
        search_tools, python_tools, cal_tools, memory_tools, memory_storage_tool, llm_model
    )

    return Agent(
        model=llm_model,
        name="Initial Agent",
        agent_id="initial_agent",
        system_prompt=ORCHESTRATOR_PROMPT,
        tools=[
            search_agent.as_tool(
                name="search_agent",
                description="Web research, news, social media, content analysis, scientific research."
            ),
            python_agent.as_tool(
                name="python_agent",
                description="Calculations, data processing, code execution, math problems."
            ),
            cal_agent.as_tool(
                name="cal_agent",
                description="Calendar scheduling, bookings, event types, availability management."
            ),
            memory_agent.as_tool(
                name="memory_agent",
                description="Storing or retrieving personal user facts."
            ),
        ] + time_tools
    )


def _make_chat(orchestrator, conversation_history):
    from services.chat import Chat
    return Chat(orchestrator=orchestrator, conversation_history=conversation_history)


class Container(containers.DeclarativeContainer):
    config_provider = providers.Configuration()
    config_provider.from_dict(config)

    llm_model = providers.Singleton(
        get_llm_model,
        base_url=config_provider.llm_base_url,
        api_key=config_provider.llm_api_key,
        model=config_provider.llm_model,
    )

    vector_store = providers.Singleton(
        QdrantVectorStore,
        url=config_provider.qdrant_url,
        api_key=config_provider.qdrant_api_key,
        collection_name=config_provider.user_collection,
        model=config_provider.qdrant_model,
        vector_size=config_provider.qdrant_vector_size,
    )

    conversation_history = providers.Singleton(
        ConversationHistoryManager,
        model=llm_model,
        uri=config_provider.mongo_uri,
        db_name=config_provider.mongo_db,
    )

    orchestrator = providers.Singleton(_create_orchestrator, llm_model=llm_model)
    chat = providers.Singleton(_make_chat, orchestrator=orchestrator, conversation_history=conversation_history)


container = Container()
chat = container.chat()
