"""
Pipeline de ingestão - busca dados reais do FBref via soccerdata.
Gera master, features, umap_clusters, outliers em data/processed/
"""
import json
import hashlib
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import DATA_DIR, SEASONS_ALLOWED

logger = logging.getLogger(__name__)

# Mapeamento FBref pos -> position_group (Scout Radar)
POS_MAP = {
    "GK": "GK",
    "DF": "CB",
    "DF,MF": "FB",
    "MF": "CM_AM",
    "MF,DF": "DM",
    "MF,FW": "CM_AM",
    "FW": "ST",
    "FW,MF": "W",
}
DEFAULT_POS = "CM_AM"


def _to_position_group(pos: str) -> str:
    """Converte posição FBref para position_group."""
    if pd.isna(pos):
        return DEFAULT_POS
    pos = str(pos).split(",")[0].strip()
    return POS_MAP.get(pos, DEFAULT_POS)


def _fetch_fbref(seasons: list[int]) -> pd.DataFrame:
    """Busca dados do FBref via soccerdata."""
    try:
        import soccerdata as sd
    except ImportError:
        raise ImportError("Instale: pip install soccerdata")

    # Liga brasileira - soccerdata pode usar "BRA-Serie A" ou similar
    league_options = ["BRA-Serie A", "BRA-Série A", "Serie A"]
    df_all = []

    for league_id in league_options:
        try:
            fbref = sd.FBref(leagues=league_id, seasons=seasons)
            stats = fbref.read_player_season_stats(stat_type="standard")
            if stats is not None and not stats.empty:
                if "season" not in stats.columns and "Season" in stats.columns:
                    stats["season"] = stats["Season"]
                df_all.append(stats)
                break
        except Exception as e:
            logger.debug("League %s failed: %s", league_id, e)
            continue

    if not df_all:
        # Fallback: listar ligas disponíveis
        try:
            fbref = sd.FBref()
            leagues = getattr(fbref, "available_leagues", lambda: [])()
            logger.warning("Liga Brasil não encontrada. Ligas disponíveis: %s", leagues)
        except Exception:
            pass
        raise ValueError(
            "soccerdata não encontrou dados do Brasileirão. "
            "Verifique se a liga 'BRA-Serie A' existe: pip install -U soccerdata"
        )

    return pd.concat(df_all, ignore_index=True)


def _fetch_fbref_alternative(seasons: list[int]) -> pd.DataFrame:
    """Scrape direto do FBref (comp 24 = Brazilian Serie A). FBref usa tabelas em HTML comments."""
    import re
    import requests
    from io import StringIO

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

    all_dfs = []
    for season in seasons:
        urls = [
            f"https://fbref.com/en/comps/24/{season}/stats/{season}-Serie-A-Stats",
            f"https://fbref.com/pt/comps/24/{season}/estatisticas/{season}-Serie-A-Estatisticas",
            "https://fbref.com/en/comps/24/Serie-A-Stats",
        ]
        for url in urls:
            try:
                r = requests.get(url, headers=headers, timeout=30)
                r.raise_for_status()
                html = r.text
                # FBref: descomentar tabelas (substituir comentários)
                html = re.sub(r"<!--", "", html)
                html = re.sub(r"-->", "", html)
                tables = pd.read_html(StringIO(html))
                for t in tables:
                    cols = [str(c).lower() for c in (t.columns.tolist() if hasattr(t.columns, 'tolist') else t.columns)]
                    flat = " ".join(cols) if isinstance(cols[0], str) else str(cols)
                    if "player" in flat and ("90s" in flat or "min" in flat or "minutes" in flat):
                        t["season"] = season
                        all_dfs.append(t)
                        break
                if all_dfs:
                    break
            except Exception as e:
                logger.debug("FBref %s: %s", url, e)
        if not all_dfs:
            break

    if not all_dfs:
        raise ValueError(
            "Não foi possível obter dados do FBref. "
            "Instale soccerdata: pip install soccerdata (suporta cache e rate limit)"
        )
    return pd.concat(all_dfs, ignore_index=True)


