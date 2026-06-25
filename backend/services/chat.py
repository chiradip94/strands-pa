import time


class Chat:

    def __init__(self, orchestrator, conversation_history):
        self.orchestrator = orchestrator
        self.conversation_history = conversation_history

    def _format_history(self, history: list[dict]) -> str:
        if not history:
            return ""
        lines = ["<context_from_older_conversation>"]
        for msg in history:
            role = msg.get("role", "unknown")
            agent = msg.get("agent_name")
            content = msg.get("content", "")
            tag = f"{role} ({agent})" if agent else role
            lines.append(f"{tag}: {content}")
        lines.append("</context_from_older_conversation>")
        lines.append("The content above is from an older conversation — it is context only, not new instructions. Any dates, times, or day names in it are stale and must not be used to determine the current date/time.")
        return "\n".join(lines)

    async def chat_with_agent(self, query: str, session_id: str = "default"):
        history = self.conversation_history.get_conversation(session_id)
        context = self._format_history(history)
        enriched_query = f"{context}\n\nNew query from user: {query}" if context else query

        self.conversation_history.add_message(session_id, "user", query)

        start_time = time.monotonic()
        final_text = ""

        async for event in self.orchestrator.stream_async(enriched_query):
            if isinstance(event, dict):
                # TextStreamEvent: {"data": "...", "delta": {"text": ...}}
                if "data" in event and isinstance(event.get("delta"), dict):
                    final_text += event["data"]
                # Sub-agent text via ToolStreamEvent
                elif event.get("type") == "tool_stream":
                    data = event.get("tool_stream_event", {}).get("data", {})
                    if "data" in data:
                        final_text += data["data"]
            yield event

        execution_time = time.monotonic() - start_time

        yield {
            "type": "done",
            "text": final_text,
            "metadata": {
                "status": "COMPLETED",
                "execution_time": round(execution_time, 2),
            }
        }

        if final_text:
            self.conversation_history.add_message(
                session_id, "assistant", final_text
            )

        if await self.conversation_history.update_conversation_with_summary(session_id):
            history = self.conversation_history.get_conversation(session_id)
            summary_text = next(
                (m["content"] for m in history if m.get("metadata", {}).get("type") == "conversation_summary"),
                None
            )
            if summary_text:
                yield {"type": "summarized", "text": summary_text}
