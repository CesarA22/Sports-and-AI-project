"""
Data loader - carrega parquets de data/processed/ e expõe DataFrames unificados.
"""
import json
import logging
from pathlib import Path
from typing import Optional

import pandas as pd

from config import (
    MASTER_PARQUET,
    FEATURES_PARQUET,
    UMAP_CLUSTERS_PARQUET,
    OUTLIERS_PARQUET,
    PLAYER_CARDS_JSONL,
)

logger = logging.getLogger(__name__)


class AppData:
    """Container para datasets carregados."""

    def __init__(
        self,
        master: pd.DataFrame,
        features: pd.DataFrame,
        umap_clusters: pd.DataFrame,
        outliers: pd.DataFrame,
        player_cards: dict[str, str],
    ):
        self.master = master
        self.features = features
        self.umap_clusters = umap_clusters
        self.outliers = outliers
        self.player_cards = player_cards

    @property
    def is_empty(self) -> bool:
        return (
            self.master.empty
            and self.features.empty
            and self.umap_clusters.empty
            and self.outliers.empty
        )


def _read_parquet(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_parquet(path)
    except Exception as e:
        logger.warning("Failed to load %s: %s", path, e)
        return pd.DataFrame()


def _load_player_cards(path: Path) -> dict[str, str]:
    cards = {}
    if not path.exists():
        return cards
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                pk = obj.get("player_key")
                if pk:
                    cards[pk] = obj.get("card", str(obj))
    except Exception as e:
        logger.warning("Failed to load player_cards: %s", e)
    return cards


def load_data() -> AppData:
    """Carrega todos os artefatos de data/processed/."""
    master = _read_parquet(MASTER_PARQUET)
    features = _read_parquet(FEATURES_PARQUET)
    umap_clusters = _read_parquet(UMAP_CLUSTERS_PARQUET)
    outliers = _read_parquet(OUTLIERS_PARQUET)
    player_cards = _load_player_cards(PLAYER_CARDS_JSONL)

    return AppData(
        master=master,
        features=features,
        umap_clusters=umap_clusters,
        outliers=outliers,
        player_cards=player_cards,
    )


def get_merged_df(data: AppData) -> pd.DataFrame:
    """
    Junta master + features + umap_clusters + outliers em um único DataFrame.
    Usa player_key e season (ou equivalentes) como chaves.
    """
    if data.is_empty:
        return pd.DataFrame()

    # Identificar colunas de join
    join_cols = ["player_key", "season"]
    for c in ["player_id", "player", "team"]:
        if c not in join_cols and (data.master.columns.isin([c])).any():
            pass  # manter join_cols padrão

    df = data.master.copy()

    # Merge features
    if not data.features.empty and "player_key" in data.features.columns:
        feat_cols = [c for c in data.features.columns if c not in join_cols]
        df = df.merge(
            data.features[join_cols + feat_cols].drop_duplicates(join_cols),
            on=join_cols,
            how="left",
            suffixes=("", "_feat"),
        )
        df = df[[c for c in df.columns if not c.endswith("_feat")]]

    # Merge umap_clusters
    if not data.umap_clusters.empty:
        uc = data.umap_clusters
        uc_cols = ["umap_x", "umap_y", "cluster_id", "cluster_prob", "is_noise"]
        uc_cols = [c for c in uc_cols if c in uc.columns]
        merge_cols = [c for c in join_cols if c in uc.columns]
        if merge_cols and uc_cols:
            df = df.merge(
                uc[merge_cols + uc_cols].drop_duplicates(merge_cols),
                on=merge_cols,
                how="left",
            )

    # Merge outliers
    if not data.outliers.empty:
        out = data.outliers
        out_cols = ["rarity_score", "impact_score", "prospect_score"]
        out_cols = [c for c in out_cols if c in out.columns]
        merge_cols = [c for c in join_cols if c in out.columns]
        if merge_cols and out_cols:
            df = df.merge(
                out[merge_cols + out_cols].drop_duplicates(merge_cols),
                on=merge_cols,
                how="left",
            )

    return df
