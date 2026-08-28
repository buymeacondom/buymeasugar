import random


async def scan(urls: list[str], proxy: dict | None = None) -> list[dict]:
    """Gateway lookup scanner stub. Filters no-captcha/no-cloudflare."""
    results = []
    for url in urls[:20]:
        if random.random() < 0.3:
            results.append({
                "url": url,
                "gateway": random.choice(["Stripe", "Shopify", "WooCommerce", "Braintree"]),
                "captcha": False,
                "cloudflare": False,
                "status": "ok",
            })
    return results
