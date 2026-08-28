import re
import time
import random
import asyncio
import httpx
from typing import Optional


PROXY_PATTERN = re.compile(
    r"^(?:(?P<type>http|https|socks4|socks5)://)?"
    r"(?:(?P<user>[^:@]+)(?::(?P<pass>[^@]*))?@)?"
    r"(?P<host>[^:@/\s]+)"
    r":(?P<port>\d+)"
    r"(?::(?P<extra_user>[^:@]+)(?::(?P<extra_pass>[^:@\s]+))?)?$"
)


def parse_proxy_format(text: str) -> dict | None:
    """Parse proxy strings in multiple formats."""
    text = text.strip()
    if not text:
        return None

    # Format: type://user:pass@host:port
    m = PROXY_PATTERN.match(text)
    if not m:
        return None

    host = m.group("host")
    port = m.group("port")
    ptype = (m.group("type") or "http").lower()
    user = m.group("user") or m.group("extra_user") or ""
    pwd = m.group("pass") or m.group("extra_pass") or ""

    proxy_url = f"{ptype}://"
    if user:
        proxy_url += f"{user}:{pwd}@" if pwd else f"{user}@"
    proxy_url += f"{host}:{port}"

    return {
        "type": ptype,
        "host": host,
        "port": int(port),
        "user": user,
        "pass": pwd,
        "proxy_url": proxy_url,
        "raw": text,
    }


def proxy_dict_to_url(p: dict) -> str:
    return p.get("proxy_url") or ""


def _get_test_endpoints() -> list[str]:
    """Return list of test endpoints to try in order."""
    return [
        "https://httpbin.org/ip",
        "https://api.ipify.org?format=json",
        "https://ipinfo.io/json",
        "https://ifconfig.me/ip",
        "https://api.myip.com",
        "http://httpbin.org/ip",
        "http://api.ipify.org?format=json",
        "http://ipinfo.io/json",
        "http://ifconfig.me/ip",
    ]


async def _test_with_client(proxy_url: str, endpoint: str, timeout: int) -> tuple[bool, float, str]:
    """Test proxy with a single endpoint using httpx (with SOCKS support if available)."""
    if not proxy_url:
        return False, 0.0, "empty proxy"
    
    start = time.time()
    try:
        # Check if it's a SOCKS proxy
        is_socks = proxy_url.startswith("socks4://") or proxy_url.startswith("socks5://")
        
        # Try to import httpx-socks for SOCKS support
        transport = None
        if is_socks:
            try:
                from httpx_socks import AsyncProxyTransport
                transport = AsyncProxyTransport.from_url(proxy_url)
            except ImportError:
                pass  # httpx-socks not available, will try without
        
        # For HTTP/HTTPS proxies, use the proxy parameter in the client
        # httpx 0.28+ uses 'proxy' parameter instead of 'proxies'
        if transport:
            async with httpx.AsyncClient(transport=transport, timeout=timeout) as client:
                r = await client.get(endpoint)
                if r.status_code == 200:
                    return True, (time.time() - start) * 1000, ""
                return False, (time.time() - start) * 1000, f"status {r.status_code}"
        else:
            # Use proxy parameter for HTTP/HTTPS proxies
            async with httpx.AsyncClient(proxy=proxy_url, timeout=timeout) as client:
                r = await client.get(endpoint)
                if r.status_code == 200:
                    return True, (time.time() - start) * 1000, ""
                return False, (time.time() - start) * 1000, f"status {r.status_code}"
    except Exception as e:
        error_msg = str(e)
        if not error_msg:
            error_msg = f"{type(e).__name__}: unknown error"
        return False, (time.time() - start) * 1000, error_msg[:100]


async def test_proxy(proxy_url: str, timeout: int = 15) -> tuple[bool, float, str]:
    """Test proxy with multiple endpoints for reliability. Returns (ok, latency_ms, error)."""
    if not proxy_url:
        return False, 0.0, "empty proxy"
    
    endpoints = _get_test_endpoints()
    last_error = ""
    
    for endpoint in endpoints:
        success, latency, error = await _test_with_client(proxy_url, endpoint, timeout)
        if success:
            return True, latency, f"OK via {endpoint}"
        last_error = f"{endpoint}: {error}"
    
    return False, 0.0, f"All endpoints failed. Last: {last_error}"


