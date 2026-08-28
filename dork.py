import random


async def scrape(query: str, limit: int = 20) -> list[str]:
    """Brave URL scraper stub."""
    return [f"https://example-site-{i}.com" for i in range(min(limit, 20))]


async def scrape_dork(query: str, proxy: str | None = None, on_progress=None) -> list[str]:
    """Brave Search URL scraper stub for /dork (bot-compatible entry point)."""
    results = [f"https://example-site-{i}.com" for i in range(min(len(query), 20))]
    if on_progress:
        await on_progress(1, len(results))
    return results


async def search(query: str, limit: int = 20) -> list[str]:
    """Alias of scrape (spec-expected entry point)."""
    return await scrape(query, limit)
