from . import TestCase

tests = [
    TestCase(
        name="workflow — search then save to file",
        prompt=(
            "Search the web for the current population of Japan, "
            "then save the answer to a file called japan_population.txt."
        ),
        expected_behavior=(
            "Hands off to search_agent to find the current population. "
            "Then calls write_file to save japan_population.txt. "
            "The file contains the population figure found by search. "
            "Both search_agent handoff and write_file tool are used."
        ),
        tags=["workflow", "search", "file"],
        cleanup_prompt=(
            "Delete the file called japan_population.txt using delete_file. "
            "Confirm it's gone."
        ),
    ),
    TestCase(
        name="workflow — time then calendar availability",
        prompt=(
            "First get the current date and time in Asia/Kolkata. "
            "Then check my calendar availability for a 1-hour meeting "
            "at that same time tomorrow."
        ),
        expected_behavior=(
            "Calls currentDateTimeAndTimezone to get today's time. "
            "Then hands off to cal_agent to check availability for tomorrow at that time. "
            "Returns both the current time and the availability result."
        ),
        min_score=0.6,
        tags=["workflow", "time", "calendar"],
    ),
    TestCase(
        name="workflow — python then save results",
        prompt=(
            "Use Python to calculate the first 8 Fibonacci numbers. "
            "Then save the result list to a file called fib_numbers.txt."
        ),
        expected_behavior=(
            "Hands off to python_agent which uses run_python(code=...) to compute "
            "the first 8 Fibonacci numbers. Then calls write_file to save "
            "fib_numbers.txt with the result. "
            "The final answer includes the sequence: 0, 1, 1, 2, 3, 5, 8, 13."
        ),
        tags=["workflow", "python", "file"],
        cleanup_prompt=(
            "Delete the file called fib_numbers.txt using delete_file. "
            "Confirm it's gone."
        ),
    ),
]
