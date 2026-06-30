from dataclasses import dataclass, field


@dataclass
class TestCase:
    name: str
    prompt: str
    expected_behavior: str
    min_score: float = 0.7
    tags: list[str] = field(default_factory=list)
    cleanup_prompt: str = ""
