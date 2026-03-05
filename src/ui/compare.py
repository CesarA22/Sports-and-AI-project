"""
Tab Compare - comparação A vs B com radar de z-scores.
"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np


def _radar_chart(row_a: pd.Series, row_b: pd.Series, metrics: list) -> go.Figure:
    """Gera radar de z-scores ou valores normalizados."""
    vals_a = [float(row_a.get(m, 0) or 0) for m in metrics]
    vals_b = [float(row_b.get(m, 0) or 0) for m in metrics]
    # Normalizar para 0-1 para visualização
    all_vals = vals_a + vals_b
    mx = max(all_vals) if all_vals else 1
    mn = min(all_vals) if all_vals else 0
    rng = mx - mn or 1
    vals_a_n = [(v - mn) / rng for v in vals_a]
    vals_b_n = [(v - mn) / rng for v in vals_b]
    vals_a_n = vals_a_n + [vals_a_n[0]]
    vals_b_n = vals_b_n + [vals_b_n[0]]
    categories = metrics + [metrics[0]]

    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=vals_a_n,
            theta=categories,
            fill="toself",
            name=str(row_a.get("player", "A")),
        )
    )
    fig.add_trace(
        go.Scatterpolar(
            r=vals_b_n,
            theta=categories,
            fill="toself",
            name=str(row_b.get("player", "B")),
        )
    )
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        showlegend=True,
        height=450,
    )
    return fig


def render_compare(df: pd.DataFrame, context: dict):
    """Renderiza comparação entre dois jogadores."""
    if df.empty:
        st.warning("Nenhum dado carregado.")
        return

    sub = df.copy()
    if "season" in sub.columns and context.get("season_list"):
        sub = sub[sub["season"].isin(context["season_list"])]
    if "position_group" in sub.columns:
        sub = sub[sub["position_group"] == context.get("position_group", "CM_AM")]

    players = sub["player"].dropna().unique().tolist() if "player" in sub.columns else []
    if not players:
        st.warning("Nenhum jogador disponível nos filtros.")
        return

    col1, col2 = st.columns(2)
    with col1:
        player_a = st.selectbox("Jogador A", players, key="compare_a")
    with col2:
        player_b = st.selectbox("Jogador B", players, key="compare_b")

    if not player_a or not player_b or player_a == player_b:
        st.info("Selecione dois jogadores diferentes.")
        return

    pk = "player_key" if "player_key" in sub.columns else "player"
    row_a = sub[sub["player"] == player_a].iloc[0]
    row_b = sub[sub["player"] == player_b].iloc[0]

    metric_cols = [c for c in sub.columns if "z_" in c or "per90" in c][:8]
    if not metric_cols:
        metric_cols = [c for c in sub.columns if sub[c].dtype in [np.float64, np.float32]][:8]

    if metric_cols:
        fig = _radar_chart(row_a, row_b, metric_cols)
        st.plotly_chart(fig, use_container_width=True)

    # Tabela comparativa
    comp_df = pd.DataFrame({
        "Métrica": metric_cols,
        str(row_a.get("player", "A")): [row_a.get(m, "") for m in metric_cols],
        str(row_b.get("player", "B")): [row_b.get(m, "") for m in metric_cols],
    })
    st.dataframe(comp_df, use_container_width=True, hide_index=True)
