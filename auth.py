import json
import os
import random
import string
import time
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()

OWNER_FILE = BASE_DIR / "owner.json"
CONFIG_FILE = BASE_DIR / "config.json"
ADMINS_FILE = BASE_DIR / "admins.json"
USERS_FILE = BASE_DIR / "users.json"
KEYS_FILE = BASE_DIR / "keys.json"
CREDITS_FILE = BASE_DIR / "credits.json"
BANNED_FILE = BASE_DIR / "banned.json"
CHARGED_FILE = BASE_DIR / "charged_cc.json"

LIMITS = {
    "free": 300,
    "premium": 8000,
    "admin": 15000,
    "owner": 30000,
}


def _load_json(path: Path, default):
    try:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return default


def _save_json(path: Path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# Load owner
owner_data = _load_json(OWNER_FILE, {"id": None})
OWNER_ID = int(owner_data.get("id", 0)) if owner_data.get("id") else 0

# Load config
config_data = _load_json(CONFIG_FILE, {"approved_group_id": None, "monitor_group_id": None})
APPROVED_GROUP_ID = config_data.get("approved_group_id")
MONITOR_GROUP_ID = config_data.get("monitor_group_id")


class UserAuth:
    def __init__(self):
        self.admins = _load_json(ADMINS_FILE, [])
        self.users = _load_json(USERS_FILE, {})
        self.keys = _load_json(KEYS_FILE, {})
        self.credits = _load_json(CREDITS_FILE, {})
        self.banned = set(_load_json(BANNED_FILE, []))
        self._ensure_files()

    def _ensure_files(self):
        for path, default in [
            (ADMINS_FILE, []),
            (USERS_FILE, {}),
            (KEYS_FILE, {}),
            (CREDITS_FILE, {}),
            (BANNED_FILE, []),
            (CHARGED_FILE, {}),
        ]:
            if not path.exists():
                _save_json(path, default)

    def _persist(self, attr: str):
        mapping = {
            "admins": ADMINS_FILE,
            "users": USERS_FILE,
            "keys": KEYS_FILE,
            "credits": CREDITS_FILE,
        }
        if attr in mapping:
            _save_json(mapping[attr], getattr(self, attr))
        elif attr == "banned":
            _save_json(BANNED_FILE, list(self.banned))

    def get_user_role(self, user_id: int) -> str:
        uid = str(user_id)
        if user_id == OWNER_ID:
            return "owner"
        if user_id in self.admins:
            return "admin"
        user = self.users.get(uid, {})
        if user.get("role") == "premium":
            expires = user.get("expires")
            if expires:
                try:
                    if datetime.utcnow() > datetime.fromisoformat(expires):
                        user["role"] = "free"
                        self._persist("users")
                        return "free"
                except Exception:
                    pass
            return "premium"
        return "free"

    # Alias used by bot.py
    get_role = get_user_role

    def is_owner(self, user_id: int) -> bool:
        return user_id == OWNER_ID

    def is_admin(self, user_id: int) -> bool:
        return self.is_owner(user_id) or user_id in self.admins

    def is_premium(self, user_id: int) -> bool:
        return self.get_user_role(user_id) == "premium"

    def has_premium_access(self, user_id: int) -> bool:
        return self.get_user_role(user_id) in ("premium", "admin", "owner")

    def save_user(self, user_id: int, username: str | None, full_name: str | None):
        uid = str(user_id)
        if uid not in self.users:
            self.users[uid] = {"role": "free"}
        self.users[uid]["username"] = username or self.users[uid].get("username", "")
        self.users[uid]["full_name"] = full_name or self.users[uid].get("full_name", "")
        self._persist("users")

    def get_limit(self, user_id: int) -> int:
        role = self.get_user_role(user_id)
        return LIMITS.get(role, LIMITS["free"])

    def get_credits(self, user_id: int) -> int:
        return int(self.credits.get(str(user_id), 0))

    def add_credits(self, user_id: int, amount: int):
        uid = str(user_id)
        self.credits[uid] = self.credits.get(uid, 0) + amount
        self._persist("credits")

    def deduct_credit(self, user_id: int) -> bool:
        uid = str(user_id)
        val = self.credits.get(uid, 0)
        if val > 0:
            self.credits[uid] = val - 1
            self._persist("credits")
            return True
        return False

    def get_total_limit(self, user_id: int) -> int:
        return self.get_limit(user_id) + self.get_credits(user_id)

    def add_admin(self, user_id: int) -> bool:
        if user_id in self.admins:
            return False
        self.admins.append(user_id)
        self._persist("admins")
        return True

    def remove_admin(self, user_id: int) -> bool:
        if user_id not in self.admins:
            return False
        self.admins.remove(user_id)
        self._persist("admins")
        return True

    def auth_user(self, user_id: int, days: int = 0):
        uid = str(user_id)
        if uid not in self.users:
            self.users[uid] = {"role": "premium"}
        else:
            self.users[uid]["role"] = "premium"
        if days > 0:
            self.users[uid]["expires"] = (datetime.utcnow() + timedelta(days=days)).isoformat()
        else:
            self.users[uid]["expires"] = None
        self.users[uid]["premium_since"] = datetime.utcnow().isoformat()
        self._persist("users")

    def unauth_user(self, user_id: int) -> bool:
        uid = str(user_id)
        if uid not in self.users or self.users[uid].get("role") != "premium":
            return False
        self.users[uid]["role"] = "free"
        self.users[uid]["expires"] = None
        self._persist("users")
        return True

    def ban_user(self, user_id: int):
        self.banned.add(user_id)
        self._persist("banned")

    def unban_user(self, user_id: int):
        if user_id in self.banned:
            self.banned.remove(user_id)
            self._persist("banned")

    def is_banned(self, user_id: int) -> bool:
        return user_id in self.banned

    def get_premium_expiry(self, user_id: int) -> str | None:
        uid = str(user_id)
        user = self.users.get(uid, {})
        if user.get("role") == "premium":
            return user.get("expires")
        return None

    def generate_key(self, key_type: str, max_users: int, days: int = 0, credits: int = 0) -> str:
        prefix = {"pkey": "goon-P", "ckey": "goon-C"}.get(key_type, "goon")
        rand = "".join(random.choices(string.ascii_uppercase + string.digits, k=12))
        key = f"{prefix}-{rand}"
        self.keys[key] = {
            "type": key_type,
            "max_users": max_users,
            "used_by": [],
            "days": days,
            "credits": credits,
        }
        self._persist("keys")
        return key

    def generate_keys(self, max_users: int, days: int = 0, credits: int = 0, created_by: int = 0) -> list[str]:
        """Generate multiple keys (wrapper for /key command). Returns list of keys."""
        # For backward compatibility, generate a single key
        # Uses generate_key with pkey type
        key = self.generate_key("pkey", max_users, days, credits)
        return [key]

    def redeem_key(self, user_id: int, key: str) -> tuple[bool, str]:
        uid = str(user_id)
        entry = self.keys.get(key)
        if not entry:
            return False, "Invalid key"
        if uid in entry["used_by"]:
            return False, "Key already used by you"
        if len(entry["used_by"]) >= entry["max_users"]:
            return False, "Key usage limit reached"

        key_type = entry.get("type", "pkey")
        days = entry.get("days", 0)
        credits = entry.get("credits", 0)

        if key_type == "pkey":
            self.auth_user(user_id, days)
            if credits > 0:
                self.add_credits(user_id, credits)
            msg = f"Premium activated"
            if days > 0:
                msg += f" for {days} days"
            else:
                msg += " (lifetime)"
            if credits > 0:
                msg += f" + {credits} credits"
        elif key_type == "ckey":
            self.add_credits(user_id, credits)
            msg = f"Added {credits} credits"
        else:
            return False, "Unknown key type"

        entry["used_by"].append(uid)
        self._persist("keys")
        return True, msg

    def get_all_user_ids(self) -> list:
        return [int(k) for k in self.users.keys()]

    def save_charged_cc(self, user_id: int, cc_str: str):
        data = _load_json(CHARGED_FILE, {})
        uid = str(user_id)
        if uid not in data:
            data[uid] = []
        data[uid].append({"cc": cc_str, "time": datetime.utcnow().isoformat()})
        _save_json(CHARGED_FILE, data)

    def set_nopecha_key(self, user_id: int, key: str):
        uid = str(user_id)
        self.users.setdefault(uid, {})["nopecha"] = key
        self._persist("users")

    def get_nopecha_key(self, user_id: int) -> str:
        uid = str(user_id)
        return self.users.get(uid, {}).get("nopecha", "")


# Module-level singleton
user_auth = UserAuth()


# Module-level wrappers (required by spec + used by bot.py)
def is_owner(user_id: int) -> bool:
    return user_auth.is_owner(user_id)


def is_admin(user_id: int) -> bool:
    return user_auth.is_admin(user_id)


def has_premium_access(user_id: int, chat_id: int | None = None) -> bool:
    # chat_id accepted for call-site compatibility (ignored)
    return user_auth.has_premium_access(user_id)


def save_user(user_id: int, username: str | None = None, full_name: str | None = None):
    return user_auth.save_user(user_id, username, full_name)


def get_user_role(user_id: int) -> str:
    return user_auth.get_user_role(user_id)


def get_role(user_id: int) -> str:
    return user_auth.get_user_role(user_id)


def get_premium_expiry(user_id: int) -> str | None:
    return user_auth.get_premium_expiry(user_id)


def get_all_user_ids() -> list:
    return user_auth.get_all_user_ids()


def add_admin(user_id: int) -> bool:
    return user_auth.add_admin(user_id)


def remove_admin(user_id: int) -> bool:
    return user_auth.remove_admin(user_id)


def auth_user(user_id: int, days: int = 0):
    return user_auth.auth_user(user_id, days)


def unauth_user(user_id: int) -> bool:
    return user_auth.unauth_user(user_id)


def generate_key(key_type: str, max_users: int, days: int = 0, credits: int = 0) -> str:
    return user_auth.generate_key(key_type, max_users, days, credits)


def generate_keys(max_users: int, days: int = 0, credits: int = 0, created_by: int = 0) -> list[str]:
    """Module-level wrapper for UserAuth.generate_keys (used by /key)."""
    return user_auth.generate_keys(max_users, days, credits, created_by)


def redeem_key(user_id: int, key: str) -> tuple[bool, str]:
    return user_auth.redeem_key(user_id, key)


def is_premium(user_id: int) -> bool:
    return user_auth.is_premium(user_id)


def save_charged_cc(cc_str: str, user_id: int, full_name: str = "", gate: str = "", price: str = ""):
    # All bot.py call sites pass (cc_str, user_id, full_name, gate, price)
    return user_auth.save_charged_cc(user_id, cc_str)


def load_admins() -> list:
    return list(user_auth.admins)


def set_nopecha_key(user_id: int, key: str):
    return user_auth.set_nopecha_key(user_id, key)


def get_nopecha_key(user_id: int) -> str:
    return user_auth.get_nopecha_key(user_id)


def ban_user(user_id: int):
    return user_auth.ban_user(user_id)


def unban_user(user_id: int):
    return user_auth.unban_user(user_id)


def is_banned(user_id: int) -> bool:
    return user_auth.is_banned(user_id)


def get_limit(user_id: int) -> int:
    return user_auth.get_limit(user_id)


def get_cc_limit(user_id: int) -> int:
    return user_auth.get_limit(user_id)


def get_credits(user_id: int) -> int:
    return user_auth.get_credits(user_id)


def add_credits(user_id: int, amount: int):
    return user_auth.add_credits(user_id, amount)
