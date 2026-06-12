from dependency_injector import containers, providers
from strands.multiagent import Swarm
from config import config
from utils.llm import get_llm_model
from agents.all_agents import get_agents
from utils.tools_cache import get_search_tools, get_python_tools, get_time_tools


def _create_swarm(agents):
    initial_agent = next(a for a in agents if a.name == "Initial Agent")
    return Swarm(
        agents,
        entry_point=initial_agent,
        id="swarm",
        max_handoffs=10,
        max_iterations=20,
    )


class Container(containers.DeclarativeContainer):
    container_config = providers.Configuration()
    container_config.from_dict(config)

    llm_model = providers.Singleton(
        get_llm_model,
        base_url=container_config.llm_base_url,
        api_key=container_config.llm_api_key,
        model=container_config.llm_model,
    )

    agents = providers.Singleton(
        get_agents,
        providers.Callable(get_search_tools),
        providers.Callable(get_python_tools),
        providers.Callable(get_time_tools),
        llm_model=llm_model,
    )

    swarm = providers.Singleton(_create_swarm, agents=agents)