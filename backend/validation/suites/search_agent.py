from . import TestCase

tests = [
    TestCase(
        name="search_agent — web search handoff",
        prompt="Search the web for the latest news about quantum computing advancements in 2026.",
        expected_behavior="Hands off to search_agent. Returns actual search results with news about quantum computing. Does NOT hallucinate or make up generic content.",
        tags=["sub-agent", "search"],
    ),
]
