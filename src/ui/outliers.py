"""
Tab Outliers - tabela Top K por prospect_score com fotos e labels traduzidos.
"""
import streamlit as st
import pandas as pd

from config import K_MAX
from src.i18n.translations import t, get_metric_label
from src.ui.column_config import build_column_config
from src.ui.components import get_image_url


def render_outliers(df: pd.DataFrame, context: dict, images_df: pd.DataFrame = None):
    """Renderiza a tabela de outliers."""
    if df.empty:
        st.warning(t("no_data"))
        return
    if images_df is None:
        images_df = pd.DataFrame()

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
    top = sub.nlargest(k, score_col).copy()

    # Adicionar coluna de imagem se houver ao menos uma URL válida
    if not images_df.empty and "player_key" in top.columns:
        urls = top["player_key"].apply(lambda pk: get_image_url(pk, images_df))
        if any(u for u in urls if u):
            top["foto"] = urls

    display_cols = ["foto"] if "foto" in top.columns else []
    display_cols += ["player", "team", "season", "position_group", "minutes", "age", score_col]
    if "rarity_score" in sub.columns and "rarity_score" not in display_cols:
        display_cols.append("rarity_score")
    if "impact_score" in sub.columns and "impact_score" not in display_cols:
        display_cols.append("impact_score")
    display_cols = [c for c in display_cols if c in top.columns]

    column_config = build_column_config(display_cols)
    if "foto" in display_cols:
        column_config["foto"] = st.column_config.ImageColumn(get_metric_label("foto"), help=t("image_source"))

    st.dataframe(top[display_cols], use_container_width=True, hide_index=True, column_config=column_config)
    st.caption(t("top_k", k=len(top), metric=get_metric_label(score_col)) + ". " + t("image_source"))
