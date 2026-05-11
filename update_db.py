"""
This file used to wipe and re-seed the DB. It has been disabled because the
destructive code referenced stale, incorrect classifications and would lose
the 2022-2025 paper data.

To seed a fresh DB, use the idempotent ``setup_db.py`` instead.

To wipe production data deliberately (rare), do it manually via SQL with a
conscious backup. Don't restore this file.
"""
raise SystemExit(
    "update_db.py is disabled. Use setup_db.py for idempotent seeding. "
    "See the file header for details."
)
