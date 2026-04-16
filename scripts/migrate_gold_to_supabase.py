#!/usr/bin/env python3
"""
Migrate Gold layer sections from storage/gold/*/sections.json into Supabase.

Creates regulation_documents and regulation_sections rows from the
existing JSON files. Safe to re-run — uses ON CONFLICT DO NOTHING.

Usage:
    python3 scripts/migrate_gold_to_supabase.py
"""

import json
import os
import sys
from pathlib import Path

import psycopg2

ROOT = Path(__file__).resolve().parent.parent
GOLD_DIR = ROOT / "storage" / "gold"

# Load .env
sys.path.insert(0, str(ROOT))
from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not set in .env")
    sys.exit(1)


def main():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    doc_count = 0
    section_count = 0

    for sections_file in sorted(GOLD_DIR.glob("*/sections.json")):
        doc_id = sections_file.parent.name
        sections = json.loads(sections_file.read_text())
        if not isinstance(sections, list) or not sections:
            continue

        first = sections[0]
        meta = first.get("metadata", {}) if isinstance(first.get("metadata"), dict) else {}

        # Upsert regulation_documents
        cur.execute("""
            INSERT INTO regulation_documents (document_id, title, document_type, jurisdiction, regulator, category, section_count)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (document_id) DO UPDATE SET
                section_count = EXCLUDED.section_count,
                document_type = EXCLUDED.document_type,
                jurisdiction = EXCLUDED.jurisdiction,
                regulator = EXCLUDED.regulator
        """, (
            doc_id,
            doc_id.replace("_", " ").title(),
            meta.get("document_type", ""),
            meta.get("jurisdiction", ""),
            meta.get("regulator", ""),
            meta.get("category", ""),
            len(sections),
        ))
        doc_count += 1

        # Insert sections
        for s in sections:
            cls = s.get("classification", {}) or {}
            label = cls.get("label", "procedural") if isinstance(cls, dict) else "procedural"
            severity = s.get("severity_signal")
            areas = s.get("operational_areas", []) or []

            cur.execute("""
                INSERT INTO regulation_sections
                    (document_id, section_id, section_number, title, body, classification, severity_signal, operational_areas)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (section_id) DO NOTHING
            """, (
                doc_id,
                s.get("section_id", ""),
                s.get("section_number", ""),
                s.get("title", ""),
                s.get("body", ""),
                label,
                severity,
                areas,
            ))
            section_count += 1

    conn.commit()
    cur.close()
    conn.close()

    print(f"Migrated {doc_count} documents, {section_count} sections to Supabase")


if __name__ == "__main__":
    main()
