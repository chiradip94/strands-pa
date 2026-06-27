from . import TestCase

tests = [
    TestCase(
        name="browser_agent — navigate and extract",
        prompt="Go to example.com and tell me the page title and main heading.",
        expected_behavior="Hands off to browser_agent. Uses browser_navigate to visit example.com. Uses browser_snapshot or browser_evaluate to extract the page title. Returns title 'Example Domain' and main heading 'Example Domain'.",
        tags=["sub-agent", "browser"],
    ),
]
