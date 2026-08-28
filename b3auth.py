import random
import asyncio
import time


async def check(cc: str, proxy: dict | None = None) -> dict:
    """B3 Auth gate stub."""
    await asyncio.sleep(random.uniform(0.8, 2.0))
    outcomes = [
        {"status": "approved", "code": "LIVE", "amount": "$0.00"},
        {"status": "declined", "code": "DECLINED", "amount": "$0.00"},
        {"status": "dead", "code": "DEAD", "amount": "$0.00"},
    ]
    weights = [20, 60, 20]
    result = random.choices(outcomes, weights=weights, k=1)[0]
    return {"gate": "B3_AUTH", "cc": cc, "site": "b3gateway.com", **result}


def b3_check_card(cc: str, mm: str, yy: str, cvv: str, proxy_url: str | None = None) -> tuple:
    """Braintree auth gate stub (sync — runs inside CHECKER_POOL).

    Returns the (status, msg, code) 3-tuple bot.py expects.
    """
    time.sleep(random.uniform(1.0, 2.0))
    outcomes = [
        ("approved", "CVV Approved — Card Added", "cvv_approved"),
        ("approved", "Insufficient Funds",        "insufficient_funds"),
        ("ccn",      "CCN — Card Number Valid",   "ccn"),
        ("declined", "Card Declined",             "declined"),
        ("dead",     "Invalid Card",              "dead"),
        ("error",    "Proxy error",               "proxy_error"),
    ]
    weights = [15, 15, 8, 45, 12, 5]
    status, msg, code = random.choices(outcomes, weights=weights, k=1)[0]
    return status, msg, code
