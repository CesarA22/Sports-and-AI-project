"""
Player Intelligence Card - foto, nome, time, radar, prospect score, botão AI.
"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from src.i18n.translations import get_metric_label, get_position_label, LOCALE
from src.ui.components.base import render_player_avatar
from src.ui.components.ai_modal import show_ai_insight
from src.ai.insights import generate_player_insight


def render_player_intelligence_card(
    row: pd.Series,
    images_df: pd.DataFrame,
    metric_cols: list,
    df_full: pd.DataFrame,
    key_suffix: str = "player_card",
):
    """Card completo do jogador com radar e botão AI scouting report."""
    pk = row.get("player_key", row.get("player", ""))
    player_name = str(row.get("player", ""))
    team = row.get("team", "")
    pos = row.get("position_group", "")
    minutes = int(row.get("minutes", 0))
    prospect = row.get("prospect_score", 0)

    with st.container(border=True):
        st.markdown("#### 🎯 Player Intelligence Card")
        col_img, col_info = st.columns([1, 2])
        with col_img:
            avatar = render_player_avatar(pk, player_name, images_df, 100)
            st.markdown(f'<div style="text-align:center">{avatar}</div>', unsafe_allow_html=True)
        with col_info:
            st.markdown(f"**{player_name}**")
            st.caption(f"{team} • {get_position_label(str(pos))} • {minutes} min")
            st.metric("Prospect Score", f"{prospect:.2f}")

        if metric_cols:
            vals = [float(row.get(m, 0) or 0) for m in metric_cols]
            all_vals = df_full[metric_cols].fillna(0).values.flatten()
            mx, mn = float(np.max(all_vals)) if len(all_vals) else 1, float(np.min(all_vals)) if len(all_vals) else 0
            rng = mx - mn or 1
            vals_n = [(v - mn) / rng for v in vals]
            vals_n = vals_n + [vals_n[0]]
            labels = [get_metric_label(m) for m in metric_cols] + [get_metric_label(metric_cols[0])]

            fig = go.Figure(go.Scatterpolar(r=vals_n, theta=labels, fill="toself", line=dict(color="#7C3AED")))
            fig.update_layout(polar=dict(radialaxis=dict(range=[0, 1])), showlegend=False, height=280, margin=dict(t=20))
            st.plotly_chart(fig, use_container_width=True)

        if metric_cols and st.button("✨ AI Scouting Report", key=f"ai_report_{key_suffix}", help="Gerar relatório de scouting por IA"):
            metrics_text = "\n".join(f"- {get_metric_label(m)}: {row.get(m, 0):.2f}" for m in metric_cols)
            with st.spinner("Gerando relatório..."):
                insight = generate_player_insight(player_name, metrics_text, locale=LOCALE)
            show_ai_insight(insight, title=f"AI Scouting Report - {player_name}")
