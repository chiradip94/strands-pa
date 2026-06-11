from dependency_injector import containers, providers
from config import config
from utils.llm import get_llm_model


class Container(containers.DeclarativeContainer):
    container_config = providers.Configuration()
    container_config.from_dict(config)

    llm_model = providers.Singleton(
        get_llm_model,
        base_url=container_config.llm_base_url,
        api_key=container_config.llm_api_key,
        model=container_config.llm_model,
    )