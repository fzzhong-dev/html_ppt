"""SQLite persistence for presentations and slides."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import aiosqlite

DB_PATH = Path(__file__).parent.parent.parent / "data" / "presentations.db"

_CREATE_TABLES = """
CREATE TABLE IF NOT EXISTS presentations (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    template_id TEXT DEFAULT 'generated',
    theme TEXT DEFAULT 'default',
    theme_data TEXT,
    created_at TEXT,
    updated_at TEXT
);
CREATE TABLE IF NOT EXISTS slides (
    id TEXT PRIMARY KEY,
    presentation_id TEXT NOT NULL,
    page_number INTEGER,
    html_content TEXT,
    editable_regions TEXT DEFAULT '{}',
    FOREIGN KEY (presentation_id) REFERENCES presentations(id) ON DELETE CASCADE
);
"""


async def _get_db() -> aiosqlite.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = await aiosqlite.connect(str(DB_PATH))
    await db.executescript(_CREATE_TABLES)
    db.row_factory = aiosqlite.Row
    return db


async def save_presentation(presentation: dict, slides: list[dict]) -> None:
    db = await _get_db()
    try:
        await db.execute(
            """INSERT OR REPLACE INTO presentations
               (id, title, template_id, theme, theme_data, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                presentation["id"],
                presentation["title"],
                presentation.get("template_id", "generated"),
                presentation.get("theme", "default"),
                json.dumps(presentation.get("theme_data"), ensure_ascii=False) if presentation.get("theme_data") else None,
                str(presentation.get("created_at", "")),
                str(presentation.get("updated_at", datetime.now().isoformat())),
            ),
        )
        await db.execute("DELETE FROM slides WHERE presentation_id = ?", (presentation["id"],))
        for s in slides:
            await db.execute(
                """INSERT INTO slides (id, presentation_id, page_number, html_content, editable_regions)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    s["id"],
                    presentation["id"],
                    s["page_number"],
                    s["html_content"],
                    json.dumps(s.get("editable_regions", {}), ensure_ascii=False),
                ),
            )
        await db.commit()
    finally:
        await db.close()


async def load_presentation(presentation_id: str) -> Optional[dict]:
    db = await _get_db()
    try:
        cursor = await db.execute("SELECT * FROM presentations WHERE id = ?", (presentation_id,))
        row = await cursor.fetchone()
        if not row:
            return None
        cursor = await db.execute(
            "SELECT * FROM slides WHERE presentation_id = ? ORDER BY page_number",
            (presentation_id,),
        )
        slides_rows = await cursor.fetchall()
        slides = []
        for r in slides_rows:
            slides.append({
                "id": r["id"],
                "page_number": r["page_number"],
                "html_content": r["html_content"],
                "editable_regions": json.loads(r["editable_regions"]) if r["editable_regions"] else {},
            })
        return {
            "id": row["id"],
            "title": row["title"],
            "template_id": row["template_id"],
            "theme": row["theme"],
            "theme_data": json.loads(row["theme_data"]) if row["theme_data"] else None,
            "slides": slides,
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
    finally:
        await db.close()


async def list_presentations() -> list[dict]:
    db = await _get_db()
    try:
        cursor = await db.execute(
            """SELECT p.id, p.title, p.created_at, p.updated_at,
                      (SELECT COUNT(*) FROM slides s WHERE s.presentation_id = p.id) AS slides_count
               FROM presentations p ORDER BY p.updated_at DESC"""
        )
        return [dict(r) for r in await cursor.fetchall()]
    finally:
        await db.close()


async def delete_presentation(presentation_id: str) -> bool:
    db = await _get_db()
    try:
        cursor = await db.execute("SELECT id FROM presentations WHERE id = ?", (presentation_id,))
        if not await cursor.fetchone():
            return False
        await db.execute("DELETE FROM slides WHERE presentation_id = ?", (presentation_id,))
        await db.execute("DELETE FROM presentations WHERE id = ?", (presentation_id,))
        await db.commit()
        return True
    finally:
        await db.close()
