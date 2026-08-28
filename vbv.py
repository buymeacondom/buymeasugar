import random
import asyncio
import time


async def check(cc: str, proxy: dict | None = None) -> dict:
    """Braintree VBV gate stub."""
    await asyncio.sleep(random.uniform(0.8, 2.0))
    outcomes = [
        {"status": "3ds", "code": "3DS_REQUIRED", "amount": "$0.00"},
        {"status": "approved", "code": "LIVE", "amount": "$0.00"},
        {"status": "declined", "code": "DECLINED", "amount": "$0.00"},
        {"status": "dead", "code": "DEAD", "amount": "$0.00"},
    ]
    weights = [20, 15, 45, 20]
    result = random.choices(outcomes, weights=weights, k=1)[0]
    return {"gate": "BRAINTREE_VBV", "cc": cc, "site": "braintree.com", **result}


def check_card_str(cc_str: str) -> tuple:
    """Braintree VBV gate stub (sync — runs inside CHECKER_POOL).

    Returns the (api_status, message, code, dbg) 4-tuple bot.py expects.
    """
    time.sleep(random.uniform(1.0, 2.5))
    outcomes = [
        ("passed",        "2D passed",      "passed",          {}),
        ("challenge_3d",  "3D challenge",   "challenge_3d",    {}),
        ("failed",        "Card declined",  "declined",        {}),
        ("failed",        "Invalid card",   "dead",            {}),
        ("error",         "Connection error", "connection_error", {}),
    ]
    weights = [25, 20, 40, 10, 5]
    api_status, message, code, dbg = random.choices(outcomes, weights=weights, k=1)[0]
    return api_status, message, code, dbg
