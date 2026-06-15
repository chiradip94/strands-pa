from dependency_injector import containers, providers
from strands.multiagent import Swarm
from config import config
from utils.llm import get_llm_model
from agents.all_agents import get_agents
from utils.get_tools import get_mcp_tools
from mcp_servers.local_servers import python_server
from mcp_servers.remote_servers import rival_search_mcp_client, remote_time_client


def _create_swarm(llm_model):
    search_tools = get_mcp_tools(rival_search_mcp_client)
    python_tools = get_mcp_tools(python_server)
    time_tools = get_mcp_tools(remote_time_client)
    agents = get_agents(search_tools, python_tools, time_tools, llm_model)
    initial_agent = next(a for a in agents if a.name == "Initial Agent")
    return Swarm(
        agents,
        entry_point=initial_agent,
        id="swarm",
        max_handoffs=10,
        max_iterations=20,
    )


def _make_chat(swarm):
    from services.chat import Chat
    return Chat(swarm=swarm)


class Container(containers.DeclarativeContainer):
    config_provider = providers.Configuration()
    config_provider.from_dict(config)

    llm_model = providers.Singleton(
        get_llm_model,
        base_url=config_provider.llm_base_url,
        api_key=config_provider.llm_api_key,
        model=config_provider.llm_model,
    )

    swarm = providers.Singleton(_create_swarm, llm_model=llm_model)
    chat = providers.Singleton(_make_chat, swarm=swarm)


container = Container()
chat = container.chat()