async def test_proxy_detailed(proxy_url: str, timeout: int = 15) -> dict:
    """Test proxy with all endpoints and return detailed results."""
    if not proxy_url:
        return {"success": False, "latency_ms": 0, "error": "empty proxy", "endpoint": None, "all_results": []}
    
    endpoints = _get_test_endpoints()
    all_results = []
    best_latency = float('inf')
    best_endpoint = None
    
    for endpoint in endpoints:
        success, latency, error = await _test_with_client(proxy_url, endpoint, timeout)
        all_results.append({
            "endpoint": endpoint,
            "success": success,
            "latency_ms": round(latency, 2) if success else 0,
            "error": error if not success else None
        })
        if success and latency < best_latency:
            best_latency = latency
            best_endpoint = endpoint
    
    if best_endpoint:
        return {
            "success": True,
            "latency_ms": round(best_latency, 2),
            "error": None,
            "endpoint": best_endpoint,
            "all_results": all_results
        }
    else:
        return {
            "success": False,
            "latency_ms": 0,
            "error": "All endpoints failed",
            "endpoint": None,
            "all_results": all_results
        }


async def bin_lookup(bin_num: str) -> dict:
    """Lookup BIN information. Falls back to defaults on failure."""
    info = {
        "bin": bin_num,
        "brand": "-",
        "type": "-",
        "level": "",
        "bank": "-",
        "country": "-",
        "flag": "",
        "scheme": "-",
    }
    endpoints = [
        f"https://lookup.binlist.net/{bin_num}",
        f"https://binlist.net/{bin_num}",
    ]
    headers = {"Accept-Version": "3"}
    for url in endpoints:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.get(url, headers=headers)
                if r.status_code != 200:
                    continue
                data = r.json()
                info["brand"] = (data.get("scheme") or data.get("brand") or "-").upper()
                info["type"] = (data.get("type") or "-").upper()
                info["level"] = (data.get("brand") or data.get("level") or "").upper()
                bank = data.get("bank") or {}
                info["bank"] = bank.get("name") or "-"
                country = data.get("country") or {}
                info["country"] = country.get("name") or "-"
                info["flag"] = country.get("emoji") or ""
                return info
        except Exception:
            continue

    # Fallback: use bin range heuristics
    brand_map = {
        "4": "VISA",
        "5": "MASTERCARD",
        "3": "AMEX",
        "6": "DISCOVER",
    }
    info["brand"] = brand_map.get(bin_num[0], "-")
    return info


CC_PATTERN = re.compile(
    r"(?P<number>\d{13,19})\s*[-|/\\:]\s*(?P<mm>\d{1,2})\s*[-|/\\:]\s*(?P<yy>\d{2,4})\s*[-|/\\:]\s*(?P<cvv>\d{3,4})"
)


def extract_cc(text: str) -> dict | None:
    """Extract card details from text."""
    m = CC_PATTERN.search(text)
    if not m:
        return None
    number = m.group("number")
    mm = m.group("mm").zfill(2)
    yy = m.group("yy")
    if len(yy) == 4:
        yy = yy[-2:]
    cvv = m.group("cvv")
    return {
        "number": number,
        "mm": mm,
        "yy": yy,
        "cvv": cvv,
        "cc": f"{number}|{mm}|{yy}|{cvv}",
    }


def close_session(session):
    """Safely close an httpx session."""
    try:
        if isinstance(session, httpx.AsyncClient):
            asyncio.create_task(session.aclose())
    except Exception:
        pass


def classify_gate_response(response: str | dict) -> tuple[str, str]:
    """Classify a gate response into (status, code).

    Status: charged, approved, declined, dead, error, 3ds
    """
    if isinstance(response, dict):
        text = " ".join(str(v) for v in response.values()).lower()
        raw = str(response)
    else:
        text = str(response).lower()
        raw = str(response)

    # Charged / success
    if any(x in text for x in ["charged", "order placed", "payment success", "success", "completed", "approved", "live", "cvv matched"]):
        if any(x in text for x in ["order placed", "charged", "payment success", "completed"]):
            return "charged", "ORDER_PLACED"
        return "approved", "LIVE"

    # 3DS / OTP
    if any(x in text for x in ["3ds", "3d secure", "otp", "authentication required", "verify", "challenge"]):
        return "3ds", "3DS_REQUIRED"

    # Insufficient funds / CVC issues (still approved/live in many checkers)
    if any(x in text for x in ["insufficient funds", "not enough funds", "05: do not honor", "do not honor"]):
        return "approved", "INSUFFICIENT_FUNDS"
    if any(x in text for x in ["incorrect cvc", "invalid cvc", "cvc_check fail", "security code", "cvv incorrect"]):
        return "approved", "INCORRECT_CVC"

    # Declined
    if any(x in text for x in ["declined", "rejected", "denied", "not approved", "card declined", "fraud", "risk"]):
        return "declined", "DECLINED"

    # Dead
    if any(x in text for x in ["dead", "invalid card", "incorrect number", "expired", "card number is invalid"]):
        return "dead", "DEAD"

    # Default error
    return "error", "ERROR"


def gate_is_charged(response: str | dict) -> bool:
    status, _ = classify_gate_response(response)
    return status == "charged"


def gate_is_approved(response: str | dict) -> bool:
    status, _ = classify_gate_response(response)
    return status in ("charged", "approved", "3ds")