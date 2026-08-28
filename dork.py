"""Search URL scraper for /dork.

Uses the DuckDuckGo HTML endpoint (html.duckduckgo.com) via POST — no API key
needed.  Fetches result pages and extracts external result URLs (ads and
internal links are filtered out).  Generic public-web search scraping.
"""
import asyncio
import re
import httpx

SEARCH_URL = "https://html.duckduckgo.com/html/"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

_SKIP_FRAGMENTS = (
    "duckduckgo.com", "ddg.co", "/y.js?", "y.js?",
    "bing.com/aclick", "javascript:", "mailto:",
)


def _extract_urls(html: str) -> list[str]:
    """Pull result URLs out of a DuckDuckGo HTML result page.

    Result anchors look like: <a rel="nofollow" class="result__a" href="...">
    (class attribute comes BEFORE href).
    """
    urls = []
    for m in re.finditer(r'class="result__a"[^>]*href="([^"]+)"', html):
        u = m.group(1)
        low = u.lower()
        if any(f in low for f in _SKIP_FRAGMENTS):
            continue
        if u not in urls:
            urls.append(u)
    return urls


def _next_page_value(html: str) -> str | None:
    """Extract the hidden 's' value DDG uses for the next result page."""
    # <form ...> ... <input type="hidden" name="s" value="30"> ... </form>
    m = re.search(r'name="s"\s+value="(\d+)"', html)
    if not m:
        m = re.search(r'value="(\d+)"\s+name="s"', html)
    return m.group(1) if m else None


async def scrape_dork(
    query: str,
    proxy: str | None = None,
    on_progress=None,
    max_pages: int = 10,
    delay: float = 1.0,
) -> list[str]:
    """Scrape DuckDuckGo HTML for a query, returning deduplicated URLs.

    Walks up to ``max_pages`` result pages.  Calls ``on_progress(page,
    total_so_far)`` after each page.  Optional HTTP(S) proxy string
    (``host:port`` or ``user:pass@host:port``).
    """
    results: list[str] = []
    kwargs = {"headers": HEADERS, "timeout": httpx.Timeout(25.0), "follow_redirects": True}
    if proxy:
        kwargs["proxy"] = proxy

    try:
        async with httpx.AsyncClient(**kwargs) as client:
            s = ""
            for page in range(max_pages):
                try:
                    data = {"q": query}
                    if s:
                        data["s"] = s
                    resp = await client.post(SEARCH_URL, data=data)
                    if resp.status_code != 200:
                        break
                    found = _extract_urls(resp.text)
                    added = [u for u in found if u not in results]
                    results.extend(added)
                    if on_progress:
                        await on_progress(page + 1, len(results))
                    if not added:
                        break
                    nxt = _next_page_value(resp.text)
                    if not nxt or nxt == s:
                        break
                    s = nxt
                    await asyncio.sleep(delay)
                except Exception:
                    break
    except Exception:
        pass
    return results


async def scrape(query: str, limit: int = 20) -> list[str]:
    """Scrape a query (limit = max results returned)."""
    return (await scrape_dork(query))[:limit]


async def search(query: str, limit: int = 20) -> list[str]:
    """Alias of scrape (spec-expected entry point)."""
    return await scrape(query, limit)
