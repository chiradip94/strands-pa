from dependency_injector import containers, providers
from strands.multiagent import Swarm
from vector_store.qdrant import QdrantVectorStore
from config import config
from session_manager.mongo_session_manager import ConversationHistoryManager
from utils.llm import get_llm_model
from agents.all_agents import get_agents
from utils.get_tools import get_mcp_tools
from mcp_servers.local_servers import python_server
from mcp_servers.remote_servers import rival_search_mcp_client, remote_time_client
from tools.vector_search import make_memory_tools
from agents.memory_graph import create_memory_graph, make_memory_graph_tool


def _create_swarm(llm_model):
    search_tools = get_mcp_tools(rival_search_mcp_client)
    python_tools = get_mcp_tools(python_server)
    time_tools = get_mcp_tools(remote_time_client)
    memory_tools = make_memory_tools(container.vector_store())
    memory_graph = create_memory_graph(llm_model, container.vector_store())
    memory_storage_tool = make_memory_graph_tool(memory_graph)
    agents = get_agents(search_tools, python_tools, time_tools, memory_tools, memory_storage_tool, llm_model)
    initial_agent = next(a for a in agents if a.name == "Initial Agent")
    return Swarm(
        agents,
        entry_point=initial_agent,
        id="swarm",
        max_handoffs=20,
        max_iterations=30,
    )


def _make_chat(swarm, conversation_history):
    from services.chat import Chat
    return Chat(swarm=swarm, conversation_history=conversation_history)


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

    swarm = providers.Singleton(_create_swarm, llm_model=llm_model)
    chat = providers.Singleton(_make_chat, swarm=swarm, conversation_history=conversation_history)


container = Container()
chat = container.chat()
