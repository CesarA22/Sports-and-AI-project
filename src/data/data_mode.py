"""
DATA_MODE: local | download | build
- local: usa arquivos existentes
- download: baixa bundle do DATA_BUNDLE_URL e extrai
- build: roda pipeline e gera
"""
import hashlib
import json
import logging
import os
import subprocess
import sys
import zipfile
from pathlib import Path
from datetime import datetime

import requests

from config import (
    DATA_DIR,
    DATA_MODE,
    DATA_BUNDLE_URL,
    METADATA_JSON,
    BUNDLE_ZIP,
    S3_ENDPOINT,
    S3_BUCKET,
    S3_ACCESS_KEY,
    S3_SECRET_KEY,
    S3_BUNDLE_KEY,
    SEASONS_ALLOWED,
)

logger = logging.getLogger(__name__)

REQUIRED_FILES = ["master.parquet", "features.parquet", "umap_clusters.parquet", "outliers.parquet"]
OPTIONAL_FILES = ["player_cards.jsonl", "player_images.parquet"]


def _sha256(path: Path) -> str:
    """Calcula SHA256 do arquivo."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_data_dir():
    """Garante que data/processed existe."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def validate_schema_minimum() -> bool:
    """Valida que existe schema mínimo (master.parquet)."""
    master = DATA_DIR / "master.parquet"
    if not master.exists():
        return False
    try:
        import pandas as pd
        df = pd.read_parquet(master)
        return "player_key" in df.columns and "player" in df.columns
    except Exception:
        return False


def load_metadata() -> dict:
    """Carrega metadata.json se existir."""
    if not METADATA_JSON.exists():
        return {}
    try:
        with open(METADATA_JSON, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning("Failed to load metadata: %s", e)
        return {}


def save_metadata(meta: dict):
    """Salva metadata.json."""
    ensure_data_dir()
    with open(METADATA_JSON, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


def build_metadata() -> dict:
    """Gera metadata a partir dos arquivos em data/processed."""
    meta = {
        "source": "sample/generate_sample_data",
        "seasons": [2023, 2024],
        "created_at": datetime.utcnow().isoformat() + "Z",
        "schema_version": 1,
        "row_count": {},
        "hashes": {},
        "files": [],
    }
    try:
        import subprocess
        result = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=Path(__file__).parent.parent.parent)
        if result.returncode == 0:
            meta["commit_hash"] = result.stdout.strip()
    except Exception:
        pass

    for fname in REQUIRED_FILES + OPTIONAL_FILES:
        path = DATA_DIR / fname
        if path.exists():
            meta["hashes"][fname] = _sha256(path)
            meta["files"].append(fname)
            if fname.endswith(".parquet"):
                try:
                    import pandas as pd
                    df = pd.read_parquet(path)
                    meta["row_count"][fname] = len(df)
                except Exception:
                    pass
    return meta


def _download_from_s3() -> bool:
    """Baixa do bucket S3/Railway com credenciais."""
    if not all([S3_ENDPOINT, S3_BUCKET, S3_ACCESS_KEY, S3_SECRET_KEY]):
        return False
    ensure_data_dir()
    try:
        import boto3
        from botocore.config import Config
        client = boto3.client(
            "s3",
            endpoint_url=S3_ENDPOINT,
            aws_access_key_id=S3_ACCESS_KEY,
            aws_secret_access_key=S3_SECRET_KEY,
            config=Config(signature_version="s3v4"),
        )
        bundle_path = BUNDLE_ZIP
        client.download_file(S3_BUCKET, S3_BUNDLE_KEY, str(bundle_path))
        with zipfile.ZipFile(bundle_path, "r") as z:
            z.extractall(DATA_DIR)
        if bundle_path.exists():
            bundle_path.unlink()
        return validate_schema_minimum()
    except Exception as e:
        logger.exception("S3 download failed: %s", e)
        return False


def run_download() -> bool:
    """Baixa bundle e extrai em data/processed. Usa S3 se credenciais definidas."""
    # 1) S3/Railway (bucket privado com auth)
    if S3_ACCESS_KEY and S3_SECRET_KEY:
        return _download_from_s3()
    # 2) URL pública (GitHub Release etc)
    if not DATA_BUNDLE_URL:
        logger.warning("DATA_BUNDLE_URL or S3_ACCESS_KEY not set, cannot download")
        return False
    ensure_data_dir()
    try:
        r = requests.get(DATA_BUNDLE_URL, timeout=60)
        r.raise_for_status()
        bundle_path = BUNDLE_ZIP
        with open(bundle_path, "wb") as f:
            f.write(r.content)
        with zipfile.ZipFile(bundle_path, "r") as z:
            z.extractall(DATA_DIR)
        if bundle_path.exists():
            bundle_path.unlink()
        meta = load_metadata()
        if meta.get("hashes"):
            for fname, expected_hash in meta["hashes"].items():
                path = DATA_DIR / fname
                if path.exists() and _sha256(path) != expected_hash:
                    logger.warning("Hash mismatch for %s", fname)
        return validate_schema_minimum()
    except Exception as e:
        logger.exception("Download failed: %s", e)
        return False


def run_build(seasons: list[int] = None) -> bool:
    """Roda pipeline de ingestão (dados reais FBref) ou sample se falhar."""
    ensure_data_dir()
    project_root = Path(__file__).resolve().parent.parent.parent

    # 1) Tentar pipeline real (FBref)
    try:
        from src.pipeline.ingest import run_pipeline
        if run_pipeline(seasons=list(SEASONS_ALLOWED) if seasons is None else seasons):
            return validate_schema_minimum()
    except Exception as e:
        logger.warning("Pipeline FBref failed: %s", e)

    # 2) Fallback: sample data
    script = project_root / "scripts" / "generate_sample_data.py"
    if script.exists():
        result = subprocess.run(
            [sys.executable, str(script)],
            cwd=str(project_root),
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return validate_schema_minimum()
        logger.error("Sample pipeline failed: %s", result.stderr)
    return False


def ensure_data() -> bool:
    """
    Garante que data/processed está pronto.
    Modo local: valida schema mínimo
    Modo download: baixa se faltando
    Modo build: gera
    """
    if DATA_MODE == "local":
        if validate_schema_minimum():
            return True
        logger.warning("Local data missing or invalid. Run pipeline or set DATA_MODE=download with DATA_BUNDLE_URL")
        return False

    if DATA_MODE == "download":
        if validate_schema_minimum():
            return True
        return run_download()

    if DATA_MODE == "build":
        return run_build()

    logger.warning("Unknown DATA_MODE=%s, falling back to local", DATA_MODE)
    return validate_schema_minimum()
