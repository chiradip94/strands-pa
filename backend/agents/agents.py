from strands import Agent as StrandsAgent
from container import Container
from dependency_injector.wiring import Provide, inject


@inject
class Agent:
    def __init__(self, name:str, description:str, tools=[], llm_model=Provide[Container.llm_model]):
        self.name = name
        self.agent = StrandsAgent(
            model=llm_model,
            name=name,
            description=description,
            tools=tools,
        )

    async def run(self,query:str):
        async for event in self.agent.stream_async(query):
            yield event