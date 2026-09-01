"""Build a publication-safe AGROLATTICE 11.19 source archive.

The generated source archive intentionally excludes user SQLite databases,
installed datasets, caches, attachments and run outputs. It is supplementary to
the complete working release, not a replacement for the researcher's local data.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

MODULE_VERSION = "1.0.0"
REFERENCE_ID = "AGROLATTICE-11.19-PRR-2026-08-12"

EXCLUDED_DIR_PARTS = {
    "__pycache__", "cache", "Datasets", "dataset_updates", "project_store",
    "study_store", "system_backups", "migration_backups", "satellite_exports",
    "external_model_runs",
}
EXCLUDED_SUBPATHS = {
    "field_operations/attachments",
    "reports/assets",
}
EXCLUDED_SUFFIXES = {".sqlite", ".pyc"}
EXCLUDED_NAME_ENDINGS = (".sqlite-wal", ".sqlite-shm")


def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024), b''):
            h.update(b)
    return h.hexdigest()


def include_path(root: Path, path: Path) -> bool:
    rel=path.relative_to(root).as_posix()
    parts=set(path.relative_to(root).parts)
    if parts & EXCLUDED_DIR_PARTS:
        return False
    if any(rel == s or rel.startswith(s + "/") for s in EXCLUDED_SUBPATHS):
        return False
    if path.suffix.lower() in EXCLUDED_SUFFIXES:
        return False
    if path.name.endswith(EXCLUDED_NAME_ENDINGS):
        return False
    # Do not recursively archive an archive built by this script.
    if path.name.startswith("AGROLATTICE_11_19_PUBLICATION_SOURCE_ONLY") and path.suffix.lower()=='.zip':
        return False
    return True


def build(root: Path, output: Path) -> dict:
    root=root.resolve(); output=output.resolve(); output.parent.mkdir(parents=True,exist_ok=True)
    entries=[]
    with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for path in sorted(root.rglob('*')):
            if not path.is_file() or path.resolve()==output:
                continue
            if not include_path(root,path):
                continue
            rel=path.relative_to(root).as_posix()
            z.write(path, arcname=f"AGROLATTICE_11_19_Publication_Source/{rel}")
            entries.append({'path':rel,'sha256':sha256(path),'size_bytes':path.stat().st_size})
        manifest={
            'release':'AGROLATTICE 11.19',
            'reference_id':REFERENCE_ID,
            'archive_type':'publication-safe source archive',
            'contains_user_sqlite_databases':False,
            'contains_installed_country_datasets':False,
            'contains_synthetic_demo':True,
            'file_count':len(entries),
            'files':entries,
        }
        z.writestr('AGROLATTICE_11_19_Publication_Source/PUBLIC_SOURCE_ARCHIVE_MANIFEST.json', json.dumps(manifest,indent=2))
    return {'path':str(output),'sha256':sha256(output),'file_count':len(entries),'size_bytes':output.stat().st_size}


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parent)
    parser.add_argument('--output',type=Path,default=Path(__file__).resolve().parent/'AGROLATTICE_11_19_PUBLICATION_SOURCE_ONLY.zip')
    args=parser.parse_args()
    result=build(args.root,args.output)
    print(json.dumps(result,indent=2))
    return 0

if __name__=='__main__':
    raise SystemExit(main())
