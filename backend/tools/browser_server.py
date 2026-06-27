import os
import asyncio
from mcp.server.fastmcp import FastMCP
from playwright.async_api import async_playwright, Playwright

mcp = FastMCP("Playwright Browser")

_pw: Playwright | None = None
_browser = None
_page = None


async def get_page():
    global _pw, _browser, _page
    if _page is None:
        if _pw is None:
            _pw = await async_playwright().start()
        if _browser is None:
            headless = os.getenv("BROWSER_HEADLESS", "false").lower() in ("1", "true", "yes")
            _browser = await _pw.firefox.launch(headless=headless)
        _page = await _browser.new_page()
    return _page


@mcp.tool()
async def browser_navigate(url: str) -> str:
    """Navigate to a URL."""
    page = await get_page()
    await page.goto(url, wait_until="domcontentloaded")
    return f"Navigated to {page.url}\nTitle: {await page.title()}"


@mcp.tool()
async def browser_snapshot() -> str:
    """Get the current page state: URL, title, and visible text content."""
    page = await get_page()
    url = page.url
    title = await page.title()
    text = await page.inner_text("body")
    return f"URL: {url}\nTitle: {title}\n\n{text.strip()}"


@mcp.tool()
async def browser_click(selector: str) -> str:
    """Click an element identified by a CSS selector."""
    page = await get_page()
    await page.click(selector)
    return f"Clicked {selector}"


@mcp.tool()
async def browser_type(selector: str, text: str) -> str:
    """Type text into an element identified by a CSS selector."""
    page = await get_page()
    await page.fill(selector, text)
    return f"Typed into {selector}"


@mcp.tool()
async def browser_fill_form(fields: dict) -> str:
    """Fill multiple form fields at once. Provide a dict mapping CSS selectors to values."""
    page = await get_page()
    for selector, value in fields.items():
        await page.fill(selector, value)
    return f"Filled {len(fields)} form fields"


@mcp.tool()
async def browser_evaluate(script: str) -> str:
    """Run JavaScript in the browser page and return the result."""
    page = await get_page()
    result = await page.evaluate(script)
    return str(result)


@mcp.tool()
async def browser_close() -> str:
    """Close the current browser page."""
    global _page
    if _page:
        await _page.close()
        _page = None
    return "Page closed"


@mcp.tool()
async def browser_hover(selector: str) -> str:
    """Hover over an element identified by a CSS selector."""
    page = await get_page()
    await page.hover(selector)
    return f"Hovered {selector}"


@mcp.tool()
async def browser_press_key(key: str) -> str:
    """Press a keyboard key (e.g. ArrowDown, Enter, Escape, Tab)."""
    page = await get_page()
    await page.press("body", key)
    return f"Pressed {key}"


@mcp.tool()
async def browser_resize(width: int, height: int) -> str:
    """Resize the browser viewport."""
    page = await get_page()
    await page.set_viewport_size({"width": width, "height": height})
    return f"Viewport set to {width}x{height}"


@mcp.tool()
async def browser_take_screenshot() -> str:
    """Take a screenshot and return it as a base64-encoded PNG."""
    page = await get_page()
    b64 = await page.screenshot(type="png", full_page=False)
    import base64
    return base64.b64encode(b64).decode()


@mcp.tool()
async def browser_navigate_back() -> str:
    """Go back to the previous page."""
    page = await get_page()
    await page.go_back()
    return f"Back to {page.url}"


@mcp.tool()
async def browser_get_text(selector: str) -> str:
    """Get the text content of an element identified by a CSS selector."""
    page = await get_page()
    text = await page.inner_text(selector)
    return text


@mcp.tool()
async def browser_select_option(selector: str, values: list[str]) -> str:
    """Select option(s) in a <select> element by their values."""
    page = await get_page()
    await page.select_option(selector, values)
    return f"Selected {values} in {selector}"


if __name__ == "__main__":
    mcp.run()
