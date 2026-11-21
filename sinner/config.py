import os

from dotenv import load_dotenv


load_dotenv()


def _ids(name: str) -> set[int]:
    raw = os.getenv(name, "").replace(" ", "")
    return {int(x) for x in raw.split(",") if x.isdigit()}

def _bool(name: str, default: str) -> bool:
    return os.getenv(name, default).lower() in ("1", "true", "yes", "oui")


TOKEN = os.getenv("DISCORD_TOKEN")
HONEYPOT_ID = int(os.getenv("HONEYPOT_CHANNEL_ID", "0"))
ADMIN_ID = int(os.getenv("ADMIN_CHANNEL_ID", "0"))

WHITELIST_USERS = _ids("WHITELIST_USER_IDS")
WHITELIST_ROLES = _ids("WHITELIST_ROLE_IDS")

DELETE_HISTORY = min(int(os.getenv("DELETE_HISTORY_SECONDS", "3600")), 604800)

AUTO_WARNING = _bool("AUTO_WARNING", "true")


def validate() -> None:
    if not TOKEN or not HONEYPOT_ID or not ADMIN_ID:
        raise SystemExit(
            "Configure DISCORD_TOKEN, HONEYPOT_CHANNEL_ID and ADMIN_CHANNEL_ID in the .env file"
        )
