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
    PLAYER_IMAGES_PARQUET,
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
        player_images: pd.DataFrame = None,
    ):
        self.master = master
        self.features = features
        self.umap_clusters = umap_clusters
        self.outliers = outliers
        self.player_cards = player_cards
        self.player_images = player_images if player_images is not None else pd.DataFrame()

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
    player_images = _read_parquet(PLAYER_IMAGES_PARQUET)

    return AppData(
        master=master,
        features=features,
        umap_clusters=umap_clusters,
        outliers=outliers,
        player_cards=player_cards,
        player_images=player_images,
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

    # Merge umap_clusters (garantir tipos compatíveis)
    if not data.umap_clusters.empty:
        uc = data.umap_clusters.copy()
        merge_cols = [c for c in join_cols if c in uc.columns and c in df.columns]
        uc_cols = [c for c in ["umap_x", "umap_y", "cluster_id", "cluster_prob", "is_noise"] if c in uc.columns]
        if merge_cols and uc_cols:
            for c in merge_cols:
                if df[c].dtype != uc[c].dtype:
                    uc[c] = uc[c].astype(df[c].dtype)
            df = df.merge(
                uc[merge_cols + uc_cols].drop_duplicates(merge_cols),
                on=merge_cols,
                how="left",
            )

    # Fallback: se não há umap ou valores NaN, criar coords
    import numpy as np
    need_umap = "umap_x" not in df.columns or "umap_y" not in df.columns
    if not need_umap and ("umap_x" in df.columns and "umap_y" in df.columns):
        need_umap = df["umap_x"].isna().all() or df["umap_y"].isna().all()
    if need_umap:
        n = len(df)
        feat_cols = [c for c in df.columns if "per90" in c or "z_" in c][:2]
        if feat_cols:
            df["umap_x"] = df[feat_cols[0]].fillna(0).values
            df["umap_y"] = df[feat_cols[1]].fillna(0).values if len(feat_cols) > 1 else np.zeros(n)
        else:
            np.random.seed(42)
            df["umap_x"] = np.random.randn(n) * 2
            df["umap_y"] = np.random.randn(n) * 2
        if "cluster_id" not in df.columns or df["cluster_id"].isna().all():
            df["cluster_id"] = np.random.randint(0, 5, n)

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
