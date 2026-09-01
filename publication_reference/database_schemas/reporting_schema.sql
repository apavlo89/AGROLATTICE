-- AGROLATTICE 11.19 schema export: reporting
-- Schema version: 1.0.0
-- No user rows are included.
PRAGMA foreign_keys=ON;

CREATE TABLE audit_log (
            audit_id TEXT PRIMARY KEY,
            study_id TEXT,
            action TEXT NOT NULL,
            entity_type TEXT,
            entity_id TEXT,
            actor TEXT,
            details_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            FOREIGN KEY(study_id) REFERENCES studies(study_id) ON DELETE CASCADE
        );

CREATE TABLE citations (
            citation_id TEXT PRIMARY KEY,
            doi TEXT,
            authors TEXT,
            year INTEGER,
            title TEXT NOT NULL,
            journal TEXT,
            bibtex TEXT,
            ris TEXT,
            notes TEXT,
            source TEXT,
            created_at TEXT NOT NULL
        );

CREATE TABLE claims (
            claim_id TEXT PRIMARY KEY,
            study_id TEXT NOT NULL,
            version_id TEXT,
            claim_text TEXT NOT NULL,
            evidence_type TEXT,
            source_reference TEXT,
            statistic TEXT,
            status TEXT NOT NULL DEFAULT 'Draft',
            notes TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(study_id) REFERENCES studies(study_id) ON DELETE CASCADE,
            FOREIGN KEY(version_id) REFERENCES report_versions(version_id)
        );

CREATE TABLE evidence_snapshots (
            snapshot_id TEXT PRIMARY KEY,
            study_id TEXT NOT NULL,
            label TEXT,
            scope_json TEXT NOT NULL DEFAULT '{}',
            manifest_json TEXT NOT NULL,
            manifest_sha256 TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(study_id) REFERENCES studies(study_id) ON DELETE CASCADE
        );

CREATE TABLE export_packages (
            export_id TEXT PRIMARY KEY,
            study_id TEXT NOT NULL,
            version_id TEXT,
            package_type TEXT NOT NULL,
            privacy_profile TEXT NOT NULL,
            file_path TEXT,
            sha256 TEXT,
            manifest_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            FOREIGN KEY(study_id) REFERENCES studies(study_id) ON DELETE CASCADE,
            FOREIGN KEY(version_id) REFERENCES report_versions(version_id)
        );

CREATE TABLE metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

CREATE TABLE report_artifacts (
            artifact_id TEXT PRIMARY KEY,
            study_id TEXT NOT NULL,
            snapshot_id TEXT,
            kind TEXT NOT NULL,
            title TEXT NOT NULL,
            caption TEXT,
            source_json TEXT NOT NULL DEFAULT '{}',
            settings_json TEXT NOT NULL DEFAULT '{}',
            file_path TEXT,
            sha256 TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(study_id) REFERENCES studies(study_id) ON DELETE CASCADE,
            FOREIGN KEY(snapshot_id) REFERENCES evidence_snapshots(snapshot_id)
        );

CREATE TABLE report_versions (
            version_id TEXT PRIMARY KEY,
            study_id TEXT NOT NULL,
            version_number INTEGER NOT NULL,
            label TEXT,
            manuscript_status TEXT NOT NULL DEFAULT 'Draft',
            evidence_snapshot_id TEXT,
            manuscript_json TEXT NOT NULL DEFAULT '{}',
            notes TEXT,
            author TEXT,
            created_at TEXT NOT NULL,
            UNIQUE(study_id, version_number),
            FOREIGN KEY(study_id) REFERENCES studies(study_id) ON DELETE CASCADE,
            FOREIGN KEY(evidence_snapshot_id) REFERENCES evidence_snapshots(snapshot_id)
        );

CREATE TABLE studies (
            study_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            short_title TEXT,
            report_type TEXT NOT NULL,
            scope_json TEXT NOT NULL DEFAULT '{}',
            manuscript_json TEXT NOT NULL DEFAULT '{}',
            authors_json TEXT NOT NULL DEFAULT '[]',
            affiliations_json TEXT NOT NULL DEFAULT '[]',
            corresponding_author TEXT,
            corresponding_orcid TEXT,
            target_journal TEXT,
            manuscript_status TEXT NOT NULL DEFAULT 'Draft',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

CREATE TABLE study_citations (
            study_id TEXT NOT NULL,
            citation_id TEXT NOT NULL,
            purpose TEXT,
            PRIMARY KEY(study_id, citation_id),
            FOREIGN KEY(study_id) REFERENCES studies(study_id) ON DELETE CASCADE,
            FOREIGN KEY(citation_id) REFERENCES citations(citation_id) ON DELETE CASCADE
        );

CREATE INDEX idx_artifacts_study ON report_artifacts(study_id, kind, created_at DESC);

CREATE UNIQUE INDEX idx_citations_doi ON citations(doi) WHERE doi IS NOT NULL AND doi <> '';

CREATE INDEX idx_claims_study ON claims(study_id, status);

CREATE INDEX idx_reports_updated ON studies(updated_at DESC);

CREATE INDEX idx_snapshots_study ON evidence_snapshots(study_id, created_at DESC);

CREATE INDEX idx_versions_study ON report_versions(study_id, version_number DESC);
