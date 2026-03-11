"""
Tools seguras - funções expostas ao LLM. Todas validam inputs e limitam output.
"""
import json
import logging
from typing import Any, Optional

import duckdb
import pandas as pd
from rapidfuzz import fuzz, process

from config import (
    METRICS_ALLOWLIST,
    POSITION_GROUPS,
    SEASONS_ALLOWED,
    TOOL_MAX_ROWS,
    K_MAX,
)
from src.data.loader import AppData, get_merged_df

logger = logging.getLogger(__name__)


def _apply_default_filters(f: dict, df: pd.DataFrame) -> pd.DataFrame:
    """Aplica filtros default se não especificados."""
    out = df.copy()
    if "season" in out.columns and f.get("season"):
        out = out[out["season"].isin(f["season"])]
    if "position_group" in out.columns and f.get("position_group"):
        out = out[out["position_group"].isin(f["position_group"])]
    if "team" in out.columns and f.get("team"):
        out = out[out["team"].isin(f["team"])]
    if "age" in out.columns and f.get("age_max") is not None:
        out = out[out["age"] <= f["age_max"]]
    if "minutes" in out.columns and f.get("minutes_min") is not None:
        out = out[out["minutes"] >= f["minutes_min"]]
    return out


def _ensure_player_key(col: str, df: pd.DataFrame) -> str:
    if "player_key" in df.columns:
        return "player_key"
    if "player_id" in df.columns:
        return "player_id"
    return "player" if "player" in df.columns else df.columns[0]


# --- Tools ---


def search_players(
    data: AppData,
    query: str,
    season: Optional[list] = None,
    position_group: Optional[list] = None,
    team: Optional[list] = None,
    limit: int = 10,
) -> list[dict]:
    """Busca fuzzy por nome de jogador."""
    limit = min(max(1, int(limit)), TOOL_MAX_ROWS)
    df = get_merged_df(data)
    if df.empty or "player" not in df.columns:
        return []

    name_col = "player"
    candidates = df.drop_duplicates([name_col] + (["season"] if "season" in df.columns else []))

    if season:
        candidates = candidates[candidates["season"].isin(season)]
    if position_group:
        candidates = candidates[candidates["position_group"].isin(position_group)]
    if team:
        candidates = candidates[candidates["team"].isin(team)]

    names = candidates[name_col].astype(str).unique().tolist()
    if not names:
        return []

    matches = process.extract(query, names, scorer=fuzz.token_sort_ratio, limit=limit)
    keys = [m[0] for m in matches]
    result = candidates[candidates[name_col].isin(keys)].head(limit)
    pk = _ensure_player_key("player_key", result)

    return result[[pk, name_col, "team", "season", "position_group", "minutes", "age"]].drop_duplicates().to_dict("records")


def get_player_profile(data: AppData, player_key: str) -> dict:
    """Retorna perfil completo de um jogador."""
    df = get_merged_df(data)
    pk_col = _ensure_player_key("player_key", df)
    row = df[df[pk_col].astype(str) == str(player_key)]
    if row.empty:
        row = df[df["player"].astype(str).str.contains(str(player_key), case=False, na=False)]
    if row.empty:
        return {"error": "Jogador não encontrado."}

    row = row.iloc[0]
    card = data.player_cards.get(str(player_key), data.player_cards.get(str(row.get(pk_col, "")), ""))

    out = row.to_dict()
    out["card"] = card
    # Serializar para JSON
    for k, v in out.items():
        if isinstance(v, (pd.Timestamp,)):
            out[k] = str(v)
        elif hasattr(v, "item"):
            out[k] = v.item()
    return out


def _resolve_player_row(df: pd.DataFrame, pk_col: str, query: str):
    """Resolve jogador por player_key ou por nome (coluna player)."""
    q = str(query).strip()
    row = df[df[pk_col].astype(str) == q]
    if row.empty and "player" in df.columns:
        row = df[df["player"].astype(str).str.strip().str.lower() == q.lower()]
    if row.empty and "player" in df.columns:
        row = df[df["player"].astype(str).str.contains(q, case=False, na=False)]
    return row


def compare_players(
    data: AppData,
    player_key_a: str,
    player_key_b: str,
    metric_set: str = "default",
) -> dict:
    """Compara dois jogadores (z-scores, médias do cluster).
    Aceita player_key (jogador_50_2024) ou nome exibido (Jogador 50).
    """
    df = get_merged_df(data)
    pk = _ensure_player_key("player_key", df)
    metrics = [c for c in METRICS_ALLOWLIST if c in df.columns and ("per90" in c or "z_score" in c)][:10]

    a = _resolve_player_row(df, pk, player_key_a)
    b = _resolve_player_row(df, pk, player_key_b)
    if a.empty or b.empty:
        return {"error": "Um ou ambos jogadores não encontrados."}

    a, b = a.iloc[0], b.iloc[0]
    out = {
        "player_a": {c: a.get(c) for c in ["player", "team", "season"] if c in a.index},
        "player_b": {c: b.get(c) for c in ["player", "team", "season"] if c in b.index},
        "metrics": {m: {"a": a.get(m), "b": b.get(m)} for m in metrics},
    }
    return out


def top_k(
    data: AppData,
    filters: dict,
    metric: str,
    k: int = 10,
    order: str = "desc",
) -> list[dict]:
    """Retorna top-k por métrica."""
    if metric not in METRICS_ALLOWLIST:
        metric = "prospect_score" if "prospect_score" in get_merged_df(data).columns else "minutes"
    k = min(max(1, int(k)), K_MAX)
    df = get_merged_df(data)
    if df.empty or metric not in df.columns:
        return []

    df = _apply_default_filters(filters, df)
    df = df.sort_values(metric, ascending=(order != "desc")).head(k)
    return df.head(TOOL_MAX_ROWS).to_dict("records")


