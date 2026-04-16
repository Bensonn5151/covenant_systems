-- Covenant Systems — Core Schema
-- Run against Supabase Postgres

-- ══════════════════════════════════════════════════════════════════
-- REGULATIONS (ground truth — managed by system, not users)
-- ══════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS regulation_documents (
    id              BIGSERIAL PRIMARY KEY,
    document_id     TEXT UNIQUE NOT NULL,          -- e.g. "pipeda"
    title           TEXT NOT NULL,                 -- e.g. "PIPEDA"
    document_type   TEXT NOT NULL DEFAULT '',       -- Act, Regulation, Guidance
    jurisdiction    TEXT NOT NULL DEFAULT '',
    regulator       TEXT NOT NULL DEFAULT '',
    category        TEXT NOT NULL DEFAULT '',       -- act, regulation, guidance
    section_count   INT NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS regulation_sections (
    id                  BIGSERIAL PRIMARY KEY,
    document_id         TEXT NOT NULL REFERENCES regulation_documents(document_id),
    section_id          TEXT UNIQUE NOT NULL,       -- e.g. "pipeda_s0001"
    section_number      TEXT NOT NULL DEFAULT '',
    title               TEXT NOT NULL DEFAULT '',
    body                TEXT NOT NULL DEFAULT '',
    classification      TEXT NOT NULL DEFAULT 'procedural',  -- obligation, prohibition, permission, definition, procedural
    severity_signal     TEXT,                       -- punitive, mandatory, procedural, definitional (only on obligation/prohibition)
    operational_areas   TEXT[] NOT NULL DEFAULT '{}',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_regsec_docid ON regulation_sections(document_id);
CREATE INDEX IF NOT EXISTS idx_regsec_classification ON regulation_sections(classification);

-- ══════════════════════════════════════════════════════════════════
-- ORGANIZATIONS + USERS (linked to Clerk)
-- ══════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS organizations (
    id              BIGSERIAL PRIMARY KEY,
    name            TEXT NOT NULL,
    clerk_org_id    TEXT UNIQUE,                    -- Clerk organization ID (optional)
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS users (
    id              BIGSERIAL PRIMARY KEY,
    clerk_user_id   TEXT UNIQUE NOT NULL,           -- Clerk user ID
    org_id          BIGINT REFERENCES organizations(id),
    email           TEXT,
    name            TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ══════════════════════════════════════════════════════════════════
-- POLICIES (uploaded by users)
-- ══════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS policies (
    id              BIGSERIAL PRIMARY KEY,
    org_id          BIGINT REFERENCES organizations(id),
    uploaded_by     TEXT NOT NULL,                  -- Clerk user ID
    name            TEXT NOT NULL,
    filename        TEXT,
    raw_text        TEXT,
    section_count   INT NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS policy_sections (
    id              BIGSERIAL PRIMARY KEY,
    policy_id       BIGINT NOT NULL REFERENCES policies(id) ON DELETE CASCADE,
    section_id      TEXT NOT NULL,                  -- e.g. "policy-s001"
    title           TEXT NOT NULL DEFAULT '',
    body            TEXT NOT NULL DEFAULT '',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_polsec_policyid ON policy_sections(policy_id);

-- ══════════════════════════════════════════════════════════════════
-- COMPLIANCE ASSESSMENTS (saved comparison results)
-- ══════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS compliance_assessments (
    id              BIGSERIAL PRIMARY KEY,
    policy_id       BIGINT NOT NULL REFERENCES policies(id) ON DELETE CASCADE,
    run_by          TEXT NOT NULL,                  -- Clerk user ID
    status          TEXT NOT NULL DEFAULT 'completed',
    regulation_count INT NOT NULL DEFAULT 0,
    avg_coverage    REAL NOT NULL DEFAULT 0,
    total_gaps      INT NOT NULL DEFAULT 0,
    total_covered   INT NOT NULL DEFAULT 0,
    heatmap         JSONB,                         -- full heatmap grid
    summary         JSONB,                         -- per-regulation summary
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS assessment_results (
    id                      BIGSERIAL PRIMARY KEY,
    assessment_id           BIGINT NOT NULL REFERENCES compliance_assessments(id) ON DELETE CASCADE,
    regulation_document_id  TEXT NOT NULL,          -- e.g. "pipeda"
    regulation_section_id   TEXT NOT NULL,          -- e.g. "pipeda_s0017"
    regulation_title        TEXT NOT NULL DEFAULT '',
    coverage_status         TEXT NOT NULL,          -- covered, partial, gap
    residual_risk           TEXT NOT NULL,          -- low, medium, high, critical
    severity_signal         TEXT,
    matched_policy_clause   TEXT,                   -- which policy clause matched
    reasoning               TEXT,                   -- LLM reasoning
    operational_areas       TEXT[] NOT NULL DEFAULT '{}',
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ar_assessid ON assessment_results(assessment_id);
CREATE INDEX IF NOT EXISTS idx_ar_status ON assessment_results(coverage_status);
