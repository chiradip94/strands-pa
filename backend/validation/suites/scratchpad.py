from . import TestCase

tests = [
    TestCase(
        name="scratchpad — create a plan",
        prompt=(
            "Use the scratchpad to create a weekend trip plan with 3 checklist tasks: "
            "book hotel, pack bags, rent car. Use markdown checkboxes."
        ),
        expected_behavior=(
            "Calls scratchpad(write, ...) to save a markdown checklist. "
            "The plan contains '- [ ] book hotel', '- [ ] pack bags', '- [ ] rent car' "
            "or similar checklist items."
        ),
        tags=["direct-tool", "scratchpad"],
        cleanup_prompt="Clear the scratchpad using scratchpad(clear, '', filename='plan.md').",
    ),
    TestCase(
        name="scratchpad — check off a task",
        prompt=(
            "Use the scratchpad to create a plan with tasks: "
            "buy groceries, cook dinner, wash dishes. "
            "Then use checkoff to mark groceries as done."
        ),
        expected_behavior=(
            "Calls scratchpad(write, ...) with a checklist, then scratchpad(checkoff, 'groceries') "
            "to strike through the groceries task. "
            "Result shows '- [x] ~~buy groceries~~' or similar."
        ),
        tags=["direct-tool", "scratchpad"],
        cleanup_prompt="Clear the scratchpad using scratchpad(clear, '', filename='plan.md').",
    ),
    TestCase(
        name="scratchpad — read and update plan",
        prompt=(
            "Use scratchpad to create a plan with tasks A, B, C. "
            "Then update it by appending task D. "
            "Finally read the full plan back and show me."
        ),
        expected_behavior=(
            "Calls scratchpad(write, ...), then scratchpad(append, ...) or scratchpad(write, ...) "
            "to add task D. Then calls scratchpad(read) and returns the updated content "
            "confirming all four tasks are present."
        ),
        min_score=0.6,
        tags=["direct-tool", "scratchpad"],
        cleanup_prompt="Clear the scratchpad using scratchpad(clear, '', filename='plan.md').",
    ),
]
