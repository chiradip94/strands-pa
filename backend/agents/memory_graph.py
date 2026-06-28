import re
from strands import tool
from strands.multiagent import GraphBuilder
from strands.multiagent.graph import GraphState
from strands.multiagent.base import MultiAgentBase, NodeResult, Status, MultiAgentResult
from strands.agent.agent_result import AgentResult
from strands.types.content import ContentBlock, Message
from strands import Agent
from strands.agent.conversation_manager import SlidingWindowConversationManager


class MemoryVerifierNode(MultiAgentBase):
    """Custom node: searches Qdrant for each fact to verify it was stored."""

    def __init__(self, vector_store):
        super().__init__()
        self.vector_store = vector_store
        self.id = "verifier"

    async def invoke_async(self, task, invocation_state=None, **kwargs):
        if isinstance(task, list):
            task_str = " ".join(
                block.get("text", "") for block in task if isinstance(block, dict)
            )
        else:
            task_str = str(task) if not isinstance(task, str) else task
        facts = self._extract_facts(task_str)

        if not facts:
            result_text = "ALL STORED"
        else:
            missing = []
            for fact in facts:
                results = self.vector_store.search(fact, top_k=3)
                if not results or results[0]["score"] < 0.3:
                    missing.append(fact)

            if not missing:
                result_text = "ALL STORED"
            else:
                result_text = "MISSING:\n" + "\n".join(f"- {f}" for f in missing)

        agent_result = AgentResult(
            stop_reason="end_turn",
            message=Message(role="assistant", content=[ContentBlock(text=result_text)]),
            metrics={},
            state={},
        )
        node_result = NodeResult(
            result=agent_result,
            execution_time=0,
            status=Status.COMPLETED,
        )
        return MultiAgentResult(
            status=Status.COMPLETED,
            results={"verifier": node_result},
            execution_count=0,
            execution_time=0,
        )

    @staticmethod
    def _extract_facts(text: str) -> list[str]:
        facts = []
        for line in text.split("\n"):
            line = line.strip()
            m = re.search(r"\d+\.\s+(.+)", line)
            if m:
                fact = m.group(1).strip()
                if len(fact) > 3:
                    facts.append(fact)
            else:
                m = re.match(r"^-\s+(.+)$", line)
                if m:
                    fact = m.group(1).strip()
                    if len(fact) > 3:
                        facts.append(fact)
        seen = set()
        return [f for f in facts if not (f in seen or seen.add(f))]


def has_missing_facts(state: GraphState) -> bool:
    node_result = state.results.get("verifier")
    if not node_result:
        return False
    inner = node_result.result
    if isinstance(inner, MultiAgentResult):
        inner_node = inner.results.get("verifier")
        if inner_node:
            return "MISSING" in str(inner_node.result)
    return False


def create_memory_graph(llm_model, vector_store):
    """Create the Memory Graph: extract → store → verify → (loop if missing)."""

    fact_extractor = Agent(
        model=llm_model,
        name="fact_extractor",
        agent_id="fact_extractor",
        conversation_manager=SlidingWindowConversationManager(window_size=5),
        system_prompt="""Extract atomic personal facts from the user's message.

Return one fact per line as a numbered list. Only extract facts about the user or people they know:
- Personal attributes (name, age, location)
- Relationships and family
- Preferences, likes, dislikes
- Personal experiences
- Goals and plans

Skip: general knowledge, questions the user asks, current events.

When the user CORRECTS a previous fact, extract only the corrected fact. Ignore apologies, negations, and conversational filler.

Example:
User: My brother is [Name], he is 2.5 years older to me
Output:
1. User's brother is [Name]
2. [Name] is 2.5 years older than the user

Example:
User: Sorry, my name is [Name] (not [OldName])
Output:
1. User's name is [Name]""",
        tools=[],
    )

    class MemoryOperatorNode(MultiAgentBase):
        """Deterministic node: stores each fact via vector_store directly."""

        def __init__(self, vector_store, llm_model):
            super().__init__()
            self.vector_store = vector_store
            self.llm_model = llm_model
            self.id = "memory_operator"

        async def invoke_async(self, task, invocation_state=None, **kwargs):
            if isinstance(task, list):
                task_str = " ".join(
                    block.get("text", "") for block in task if isinstance(block, dict)
                )
            else:
                task_str = str(task) if not isinstance(task, str) else task

            facts = self._extract_facts(task_str)
            if not facts:
                result_text = "STORED:\n(no facts to store)"
            else:
                stored = []
                for fact in facts:
                    existing = self.vector_store.search(fact, top_k=10)
                    for r in existing:
                        if r["score"] >= 0.4:
                            old_text = r["metadata"].get("original_text", "").strip().lower()
                            if old_text and old_text != fact.strip().lower():
                                self.vector_store.delete(r["id"])
                    is_dup = any(
                        r["metadata"].get("original_text", "").strip().lower() == fact.strip().lower()
                        for r in existing if r["score"] >= 0.3
                    )
                    if not is_dup:
                        self.vector_store.add_vector(fact, {})
                    stored.append(fact)
                result_text = "STORED:\n" + "\n".join(f"- {f}" for f in stored)

            agent_result = AgentResult(
                stop_reason="end_turn",
                message=Message(role="assistant", content=[ContentBlock(text=result_text)]),
                metrics={},
                state={},
            )
            node_result = NodeResult(
                result=agent_result,
                execution_time=0,
                status=Status.COMPLETED,
            )
            return MultiAgentResult(
                status=Status.COMPLETED,
                results={"memory_operator": node_result},
                execution_count=0,
                execution_time=0,
            )

        @staticmethod
        def _extract_facts(text: str) -> list[str]:
            return MemoryVerifierNode._extract_facts(text)

    memory_operator = MemoryOperatorNode(vector_store, llm_model)

    verifier = MemoryVerifierNode(vector_store)

    builder = GraphBuilder()
    builder.add_node(fact_extractor, "fact_extractor")
    builder.add_node(memory_operator, "memory_operator")
    builder.add_node(verifier, "verifier")

    builder.add_edge("fact_extractor", "memory_operator")
    builder.add_edge("memory_operator", "verifier")
    builder.add_edge("verifier", "memory_operator", condition=has_missing_facts)

    builder.set_entry_point("fact_extractor")
    builder.set_max_node_executions(12)
    builder.reset_on_revisit(True)
    builder.set_graph_id("memory_graph")

    return builder.build()


def make_memory_graph_tool(memory_graph):
    """Create a @tool that wraps the Memory Graph for use by agents."""

    @tool
    def store_memories(query: str) -> str:
        """Store personal facts from the user's message into persistent memory.

        Extracts atomic personal facts, stores them (skipping duplicates,
        updating contradictions), and verifies they were saved. Use this
        when the user shares personal information about themselves or
        people they know.

        Args:
            query: The user's original message containing personal facts
        Returns:
            Summary of what was stored and verification result
        """
        result = memory_graph(query)
        node_result = result.results.get("verifier")
        summary = "Memory storage completed."
        if node_result and node_result.status == Status.COMPLETED:
            # Custom nodes nest their result inside the node's MultiAgentResult
            inner = node_result.result
            if isinstance(inner, MultiAgentResult):
                inner_node = inner.results.get("verifier")
                if inner_node:
                    summary = str(inner_node.result)
            else:
                summary = str(inner)
        return f"Memory storage result:\n{summary}"

    return store_memories
