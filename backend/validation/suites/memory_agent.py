from . import TestCase

tests = [
    TestCase(
        name="memory_agent — store and retrieve",
        prompt="Please remember that my name is Alex and I live in Tokyo. Then tell me what you remember about me.",
        expected_behavior="Hands off to memory_agent. Stores the fact via store_memories. Then retrieves it via search_memory. Confirms both name=Alex and location=Tokyo in the response.",
        tags=["sub-agent", "memory"],
    ),
]
