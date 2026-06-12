from dependency_injector.wiring import inject, Provide
from container import Container


class Chat:

    @inject
    def __init__(self, swarm=Provide[Container.swarm]):
        self.swarm = swarm

    @classmethod
    async def create(cls):
        container = Container()
        container.wire(modules=["agents.all_agents", "services.chat"])
        return cls()

    async def chat_with_agent(self, query: str):
        async for event in self.swarm.stream_async(query):
            yield event