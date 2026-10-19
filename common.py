"""Shared helpers: env loading, Supabase REST access, Telegram notifications."""
import os

import requests

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # python-dotenv optional
    pass

DEFAULT_SUPABASE_URL = "https://ikjqsaosfnwanhhclgut.supabase.co"
DEFAULT_SITE_URL = "https://ahmed-istiaq.github.io/area139/"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

# Stable ordering matters when a table has more than one page of rows.
TABLE_ORDER = {"posts": "id", "post_categories": "id"}


def supabase_url() -> str:
    return os.getenv("SUPABASE_URL", DEFAULT_SUPABASE_URL).rstrip("/")


def has_service_key() -> bool:
    return bool(os.getenv("SUPABASE_SERVICE_KEY"))


def supabase_key() -> str:
    key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")
    if not key:
        raise RuntimeError(
            "SUPABASE_KEY (or SUPABASE_SERVICE_KEY for backups) is not set."
        )
    return key


def _auth_headers(key: str) -> dict:
    headers = {"apikey": key}
    if key.startswith("eyJ"):  # legacy JWT-style keys also go in Authorization
        headers["Authorization"] = f"Bearer {key}"
    return headers


def fetch_table(table: str, page_size: int = 1000) -> list[dict]:
    """Fetch every row of a table through Supabase's REST API (paginated)."""
    base = f"{supabase_url()}/rest/v1/{table}"
    headers = {**_auth_headers(supabase_key()), "Range-Unit": "items"}
    order = TABLE_ORDER.get(table)
    rows: list[dict] = []
    start = 0
    while True:
        params = {"select": "*"}
        if order:
            params["order"] = order
        headers["Range"] = f"{start}-{start + page_size - 1}"
        r = requests.get(base, headers=headers, params=params, timeout=30)
        if r.status_code == 400 and order:  # order column doesn't exist
            order = None
            continue
        if r.status_code not in (200, 206):
            raise RuntimeError(f"{table}: HTTP {r.status_code} - {r.text[:200]}")
        batch = r.json()
        rows.extend(batch)
        if len(batch) < page_size:
            return rows
        start += page_size


def telegram_notify(text: str) -> bool:
    token, chat = os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")
    if not (token and chat):
        return False
    r = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data={"chat_id": chat, "text": text[:4000], "disable_web_page_preview": True},
        timeout=20,
    )
    return r.ok


def telegram_send_file(path, caption: str = "") -> bool:
    token, chat = os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")
    if not (token and chat):
        return False
    with open(path, "rb") as fh:
        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendDocument",
            data={"chat_id": chat, "caption": caption[:1000]},
            files={"document": fh},
            timeout=120,
        )
    return r.ok
