from . import TestCase

tests = [
    TestCase(
        name="http_request — GET external API",
        prompt="Fetch https://httpbin.org/get and tell me what URL was sent in the response.",
        expected_behavior="Uses http_request tool to fetch https://httpbin.org/get. Correctly reports that the url field in the response is https://httpbin.org/get or similar. Does NOT hallucinate the result.",
        tags=["direct-tool", "http"],
    ),
    TestCase(
        name="http_request + write_file — save response to file",
        prompt="Fetch https://httpbin.org/get and save the response to a file named httpbin_test.json. Then read it back and confirm its contents.",
        expected_behavior="Uses http_request with output=httpbin_test.json to save the response. Then reads it back with read_file. Confirms the file contains valid JSON with a 'url' field.",
        min_score=0.65,
        tags=["direct-tool", "http", "file"],
    ),
    TestCase(
        name="file_ops — write, read, delete cycle",
        prompt="Create a file called greeting.txt with content 'Hello from validation!', then read it back, then delete it, then list files to confirm it's gone.",
        expected_behavior="Calls write_file, read_file, delete_file, list_files in sequence. Each step succeeds. Final listing does not contain greeting.txt.",
        tags=["direct-tool", "file"],
    ),
]
