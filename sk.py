import random
import asyncio


async def check(sk: str, pk: str, cc: str, proxy: dict | None = None) -> dict:
    """Stripe SK checker stub."""
    await asyncio.sleep(random.uniform(1.0, 2.5))
    if not sk.startswith("sk_") or not pk.startswith("pk_"):
        return {"gate": "SK_CVV", "cc": cc, "status": "error", "code": "INVALID_SK", "amount": "$0.00"}
    outcomes = [
        {"status": "charged", "code": "CHARGED", "amount": "$5.00"},
        {"status": "approved", "code": "LIVE", "amount": "$0.00"},
        {"status": "declined", "code": "DECLINED", "amount": "$0.00"},
        {"status": "dead", "code": "DEAD", "amount": "$0.00"},
    ]
    weights = [5, 15, 55, 25]
    result = random.choices(outcomes, weights=weights, k=1)[0]
    return {"gate": "SK_CVV", "cc": cc, **result}


async def validate_key(sk: str, pk: str, proxy: dict | None = None) -> tuple[bool, str]:
    """Validate SK + PK pair."""
    await asyncio.sleep(0.5)
    if sk.startswith("sk_") and pk.startswith("pk_"):
        return True, "Key valid (stub)"
    return False, "Invalid SK/PK format"
