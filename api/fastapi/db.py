"""
Database connection module for Supabase Postgres.

Uses psycopg2 with a simple connection pool. All queries go through
get_conn() which returns a connection from the pool.
"""

import os
from contextlib import contextmanager
from typing import Generator

import psycopg2
from psycopg2 import pool

_pool: pool.SimpleConnectionPool | None = None


def _get_pool() -> pool.SimpleConnectionPool:
    global _pool
    if _pool is None:
        url = os.environ.get("DATABASE_URL")
        if not url:
            raise RuntimeError("DATABASE_URL not set")
        _pool = pool.SimpleConnectionPool(minconn=1, maxconn=5, dsn=url)
    return _pool


@contextmanager
def get_conn() -> Generator:
    """Get a connection from the pool. Auto-returns on exit."""
    p = _get_pool()
    conn = p.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        p.putconn(conn)


# ── Regulation queries ───────────────────────────────────────────────────────

def list_regulation_documents() -> list[dict]:
    """Return all regulation documents."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT document_id, title, document_type, jurisdiction, regulator, category, section_count
            FROM regulation_documents ORDER BY section_count DESC
        """)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]


def get_regulation_sections(document_id: str) -> list[dict]:
    """Return all sections for a regulation document."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT section_id, section_number, title, body, classification,
                   severity_signal, operational_areas
            FROM regulation_sections
            WHERE document_id = %s
            ORDER BY section_id
        """, (document_id,))
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]


def get_obligation_sections_db(document_id: str) -> list[dict]:
    """Return only obligation + prohibition sections for a regulation."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT section_id, section_number, title, body, classification,
                   severity_signal, operational_areas
            FROM regulation_sections
            WHERE document_id = %s AND classification IN ('obligation', 'prohibition')
            ORDER BY section_id
        """, (document_id,))
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]


def list_regulation_ids() -> list[str]:
    """Return all regulation document IDs."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT document_id FROM regulation_documents ORDER BY section_count DESC")
        return [row[0] for row in cur.fetchall()]


# ── Policy queries ───────────────────────────────────────────────────────────

def save_policy(uploaded_by: str, name: str, filename: str | None, raw_text: str | None,
                sections: list[dict], org_id: int | None = None) -> int:
    """Save an uploaded policy and its sections. Returns policy ID."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO policies (org_id, uploaded_by, name, filename, raw_text, section_count)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (org_id, uploaded_by, name, filename, raw_text, len(sections)))
        policy_id = cur.fetchone()[0]

        for s in sections:
            cur.execute("""
                INSERT INTO policy_sections (policy_id, section_id, title, body)
                VALUES (%s, %s, %s, %s)
            """, (policy_id, s.get("section_id", ""), s.get("title", ""), s.get("body", "")))

        return policy_id


def get_policy(policy_id: int) -> dict | None:
    """Get a policy by ID."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, name, filename, section_count, created_at FROM policies WHERE id = %s", (policy_id,))
        row = cur.fetchone()
        if not row:
            return None
        return {"id": row[0], "name": row[1], "filename": row[2], "section_count": row[3], "created_at": str(row[4])}


def get_policy_sections(policy_id: int) -> list[dict]:
    """Get sections for a policy."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT section_id, title, body FROM policy_sections
            WHERE policy_id = %s ORDER BY id
        """, (policy_id,))
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]


def list_policies(uploaded_by: str) -> list[dict]:
    """List policies for a user."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, name, filename, section_count, created_at
            FROM policies WHERE uploaded_by = %s
            ORDER BY created_at DESC
        """, (uploaded_by,))
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]


# ── Assessment queries ───────────────────────────────────────────────────────

def save_assessment(policy_id: int, run_by: str, regulation_count: int,
                    avg_coverage: float, total_gaps: int, total_covered: int,
                    heatmap: dict, summary: dict, results: list[dict]) -> int:
    """Save a compliance assessment and its per-obligation results. Returns assessment ID."""
    import json
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO compliance_assessments
                (policy_id, run_by, regulation_count, avg_coverage, total_gaps, total_covered, heatmap, summary)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (policy_id, run_by, regulation_count, avg_coverage, total_gaps, total_covered,
              json.dumps(heatmap), json.dumps(summary)))
        assessment_id = cur.fetchone()[0]

        for r in results:
            cur.execute("""
                INSERT INTO assessment_results
                    (assessment_id, regulation_document_id, regulation_section_id, regulation_title,
                     coverage_status, residual_risk, severity_signal, matched_policy_clause, reasoning, operational_areas)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (assessment_id, r.get("regulation_document_id", ""), r.get("regulation_section_id", ""),
                  r.get("regulation_title", ""), r.get("coverage_status", "gap"), r.get("residual_risk", "high"),
                  r.get("severity_signal"), r.get("matched_policy_clause"), r.get("reasoning"),
                  r.get("operational_areas", [])))

        return assessment_id


def get_assessment(assessment_id: int) -> dict | None:
    """Get a saved assessment with its results."""
    import json
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, policy_id, run_by, regulation_count, avg_coverage,
                   total_gaps, total_covered, heatmap, summary, created_at
            FROM compliance_assessments WHERE id = %s
        """, (assessment_id,))
        row = cur.fetchone()
        if not row:
            return None
        return {
            "id": row[0], "policy_id": row[1], "run_by": row[2],
            "regulation_count": row[3], "avg_coverage": row[4],
            "total_gaps": row[5], "total_covered": row[6],
            "heatmap": row[7], "summary": row[8],
            "created_at": str(row[9]),
        }


def list_assessments(policy_id: int) -> list[dict]:
    """List assessments for a policy."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, regulation_count, avg_coverage, total_gaps, total_covered, created_at
            FROM compliance_assessments WHERE policy_id = %s
            ORDER BY created_at DESC
        """, (policy_id,))
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]


# ── User/org queries ─────────────────────────────────────────────────────────

def ensure_user(clerk_user_id: str, email: str | None = None, name: str | None = None) -> dict:
    """Create or get a user by Clerk ID. Auto-creates a personal org."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, org_id, email, name FROM users WHERE clerk_user_id = %s", (clerk_user_id,))
        row = cur.fetchone()
        if row:
            return {"id": row[0], "org_id": row[1], "email": row[2], "name": row[3]}

        # Create personal org
        display = name or email or clerk_user_id
        cur.execute("INSERT INTO organizations (name) VALUES (%s) RETURNING id", (f"{display}'s org",))
        org_id = cur.fetchone()[0]

        cur.execute("""
            INSERT INTO users (clerk_user_id, org_id, email, name)
            VALUES (%s, %s, %s, %s) RETURNING id
        """, (clerk_user_id, org_id, email, name))
        user_id = cur.fetchone()[0]

        return {"id": user_id, "org_id": org_id, "email": email, "name": name}
