"""
Cria processed_bundle.zip para upload em GitHub Release ou bucket.
Execute após gerar os parquets:
  python scripts/generate_sample_data.py
  python scripts/create_bundle.py
"""
import json
import sys
import zipfile
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "processed"
BUNDLE_PATH = PROJECT_ROOT / "data" / "processed_bundle.zip"

REQUIRED = ["master.parquet", "features.parquet", "umap_clusters.parquet", "outliers.parquet"]
OPTIONAL = ["player_cards.jsonl", "player_images.parquet", "metadata.json"]


def sha256(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    meta = {
        "source": "FBref/sample",
        "seasons": [2023, 2024],
        "created_at": datetime.utcnow().isoformat() + "Z",
        "schema_version": 1,
        "row_count": {},
        "hashes": {},
    }
    try:
        import subprocess
        r = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=PROJECT_ROOT)
        if r.returncode == 0:
            meta["commit_hash"] = r.stdout.strip()
    except Exception:
        pass

    files_to_bundle = []
    for f in REQUIRED:
        p = DATA_DIR / f
        if not p.exists():
            print(f"Missing required: {f}")
            sys.exit(1)
        meta["hashes"][f] = sha256(p)
        try:
            import pandas as pd
            meta["row_count"][f] = len(pd.read_parquet(p))
        except Exception:
            pass
        files_to_bundle.append(p)

    for f in OPTIONAL:
        p = DATA_DIR / f
        if p.exists() and f != "metadata.json":
            meta["hashes"][f] = sha256(p)
            files_to_bundle.append(p)

    meta_path = DATA_DIR / "metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    files_to_bundle.append(meta_path)

    BUNDLE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(BUNDLE_PATH, "w", zipfile.ZIP_DEFLATED) as z:
        for p in files_to_bundle:
            z.write(p, p.name)

    print(f"Bundle criado: {BUNDLE_PATH}")
    print(f"  Arquivos: {len(files_to_bundle)}")
    print(f"  Tamanho: {BUNDLE_PATH.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
