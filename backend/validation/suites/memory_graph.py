from . import TestCase

tests = [
    TestCase(
        name="memory_graph — store and retrieve",
        prompt="Remember that my favorite color is blue. Then tell me what my favorite color is.",
        expected_behavior=(
            "Hands off to memory_agent. Uses store_memories to persist "
            "the fact 'favorite color is blue'. Then uses search_memory "
            "to retrieve it. Confirms the color is blue."
        ),
        tags=["sub-agent", "memory"],
        cleanup_prompt=(
            "Actually, I don't have a favorite color. That was a test — "
            "please forget it. Store that I have no favorite color."
        ),
    ),
    TestCase(
        name="memory_graph — update stored facts",
        prompt=(
            "Remember that I live in Paris. "
            "Actually, I moved — I live in Berlin now. "
            "What city do I live in?"
        ),
        expected_behavior=(
            "Hands off to memory_agent. Stores 'live in Paris', then on correction "
            "detects the contradiction and updates to 'live in Berlin'. "
            "Final answer confirms Berlin, not Paris."
        ),
        tags=["sub-agent", "memory"],
        cleanup_prompt=(
            "That was a test. I don't live in Paris or Berlin. "
            "Please forget all location facts about me."
        ),
    ),
]