def similar_players(
    data: AppData,
    player_key: str,
    k: int = 5,
    method: str = "feature_distance",
) -> list[dict]:
    """Jogadores similares no espaço de features."""
    import numpy as np

    k = min(max(1, int(k)), K_MAX)
    df = get_merged_df(data)
    pk = _ensure_player_key("player_key", df)
    target = df[df[pk].astype(str) == str(player_key)]
    if target.empty:
        target = df[df["player"].astype(str).str.contains(str(player_key), case=False, na=False)]
    if target.empty:
        return []

    target = target.iloc[0]
    feat_cols = [c for c in df.columns if "per90" in c or "z_" in c]
    if not feat_cols:
        return []

    same_pg = df["position_group"] == target["position_group"]
    same_season = df["season"] == target["season"] if "season" in df.columns else True
    candidates = df[same_pg & same_season].copy()
    candidates = candidates[candidates[pk].astype(str) != str(player_key)]

    if candidates.empty:
        return []

    X = candidates[feat_cols].fillna(0)
    t_vec = target[feat_cols].fillna(0).values.reshape(1, -1)
    dists = np.linalg.norm(X.values - t_vec, axis=1)
    candidates = candidates.copy()
    candidates["_dist"] = dists
    candidates = candidates.nsmallest(k, "_dist").drop(columns=["_dist"])
    return candidates.to_dict("records")


def explain_cluster(
    data: AppData,
    position_group: str,
    season: int,
    cluster_id: int,
) -> dict:
    """Explica um cluster (médias vs posição, jogadores representativos)."""
    if position_group not in POSITION_GROUPS or season not in SEASONS_ALLOWED:
        return {"error": "position_group ou season inválido."}

    df = get_merged_df(data)
    mask = (df["position_group"] == position_group) & (df["season"] == season)
    if "cluster_id" in df.columns:
        mask = mask & (df["cluster_id"] == cluster_id)
    sub = df[mask]
    if sub.empty:
        return {"error": "Cluster vazio ou não encontrado."}

    feat_cols = [c for c in sub.columns if "per90" in c or "z_" in c]
    means = sub[feat_cols].mean().to_dict() if feat_cols else {}
    all_pos = df[(df["position_group"] == position_group) & (df["season"] == season)]
    pos_means = all_pos[feat_cols].mean().to_dict() if feat_cols else {}

    pk = _ensure_player_key("player_key", sub)
    reps = sub.nlargest(3, "minutes" if "minutes" in sub.columns else pk)
    rep_list = reps[["player", "team", "minutes"]].to_dict("records") if "player" in reps.columns else []

    return {
        "cluster_id": cluster_id,
        "position_group": position_group,
        "season": season,
        "cluster_means": means,
        "position_means": pos_means,
        "representative_players": rep_list,
    }


def explain_methodology() -> str:
    """Retorna texto fixo da metodologia (README)."""
    return """
## Metodologia do Scout Radar

O projeto utiliza dados do **Brasileirão Série A** (2023–2024).

**Pipeline:**
1. Filtragem de jogadores com idade ≤23
2. Normalização das métricas por 90 minutos
3. Padronização por posição (z-scores)
4. Redução dimensional com UMAP
5. Clustering com HDBSCAN
6. Identificação de outliers com Isolation Forest
7. Prospect score = raridade + impacto

**Fontes (dataset):**
- features.parquet
- umap_clusters.parquet
- outliers.parquet
"""


def execute_tools(plan: dict, data: AppData) -> dict:
    """
    Executa as tools conforme o plano e retorna evidence para o Answer Writer.
    """
    intent = plan.get("intent", "out_of_scope")
    if intent == "out_of_scope":
        return {"intent": "out_of_scope", "evidence": None, "tools_called": []}

    filters = plan.get("filters", {})
    entities = plan.get("entities", {})
    metrics = plan.get("metrics", [])
    k = plan.get("k", 10)
    tools_called = []

    evidence = {}

    if intent == "methodology":
        evidence["methodology"] = explain_methodology()
        tools_called.append("explain_methodology")
        return {"intent": intent, "evidence": evidence, "tools_called": tools_called}

    if intent == "player_profile":
        players = entities.get("players", [])
        if players:
            pk = players[0]
            evidence["profile"] = get_player_profile(data, pk)
            tools_called.append("get_player_profile")
        else:
            evidence["profile"] = {"error": "Nenhum jogador especificado."}

    elif intent == "compare":
        players = entities.get("players", [])
        if len(players) >= 2:
            evidence["compare"] = compare_players(data, players[0], players[1])
            tools_called.append("compare_players")
        else:
            evidence["compare"] = {"error": "É necessário especificar 2 jogadores."}

    elif intent == "top_k":
        metric = metrics[0] if metrics else "prospect_score"
        evidence["top_k"] = top_k(data, filters, metric, k)
        tools_called.append("top_k")

    elif intent == "similar":
        players = entities.get("players", [])
        if players:
            evidence["similar"] = similar_players(data, players[0], k)
            tools_called.append("similar_players")
        else:
            evidence["similar"] = {"error": "Jogador não especificado."}

    elif intent == "cluster_explain":
        cid = entities.get("cluster_id") or 0
        pg = filters.get("position_group", ["CM_AM"])[0]
        seas = filters.get("season", [2024])[0]
        evidence["cluster"] = explain_cluster(data, pg, seas, cid)
        tools_called.append("explain_cluster")

    return {"intent": intent, "evidence": evidence, "tools_called": tools_called}
