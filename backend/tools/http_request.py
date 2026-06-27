import socket
import ipaddress
from urllib.parse import urlparse

import httpx
from pathlib import Path
from strands import tool

SCRATCH_DIR = Path(__file__).resolve().parent.parent / "scratch"


def _check_ssrf(url: str) -> str | None:
    host = urlparse(url).hostname
    if not host:
        return "Invalid URL: could not parse hostname"
    try:
        ips = socket.getaddrinfo(host, None)
        for family, _, _, _, sockaddr in ips:
            ip = ipaddress.ip_address(sockaddr[0])
            if ip.is_private or ip.is_loopback or ip.is_link_local:
                return f"Blocked: requests to internal IPs are not allowed"
    except socket.gaierror:
        return f"Could not resolve hostname: {host}"
    return None


@tool
async def http_request(
    url: str,
    method: str = "GET",
    headers: dict | None = None,
    body: str | None = None,
    output: str = "",
) -> str:
    """Make an HTTP request to fetch JSON, HTML, or any web resource. Use this for calling REST APIs, fetching JSON data, or retrieving web content when a full browser is unnecessary. Requests to private/internal IPs are blocked.

    Args:
        url: The full URL to request (including https://)
        method: HTTP method — GET, POST, PUT, PATCH, DELETE (default GET)
        headers: Optional dict of HTTP headers (e.g. {"Authorization": "Bearer ..."})
        body: Request body string for POST/PUT/PATCH (ignored for GET/DELETE)
        output: Optional filename to save the response body to. When set, returns a short summary instead of the full body. Use this to save large responses for later processing without printing them.

    Returns:
        Status line + body text (or short summary if output= is set)
    """
    reason = _check_ssrf(url)
    if reason:
        return reason
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.request(method, url, headers=headers, content=body)
        if output:
            path = (SCRATCH_DIR / output).resolve()
            if not str(path).startswith(str(SCRATCH_DIR.resolve())):
                return "Error: output path traversal blocked"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(resp.text)
            size = len(resp.text)
            return f"Status: {resp.status_code} — saved {size} bytes"
        return f"Status: {resp.status_code}\n\n{resp.text}"
