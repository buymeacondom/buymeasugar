import random
import asyncio
import time


async def check(cc: str, proxy: dict | None = None, site: str | None = None) -> dict:
    """Razorpay RZ gate stub."""
    await asyncio.sleep(random.uniform(0.8, 2.0))
    outcomes = [
        {"status": "charged", "code": "ORDER_PLACED", "site": site or "razorpay-store.com", "amount": "₹399"},
        {"status": "approved", "code": "LIVE", "site": site or "razorpay-store.com", "amount": "₹0"},
        {"status": "approved", "code": "INSUFFICIENT_FUNDS", "site": site or "razorpay-store.com", "amount": "₹0"},
        {"status": "declined", "code": "DECLINED", "site": site or "razorpay-store.com", "amount": "₹0"},
        {"status": "dead", "code": "DEAD", "site": site or "razorpay-store.com", "amount": "₹0"},
    ]
    weights = [2, 8, 12, 60, 18]
    result = random.choices(outcomes, weights=weights, k=1)[0]
    return {"gate": "RAZORPAY", "cc": cc, **result}


def normalize_pages_url(url: str) -> str:
    """Normalize a Razorpay checkout page URL (sync)."""
    url = (url or "").strip()
    if not url:
        return url
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url.rstrip("/")


def charge_payment_page_card(site_url: str, cc: str, mm: str, yy: str, cvv: str,
                             proxy_url: str | None = None, timeout: float = 40.0) -> tuple:
    """Razorpay payment-page gate stub (sync — runs inside CHECKER_POOL).

    Returns the (status, msg, code, dbg) 4-tuple bot.py expects.
    """
    time.sleep(random.uniform(1.0, 2.5))
    outcomes = [
        ("charged",  "ORDER_PLACED",          "ORDER_PLACED",          {}),
        ("approved", "LIVE",                  "LIVE",                  {}),
        ("approved", "INSUFFICIENT_FUNDS",    "INSUFFICIENT_FUNDS",    {}),
        ("declined", "CARD_DECLINED",         "DECLINED",              {}),
        ("dead",     "DEAD",                  "DEAD",                  {}),
        ("error",    "Page fetch failed",     "page_fetch_failed",     {}),
    ]
    weights = [2, 8, 12, 55, 18, 5]
    status, msg, code, dbg = random.choices(outcomes, weights=weights, k=1)[0]
    return status, msg, code, dbg
