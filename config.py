"""
Scout Radar - Configuração central.
"""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_ROOT = PROJECT_ROOT / "data"
DATA_DIR = DATA_ROOT / "processed"
RAW_DIR = DATA_ROOT / "raw"
CACHE_DIR = DATA_ROOT / "cache"

# Data files
MASTER_PARQUET = DATA_DIR / "master.parquet"
FEATURES_PARQUET = DATA_DIR / "features.parquet"
UMAP_CLUSTERS_PARQUET = DATA_DIR / "umap_clusters.parquet"
OUTLIERS_PARQUET = DATA_DIR / "outliers.parquet"
PLAYER_CARDS_JSONL = DATA_DIR / "player_cards.jsonl"
PLAYER_IMAGES_PARQUET = DATA_DIR / "player_images.parquet"
METADATA_JSON = DATA_DIR / "metadata.json"
BUNDLE_ZIP = DATA_ROOT / "processed_bundle.zip"

# DATA_MODE: local | download | build
DATA_MODE = os.getenv("DATA_MODE", "local")
DATA_BUNDLE_URL = os.getenv("DATA_BUNDLE_URL", "")

# Railway/S3-compatible (bucket privado - precisa auth)
S3_ENDPOINT = os.getenv("S3_ENDPOINT", "")  # ex: https://t3.storageapi.dev
S3_BUCKET = os.getenv("S3_BUCKET", "")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "")
S3_BUNDLE_KEY = os.getenv("S3_BUNDLE_KEY", "processed_bundle.zip")

# Chat limits
USER_INPUT_MAX_CHARS = 800
TOOL_MAX_ROWS = 50
K_MAX = 25

# Seasons & scope
SEASONS_ALLOWED = {2023, 2024}
POSITION_GROUPS = ["GK", "CB", "FB", "DM", "CM_AM", "W", "ST"]

# Metrics allowlist (colunas permitidas nas respostas)
METRICS_ALLOWLIST = frozenset([
    "xg_per90", "xa_per90", "prog_passes_per90", "prog_carries_per90",
    "touches_box_per90", "tackles_per90", "interceptions_per90",
    "aerial_won_per90", "passes_completed_per90", "pass_accuracy",
    "pressures_per90", "shots_per90", "goals_per90", "assists_per90",
    "minutes", "age", "position_group", "team", "season",
    "prospect_score", "rarity_score", "impact_score",
    "cluster_id", "umap_x", "umap_y"
])
