"""
Tab Outliers - tabela Top K por prospect_score.
"""
import streamlit as st
import pandas as pd

from config import K_MAX


def render_outliers(df: pd.DataFrame, context: dict):
    """Renderiza a tabela de outliers."""
    if df.empty:
        st.warning("Nenhum dado carregado.")
        return

    sub = df.copy()
    if "season" in sub.columns and context.get("season_list"):
        sub = sub[sub["season"].isin(context["season_list"])]
    if "position_group" in sub.columns:
        sub = sub[sub["position_group"] == context.get("position_group", "CM_AM")]
    if "age" in sub.columns and context.get("age_max"):
        sub = sub[sub["age"] <= context["age_max"]]
    if "minutes" in sub.columns and context.get("minutes_min"):
        sub = sub[sub["minutes"] >= context["minutes_min"]]
    if context.get("team"):
        sub = sub[sub["team"].isin(context["team"])]

    score_col = "prospect_score" if "prospect_score" in sub.columns else "rarity_score"
    if score_col not in sub.columns:
        score_col = "impact_score" if "impact_score" in sub.columns else sub.columns[0]

    k = min(25, K_MAX)
    top = sub.nlargest(k, score_col)

    display_cols = ["player", "team", "season", "position_group", "minutes", "age", score_col]
    if "rarity_score" in sub.columns and "rarity_score" not in display_cols:
        display_cols.append("rarity_score")
    if "impact_score" in sub.columns and "impact_score" not in display_cols:
        display_cols.append("impact_score")
    display_cols = [c for c in display_cols if c in top.columns]

    st.dataframe(top[display_cols], use_container_width=True, hide_index=True)
    st.caption(f"Top {len(top)} por {score_col}.")
