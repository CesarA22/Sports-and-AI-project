"""
Tab Explorer - scatter UMAP com clusters.
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from src.data.loader import get_merged_df


def render_explorer(df: pd.DataFrame, context: dict):
    """Renderiza o scatter UMAP."""
    if df.empty:
        st.warning("Nenhum dado carregado. Coloque os parquets em data/processed/.")
        return

    if "umap_x" not in df.columns or "umap_y" not in df.columns:
        st.warning("Colunas umap_x/umap_y não encontradas.")
        return

    # Aplicar filtros
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
    if context.get("cluster") and "cluster_id" in sub.columns:
        sub = sub[sub["cluster_id"].isin(context["cluster"])]

    color_col = "cluster_id" if "cluster_id" in sub.columns else None
    hover_cols = ["player", "team", "age", "minutes", "prospect_score"]
    hover_cols = [c for c in hover_cols if c in sub.columns]
    # 3 métricas-chave para hover
    metric_cols = [c for c in sub.columns if "per90" in c or "z_" in c][:3]
    hover_cols.extend(metric_cols)

    fig = px.scatter(
        sub,
        x="umap_x",
        y="umap_y",
        color=color_col,
        hover_data=hover_cols,
        title="UMAP - Jogadores por cluster",
    )
    fig.update_layout(
        height=600,
        xaxis_title="UMAP 1",
        yaxis_title="UMAP 2",
        legend_title="Cluster",
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"{len(sub)} jogadores exibidos.")
