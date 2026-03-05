"""
Scout Radar - Configuração central.
"""
import os
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data" / "processed"

# Data files
MASTER_PARQUET = DATA_DIR / "master.parquet"
FEATURES_PARQUET = DATA_DIR / "features.parquet"
UMAP_CLUSTERS_PARQUET = DATA_DIR / "umap_clusters.parquet"
OUTLIERS_PARQUET = DATA_DIR / "outliers.parquet"
PLAYER_CARDS_JSONL = DATA_DIR / "player_cards.jsonl"

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
