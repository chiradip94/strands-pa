from . import TestCase

tests = [
    TestCase(
        name="currentDateTimeAndTimezone — direct time tool",
        prompt="What time is it right now? Tell me the current date and time in Asia/Kolkata.",
        expected_behavior="Uses the currentDateTimeAndTimezone tool to get the current time. Returns a valid date/time in Asia/Kolkata timezone. Does NOT hallucinate a date from training data.",
        tags=["direct-tool", "time"],
    ),
    TestCase(
        name="convertTimezones — timezone conversion",
        prompt="What time is it right now in New York (America/New_York)? First get the current time, then convert to New York.",
        expected_behavior="First calls currentDateTimeAndTimezone to get current time, then calls convertTimezones to convert to America/New_York. Returns correct converted time.",
        min_score=0.65,
        tags=["direct-tool", "time"],
    ),
    TestCase(
        name="mutateDate — date arithmetic",
        prompt="What is the date 7 days from today?",
        expected_behavior="Uses currentDateTimeAndTimezone (or mutateDate directly) to get today's date and adds 7 days. Returns a future date correctly.",
        tags=["direct-tool", "time"],
    ),
]
