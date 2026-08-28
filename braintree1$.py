import random
import time


def check(cc: str, mm: str, yy: str, cvv: str, url: str, proxy_list: list | None = None) -> dict:
    """Braintree auth gate stub (sync — runs inside CHECKER_POOL, used by /addsite).

    Returns a dict; bot.py stringifies it to display the response.
    """
    time.sleep(random.uniform(0.8, 2.0))
    outcomes = [
        {"status": "approved", "code": "LIVE", "amount": "$0.00"},
        {"status": "approved", "code": "INSUFFICIENT_FUNDS", "amount": "$0.00"},
        {"status": "declined", "code": "DECLINED", "amount": "$0.00"},
        {"status": "dead", "code": "DEAD", "amount": "$0.00"},
    ]
    weights = [15, 15, 50, 20]
    result = random.choices(outcomes, weights=weights, k=1)[0]
    return {"gate": "BRAINTREE_AUTH", "cc": f"{cc}|{mm}|{yy}|{cvv}", "site": url, **result}


def check_card_str(cc_str: str, proxy_url: str | None = None) -> tuple:
    """Braintree auth gate stub (sync). Returns (status, msg, code) 3-tuple."""
    time.sleep(random.uniform(0.8, 2.0))
    outcomes = [
        ("approved", "CVV Approved — Card Added", "cvv_approved"),
        ("approved", "Insufficient Funds",        "insufficient_funds"),
        ("declined", "Card Declined",             "declined"),
        ("dead",     "DEAD",                      "dead"),
        ("error",    "Proxy error",               "proxy_error"),
    ]
    weights = [15, 15, 50, 15, 5]
    status, msg, code = random.choices(outcomes, weights=weights, k=1)[0]
    return status, msg, code
