from . import TestCase

tests = [
    TestCase(
        name="cal_agent — get profile",
        prompt="Tell me my Cal.com profile information — what's my name and email?",
        expected_behavior=(
            "Hands off to cal_agent. Uses get_me tool to retrieve the user's Cal.com profile. "
            "Returns name and email from the response. Does NOT hallucinate profile data."
        ),
        tags=["sub-agent", "calendar"],
    ),
    TestCase(
        name="cal_agent — check availability",
        prompt="Check my availability for a 1-hour meeting tomorrow at 2:00 PM IST.",
        expected_behavior=(
            "Hands off to cal_agent. Uses get_availability or similar tool to check "
            "the time slot. Returns whether the slot is free or busy. "
            "Does NOT hallucinate availability."
        ),
        tags=["sub-agent", "calendar"],
    ),
    TestCase(
        name="cal_agent — list event types",
        prompt="What event types do I have on my calendar? List them.",
        expected_behavior=(
            "Hands off to cal_agent. Uses get_event_types to retrieve event types. "
            "Returns a list of event type names. Does NOT make up event types."
        ),
        tags=["sub-agent", "calendar"],
    ),
]
