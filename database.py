"""SQLite persistence for PRESTYJ Lead Scraper search history."""

import json
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "leads.db")


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create tables if they don't exist (safe to call on every app start)."""
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS searches (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                business_type TEXT NOT NULL,
                location      TEXT NOT NULL,
                lead_count    INTEGER NOT NULL,
                enriched      INTEGER NOT NULL DEFAULT 0,
                scored        INTEGER NOT NULL DEFAULT 0,
                emails_found  INTEGER NOT NULL DEFAULT 0,
                created_at    TEXT NOT NULL DEFAULT (datetime('now','localtime'))
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS leads (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                search_id INTEGER NOT NULL UNIQUE,
                leads_json TEXT NOT NULL,
                FOREIGN KEY (search_id) REFERENCES searches(id) ON DELETE CASCADE
            )
            """
        )


def save_search(business_type, location, leads, enriched=False, scored=False, emails_found=False):
    """Save a search and its leads. Returns the new search_id."""
    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO searches (business_type, location, lead_count, enriched, scored, emails_found)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (business_type, location, len(leads), int(enriched), int(scored), int(emails_found)),
        )
        search_id = cur.lastrowid
        conn.execute(
            "INSERT INTO leads (search_id, leads_json) VALUES (?, ?)",
            (search_id, json.dumps(leads)),
        )
    return search_id


def get_search_history():
    """Return all searches newest-first (metadata only, no blobs)."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, business_type, location, lead_count, enriched, scored, emails_found, created_at "
            "FROM searches ORDER BY id DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def get_leads_for_search(search_id):
    """Deserialize and return leads for a given search, or None."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT leads_json FROM leads WHERE search_id = ?", (search_id,)
        ).fetchone()
    if row:
        return json.loads(row["leads_json"])
    return None


def delete_search(search_id):
    """Delete a search and its leads (cascade). Returns True if a row was deleted."""
    with _connect() as conn:
        cur = conn.execute("DELETE FROM searches WHERE id = ?", (search_id,))
    return cur.rowcount > 0


def delete_all_searches():
    """Delete all searches and leads. Returns number of searches deleted."""
    with _connect() as conn:
        cur = conn.execute("DELETE FROM searches")
    return cur.rowcount
