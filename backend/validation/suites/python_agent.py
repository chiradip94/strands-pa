from . import TestCase

tests = [
    TestCase(
        name="run_python(code=) — inline computation",
        prompt="Calculate the sum of all numbers from 1 to 100 using Python.",
        expected_behavior="Hands off to python_agent which uses run_python(code=...). Executes code sum(range(1,101)) or similar. Returns the correct answer: 5050.",
        tags=["sub-agent", "python"],
    ),
    TestCase(
        name="run_python(path=) — file-based execution",
        prompt="Write a Python script to a file called fibonacci.py that prints the first 15 Fibonacci numbers. Then run it.",
        expected_behavior="Uses write_file to save fibonacci.py to scratch, then uses run_python(path='fibonacci.py'). Output shows correct Fibonacci sequence: 0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377.",
        tags=["sub-agent", "python", "file"],
    ),
    TestCase(
        name="python_agent — data processing",
        prompt="Given the list [45, 67, 23, 89, 12, 56, 78, 34, 90, 11], find the mean, median, and mode using Python.",
        expected_behavior="Hands off to python_agent. Uses run_python to compute statistics. Returns correct mean (~50.5), median (50.5/51), and mode (no mode — all unique).",
        min_score=0.6,
        tags=["sub-agent", "python"],
    ),
]
