-- AGROLATTICE 11.19 schema export: crop_profiles
-- Schema version: 1.0.0
-- No user rows are included.
PRAGMA foreign_keys=ON;

CREATE TABLE crop_profile_versions(
                    version_id TEXT PRIMARY KEY,
                    profile_id TEXT NOT NULL,
                    version_number INTEGER NOT NULL,
                    parameters_json TEXT NOT NULL,
                    source_citation TEXT,
                    change_note TEXT,
                    created_by TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(profile_id) REFERENCES crop_profiles(profile_id) ON DELETE CASCADE,
                    UNIQUE(profile_id, version_number)
                );

CREATE TABLE crop_profiles(
                    profile_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    crop TEXT NOT NULL,
                    cultivar TEXT,
                    country TEXT,
                    region TEXT,
                    source_profile TEXT,
                    evidence_grade TEXT,
                    status TEXT NOT NULL,
                    author TEXT,
                    notes TEXT,
                    current_version INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

CREATE TABLE metadata(
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

CREATE INDEX idx_crop_profiles_country ON crop_profiles(country);

CREATE INDEX idx_crop_profiles_crop ON crop_profiles(crop);
