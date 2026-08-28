import random
import time


def check(cc: str, mm: str, yy: str, cvv: str, url: str, proxy_list: list | None = None) -> dict:
    """Stripe $1 gate stub (sync — runs inside CHECKER_POOL, used by /addsite).

    Returns a dict; bot.py stringifies it to display the response.
    """
    time.sleep(random.uniform(0.8, 2.0))
    outcomes = [
        {"status": "charged", "code": "ORDER_PLACED", "amount": "$1.00"},
        {"status": "approved", "code": "LIVE", "amount": "$0.00"},
        {"status": "approved", "code": "INCORRECT_CVC", "amount": "$0.00"},
        {"status": "declined", "code": "DECLINED", "amount": "$0.00"},
        {"status": "dead", "code": "DEAD", "amount": "$0.00"},
    ]
    weights = [5, 15, 15, 40, 25]
    result = random.choices(outcomes, weights=weights, k=1)[0]
    return {"gate": "STRIPE_1DOLLAR", "cc": f"{cc}|{mm}|{yy}|{cvv}", "site": url, **result}


def check_card_str(cc_str: str, proxy_url: str | None = None) -> tuple:
    """Stripe $1 gate stub (sync — runs inside CHECKER_POOL).

    Returns the (status, msg, code) 3-tuple bot.py expects (_usd1_run_check).
    """
    time.sleep(random.uniform(0.8, 2.0))
    outcomes = [
        ("charged",  "ORDER_PLACED",       "ORDER_PLACED"),
        ("approved", "LIVE",               "LIVE"),
        ("approved", "Insufficient Funds", "insufficient_funds"),
        ("approved", "Incorrect CVC",      "incorrect_cvc"),
        ("declined", "Card Declined",      "declined"),
        ("dead",     "DEAD",               "DEAD"),
        ("error",    "Proxy error",        "proxy_error"),
    ]
    weights = [5, 15, 12, 15, 40, 10, 3]
    status, msg, code = random.choices(outcomes, weights=weights, k=1)[0]
    return status, msg, code