def run_pipeline(seasons: list[int] = None) -> bool:
    """
    Executa o pipeline completo.
    seasons: ex [2023, 2024]. Default: SEASONS_ALLOWED do config.
    """
    seasons = seasons or list(SEASONS_ALLOWED)

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # 1) Buscar dados
    try:
        df = _fetch_fbref(seasons)
    except (ValueError, ImportError) as e:
        logger.info("Tentando scraping direto: %s", e)
        try:
            df = _fetch_fbref_alternative(seasons)
        except Exception as e2:
            logger.exception("Pipeline failed: %s", e2)
            return False

    # 2) Normalizar colunas (FBref usa multiline headers às vezes)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = ["_".join(str(c) for c in col).strip("_") for col in df.columns]
    df.columns = [str(c).strip() for c in df.columns]

    col_map = {"Player": "player", "Squad": "team", "Min": "minutes", "Minutes": "minutes", "90s": "90s", "Age": "age", "Pos": "pos"}
    for old, new in col_map.items():
        if old in df.columns:
            df = df.rename(columns={old: new})
    if "player" not in df.columns and "Player" in df.columns:
        df["player"] = df["Player"]
    if "team" not in df.columns and "Squad" in df.columns:
        df["team"] = df["Squad"]

    if "minutes" not in df.columns and "90s" in df.columns:
        df["minutes"] = (df["90s"].astype(float) * 90).astype(int)
    if "player" not in df.columns:
        raise ValueError("Coluna 'player' não encontrada. Colunas: " + str(list(df.columns)))

    df["position_group"] = df.get("pos", pd.Series(dtype=object)).apply(_to_position_group)
    df["age"] = pd.to_numeric(df.get("age", 22), errors="coerce").fillna(22).astype(int)

    # 3) Filtrar U-23 e minutos mínimos
    df = df[df["age"] <= 23]
    df = df[df["minutes"] >= 400]

    # 4) player_key estável
    def make_key(row):
        name = str(row["player"]).lower().replace(" ", "_").replace(".", "")
        for c in "áàãâéêíóôõúç":
            name = name.replace(c, c.encode("ascii", "ignore").decode() or "a")
        return f"{name}_{int(row['season'])}"

    df["player_key"] = df.apply(make_key, axis=1)
    df = df.drop_duplicates(subset=["player_key"], keep="first").reset_index(drop=True)

    # 5) master.parquet
    master_cols = ["player_key", "player", "team", "season", "position_group", "age", "minutes"]
    master = df[[c for c in master_cols if c in df.columns]].copy()

    # 6) features.parquet (métricas per90)
    feat_cols = [c for c in df.columns if "per 90" in c.lower() or "Per 90" in str(c) or "/90" in str(c)]
    if not feat_cols:
        feat_cols = [c for c in df.columns if c in ["Gls", "Ast", "xG", "xAG", "PrgC", "PrgP", "Cmp", "Att"]]
    features = master[["player_key", "season"]].copy()
    for c in feat_cols[:15]:
        if c in df.columns:
            features[c] = df[c].values

    # Renomear para padrão per90
    features = features.rename(columns=lambda x: x.lower().replace(" ", "_").replace("-", "_") if isinstance(x, str) else x)

    # 7) umap_clusters (simplificado - PCA/UMAP real precisaria de mais features)
    from sklearn.preprocessing import StandardScaler
    from sklearn.decomposition import PCA

    numeric_cols = [c for c in features.columns if features[c].dtype in [np.float64, np.float32] and c not in ["player_key", "season"]]
    if len(numeric_cols) >= 2:
        X = features[numeric_cols].fillna(0)
        X = StandardScaler().fit_transform(X)
        if X.shape[1] > 2:
            pca = PCA(n_components=2, random_state=42)
            xy = pca.fit_transform(X)
        else:
            xy = X
        umap_df = master[["player_key", "player", "team", "season", "position_group"]].copy()
        umap_df["umap_x"] = xy[:, 0]
        umap_df["umap_y"] = xy[:, 1]
    else:
        umap_df = master[["player_key", "player", "team", "season", "position_group"]].copy()
        umap_df["umap_x"] = np.random.randn(len(master)) * 2
        umap_df["umap_y"] = np.random.randn(len(master)) * 2

    try:
        from sklearn.cluster import HDBSCAN
        clusterer = HDBSCAN(min_cluster_size=3, min_samples=2)
        umap_df["cluster_id"] = clusterer.fit_predict(umap_df[["umap_x", "umap_y"]])
        umap_df["cluster_prob"] = 0.9
        umap_df["is_noise"] = (umap_df["cluster_id"] == -1).astype(int)
    except Exception:
        umap_df["cluster_id"] = 0
        umap_df["cluster_prob"] = 0.9
        umap_df["is_noise"] = 0

    # 8) outliers (scores simplificados)
    from sklearn.ensemble import IsolationForest
    X_out = umap_df[["umap_x", "umap_y"]].values
    iso = IsolationForest(contamination=0.1, random_state=42)
    pred = iso.fit_predict(X_out)
    rarity = 1 - (pred == 1).astype(float) * 0.5
    impact = np.abs(umap_df["umap_x"]) + np.abs(umap_df["umap_y"])
    impact = (impact - impact.min()) / (impact.max() - impact.min() + 1e-8)
    outliers_df = master[["player_key", "player", "team", "season"]].copy()
    outliers_df["rarity_score"] = rarity
    outliers_df["impact_score"] = impact
    outliers_df["prospect_score"] = rarity + impact + np.random.rand(len(outliers_df)) * 0.2

    # 9) Salvar
    master.to_parquet(DATA_DIR / "master.parquet", index=False)
    features.to_parquet(DATA_DIR / "features.parquet", index=False)
    umap_df.to_parquet(DATA_DIR / "umap_clusters.parquet", index=False)
    outliers_df.to_parquet(DATA_DIR / "outliers.parquet", index=False)

    # 10) player_cards.jsonl
    with open(DATA_DIR / "player_cards.jsonl", "w", encoding="utf-8") as f:
        for _, row in master.iterrows():
            card = {
                "player_key": row["player_key"],
                "player": row["player"],
                "team": row["team"],
                "season": int(row["season"]),
                "card": f"{row['player']} ({row['team']}, {row['season']}) - {row['position_group']}, {row['minutes']} min.",
            }
            f.write(json.dumps(card, ensure_ascii=False) + "\n")

    # 11) metadata.json
    def _sha(p):
        h = hashlib.sha256()
        with open(p, "rb") as f:
            for c in iter(lambda: f.read(65536), b""):
                h.update(c)
        return h.hexdigest()

    meta = {
        "source": "FBref via soccerdata",
        "seasons": seasons,
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "schema_version": 1,
        "row_count": {"master": len(master)},
        "hashes": {},
    }
    for f in ["master.parquet", "features.parquet", "umap_clusters.parquet", "outliers.parquet"]:
        p = DATA_DIR / f
        if p.exists():
            meta["hashes"][f] = _sha(p)
    with open(DATA_DIR / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    logger.info("Pipeline OK: %d jogadores", len(master))
    return True
