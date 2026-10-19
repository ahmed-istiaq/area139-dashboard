#!/usr/bin/env python3
"""Backup Supabase tables of Area 139 into one timestamped .zip (one JSON per table).

Usage:
    python backup.py                 # -> backups/area139-backup-YYYY-MM-DD_HHMM.zip
    python backup.py --telegram      # also send the zip to your Telegram chat
    python backup.py --keep 12       # keep only the newest 12 local zips

Use SUPABASE_SERVICE_KEY so Row Level Security doesn't hide drafts/private rows.
"""
import argparse
import json
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from common import has_service_key, fetch_table, supabase_url, telegram_send_file

TABLES = [
    "posts",
    "post_categories",
    "category_order",
    "static_post_order",
    "static_post_overrides",
]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="backups")
    ap.add_argument("--keep", type=int, default=0, help="keep newest N local zips (0 = keep all)")
    ap.add_argument("--telegram", action="store_true", help="send zip to TELEGRAM_CHAT_ID")
    ap.add_argument("--include-admin", action="store_true", help="also back up admin_users (sensitive!)")
    a = ap.parse_args()

    tables = TABLES + (["admin_users"] if a.include_admin else [])
    if not has_service_key():
        print("WARNING: SUPABASE_SERVICE_KEY is not set - Row Level Security may hide some rows from the backup.")

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M")
    zip_path = out / f"area139-backup-{stamp}.zip"

    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "supabase_url": supabase_url(),
        "rows": {},
    }
    errors = []

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for t in tables:
            try:
                rows = fetch_table(t)
                z.writestr(f"{t}.json", json.dumps(rows, ensure_ascii=False, indent=2))
                manifest["rows"][t] = len(rows)
                print(f"  {t}: {len(rows)} rows")
            except Exception as e:
                errors.append(f"{t}: {e}")
                print(f"  {t}: FAILED - {e}")
        if manifest["rows"].get("posts") == 0:
            errors.append("posts table returned 0 rows - suspicious (wrong key or RLS?)")
        manifest["errors"] = errors
        z.writestr("manifest.json", json.dumps(manifest, indent=2))

    size_kb = zip_path.stat().st_size / 1024
    print(f"Saved {zip_path} ({size_kb:.1f} KB)")

    if a.keep > 0:
        old = sorted(out.glob("area139-backup-*.zip"))[: -a.keep]
        for p in old:
            p.unlink()
            print(f"Pruned {p.name}")

    if a.telegram:
        caption = f"Area 139 backup {stamp} - " + ", ".join(
            f"{k}:{v}" for k, v in manifest["rows"].items()
        )
        print("Telegram:", "sent" if telegram_send_file(zip_path, caption) else "not sent (token/chat missing or failed)")

    if errors:
        print("\nERRORS:\n  " + "\n  ".join(errors))
        sys.exit(1)


if __name__ == "__main__":
    main()
