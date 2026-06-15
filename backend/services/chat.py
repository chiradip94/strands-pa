class Chat:

    def __init__(self, swarm):
        self.swarm = swarm

    async def chat_with_agent(self, query: str):
        async for event in self.swarm.stream_async(query):
            yield event