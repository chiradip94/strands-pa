import time

from agents.orchestrator import create_orchestrator

AGENT_ID = "initial_agent"


class Chat:

    def __init__(self, sub_agent_bundle, session_repo, llm_model, system_prompt):
        self._sub_agent_bundle = sub_agent_bundle
        self._session_repo = session_repo
        self._llm_model = llm_model
        self._system_prompt = system_prompt
        self._orchestrators = {}

    def _get_or_create(self, session_id: str):
        if session_id not in self._orchestrators:
            orchestrator = create_orchestrator(
                self._sub_agent_bundle,
                self._session_repo,
                self._llm_model,
                self._system_prompt,
                session_id,
            )
            self._orchestrators[session_id] = orchestrator
        return self._orchestrators[session_id]

    async def chat_with_agent(self, query: str, session_id: str = "default"):
        orchestrator = self._get_or_create(session_id)

        start_time = time.monotonic()
        final_text = ""

        async for event in orchestrator.stream_async(query):
            if isinstance(event, dict):
                if "data" in event and isinstance(event.get("delta"), dict):
                    final_text += event["data"]
                elif event.get("type") == "tool_stream":
                    data = event.get("tool_stream_event", {}).get("data", {})
                    if "data" in data:
                        final_text += data["data"]
            yield event

        yield {
            "type": "done",
            "text": final_text,
            "metadata": {
                "status": "COMPLETED",
                "execution_time": round(time.monotonic() - start_time, 2),
            }
        }
