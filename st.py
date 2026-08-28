import random
import asyncio
import time


async def check(cc: str, proxy: dict | None = None, site: str | None = None) -> dict:
    """WooCommerce ST gate stub."""
    await asyncio.sleep(random.uniform(0.8, 2.0))
    outcomes = [
        {"status": "charged", "code": "ORDER_PLACED", "site": site or "woocommerce-store.com", "amount": "$5.00"},
        {"status": "approved", "code": "LIVE", "site": site or "woocommerce-store.com", "amount": "$0.00"},
        {"status": "approved", "code": "INSUFFICIENT_FUNDS", "site": site or "woocommerce-store.com", "amount": "$0.00"},
        {"status": "declined", "code": "DECLINED", "site": site or "woocommerce-store.com", "amount": "$0.00"},
        {"status": "dead", "code": "DEAD", "site": site or "woocommerce-store.com", "amount": "$0.00"},
    ]
    weights = [2, 8, 12, 60, 18]
    result = random.choices(outcomes, weights=weights, k=1)[0]
    return {"gate": "WOOCOMMERCE_ST", "cc": cc, **result}


def VW(cc: str, site_url: str | None = None, proxy_url: str | None = None,
       proxy_list: list | None = None) -> str:
    """WooCommerce Stripe gate stub (sync — runs inside CHECKER_POOL).

    Returns a raw response string; bot.py parses it with _st_status_line().
    """
    time.sleep(random.uniform(1.0, 3.0))
    outcomes = [
        "Card added",
        "3D requires_action",
        "Insufficient Funds",
        "Incorrect CVC",
        "Card was declined",
        "Card Expired",
        "Payment error: do not honor",
    ]
    weights = [3, 12, 12, 15, 45, 8, 5]
    return random.choices(outcomes, weights=weights, k=1)[0]
