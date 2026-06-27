import httpx
from strands import tool


@tool
async def http_request(
    url: str,
    method: str = "GET",
    headers: dict | None = None,
    body: str | None = None,
) -> str:
    """Make an HTTP request to fetch JSON, HTML, or any web resource. Use this for calling REST APIs, fetching JSON data, or retrieving web content when a full browser is unnecessary.

    Args:
        url: The full URL to request (including https://)
        method: HTTP method — GET, POST, PUT, PATCH, DELETE (default GET)
        headers: Optional dict of HTTP headers (e.g. {"Authorization": "Bearer ..."})
        body: Request body string for POST/PUT/PATCH (ignored for GET/DELETE)

    Returns:
        Response status code and body content as text
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.request(method, url, headers=headers, content=body)
        return f"Status: {resp.status_code}\n\n{resp.text}"
