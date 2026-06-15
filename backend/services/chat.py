class Chat:

    def __init__(self, swarm, conversation_history):
        self.swarm = swarm
        self.conversation_history = conversation_history

    def _format_history(self, history: list[dict]) -> str:
        if not history:
            return ""
        lines = ["Previous conversation:"]
        for msg in history:
            role = msg.get("role", "unknown")
            agent = msg.get("agent_name")
            content = msg.get("content", "")
            tag = f"{role} ({agent})" if agent else role
            lines.append(f"{tag}: {content}")
        return "\n".join(lines)

    async def chat_with_agent(self, query: str, session_id: str = "default"):
        history = self.conversation_history.get_conversation(session_id)
        context = self._format_history(history)
        enriched_query = f"{context}\n\n{query}" if context else query

        self.conversation_history.add_message(session_id, "user", query)

        final_text = None
        async for event in self.swarm.stream_async(enriched_query):
            if isinstance(event, dict) and event.get("type") == "multiagent_result":
                result = event.get("result")
                last_node = result.node_history[-1]
                node_result = result.results[last_node.node_id]
                final_text = str(node_result.result)
            yield event

        if final_text:
            self.conversation_history.add_message(
                session_id, "assistant", final_text
            )

        await self.conversation_history.update_conversation_with_summary(session_id)