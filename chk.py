import random
import asyncio
import time


async def check(cc: str, proxy: dict | None = None) -> dict:
    """Stripe Auth CHK gate stub."""
    await asyncio.sleep(random.uniform(0.8, 2.0))
    outcomes = [
        {"status": "charged", "code": "ORDER_PLACED", "amount": "$5.00"},
        {"status": "approved", "code": "LIVE", "amount": "$0.00"},
        {"status": "approved", "code": "INCORRECT_CVC", "amount": "$0.00"},
        {"status": "declined", "code": "DECLINED", "amount": "$0.00"},
        {"status": "dead", "code": "DEAD", "amount": "$0.00"},
    ]
    weights = [2, 10, 15, 58, 15]
    result = random.choices(outcomes, weights=weights, k=1)[0]
    return {"gate": "STRIPE_AUTH", "cc": cc, "site": "stripe.com", **result}


def check_card_str(cc_str: str, max_retries: int = 4) -> tuple:
    """Stripe auth gate stub (sync — runs inside CHECKER_POOL).

    Returns the (status, msg, code, site_url) 4-tuple bot.py expects.
    """
    time.sleep(random.uniform(1.0, 2.5))
    outcomes = [
        ("approved", "CVV Approved — Card Added",  "cvv_approved",      "stripe.com"),
        ("approved", "Insufficient Funds",         "insufficient_funds","stripe.com"),
        ("approved", "Incorrect CVC",              "incorrect_cvc",     "stripe.com"),
        ("ccn",      "CCN — Incorrect CVC",        "ccn",               "stripe.com"),
        ("declined", "Card Declined",              "declined",          "stripe.com"),
        ("dead",     "Invalid Card Number",        "dead",              "stripe.com"),
        ("error",    "Connection error",           "connection_error",  ""),
    ]
    weights = [15, 12, 15, 8, 40, 7, 3]
    status, msg, code, site_url = random.choices(outcomes, weights=weights, k=1)[0]
    return status, msg, code, site_url
